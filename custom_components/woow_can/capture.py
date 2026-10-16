"""Frames over time: the trace ring buffer, candump log files, recordings.

The ring keeps the last TRACE_CAPACITY frames of an interface in fixed 24-byte records (time,
raw ID, length, flags, first 8 data bytes; longer CAN FD payloads on the side), about 4.8 MB
for 200 000 frames. Pages, searches and exports work on a copy, in an executor.

Files use candump's log format (`candump -L`, with `-x`'s R / T at the end), which canplayer,
SavvyCAN, python-can and Wireshark's tools read:
    (1760600000.123456) can0 123#DEADBEEF R
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
import os
import re
import struct
from typing import Any

from .can_port import CAN_EFF_FLAG, CAN_ERR_FLAG, CAN_ERR_MASK, CAN_RTR_FLAG, F_BRS, F_ERR, F_FD, F_LOCAL, F_OWN, \
    decode_error, frame_text, id_hex, parse_id

REC = struct.Struct("<dIBBxx8s")  # 24 bytes


@dataclass(frozen=True)
class TraceFrame:
    seq: int
    t: float
    raw: int
    data: bytes
    flags: int

    def as_list(self) -> list[Any]:
        """[seq, time, raw id, flags, data hex] for the panel."""
        return [self.seq, round(self.t, 6), self.raw, self.flags, self.data.hex().upper()]

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"seq": self.seq, "time": round(self.t, 6),
                               "direction": "tx" if self.flags & F_OWN else "rx"}
        if self.flags & F_LOCAL and not self.flags & F_OWN:
            out["from_this_host"] = True  # sent by another program on this host
        if self.flags & F_ERR:
            out.update(error=decode_error(self.raw, self.data), frame=frame_text(self.raw, self.data, self.flags))
            return out
        out.update(id=id_hex(self.raw), extended=bool(self.raw & CAN_EFF_FLAG), data=self.data.hex(" ").upper(),
                   length=len(self.data), frame=frame_text(self.raw, self.data, self.flags))
        if self.flags & F_FD:
            out["fd"] = True
        if self.raw & CAN_RTR_FLAG and not self.flags & F_FD:
            out["rtr"] = True
        return out


class TraceBuffer:
    """The most recent frames of one interface, oldest overwritten first."""

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.buf = bytearray(capacity * REC.size)
        self.seq = 0  # frames appended so far; the next one gets this number
        self.long: dict[int, bytes] = {}  # seq -> payload of CAN FD frames longer than 8 bytes

    @property
    def first(self) -> int:
        return max(0, self.seq - self.capacity)

    def append(self, ts: float, raw: int, data: bytes, flags: int) -> None:
        seq = self.seq
        REC.pack_into(self.buf, (seq % self.capacity) * REC.size, ts, raw, len(data), flags, data)
        if len(data) > 8:
            self.long[seq] = data
        if self.long and seq >= self.capacity:
            self.long.pop(seq - self.capacity, None)
        self.seq = seq + 1

    def clear(self) -> None:
        self.seq = 0
        self.long.clear()

    def snapshot(self) -> TraceSnapshot:
        """A copy to read in an executor while frames keep arriving."""
        return TraceSnapshot(bytes(self.buf), self.capacity, self.first, self.seq, dict(self.long))


class TraceSnapshot:
    def __init__(self, buf: bytes, capacity: int, first: int, end: int, long: dict[int, bytes]) -> None:
        self.buf, self.capacity, self.first, self.end, self.long = buf, capacity, first, end, long

    def frame(self, seq: int) -> TraceFrame:
        ts, raw, length, flags, data8 = REC.unpack_from(self.buf, (seq % self.capacity) * REC.size)
        data = self.long.get(seq, data8[:length]) if length > 8 else data8[:length]
        return TraceFrame(seq, ts, raw, data, flags)

    def frames(self, start: int | None = None, end: int | None = None) -> Iterator[TraceFrame]:
        for seq in range(max(self.first, start or 0), min(self.end, self.end if end is None else end)):
            yield self.frame(seq)

    def page(self, before: int | None = None, limit: int = 200, match: Callable[[TraceFrame], bool] | None = None,
             since: float | None = None, until: float | None = None) -> dict[str, Any]:
        """Up to `limit` frames before seq `before` (default: the newest), newest first."""
        seq = min(self.end, self.end if before is None else before) - 1
        out: list[TraceFrame] = []
        scanned = 0
        while seq >= self.first and len(out) < limit:
            frame = self.frame(seq)
            scanned += 1
            if until is not None and frame.t > until:
                seq -= 1
                continue
            if since is not None and frame.t < since:
                break
            if match is None or match(frame):
                out.append(frame)
            seq -= 1
        more = seq >= self.first
        if more and since is not None and self.frame(seq).t < since:
            more = False
        return {"frames": out, "next": seq + 1 if more else None, "first": self.first, "end": self.end,
                "scanned": scanned}


def trace_matcher(ids: Callable[[int], bool] | None, direction: str | None,
                  errors: bool = True) -> Callable[[TraceFrame], bool] | None:
    if ids is None and not direction and errors:
        return None

    def match(frame: TraceFrame) -> bool:
        if frame.flags & F_ERR:
            return errors and ids is None
        if direction == "rx" and frame.flags & F_OWN:
            return False
        if direction == "tx" and not frame.flags & F_OWN:
            return False
        return ids is None or ids(frame.raw)

    return match


# ---- candump log format ------------------------------------------------------------------
def log_line(ifname: str, ts: float, raw: int, data: bytes, flags: int) -> str:
    direction = "T" if flags & (F_OWN | F_LOCAL) else "R"  # as candump -x: T = sent from this host
    return f"({ts:017.6f}) {ifname} {frame_text(raw, data, flags)} {direction}\n"


_LINE = re.compile(r"^\((\d+)\.(\d+)\)\s+(\S+)\s+(\S+)(?:\s+([RT]))?\s*$")


def parse_log_line(line: str) -> tuple[str, float, int, bytes, int] | None:
    """One candump log line -> (interface, time, raw id, data, flags); None for anything else."""
    m = _LINE.match(line.strip())
    if not m:
        return None
    sec, frac, ifname, frame, direction = m.groups()
    ts = int(sec) + int(frac) / 10 ** len(frac)
    flags = F_LOCAL if direction == "T" else 0
    id_part, sep, rest = frame.partition("#")
    if not sep:
        return None
    try:
        if len(id_part) == 8 and int(id_part, 16) & CAN_ERR_FLAG:  # error frame: 2xxxxxxx#<8 bytes>
            return ifname, ts, int(id_part, 16) & CAN_ERR_MASK | CAN_ERR_FLAG, bytes.fromhex(rest), flags | F_ERR
        can_id, extended = parse_id(id_part)
        raw = can_id | (CAN_EFF_FLAG if extended else 0)
        if rest[:1] in ("R", "r"):
            return ifname, ts, raw | CAN_RTR_FLAG, b"", flags
        if rest.startswith("#"):  # CAN FD: ##<flags nibble><data>
            fd_flags = int(rest[1], 16)
            return ifname, ts, raw, bytes.fromhex(rest[2:]), flags | F_FD | (F_BRS if fd_flags & 1 else 0)
        data = bytes.fromhex(rest.replace(".", "").split("_")[0])
    except (ValueError, IndexError):
        return None
    if len(data) > 8:
        return None
    return ifname, ts, raw, data, flags


def read_log(path: str, limit: int) -> tuple[dict[str, list[tuple[float, int, bytes, int]]], int, int]:
    """Blocking: frames of a candump log by interface (the last `limit` of each), lines read, lines skipped."""
    out: dict[str, list[tuple[float, int, bytes, int]]] = {}
    lines = skipped = 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            lines += 1
            parsed = parse_log_line(line)
            if parsed is None:
                if line.strip():
                    skipped += 1
                continue
            ifname, *frame = parsed
            frames = out.setdefault(ifname, [])
            frames.append(tuple(frame))  # type: ignore[arg-type]
            if len(frames) > 2 * limit:
                del frames[:-limit]
    for ifname, frames in out.items():
        del frames[:-limit]
    return out, lines, skipped


def write_log(path: str, ifname: str, frames: Iterable[TraceFrame]) -> int:
    """Blocking: write frames as a candump log; returns the number written."""
    n = 0
    with open(path, "w", encoding="ascii") as fh:
        for frame in frames:
            fh.write(log_line(ifname, frame.t, frame.raw, frame.data, frame.flags))
            n += 1
    return n


def export_text(snapshot: TraceSnapshot, ifname: str, match: Callable[[TraceFrame], bool] | None = None) -> str:
    """Blocking: the buffer as candump log text."""
    return "".join(log_line(ifname, f.t, f.raw, f.data, f.flags) for f in snapshot.frames()
                   if match is None or match(f))


class Recording:
    """Frames of one interface going to a log file, written every second from an executor."""

    def __init__(self, path: str, ifname: str, entry_id: str, max_bytes: int) -> None:
        self.path = path
        self.name = os.path.basename(path)
        self.ifname = ifname
        self.entry_id = entry_id
        self.max_bytes = max_bytes
        self.pending: list[str] = []
        self.frames = 0
        self.bytes = 0
        self.full = False

    def add(self, ts: float, raw: int, data: bytes, flags: int) -> None:
        if self.full:
            return
        line = log_line(self.ifname, ts, raw, data, flags)
        self.bytes += len(line)
        if self.bytes > self.max_bytes:
            self.full = True
            return
        self.pending.append(line)
        self.frames += 1

    def take(self) -> list[str]:
        lines, self.pending = self.pending, []
        return lines

    @staticmethod
    def write(path: str, lines: list[str]) -> None:
        """Blocking."""
        with open(path, "a", encoding="ascii") as fh:
            fh.writelines(lines)


SAFE_NAME = re.compile(r"^[\w.\-]{1,120}$")


def safe_name(name: str) -> str:
    """A capture file name without directories or odd characters."""
    name = name.strip()
    if not SAFE_NAME.match(name) or name.startswith("."):
        raise ValueError(f"bad file name {name!r}: use letters, digits, '.', '_' and '-'")
    return name
