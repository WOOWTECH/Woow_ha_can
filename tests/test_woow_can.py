"""Unit tests of WOOW CAN's logic (no Home Assistant instance or CAN hardware needed)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from custom_components.woow_can import SEND_SCHEMA
from custom_components.woow_can import config_flow as cf
from custom_components.woow_can.can_port import (
    CAN_EFF_FLAG,
    CAN_ERR_FLAG,
    CAN_RTR_FLAG,
    F_BRS,
    F_ERR,
    F_FD,
    F_LOCAL,
    F_OWN,
    CanFrame,
    IdMatcher,
    decode_error,
    frame_text,
    parse_filters,
    parse_id,
)
from custom_components.woow_can.capture import (
    TraceBuffer,
    export_text,
    log_line,
    parse_log_line,
    safe_name,
    trace_matcher,
)
from custom_components.woow_can.const import CAN_DEFAULTS
from custom_components.woow_can.hub import BusLoad, ErrorLog, EventGate
from custom_components.woow_can.monitor import TX_KEY, Monitor, Viewer
from custom_components.woow_can.periodic import PeriodicError, PeriodicManager

HERE = Path(__file__).resolve().parents[1] / "custom_components" / "woow_can"

# A Pylontech battery talking to an inverter (setfirelabs capture, 10 x US3000)
PYLON = {
    0x351: "14 02 74 0E 74 0E CC 01",
    0x355: "0E 00 64 00",
    0x356: "02 13 00 00 4A 01",
    0x359: "00 00 00 00 0A 50 4E",
    0x35C: "C0 00",
    0x35E: "50 59 4C 4F 4E 20 20 20",
}


@pytest.mark.parametrize("text", ["123#11223344", "18FF50E5#0102", "456##1000102030405060708090A0B"])
def test_frames_round_trip(text):
    frame = CanFrame.parse(text)
    assert CanFrame.unpack(frame.pack()) == frame
    assert str(frame) == text


def test_frame_details():
    assert CanFrame.parse("123#R").rtr
    assert len(CanFrame.parse("456##1000102030405060708090A").data) == 12  # 11 bytes padded to FD length 12
    assert parse_id("7E8") == (0x7E8, False) and parse_id("18FF50E5") == (0x18FF50E5, True)
    assert CanFrame.parse("18FF50E5#0102").as_dict()["id_hex"] == "18FF50E5"
    with pytest.raises(ValueError):
        CanFrame.parse("123#112233445566778899")  # 9 bytes on classic CAN
    with pytest.raises(ValueError):
        CanFrame.parse("123#XYZ")
    with pytest.raises(ValueError):
        parse_id("G12")


def test_raw_frames():
    frame = CanFrame.parse("18FF50E5#0102")
    assert frame.raw_id == 0x18FF50E5 | CAN_EFF_FLAG
    assert CanFrame.from_raw(frame.raw_id, b"\x01\x02", 0) == frame
    assert frame_text(0x123 | CAN_RTR_FLAG, b"", 0) == "123#R"
    assert frame_text(0x456, bytes(range(12)), F_FD | F_BRS) == "456##1000102030405060708090A0B"
    assert frame_text(0x20000040 & 0x1FFFFFFF | CAN_ERR_FLAG, bytes(8), F_ERR) == "20000040#0000000000000000"


def test_filters():
    assert [(hex(i), hex(m)) for i, m in parse_filters("123, 7E0/7F0")] == [("0x123", "0x800007ff"), ("0x7e0", "0x800007f0")]
    assert parse_filters("") == []
    with pytest.raises(ValueError):
        parse_filters("XYZ")


def test_id_matcher():
    m = IdMatcher("123, 7E0/7F0, 300-30F, 18FF50E5")
    assert m(0x123) and m(0x7E8) and m(0x305) and m(0x18FF50E5 | CAN_EFF_FLAG)
    assert not m(0x124) and not m(0x310) and not m(0x123 | CAN_EFF_FLAG)  # 29-bit 0x123 is another ID
    assert IdMatcher("").empty and not IdMatcher("*").empty and IdMatcher("*")(0x7FF)
    with pytest.raises(ValueError):
        IdMatcher("30F-300")
    with pytest.raises(ValueError):
        IdMatcher("nope")


def test_error_frames():
    # controller: TX passive; then bus off; no ACK with a protocol error on transmission
    assert decode_error(0x004 | CAN_ERR_FLAG, bytes([0, 0x20, 0, 0, 0, 0, 0x80, 0])) == ["controller:tx_passive"]
    assert decode_error(0x040 | CAN_ERR_FLAG, bytes(8)) == ["bus_off"]
    assert decode_error(0x028 | CAN_ERR_FLAG, bytes([0, 0, 0x80, 0x19, 0, 0, 0, 0])) == ["protocol:on_tx", "no_ack"]
    log = ErrorLog()
    log.add(1.0, 0x004 | CAN_ERR_FLAG, bytes([0, 0x20, 0, 0, 0, 0, 128, 0]), F_ERR)
    assert log.counts == {"controller:tx_passive": 1} and log.last["tx_error_counter"] == 128


def test_monitor_rows_and_batches():
    mon = Monitor()
    sent: list[dict] = []
    viewer = Viewer(sent.append)
    mon.attach(viewer)
    for i in range(5):  # a Pylontech battery every second; the voltage low byte wanders
        for can_id, data in PYLON.items():
            raw = bytearray.fromhex(data)
            if can_id == 0x356:
                raw[0] = 0x02 + (i % 2)
            mon.add(100.0 + i, can_id, bytes(raw), 0)
    st = mon.stats[0x356]
    assert st.count == 5 and st.changes == 4 and abs(st.period - 1.0) < 1e-9
    assert mon.stats[0x351].changes == 0
    batch = mon.batch(viewer, 105.0)
    rows = {r[0]: r for r in batch["rows"]}
    assert set(rows) == set(PYLON) and batch["seq"] == 1
    assert rows[0x356][8] == "FFFFFFFFFFFF"  # a new row: every bit is news
    assert mon.batch(viewer, 105.1) is None  # nothing new
    mon.add(106.0, 0x356, bytes.fromhex("03 13 00 00 4B 01"), 0)
    assert mon.batch(viewer, 106.0)["seq"] == 2
    mon.add(107.0, 0x356, bytes.fromhex("02 13 00 00 4B 01"), 0)
    assert mon.batch(viewer, 107.0) is None  # two batches unacknowledged: wait
    viewer.acked = 2
    third = mon.batch(viewer, 107.1)
    assert third["rows"][0][8] == "010000000000"  # 03 -> 02 only
    # frames WOOW CAN sent are separate rows; other programs on this host count as received
    mon.add(108.0, 0x356, bytes(6), F_OWN)
    assert (0x356 | TX_KEY) in mon.stats
    summary = mon.summary(108.0, match=IdMatcher("356"))
    assert [r["direction"] for r in summary] == ["rx", "tx"]
    assert summary[0]["rate_hz"] == pytest.approx(0.9, abs=0.01)  # the 2 s gap before 106 s pulls the average
    mon.add(108.5, 0x356, bytes(6), F_LOCAL)
    assert mon.stats[0x356].count == 8  # 7 received before, and this one from another program
    assert mon.summary(109.0, match=IdMatcher("356"))[0]["from_this_host"] is True
    mon.clear()
    assert mon.batch(viewer, 109.0)["clear"] is True and not mon.stats


def test_monitor_limit():
    mon = Monitor(max_ids=2)
    for can_id in (1, 2, 3, 3):
        mon.add(1.0, can_id, b"", 0)
    assert len(mon.stats) == 2 and mon.overflow == 2


def test_trace_buffer_pages_and_logs():
    buf = TraceBuffer(5)
    for i in range(8):
        buf.append(1000.0 + i, 0x100 + i, bytes([i]), F_OWN if i % 2 else 0)
    buf.append(1008.5, 0x200, bytes(range(16)), F_FD | F_BRS)  # longer than 8 bytes: kept on the side
    snap = buf.snapshot()
    assert (snap.first, snap.end) == (4, 9)
    page = snap.page(limit=2)
    assert [f.seq for f in page["frames"]] == [8, 7] and page["next"] == 7
    assert page["frames"][0].data == bytes(range(16))
    more = snap.page(before=page["next"], limit=10)
    assert [f.seq for f in more["frames"]] == [6, 5, 4] and more["next"] is None
    rx_only = snap.page(match=trace_matcher(None, "rx"))
    assert [f.seq for f in rx_only["frames"]] == [8, 6, 4]
    since = snap.page(since=1006.0)
    assert [f.seq for f in since["frames"]] == [8, 7, 6]
    text = export_text(snap, "can0")
    lines = text.splitlines()
    assert lines[0] == "(0000001004.000000) can0 104#04 R" and lines[-1].endswith("200##1000102030405060708090A0B0C0D0E0F R")
    for line in lines:
        ifname, ts, raw, data, flags = parse_log_line(line)
        assert log_line(ifname, ts, raw, data, flags).strip() == line
    assert len(buf.long) == 1


def test_log_parsing():
    assert parse_log_line("(1760600000.123456) can0 123#DEADBEEF")[1:4] == (1760600000.123456, 0x123, b"\xde\xad\xbe\xef")
    _, _, raw, data, flags = parse_log_line("(1760600000.124001) can1 18FF50E5#0102030405060708 T")
    assert raw == 0x18FF50E5 | CAN_EFF_FLAG and flags == F_LOCAL and len(data) == 8
    _, _, raw, data, flags = parse_log_line("(1760600000.126000) can0 20000040#0000000000000000")
    assert flags & F_ERR and decode_error(raw, data) == ["bus_off"]
    assert parse_log_line("(1.5) can0 123#R")[2] == 0x123 | CAN_RTR_FLAG
    for junk in ("DROPCOUNT: 3", "", "can0 123 [2] 11 22", "(1.0) can0 123#112233445566778899"):
        assert parse_log_line(junk) is None
    assert safe_name("can0_20261016-210000.log") == "can0_20261016-210000.log"
    for bad in ("../x.log", ".hidden", "a b.log"):
        with pytest.raises(ValueError):
            safe_name(bad)


def test_bus_load_estimate():
    load = BusLoad()
    load.update(0.0, {"rx_packets": 0, "tx_packets": 0, "rx_bytes": 0, "tx_bytes": 0}, (0, 0, 0), 500000, 0)
    # one second of 1000 classic 8-byte frames with 11-bit IDs: 1000 * (55 + 80) bits = 27 % of 500 kbit/s
    load.update(1.0, {"rx_packets": 1000, "tx_packets": 0, "rx_bytes": 8000, "tx_bytes": 0}, (1000, 0, 0), 500000, 0)
    assert load.now == pytest.approx(27.0) and load.rx_fps == 1000 and load.peak == pytest.approx(27.0)
    # 29-bit IDs cost 25 bits more each
    load.update(2.0, {"rx_packets": 2000, "tx_packets": 0, "rx_bytes": 16000, "tx_bytes": 0}, (1000, 1000, 0), 500000, 0)
    assert load.now == pytest.approx(32.0)
    assert load.as_dict()["avg"][0] is not None


def test_event_gate():
    gate = EventGate("", 20)
    assert not gate.wants(0x123)
    gate = EventGate("350-35F", 2)
    assert gate.wants(0x356) and not gate.wants(0x360)
    assert [gate.allow() for _ in range(4)] == [True, True, False, False] and gate.dropped == 2


def test_periodic_validation():
    item = PeriodicManager.validate({"entry_id": "e1", "frame": "305#0000000000000000", "period_ms": "1000"})
    assert item.period_ms == 1000 and item.count == 0 and item.name == "305#0000000000000000"
    for raw, code in (({"entry_id": "e1", "frame": "305#00", "period_ms": 5}, "bad_period"),
                      ({"entry_id": "e1", "frame": "nope", "period_ms": 100}, "bad_frame"),
                      ({"frame": "305#00", "period_ms": 100}, "no_interface"),
                      ({"entry_id": "e1", "frame": "305#00", "period_ms": 100, "count": -1}, "bad_count")):
        with pytest.raises(PeriodicError) as err:
            PeriodicManager.validate(raw)
        assert err.value.code == code


def test_form_and_service_schema():
    import probatio
    from homeassistant.helpers import config_validation as cv

    for fd in (False, True):
        vals = {**CAN_DEFAULTS, "name": "CAN0"}
        schema = cf.can_schema(vals, True, fd)
        probatio.to_field_list(schema, custom_serializer=cv.custom_serializer)
        form = {k: (str(v) if k in ("bitrate", "dbitrate") else v) for k, v in vals.items()}
        if not fd:
            form.pop("fd"), form.pop("dbitrate")
        out = cf.coerce(schema(form))
        assert out["bitrate"] == 500000 and out["listen_only"] is True and out["event_filter"] == ""
    virtual = cf.can_schema({**CAN_DEFAULTS, "name": "VCAN0"}, True, True, virtual=True)
    probatio.to_field_list(virtual, custom_serializer=cv.custom_serializer)
    assert "bitrate" not in {str(k) for k in virtual.schema}
    assert cf.filters_error({"filters": "123, nope"}) == {"filters": "bad_filter"}
    assert cf.filters_error({"event_filter": "300-2FF"}) == {"event_filter": "bad_event_filter"}
    assert cf.filters_error({"filters": "123", "event_filter": "*"}) == {}
    sent = SEND_SCHEMA({"config_entry_id": "x", "can_id": "7DF", "data": "02 01 0C", "wait_id": "7E8", "wait_ms": 500})
    assert sent["fd"] is False and sent["wait_ms"] == 500 and sent["note"] == ""
    assert SEND_SCHEMA({"interface": "CAN0", "frame": "7DF#02010C"})["frame"] == "7DF#02010C"


def test_translations_and_service_texts_agree():
    import yaml

    en = json.loads((HERE / "translations" / "en.json").read_text(encoding="utf-8"))
    zh = json.loads((HERE / "translations" / "zh-Hant.json").read_text(encoding="utf-8"))

    def keys(d, prefix=""):
        out = set()
        for k, v in d.items():
            out |= keys(v, f"{prefix}{k}.") if isinstance(v, dict) else {prefix + k}
        return out

    assert keys(en) == keys(zh)

    def strings(d):
        for v in d.values():
            yield from strings(v) if isinstance(v, dict) else [v]

    for lang in (en, zh):  # hassfest refuses anything that looks like HTML
        assert not [t for t in strings(lang) if "<" in t or ">" in t]
    services = yaml.safe_load((HERE / "services.yaml").read_text(encoding="utf-8"))
    assert set(services) == set(en["services"])
    for name, spec in services.items():
        assert spec["name"] == en["services"][name]["name"]
        for field, config in (spec.get("fields") or {}).items():
            assert config["name"] == en["services"][name]["fields"][field]["name"], (name, field)
