"""End-to-end check of WOOW CAN on a live Home Assistant with a virtual interface (run in the SSH add-on).

Needs tools/sim/can_sim.py running on the same vcan inside the Core container, e.g.
    docker exec -d homeassistant python3 /tmp/can_sim.py vcan0 300
then:
    python3 can_live_check.py vcan0
It creates the interface's config entry if needed (menu > virtual), exercises services, websocket
commands and file views, and cleans up what it made except the interface itself (--remove drops it too).
"""

from __future__ import annotations

import json
import sys
import time
import urllib.request

from wsclient import TOKEN, WS, rest

IFNAME = sys.argv[1] if len(sys.argv) > 1 else "vcan0"
REMOVE = "--remove" in sys.argv
results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> bool:
    results.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail else ""), flush=True)
    return bool(ok)


def service(ws: WS, _service: str, **data):
    """Call a woow_can service with return_response through the websocket API."""
    res = ws.call("call_service", domain="woow_can", service=_service, service_data=data, return_response=True)
    if isinstance(res, dict) and "__error__" in res:
        return res
    return res.get("response")


def entries() -> list[dict]:
    return [e for e in rest("GET", "/config/config_entries/entry") if e["domain"] == "woow_can"]


def ensure_interface() -> dict:
    for e in entries():
        if e["title"].lower() == IFNAME.lower():
            return e
    flow = rest("POST", "/config/config_entries/flow", {"handler": "woow_can", "show_advanced_options": False})
    assert flow["type"] == "menu", flow
    flow = rest("POST", f"/config/config_entries/flow/{flow['flow_id']}", {"next_step_id": "virtual"})
    flow = rest("POST", f"/config/config_entries/flow/{flow['flow_id']}", {"port": IFNAME})
    assert flow.get("step_id") == "can", flow
    flow = rest("POST", f"/config/config_entries/flow/{flow['flow_id']}", {
        "name": IFNAME.upper(), "filters": "", "event_filter": "", "max_events_per_sec": 20})
    assert flow["type"] == "create_entry", flow
    time.sleep(2)
    return next(e for e in entries() if e["title"].lower() == IFNAME.lower())


def http_get(path: str) -> str:
    req = urllib.request.Request("http://supervisor/core/api" + path, headers={"Authorization": "Bearer " + TOKEN})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode()


def main() -> None:
    entry = ensure_interface()
    entry_id = entry["entry_id"]
    name = entry["title"]
    check("interface entry", entry["state"] == "loaded", f"{name} {entry['state']}")
    hub = [e for e in entries() if e["title"] in ("管理面板", "Admin panel")]
    check("admin panel entry", hub and hub[0]["state"] == "loaded")
    time.sleep(3)
    ws = WS()

    # ---- services: reads -------------------------------------------------------------
    info = service(ws, "list_interfaces")
    me = next((i for i in info["interfaces"] if i["config_entry_id"] == entry_id), None)
    check("list_interfaces", me and me["state"] == "virtual" and me["virtual"] and me["can_send"],
          json.dumps({k: me.get(k) for k in ("state", "frames_per_second", "ids_seen")}) if me else str(info))
    mon = service(ws, "get_monitor", interface=name)
    rows = {r["id"]: r for r in mon["interfaces"][0]["ids"]}
    check("get_monitor: battery IDs", {"351", "355", "356", "359", "35C", "35E", "305"} <= set(rows), ",".join(sorted(rows)))
    check("get_monitor: 50 Hz counter", "0C0" in rows and 40 <= (rows["0C0"]["rate_hz"] or 0) <= 60,
          str(rows.get("0C0", {}).get("rate_hz")))
    check("get_monitor: J1939 29-bit", "0CF00400" in rows and rows["0CF00400"]["extended"])
    check("simulator frames count as received", rows["351"]["direction"] == "rx" and rows["351"]["from_this_host"])
    check("get_monitor: changes counted", rows.get("0C0", {}).get("data_changes", 0) > 10 and rows["351"]["data_changes"] == 0)
    one = service(ws, "get_monitor", interface=IFNAME, ids="350-35F")
    check("get_monitor: id range", {r["id"] for r in one["interfaces"][0]["ids"]} == {"351", "355", "356", "359", "35C", "35E"})
    trace = service(ws, "get_trace", interface=name, ids="35E", limit=3)
    frames = trace["frames"]
    check("get_trace: newest first", len(frames) == 3 and frames[0]["time"] > frames[1]["time"] > frames[2]["time"]
          and all(f["data"] == "50 59 4C 4F 4E 20 20 20" for f in frames), str(frames[:1]))
    more = service(ws, "get_trace", interface=name, ids="35E", limit=2, before=trace["next_before"])
    check("get_trace: paging", more["frames"] and more["frames"][0]["seq"] < frames[-1]["seq"])
    recent = service(ws, "get_trace", interface=name, seconds=0.5, limit=2000)
    check("get_trace: last seconds", 20 <= len(recent["frames"]) <= 60, f"{len(recent['frames'])} frames in 0.5 s")
    bad = service(ws, "get_trace", interface="nope")
    check("get_trace: unknown interface explained", "__error__" in bad and "nope" in json.dumps(bad), json.dumps(bad)[:160])
    bad = service(ws, "get_monitor", ids="300-2FF")
    check("bad id list explained", "__error__" in bad, json.dumps(bad)[:160])
    desc = service(ws, "describe")
    check("describe", desc["integration"] == "woow_can" and any(i["name"] == name for i in desc["interfaces"]))

    # ---- send and request / response ---------------------------------------------------
    sent = service(ws, "send", interface=name, frame="7DF#02010CCCCCCCCC", wait_id="7E8", wait_ms=500,
                   note="live check: OBD request")
    check("send with reply", sent and sent.get("reply", {}).get("data") == "04 41 0C 1A F8 CC CC CC",
          json.dumps(sent)[:200])
    old = service(ws, "send", config_entry_id=entry_id, can_id="123", data="11 22 33 44")
    check("send (0.1 fields)", old and old["sent"]["frame"] == "123#11223344", json.dumps(old)[:200])
    bad = service(ws, "send", interface=name, frame="123#112233445566778899")
    check("send: 9 bytes refused", "__error__" in bad, json.dumps(bad)[:160])
    time.sleep(0.3)
    own = service(ws, "get_trace", interface=name, ids="123", direction="tx", limit=1)
    check("own frame in trace as tx", own["frames"] and own["frames"][0]["direction"] == "tx")

    # ---- panel websocket ---------------------------------------------------------------
    snap = ws.call("woow_can/snapshot")
    check("ws snapshot", any(i["id"] == entry_id for i in snap["interfaces"]), str(snap.get("__error__", "")))
    ws.id += 1
    sub_id = ws.id
    ws.send({"id": sub_id, "type": "woow_can/monitor/subscribe", "source": entry_id, "token": "live-check"})
    batches: list[dict] = []
    deadline = time.time() + 3
    while time.time() < deadline and len(batches) < 3:
        msg = ws.recv()
        if msg.get("id") == sub_id and msg.get("type") == "event":
            batches.append(msg["event"])
    full = batches[0] if batches else {}
    check("monitor: full snapshot first", full.get("full") and len(full.get("rows", [])) >= 9,
          f"{len(full.get('rows', []))} rows")
    deltas = [b for b in batches[1:] if not b.get("full")]
    check("monitor: batches", len(deltas) == 2 and deltas[0]["seq"] == 1, str([b.get("seq") for b in batches]))
    # two unacknowledged batches: nothing more until an ack
    quiet_until = time.time() + 1.0
    extra = 0
    while time.time() < quiet_until:
        ws.sock.settimeout(max(0.05, quiet_until - time.time()))
        try:
            msg = ws.recv()
        except (TimeoutError, OSError):
            break
        if msg.get("id") == sub_id:
            extra += 1
    ws.sock.settimeout(300)
    check("monitor: waits for ack", extra == 0, f"{extra} batches without ack")
    ack = ws.call("woow_can/monitor/ack", token="live-check", seq=2)
    got = None
    deadline = time.time() + 2
    while time.time() < deadline:
        msg = ws.pending.pop(0) if ws.pending else ws.recv()
        if msg.get("id") == sub_id and msg.get("type") == "event":
            got = msg["event"]
            break
    check("monitor: resumes after ack", ack is None and got is not None and got["seq"] == 3, str(got and got.get("seq")))
    counter_row = next((r for r in (got or {}).get("rows", []) if r[1] == 0x0C0), None)
    check("monitor: changed bits of the counter", counter_row is not None and counter_row[8][:2] not in ("", "00"),
          str(counter_row))
    ws.call("unsubscribe_events", subscription=sub_id)
    page = ws.call("woow_can/trace", source=entry_id, ids="0CF00400", limit=5)
    check("ws trace", len(page["frames"]) == 5 and all(f[2] == 0x0CF00400 | 0x80000000 for f in page["frames"]),
          str(page.get("__error__", "")))

    # ---- periodic sends ----------------------------------------------------------------
    saved = service(ws, "save_periodic", interface=name, frame="321#A5", period_ms=100, count=10,
                    name="live check burst", start=True, note="live check")
    item = (saved or {}).get("periodic", {})
    check("save_periodic + start", item.get("running") is True, json.dumps(saved)[:200])
    time.sleep(1.6)
    listed = service(ws, "list_periodic")
    mine = next((p for p in listed["periodic"] if p["id"] == item.get("id")), {})
    check("periodic stops after count", mine.get("running") is False and mine.get("sent") == 10
          and mine.get("stopped_by") == "count", json.dumps(mine)[:200])
    burst = service(ws, "get_trace", interface=name, ids="321", limit=20)
    times = [f["time"] for f in burst["frames"]]
    gaps = [round(a - b, 3) for a, b in zip(times, times[1:])]
    check("periodic: 10 frames ~100 ms apart", len(times) == 10 and all(0.08 <= g <= 0.12 for g in gaps), str(gaps))
    service(ws, "control_periodic", item=item.get("id", "?"), action="delete", note="live check cleanup")
    check("periodic deleted", all(p["id"] != item.get("id") for p in service(ws, "list_periodic")["periodic"]))

    # ---- events --------------------------------------------------------------------------
    res = ws.call("woow_can/interface/events", entry_id=entry_id, event_filter="35E")
    check("event filter set live", res is None, str(res))
    time.sleep(0.5)
    still = [e for e in entries() if e["entry_id"] == entry_id][0]
    check("no reload for the event filter", still["state"] == "loaded")
    ws.id += 1
    ev_id = ws.id
    ws.send({"id": ev_id, "type": "subscribe_events", "event_type": "woow_can_frame"})
    events: list[dict] = []
    deadline = time.time() + 2.6
    while time.time() < deadline:
        ws.sock.settimeout(max(0.05, deadline - time.time()))
        try:
            msg = ws.recv()
        except (TimeoutError, OSError):
            break
        if msg.get("id") == ev_id and msg.get("type") == "event":
            events.append(msg["event"]["data"])
    ws.sock.settimeout(300)
    ws.call("unsubscribe_events", subscription=ev_id)
    check("events only for the filter", 2 <= len(events) <= 3 and all(e["id_hex"] == "35E" for e in events),
          f"{len(events)} events {[e.get('id_hex') for e in events]}")
    ws.call("woow_can/interface/events", entry_id=entry_id, event_filter="")

    # ---- captures --------------------------------------------------------------------------
    rec = service(ws, "capture", interface=name, action="start", note="live check")
    check("capture start", rec and rec.get("recording", "").endswith(".log"), json.dumps(rec)[:160])
    time.sleep(2.5)
    stop = service(ws, "capture", interface=name, action="stop", note="live check")
    check("capture stop", stop and stop.get("frames", 0) > 100, json.dumps(stop)[:160])
    listed = service(ws, "list_captures")
    file = next((c for c in listed["captures"] if c["name"] == rec.get("recording")), None)
    check("capture listed", file is not None and file["size"] > 1000, json.dumps(file))
    text = http_get(f"/woow_can/captures/{rec.get('recording')}")
    lines = text.splitlines()
    check("capture download", len(lines) == stop.get("frames") and lines[0].startswith("(") and IFNAME in lines[0],
          f"{len(lines)} lines, first: {lines[0] if lines else ''}")
    opened = ws.call("woow_can/capture/control", action="open", name=rec.get("recording"))
    src = (opened.get("sources") or [{}])[0] if isinstance(opened, dict) else {}
    check("capture opened offline", src.get("frames") == len(lines), json.dumps(opened)[:200])
    if src.get("id"):
        page = ws.call("woow_can/trace", source=src["id"], limit=3)
        check("offline trace", len(page.get("frames", [])) == 3)
        ws.call("woow_can/capture/control", action="close", source=src["id"])
    export = http_get(f"/woow_can/export/{entry_id}?ids=35E")
    check("export buffer", export.count("\n") >= 3 and all(" 35E#" in l for l in export.splitlines()),
          f"{export.count(chr(10))} lines")
    deleted = ws.call("woow_can/capture/control", action="delete", name=rec.get("recording"))
    check("capture deleted", deleted == {} or deleted is None, str(deleted))

    # ---- clear, activity -------------------------------------------------------------
    service(ws, "clear_monitor", interface=name, note="live check")
    after = service(ws, "get_monitor", interface=name)["interfaces"][0]
    check("clear_monitor", after["frames"] < 300, f"{after['frames']} frames since clear")
    act = service(ws, "get_activity", limit=20)["activity"]
    kinds = {a["action"] for a in act}
    check("activity log", {"send", "save_periodic", "start_capture", "stop_capture", "clear_monitor"} <= kinds,
          ",".join(sorted(kinds)))

    if REMOVE:
        rest("DELETE", f"/config/config_entries/entry/{entry_id}")
        check("interface removed", all(e["entry_id"] != entry_id for e in entries()))
    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
