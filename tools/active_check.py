"""End-to-end check of devices that send: polling (OBD-II, Daly, CANopen SDO) and writing (CiA 401 outputs).

Run in the SSH add-on next to wsclient.py, with tools/sim/can_sim.py running on the virtual interface:
    python3 active_check.py VCAN0
Creates one device from each sending template, checks that nothing is sent until polling or writing is
turned on, then checks the values, the politeness (rate, one request at a time, backing off a PID that never
answers), the NMT start button, output switches looped back to inputs by the simulator, the activity log,
and that turning polling off stops the requests. Removes the devices at the end.
"""

from __future__ import annotations

import json
import sys
import time

from wsclient import WS, rest

NAME = sys.argv[1] if len(sys.argv) > 1 else "VCAN0"
results: list[tuple[str, bool, str]] = []
PREFIX = "Active check"


def check(name: str, ok: bool, detail: str = "") -> bool:
    results.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail else ""), flush=True)
    return bool(ok)


def service(ws: WS, _service: str, **data):
    res = ws.call("call_service", domain="woow_can", service=_service, service_data=data, return_response=True)
    if isinstance(res, dict) and "__error__" in res:
        return res
    return res.get("response")


def ha(ws: WS, domain: str, svc: str, entity_id: str, **data):
    return ws.call("call_service", domain=domain, service=svc, service_data={"entity_id": entity_id, **data})


def values(ws: WS, device: str) -> dict:
    dev = service(ws, "get_device", device=device)["device"]
    return {f"{m['name']}.{s['name']}": s["value"] for m in dev["status"] for s in m["signals"]}


def view(ws: WS, device: str) -> dict:
    return service(ws, "get_device", device=device)["device"]


def entity(dev: dict, message: str, signal: str) -> str | None:
    for m in dev["status"]:
        if m["name"] == message:
            for s in m["signals"]:
                if s["name"] == signal:
                    return s["entity_id"]
    return None


def frames(ws: WS, ids: str, seconds: float) -> list[dict]:
    return service(ws, "get_trace", interface=NAME, ids=ids, direction="tx", seconds=seconds, limit=2000)["frames"]


def main() -> None:
    ws = WS()
    for dev in service(ws, "list_devices")["devices"]:
        if dev["name"].startswith(PREFIX):
            service(ws, "delete_device", device=dev["id"], note="active check: leftovers")
    made = {}
    for tid, params, suffix in (("obd2_mode01", {}, "car"), ("daly_bms", {}, "battery"),
                                ("cia401_io", {"node_id": 7}, "io"), ("cia402_drive_monitor", {"node_id": 5}, "drive")):
        res = service(ws, "create_from_template", template=tid, interface=NAME, name=f"{PREFIX} {suffix}",
                      params=params, note="active check")
        made[suffix] = res["device"]["name"] if res and "device" in res else None
        check(f"created {tid}", made[suffix] is not None and not res["device"]["active"], json.dumps(res)[:200])
    time.sleep(3)
    quiet = frames(ws, "7DF, 18900140-189801FF, 605, 607, 0", 3)
    check("nothing sent before polling is turned on", quiet == [], f"{len(quiet)} frames")

    # ---- OBD-II -----------------------------------------------------------------------------
    car = made["car"]
    res = service(ws, "control_device", device=car, active=True, note="active check: poll the car")
    check("polling on", res and res["device"]["active"], json.dumps(res)[:200])
    time.sleep(6)
    v = values(ws, car)
    check("OBD values", (v.get("PID_0C.EngineSpeed"), v.get("PID_0D.VehicleSpeed"), v.get("PID_05.CoolantTemperature"),
                         v.get("PID_42.ModuleVoltage"), v.get("PID_5E.FuelRate")) == (1726, 50, 83, 14, 12.5),
          json.dumps({k: v[k] for k in list(v)[:6]}))
    sent = frames(ws, "7DF", 5)
    rate = len(sent) / 5
    check("OBD polite rate (under 10 a second)", 4 <= rate <= 10, f"{rate:.1f}/s")
    times = sorted(f["time"] for f in sent)
    gaps = [b - a for a, b in zip(times, times[1:])]
    check("one OBD request at a time", min(gaps) > 0.0005 if gaps else False, f"min gap {min(gaps) * 1000:.1f} ms")
    status = {r["name"]: r for r in view(ws, car)["requests"]}
    check("answered PIDs ok", status["PID 0C"]["state"] == "ok" and status["PID 0C"]["replies"] >= 8,
          json.dumps(status["PID 0C"]))
    check("unanswered PID waits", status["PID 5C"]["replies"] == 0 and status["PID 5C"]["sent"] >= 1,
          json.dumps(status["PID 5C"]))
    states = {s["entity_id"]: s["state"] for s in rest("GET", "/states")
              if s["entity_id"].startswith("sensor.active_check_car")}
    check("OBD entities", float(states.get("sensor.active_check_car_engine_speed", "nan")) == 1726
          and float(states.get("sensor.active_check_car_vehicle_speed", "nan")) == 50, json.dumps(states)[:300])

    # ---- Daly --------------------------------------------------------------------------------
    battery = made["battery"]
    service(ws, "control_device", device=battery, active=True, note="active check: poll the BMS")
    time.sleep(6)
    v = values(ws, battery)
    check("Daly values", (v.get("Pack_90.TotalVoltage"), v.get("Pack_90.Current"), v.get("Pack_90.SOC"),
                          v.get("Cells_91.CellDelta"), v.get("Mos_93.State")) == (52.5, 11.0, 85.0, 40.0, "discharging"),
          json.dumps({k: v[k] for k in ("Pack_90.TotalVoltage", "Pack_90.Current", "Pack_90.SOC", "Cells_91.CellDelta",
                                        "Mos_93.State") if k in v}))
    daly = frames(ws, "18900140", 5)
    check("Daly asks 0x90 once a second", 4 <= len(daly) <= 6, f"{len(daly)} in 5 s")

    # ---- CiA 402 drive (reads only) -------------------------------------------------------------
    drive = made["drive"]
    v = values(ws, drive)
    check("drive state from TPDO1 (listening)", v.get("Statusword_TPDO1.State") in ("operation_enabled", "fault"),
          str(v.get("Statusword_TPDO1.State")))
    service(ws, "control_device", device=drive, active=True, note="active check: poll the drive")
    time.sleep(5)
    v = values(ws, drive)
    check("drive values by SDO", v.get("Velocity_SDO.VelocityActual") == 1500 and v.get("Torque_SDO.TorqueActual") == 50.0
          and v.get("Mode_SDO.ModeDisplay") == "profile_velocity" and isinstance(v.get("Position_SDO.PositionActual"), int),
          json.dumps({k: v.get(k) for k in ("Velocity_SDO.VelocityActual", "Torque_SDO.TorqueActual",
                                            "Mode_SDO.ModeDisplay", "Position_SDO.PositionActual")}))
    bad = service(ws, "control_device", device=drive, allow_write=True)
    check("a read-only template cannot allow writing", "__error__" in bad, json.dumps(bad)[:160])

    # ---- CiA 401 I/O: NMT start, outputs, inputs, analogue inputs ------------------------------------------
    service(ws, "send", interface=NAME, frame="000#8007", note="active check: node 7 back to pre-operational")
    time.sleep(1.2)
    io = made["io"]
    dev = view(ws, io)
    check("no switches until writing is allowed", entity(dev, "Outputs", "DO3") is None
          and dev["writable"] and not dev["allow_write"])
    bad = service(ws, "write_signal", device=io, message="Outputs", signal="DO3", value=1)
    check("writing refused while not allowed", "__error__" in bad and "write_not_allowed" in json.dumps(bad),
          json.dumps(bad)[:160])
    service(ws, "control_device", device=io, allow_write=True, note="active check: allow writing")
    time.sleep(2)
    dev = view(ws, io)
    button = entity(dev, "NMT", "Command")
    switch3 = entity(dev, "Outputs", "DO3")
    check("switches and the start button appear", bool(button and switch3), f"{button} {switch3}")
    v = values(ws, io)
    check("node pre-operational: no inputs yet", v.get("Heartbeat.State") == "pre_operational"
          and v.get("Inputs.DI0") is None, json.dumps({k: v.get(k) for k in ("Heartbeat.State", "Inputs.DI0")}))
    ha(ws, "button", "press", button)
    time.sleep(1.5)
    nmt = service(ws, "get_trace", interface=NAME, ids="0", direction="tx", limit=1)["frames"]
    check("NMT start sent", nmt and nmt[0]["data"] == "01 07", json.dumps(nmt[:1]))
    v = values(ws, io)
    check("node operational, inputs arrive", v.get("Heartbeat.State") == "operational" and v.get("Inputs.DI0") in (0, 1),
          json.dumps({k: v.get(k) for k in ("Heartbeat.State", "Inputs.DI0")}))
    ha(ws, "switch", "turn_on", switch3)
    time.sleep(0.4)
    ha(ws, "switch", "turn_on", entity(dev, "Outputs", "DO5"))
    time.sleep(1.5)
    out = service(ws, "get_trace", interface=NAME, ids="207", direction="tx", limit=2)["frames"]
    check("RPDO1 keeps the other outputs", [f["data"] for f in out] == ["28 00", "08 00"], json.dumps(out))
    v = values(ws, io)
    check("outputs looped back to inputs", v.get("Inputs.DI11") == 1 and v.get("Inputs.DI13") == 1
          and v.get("Inputs.DI12") == 0, json.dumps({k: v.get(k) for k in ("Inputs.DI11", "Inputs.DI12", "Inputs.DI13")}))
    state = rest("GET", f"/states/{switch3}")["state"]
    check("switch state", state == "on", state)
    res = service(ws, "write_signal", device=io, message="Outputs", signal="DO3", value=0, note="active check")
    check("write_signal service", res and res.get("data") == "20 00", json.dumps(res))
    service(ws, "control_device", device=io, active=True, note="active check: poll analogue inputs")
    time.sleep(3)
    v = values(ws, io)
    check("analogue inputs by SDO", v.get("AI1_SDO.AI1") == 16383 and v.get("AI2_SDO.AI2") == -16383,
          json.dumps({k: v.get(k) for k in ("AI1_SDO.AI1", "AI2_SDO.AI2", "AI3_SDO.AI3")}))
    acts = service(ws, "get_activity", limit=30)["activity"]
    writes = [a for a in acts if a["action"] == "write_signal"]
    check("writes in the activity log", len(writes) >= 3 and any("DO5" in a["summary"] for a in writes),
          json.dumps([a["summary"] for a in writes][:4], ensure_ascii=False))

    # ---- polling off stops the requests ------------------------------------------------------------
    for key in ("car", "battery", "drive"):
        service(ws, "control_device", device=made[key], active=False, note="active check: off")
    service(ws, "control_device", device=made["io"], active=False, allow_write=False, note="active check: off")
    time.sleep(2.5)
    late = frames(ws, "7DF, 18900140-189801FF, 605, 607", 2)
    check("polling off: no more requests", late == [], f"{len(late)} frames")
    dev = view(ws, io)
    check("writing off: switches gone", entity(dev, "Outputs", "DO3") is None)

    for key, name in made.items():
        if name:
            service(ws, "delete_device", device=name, note="active check cleanup")
    left = [d["name"] for d in service(ws, "list_devices")["devices"] if d["name"].startswith(PREFIX)]
    check("cleaned up", not left, ",".join(left))
    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
