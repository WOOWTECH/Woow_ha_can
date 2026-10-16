"""Signal codec, DBC reading and multi-frame transports (stdlib only, no Home Assistant needed)."""

from __future__ import annotations

import struct

import pytest

from custom_components.woow_can import dbc
from custom_components.woow_can.signals import (
    DefinitionError,
    FastPacket,
    J1939Transport,
    Message,
    Signal,
    decode_dm1,
    j1939_pgn,
    number,
)

EFF = 0x80000000


def fb(text: str) -> bytes:
    return bytes.fromhex(text.replace(" ", ""))


def test_intel_and_motorola_bits():
    data = fb("12 34 56 78 9A BC DE F0")
    intel = Signal("a", 4, 12)  # bits 4..15, little endian: 0x341
    assert intel.raw(data) == (int.from_bytes(data, "little") >> 4) & 0xFFF == 0x341
    motorola = Signal("b", 7, 16, byte_order="big")  # byte 0 bit 7 down through byte 1: 0x1234
    assert motorola.raw(data) == 0x1234
    nibble = Signal("c", 11, 4, byte_order="big")  # low nibble of byte 1
    assert nibble.raw(data) == 0x4
    across = Signal("d", 3, 8, byte_order="big")  # byte 0 bits 3..0 then byte 1 bits 7..4: 0x23
    assert across.raw(data) == 0x23
    assert Signal("e", 56, 16).raw(data) is None  # beyond the frame: no data


def test_signed_float_ascii_and_scaling():
    data = struct.pack("<hhh", 5120, -253, -55)
    assert Signal("v", 0, 16, signed=True, factor=0.01).decode_raw(data)[1] == 51.2
    assert Signal("i", 16, 16, signed=True, factor=0.1).decode_raw(data)[1] == -25.3
    f32 = Signal("f", 0, 32, kind="float")
    assert f32.decode_raw(struct.pack(">f", 1.5)[::-1])[1] == 1.5  # Intel: little-endian float
    f64 = Signal("g", 7, 64, kind="float", byte_order="big")
    assert f64.decode_raw(struct.pack(">d", -2.25))[1] == -2.25
    text = Signal("t", 0, 64, kind="ascii")
    assert text.decode_raw(b"PYLON   ")[1] == "PYLON" and text.decode_raw(b"BYD\0\0\0\0\0")[1] == "BYD"
    with pytest.raises(DefinitionError):
        Signal("x", 3, 16, kind="ascii")  # not byte aligned
    with pytest.raises(DefinitionError):
        Signal("x", 0, 16, kind="float")


def test_invalid_rules():
    j = Signal("rpm", 24, 16, factor=0.125, invalid="j1939")
    assert j.decode_raw(fb("00 00 00 FF FF 00 00 00"))[1] is None  # n/a, not 8191.875 rpm
    assert j.decode_raw(fb("00 00 00 FF FA 00 00 00"))[1] == 0xFAFF * 0.125
    two = Signal("sw", 0, 2, invalid="j1939")
    assert [two.decode_raw(bytes([v]))[1] for v in range(4)] == [0, 1, None, None]
    n2k_u = Signal("soc", 0, 8, invalid="n2k")
    assert n2k_u.decode_raw(b"\xff")[1] is None and n2k_u.decode_raw(b"\xfe")[1] is None and n2k_u.decode_raw(b"\x64")[1] == 100
    n2k_s = Signal("i", 0, 16, signed=True, invalid="n2k")
    assert n2k_s.decode_raw(fb("FF 7F"))[1] is None and n2k_s.decode_raw(fb("FE 7F"))[1] is None
    sma_s = Signal("i", 0, 16, signed=True, invalid="sma")
    assert sma_s.decode_raw(fb("00 80"))[1] is None and sma_s.decode_raw(fb("01 80"))[1] == -32767
    assert Signal("u", 0, 16, invalid="sma").decode_raw(fb("FF FF"))[1] is None
    pair = Signal("p", 0, 2, invalid=[0, 3])
    assert [pair.decode_raw(bytes([v]))[1] for v in range(4)] == [None, 1, 2, None]
    labelled = Signal("s", 0, 2, values={3: "n/a"}, invalid="j1939")
    assert labelled.decode_raw(b"\x03")[1] == "n/a"  # a value table wins over the rule


def test_derived_values():
    msg = Message.from_dict({"name": "M", "can_id": "123", "signals": [
        {"name": "V", "start": 0, "length": 16, "factor": 0.01, "signed": True},
        {"name": "I", "start": 16, "length": 16, "factor": 0.1, "signed": True},
        {"name": "P", "start": 0, "length": 0, "derive": {"op": "product", "of": ["V", "I"]}},
        {"name": "A", "start": 32, "length": 1},
        {"name": "B", "start": 33, "length": 1},
        {"name": "Any", "start": 0, "length": 0, "derive": {"op": "any", "of": ["A", "B"]}},
        {"name": "NZ", "start": 0, "length": 0, "derive": {"op": "nonzero", "of": ["I"]}},
        {"name": "Here", "start": 0, "length": 0, "derive": {"op": "present"}},
    ]})
    values = msg.decode(struct.pack("<hhB", 5000, -100, 0b10))
    assert values == {"V": 50.0, "I": -10.0, "P": -500.0, "A": 0, "B": 1, "Any": 1, "NZ": 1, "Here": 1}
    assert msg.decode(struct.pack("<hhB", 5000, 0, 0))["Any"] == 0
    with pytest.raises(DefinitionError):
        Message.from_dict({"name": "M", "can_id": "1", "signals": [
            {"name": "P", "start": 0, "length": 0, "derive": {"op": "product", "of": ["missing"]}}]})


def test_multiplexing_and_building():
    obd = Message.from_dict({"name": "OBD2_7E8", "can_id": "7E8", "signals": [
        {"name": "service", "start": 11, "length": 4, "byte_order": "big", "multiplexor": True},
        {"name": "pid", "start": 23, "length": 8, "byte_order": "big", "multiplexor": True,
         "mux_by": "service", "mux_values": [[1, 1]]},
        {"name": "rpm", "start": 31, "length": 16, "byte_order": "big", "factor": 0.25, "unit": "rpm",
         "mux_by": "pid", "mux_values": [[12, 12]]},
        {"name": "speed", "start": 31, "length": 8, "byte_order": "big", "mux_by": "pid", "mux_values": [[13, 13]]},
    ]})
    assert obd.decode(fb("04 41 0C 1A F8 CC CC CC")) == {"service": 1, "pid": 12, "rpm": 1726.0}
    assert obd.decode(fb("03 41 0D 32 AA AA AA AA")) == {"service": 1, "pid": 13, "speed": 50}
    built = obd.build({"rpm": 1726})
    assert obd.decode(built)["rpm"] == 1726.0 and built[1] & 0x0F == 1 and built[2] == 0x0C
    plain = Message.from_dict({"name": "M", "can_id": "123", "signals": [
        {"name": "v", "start": 8, "length": 12, "factor": 0.5, "offset": -10, "minimum": -10, "maximum": 2000,
         "start_value": 20}]})
    assert plain.decode(plain.build({}))["v"] == 0.0  # start value 20 -> 20 x 0.5 - 10
    assert plain.decode(plain.build({"v": 100}, base=bytes(8)))["v"] == 100.0
    with pytest.raises(DefinitionError):
        plain.build({"v": 5000})


def test_matching():
    eec1 = Message.from_dict({"name": "EEC1", "pgn": 61444, "signals": []})
    assert eec1.matches(0x0CF00400 | EFF) and eec1.matches(0x18F00417 | EFF) and not eec1.matches(0x18FEF100 | EFF)
    only = Message.from_dict({"name": "EEC1", "pgn": "61444", "source": "sa", "signals": []}, {"sa": "00"})
    assert only.matches(0x0CF00400 | EFF) and not only.matches(0x0CF00401 | EFF)
    anyone = Message.from_dict({"name": "EEC1", "pgn": 61444, "source": "sa", "signals": []}, {"sa": ""})
    assert anyone.source is None
    hb = Message.from_dict({"name": "HB", "can_id": "0x700 + node", "extended": False, "cycle_ms": "period",
                            "signals": []}, {"node": 5, "period": 2000})
    assert hb.can_id == 0x705 and hb.timeout == 6.0 and hb.matches(0x705) and not hb.matches(0x705 | EFF)
    masked = Message.from_dict({"name": "M", "can_id": "7E0", "id_mask": "7F0", "signals": []})
    assert masked.matches(0x7E8) and not masked.matches(0x7F0)
    filtered = Message.from_dict({"name": "N", "pgn": 127508, "filters": [{"byte": 0, "value": "inst"}],
                                  "signals": []}, {"inst": 3})
    assert filtered.matches(0x19F21423 | EFF, b"\x03") and not filtered.matches(0x19F21423 | EFF, b"\x00")
    assert Message.from_dict({"name": "X", "can_id": "18FF50E5", "signals": []}).extended
    assert not Message.from_dict({"name": "X", "can_id": "356", "signals": []}).extended
    assert j1939_pgn(0x19F21423) == 127508 and j1939_pgn(0x18EAFF00) == 59904
    assert number("0x700 + n", {"n": 1}) == 0x701 and number("7E8") == 0x7E8 and number(17) == 17
    with pytest.raises(DefinitionError):
        number("n + 1", {})


def test_dm1_and_transports():
    one = decode_dm1(fb("04 FF 64 00 01 03 FF FF"))
    assert one["amber_warning_lamp"] is True and one["dtcs"] == [
        {"spn": 100, "fmi": 1, "occurrences": 3, "conversion_method": 0}]
    assert decode_dm1(fb("00 FF 00 00 00 00 FF FF"))["dtc_count"] == 0  # no active fault
    tp = J1939Transport()
    assert tp.feed(1.0, 0x1CECFF00 | EFF, fb("20 0A 00 02 FF CA FE 00")) is None
    assert tp.feed(1.05, 0x1CEBFF00 | EFF, fb("01 14 FF 64 00 01 03 6E")) is None
    pgn, sa, payload = tp.feed(1.1, 0x1CEBFF00 | EFF, fb("02 00 00 01 FF FF FF FF"))
    assert (pgn, sa, len(payload)) == (65226, 0, 10) and decode_dm1(payload)["dtc_count"] == 2
    tp.feed(2.0, 0x1CECFF00 | EFF, fb("20 0A 00 02 FF CA FE 00"))
    tp.feed(2.05, 0x1CEBFF00 | EFF, fb("01 14 FF 64 00 01 03 6E"))
    assert tp.feed(3.0, 0x1CEBFF00 | EFF, fb("02 00 00 01 FF FF FF FF")) is None  # gap > 750 ms: dropped
    fp = FastPacket()
    assert fp.feed(0x19F21223 | EFF, fb("40 09 52 01 00 64 FF 60")) is None
    assert fp.feed(0x19F21223 | EFF, fb("41 32 A5 00 FF FF FF FF")) == fb("52 01 00 64 FF 60 32 A5 00")
    fp.feed(0x19F21223 | EFF, fb("60 09 52 01 00 64 FF 60"))
    assert fp.feed(0x19F21223 | EFF, fb("42 32 A5 00 FF FF FF FF")) is None  # wrong sequence: dropped


DBC_TEXT = r'''VERSION ""
NS_ :
    CM_
    BA_DEF_
BS_:
BU_: BMS INV
BO_ 849 BMS_351_Limits: 8 BMS
 SG_ ChargeVoltageLimit : 0|16@1+ (0.1,0) [0|6553.5] "V" INV
 SG_ ChargeCurrentLimit : 16|16@1- (0.1,0) [-3276.8|3276.7] "A" INV
BO_ 858 SMA_35A: 8 BMS
 SG_ AL_General : 0|2@1+ (1,0) [0|3] "" INV
BO_ 2364540158 EEC1: 8 Vector__XXX
 SG_ EngineSpeed : 24|16@1+ (0.125,0) [0|8031.875] "rpm" Vector__XXX
BO_ 2024 OBD2: 8 Vector__XXX
 SG_ service M : 11|4@0+ (1,0) [0|15] "" Vector__XXX
 SG_ pid m1M : 23|8@0+ (1,0) [0|255] "" Vector__XXX
 SG_ rpm m12 : 31|16@0+ (0.25,0) [0|16383.75] "rpm" Vector__XXX
BO_ 1280 FLOATS: 8 Vector__XXX
 SG_ Temp : 0|32@1- (1,0) [0|0] "degC" Vector__XXX
BO_ 3221225472 VECTOR__INDEPENDENT_SIG_MSG: 0 Vector__XXX
 SG_ Orphan : 0|8@1+ (1,0) [0|0] "" Vector__XXX
CM_ BO_ 849 "Limits; two
lines";
CM_ SG_ 849 ChargeCurrentLimit "positive = charging";
BA_DEF_ BO_ "GenMsgCycleTime" INT 0 65535;
BA_DEF_ BO_ "VFrameFormat" ENUM "StandardCAN","ExtendedCAN","reserved","J1939PG";
BA_DEF_DEF_ "GenMsgCycleTime" 0;
BA_ "GenMsgCycleTime" BO_ 849 1000;
BA_ "VFrameFormat" BO_ 2364540158 3;
BA_ "GenSigStartValue" SG_ 849 ChargeVoltageLimit 540;
VAL_ 858 AL_General 0 "no info" 1 "raised" 2 "cleared" 3 "no info" ;
SIG_VALTYPE_ 1280 Temp : 1;
SG_MUL_VAL_ 2024 rpm pid 12-12;
SG_MUL_VAL_ 2024 pid service 1-1;
EV_ Unknown: 0 [0|0] "" 0 0 DUMMY_NODE_VECTOR0 Vector__XXX;
'''


def test_dbc_subset():
    parsed = dbc.parse(DBC_TEXT.encode("cp1252"))
    report = parsed.report()
    assert report["messages"] == 5 and report["warnings"] == [] and report["nodes"] == ["BMS", "INV"]
    assert report["skipped_statements"] >= 1  # EV_
    msgs = {m["name"]: Message.from_dict(m) for m in parsed.messages}
    limits = msgs["BMS_351_Limits"]
    assert limits.cycle_ms == 1000 and limits.comment == "Limits; two\nlines"
    assert limits.by_name["ChargeCurrentLimit"].comment == "positive = charging"
    assert limits.decode(limits.build({}))["ChargeVoltageLimit"] == 54.0  # start value 540
    assert msgs["SMA_35A"].decode(b"\x01" + bytes(7)) == {"AL_General": "raised"}
    eec1 = msgs["EEC1"]
    assert eec1.pgn == 61444 and eec1.matches(0x0CF00401 | EFF) and eec1.by_name["EngineSpeed"].invalid == "j1939"
    assert msgs["OBD2"].decode(fb("04 41 0C 1A F8 CC CC CC"))["rpm"] == 1726.0
    assert msgs["FLOATS"].decode(struct.pack("<f", -12.5) + bytes(4))["Temp"] == -12.5
    again = dbc.parse(dbc.dump(list(msgs.values())))
    assert again.report()["messages"] == 5 and again.warnings == []
    for name, msg in msgs.items():
        twin = Message.from_dict(next(m for m in again.messages if m["name"] == name))
        for data in (fb("04 41 0C 1A F8 CC CC CC"), fb("11 22 33 44 55 66 77 88")):
            assert twin.decode(data) == msg.decode(data), name


def test_dbc_tolerates_junk():
    parsed = dbc.parse("BO_ 100 Good: 2 X\n SG_ a : 0|8@1+ (1,0) [0|0] \"\" X\n SG_ broken line\nGARBAGE;\n")
    assert len(parsed.messages) == 1 and parsed.warnings and parsed.skipped >= 1
