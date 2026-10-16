"""Per-ID view of a bus: one row per (ID, direction), as cansniffer / SavvyCAN / cabana show it.

Every frame costs a dictionary lookup and a few assignments; nothing is sent per frame. Viewers
(the panel) get a batch every MONITOR_PUSH seconds with the rows that changed since their last
batch, and must acknowledge it: a viewer with MONITOR_UNACKED batches outstanding gets nothing
until it catches up, while its changes keep merging (counts, latest data, changed bits). A slow
phone then updates less often instead of overflowing Home Assistant's websocket queue.
"""

from __future__ import annotations

from collections.abc import Callable
import time
from typing import Any

from .can_port import CAN_EFF_FLAG, CAN_EFF_MASK, CAN_RTR_FLAG, CAN_SFF_MASK, F_BRS, F_FD, F_LOCAL, F_OWN, id_hex
from .const import MONITOR_MAX_IDS, MONITOR_UNACKED

TX_KEY = 1 << 32  # added to the key of frames WOOW CAN sent itself


class IdStat:
    """What one ID (in one direction) has done so far."""

    __slots__ = ("key", "raw", "flags", "count", "first", "last", "data", "period", "pmin", "pmax",
                 "changed", "changed_prev", "changes")

    def __init__(self, key: int, raw: int, flags: int, ts: float, data: bytes) -> None:
        self.key = key
        self.raw = raw
        self.flags = flags
        self.count = 0
        self.first = ts
        self.last = ts
        self.data = data
        self.period = 0.0  # smoothed interval between frames, s
        self.pmin = 0.0  # slowly decaying envelope of the intervals
        self.pmax = 0.0
        self.changed = ts  # when the data last changed
        self.changed_prev = 0.0  # ... and the time before
        self.changes = 0

    def row(self, mask: int) -> list[Any]:
        """[key, raw id, flags, data hex, count, period µs, min µs, max µs, changed bits hex, last, changed,
        changed before]; the panel reads it by position."""
        width = 2 * len(self.data)
        return [self.key, self.raw, self.flags, self.data.hex().upper(), self.count, round(self.period * 1e6),
                round(self.pmin * 1e6), round(self.pmax * 1e6), f"{mask:0{width}X}" if mask and width else "",
                round(self.last, 6), round(self.changed, 6), round(self.changed_prev, 6)]

    def as_dict(self, now: float) -> dict[str, Any]:
        """For agents: plain names instead of positions."""
        return {
            "id": id_hex(self.raw),
            "extended": bool(self.raw & CAN_EFF_FLAG),
            "rtr": bool(self.raw & CAN_RTR_FLAG),
            "direction": "tx" if self.key & TX_KEY else "rx",
            "from_this_host": bool(self.flags & F_LOCAL) and not self.key & TX_KEY,
            "fd": bool(self.flags & F_FD),
            "data": self.data.hex(" ").upper(),
            "length": len(self.data),
            "count": self.count,
            "period_ms": round(self.period * 1000, 3) if self.period else None,
            "period_range_ms": [round(self.pmin * 1000, 3), round(self.pmax * 1000, 3)] if self.period else None,
            "rate_hz": round(1 / self.period, 3) if self.period else None,
            "last_seen_s_ago": round(now - self.last, 3),
            "data_changes": self.changes,
            "data_changed_s_ago": round(now - self.changed, 3) if self.changes else None,
        }


class Viewer:
    """One subscriber of a monitor: the rows that changed since its last batch, and how far behind it is."""

    def __init__(self, send: Callable[[dict[str, Any]], None]) -> None:
        self.send = send
        self.dirty: dict[int, int] = {}  # key -> bits that changed since the last batch
        self.seq = 0
        self.acked = 0
        self.cleared = False

    @property
    def unacked(self) -> int:
        return self.seq - self.acked


class Monitor:
    """The per-ID statistics of one interface (or of a capture file opened in the panel)."""

    def __init__(self, max_ids: int = MONITOR_MAX_IDS) -> None:
        self.max_ids = max_ids
        self.stats: dict[int, IdStat] = {}
        self.viewers: list[Viewer] = []
        self.overflow = 0  # frames of IDs beyond max_ids (counted, not shown)
        self.frames = 0
        self.since = time.time()
        # Since the last bus load estimate: frame mix (29-bit share, CAN FD with bit rate switch)
        self.mix_total = 0
        self.mix_eff = 0
        self.mix_brs = 0

    def add(self, ts: float, raw: int, data: bytes, flags: int) -> None:
        self.frames += 1
        self.mix_total += 1
        if raw & CAN_EFF_FLAG:
            self.mix_eff += 1
        if flags & F_BRS:
            self.mix_brs += 1
        key = raw | (TX_KEY if flags & F_OWN else 0)
        st = self.stats.get(key)
        if st is None:
            if len(self.stats) >= self.max_ids:
                self.overflow += 1
                return
            st = self.stats[key] = IdStat(key, raw, flags, ts, data)
            mask = (1 << (8 * len(data))) - 1
        else:
            dt = ts - st.last
            if dt > 0:
                if st.period:
                    st.period += (dt - st.period) / 8
                    st.pmin = min(dt, st.pmin + (st.period - st.pmin) / 32)
                    st.pmax = max(dt, st.pmax - (st.pmax - st.period) / 32)
                else:
                    st.period = st.pmin = st.pmax = dt
            if data == st.data:
                mask = 0
            else:
                if len(data) == len(st.data):
                    mask = int.from_bytes(data, "big") ^ int.from_bytes(st.data, "big")
                else:
                    mask = (1 << (8 * len(data))) - 1
                st.data = data
                st.changed_prev, st.changed = st.changed, ts
                st.changes += 1
            st.last = ts
            st.flags = flags
        st.count += 1
        for viewer in self.viewers:
            viewer.dirty[key] = viewer.dirty.get(key, 0) | mask

    def take_mix(self) -> tuple[int, int, int]:
        mix = (self.mix_total, self.mix_eff, self.mix_brs)
        self.mix_total = self.mix_eff = self.mix_brs = 0
        return mix

    def clear(self) -> None:
        self.stats.clear()
        self.overflow = 0
        self.frames = 0
        self.since = time.time()
        for viewer in self.viewers:
            viewer.dirty.clear()
            viewer.cleared = True

    # ---- viewers ----------------------------------------------------------------------
    def attach(self, viewer: Viewer) -> Callable[[], None]:
        self.viewers.append(viewer)
        return lambda: self.viewers.remove(viewer) if viewer in self.viewers else None

    def full(self) -> list[list[Any]]:
        return [st.row(0) for st in self.stats.values()]

    def batch(self, viewer: Viewer, now: float, extra: dict[str, Any] | None = None) -> dict[str, Any] | None:
        """The next batch for a viewer, or None if there is nothing new or it has to catch up first."""
        if viewer.unacked >= MONITOR_UNACKED or not (viewer.dirty or viewer.cleared):
            return None
        rows = [st.row(mask) for key, mask in viewer.dirty.items() if (st := self.stats.get(key)) is not None]
        viewer.dirty = {}
        viewer.seq += 1
        payload: dict[str, Any] = {"seq": viewer.seq, "t": round(now, 6), "rows": rows, "overflow": self.overflow,
                                   "frames": self.frames}
        if viewer.cleared:
            payload["clear"] = True
            viewer.cleared = False
        if extra:
            payload.update(extra)
        return payload

    def summary(self, now: float, limit: int = 200, match: Callable[[int], bool] | None = None) -> list[dict[str, Any]]:
        rows = [st for st in self.stats.values() if match is None or match(st.raw)]
        rows.sort(key=lambda st: (bool(st.raw & CAN_EFF_FLAG), st.raw & (CAN_EFF_MASK if st.raw & CAN_EFF_FLAG
                                                                         else CAN_SFF_MASK), st.key))
        return [st.as_dict(now) for st in rows[:limit]]
