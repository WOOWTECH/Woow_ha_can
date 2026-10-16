"""Check the built-in templates and DBC import end to end on a live Home Assistant (run in the SSH add-on).

Needs the VCAN0 interface (tools/can_live_check.py creates it) and tools/sim/can_sim.py running on vcan0
for at least 90 s. Creates one device per template, compares decoded values and entity states with the
values the simulator sends, watches a CANopen node go offline and an emergency come and go, imports a
DBC file, then deletes everything it made (--keep leaves the devices).
    python3 template_check.py [--keep]
"""

from __future__ import annotations

import json
import sys
import time

from wsclient import WS, rest

KEEP = "--keep" in sys.argv
NAME = "VCAN0"
results: list[tuple[str, bool, str]] = []
BMS_DBC = """VERSION ""
NS_ :
BS_:
BU_: BMS INV
BO_ 849 BMS_351_Limits: 8 BMS
 SG_ ChargeVoltageLimit : 0|16@1+ (0.1,0) [0|6553.5] "V" INV
 SG_ ChargeCurrentLimit : 16|16@1- (0.1,0) [-3276.8|3276.7] "A" INV
BO_ 854 BMS_356_Meas: 8 BMS
 SG_ BatteryVoltage : 0|16@1- (0.01,0) [-327.68|327.67] "V" INV
 SG_ BatteryCurrent : 16|16@1- (0.1,0) [-3276.8|3276.7] "A" INV
 SG_ BatteryTemperature : 32|16@1- (0.1,0) [-3276.8|3276.7] "degC" INV
CM_ SG_ 854 BatteryCurrent "positive = charging";
BA_DEF_ BO_ "GenMsgCycleTime" INT 0 65535;
BA_ "GenMsgCycleTime" BO_ 854 1000;
"""


def check(name: str, ok: bool, detail: str = "") -> bool:
    results.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail else ""), flush=True)
    return bool(ok)


def service(ws: WS, _service: str, **data):
    res = ws.call("call_service", domain="woow_can", service=_service, service_data=data, return_response=True)
    if isinstance(res, dict) and "__error__" in res:
        return res
    return res.get("response")


def near(value, want, tol=0.011) -> bool:
    return isinstance(value, (int, float)) and abs(value - want) <= tol


def values_of(ws: WS, device: str) -> dict:
    got = service(ws, "get_device", device=device)["device"]
    out = {}
    for msg in got["status"]:
        for sig in msg["signals"]:
            out[f"{msg['name']}.{sig['name']}"] = sig
    return out


def state(entity_id: str | None) -> dict:
    if not entity_id:
        return {}
    try:
        return rest("GET", f"/states/{entity_id}")
    except Exception:  # noqa: BLE001
        return {}


def create(ws: WS, template: str, name: str, **kw):
    old = service(ws, "list_devices")
    for dev in old.get("devices", []):
        if dev["name"] == name:
            service(ws, "delete_device", device=name, note="template check: start over")
    return service(ws, "create_from_template", template=template, interface=NAME, name=name,
                   note="template check", **kw)


def main() -> None:
    ws = WS()
    templates = {t["id"]: t for t in service(ws, "list_templates")["templates"]}
    check("templates listed", {"bms_lv_0x35x", "j1939_engine_vehicle", "j1939_dm1", "nmea2000_dc",
                               "canopen_node_monitor"} <= set(templates), ",".join(sorted(templates)))
    check("template facts", all(t["source"] and t["license"] and t["confidence"] for t in templates.values()))

    # ---- battery ----------------------------------------------------------------------------
    bms = create(ws, "bms_lv_0x35x", "Sim BMS")
    groups = (bms or {}).get("device", {}).get("groups")
    check("BMS: groups detected from traffic", groups == ["pylon", "victron", "inverter"], str(groups or bms))
    time.sleep(4)
    v = values_of(ws, "Sim BMS")
    val = lambda k: v.get(k, {}).get("value")  # noqa: E731
    check("BMS: limits", near(val("BMS_351_Limits.ChargeVoltageLimit"), 53.2) and near(val("BMS_351_Limits.ChargeCurrentLimit"), 370)
          and near(val("BMS_351_Limits.DischargeVoltageLimit"), 46.0),
          json.dumps({k: val(f"BMS_351_Limits.{k}") for k in ("ChargeVoltageLimit", "ChargeCurrentLimit",
                                                               "DischargeCurrentLimit", "DischargeVoltageLimit")}))
    soc = val("BMS_355_SOC.SOC")
    check("BMS: SOC and SOH", isinstance(soc, int) and 10 <= soc <= 14 and val("BMS_355_SOC.SOH") == 100, f"{soc}")
    volt, amps = val("BMS_356_Measurements.BatteryVoltage"), val("BMS_356_Measurements.BatteryCurrent")
    check("BMS: voltage / current / power", (near(volt, 48.66, 0.02) or near(volt, 48.46, 0.02)) and amps in (0.0, -25.3)
          and near(val("BMS_356_Measurements.BatteryPower"), volt * amps, 0.01), f"{volt} V {amps} A")
    check("BMS: manufacturer, modules", val("BMS_35E_Manufacturer.Manufacturer") == "PYLON"
          and val("PYLON_359_Alarms.ModuleCount") == 10)
    check("BMS: Victron extensions", near(val("VICTRON_373_CellExtremes.MinCellVoltage"), 3.306, 0.0005)
          and val("VICTRON_373_CellExtremes.MaxCellTemperature") == 17
          and near(val("BMS_378_Energy.ChargedEnergy"), 211.2) and val("VICTRON_379_Capacity.InstalledCapacity") == 156)
    soc_state = state(v.get("BMS_355_SOC.SOC", {}).get("entity_id"))
    check("BMS: SOC entity", soc_state.get("attributes", {}).get("device_class") == "battery"
          and soc_state.get("attributes", {}).get("unit_of_measurement") == "%"
          and soc_state.get("state") == str(soc), json.dumps({k: soc_state.get(k) for k in ("entity_id", "state")}))
    energy = state(v.get("BMS_378_Energy.ChargedEnergy", {}).get("entity_id")).get("attributes", {})
    check("BMS: energy entity for the energy dashboard", energy.get("state_class") == "total_increasing"
          and energy.get("unit_of_measurement") == "kWh", json.dumps(energy)[:160])
    charge = state(v.get("PYLON_35C_Requests.ChargeEnable", {}).get("entity_id"))
    protection = state(v.get("PYLON_359_Alarms.ProtectionActive", {}).get("entity_id"))
    check("BMS: binary sensors", charge.get("state") == "on" and protection.get("state") == "off",
          f"charge {charge.get('state')} protection {protection.get('state')}")
    temp = state(v.get("BMS_356_Measurements.BatteryTemperature", {}).get("entity_id")).get("attributes", {})
    check("BMS: temperature unit", temp.get("unit_of_measurement") == "°C" and temp.get("device_class") == "temperature")

    # ---- J1939 engine ---------------------------------------------------------------------
    create(ws, "j1939_engine_vehicle", "Sim Engine", params={"source_address": "00"})
    create(ws, "j1939_engine_vehicle", "Other ECU", params={"source_address": "01"})
    create(ws, "j1939_dm1", "Sim Faults", params={"source_address": "00"})
    create(ws, "nmea2000_dc", "Sim DC", params={"instance": 0, "source_address": "23"})
    create(ws, "canopen_node_monitor", "Sim Node", params={"node_id": 5, "heartbeat_ms": 1000})
    time.sleep(4)
    e = values_of(ws, "Sim Engine")
    ev = lambda k: e.get(k, {}).get("value")  # noqa: E731
    check("J1939: engine speed", ev("EEC1.EngineSpeed") in (1491.25, 1500), str(ev("EEC1.EngineSpeed")))
    check("J1939: vehicle", near(ev("CCVS1.WheelBasedSpeed"), 80.0) and ev("CCVS1.BrakeSwitch") == 1
          and ev("CCVS1.CruiseControlActive") == 0)
    check("J1939: temperatures", ev("ET1.CoolantTemperature") == 85 and ev("ET1.FuelTemperature") == 30
          and near(ev("ET1.OilTemperature"), 95.0) and ev("ET1.TurboOilTemperature") is None)
    check("J1939: oil, fuel, battery, hours", near(ev("EFL_P1.OilLevel"), 86.0) and ev("EFL_P1.OilPressure") == 400
          and near(ev("LFE1.FuelRate"), 12.5) and near(ev("LFE1.ThrottlePosition"), 40.0)
          and near(ev("VEP1.BatteryPotential"), 27.85) and near(ev("HOURS.EngineHours"), 1234.5))
    rpm = state(e.get("EEC1.EngineSpeed", {}).get("entity_id"))
    check("J1939: engine speed entity", rpm.get("state") in ("1491.25", "1500.0", "1500") and
          rpm.get("attributes", {}).get("unit_of_measurement") == "rpm", json.dumps({k: rpm.get(k) for k in ("entity_id", "state")}))
    brake = state(e.get("CCVS1.BrakeSwitch", {}).get("entity_id"))
    check("J1939: brake binary sensor", brake.get("state") == "on", str(brake.get("state")))
    other = values_of(ws, "Other ECU")
    check("J1939: another source address hears nothing", other.get("EEC1.EngineSpeed", {}).get("value") is None)
    other_state = state(other.get("EEC1.EngineSpeed", {}).get("entity_id"))
    check("J1939: silent device unavailable", other_state.get("state") == "unavailable", str(other_state.get("state")))

    # ---- NMEA 2000 ----------------------------------------------------------------------------
    n = values_of(ws, "Sim DC")
    nv = lambda k: n.get(k, {}).get("value")  # noqa: E731
    check("NMEA 2000: battery status", near(nv("BatteryStatus_127508.Voltage"), 26.72) and near(nv("BatteryStatus_127508.Current"), 6.7)
          and near(nv("BatteryStatus_127508.Temperature"), 16.62) and near(nv("BatteryStatus_127508.Power"), 179.024, 0.01))
    check("NMEA 2000: fast-packet DC status", nv("DcDetailedStatus_127506.StateOfCharge") == 87
          and nv("DcDetailedStatus_127506.StateOfHealth") == 95 and nv("DcDetailedStatus_127506.TimeRemaining") == 600
          and near(nv("DcDetailedStatus_127506.RippleVoltage"), 0.165, 0.0005),
          json.dumps({k.split(".")[1]: nv(k) for k in n if k.startswith("DcDetailed")}))

    # ---- DM1, CANopen: watch them change over a minute ------------------------------------------
    counts, texts, red = set(), set(), set()
    node_states, online, error = set(), set(), set()
    deadline = time.time() + 65
    while time.time() < deadline:
        f = values_of(ws, "Sim Faults")
        counts.add(f.get("DM1.ActiveFaults", {}).get("value"))
        texts.add(f.get("DM1.FaultCodes", {}).get("value"))
        red.add(f.get("DM1.RedStopLamp", {}).get("value"))
        node = values_of(ws, "Sim Node")
        node_states.add(node.get("Heartbeat.State", {}).get("value"))
        online.add(state(node.get("Heartbeat.Online", {}).get("entity_id")).get("state"))
        error.add((node.get("Emergency.ErrorCode", {}).get("value"),
                   state(node.get("Emergency.InError", {}).get("entity_id")).get("state")))
        if {1, 2} <= counts and {"on", "off"} <= online and len({e for e in error if e[0] is not None}) >= 2:
            break
        time.sleep(1)
    check("DM1: single frame and BAM", {1, 2} <= counts and "SPN 100 FMI 1, SPN 110 FMI 0" in texts
          and {True, False} <= red, f"counts {counts} red {red}")
    check("CANopen: NMT state", "operational" in node_states, str(node_states))
    check("CANopen: offline after the heartbeat stops", {"on", "off"} <= online, str(online))
    check("CANopen: emergency comes and goes", (33072, "on") in error and (0, "off") in error, str(error))

    # ---- policies, decode, monitor names -------------------------------------------------------
    res = service(ws, "set_signal", device="Sim BMS", message="BMS_356_Measurements", signal="BatteryVoltage",
                  min_interval=5, note="template check")
    got = service(ws, "get_device", device="Sim BMS")["device"]["definition"]
    voltage = next(s for m in got["messages"] if m["name"] == "BMS_356_Measurements" for s in m["signals"]
                   if s["name"] == "BatteryVoltage")
    check("set_signal", voltage["entity"].get("min_interval") == 5, json.dumps(voltage.get("entity"))[:120])
    dec = service(ws, "decode_frame", interface=NAME, frame="356#BE14F9FF8C000000")
    first = (dec or {}).get("decoded", [{}])[0]
    check("decode_frame", first.get("source") == "Sim BMS" and any(
        s["name"] == "BatteryVoltage" and near(s["value"], 53.1) for s in first.get("signals", [])), json.dumps(dec)[:200])
    entry_id = next(i["config_entry_id"] for i in service(ws, "list_interfaces")["interfaces"] if i["name"] == NAME)
    ws.id += 1
    sub = ws.id
    ws.send({"id": sub, "type": "woow_can/monitor/subscribe", "source": entry_id, "token": "template-check"})
    names = {}
    while True:
        msg = ws.recv()
        if msg.get("id") == sub and msg.get("type") == "event":
            names = msg["event"].get("names", {})
            break
    ws.call("unsubscribe_events", subscription=sub)
    check("monitor names rows", names.get("854") == "BMS_356_Measurements" and names.get(str(0x0CF00400 | 0x80000000)) == "EEC1",
          json.dumps({k: names[k] for k in list(names)[:6]}))
    test = service(ws, "test_signal", interface=NAME, can_id="356", start=16, length=16, signed=True, factor=0.1, seconds=20)
    check("test_signal finds the current", test and set(s["value"] for s in test["samples"]) <= {0.0, -25.3}
          and test["frames"] >= 10, json.dumps({k: test.get(k) for k in ("frames", "min", "max", "changes")}) if test else "")

    # ---- DBC ---------------------------------------------------------------------------------
    imported = service(ws, "import_dbc", name="sim_bms.dbc", content=BMS_DBC, attach=[NAME], note="template check")
    summary = (imported or {}).get("database", {})
    check("import_dbc", summary.get("messages") == 2 and summary.get("signals") == 5 and summary.get("warning_count") == 0,
          json.dumps(summary)[:200])
    service(ws, "delete_device", device="Sim BMS", note="template check: let the DBC decode")
    dec = service(ws, "decode_frame", interface=NAME, frame="356#BE14F9FF8C000000")
    check("decode with the DBC", any(d["source"] == "sim_bms.dbc" and d["message"] == "BMS_356_Meas" for d in dec["decoded"]),
          json.dumps(dec)[:200])
    made = service(ws, "create_from_dbc", dbc="sim_bms.dbc", interface=NAME, name="DBC BMS", messages=["BMS_356_Meas"],
                   note="template check")
    time.sleep(3)
    d = values_of(ws, "DBC BMS")
    volt_entity = state(d.get("BMS_356_Meas.BatteryVoltage", {}).get("entity_id"))
    check("device from DBC", made and volt_entity.get("attributes", {}).get("device_class") == "voltage"
          and volt_entity.get("state") not in (None, "unknown", "unavailable"), json.dumps({k: volt_entity.get(k) for k in ("entity_id", "state")}))

    if not KEEP:
        for name in ("Sim Engine", "Other ECU", "Sim Faults", "Sim DC", "Sim Node", "DBC BMS"):
            service(ws, "delete_device", device=name, note="template check cleanup")
        ws.call("woow_can/dbc/control", action="delete", name="sim_bms.dbc")
        left = service(ws, "list_devices")["devices"]
        check("cleanup", not left, ",".join(d["name"] for d in left))
    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
