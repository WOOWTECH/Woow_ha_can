"""CAN signals: bit fields of frames, decoded and encoded the way DBC files define them (stdlib only).

Devices, templates and imported DBC files share one JSON shape, compiled here into Message and
Signal objects. Bit numbering follows DBC:
- Intel (byte_order "little", DBC @1): `start` is the least significant bit, counted LSB first
  through the bytes (bit 8 is bit 0 of byte 1).
- Motorola (byte_order "big", DBC @0): `start` is the most significant bit in the same numbering
  (DBC's "sawtooth"); the signal continues into the high bits of the following byte.

Protocol rules for "no data" decide when a value is unavailable instead of a number:
- j1939: fields of 8 bits or more are valid up to 0xFA in their top byte (FB.. parameter specific,
  FE.. error, FF.. not available); smaller fields lose their two highest values (2 bits: 10 error, 11 n/a);
- n2k: the two highest values (unsigned) or the two highest positive values (signed) mean error / unknown;
- sma: 0x8000-style minimum for signed fields, all ones for unsigned ones.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from decimal import Decimal
import math
import operator
import struct
from typing import Any

EFF_FLAG = 0x80000000
EFF_MASK = 0x1FFFFFFF
SFF_MASK = 0x7FF
INVALID_RULES = ("j1939", "n2k", "sma")
KINDS = ("int", "float", "ascii")
J1939_TP_CM, J1939_TP_DT = 0xEC00, 0xEB00


class DefinitionError(ValueError):
    """A definition that cannot be used; `code` and `detail` name the problem for the panel and agents."""

    def __init__(self, code: str, **detail: Any) -> None:
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code
        self.detail = detail

    def as_dict(self) -> dict[str, Any]:
        return {"code": self.code, **{k: str(v) for k, v in self.detail.items()}}


# ---- small safe expressions for template parameters (0x700 + node_id) --------------------------------
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.LShift: operator.lshift,
        ast.RShift: operator.rshift, ast.BitOr: operator.or_, ast.BitAnd: operator.and_,
        ast.FloorDiv: operator.floordiv}


_HEX = set("0123456789abcdefABCDEF")


def is_hex(text: str) -> bool:
    digits = text.strip()
    if digits[:2].lower() == "0x":
        digits = digits[2:]
    return bool(digits) and all(c in _HEX for c in digits)


def number(value: Any, params: dict[str, Any] | None = None) -> int:
    """An int from an int, hex text ("7E8", "0x7E8": hex, as everywhere in this integration), or an
    integer expression over template parameters ("0x700 + node_id"; write hex literals with 0x there)."""
    if isinstance(value, bool):
        raise DefinitionError("bad_number", value=value)
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    text = str(value).strip()
    if is_hex(text):
        return int(text[2:] if text[:2].lower() == "0x" else text, 16)
    params = params or {}
    try:
        tree = ast.parse(text, mode="eval")
    except SyntaxError as err:
        raise DefinitionError("bad_number", value=value) from err

    def run(node: ast.AST) -> int:
        if isinstance(node, ast.Expression):
            return run(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool):
            return node.value
        if isinstance(node, ast.Name):
            if node.id not in params:
                raise DefinitionError("unknown_param", param=node.id)
            return number(params[node.id])
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](run(node.left), run(node.right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -run(node.operand)
        raise DefinitionError("bad_expression", expression=text)

    return run(tree)


def parse_can_id(value: Any, params: dict[str, Any] | None = None, extended: bool | None = None) -> tuple[int, bool]:
    """A CAN ID and whether it is 29-bit: as written ("7DF" 11-bit, "18DB33F1" 29-bit), or by its size."""
    can_id = number(value, params)
    if extended is None:
        text = str(value).strip()
        digits = text[2:] if text[:2].lower() == "0x" else text
        extended = can_id > SFF_MASK or (is_hex(text) and len(digits) > 3)
    if can_id > (EFF_MASK if extended else SFF_MASK) or can_id < 0:
        raise DefinitionError("bad_id", can_id=str(value))
    return can_id, bool(extended)


def frame_data(value: Any, params: dict[str, Any] | None = None) -> bytes:
    """Frame bytes from hex text ("40 41 60 00 00 00 00 00") or a list of byte expressions (["0x01", "node_id"])."""
    if isinstance(value, (list, tuple)):
        out = [number(v, params) for v in value]
        if any(not 0 <= b <= 0xFF for b in out):
            raise DefinitionError("bad_data", data=str(value))
        return bytes(out)
    try:
        return bytes.fromhex(str(value).replace(" ", ""))
    except ValueError as err:
        raise DefinitionError("bad_data", data=str(value)) from err


def decimal_number(value: Any) -> int:
    """A PGN or other decimal number: ints and decimal text."""
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    text = str(value).strip()
    if text.isdigit():
        return int(text)
    raise DefinitionError("bad_number", value=value)


def decimals(factor: float) -> int:
    """Decimal places a factor produces: 0.1 -> 1, 0.00390625 -> 8, 5 -> 0."""
    if factor == 0 or not math.isfinite(factor):
        return 0
    exponent = Decimal(repr(abs(factor))).normalize().as_tuple().exponent
    return max(0, -int(exponent)) if isinstance(exponent, int) else 0


def j1939_pgn(raw: int) -> int:
    """The parameter group number of a 29-bit J1939 / NMEA 2000 identifier."""
    pf = (raw >> 16) & 0xFF
    pgn = ((raw >> 8) & 0x3FF00) | (raw >> 8 & 0xFF if pf >= 240 else 0)
    return pgn & 0x3FFFF


@dataclass
class Signal:
    """One field of a message."""

    name: str
    start: int
    length: int
    byte_order: str = "little"
    signed: bool = False
    kind: str = "int"
    factor: float = 1.0
    offset: float = 0.0
    minimum: float | None = None
    maximum: float | None = None
    unit: str = ""
    values: dict[int, str] = field(default_factory=dict)
    invalid: str | list[int] | None = None
    mux_by: str | None = None  # the multiplexor this signal depends on
    mux_values: list[tuple[int, int]] = field(default_factory=list)  # raw value ranges of that multiplexor
    multiplexor: bool = False
    start_value: int | None = None  # raw value used when building a frame from nothing (GenSigStartValue)
    derive: dict[str, Any] | None = None  # {"op": "product", "of": [a, b]}: computed from other signals
    decoder_field: str | None = None  # a value a message decoder produces (DM1 counts, lists)
    comment: str = ""
    entity: dict[str, Any] | None = None  # set when the signal is a Home Assistant entity

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise DefinitionError("bad_kind", signal=self.name, kind=self.kind)
        if self.byte_order not in ("little", "big"):
            raise DefinitionError("bad_byte_order", signal=self.name, byte_order=self.byte_order)
        if not self.derive and not self.decoder_field:
            if not 0 <= self.start < 512 or not 1 <= self.length <= 512:
                raise DefinitionError("bad_bits", signal=self.name, start=self.start, length=self.length)
            if self.kind == "float" and self.length not in (32, 64):
                raise DefinitionError("bad_float", signal=self.name, length=self.length)
            if self.kind == "ascii" and (self.length % 8 or (self.byte_order == "little" and self.start % 8)
                                         or (self.byte_order == "big" and self.start % 8 != 7)):
                raise DefinitionError("bad_ascii", signal=self.name)
        self.values = {int(k): str(v) for k, v in (self.values or {}).items()}
        self._mask = (1 << self.length) - 1 if self.length else 0
        self._msb0 = (self.start // 8) * 8 + (7 - self.start % 8)
        self._need = self.start + self.length if self.byte_order == "little" else self._msb0 + self.length
        self._decimals = decimals(self.factor)

    # ---- bits -------------------------------------------------------------------------------
    @property
    def bits_needed(self) -> int:
        """How many data bits (from the start of the frame) the signal reaches."""
        return self._need

    def raw(self, data: bytes) -> int | None:
        """The field's bits as an unsigned int; None when the frame is too short to hold it."""
        n = len(data) * 8
        if self._need > n:
            return None
        if self.byte_order == "little":
            return (int.from_bytes(data, "little") >> self.start) & self._mask
        return (int.from_bytes(data, "big") >> (n - self._need)) & self._mask

    def insert(self, data: bytearray, raw: int) -> None:
        """Write a raw (unsigned) value into the frame data."""
        n = len(data) * 8
        if self._need > n:
            raise DefinitionError("frame_too_short", signal=self.name, bytes=len(data))
        raw &= self._mask
        if self.byte_order == "little":
            value = int.from_bytes(data, "little")
            value = (value & ~(self._mask << self.start)) | (raw << self.start)
            data[:] = value.to_bytes(len(data), "little")
        else:
            shift = n - self._need
            value = int.from_bytes(data, "big")
            value = (value & ~(self._mask << shift)) | (raw << shift)
            data[:] = value.to_bytes(len(data), "big")

    def signed_value(self, raw: int) -> int:
        if self.signed and raw >> (self.length - 1) & 1:
            return raw - (1 << self.length)
        return raw

    # ---- values -----------------------------------------------------------------------------
    def invalid_raw(self, raw: int) -> bool:
        rule = self.invalid
        if not rule:
            return False
        n = self.length
        if isinstance(rule, list):
            return raw in rule
        if rule == "j1939":
            if n >= 8:
                return (raw >> (n - 8)) > 0xFA
            return n >= 2 and raw >= (1 << n) - 2
        if rule == "n2k":
            if n < 2:
                return False
            if self.signed:
                return self.signed_value(raw) >= (1 << (n - 1)) - 2
            return raw >= (1 << n) - 2
        if rule == "sma":
            return raw == (1 << (n - 1) if self.signed else (1 << n) - 1)
        return False

    def physical(self, raw: int) -> float | int | str:
        if self.kind == "float":
            number = struct.unpack(">f" if self.length == 32 else ">d",
                                   raw.to_bytes(self.length // 8, "big"))[0]
            return number * self.factor + self.offset
        value = self.signed_value(raw) * self.factor + self.offset
        if self._decimals == 0 and float(value).is_integer():
            return int(value)
        return round(value, min(12, self._decimals + 1))

    def decode_raw(self, data: bytes) -> tuple[int | None, Any]:
        """(raw bits, value): the value is a number, a value-table label, text, or None (no data)."""
        raw = self.raw(data)
        if raw is None:
            return None, None
        if self.kind == "ascii":
            first = self.start // 8 if self.byte_order == "little" else self._msb0 // 8
            text = bytes(data[first:first + self.length // 8]).split(b"\0")[0]
            return raw, text.decode("latin-1").rstrip(" \0") or None
        if raw in self.values:
            return raw, self.values[raw]
        if self.invalid_raw(raw):
            return raw, None
        return raw, self.physical(raw)

    def to_raw(self, value: float | int | str) -> int:
        """A physical value (or a value-table label) as the raw bits to send."""
        if isinstance(value, str):
            for raw, label in self.values.items():
                if label == value:
                    return raw
            try:
                value = float(value)
            except ValueError as err:
                raise DefinitionError("bad_value", signal=self.name, value=value) from err
        if self.minimum is not None and self.maximum is not None and self.minimum < self.maximum:
            if not self.minimum <= value <= self.maximum:
                raise DefinitionError("out_of_range", signal=self.name, value=value,
                                      minimum=self.minimum, maximum=self.maximum)
        if self.kind == "float":
            packed = struct.pack(">f" if self.length == 32 else ">d", (float(value) - self.offset) / self.factor)
            return int.from_bytes(packed, "big")
        raw = round((float(value) - self.offset) / self.factor)
        low, high = (-(1 << (self.length - 1)), (1 << (self.length - 1)) - 1) if self.signed else (0, self._mask)
        if not low <= raw <= high:
            raise DefinitionError("out_of_range", signal=self.name, value=value)
        return raw & self._mask

    # ---- JSON -------------------------------------------------------------------------------
    @classmethod
    def from_dict(cls, raw: dict[str, Any], params: dict[str, Any] | None = None) -> Signal:
        params = params or {}
        try:
            mux_values = [tuple(r) if isinstance(r, (list, tuple)) else (int(r), int(r))
                          for r in raw.get("mux_values") or []]
            if raw.get("mux_value") is not None:
                mux_values.append((int(raw["mux_value"]), int(raw["mux_value"])))
            return cls(
                name=str(raw["name"]),
                start=int(raw.get("start", 0)),
                length=int(raw.get("length", 0)),
                byte_order=str(raw.get("byte_order", "little")),
                signed=bool(raw.get("signed", False)),
                kind=str(raw.get("kind", "int")),
                factor=float(raw.get("factor", 1)),
                offset=float(raw.get("offset", 0)),
                minimum=None if raw.get("minimum") is None else float(raw["minimum"]),
                maximum=None if raw.get("maximum") is None else float(raw["maximum"]),
                unit=str(raw.get("unit", "")),
                values=raw.get("values") or {},
                invalid=raw.get("invalid"),
                mux_by=raw.get("mux_by"),
                mux_values=[(int(a), int(b)) for a, b in mux_values],
                multiplexor=bool(raw.get("multiplexor", False)),
                start_value=None if raw.get("start_value") is None else int(raw["start_value"]),
                derive=raw.get("derive"),
                decoder_field=raw.get("decoder_field"),
                comment=str(raw.get("comment", "")),
                entity=raw.get("entity"),
            )
        except (KeyError, TypeError, ValueError) as err:
            if isinstance(err, DefinitionError):
                raise
            raise DefinitionError("bad_signal", signal=raw.get("name", "?"), error=str(err)) from err

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"name": self.name, "start": self.start, "length": self.length,
                               "byte_order": self.byte_order, "signed": self.signed}
        for key, default in (("kind", "int"), ("factor", 1.0), ("offset", 0.0), ("unit", ""), ("comment", "")):
            if getattr(self, key) != default:
                out[key] = getattr(self, key)
        for key in ("minimum", "maximum", "invalid", "mux_by", "start_value", "derive", "decoder_field", "entity"):
            if getattr(self, key) is not None:
                out[key] = getattr(self, key)
        if self.values:
            out["values"] = {str(k): v for k, v in self.values.items()}
        if self.mux_values:
            out["mux_values"] = [list(r) for r in self.mux_values]
        if self.multiplexor:
            out["multiplexor"] = True
        return out


@dataclass
class Message:
    """A frame layout: which frames it matches and the signals in them."""

    name: str
    can_id: int = 0
    extended: bool = False
    length: int = 8
    signals: list[Signal] = field(default_factory=list)
    cycle_ms: int | None = None
    id_mask: int | None = None  # bits of the ID that must match; None = all of them
    pgn: int | None = None  # J1939 / NMEA 2000: match by PGN, any priority
    source: int | None = None  # J1939 / NMEA 2000 source address to accept (None = any)
    filters: list[tuple[int, tuple[int, ...]]] = field(default_factory=list)  # (byte, values it may have)
    send: bool = False  # a frame this integration sends (commands), not one it decodes
    base: bytes | None = None  # fixed bytes of a sent frame, under its signals ("data" in JSON)
    transport: str | None = None  # "j1939_tp" (BAM reassembly) or "n2k_fast" (fast-packet)
    decoder: str | None = None  # "j1939_dm1"
    comment: str = ""
    senders: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.transport not in (None, "j1939_tp", "n2k_fast"):
            raise DefinitionError("bad_transport", message=self.name, transport=self.transport)
        if self.decoder not in (None, "j1939_dm1"):
            raise DefinitionError("bad_decoder", message=self.name, decoder=self.decoder)
        if self.pgn is not None:
            self.extended = True
        names = [s.name for s in self.signals]
        if len(set(names)) != len(names):
            raise DefinitionError("duplicate_signal", message=self.name)
        self.by_name = {s.name: s for s in self.signals}
        for sig in self.signals:
            if sig.mux_by and sig.mux_by not in self.by_name:
                raise DefinitionError("unknown_multiplexor", message=self.name, signal=sig.name, mux=sig.mux_by)
            if sig.derive:
                missing = [n for n in sig.derive.get("of", []) if n not in self.by_name]
                if missing or sig.derive.get("op") not in DERIVE_OPS:
                    raise DefinitionError("bad_derive", message=self.name, signal=sig.name)

    # ---- matching ---------------------------------------------------------------------------
    @property
    def raw_id(self) -> int:
        return (self.can_id & EFF_MASK) | EFF_FLAG if self.extended else self.can_id & SFF_MASK

    @property
    def exact(self) -> bool:
        """Matched by the whole raw ID (no mask, no PGN)."""
        return self.pgn is None and self.id_mask is None

    def matches(self, raw: int, data: bytes | None = None) -> bool:
        ext = bool(raw & EFF_FLAG)
        if self.pgn is not None:
            if not ext or j1939_pgn(raw) != self.pgn:
                return False
            if self.source is not None and raw & 0xFF != self.source:
                return False
        elif ext != self.extended:
            return False
        elif self.id_mask is not None:
            if (raw & self.id_mask) != (self.can_id & self.id_mask):
                return False
        elif (raw & (EFF_MASK if ext else SFF_MASK)) != self.can_id:
            return False
        if data is not None and self.filters:
            return all(len(data) > i and data[i] in vs for i, vs in self.filters)
        return True

    @property
    def timeout(self) -> float | None:
        """Seconds without a frame after which its values count as gone: max(3 cycles, 5 s)."""
        return max(3 * self.cycle_ms / 1000, 5.0) if self.cycle_ms else None

    # ---- decoding ---------------------------------------------------------------------------
    def decode(self, data: bytes, only: set[str] | None = None) -> dict[str, Any]:
        """{signal name: value} for the signals present in this frame (multiplexing honoured)."""
        values: dict[str, Any] = {}
        raws: dict[str, int | None] = {}
        extra = decode_dm1(data) if self.decoder == "j1939_dm1" else None

        def get(sig: Signal) -> Any:
            if sig.name in values or sig.name in raws:
                return values.get(sig.name)
            if sig.mux_by is not None:
                mux = self.by_name[sig.mux_by]
                get(mux)
                mraw = raws.get(mux.name)
                if mraw is None or not any(lo <= mraw <= hi for lo, hi in sig.mux_values):
                    raws[sig.name] = None
                    return None
            if sig.decoder_field is not None:
                raws[sig.name] = None
                values[sig.name] = None if extra is None else extra.get(sig.decoder_field)
                return values[sig.name]
            if sig.derive:
                parts = [get(self.by_name[n]) for n in sig.derive.get("of", [])]
                raws[sig.name] = None
                values[sig.name] = derive(sig, parts)
                return values[sig.name]
            raw, value = sig.decode_raw(data)
            raws[sig.name] = raw
            values[sig.name] = value
            return value

        for sig in self.signals:
            if only is None or sig.name in only:
                get(sig)
        return {k: v for k, v in values.items() if only is None or k in only}

    def build(self, values: dict[str, Any], base: bytes | None = None) -> bytes:
        """Frame data with the given signal values, over `base` (the last frame) or the fixed bytes and start
        values."""
        base = base or self.base
        data = bytearray(base[:self.length] if base else bytes(self.length))
        if len(data) < self.length:
            data.extend(bytes(self.length - len(data)))
        if not base or base is self.base:
            for sig in self.signals:
                if sig.start_value is not None and not sig.derive and not sig.decoder_field:
                    sig.insert(data, sig.start_value)
        for name, value in values.items():
            sig = self.by_name.get(name)
            if sig is None:
                raise DefinitionError("unknown_signal", message=self.name, signal=name)
            child = sig
            while child.mux_by is not None and child.mux_values:  # select the branch, up to the root
                parent = self.by_name[child.mux_by]
                parent.insert(data, child.mux_values[0][0])
                child = parent
            sig.insert(data, sig.to_raw(value))
        return bytes(data)

    # ---- JSON -------------------------------------------------------------------------------
    @classmethod
    def from_dict(cls, raw: dict[str, Any], params: dict[str, Any] | None = None) -> Message:
        params = params or {}
        try:
            can_id_text = raw.get("can_id")
            pgn = raw.get("pgn")
            if can_id_text is None and pgn is None:
                raise DefinitionError("no_id", message=raw.get("name", "?"))
            can_id = 0
            extended = bool(raw.get("extended", False))
            if can_id_text is not None:
                can_id = number(can_id_text, params)
                if "extended" not in raw:  # like everywhere: 1-3 hex digits = 11-bit, longer = 29-bit
                    text = str(can_id_text).strip()
                    digits = text[2:] if text[:2].lower() == "0x" else text
                    extended = can_id > SFF_MASK or (is_hex(text) and len(digits) > 3)
            source = raw.get("source")
            if isinstance(source, str) and source in params and params[source] in (None, "", "any"):
                source = None
            source = None if source in (None, "", "any") else number(source, params)
            cycle = raw.get("cycle_ms")
            cycle = number(cycle, params) if isinstance(cycle, str) else cycle
            filters = [(int(f["byte"]), tuple(number(v, params) for v in (f["values"] if "values" in f else [f["value"]])))
                       for f in raw.get("filters") or []]
            base = frame_data(raw["data"], params) if raw.get("data") else None
            return cls(
                name=str(raw.get("name") or f"{can_id:X}"),
                can_id=can_id & EFF_MASK,
                extended=extended,
                length=int(raw.get("length", 8)),
                signals=[Signal.from_dict(s, params) for s in raw.get("signals") or []],
                cycle_ms=None if cycle in (None, 0) else int(cycle),
                id_mask=None if raw.get("id_mask") is None else number(raw["id_mask"], params),
                pgn=None if pgn is None else decimal_number(pgn),
                source=source,
                filters=filters,
                send=bool(raw.get("send", False)),
                base=base,
                transport=raw.get("transport"),
                decoder=raw.get("decoder"),
                comment=str(raw.get("comment", "")),
                senders=list(raw.get("senders") or []),
            )
        except (KeyError, TypeError, ValueError) as err:
            if isinstance(err, DefinitionError):
                raise
            raise DefinitionError("bad_message", message=raw.get("name", "?"), error=str(err)) from err

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"name": self.name}
        if self.pgn is not None:
            out["pgn"] = self.pgn
            if self.source is not None:
                out["source"] = self.source
        else:
            out["can_id"] = f"{self.can_id:08X}" if self.extended else f"{self.can_id:03X}"
            out["extended"] = self.extended
        out["length"] = self.length
        if self.cycle_ms:
            out["cycle_ms"] = self.cycle_ms
        if self.id_mask is not None:
            out["id_mask"] = f"{self.id_mask:08X}"
        if self.filters:
            out["filters"] = [{"byte": b, "value": vs[0]} if len(vs) == 1 else {"byte": b, "values": list(vs)}
                              for b, vs in self.filters]
        if self.send:
            out["send"] = True
        if self.base is not None:
            out["data"] = self.base.hex(" ").upper()
        for key in ("transport", "decoder"):
            if getattr(self, key):
                out[key] = getattr(self, key)
        if self.comment:
            out["comment"] = self.comment
        if self.senders:
            out["senders"] = self.senders
        out["signals"] = [s.as_dict() for s in self.signals]
        return out

    def label(self) -> str:
        if self.pgn is not None:
            return f"PGN {self.pgn}" + (f" SA {self.source:02X}" if self.source is not None else "")
        return f"{self.can_id:08X}" if self.extended else f"{self.can_id:03X}"


# ---- derived values --------------------------------------------------------------------------------
DERIVE_OPS = ("product", "sum", "difference", "any", "nonzero", "present", "masked_lookup")


def derive(sig: Signal, parts: list[Any]) -> Any:
    """product / sum / difference of numbers; any (1 when a part equals `equals`, default 1); nonzero; present
    (1 whenever the message arrives: a node's heartbeat says it is there)."""
    op = sig.derive.get("op") if sig.derive else None
    if op == "present":
        return 1
    if op == "masked_lookup":  # the first [mask, value, label] whose value equals the part masked (CiA 402 states)
        if not parts or not isinstance(parts[0], int) or isinstance(parts[0], bool):
            return None
        for mask, value, label in sig.derive.get("table", []):
            if parts[0] & number(mask) == number(value):
                return label
        return None
    if op == "any":
        want = sig.derive.get("equals", 1)
        known = [p for p in parts if p is not None]
        if not known:
            return None
        return 1 if any(p == want for p in known) else 0
    if op == "nonzero":
        return None if not parts or parts[0] is None else int(parts[0] != 0)
    if any(not isinstance(p, (int, float)) or isinstance(p, bool) for p in parts):
        return None
    result = math.prod(parts) if op == "product" else sum(parts) if op == "sum" else parts[0] - sum(parts[1:])
    return round(result * sig.factor + sig.offset, 6)


# ---- J1939 DM1 ------------------------------------------------------------------------------------
LAMPS = ("protect_lamp", "amber_warning_lamp", "red_stop_lamp", "malfunction_lamp")


def decode_dm1(data: bytes) -> dict[str, Any]:
    """DM1 / DM2 payload: lamp states and the diagnostic trouble codes (SPN, FMI, occurrences)."""
    out: dict[str, Any] = {}
    if len(data) < 2:
        return out
    for i, name in enumerate(LAMPS):
        state = (data[0] >> (2 * i)) & 3
        out[name] = True if state == 1 else False if state == 0 else None
    dtcs = []
    for pos in range(2, len(data) - 3, 4):
        b3, b4, b5, b6 = data[pos:pos + 4]
        spn = b3 | (b4 << 8) | ((b5 & 0xE0) << 11)
        fmi = b5 & 0x1F
        if spn == 0 and fmi == 0 and (b6 & 0x7F) == 0:
            continue  # "no active fault" filler
        if b3 == b4 == b5 == b6 == 0xFF:
            continue  # padding
        dtcs.append({"spn": spn, "fmi": fmi, "occurrences": b6 & 0x7F, "conversion_method": b6 >> 7})
    out["dtcs"] = dtcs
    out["dtc_count"] = len(dtcs)
    out["dtc_text"] = ", ".join(f"SPN {d['spn']} FMI {d['fmi']}" for d in dtcs) or "none"
    return out


# ---- multi-frame transports ----------------------------------------------------------------------
class J1939Transport:
    """Reassembles J1939 broadcast transfers (TP.CM BAM + TP.DT) per source address."""

    TIMEOUT = 0.75  # s allowed between packets (T1)

    def __init__(self) -> None:
        self._sessions: dict[int, dict[str, Any]] = {}

    def feed(self, ts: float, raw: int, data: bytes) -> tuple[int, int, bytes] | None:
        """A TP frame in; (pgn, source address, payload) out when a transfer completes."""
        pgn = j1939_pgn(raw)
        sa = raw & 0xFF
        if pgn == J1939_TP_CM and len(data) >= 8:
            if data[0] == 32:  # BAM
                size = data[1] | (data[2] << 8)
                self._sessions[sa] = {"pgn": data[5] | (data[6] << 8) | (data[7] << 16), "size": size,
                                      "packets": data[3], "parts": {}, "t": ts}
            elif data[0] == 255:  # abort
                self._sessions.pop(sa, None)
            return None
        if pgn != J1939_TP_DT or len(data) < 2:
            return None
        session = self._sessions.get(sa)
        if session is None:
            return None
        if ts - session["t"] > self.TIMEOUT:
            self._sessions.pop(sa, None)
            return None
        session["t"] = ts
        session["parts"][data[0]] = bytes(data[1:8])
        if len(session["parts"]) < session["packets"]:
            return None
        self._sessions.pop(sa, None)
        try:
            payload = b"".join(session["parts"][n] for n in range(1, session["packets"] + 1))
        except KeyError:
            return None
        return session["pgn"], sa, payload[:session["size"]]


class FastPacket:
    """Reassembles NMEA 2000 fast-packet messages per (source address, PGN)."""

    def __init__(self) -> None:
        self._sessions: dict[tuple[int, int], dict[str, Any]] = {}

    def feed(self, raw: int, data: bytes) -> bytes | None:
        if not data:
            return None
        key = (raw & 0xFF, j1939_pgn(raw))
        seq, index = data[0] >> 5, data[0] & 0x1F
        if index == 0:
            if len(data) < 2:
                return None
            session = {"seq": seq, "size": data[1], "data": bytearray(data[2:8]), "next": 1}
            self._sessions[key] = session
        else:
            session = self._sessions.get(key)
            if session is None or session["seq"] != seq or session["next"] != index:
                self._sessions.pop(key, None)
                return None
            session["data"].extend(data[1:8])
            session["next"] += 1
        if len(session["data"]) >= session["size"]:
            self._sessions.pop(key, None)
            return bytes(session["data"][:session["size"]])
        return None
