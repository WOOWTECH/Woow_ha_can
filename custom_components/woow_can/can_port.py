"""SocketCAN port: interface setup over rtnetlink and raw frame I/O (stdlib only).

HAOS has no iproute2 with CAN support (busybox `ip` only), so bitrate / FD / listen-only
are set with a small rtnetlink client; verified on can0 (MCP2515) and can1 (MCP2518FD)
from inside the Core container on 2026-10-16. Virtual interfaces (vcan) are created the
same way and need no bit timing.

Every frame arrives with the kernel's receive time (SO_TIMESTAMP). Frames this socket sent
come back once they are on the bus (CAN_RAW_RECV_OWN_MSGS, flagged MSG_CONFIRM), so the
monitor shows what really went out; frames other programs on this host sent are flagged
MSG_DONTROUTE.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
import os
import socket
import struct
import time

# rtnetlink
RTM_NEWLINK, RTM_DELLINK, RTM_GETLINK = 16, 17, 18
NLM_F_REQUEST, NLM_F_MULTI, NLM_F_ACK, NLM_F_EXCL, NLM_F_CREATE = 0x1, 0x2, 0x4, 0x200, 0x400
NLMSG_ERROR, NLMSG_DONE = 2, 3
IFF_UP = 0x1
IFLA_IFNAME, IFLA_LINKINFO = 3, 18
IFLA_INFO_KIND, IFLA_INFO_DATA, IFLA_INFO_XSTATS = 1, 2, 3
IFLA_CAN_BITTIMING, IFLA_CAN_CLOCK, IFLA_CAN_STATE, IFLA_CAN_CTRLMODE = 1, 3, 4, 5
IFLA_CAN_RESTART_MS, IFLA_CAN_BERR_COUNTER, IFLA_CAN_DATA_BITTIMING = 6, 8, 9
IFLA_CAN_CTRLMODE_EXT, IFLA_CAN_CTRLMODE_SUPPORTED = 17, 1
CTRLMODE_LOOPBACK, CTRLMODE_LISTENONLY, CTRLMODE_BERR_REPORTING, CTRLMODE_FD = 0x01, 0x02, 0x10, 0x20
CAN_STATES = ["error_active", "error_warning", "error_passive", "bus_off", "stopped", "sleeping"]
DEVICE_STATS = ("bus_error", "error_warning", "error_passive", "bus_off", "arbitration_lost", "restarts")
VIRTUAL_KINDS = {"vcan", "vxcan"}

# SocketCAN
CAN_EFF_FLAG, CAN_RTR_FLAG, CAN_ERR_FLAG = 0x80000000, 0x40000000, 0x20000000
CAN_SFF_MASK, CAN_EFF_MASK = 0x7FF, 0x1FFFFFFF
CAN_ERR_MASK = 0x1FFFFFFF
CANFD_BRS = 0x01
SOL_CAN_RAW = getattr(socket, "SOL_CAN_RAW", 101)
CAN_RAW_FILTER = getattr(socket, "CAN_RAW_FILTER", 1)
CAN_RAW_ERR_FILTER = getattr(socket, "CAN_RAW_ERR_FILTER", 2)
CAN_RAW_RECV_OWN_MSGS = getattr(socket, "CAN_RAW_RECV_OWN_MSGS", 4)
CAN_RAW_FD_FRAMES = getattr(socket, "CAN_RAW_FD_FRAMES", 5)
# Not exported by Python's socket module; values of the Linux generic ABI (aarch64, x86_64).
SO_TIMESTAMP, SO_RXQ_OVFL = 29, 40
MSG_CONFIRM = getattr(socket, "MSG_CONFIRM", 0x800)
MSG_DONTROUTE = getattr(socket, "MSG_DONTROUTE", 0x4)
CLASSIC_SIZE, FD_SIZE = 16, 72
FD_LENGTHS = (0, 1, 2, 3, 4, 5, 6, 7, 8, 12, 16, 20, 24, 32, 48, 64)
FD_DRIVERS = {"mcp251xfd", "m_can_platform", "tcan4x5x", "ctucanfd", "flexcan", "peak_usb", "gs_usb", "vcan"}

# Flags of a received frame (also stored in the trace buffer)
F_FD, F_BRS, F_OWN, F_LOCAL, F_ERR = 0x01, 0x02, 0x04, 0x08, 0x10


def parse_id(text: str) -> tuple[int, bool]:
    """Hex CAN ID -> (id, extended). 1-3 hex digits = 11-bit, longer = 29-bit."""
    digits = text.strip()
    if digits[:2].lower() == "0x":
        digits = digits[2:]
    if not digits or len(digits) > 8:
        raise ValueError(f"bad CAN ID {text!r}")
    try:
        can_id = int(digits, 16)
    except ValueError:
        raise ValueError(f"bad CAN ID {text!r}") from None
    extended = len(digits) > 3 or can_id > CAN_SFF_MASK
    if can_id > CAN_EFF_MASK:
        raise ValueError(f"CAN ID {text!r} is out of range")
    return can_id, extended


@dataclass(frozen=True)
class CanFrame:
    """One CAN / CAN FD frame."""

    can_id: int
    data: bytes = b""
    extended: bool = False
    fd: bool = False
    brs: bool = False
    rtr: bool = False

    @classmethod
    def build(cls, can_id: int, data: bytes, extended: bool, fd: bool = False,
              brs: bool = False, rtr: bool = False) -> CanFrame:
        if can_id > (CAN_EFF_MASK if extended else CAN_SFF_MASK):
            raise ValueError(f"CAN ID {can_id:X} does not fit a {'29' if extended else '11'}-bit ID")
        if fd:
            if rtr:
                raise ValueError("CAN FD has no remote frames")
            if len(data) > 64:
                raise ValueError("CAN FD carries at most 64 bytes")
            size = next(n for n in FD_LENGTHS if n >= len(data))
            data = data.ljust(size, b"\0")
        elif len(data) > 8:
            raise ValueError("classic CAN carries at most 8 bytes (turn on CAN FD for more)")
        return cls(can_id, b"" if rtr else bytes(data), extended, fd, fd and brs, rtr)

    @classmethod
    def parse(cls, text: str) -> CanFrame:
        """cansend notation: 123#11223344, 18FF50E5#01, 123#R, 456##1<data> (FD + flags)."""
        id_part, sep, rest = text.strip().partition("#")
        if not sep:
            raise ValueError("use ID#DATA, e.g. 123#11223344")
        can_id, extended = parse_id(id_part)
        if rest[:1] in ("R", "r"):
            return cls.build(can_id, b"", extended, rtr=True)
        fd = brs = False
        if rest.startswith("#"):
            if len(rest) < 2:
                raise ValueError("CAN FD needs a flags digit after ##, e.g. 456##1AABB")
            fd, brs, rest = True, bool(int(rest[1], 16) & CANFD_BRS), rest[2:]
        try:
            data = bytes.fromhex(rest.replace(".", "").replace(" ", ""))
        except ValueError:
            raise ValueError(f"bad data {rest!r}: use hex bytes") from None
        return cls.build(can_id, data, extended, fd, brs)

    @classmethod
    def from_raw(cls, raw: int, data: bytes, flags: int) -> CanFrame:
        extended = bool(raw & CAN_EFF_FLAG)
        fd = bool(flags & F_FD)
        rtr = bool(raw & CAN_RTR_FLAG) and not fd
        return cls(raw & (CAN_EFF_MASK if extended else CAN_SFF_MASK), b"" if rtr else bytes(data), extended, fd,
                   fd and bool(flags & F_BRS), rtr)

    @property
    def raw_id(self) -> int:
        """The ID as the kernel writes it, with the 29-bit and remote flags."""
        return self.can_id | (CAN_EFF_FLAG if self.extended else 0) | (CAN_RTR_FLAG if self.rtr else 0)

    def pack(self) -> bytes:
        if self.fd:
            return struct.pack("=IBB2x64s", self.raw_id, len(self.data), CANFD_BRS if self.brs else 0, self.data)
        return struct.pack("=IB3x8s", self.raw_id, len(self.data), self.data)

    @classmethod
    def unpack(cls, buf: bytes) -> CanFrame:
        raw, length, fdflags = struct.unpack_from("=IBB", buf)
        flags = (F_FD | (F_BRS if fdflags & CANFD_BRS else 0)) if len(buf) == FD_SIZE else 0
        return cls.from_raw(raw, bytes(buf[8:8 + length]), flags)

    @property
    def id_hex(self) -> str:
        return f"{self.can_id:08X}" if self.extended else f"{self.can_id:03X}"

    def __str__(self) -> str:
        if self.rtr:
            return f"{self.id_hex}#R"
        if self.fd:
            return f"{self.id_hex}##{int(self.brs):X}{self.data.hex().upper()}"
        return f"{self.id_hex}#{self.data.hex().upper()}"

    def as_dict(self) -> dict:
        return {"frame": str(self), "id": self.can_id, "id_hex": self.id_hex,
                "data": self.data.hex(" ").upper(), "length": len(self.data),
                "extended": self.extended, "fd": self.fd, "brs": self.brs, "rtr": self.rtr}


def id_hex(raw: int) -> str:
    return f"{raw & CAN_EFF_MASK:08X}" if raw & CAN_EFF_FLAG else f"{raw & CAN_SFF_MASK:03X}"


def frame_text(raw: int, data: bytes, flags: int) -> str:
    """candump notation of a raw frame (error frames keep their error-class ID, as candump writes them)."""
    if flags & F_ERR:
        return f"{(raw & CAN_ERR_MASK) | CAN_ERR_FLAG:08X}#{data.hex().upper()}"
    if raw & CAN_RTR_FLAG and not flags & F_FD:
        return f"{id_hex(raw)}#R"
    if flags & F_FD:
        return f"{id_hex(raw)}##{1 if flags & F_BRS else 0}{data.hex().upper()}"
    return f"{id_hex(raw)}#{data.hex().upper()}"


def parse_filters(text: str) -> list[tuple[int, int]]:
    """'123, 7E0/7F0, 18FF50E5' -> kernel (can_id, can_mask) pairs; empty = everything."""
    out = []
    for item in text.replace(";", ",").split(","):
        item = item.strip()
        if not item:
            continue
        id_text, _, mask_text = item.partition("/")
        can_id, extended = parse_id(id_text)
        if mask_text:
            mask = parse_id(mask_text)[0]
        else:
            mask = CAN_EFF_MASK if extended else CAN_SFF_MASK
        if extended:
            out.append((can_id | CAN_EFF_FLAG, mask | CAN_EFF_FLAG))
        else:
            out.append((can_id, mask | CAN_EFF_FLAG))
    return out


class IdMatcher:
    """Which frames an ID list picks: '*' (all), '123', '18FF50E5', '7E0/7F0' (ID/mask), '100-1FF' (range).

    Empty text picks nothing. 1-3 hex digits are 11-bit IDs, longer ones 29-bit.
    """

    def __init__(self, text: str) -> None:
        self.text = text.strip()
        self.all = False
        self._exact: set[int] = set()  # raw ids (with the 29-bit flag)
        self._masks: list[tuple[int, int, bool]] = []
        self._ranges: list[tuple[int, int, bool]] = []
        for item in self.text.replace(";", ",").split(","):
            item = item.strip()
            if not item:
                continue
            if item == "*":
                self.all = True
                continue
            if "-" in item:
                low_text, _, high_text = item.partition("-")
                low, ext = parse_id(low_text)
                high, ext_high = parse_id(high_text)
                if high < low:
                    raise ValueError(f"empty range {item!r}")
                self._ranges.append((low, high, ext or ext_high))
            elif "/" in item:
                id_text, _, mask_text = item.partition("/")
                can_id, ext = parse_id(id_text)
                self._masks.append((can_id, parse_id(mask_text)[0], ext))
            else:
                can_id, ext = parse_id(item)
                self._exact.add(can_id | (CAN_EFF_FLAG if ext else 0))

    @property
    def empty(self) -> bool:
        return not (self.all or self._exact or self._masks or self._ranges)

    def __call__(self, raw: int) -> bool:
        if self.all:
            return True
        ext = bool(raw & CAN_EFF_FLAG)
        key = raw & (CAN_EFF_FLAG | CAN_EFF_MASK)
        if key in self._exact:
            return True
        can_id = raw & CAN_EFF_MASK
        for want, mask, want_ext in self._masks:
            if want_ext == ext and can_id & mask == want & mask:
                return True
        for low, high, want_ext in self._ranges:
            if want_ext == ext and low <= can_id <= high:
                return True
        return False


# ---- error frames -----------------------------------------------------------------------
_CRTL = {0x01: "rx_overflow", 0x02: "tx_overflow", 0x04: "rx_warning", 0x08: "tx_warning",
         0x10: "rx_passive", 0x20: "tx_passive", 0x40: "active"}
_PROT = {0x01: "bit", 0x02: "form", 0x04: "stuff", 0x08: "bit0", 0x10: "bit1", 0x20: "overload",
         0x40: "active_error", 0x80: "on_tx"}


def decode_error(raw: int, data: bytes) -> list[str]:
    """An error frame as short codes the panel translates, e.g. ['controller:tx_passive', 'no_ack']."""
    cls = raw & CAN_ERR_MASK
    data = data.ljust(8, b"\0")
    out: list[str] = []
    if cls & 0x001:
        out.append("tx_timeout")
    if cls & 0x002:
        out.append("lost_arbitration")
    if cls & 0x004:
        out += [f"controller:{name}" for bit, name in _CRTL.items() if data[1] & bit] or ["controller"]
    if cls & 0x008:
        out += [f"protocol:{name}" for bit, name in _PROT.items() if data[2] & bit] or ["protocol"]
    if cls & 0x010:
        out.append("transceiver")
    if cls & 0x020:
        out.append("no_ack")
    if cls & 0x040:
        out.append("bus_off")
    if cls & 0x080:
        out.append("bus_error")
    if cls & 0x100:
        out.append("restarted")
    return out


# ---- rtnetlink ------------------------------------------------------------------------
def _rta(kind: int, payload: bytes) -> bytes:
    n = 4 + len(payload)
    return struct.pack("=HH", n, kind) + payload + b"\0" * (-n % 4)


def _parse(buf: bytes) -> dict[int, bytes]:
    out, i = {}, 0
    while i + 4 <= len(buf):
        n, kind = struct.unpack_from("=HH", buf, i)
        if n < 4:
            break
        out[kind & 0x3FFF] = buf[i + 4:i + n]
        i += (n + 3) & ~3
    return out


def _netlink(msg_type: int, flags: int, ifindex: int, ifi_flags: int = 0,
             ifi_change: int = 0, attrs: bytes = b"") -> list[bytes]:
    body = struct.pack("=BxHiII", 0, 0, ifindex, ifi_flags, ifi_change) + attrs
    with socket.socket(socket.AF_NETLINK, socket.SOCK_RAW, 0) as sock:
        sock.bind((0, 0))
        sock.settimeout(5)
        sock.send(struct.pack("=IHHII", 16 + len(body), msg_type, flags, 1, 0) + body)
        msgs: list[bytes] = []
        while True:
            data, off, done = sock.recv(65536), 0, False
            while off + 16 <= len(data):
                length, kind, msg_flags, _, _ = struct.unpack_from("=IHHII", data, off)
                payload = data[off + 16:off + length]
                if kind == NLMSG_ERROR:
                    err = struct.unpack_from("=i", payload)[0]
                    if err:
                        raise OSError(-err, os.strerror(-err))
                    done = True
                elif kind == NLMSG_DONE:
                    done = True
                else:
                    msgs.append(payload)
                    done = done or not msg_flags & NLM_F_MULTI
                off += (length + 3) & ~3
            if done:
                return msgs


def link_up(ifname: str, up: bool) -> None:
    _netlink(RTM_NEWLINK, NLM_F_REQUEST | NLM_F_ACK, socket.if_nametoindex(ifname),
             IFF_UP if up else 0, IFF_UP)


def link_configure(ifname: str, bitrate: int, ctrl_mask: int, ctrl_flags: int,
                   restart_ms: int, dbitrate: int = 0) -> None:
    """Set bit timing / control mode (the interface must be down)."""
    data = _rta(IFLA_CAN_CTRLMODE, struct.pack("=II", ctrl_mask, ctrl_flags))
    if bitrate:
        data += _rta(IFLA_CAN_BITTIMING, struct.pack("=8I", bitrate, 0, 0, 0, 0, 0, 0, 0))
    if dbitrate:
        data += _rta(IFLA_CAN_DATA_BITTIMING, struct.pack("=8I", dbitrate, 0, 0, 0, 0, 0, 0, 0))
    data += _rta(IFLA_CAN_RESTART_MS, struct.pack("=I", restart_ms))
    _netlink(RTM_NEWLINK, NLM_F_REQUEST | NLM_F_ACK, socket.if_nametoindex(ifname),
             attrs=_rta(IFLA_LINKINFO, _rta(IFLA_INFO_KIND, b"can\0") + _rta(IFLA_INFO_DATA, data)))


def vcan_add(ifname: str) -> None:
    """Create a virtual CAN interface and bring it up (the kernel loads the vcan module itself)."""
    attrs = _rta(IFLA_IFNAME, ifname.encode() + b"\0") + _rta(IFLA_LINKINFO, _rta(IFLA_INFO_KIND, b"vcan\0"))
    _netlink(RTM_NEWLINK, NLM_F_REQUEST | NLM_F_ACK | NLM_F_CREATE | NLM_F_EXCL, 0, attrs=attrs)
    link_up(ifname, True)


def vcan_del(ifname: str) -> None:
    _netlink(RTM_DELLINK, NLM_F_REQUEST | NLM_F_ACK, socket.if_nametoindex(ifname))


def link_exists(ifname: str) -> bool:
    return os.path.exists(f"/sys/class/net/{ifname}")


def _getlink(ifname: str) -> tuple[int, dict[int, bytes]]:
    payload = _netlink(RTM_GETLINK, NLM_F_REQUEST, socket.if_nametoindex(ifname))[0]
    return struct.unpack_from("=BxHiII", payload)[3], _parse(payload[16:])


def link_kind(ifname: str) -> str:
    """'can', 'vcan', ... from the interface's link info."""
    _, attrs = _getlink(ifname)
    return _parse(attrs.get(IFLA_LINKINFO, b"")).get(IFLA_INFO_KIND, b"").rstrip(b"\0").decode() or "?"


def _sysfs_stats(ifname: str, keys: tuple[str, ...]) -> dict[str, int]:
    out = {}
    for key in keys:
        with open(f"/sys/class/net/{ifname}/statistics/{key}", encoding="ascii") as fh:
            out[key] = int(fh.read())
    return out


COUNTERS = ("rx_packets", "tx_packets", "rx_bytes", "tx_bytes", "rx_errors", "tx_errors",
            "rx_dropped", "tx_dropped", "rx_over_errors")


def link_status(ifname: str) -> dict:
    """Bus state, bit timing, error counters, controller statistics and interface counters."""
    ifi_flags, attrs = _getlink(ifname)
    info = _parse(attrs.get(IFLA_LINKINFO, b""))
    kind = info.get(IFLA_INFO_KIND, b"").rstrip(b"\0").decode() or "?"
    data = _parse(info.get(IFLA_INFO_DATA, b""))
    out: dict = {"up": bool(ifi_flags & IFF_UP), "kind": kind, "virtual": kind in VIRTUAL_KINDS}
    if out["virtual"]:
        out["state"] = "virtual"
    if IFLA_CAN_STATE in data:
        state = struct.unpack_from("=I", data[IFLA_CAN_STATE])[0]
        out["state"] = CAN_STATES[state] if state < len(CAN_STATES) else None
    if IFLA_CAN_BITTIMING in data:
        timing = struct.unpack_from("=8I", data[IFLA_CAN_BITTIMING])
        out["bitrate"], out["sample_point"] = timing[0], timing[1] / 1000
    if IFLA_CAN_DATA_BITTIMING in data:
        out["dbitrate"] = struct.unpack_from("=8I", data[IFLA_CAN_DATA_BITTIMING])[0]
    if IFLA_CAN_CTRLMODE in data:
        mode = struct.unpack_from("=II", data[IFLA_CAN_CTRLMODE])[1]
        out["fd"] = bool(mode & CTRLMODE_FD)
        out["listen_only"] = bool(mode & CTRLMODE_LISTENONLY)
        out["loopback"] = bool(mode & CTRLMODE_LOOPBACK)
        out["berr_reporting"] = bool(mode & CTRLMODE_BERR_REPORTING)
    if IFLA_CAN_CTRLMODE_EXT in data:
        ext = _parse(data[IFLA_CAN_CTRLMODE_EXT])
        if IFLA_CAN_CTRLMODE_SUPPORTED in ext:
            supported = struct.unpack_from("=I", ext[IFLA_CAN_CTRLMODE_SUPPORTED])[0]
            out["berr_supported"] = bool(supported & CTRLMODE_BERR_REPORTING)
            out["fd_supported"] = bool(supported & CTRLMODE_FD)
    if IFLA_CAN_BERR_COUNTER in data:
        out["tx_error_counter"], out["rx_error_counter"] = struct.unpack_from("=HH", data[IFLA_CAN_BERR_COUNTER])
    if IFLA_CAN_RESTART_MS in data:
        out["restart_ms"] = struct.unpack_from("=I", data[IFLA_CAN_RESTART_MS])[0]
    if IFLA_CAN_CLOCK in data:
        out["clock"] = struct.unpack_from("=I", data[IFLA_CAN_CLOCK])[0]
    xstats = info.get(IFLA_INFO_XSTATS, b"")
    if len(xstats) >= 24:
        out.update(zip(DEVICE_STATS, struct.unpack_from("=6I", xstats)))
    out.update(_sysfs_stats(ifname, COUNTERS))
    return out


# ---- frame I/O --------------------------------------------------------------------------
@dataclass
class CanConfig:
    """Interface settings plus receive limits."""

    ifname: str
    bitrate: int = 500000
    fd: bool = False
    dbitrate: int = 2000000
    listen_only: bool = False
    restart_ms: int = 100
    filters: list[tuple[int, int]] = field(default_factory=list)
    loopback: bool = False  # controller-internal loop, for self tests only (not in the UI)


FrameCallback = Callable[[float, int, bytes, int], None]  # time, raw id, data, F_* flags


class CanPort:
    """Brings the interface up with the configured timing and exchanges frames."""

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        cfg: CanConfig,
        on_frame: FrameCallback,
        on_error: FrameCallback,
        on_lost: Callable[[Exception], None],
    ) -> None:
        self._loop = loop
        self.cfg = cfg
        self._on_frame = on_frame
        self._on_error = on_error
        self._on_lost = on_lost
        self._sock: socket.socket | None = None
        self._waiters: list[tuple[Callable[[CanFrame], bool], asyncio.Future[CanFrame]]] = []
        self.kind = "can"
        self.socket_drops = 0  # frames the kernel dropped because this socket's queue was full

    @property
    def is_open(self) -> bool:
        return self._sock is not None

    @property
    def virtual(self) -> bool:
        return self.kind in VIRTUAL_KINDS

    def _open_blocking(self) -> socket.socket:
        cfg = self.cfg
        self.kind = link_kind(cfg.ifname)
        if self.virtual:  # no bit timing: just make sure it is up
            link_up(cfg.ifname, True)
        else:
            link_up(cfg.ifname, False)
            mask = CTRLMODE_LOOPBACK | CTRLMODE_LISTENONLY | CTRLMODE_FD
            flags = ((CTRLMODE_LISTENONLY if cfg.listen_only else 0) | (CTRLMODE_FD if cfg.fd else 0)
                     | (CTRLMODE_LOOPBACK if cfg.loopback else 0))
            link_configure(cfg.ifname, cfg.bitrate, mask, flags, cfg.restart_ms, cfg.dbitrate if cfg.fd else 0)
            link_up(cfg.ifname, True)
        sock = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
        try:
            if cfg.fd or self.virtual:
                sock.setsockopt(SOL_CAN_RAW, CAN_RAW_FD_FRAMES, 1)
            if cfg.filters:
                sock.setsockopt(SOL_CAN_RAW, CAN_RAW_FILTER,
                                b"".join(struct.pack("=II", i, m) for i, m in cfg.filters))
            sock.setsockopt(SOL_CAN_RAW, CAN_RAW_ERR_FILTER, struct.pack("=I", CAN_ERR_MASK))
            sock.setsockopt(SOL_CAN_RAW, CAN_RAW_RECV_OWN_MSGS, 1)
            sock.setsockopt(socket.SOL_SOCKET, SO_TIMESTAMP, 1)
            sock.setsockopt(socket.SOL_SOCKET, SO_RXQ_OVFL, 1)
            sock.bind((cfg.ifname,))
            sock.setblocking(False)
        except Exception:
            sock.close()
            raise
        return sock

    async def open(self) -> None:
        self._sock = await self._loop.run_in_executor(None, self._open_blocking)
        self._loop.add_reader(self._sock.fileno(), self._readable)

    async def close(self) -> None:
        sock, self._sock = self._sock, None
        self._fail_waiters(OSError("CAN interface closed"))
        if sock is not None:
            self._loop.remove_reader(sock.fileno())
            sock.close()
        if self.virtual:  # other programs may use a vcan too; leave it up
            return
        try:
            await self._loop.run_in_executor(None, link_up, self.cfg.ifname, False)
        except OSError:
            pass

    def _lost(self, err: Exception) -> None:
        if self._sock is not None:
            self._loop.remove_reader(self._sock.fileno())
            self._sock.close()
            self._sock = None
        self._fail_waiters(err)
        self._on_lost(err)

    def _fail_waiters(self, err: Exception) -> None:
        for _, fut in self._waiters:
            if not fut.done():
                fut.set_exception(err)

    _ANC = socket.CMSG_SPACE(16) + socket.CMSG_SPACE(4) if hasattr(socket, "CMSG_SPACE") else 64

    def _readable(self) -> None:
        for _ in range(256):  # drain a burst, then give the loop back
            if self._sock is None:
                return
            try:
                buf, anc, msg_flags, _addr = self._sock.recvmsg(FD_SIZE, self._ANC)
            except BlockingIOError:
                return
            except OSError as err:
                self._lost(err)
                return
            if len(buf) < CLASSIC_SIZE:
                continue
            ts = 0.0
            for level, ctype, cdata in anc:
                if level == socket.SOL_SOCKET:
                    if ctype == SO_TIMESTAMP and len(cdata) >= 16:
                        sec, usec = struct.unpack_from("=qq", cdata)
                        ts = sec + usec / 1e6
                    elif ctype == SO_RXQ_OVFL and len(cdata) >= 4:
                        self.socket_drops = struct.unpack_from("=I", cdata)[0]
            raw, length, fdflags = struct.unpack_from("=IBB", buf)
            data = bytes(buf[8:8 + length])
            flags = ((F_FD | (F_BRS if fdflags & CANFD_BRS else 0)) if len(buf) == FD_SIZE else 0) \
                | (F_OWN if msg_flags & MSG_CONFIRM else 0) | (F_LOCAL if msg_flags & MSG_DONTROUTE else 0)
            ts = ts or time.time()
            if raw & CAN_ERR_FLAG:
                self._on_error(ts, raw, data, flags | F_ERR)
                continue
            if self._waiters and not flags & F_OWN:
                frame = CanFrame.from_raw(raw, data, flags)
                for match, fut in self._waiters:
                    if not fut.done() and match(frame):
                        fut.set_result(frame)
            self._on_frame(ts, raw, data, flags)

    async def send(self, frame: CanFrame) -> None:
        if self._sock is None:
            raise OSError("CAN interface is not open")
        if frame.fd and not (self.cfg.fd or self.virtual):
            raise ValueError("CAN FD is off for this interface")
        await self._loop.sock_sendall(self._sock, frame.pack())

    async def request(self, frame: CanFrame, match: Callable[[CanFrame], bool],
                      timeout: float) -> CanFrame | None:
        """Send, then return the first received frame that `match` accepts."""
        item: tuple[Callable[[CanFrame], bool], asyncio.Future[CanFrame]] = (match, self._loop.create_future())
        self._waiters.append(item)
        try:
            await self.send(frame)
            return await asyncio.wait_for(item[1], timeout)
        except TimeoutError:
            return None
        finally:
            self._waiters.remove(item)

    def status(self) -> dict:
        """Blocking: netlink + sysfs snapshot (run in an executor)."""
        return link_status(self.cfg.ifname)
