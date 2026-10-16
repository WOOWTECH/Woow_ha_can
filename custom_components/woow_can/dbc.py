"""Read (and write) the part of the DBC format CAN tools use for messages and signals (stdlib only).

Understood: BO_ messages, SG_ signals (Intel / Motorola, signed, simple and extended multiplexing),
SIG_VALTYPE_ (float), VAL_ / VAL_TABLE_ value tables, CM_ comments, and three attributes:
GenMsgCycleTime (timeouts), VFrameFormat (J1939 parameter groups), GenSigStartValue. Anything else
is skipped and counted in the import report, never a reason to fail the whole file.
J1939 messages (VFrameFormat J1939PG, or ProtocolType "J1939") are matched by PGN, any priority and
any source address, as the DBC's IDs carry a placeholder source address.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

from .signals import DefinitionError, Message, Signal, j1939_pgn

_BO = re.compile(r"^BO_\s+(\d+)\s+([A-Za-z0-9_]+)\s*:\s*(\d+)\s+(\S+)")
_SG = re.compile(
    r"^SG_\s+([A-Za-z0-9_]+)\s*(M|m\d+M?)?\s*:\s*(\d+)\|(\d+)@([01])([+-])\s*"
    r"\(\s*([^,\s]+)\s*,\s*([^)\s]+)\s*\)\s*\[\s*([^|\]]*)\|([^\]]*)\]\s*\"((?:[^\"\\]|\\.)*)\"\s*(.*)$"
)
_PAIRS = re.compile(r"(-?\d+)\s+\"((?:[^\"\\]|\\.)*)\"")
SKIPPED = ("VERSION", "NS_", "BS_", "BU_", "EV_", "ENVVAR_DATA_", "BO_TX_BU_", "CAT_DEF_", "CAT_", "FILTER",
           "SIG_GROUP_", "SIG_TYPE_REF_", "SGTYPE_", "SIG_VALTYPE_", "BA_DEF_SGTYPE_", "BA_SGTYPE_",
           "SIGTYPE_VALTYPE_", "BA_DEF_REL_", "BA_REL_", "BA_DEF_DEF_REL_", "BU_SG_REL_", "BU_EV_REL_",
           "BU_BO_REL_", "SG_MUL_VAL_")
VECTOR_INDEPENDENT = 0xC0000000


@dataclass
class DbcFile:
    messages: list[dict[str, Any]] = field(default_factory=list)  # Message JSON definitions
    nodes: list[str] = field(default_factory=list)
    comment: str = ""
    warnings: list[str] = field(default_factory=list)
    skipped: int = 0  # statements not understood (or not needed)

    def report(self) -> dict[str, Any]:
        return {"messages": len(self.messages), "signals": sum(len(m["signals"]) for m in self.messages),
                "nodes": self.nodes, "skipped_statements": self.skipped, "warnings": self.warnings[:30],
                "warning_count": len(self.warnings)}


def decode_text(raw: bytes) -> str:
    """DBC files are usually cp1252; take UTF-8 when the bytes are valid UTF-8."""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace")


def _unescape(text: str) -> str:
    return text.replace('\\"', '"').replace("\\\\", "\\")


_SINGLE_LINE = ("VERSION", "NS_", "BS_", "BU_")


def _complete(buf: str) -> bool:
    """A statement ends with ';' outside quotes (comments may span lines and contain ';')."""
    in_quote = escaped = False
    for ch in buf:
        if escaped:
            escaped = False
        elif ch == "\\":
            escaped = True
        elif ch == '"':
            in_quote = not in_quote
    return not in_quote and buf.rstrip().endswith(";")


def _statements(text: str) -> list[str]:
    """Logical statements: BO_ / SG_ and header lines on their own; the rest run to a ';' outside quotes."""
    out: list[str] = []
    buf = ""
    for line in text.splitlines():
        if buf:
            buf += "\n" + line
            if _complete(buf):
                out.append(buf.strip())
                buf = ""
            continue
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        first = stripped.split(None, 1)[0].rstrip(":")
        if stripped.startswith(("BO_ ", "SG_ ")) or first in _SINGLE_LINE:
            out.append(stripped)
            continue
        if line[:1] in " \t" and len(stripped.split()) == 1:  # the keyword list under NS_
            continue
        if _complete(stripped):
            out.append(stripped)
        else:
            buf = stripped
    if buf.strip():
        out.append(buf.strip())
    return out


def _number(text: str) -> float:
    return float(text.strip())


def parse(content: str | bytes) -> DbcFile:
    """Parse DBC text into JSON message definitions plus a report of what was skipped."""
    text = decode_text(content) if isinstance(content, bytes) else content
    result = DbcFile()
    messages: dict[int, dict[str, Any]] = {}  # DBC id -> message (signals as lists of dicts)
    message_comments: dict[int, str] = {}
    signal_comments: dict[tuple[int, str], str] = {}
    cycle: dict[int, int] = {}
    frame_format: dict[int, str] = {}
    start_values: dict[tuple[int, str], int] = {}
    value_tables: dict[str, dict[int, str]] = {}
    values: dict[tuple[int, str], dict[int, str]] = {}
    valtype: dict[tuple[int, str], int] = {}
    mux_ranges: dict[tuple[int, str], tuple[str, list[tuple[int, int]]]] = {}
    enums: dict[str, list[str]] = {}
    defaults: dict[str, str] = {}
    protocol = ""
    current: dict[str, Any] | None = None

    for st in _statements(text):
        head = st.split(None, 1)[0].rstrip(":")
        if st.startswith("BO_ "):
            m = _BO.match(st)
            if not m:
                result.warnings.append(f"message line not understood: {st[:80]}")
                current = None
                continue
            dbc_id = int(m.group(1))
            if dbc_id == VECTOR_INDEPENDENT:
                current = None
                continue
            current = {"dbc_id": dbc_id, "name": m.group(2), "length": int(m.group(3)),
                       "senders": [] if m.group(4) == "Vector__XXX" else [m.group(4)], "signals": []}
            messages[dbc_id] = current
            continue
        if st.startswith("SG_ "):
            if current is None:
                continue
            m = _SG.match(st)
            if not m:
                result.warnings.append(f"{current['name']}: signal line not understood: {st[:80]}")
                continue
            name, mux, start, length, order, sign, factor, offset, low, high, unit, _receivers = m.groups()
            sig: dict[str, Any] = {
                "name": name, "start": int(start), "length": int(length),
                "byte_order": "little" if order == "1" else "big", "signed": sign == "-",
                "factor": _number(factor), "offset": _number(offset), "unit": _unescape(unit),
            }
            try:
                lo, hi = _number(low or "0"), _number(high or "0")
                if lo != hi:
                    sig["minimum"], sig["maximum"] = lo, hi
            except ValueError:
                pass
            if mux == "M":
                sig["multiplexor"] = True
            elif mux:
                sig["_mux"] = int(mux[1:].rstrip("M"))
                if mux.endswith("M"):
                    sig["multiplexor"] = True
            current["signals"].append(sig)
            continue
        if head == "CM_":
            m = re.match(r'^CM_\s+(BO_|SG_|BU_|EV_)?\s*(\d+)?\s*([A-Za-z0-9_]+)?\s*"((?:[^"\\]|\\.)*)"\s*;?$',
                         st, re.S)
            if not m:
                m2 = re.match(r'^CM_\s+"((?:[^"\\]|\\.)*)"\s*;?$', st, re.S)
                if m2:
                    result.comment = _unescape(m2.group(1))
                else:
                    result.skipped += 1
                continue
            kind, ident, sig_name, comment = m.groups()
            if kind == "BO_" and ident:
                message_comments[int(ident)] = _unescape(comment)
            elif kind == "SG_" and ident and sig_name:
                signal_comments[(int(ident), sig_name)] = _unescape(comment)
            elif kind is None and ident is None:
                result.comment = _unescape(comment)
            continue
        if head == "BA_DEF_DEF_":
            m = re.match(r'^BA_DEF_DEF_\s+"([^"]+)"\s+(.+?)\s*;$', st, re.S)
            if m:
                defaults[m.group(1)] = m.group(2).strip().strip('"')
            continue
        if head == "BA_DEF_":
            m = re.match(r'^BA_DEF_\s+(?:BO_|SG_|BU_|EV_)?\s*"([^"]+)"\s+ENUM\s+(.+?)\s*;$', st, re.S)
            if m:
                enums[m.group(1)] = [v.strip().strip('"') for v in m.group(2).split(",")]
            continue
        if head == "BA_":
            m = re.match(r'^BA_\s+"([^"]+)"\s+(?:(BO_|SG_|BU_|EV_)\s+)?(.+?)\s*;$', st, re.S)
            if not m:
                result.skipped += 1
                continue
            attr, kind, rest = m.groups()
            parts = rest.split()
            try:
                if attr == "ProtocolType" and kind is None:
                    protocol = rest.strip().strip('"')
                elif attr == "GenMsgCycleTime" and kind == "BO_":
                    cycle[int(parts[0])] = int(float(parts[1]))
                elif attr == "VFrameFormat" and kind == "BO_":
                    value = parts[1].strip('"')
                    names = enums.get("VFrameFormat", [])
                    frame_format[int(parts[0])] = names[int(value)] if value.isdigit() and int(value) < len(names) else value
                elif attr == "GenSigStartValue" and kind == "SG_":
                    start_values[(int(parts[0]), parts[1])] = int(float(parts[2]))
            except (IndexError, ValueError):
                result.warnings.append(f"attribute not understood: {st[:80]}")
            continue
        if head == "VAL_TABLE_":
            m = re.match(r"^VAL_TABLE_\s+([A-Za-z0-9_]+)\s+(.*?);?$", st, re.S)
            if m:
                value_tables[m.group(1)] = {int(a): _unescape(b) for a, b in _PAIRS.findall(m.group(2))}
            continue
        if head == "VAL_":
            m = re.match(r"^VAL_\s+(\d+)\s+([A-Za-z0-9_]+)\s+(.*?);?$", st, re.S)
            if m:
                pairs = _PAIRS.findall(m.group(3))
                if pairs:
                    values[(int(m.group(1)), m.group(2))] = {int(a): _unescape(b) for a, b in pairs}
                elif m.group(3).strip() in value_tables:
                    values[(int(m.group(1)), m.group(2))] = value_tables[m.group(3).strip()]
            continue
        if head == "SIG_VALTYPE_":
            m = re.match(r"^SIG_VALTYPE_\s+(\d+)\s+([A-Za-z0-9_]+)\s*:?\s*(\d)\s*;?$", st)
            if m:
                valtype[(int(m.group(1)), m.group(2))] = int(m.group(3))
            continue
        if head == "SG_MUL_VAL_":
            m = re.match(r"^SG_MUL_VAL_\s+(\d+)\s+([A-Za-z0-9_]+)\s+([A-Za-z0-9_]+)\s+(.*?);?$", st, re.S)
            if m:
                ranges = [(int(a), int(b)) for a, b in re.findall(r"(\d+)\s*-\s*(\d+)", m.group(4))]
                mux_ranges[(int(m.group(1)), m.group(2))] = (m.group(3), ranges)
            continue
        if head == "BU_":
            result.nodes = [n for n in st.split(":", 1)[-1].split() if n]
            continue
        if head in SKIPPED or head.startswith(("BA_", "NS_")):
            result.skipped += 1
            continue
        result.skipped += 1

    j1939_file = protocol.upper() == "J1939"
    default_cycle = int(float(defaults.get("GenMsgCycleTime", "0") or 0))
    for dbc_id, msg in messages.items():
        extended = bool(dbc_id & 0x80000000)
        can_id = dbc_id & 0x1FFFFFFF
        fmt = frame_format.get(dbc_id, "")
        definition: dict[str, Any] = {"name": msg["name"], "length": msg["length"]}
        if extended and (fmt == "J1939PG" or (j1939_file and not fmt)):
            definition["pgn"] = j1939_pgn(can_id | 0x80000000)
        else:
            definition["can_id"] = f"{can_id:08X}" if extended else f"{can_id:03X}"
            definition["extended"] = extended
        if cycle.get(dbc_id, default_cycle):
            definition["cycle_ms"] = cycle.get(dbc_id, default_cycle)
        if msg["dbc_id"] in message_comments:
            definition["comment"] = message_comments[msg["dbc_id"]]
        if msg["senders"]:
            definition["senders"] = msg["senders"]
        roots = [s["name"] for s in msg["signals"] if s.get("multiplexor") and "_mux" not in s]
        signals = []
        for sig in msg["signals"]:
            key = (dbc_id, sig["name"])
            if key in mux_ranges:
                switch, ranges = mux_ranges[key]
                sig["mux_by"], sig["mux_values"] = switch, [list(r) for r in ranges]
            elif "_mux" in sig:
                if len(roots) != 1:
                    result.warnings.append(f"{msg['name']}.{sig['name']}: multiplexed, but the multiplexor is unclear")
                    continue
                sig["mux_by"], sig["mux_values"] = roots[0], [[sig["_mux"], sig["_mux"]]]
            sig.pop("_mux", None)
            if valtype.get(key) in (1, 2):
                sig["kind"] = "float"
            if key in values:
                sig["values"] = {str(k): v for k, v in values[key].items()}
            if key in signal_comments:
                sig["comment"] = signal_comments[key]
            if key in start_values:
                sig["start_value"] = start_values[key]
            if definition.get("pgn") is not None:
                sig["invalid"] = "j1939"
            try:
                Signal.from_dict(sig)
            except DefinitionError as err:
                result.warnings.append(f"{msg['name']}.{sig['name']}: {err}")
                continue
            signals.append(sig)
        definition["signals"] = signals
        try:
            Message.from_dict(definition)
        except DefinitionError as err:
            result.warnings.append(f"{msg['name']}: {err}")
            continue
        result.messages.append(definition)
    return result


def _dbc_number(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else repr(float(value))


def dump(messages: list[Message], nodes: list[str] | None = None, comment: str = "") -> str:
    """Messages as a DBC file (what WOOW CAN knows of them)."""
    lines = ['VERSION ""', "", "", "NS_ :", "    CM_", "    BA_DEF_", "    BA_", "    VAL_", "    BA_DEF_DEF_",
             "    SIG_VALTYPE_", "", "BS_:", "", "BU_: " + " ".join(nodes or []), "", ""]
    comments, attrs, vals, valtypes, muls = [], [], [], [], []
    for msg in messages:
        dbc_id = msg.raw_id if msg.pgn is None else (0x18000000 | (msg.pgn << 8) | (msg.source or 0xFE)) | 0x80000000
        sender = msg.senders[0] if msg.senders else "Vector__XXX"
        lines.append(f"BO_ {dbc_id} {msg.name}: {msg.length} {sender}")
        roots = {s.name for s in msg.signals if s.multiplexor and not s.mux_by}
        for sig in msg.signals:
            if sig.derive or sig.decoder_field:
                continue
            mux = ""
            if sig.mux_by:
                mux = f" m{sig.mux_values[0][0]}" + ("M" if sig.multiplexor else "")
                if sig.mux_by not in roots or len(sig.mux_values) != 1 or sig.mux_values[0][0] != sig.mux_values[0][1]:
                    ranges = ", ".join(f"{a}-{b}" for a, b in sig.mux_values)
                    muls.append(f"SG_MUL_VAL_ {dbc_id} {sig.name} {sig.mux_by} {ranges};")
            elif sig.multiplexor:
                mux = " M"
            order = "1" if sig.byte_order == "little" else "0"
            sign = "-" if sig.signed else "+"
            low = sig.minimum if sig.minimum is not None else 0
            high = sig.maximum if sig.maximum is not None else 0
            unit = sig.unit.replace('"', '\\"')
            lines.append(f" SG_ {sig.name}{mux} : {sig.start}|{sig.length}@{order}{sign} "
                         f"({_dbc_number(sig.factor)},{_dbc_number(sig.offset)}) "
                         f"[{_dbc_number(low)}|{_dbc_number(high)}] \"{unit}\" Vector__XXX")
            if sig.values:
                pairs = " ".join(f'{k} "{v}"' for k, v in sorted(sig.values.items(), reverse=True))
                vals.append(f"VAL_ {dbc_id} {sig.name} {pairs} ;")
            if sig.kind == "float":
                valtypes.append(f"SIG_VALTYPE_ {dbc_id} {sig.name} : {1 if sig.length == 32 else 2};")
            if sig.comment:
                comments.append(f'CM_ SG_ {dbc_id} {sig.name} "{sig.comment}";')
        if msg.comment:
            comments.append(f'CM_ BO_ {dbc_id} "{msg.comment}";')
        if msg.cycle_ms:
            attrs.append(f'BA_ "GenMsgCycleTime" BO_ {dbc_id} {msg.cycle_ms};')
        if msg.pgn is not None:
            attrs.append(f'BA_ "VFrameFormat" BO_ {dbc_id} 3;')
        elif msg.extended:
            attrs.append(f'BA_ "VFrameFormat" BO_ {dbc_id} 1;')
        for sig in msg.signals:
            if sig.start_value is not None and not sig.derive and not sig.decoder_field:
                attrs.append(f'BA_ "GenSigStartValue" SG_ {dbc_id} {sig.name} {sig.start_value};')
        lines.append("")
    if comment:
        comments.insert(0, f'CM_ "{comment}";')
    header = ['BA_DEF_ BO_ "GenMsgCycleTime" INT 0 65535;',
              'BA_DEF_ BO_ "VFrameFormat" ENUM "StandardCAN","ExtendedCAN","reserved","J1939PG";',
              'BA_DEF_ SG_ "GenSigStartValue" INT 0 2147483647;',
              'BA_DEF_DEF_ "GenMsgCycleTime" 0;', 'BA_DEF_DEF_ "VFrameFormat" "StandardCAN";',
              'BA_DEF_DEF_ "GenSigStartValue" 0;']
    return "\n".join(lines + comments + [""] + header + attrs + [""] + vals + valtypes + muls) + "\n"
