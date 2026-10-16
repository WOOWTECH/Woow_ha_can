"""Reverse engineering: which bits change, which field holds a value, what an action changes.

Pure functions over frame data, used by the panel and by the services bit_activity, find_signal and
guided_capture. Bit positions follow the signal definitions (DBC numbering): bit i is bit i % 8 of byte
i // 8, 0 = least significant; a big-endian (Motorola) field starts at its most significant bit.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from dataclasses import dataclass, field
from typing import Any

from .signals import Signal

# Scaling tried when looking for a known value: the usual resolutions and offsets of CAN signals
# (J1939 temperatures -40 / -273, torque -125, battery currents -1000 / -3200 ...).
FACTORS = tuple(sorted((1.0, 0.1, 0.01, 0.001, 0.5, 0.25, 0.2, 0.125, 0.05, 0.02, 0.0625, 0.03125, 0.00390625,
                        2.0, 10.0, 100.0)))
OFFSETS = (0.0, -40.0, -50.0, -100.0, -125.0, -273.0, -1000.0, -3200.0)
MAX_CANDIDATES = 20000
SCAN_BYTES = 16  # CAN FD frames: fields in the first 16 bytes
MODES = ("equals", "increased", "decreased", "changed", "unchanged")


# ---- bit activity ------------------------------------------------------------------------------
def bit_activity(datas: list[bytes]) -> dict[str, Any]:
    """Per bit: how often it changed between consecutive frames and how often it was 1; per byte: range."""
    width = max((len(d) for d in datas), default=0)
    changes = [0] * (width * 8)
    ones = [0] * (width * 8)
    lows = [255] * width
    highs = [0] * width
    distinct: list[set[int]] = [set() for _ in range(width)]
    prev: int | None = None
    for data in datas:
        value = int.from_bytes(data.ljust(width, b"\0"), "little")
        bits = value
        while bits:
            low = bits & -bits
            ones[low.bit_length() - 1] += 1
            bits ^= low
        if prev is not None:
            diff = value ^ prev
            while diff:
                low = diff & -diff
                changes[low.bit_length() - 1] += 1
                diff ^= low
        prev = value
        for i, byte in enumerate(data):
            lows[i] = min(lows[i], byte)
            highs[i] = max(highs[i], byte)
            if len(distinct[i]) <= 256:
                distinct[i].add(byte)
    return {"frames": len(datas), "length": width, "changes": changes, "ones": ones,
            "bytes": [{"min": lows[i] if datas else 0, "max": highs[i], "distinct": len(distinct[i])}
                      for i in range(width)]}


def series(frames: list[tuple[float, bytes]], sig: Signal, samples: int = 300) -> dict[str, Any]:
    """A (candidate) signal over frames: summary numbers and evenly spread samples."""
    values = [(t, sig.decode_raw(data)[1]) for t, data in frames]
    numbers = [v for _, v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]
    changes = sum(1 for (_, a), (_, b) in zip(values, values[1:]) if a != b)
    step = max(1, -(-len(values) // samples)) if samples else 1
    picked = values[::step]
    if values and picked[-1] is not values[-1]:
        picked.append(values[-1])
    return {"frames": len(values), "distinct_values": len({v for _, v in values}), "changes": changes,
            "min": min(numbers, default=None), "max": max(numbers, default=None),
            "first": values[0][1] if values else None, "last": values[-1][1] if values else None,
            "samples": [{"time": round(t, 3), "value": v} for t, v in picked]}


# ---- fields worth trying --------------------------------------------------------------------
def fields_for(length: int) -> list[tuple[int, int, str]]:
    """(start, length, byte order) of the byte-, nibble- and bit-aligned fields of a payload."""
    n = min(length, SCAN_BYTES)
    bits = 8 * n
    out: set[tuple[int, int, str]] = set()
    for b in range(n):
        for w in (1, 2, 3, 4):
            if b + w <= n:
                out.add((8 * b, 8 * w, "little"))
                if w > 1:
                    out.add((8 * b + 7, 8 * w, "big"))
    for j in range(2 * n):
        out.add((4 * j, 4, "little"))  # nibbles
        if 4 * j + 12 <= bits:
            out.add((4 * j, 12, "little"))
            msb = 4 * j  # 12-bit big-endian fields whose most significant bit starts a nibble
            out.add(((msb // 8) * 8 + 7 - msb % 8, 12, "big"))
    for i in range(bits):
        out.add((i, 1, "little"))
    return sorted(out, key=lambda f: (f[0], f[1], f[2]))


@dataclass(slots=True)
class Candidate:
    key: int  # monitor key: raw id (+ TX_KEY for frames this integration sent)
    start: int
    length: int
    order: str
    signed: bool
    factor: float
    offset: float
    value: float  # at the last step

    def signal(self) -> Signal:
        return Signal(name="candidate", start=self.start, length=self.length, byte_order=self.order,
                      signed=self.signed, factor=self.factor, offset=self.offset)

    def read(self, data: bytes) -> float | None:
        raw = self.signal().raw(data)
        if raw is None:
            return None
        if self.signed and raw >> (self.length - 1):
            raw -= 1 << self.length
        return raw * self.factor + self.offset

    def rank(self) -> float:
        """Lower is likelier: plain scaling, byte alignment, common widths first."""
        score = 0.0
        if self.factor != 1.0:
            score += 1.0 if self.factor in (0.1, 0.01, 0.001, 0.5) else 2.0
        if self.offset:
            score += 2.0
        aligned = self.start % 8 == (0 if self.order == "little" else 7) and self.length % 8 == 0
        score += 0.0 if aligned else 1.5
        score += 0.5 if self.signed else 0.0
        score += 1.0 if self.length < 4 else 0.0
        return score

    def as_dict(self, id_text: str) -> dict[str, Any]:
        return {"id": id_text, "key": self.key, "start": self.start, "length": self.length, "byte_order": self.order,
                "signed": self.signed, "factor": self.factor, "offset": self.offset, "value": _round(self.value)}


def _round(value: float) -> float | int:
    rounded = round(value, 6)
    return int(rounded) if rounded == int(rounded) else rounded


def _scalings(raw: int, value: float, tol: float) -> list[tuple[float, float]]:
    """(factor, offset) pairs with raw x factor + offset within tol of value."""
    if raw == 0:
        return [(1.0, o) for o in OFFSETS if abs(o - value) <= tol][:1]
    out = []
    for offset in OFFSETS:
        lo = (value - tol - offset) / raw
        hi = (value + tol - offset) / raw
        if lo > hi:
            lo, hi = hi, lo
        for factor in FACTORS[bisect_left(FACTORS, lo):bisect_right(FACTORS, hi)]:
            out.append((factor, offset))
    return out


def default_tolerance(value: float) -> float:
    return max(abs(value) * 0.01, 0.05)


@dataclass
class Search:
    """Narrow the fields of all IDs down to the one holding a value, step by step (like a memory scanner)."""

    steps: list[dict[str, Any]] = field(default_factory=list)
    candidates: list[Candidate] = field(default_factory=list)
    truncated: bool = False

    def start(self, latest: dict[int, bytes], value: float | None = None, tol: float | None = None) -> None:
        """With a value: the fields (and scalings) that read it now; without: every field, raw."""
        self.steps, self.candidates, self.truncated = [], [], False
        out: list[Candidate] = []
        for key, data in latest.items():
            for start, length, order in fields_for(len(data)):
                plain = Candidate(key, start, length, order, False, 1.0, 0.0, 0.0)
                raw = plain.signal().raw(data)
                if raw is None:
                    continue
                variants = [(False, raw)]
                if length >= 8:
                    variants.append((True, raw - (1 << length) if raw >> (length - 1) else raw))
                for signed, number in variants:
                    if value is None:
                        out.append(Candidate(key, start, length, order, signed, 1.0, 0.0, float(number)))
                        continue
                    scalings = _scalings(number, value, tol if tol is not None else default_tolerance(value))
                    if length < 8:
                        scalings = [s for s in scalings if s == (1.0, 0.0)]
                    for factor, offset in scalings:
                        out.append(Candidate(key, start, length, order, signed, factor, offset,
                                             number * factor + offset))
        out.sort(key=lambda c: c.rank())
        self.truncated = len(out) > MAX_CANDIDATES
        self.candidates = out[:MAX_CANDIDATES]
        self.steps.append({"mode": "equals" if value is not None else "start", "value": value,
                           "tolerance": tol if value is None or tol is not None else default_tolerance(value),
                           "left": len(self.candidates)})

    def narrow(self, latest: dict[int, bytes], mode: str, value: float | None = None, tol: float | None = None) -> None:
        """Keep the candidates that now read `value` (equals) or moved as said since the last step."""
        if mode not in MODES:
            raise ValueError(f"mode: one of {', '.join(MODES)}")
        if mode == "equals" and value is None:
            raise ValueError("equals needs a value")
        tol = (tol if tol is not None else default_tolerance(value)) if value is not None else None
        kept = []
        for cand in self.candidates:
            data = latest.get(cand.key)
            now = cand.read(data) if data is not None else None
            if now is None:
                continue
            if mode == "equals":
                ok = abs(now - value) <= tol  # type: ignore[operator]
            elif mode == "increased":
                ok = now > cand.value
            elif mode == "decreased":
                ok = now < cand.value
            elif mode == "changed":
                ok = now != cand.value
            else:
                ok = now == cand.value
            if ok:
                cand.value = now
                kept.append(cand)
        self.candidates = kept
        self.steps.append({"mode": mode, "value": value, "tolerance": tol, "left": len(kept)})

    def top(self, limit: int, id_text: Any) -> list[dict[str, Any]]:
        """The likeliest candidates; a signed one reading the same as its unsigned twin is left out."""
        unsigned = {(c.key, c.start, c.length, c.order, c.factor, c.offset, c.value)
                    for c in self.candidates if not c.signed}
        out = []
        for c in self.candidates:
            if c.signed and (c.key, c.start, c.length, c.order, c.factor, c.offset, c.value) in unsigned:
                continue
            out.append(c.as_dict(id_text(c.key)))
            if len(out) >= limit:
                break
        return out

    def summary(self, limit: int, id_text: Any) -> dict[str, Any]:
        keys = {c.key for c in self.candidates}
        return {"left": len(self.candidates), "ids": len(keys), "truncated": self.truncated, "steps": self.steps,
                "candidates": self.top(limit, id_text)}


# ---- comparing periods -------------------------------------------------------------------------
@dataclass
class Phase:
    label: str
    start: float
    end: float | None = None


STEADY_SHARE = 0.8  # a bit is steady in a phase when it holds one value this often ...
STEADY_CHANGES = 2  # ... and changes at most this many times (people act a moment after pressing next)
MAX_PHASES = 9  # idle, action, idle, action ... : repeating the action rules out coincidences


def _phase_stats(datas: list[bytes], width: int) -> tuple[int, list[int], list[int], list[tuple[int, int]]]:
    """Frames, per bit the ones and the changes, per byte the 10-90 % range of its values."""
    ones = [0] * (8 * width)
    changes = [0] * (8 * width)
    prev: int | None = None
    columns: list[list[int]] = [[] for _ in range(width)]
    for data in datas:
        value = int.from_bytes(data[:width].ljust(width, b"\0"), "little")
        bits = value
        while bits:
            low = bits & -bits
            ones[low.bit_length() - 1] += 1
            bits ^= low
        if prev is not None:
            diff = value ^ prev
            while diff:
                low = diff & -diff
                changes[low.bit_length() - 1] += 1
                diff ^= low
        prev = value
        for i in range(width):
            columns[i].append(data[i] if i < len(data) else 0)
    ranges = []
    for column in columns:
        column.sort()
        n = len(column)
        ranges.append((column[int(0.1 * (n - 1))], column[int(0.9 * (n - 1))]) if n else (0, 0))
    return len(datas), ones, changes, ranges


def _steady(n: int, ones: int, changes: int) -> int | None:
    """The value a bit held through a phase, or None when it moved."""
    if not n or changes > STEADY_CHANGES:
        return None
    if ones >= STEADY_SHARE * n:
        return 1
    if n - ones >= STEADY_SHARE * n:
        return 0
    return None


def counter_bits(values: list[int], nbits: int) -> set[int]:
    """Bits of rolling counters: chains where a bit changes only when the bit below it falls from 1 to 0
    (a carry), little endian (bit 7 carries into bit 0 of the next byte) or big endian (of the previous)."""
    pairs = list(zip(values, values[1:]))
    if len(pairs) < 4:
        return set()
    changes = [0] * nbits
    for p, q in pairs:
        diff = p ^ q
        while diff:
            low = diff & -diff
            changes[low.bit_length() - 1] += 1
            diff ^= low

    def carried(a: int, b: int, least: int) -> bool:
        if changes[b] < least:
            return False
        bad = sum(1 for p, q in pairs if (p ^ q) >> b & 1 and not (p >> a & 1 and not q >> a & 1))
        return bad <= changes[b] // 20  # a few dropped frames break the pattern

    out: set[int] = set()
    for root in range(nbits):
        if not changes[root] or root in out:
            continue
        chain, a = [root], root
        while True:
            nxt = [a + 1] if a % 8 != 7 else [a + 1, a - 15]
            least = 2 if len(chain) == 1 else 1  # once the chain is clear, one carry is enough for slow upper bits
            b = next((b for b in nxt if 0 <= b < nbits and b not in chain and carried(a, b, least)), None)
            if b is None:
                break
            chain.append(b)
            a = b
        if len(chain) >= 2:
            out.update(chain)
    return out


def compare(phases: list[dict[int, list[bytes]]], id_text: Any, limit: int = 20) -> list[dict[str, Any]]:
    """What an action changes: phases alternate idle (0, 2, 4 ...) and action (1, 3 ...).

    Per ID: bits steady in every phase, with one value while idle and the other during the action (the
    strongest hint: a switch, a lamp, a gear); bits steady while idle that move during the action; bytes
    whose levels do not overlap; IDs that only appear during the action. "Steady" allows a few frames of
    the old value at a phase's start, as people press next a moment before or after they act; counter
    bits are left out. A change seen in every repetition is "confirmed"."""
    idle, action = phases[0::2], phases[1::2]
    repeated = len(phases) >= 3
    out = []
    for key in sorted(set().union(*phases)):
        per = [p.get(key, []) for p in phases]
        row: dict[str, Any] = {"id": id_text(key), "key": key, "frames": [len(f) for f in per]}
        if not any(per[0::2]) and all(per[1::2]):
            row.update({"only_in": "action", "confirmed": repeated, "score": 12 if repeated else 6})
            out.append(row)
            continue
        if not all(per):
            continue  # missing in some phase: a slow message or one that stopped, not a clear hint
        width = min(len(d) for f in per for d in f)
        if width == 0:
            continue
        stats = [_phase_stats(f, width) for f in per]
        values = [int.from_bytes(d[:width], "little") for f in per for d in f]
        counters = counter_bits(values, 8 * width)
        flips, moves = [], []
        for i in range(8 * width):
            if i in counters:
                continue
            steady = [_steady(n, ones[i], changes[i]) for n, ones, changes, _ in stats]
            idle_values = set(steady[0::2])
            if None in idle_values or len(idle_values) != 1:
                continue
            (was,) = idle_values
            act = steady[1::2]
            if all(v is not None and v != was for v in act):
                flips.append({"byte": i // 8, "bit": i % 8, "start": i, "idle": was, "action": 1 - was,
                              "confirmed": repeated})
            elif any(v is None and stats[2 * k + 1][2][i] > STEADY_CHANGES for k, v in enumerate(act)):
                moves.append({"byte": i // 8, "bit": i % 8, "start": i})
        flipped_per_byte: dict[int, int] = {}
        for f in flips:
            flipped_per_byte[f["byte"]] = flipped_per_byte.get(f["byte"], 0) + 1
        shifted = []
        for b in range(width):
            if flipped_per_byte.get(b) == 1 or sum(1 for c in counters if c // 8 == b) >= 2:
                continue  # a single flag is reported as a bit; counter bytes are not levels
            idle_lo = min(stats[k][3][b][0] for k in range(0, len(stats), 2))
            idle_hi = max(stats[k][3][b][1] for k in range(0, len(stats), 2))
            act_lo = min(stats[k][3][b][0] for k in range(1, len(stats), 2))
            act_hi = max(stats[k][3][b][1] for k in range(1, len(stats), 2))
            if idle_hi < act_lo or act_hi < idle_lo:
                shifted.append({"byte": b, "idle": [idle_lo, idle_hi], "action": [act_lo, act_hi],
                                "confirmed": repeated})
        score = (10 + 3 * (len(flips) - 1) if flips else 0) + (6 + 2 * (len(shifted) - 1) if shifted else 0) \
            + (2 if moves else 0)
        if repeated and (flips or shifted):
            score *= 2
        if not score:
            continue
        row.update({"flipped": flips, "moving": moves[:32], "shifted_bytes": shifted,
                    "counter_bits": sorted(counters), "score": score})
        out.append(row)
    out.sort(key=lambda r: -r["score"])
    return out[:limit]
