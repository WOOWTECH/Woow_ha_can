"""Log file formats: round trips, hand-checked samples and (when python-can is installed) python-can's own
readers and writers for ASC, TRC and candump logs.

The modules are loaded from their files so this runs without Home Assistant installed.
"""

from __future__ import annotations

import importlib.util
import io
from pathlib import Path
import random
import struct
import sys
import types

import pytest

BASE = Path(__file__).resolve().parents[1] / "custom_components" / "woow_can"
_pkg = types.ModuleType("woow_can_pure")
_pkg.__path__ = [str(BASE)]
sys.modules.setdefault("woow_can_pure", _pkg)


def _load(name: str):
    if f"woow_can_pure.{name}" in sys.modules:
        return sys.modules[f"woow_can_pure.{name}"]
    spec = importlib.util.spec_from_file_location(f"woow_can_pure.{name}", BASE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"woow_can_pure.{name}"] = module
    spec.loader.exec_module(module)
    return module


can_port = _load("can_port")
_load("capture")
formats = _load("formats")
EFF, RTR, ERR = can_port.CAN_EFF_FLAG, can_port.CAN_RTR_FLAG, can_port.CAN_ERR_FLAG
F_FD, F_BRS, F_LOCAL, F_ERR = can_port.F_FD, can_port.F_BRS, can_port.F_LOCAL, can_port.F_ERR
T0 = 1760600000.0


def sample_frames(seed: int = 7, n: int = 300, fd: bool = True, rtr: bool = True) -> list[tuple]:
    rnd = random.Random(seed)
    out, t = [], T0
    for _ in range(n):
        t += rnd.choice((0.000250, 0.001, 0.0105, 0.1))
        extended = rnd.random() < 0.4
        raw = rnd.randrange(0x20000000) | EFF if extended else rnd.randrange(0x800)
        flags = F_LOCAL if rnd.random() < 0.2 else 0
        kind = rnd.random()
        if rtr and kind < 0.05:
            out.append((round(t, 6), raw | RTR, b"", flags))
        elif fd and kind < 0.2:
            length = rnd.choice(can_port.FD_LENGTHS[9:])
            out.append((round(t, 6), raw, bytes(rnd.randrange(256) for _ in range(length)),
                        flags | F_FD | (F_BRS if rnd.random() < 0.5 else 0)))
        else:
            out.append((round(t, 6), raw, bytes(rnd.randrange(256) for _ in range(rnd.randrange(9))), flags))
    return out


def same(a: list[tuple], b: list[tuple], tol: float = 2e-6) -> None:
    assert len(a) == len(b)
    for x, y in zip(a, b):
        assert abs(x[0] - y[0]) < tol, (x, y)
        assert x[1:] == y[1:], (x, y)


def relative(frames: list[tuple]) -> list[tuple]:
    start = frames[0][0]
    return [(f[0] - start, *f[1:]) for f in frames]


# ---- round trips -----------------------------------------------------------------------------
@pytest.mark.parametrize("fmt", ["log", "asc", "pcap"])
def test_round_trip(fmt):
    frames = sample_frames()
    data = formats.write(fmt, {"can0": frames})
    by_iface, skipped, found = formats.read_bytes(data)
    assert found == fmt and skipped == 0
    (got,) = by_iface.values()
    if fmt == "asc":  # ASC times are relative to the start, written to the microsecond
        same(relative(got), relative(frames))
    elif fmt == "pcap":  # LINKTYPE_CAN_SOCKETCAN has no direction
        same(got, [(f[0], f[1], f[2], f[3] & ~F_LOCAL) for f in frames])
    else:
        same(got, frames)


def test_round_trip_csv_classic_only():
    frames = sample_frames()
    data = formats.write("csv", {"can0": frames})
    by_iface, skipped, found = formats.read_bytes(data)
    assert found == "csv" and skipped == 0
    expected = [f for f in frames if not f[3] & (F_FD | F_ERR) and not f[1] & RTR]
    same(by_iface["bus0"], expected)


def test_two_interfaces_become_channels():
    a = [(T0 + 0.1, 0x100, b"\x01", 0), (T0 + 0.3, 0x101, b"\x02", 0)]
    b = [(T0 + 0.2, 0x200, b"\x03", 0)]
    text = formats.write("asc", {"can0": a, "can1": b}).decode()
    by_iface, _ = formats.read(text)
    assert [f[1] for f in by_iface["ch1"]] == [0x100, 0x101]
    assert [f[1] for f in by_iface["ch2"]] == [0x200]
    log = formats.write("log", {"can0": a, "can1": b}).decode().splitlines()
    assert [line.split()[1] for line in log] == ["can0", "can1", "can0"]


def test_error_frames_survive_log_and_pcap():
    frames = [(T0, ERR | 0x04, bytes([0, 0x08, 0, 0, 0, 0, 0x7F, 0]), F_ERR), (T0 + 0.5, 0x123, b"\x11", 0)]
    for fmt in ("log", "pcap"):
        by_iface, skipped, _ = formats.read_bytes(formats.write(fmt, {"can0": frames}))
        (got,) = by_iface.values()
        same(got, frames)


# ---- samples from the formats' documentation -------------------------------------------------
def test_asc_vector_sample():
    text = """date Thu Oct 16 02:30:00.000 pm 2026
base hex  timestamps absolute
internal events logged
// version 13.0.0
Begin Triggerblock Thu Oct 16 02:30:00.000 pm 2026
   0.000000 Start of measurement
   0.010000 1  123             Rx   d 8 11 22 33 44 55 66 77 88  Length = 236000 BitCount = 122 ID = 291
   0.020000 2  18FF50E5x       Tx   d 2 01 02
   0.030000 1  7DF             Rx   r 8
   0.040000 1  ErrorFrame
   0.050000 CANFD   1 Rx       456                                   1 0 9 12 01 02 03 04 05 06 07 08 09 0A 0B 0C        0    0     3000        0        0        0        0        0
   2.501000 1  Statistic: D 0 R 0 XD 0 XR 0 E 0 O 0 B 0.00%
End TriggerBlock
"""
    by_iface, skipped = formats.read(text)
    assert formats.detect(text) == "asc"
    ch1, ch2 = by_iface["ch1"], by_iface["ch2"]
    assert ch1[0][1:] == (0x123, bytes.fromhex("1122334455667788"), 0)
    assert ch2[0][1:] == (0x18FF50E5 | EFF, b"\x01\x02", F_LOCAL)
    assert ch1[1][1:] == (0x7DF | RTR, b"", 0)
    assert ch1[2][3] == F_ERR
    assert ch1[3][1:] == (0x456, bytes(range(1, 13)), F_FD | F_BRS)
    assert round(ch1[3][0] - ch1[0][0], 6) == 0.04
    assert skipped == 0  # "Start of measurement" and the statistics line are events, not frames


def test_asc_relative_and_decimal():
    text = "base dec  timestamps relative\n0.5 1  291 Rx d 2 17 255\n0.25 1  291 Rx d 2 18 0\n"
    by_iface, _ = formats.read(text, "asc")
    frames = by_iface["ch1"]
    assert [f[2] for f in frames] == [bytes([17, 255]), bytes([18, 0])]
    assert frames[0][1] == 291 and round(frames[1][0] - frames[0][0], 6) == 0.25


def test_gvret_csv_sample():
    text = ("Time Stamp,ID,Extended,Dir,Bus,LEN,D1,D2,D3,D4,D5,D6,D7,D8\n"
            "166064000,0000021A,false,Rx,0,8,FE,36,12,FE,69,05,07,AD,\n"
            "166064150,18FF50E5,true,Tx,1,3,01,02,03,00,00,00,00,00,\n")
    by_iface, skipped = formats.read(text)
    assert skipped == 0
    assert by_iface["bus0"] == [(166.064, 0x21A, bytes.fromhex("FE3612FE690507AD"), 0)]
    assert by_iface["bus1"] == [(166.06415, 0x18FF50E5 | EFF, b"\x01\x02\x03", F_LOCAL)]


@pytest.mark.parametrize("version,line", [
    ("1.0", "     1)      2850  0300  8  00 11 22 33 44 55 66 77"),
    ("1.1", "     1)      2850.8  Rx         0300  8  00 11 22 33 44 55 66 77"),
    ("1.2", "     1)      2850.8 1  Rx         0300  8  00 11 22 33 44 55 66 77"),
    ("1.3", "     1)      2850.8 1  Rx        0300 -  8    00 11 22 33 44 55 66 77"),
])
def test_trc_v1(version, line):
    text = f";$FILEVERSION={version}\n;$STARTTIME=46311.5\n;   Message Number\n{line}\n"
    by_iface, skipped = formats.read(text)
    assert formats.detect(text) == "trc" and skipped == 0
    (frame,) = by_iface["bus1"]
    assert frame[1:] == (0x300, bytes.fromhex("0011223344556677"), 0)


def test_trc_v2():
    text = """;$FILEVERSION=2.1
;$STARTTIME=46311.5
;$COLUMNS=N,O,T,B,I,d,R,L,D
      1      1059.900 DT 1      0300 Rx -  8    00 00 00 00 00 00 00 01
      2      1060.100 DT 2  18FF50E5 Tx -  2    0A 0B
      3      1061.000 FB 1      0456 Rx -  9    01 02 03 04 05 06 07 08 09 0A 0B 0C
      4      1062.000 RR 1      07DF Rx -  8
      5      1063.000 ST 1      Rx  00000000
"""
    by_iface, skipped = formats.read(text)
    bus1, bus2 = by_iface["bus1"], by_iface["bus2"]
    assert bus1[0][1:] == (0x300, bytes(7) + b"\x01", 0)
    assert bus2[0][1:] == (0x18FF50E5 | EFF, b"\x0a\x0b", F_LOCAL)
    assert bus1[1][1:] == (0x456, bytes(range(1, 13)), F_FD | F_BRS)
    assert bus1[2][1:] == (0x7DF | RTR, b"", 0)
    assert round(bus1[1][0] - bus1[0][0], 6) == 0.0011  # offsets are milliseconds
    assert skipped == 1


def test_crtd_sample():
    text = ("1542473792.462190 CXX OVMS CRTD\n"
            "1542473792.462190 1R11 4F0 00 01 02 03 04 05 06 07\n"
            "1542473792.472190 2T29 18FF50E5 0A\n"
            "1542473792.482190 R11 7E8 03 41 0C 1A\n")
    by_iface, skipped = formats.read(text)
    assert formats.detect(text) == "crtd" and skipped == 1
    assert by_iface["bus1"][0][1:] == (0x4F0, bytes(range(8)), 0)
    assert by_iface["bus2"][0][1:] == (0x18FF50E5 | EFF, b"\x0a", F_LOCAL)
    assert by_iface["bus1"][1][1:] == (0x7E8, bytes.fromhex("03410C1A"), 0)


def test_pcap_bytes_by_hand():
    data = formats.write("pcap", {"can0": [(T0 + 0.25, 0x123, b"\xde\xad", 0),
                                           (T0 + 0.5, 0x456, bytes(12), F_FD | F_BRS)]})
    assert data[:4] == b"\xd4\xc3\xb2\xa1" and struct.unpack("<I", data[20:24])[0] == 227
    sec, usec, incl, orig = struct.unpack("<IIII", data[24:40])
    assert (sec, usec, incl, orig) == (int(T0), 250000, 16, 16)
    assert data[40:56] == bytes.fromhex("00000123" "02000000" "dead000000000000")
    sec, usec, incl, _ = struct.unpack("<IIII", data[56:72])
    assert incl == 72 and data[72:80] == bytes.fromhex("00000456" "0c050000")


def test_unknown_text_is_all_skipped():
    by_iface, skipped, fmt = formats.read_bytes(b"hello\nworld\n")
    assert (by_iface, skipped, fmt) == ({}, 2, "unknown")


def test_limit_keeps_the_newest():
    frames = sample_frames(n=50, fd=False, rtr=False)
    by_iface, _ = formats.collect(("can0", f) for f in frames)
    limited, _ = formats.collect((("can0", f) for f in frames), limit=10)
    assert limited["can0"] == by_iface["can0"][-10:]


# ---- python-can (CI: pip install python-can) ---------------------------------------------------
def _messages(frames):
    can = pytest.importorskip("can")
    out = []
    for ts, raw, data, flags in frames:
        out.append(can.Message(timestamp=ts, arbitration_id=raw & can_port.CAN_EFF_MASK,
                               is_extended_id=bool(raw & EFF), is_remote_frame=bool(raw & RTR),
                               dlc=0 if raw & RTR else len(data), data=data, is_fd=bool(flags & F_FD),
                               bitrate_switch=bool(flags & F_BRS), is_rx=not flags & F_LOCAL, channel=0))
    return out


def _ours(msg) -> tuple:
    raw = msg.arbitration_id | (EFF if msg.is_extended_id else 0) | (RTR if msg.is_remote_frame else 0)
    flags = (F_FD if msg.is_fd else 0) | (F_BRS if msg.bitrate_switch else 0) | (0 if msg.is_rx else F_LOCAL)
    return msg.timestamp, raw, b"" if msg.is_remote_frame else bytes(msg.data), flags


def test_python_can_asc_both_ways(tmp_path):
    can = pytest.importorskip("can")
    frames = sample_frames(seed=11)
    path = tmp_path / "theirs.asc"
    writer = can.ASCWriter(str(path))
    for msg in _messages(frames):
        writer.on_message_received(msg)
    writer.stop()
    by_iface, skipped, fmt = formats.read_file(str(path))
    assert fmt == "asc"
    same(relative(by_iface["ch1"]), relative(frames))

    mine = tmp_path / "mine.asc"
    mine.write_bytes(formats.write("asc", {"can0": frames}))
    theirs = [_ours(m) for m in can.ASCReader(str(mine), relative_timestamp=True)]
    same(relative(theirs), relative(frames))


def test_python_can_trc(tmp_path):
    can = pytest.importorskip("can")
    frames = sample_frames(seed=12, fd=False, rtr=False)  # python-can's TRC writer skips both
    path = tmp_path / "theirs.trc"
    writer = can.TRCWriter(str(path))
    for msg in _messages(frames):
        writer.on_message_received(msg)
    writer.stop()
    by_iface, skipped, fmt = formats.read_file(str(path))
    assert fmt == "trc" and skipped == 0
    (got,) = by_iface.values()
    same(relative(got), relative(frames), tol=2e-4)  # TRC 2.1 offsets are written in 0.1 ms


def test_python_can_candump(tmp_path):
    can = pytest.importorskip("can")
    frames = sample_frames(seed=13)
    path = tmp_path / "theirs.log"
    writer = can.CanutilsLogWriter(str(path), channel="can0")
    for msg in _messages(frames):
        writer.on_message_received(msg)
    writer.stop()
    by_iface, skipped, fmt = formats.read_file(str(path))
    assert fmt == "log" and skipped == 0
    same([(f[0], f[1], f[2], f[3] & ~F_LOCAL) for f in by_iface["can0"]],
         [(f[0], f[1], f[2], f[3] & ~F_LOCAL) for f in frames])

    mine = tmp_path / "mine.log"
    mine.write_bytes(formats.write("log", {"can0": frames}))
    theirs = [_ours(m) for m in can.CanutilsLogReader(str(mine))]
    same([(f[0], f[1], f[2], f[3] & ~F_LOCAL) for f in theirs], [(f[0], f[1], f[2], f[3] & ~F_LOCAL) for f in frames])


def test_io_is_text_for_text_formats():
    assert isinstance(formats.write("asc", {"can0": []}), bytes)
    assert io.BytesIO(formats.write("pcap", {"can0": []})).read(4) == b"\xd4\xc3\xb2\xa1"


def test_convert_file_streams_every_format(tmp_path):
    a = sample_frames(seed=21, n=120)
    b = [(f[0] + 0.0001, f[1], f[2], f[3]) for f in sample_frames(seed=22, n=80, fd=False)]
    src = tmp_path / "two.log"
    src.write_bytes(formats.write("log", {"can0": a, "can1": b}))
    for fmt in ("asc", "csv", "pcap", "log"):
        dst = tmp_path / f"out.{fmt}"
        result = formats.convert_file(str(src), str(dst), fmt)
        assert result["frames"] == 200 and result["skipped"] == 0 and result["interfaces"] == ["can0", "can1"]
        by_iface, skipped, found = formats.read_file(str(dst))
        assert found == fmt and skipped == 0
        total = sum(len(v) for v in by_iface.values())
        if fmt == "csv":
            assert total == sum(1 for f in a + b if not f[3] & (F_FD | F_ERR) and not f[1] & RTR)
        else:
            assert total == 200
    with pytest.raises(ValueError):
        formats.convert_file(str(src), str(tmp_path / "x.trc"), "trc")
