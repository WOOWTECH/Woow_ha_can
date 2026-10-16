"""End-to-end check of the log formats and the reverse engineering tools on a live Home Assistant.

Run in the SSH add-on next to wsclient.py, with tools/sim/can_sim.py running on the virtual interface
(see can_live_check.py):
    python3 analysis_check.py VCAN0
Records and converts a capture (ASC, CSV, pcap), uploads an ASC file and opens it, exports the buffer as
ASC, then uses bit_activity, find_signal (the battery voltage on 0x356), guided_capture (the simulator's
door on 0x3C0, "opened" with 6F0#01) and add_signal, and removes what it made.
"""

from __future__ import annotations

import json
import struct
import sys
import time
import urllib.request

from wsclient import TOKEN, WS, rest

NAME = sys.argv[1] if len(sys.argv) > 1 else "VCAN0"
results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> bool:
    results.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail else ""), flush=True)
    return bool(ok)


def service(ws: WS, _service: str, **data):
    res = ws.call("call_service", domain="woow_can", service=_service, service_data=data, return_response=True)
    if isinstance(res, dict) and "__error__" in res:
        return res
    return res.get("response")


def http(path: str, body: bytes | None = None) -> bytes:
    req = urllib.request.Request("http://supervisor/core/api" + path, data=body, method="POST" if body else "GET",
                                 headers={"Authorization": "Bearer " + TOKEN})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def row(ws: WS, can_id: str) -> dict:
    mon = service(ws, "get_monitor", interface=NAME, ids=can_id)
    rows = mon["interfaces"][0]["ids"]
    return next((r for r in rows if r["direction"] == "rx"), {})


def volts(r: dict) -> float:
    data = bytes.fromhex(r["data"].replace(" ", ""))
    return round(int.from_bytes(data[:2], "little") * 0.01, 2)


def main() -> None:
    ws = WS()
    entry = next(e for e in rest("GET", "/config/config_entries/entry")
                 if e["domain"] == "woow_can" and e["title"] == NAME)
    entry_id = entry["entry_id"]
    made: list[str] = []

    # ---- formats -----------------------------------------------------------------------------
    rec = service(ws, "capture", interface=NAME, action="start", note="analysis check")
    time.sleep(2.0)
    stop = service(ws, "capture", interface=NAME, action="stop", note="analysis check")
    log = rec.get("recording", "")
    made.append(log)
    frames = stop.get("frames", 0)
    check("recorded", frames > 100, f"{frames} frames")
    listed = service(ws, "list_captures")
    check("list_captures names the formats", listed.get("writable") == ["log", "asc", "csv", "pcap"]
          and "trc" in listed.get("readable", []), json.dumps({k: listed.get(k) for k in ("readable", "writable")}))
    for fmt in ("asc", "csv", "pcap"):
        conv = service(ws, "convert_capture", file=log, format=fmt, note="analysis check")
        cap = (conv or {}).get("capture", {})
        made.append(cap.get("name", ""))
        check(f"convert to {fmt}", cap.get("frames") == frames and cap.get("name", "").endswith("." + fmt),
              json.dumps(conv)[:200])
        body = http(f"/woow_can/captures/{cap.get('name')}")
        if fmt == "asc":
            lines = body.decode().splitlines()
            n = sum(1 for line in lines if " Rx " in line or " Tx " in line)
            check("ASC download", lines[0].startswith("date ") and n == frames, f"{n} frame lines")
        elif fmt == "csv":
            lines = body.decode().splitlines()
            check("CSV download", lines[0].startswith("Time Stamp,ID,Extended") and len(lines) - 1 == frames,
                  f"{len(lines) - 1} rows")
        else:
            count, pos = 0, 24
            while pos + 16 <= len(body):
                incl = struct.unpack_from("<I", body, pos + 8)[0]
                pos += 16 + incl
                count += 1
            check("pcap download", body[:4] == b"\xd4\xc3\xb2\xa1" and count == frames, f"{count} records")
    again = service(ws, "convert_capture", file=log, format="asc", note="analysis check")
    second = (again or {}).get("capture", {}).get("name", "")
    made.append(second)
    check("a second conversion gets its own name", second.endswith("-2.asc"), second)
    asc = ("date Thu Oct 16 02:30:00.000 pm 2026\nbase hex  timestamps absolute\ninternal events logged\n"
           "Begin Triggerblock Thu Oct 16 02:30:00.000 pm 2026\n   0.000000 Start of measurement\n"
           "   0.010000 1  123             Rx   d 2 11 22\n   0.020000 1  18FF50E5x       Rx   d 1 01\n"
           "   0.030000 2  456             Tx   d 1 02\nEnd TriggerBlock\n")
    up = json.loads(http("/woow_can/captures?name=analysis_check.asc", asc.encode()))
    made.append(up.get("name", ""))
    check("upload keeps the .asc name", up.get("name") == "analysis_check.asc", json.dumps(up))
    opened = ws.call("woow_can/capture/control", action="open", name="analysis_check.asc")
    sources = opened.get("sources", []) if isinstance(opened, dict) else []
    check("ASC opened per channel", sorted((s["port"], s["frames"], s.get("format")) for s in sources)
          == [("ch1", 2, "asc"), ("ch2", 1, "asc")], json.dumps(opened)[:300])
    for src in sources:
        ws.call("woow_can/capture/control", action="close", source=src["id"])
    export = http(f"/woow_can/export/{entry_id}?ids=35E&format=asc").decode().splitlines()
    check("export buffer as ASC", export[0].startswith("date ") and any(" 35E " in line for line in export),
          f"{len(export)} lines")
    bad = service(ws, "convert_capture", file="nope.log", format="asc")
    check("convert: missing file explained", "__error__" in bad, json.dumps(bad)[:160])

    # ---- bit activity ------------------------------------------------------------------------
    bits = service(ws, "bit_activity", interface=NAME, can_id="0C0", seconds=2)
    changing = {b["start"]: b for b in bits.get("changing_bits", [])}
    check("bit_activity: counter bit 0 changes every frame", changing.get(0, {}).get("change_rate", 0) > 0.95,
          json.dumps(changing.get(0)))
    check("bit_activity: bytes 1-2 constant", not [s for s in changing if 8 <= s < 24]
          and bits["bytes"][1] == {"min": 0x10, "max": 0x10, "distinct": 1}, json.dumps(bits["bytes"][:3]))

    # ---- find the battery voltage ----------------------------------------------------------------
    found = None
    for _ in range(3):
        value = volts(row(ws, "356"))
        res = service(ws, "find_signal", interface=NAME, action="start", value=value, tolerance=0.004, limit=200)
        found = next((c for c in res.get("candidates", []) if c["id"] == "356" and c["start"] == 0
                      and c["length"] == 16 and c["byte_order"] == "little" and c["factor"] == 0.01), None)
        if found:
            break
    check("find_signal: start finds 0x356 bytes 0-1 x 0.01", found is not None,
          f"{res.get('left')} candidates for {value} V")
    first = res.get("left", 0)
    narrowed = None
    for _ in range(3):
        before = row(ws, "356")["data"]
        deadline = time.time() + 20
        while time.time() < deadline and (r := row(ws, "356"))["data"] == before:
            time.sleep(0.1)
        if volts(r) != value:
            narrowed = service(ws, "find_signal", interface=NAME, action="narrow", mode="equals", value=volts(r),
                               tolerance=0.004, limit=5)
            break
    top = (narrowed or {}).get("candidates", [{}])[0]
    fields = {(c["id"], c["start"], c["length"], c["byte_order"]) for c in (narrowed or {}).get("candidates", [])}
    check("find_signal: narrowing leaves the voltage on top",
          (top.get("id"), top.get("start"), top.get("length"), top.get("factor")) == ("356", 0, 16, 0.01)
          and narrowed["left"] <= first and len(fields) <= 3,
          f"{first} -> {narrowed and narrowed['left']}: {sorted(fields)}")
    status = service(ws, "find_signal", interface=NAME, action="status", limit=1)
    check("find_signal: status keeps the steps", len(status.get("steps", [])) == 2, json.dumps(status.get("steps")))
    service(ws, "find_signal", interface=NAME, action="clear")

    # ---- guided capture: the door, opened and closed twice -------------------------------------------
    service(ws, "send", interface=NAME, frame="6F0#00", note="analysis check: door closed")
    time.sleep(0.5)
    g = service(ws, "guided_capture", interface=NAME, action="start", label="door closed")
    check("guided: started", g.get("running") and g["phases"][0]["label"] == "door closed", json.dumps(g)[:200])
    time.sleep(2.5)
    for state in (1, 0, 1, 0):
        service(ws, "guided_capture", interface=NAME, action="next", label="door open" if state else "door closed")
        time.sleep(0.3)  # a person opens / closes the door a moment after pressing next
        service(ws, "send", interface=NAME, frame=f"6F0#0{state}", note="analysis check: the simulated door")
        time.sleep(2.5)
    done = service(ws, "guided_capture", interface=NAME, action="finish")
    rows = {r["id"]: r for r in done.get("results", [])}
    door = rows.get("3C0", {})
    flips = [(f["byte"], f["bit"], f["idle"], f["action"], f["confirmed"]) for f in door.get("flipped", [])]
    check("guided: the door bit, confirmed", flips == [(0, 2, 0, 1, True)], json.dumps(door)[:300])
    check("guided: the door ranks first", done.get("results", [{}])[0].get("id") == "3C0",
          ",".join(f"{r['id']}:{r['score']}" for r in done.get("results", [])[:5]))
    check("guided: the counter is recognised", set(range(8, 13)) <= set(door.get("counter_bits", [])),
          json.dumps(door.get("counter_bits")))
    check("guided: the command frame (sent in every phase but the first) is no hint", "6F0 (tx)" not in rows,
          json.dumps(rows.get("6F0 (tx)")))
    check("guided: five phases reported", [p["label"] for p in done.get("phases", [])]
          == ["door closed", "door open", "door closed", "door open", "door closed"] and not done.get("running"),
          json.dumps([p["label"] for p in done.get("phases", [])]))
    bad = service(ws, "guided_capture", interface=NAME, action="next")
    check("guided: next after finish explained", "__error__" in bad, json.dumps(bad)[:160])

    # ---- the light, by guided capture with two phases, into a device -----------------------------
    service(ws, "guided_capture", interface=NAME, action="start", label="light off")
    time.sleep(2)
    service(ws, "guided_capture", interface=NAME, action="next", label="light on")
    service(ws, "send", interface=NAME, frame="6F0#02", note="analysis check: light on")
    time.sleep(2.5)
    done = service(ws, "guided_capture", interface=NAME, action="finish")
    body = next((r for r in done.get("results", []) if r["id"] == "3C0"), {})
    check("guided: the light bit and its level byte, no counter bits",
          [(f["byte"], f["bit"]) for f in body.get("flipped", []) if f["byte"] != 4] == [(0, 5)]
          and [(s["byte"], s["action"]) for s in body.get("shifted_bytes", [])] == [(4, [80, 80])],
          json.dumps(body)[:300])
    added = service(ws, "add_signal", interface=NAME, can_id="3C0", name="Light", start=5, length=1,
                    device_name="Analysis check body", message="Body", note="analysis check")
    dev = (added or {}).get("device", {})
    check("add_signal: new device", dev.get("name") == "Analysis check body", json.dumps(added)[:300])
    added = service(ws, "add_signal", interface=NAME, can_id="3C0", name="Cabin temperature", start=16, length=16,
                    factor=0.1, unit="°C", device="Analysis check body", note="analysis check")
    dev = (added or {}).get("device", {})
    time.sleep(2.5)
    view = service(ws, "get_device", device="Analysis check body")
    status = (view or {}).get("device", {}).get("status", [])
    signals = {s["name"]: s for s in (status[0]["signals"] if status else [])}
    check("add_signal: two signals, one message", len(status) == 1 and set(signals) == {"Light", "Cabin temperature"}
          and signals["Light"]["platform"] == "binary_sensor", json.dumps(status)[:400])
    states = {name: rest("GET", f"/states/{s['entity_id']}")["state"] for name, s in signals.items() if s["entity_id"]}
    check("add_signal: entities with values", states == {"Light": "on", "Cabin temperature": "21.5"}, json.dumps(states))
    dup = service(ws, "add_signal", interface=NAME, can_id="3C0", name="Light", start=5, length=1,
                  device="Analysis check body")
    check("add_signal: duplicate refused", "__error__" in dup, json.dumps(dup)[:160])

    # ---- clean up ----------------------------------------------------------------------------------
    service(ws, "send", interface=NAME, frame="6F0#00", note="analysis check: light off")
    service(ws, "delete_device", device="Analysis check body", note="analysis check cleanup")
    for name in [m for m in made if m]:
        ws.call("woow_can/capture/control", action="delete", name=name)
    left = {c["name"] for c in service(ws, "list_captures")["captures"]}
    check("cleaned up", not (set(made) & left) and "__error__" in service(ws, "get_device", device="Analysis check body"),
          ",".join(sorted(set(made) & left)))
    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
