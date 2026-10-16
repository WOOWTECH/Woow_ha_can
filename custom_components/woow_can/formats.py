"""CAN log file formats: candump log, Vector ASC, SavvyCAN GVRET CSV, PEAK TRC, OVMS CRTD and pcap.

Read: candump log, ASC, GVRET CSV, TRC (1.0 to 2.1), CRTD, pcap (LINKTYPE_CAN_SOCKETCAN). Write: candump log,
ASC, GVRET CSV, pcap (for Wireshark). Frames are (time, raw id, data, flags) as everywhere in this integration;
formats without interface names give their channel ("ch1", "bus0").
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta
import io
import re
import struct
from typing import Any, BinaryIO

from .can_port import (
    CAN_EFF_FLAG,
    CAN_EFF_MASK,
    CAN_ERR_FLAG,
    CAN_ERR_MASK,
    CAN_RTR_FLAG,
    CAN_SFF_MASK,
    F_BRS,
    F_ERR,
    F_FD,
    F_LOCAL,
    F_OWN,
    FD_LENGTHS,
)
from .capture import log_line, parse_log_line

Frame = tuple[float, int, bytes, int]  # time, raw id, data, flags
Item = tuple[str, Frame] | None  # None: a line that is not a frame

READ_FORMATS = {"log": "candump log", "asc": "Vector ASC", "csv": "SavvyCAN GVRET CSV", "trc": "PEAK TRC",
                "crtd": "OVMS CRTD", "pcap": "pcap (Wireshark)"}
WRITE_FORMATS = {"log": "candump log", "asc": "Vector ASC", "csv": "SavvyCAN GVRET CSV", "pcap": "pcap (Wireshark)"}
EXTENSIONS = (".log", ".txt", ".asc", ".csv", ".trc", ".crtd", ".pcap")
CONTENT_TYPES = {"log": "text/plain", "asc": "text/plain", "csv": "text/csv", "pcap": "application/vnd.tcpdump.pcap"}
PCAP_MAGIC = {b"\xd4\xc3\xb2\xa1": ("<", 1e-6), b"\xa1\xb2\xc3\xd4": (">", 1e-6),
              b"\x4d\x3c\xb2\xa1": ("<", 1e-9), b"\xa1\xb2\x3c\x4d": (">", 1e-9)}
LINKTYPE_CAN_SOCKETCAN = 227
CANFD_FDF = 0x04
HEAD = 8192


def _raw(can_id: int, extended: bool) -> int:
    return (can_id & CAN_EFF_MASK) | CAN_EFF_FLAG if extended else can_id & CAN_SFF_MASK


def _tx(flags: int) -> bool:
    return bool(flags & (F_OWN | F_LOCAL))


# ---- detection -------------------------------------------------------------------------------
def detect(head: str) -> str:
    """The format of a text log from its beginning: log, asc, csv, trc, crtd (or "unknown")."""
    lines = [line.strip() for line in head.splitlines() if line.strip()][:40]
    text = "\n".join(lines)
    if any(line.startswith(";$FILEVERSION") for line in lines) or re.search(r"^\d+\)\s+\d", text, re.M):
        return "trc"
    if re.search(r"^Time Stamp,ID,Extended", text, re.M | re.I):
        return "csv"
    if re.search(r"^(date |base (hex|dec)|Begin Triggerblock)", text, re.M | re.I):
        return "asc"
    if re.search(r"^\(\d+\.\d+\)\s+\S+\s+[0-9A-Fa-f]+#", text, re.M):
        return "log"
    if re.search(r"^\d+(\.\d+)?\s+\d*[RT](11|29)\s+[0-9A-Fa-f]+", text, re.M):
        return "crtd"
    return "unknown"


# ---- reading ---------------------------------------------------------------------------------
def frames_of(lines: Iterable[str], fmt: str) -> Iterator[Item]:
    reader = _READERS.get(fmt)
    if reader is None:
        yield from (None for line in lines if line.strip())
        return
    yield from reader(iter(lines))


def collect(items: Iterable[Item], limit: int | None = None) -> tuple[dict[str, list[Frame]], int]:
    """Frames by interface (the last `limit` of each, in time order) and the number of lines skipped."""
    out: dict[str, list[Frame]] = {}
    skipped = 0
    for item in items:
        if item is None:
            skipped += 1
            continue
        ifname, frame = item
        frames = out.setdefault(ifname, [])
        frames.append(frame)
        if limit and len(frames) > 2 * limit:
            del frames[:-limit]
    for frames in out.values():
        if any(frames[i][0] > frames[i + 1][0] for i in range(len(frames) - 1)):
            frames.sort(key=lambda f: f[0])
        if limit:
            del frames[:-limit]
    return out, skipped


def read(text: str, fmt: str | None = None) -> tuple[dict[str, list[Frame]], int]:
    return collect(frames_of(text.splitlines(), fmt or detect(text[:HEAD])))


def read_bytes(data: bytes, limit: int | None = None) -> tuple[dict[str, list[Frame]], int, str]:
    if data[:4] in PCAP_MAGIC:
        by_iface, skipped = collect(_read_pcap(io.BytesIO(data)), limit)
        return by_iface, skipped, "pcap"
    text = data.decode("utf-8-sig", "replace")
    fmt = detect(text[:HEAD])
    by_iface, skipped = collect(frames_of(text.splitlines(), fmt), limit)
    return by_iface, skipped, fmt


@contextmanager
def open_items(path: str) -> Iterator[tuple[str, Iterator[Item]]]:
    """Blocking: the format of a log file and its frames, read as they are iterated."""
    with open(path, "rb") as fh:
        if fh.read(4) in PCAP_MAGIC:
            fh.seek(0)
            yield "pcap", _read_pcap(fh)
            return
    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        fmt = detect(fh.read(HEAD))
        fh.seek(0)
        yield fmt, frames_of(fh, fmt)


def read_file(path: str, limit: int | None = None) -> tuple[dict[str, list[Frame]], int, str]:
    """Blocking: frames of a log file of any readable format, lines skipped, the format found."""
    with open_items(path) as (fmt, items):
        by_iface, skipped = collect(items, limit)
    return by_iface, skipped, fmt


def convert_file(src: str, dst: str, fmt: str) -> dict[str, Any]:
    """Blocking: a log file of any readable format written as `fmt`, frame by frame (any size)."""
    if fmt not in WRITE_FORMATS:
        raise ValueError(f"unknown format {fmt!r}: use one of {', '.join(WRITE_FORMATS)}")
    names: list[str] = []
    index: dict[str, int] = {}
    counts = {"frames": 0, "skipped": 0}

    def items(source: Iterator[Item]) -> Iterator[tuple[int, Frame]]:
        for item in source:
            if item is None:
                counts["skipped"] += 1
                continue
            ifname, frame = item
            if ifname not in index:
                index[ifname] = len(names)
                names.append(ifname)
            counts["frames"] += 1
            yield index[ifname], frame

    with open_items(src) as (found, source), open(dst, "wb") as out:
        if found == "unknown":
            raise ValueError("not a CAN log this integration reads")
        for chunk in encode(fmt, items(source), names):
            out.write(chunk)
    return {**counts, "from": found, "to": fmt, "interfaces": names}


def _read_log(lines: Iterator[str]) -> Iterator[Item]:
    for line in lines:
        if not line.strip():
            continue
        parsed = parse_log_line(line)
        if parsed is None:
            yield None
            continue
        ifname, ts, raw, data, flags = parsed
        yield ifname, (ts, raw, data, flags)


_ASC_DATES = ("%a %b %d %I:%M:%S.%f %p %Y", "%a %b %d %H:%M:%S.%f %Y", "%a %b %d %I:%M:%S %p %Y",
              "%a %b %d %H:%M:%S %Y")


def _asc_date(value: str) -> float | None:
    for fmt in _ASC_DATES:
        try:
            return datetime.strptime(value.strip(), fmt).timestamp()
        except ValueError:
            continue
    return None


def _read_asc(lines: Iterator[str]) -> Iterator[Item]:
    base, relative, start, prev = 16, False, 0.0, None
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        lower = stripped.lower()
        if lower.startswith("date "):
            start = _asc_date(stripped[5:]) or start
            continue
        if lower.startswith("base "):
            parts = lower.split()
            base = 10 if len(parts) > 1 and parts[1] == "dec" else 16
            relative = "relative" in parts
            continue
        if lower.startswith(("begin triggerblock", "end triggerblock", "internal events", "no internal")):
            continue
        tokens = stripped.split()
        try:
            t = float(tokens[0])
        except ValueError:
            yield None
            continue
        ts = ((prev if prev is not None else start) + t) if relative else start + t
        prev = ts
        rest = tokens[1:]
        if rest and rest[0].upper() == "CANFD":
            yield _asc_fd(rest[1:], ts, base)
        elif len(rest) >= 2 and rest[1] == "ErrorFrame":
            yield f"ch{rest[0]}", (ts, CAN_ERR_FLAG, bytes(8), F_ERR)
        elif len(rest) >= 4 and rest[0].isdigit() and rest[2].lower() in ("rx", "tx"):
            yield _asc_classic(rest, ts, base)
        # anything else is an event: start of measurement, statistics, chip status, comments


def _asc_id(text: str, base: int) -> int:
    return _raw(int(text.rstrip("xX"), base), text[-1:] in ("x", "X"))


def _asc_classic(rest: list[str], ts: float, base: int) -> Item:
    ch, ident, direction, kind = rest[0], rest[1], rest[2].lower(), rest[3].lower()
    if kind not in ("d", "r"):
        return None
    try:
        raw = _asc_id(ident, base)
        flags = F_LOCAL if direction == "tx" else 0
        if kind == "r":
            return f"ch{ch}", (ts, raw | CAN_RTR_FLAG, b"", flags)
        dlc = min(int(rest[4], base), 8)
        data = bytes(int(b, base) for b in rest[5:5 + dlc])
    except (ValueError, IndexError):
        return None
    if len(data) != dlc:
        return None
    return f"ch{ch}", (ts, raw, data, flags)


def _asc_fd(tokens: list[str], ts: float, base: int) -> Item:
    # CANFD <ch> <dir> <id> [<name>] <brs> <esi> <dlc hex> <length> <data> <duration> ... (python-can, CANalyzer)
    try:
        ch, direction = tokens[0], tokens[1].lower()
        raw = _asc_id(tokens[2], base)
        i = 3 if tokens[3] in ("0", "1") else 4
        brs = tokens[i] == "1"
        length = int(tokens[i + 3])
        data = bytes(int(b, base) for b in tokens[i + 4:i + 4 + length])
    except (ValueError, IndexError):
        return None
    if len(data) != length:
        return None
    flags = F_FD | (F_BRS if brs else 0) | (F_LOCAL if direction == "tx" else 0)
    return f"ch{ch}", (ts, raw, data, flags)


def _read_csv(lines: Iterator[str]) -> Iterator[Item]:
    col: dict[str, int] | None = None
    for line in lines:
        if not line.strip():
            continue
        cells = [c.strip() for c in line.split(",")]
        if col is None:
            col = {name.lower(): i for i, name in enumerate(cells)}
            if not {"time stamp", "id", "extended", "len", "d1"} <= set(col):
                col = None
                yield None
            continue
        try:
            ts = int(cells[col["time stamp"]]) / 1e6
            raw = _raw(int(cells[col["id"]], 16), cells[col["extended"]].lower() == "true")
            length = int(cells[col["len"]])
            first = col["d1"]
            data = bytes(int(c, 16) for c in cells[first:first + length])
            direction = cells[col["dir"]].lower() if "dir" in col else "rx"
            bus = cells[col["bus"]] if "bus" in col else "0"
        except (ValueError, IndexError):
            yield None
            continue
        if len(data) != length or length > 64:
            yield None
            continue
        flags = (F_LOCAL if direction == "tx" else 0) | (F_FD if length > 8 else 0)
        yield f"bus{bus}", (ts, raw, data, flags)


def _ole_date(days: float) -> float:
    return (datetime(1899, 12, 30) + timedelta(days=days)).timestamp()


def _read_trc(lines: Iterator[str]) -> Iterator[Item]:
    version, start = 1.0, 0.0
    columns: list[str] | None = None
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(";"):
            key, _, value = stripped[1:].partition("=")
            try:
                if key == "$FILEVERSION":
                    version = float(value)
                elif key == "$STARTTIME":
                    start = _ole_date(float(value))
            except ValueError:
                pass
            if key == "$COLUMNS":
                columns = value.split(",")
            continue
        tokens = stripped.split()
        if version >= 2.0:
            yield _trc2(tokens, columns or ["N", "O", "T", "I", "d", "l", "D"], start)
        else:
            yield _trc1(tokens, version, start)


def _trc_id(text: str) -> int:
    return _raw(int(text, 16), len(text) > 4)


def _trc1(tokens: list[str], version: float, start: float) -> Item:
    # 1.0: N) O ID DLC D..   1.1: N) O T ID DLC D..   1.2: N) O B T ID DLC D..   1.3: N) O B T ID - DLC D..
    try:
        if not tokens[0].endswith(")"):
            return None
        ts = start + float(tokens[1]) / 1000
        i, bus, kind = 2, "1", "Rx"
        if version >= 1.2:
            bus, i = tokens[i], i + 1
        if version >= 1.1:
            kind, i = tokens[i], i + 1
        if kind not in ("Rx", "Tx"):
            return None  # Error, Warng: status entries
        raw = _trc_id(tokens[i])
        i += 1
        if version >= 1.3 and tokens[i] == "-":
            i += 1
        dlc = int(tokens[i])
        rest = tokens[i + 1:]
    except (ValueError, IndexError):
        return None
    flags = F_LOCAL if kind == "Tx" else 0
    if rest[:1] == ["RTR"]:
        return f"bus{bus}", (ts, raw | CAN_RTR_FLAG, b"", flags)
    try:
        data = bytes(int(b, 16) for b in rest[:min(dlc, 8)])
    except ValueError:
        return None
    if len(data) != min(dlc, 8):
        return None
    return f"bus{bus}", (ts, raw, data, flags)


def _trc2(tokens: list[str], columns: list[str], start: float) -> Item:
    values = dict(zip(columns, tokens))
    kind = values.get("T", "DT")
    try:
        ts = start + float(values["O"]) / 1000
        bus = values.get("B", "1")
        if kind == "ER":
            return f"bus{bus}", (ts, CAN_ERR_FLAG, bytes(8), F_ERR)
        if kind not in ("DT", "FD", "FB", "FE", "BI", "RR"):
            return None  # status, event and warning entries
        raw = _trc_id(values["I"])
        flags = F_LOCAL if values.get("d", "Rx") == "Tx" else 0
        if kind == "RR":
            return f"bus{bus}", (ts, raw | CAN_RTR_FLAG, b"", flags)
        if "l" in values:
            length = int(values["l"])
        else:
            dlc = int(values.get("L", "0"))
            length = FD_LENGTHS[min(dlc, 15)] if kind != "DT" else min(dlc, 8)
        if kind != "DT":
            flags |= F_FD | (F_BRS if kind in ("FB", "BI") else 0)
        first = columns.index("D") if "D" in columns else len(tokens) - length
        data = bytes(int(b, 16) for b in tokens[first:first + length])
    except (ValueError, IndexError, KeyError):
        return None
    if len(data) != length:
        return None
    return f"bus{bus}", (ts, raw, data, flags)


_CRTD = re.compile(r"^(\d+(?:\.\d+)?)\s+(\d*)([RT])(11|29)\s+([0-9A-Fa-f]+)((?:\s+[0-9A-Fa-f]{2})*)\s*$")


def _read_crtd(lines: Iterator[str]) -> Iterator[Item]:
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        m = _CRTD.match(stripped)
        if not m:
            yield None  # comments (CXX), errors, events and other record types
            continue
        ts, bus, kind, bits, ident, data_text = m.groups()
        data = bytes(int(b, 16) for b in data_text.split())
        if len(data) > 8:
            yield None
            continue
        raw = _raw(int(ident, 16), bits == "29")
        yield f"bus{bus or '1'}", (float(ts), raw, data, F_LOCAL if kind == "T" else 0)


def _read_pcap(fh: BinaryIO) -> Iterator[Item]:
    header = fh.read(24)
    endian, unit = PCAP_MAGIC[header[:4]]
    if len(header) < 24 or struct.unpack(endian + "I", header[20:24])[0] & 0xFFFF != LINKTYPE_CAN_SOCKETCAN:
        yield None  # only SocketCAN captures (tcpdump -i can0, Wireshark on a CAN interface)
        return
    record = struct.Struct(endian + "IIII")
    while True:
        head = fh.read(16)
        if len(head) < 16:
            return
        sec, frac, incl, _orig = record.unpack(head)
        body = fh.read(incl)
        if len(body) < 8 or len(body) < incl:
            yield None
            continue
        (can_id,) = struct.unpack(">I", body[:4])  # network byte order
        length, fd_flags = body[4], body[5]
        data = bytes(body[8:8 + length])
        ts = sec + frac * unit
        if can_id & CAN_ERR_FLAG:
            yield "pcap", (ts, (can_id & CAN_ERR_MASK) | CAN_ERR_FLAG, data.ljust(8, b"\0")[:8], F_ERR)
            continue
        raw = _raw(can_id, bool(can_id & CAN_EFF_FLAG))
        if can_id & CAN_RTR_FLAG:
            yield "pcap", (ts, raw | CAN_RTR_FLAG, b"", 0)
            continue
        fd = bool(fd_flags & CANFD_FDF) or incl == 72 or length > 8
        yield "pcap", (ts, raw, data, (F_FD | (F_BRS if fd_flags & 0x01 else 0)) if fd else 0)


_READERS = {"log": _read_log, "asc": _read_asc, "csv": _read_csv, "trc": _read_trc, "crtd": _read_crtd}


# ---- writing ---------------------------------------------------------------------------------
def write(fmt: str, by_iface: dict[str, list[Frame]]) -> bytes:
    """Frames of one or more interfaces in time order as a file (channels / buses numbered in order)."""
    names = list(by_iface)
    if len(by_iface) == 1:
        merged: Iterable[tuple[int, Frame]] = ((0, f) for f in by_iface[names[0]])
    else:
        merged = sorted(((i, f) for i, frames in enumerate(by_iface.values()) for f in frames), key=lambda x: x[1][0])
    return b"".join(encode(fmt, merged, names))


def encode(fmt: str, items: Iterable[tuple[int, Frame]], names: list[str]) -> Iterator[bytes]:
    """Chunks of a file in `fmt`; items are (interface index, frame), names[index] the interface name."""
    if fmt not in WRITE_FORMATS:
        raise ValueError(f"unknown format {fmt!r}: use one of {', '.join(WRITE_FORMATS)}")
    if fmt == "pcap":
        yield struct.pack("<IHHiIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, LINKTYPE_CAN_SOCKETCAN)
        for _i, frame in items:
            yield _pcap_record(frame)
        return
    if fmt == "csv":
        yield b"Time Stamp,ID,Extended,Dir,Bus,LEN,D1,D2,D3,D4,D5,D6,D7,D8\n"
        yield from (_csv_row(i, frame).encode("ascii") for i, frame in items)
        return
    if fmt == "log":
        yield from (log_line(names[i], *frame).encode("ascii") for i, frame in items)
        return
    items = iter(items)
    first = next(items, None)
    start = first[1][0] if first else datetime.now().timestamp()
    yield _asc_head(start).encode("ascii")
    if first is not None:
        yield _asc_row(start, *first).encode("ascii")
        yield from (_asc_row(start, i, frame).encode("ascii") for i, frame in items)
    yield b"End TriggerBlock\n"


def _asc_ident(raw: int) -> str:
    return f"{raw & CAN_EFF_MASK:X}x" if raw & CAN_EFF_FLAG else f"{raw & CAN_SFF_MASK:X}"


def _asc_head(start: float) -> str:
    when = datetime.fromtimestamp(start)
    stamp = f"{when:%a %b %d %I:%M:%S}.{when.microsecond // 1000:03d} {'am' if when.hour < 12 else 'pm'} {when.year}"
    return (f"date {stamp}\nbase hex  timestamps absolute\ninternal events logged\n// version 9.0.0\n"
            f"Begin Triggerblock {stamp}\n   0.000000 Start of measurement\n")


def _asc_row(start: float, i: int, frame: Frame) -> str:
    ts, raw, data, flags = frame
    t, ch, direction = ts - start, i + 1, "Tx" if _tx(flags) else "Rx"
    if flags & F_ERR:
        return f"{t:11.6f} {ch}  ErrorFrame\n"
    if flags & F_FD:
        dlc = next((n for n, size in enumerate(FD_LENGTHS) if size >= len(data)), 15)
        body = " ".join(f"{b:02X}" for b in data)
        brs = 1 if flags & F_BRS else 0
        return (f"{t:11.6f} CANFD {ch:>3} {direction:<4} {_asc_ident(raw):>8}  {'':>32} {brs} 0 {dlc:x} "
                f"{len(data):>2} {body} {0:>8} {0:>4} {0x1000 | (0x2000 if brs else 0):>8X} {0:>8} {0:>8} "
                f"{0:>8} {0:>8} {0:>8}\n")
    if raw & CAN_RTR_FLAG:
        return f"{t:11.6f} {ch}  {_asc_ident(raw):<15} {direction:<4} r 0\n"
    body = " ".join(f"{b:02X}" for b in data)
    return f"{t:11.6f} {ch}  {_asc_ident(raw):<15} {direction:<4} d {len(data):x} {body}\n"


def _csv_row(i: int, frame: Frame) -> str:
    ts, raw, data, flags = frame
    if flags & (F_ERR | F_FD) or raw & CAN_RTR_FLAG:
        return ""  # GVRET CSV has no error frames, remote frames or more than 8 bytes
    cells = [f"{b:02X}" for b in data] + ["00"] * (8 - len(data))
    return (f"{int(round(ts * 1e6))},{raw & CAN_EFF_MASK:08X},{'true' if raw & CAN_EFF_FLAG else 'false'},"
            f"{'Tx' if _tx(flags) else 'Rx'},{i},{len(data)},{','.join(cells)},\n")


def _pcap_record(frame: Frame) -> bytes:
    ts, raw, data, flags = frame
    if flags & F_FD:
        record = struct.pack(">IBBxx", raw & 0xFFFFFFFF, len(data), CANFD_FDF | (0x01 if flags & F_BRS else 0))
        record += data.ljust(64, b"\0")
    else:
        record = struct.pack(">IBxxx", raw & 0xFFFFFFFF, len(data)) + data.ljust(8, b"\0")[:8]
    sec = int(ts)
    usec = min(int(round((ts - sec) * 1e6)), 999999)
    return struct.pack("<IIII", sec, usec, len(record), len(record)) + record
