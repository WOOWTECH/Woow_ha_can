"""Devices: groups of messages on an interface whose chosen signals become Home Assistant entities.

A device is self-contained JSON (from a template, from an imported DBC file, or written by hand or by
an agent): an interface, messages with signals, and for each adopted signal its entity settings. The
manager routes received frames to devices (exact IDs, J1939 / NMEA 2000 parameter groups, masks),
reassembles multi-frame transfers (J1939 BAM, NMEA 2000 fast-packet), decodes only when a message's
data changed, and hands values to the entities, which decide when to write (see managed.py).
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
import logging
import time
from typing import Any
import uuid

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, Context, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.storage import Store

from .can_port import CanFrame
from .const import DOMAIN
from .polling import RequestScheduler
from .signals import (
    EFF_FLAG,
    J1939_TP_CM,
    J1939_TP_DT,
    DefinitionError,
    FastPacket,
    J1939Transport,
    Message,
    Signal,
    frame_data,
    j1939_pgn,
    number,
    parse_can_id,
)

_LOGGER = logging.getLogger(__name__)
SAVE_DELAY = 5
TIMEOUT_CHECK = 1.0  # s between checks for silent messages
VALUES_PUSH = 0.25  # s between value pushes to the panel
MIN_PERIOD_MS = 100  # shortest request period
MAX_DEVICE_RATE = 50.0  # requests a second a device may be allowed
WRITE_GAP = 0.05  # s between two writes of the same command frame


def new_id() -> str:
    return uuid.uuid4().hex[:12]


@dataclass
class Request:
    """A frame sent every period_ms while the device is active; `reply` names the message that answers it."""

    name: str
    can_id: int
    extended: bool
    data: bytes
    period_ms: int
    reply: str | None = None
    timeout_ms: int = 300

    @property
    def raw_id(self) -> int:
        return self.can_id | EFF_FLAG if self.extended else self.can_id

    @classmethod
    def from_dict(cls, raw: dict[str, Any], params: dict[str, Any]) -> Request:
        try:
            can_id, extended = parse_can_id(raw["can_id"], params, raw.get("extended"))
            data = frame_data(raw.get("data", ""), params)
            period = number(raw.get("period_ms", 1000), params)
            timeout = number(raw.get("timeout_ms", 300), params)
        except (KeyError, TypeError, ValueError) as err:
            if isinstance(err, DefinitionError):
                raise
            raise DefinitionError("bad_request", request=raw.get("name", "?"), error=str(err)) from err
        if len(data) > 8:
            raise DefinitionError("bad_request", request=raw.get("name", "?"), error="at most 8 bytes")
        if not MIN_PERIOD_MS <= period <= 3_600_000 or not 10 <= timeout <= 10_000:
            raise DefinitionError("bad_request", request=raw.get("name", "?"),
                                  error=f"period_ms {MIN_PERIOD_MS}-3600000, timeout_ms 10-10000")
        return cls(name=str(raw.get("name") or f"{can_id:X}"), can_id=can_id, extended=extended, data=data,
                   period_ms=period, reply=raw.get("reply") or None, timeout_ms=timeout)

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"name": self.name,
                               "can_id": f"{self.can_id:08X}" if self.extended else f"{self.can_id:03X}",
                               "extended": self.extended, "data": self.data.hex(" ").upper(),
                               "period_ms": self.period_ms, "timeout_ms": self.timeout_ms}
        if self.reply:
            out["reply"] = self.reply
        return out


@dataclass
class Device:
    id: str
    name: str
    interface: str  # config entry id of the CAN interface
    messages: list[Message]
    template: str | None = None
    params: dict[str, Any] = field(default_factory=dict)
    groups: list[str] = field(default_factory=list)
    manufacturer: str = ""
    model: str = ""
    source: str = ""  # "template", "dbc:<file>", "custom"
    created: float = 0.0
    requests: list[Request] = field(default_factory=list)
    active: bool = False  # sends its requests (off until someone turns it on)
    allow_write: bool = False  # has writable entities and accepts writes (off until someone turns it on)
    max_rate: float = 10.0  # requests a second at most

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Device:
        if not raw.get("name"):
            raise DefinitionError("no_name")
        if not raw.get("interface"):
            raise DefinitionError("no_interface")
        params = raw.get("params") or {}
        messages = [Message.from_dict(m, params) for m in raw.get("messages") or []]
        if not messages:
            raise DefinitionError("no_messages")
        names = [m.name for m in messages]
        if len(set(names)) != len(names):
            raise DefinitionError("duplicate_message")
        requests = [Request.from_dict(r, params) for r in raw.get("requests") or []]
        by_name = {m.name: m for m in messages}
        if len({r.name for r in requests}) != len(requests):
            raise DefinitionError("duplicate_request")
        for req in requests:
            if req.reply and (req.reply not in by_name or by_name[req.reply].send):
                raise DefinitionError("unknown_reply", request=req.name, message=req.reply)
        for msg in messages:
            for sig in msg.signals:
                write_check(msg, sig, by_name)
        try:
            max_rate = float(raw.get("max_rate", 10.0))
        except (TypeError, ValueError) as err:
            raise DefinitionError("bad_max_rate", value=raw.get("max_rate")) from err
        if not 0.1 <= max_rate <= MAX_DEVICE_RATE:
            raise DefinitionError("bad_max_rate", value=max_rate)
        return cls(id=str(raw.get("id") or new_id()), name=str(raw["name"]).strip(), interface=str(raw["interface"]),
                   messages=messages, template=raw.get("template"), params=dict(params),
                   groups=list(raw.get("groups") or []), manufacturer=str(raw.get("manufacturer") or ""),
                   model=str(raw.get("model") or ""), source=str(raw.get("source") or "custom"),
                   created=float(raw.get("created") or 0), requests=requests, active=bool(raw.get("active", False)),
                   allow_write=bool(raw.get("allow_write", False)), max_rate=max_rate)

    def as_dict(self) -> dict[str, Any]:
        out = {"id": self.id, "name": self.name, "interface": self.interface, "template": self.template,
               "params": self.params, "groups": self.groups, "manufacturer": self.manufacturer,
               "model": self.model, "source": self.source, "created": self.created,
               "messages": [m.as_dict() for m in self.messages]}
        if self.requests:
            out["requests"] = [r.as_dict() for r in self.requests]
            out["max_rate"] = self.max_rate
        if self.active:
            out["active"] = True
        if self.allow_write:
            out["allow_write"] = True
        return out

    def message(self, name: str) -> Message | None:
        return next((m for m in self.messages if m.name == name), None)

    @property
    def writable(self) -> bool:
        return any(is_write(s) for m in self.messages for s in m.signals)

    def adopted(self) -> list[tuple[Message, Any]]:
        """Signals with an entity; writable ones only while writing is allowed."""
        return [(m, s) for m in self.messages for s in m.signals if s.entity and (self.allow_write or not is_write(s))]


WRITE_PLATFORMS = ("number", "select", "switch", "button")


def write_view(sig: Signal) -> dict[str, Any]:
    """What the panel needs to offer a control for a writable signal."""
    entity = sig.entity or {}
    out: dict[str, Any] = {"platform": entity["platform"]}
    if entity["platform"] == "number":
        out.update({"min": entity.get("min", sig.minimum), "max": entity.get("max", sig.maximum),
                    "step": entity.get("step", sig.factor)})
    elif entity["platform"] == "select":
        out["options"] = list(sig.values.values())
    elif entity["platform"] == "button":
        out["press"] = entity["press"]
    elif entity["platform"] == "switch":
        out.update({"on": entity.get("on", 1), "off": entity.get("off", 0)})
    return out


def is_write(sig: Signal) -> bool:
    return (sig.entity or {}).get("platform") in WRITE_PLATFORMS


def write_target(msg: Message, sig: Signal, by_name: dict[str, Message]) -> tuple[Message, Signal]:
    """Where a writable signal's value goes: its own message when that is sent, else entity.write {message, signal}
    (a status signal that shows what a command message set)."""
    if msg.send:
        return msg, sig
    spec = (sig.entity or {}).get("write") or {}
    target = by_name.get(spec.get("message", ""))
    tsig = target.by_name.get(spec.get("signal", sig.name)) if target is not None else None
    if target is None or not target.send or tsig is None:
        raise DefinitionError("no_write_target", message=msg.name, signal=sig.name)
    return target, tsig


def write_check(msg: Message, sig: Signal, by_name: dict[str, Message]) -> None:
    if not is_write(sig):
        return
    entity = sig.entity or {}
    target, tsig = write_target(msg, sig, by_name)
    platform = entity["platform"]
    if platform == "number" and None in (entity.get("min", tsig.minimum), entity.get("max", tsig.maximum)):
        raise DefinitionError("number_needs_range", signal=sig.name)
    if platform == "select" and not tsig.values:
        raise DefinitionError("select_needs_values", signal=sig.name)
    if platform == "button" and "press" not in entity:
        raise DefinitionError("button_needs_press", signal=sig.name)


@dataclass
class _Index:
    """Where the frames of one interface go."""

    exact: dict[int, list[tuple[Device, Message]]] = field(default_factory=dict)
    by_pgn: dict[int, list[tuple[Device, Message]]] = field(default_factory=dict)
    masked: list[tuple[Device, Message]] = field(default_factory=list)
    tp: J1939Transport | None = None
    fast: FastPacket | None = None
    fast_pgns: set[int] = field(default_factory=set)


class DeviceManager:
    """The devices, their routing, current values and entity bookkeeping."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry  # the admin entry: device entities belong to it
        self.devices: dict[str, Device] = {}
        self.loaded = False
        self._store: Store[dict[str, Any]] = Store(hass, 1, f"{DOMAIN}.devices")
        self._index: dict[str, _Index] = {}
        self._last_data: dict[tuple[str, str], bytes] = {}
        self.last_seen: dict[tuple[str, str], float] = {}  # (device, message) -> monotonic time
        self.values: dict[str, dict[str, Any]] = {}  # device id -> {"Message.Signal": value}
        self.extra: dict[str, dict[str, Any]] = {}  # device id -> {"Message.field": decoder output}
        self._entities: dict[str, Any] = {}  # unique id -> live entity
        self._adders: dict[str, AddEntitiesCallback] = {}
        self._feed: list[Callable[[str, dict[str, Any]], None]] = []
        self._changed: dict[str, dict[str, Any]] = {}
        self._push_handle: Any = None
        self._timeout_unsub: CALLBACK_TYPE | None = None
        self.on_frames_routed: Callable[[str], None] | None = None
        self.version = 0  # bumps whenever devices change
        # sending, set by the admin layer: why an interface cannot send now (None = it can), and a sender
        self.cannot_send: Callable[[str], str | None] = lambda _entry_id: "not connected"
        self.sender: Callable[[str, CanFrame], Awaitable[Any]] | None = None
        self.on_written: Callable[[Device, str, str, Any, Context | None], None] | None = None
        self.scheduler = RequestScheduler(hass, self)
        self._written: dict[tuple[str, str], bytes] = {}  # (device, sent message) -> its last data
        self._write_locks: dict[tuple[str, str], asyncio.Lock] = {}
        self._write_at: dict[tuple[str, str], float] = {}
        self._status_marks: dict[str, tuple[Any, ...]] = {}

    # ---- persistence / lifecycle --------------------------------------------------------
    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        for raw in data.get("devices", []):
            try:
                device = Device.from_dict(raw)
            except DefinitionError as err:
                _LOGGER.warning("Skipping stored device %s: %s", raw.get("name"), err)
                continue
            self.devices[device.id] = device
        self.loaded = True
        self._reindex()

    def _data(self) -> dict[str, Any]:
        return {"devices": [d.as_dict() for d in self.devices.values()]}

    async def async_flush(self) -> None:
        await self._store.async_save(self._data())

    @callback
    def start(self) -> None:
        from homeassistant.helpers.event import async_track_time_interval  # noqa: PLC0415
        from datetime import timedelta  # noqa: PLC0415

        self._timeout_unsub = async_track_time_interval(self.hass, self._check_timeouts,
                                                        timedelta(seconds=TIMEOUT_CHECK))
        self.scheduler.start()

    @callback
    def stop(self) -> None:
        self.scheduler.stop()
        if self._timeout_unsub is not None:
            self._timeout_unsub()
            self._timeout_unsub = None
        if self._push_handle is not None:
            self._push_handle.cancel()
            self._push_handle = None

    # ---- routing ------------------------------------------------------------------------
    @callback
    def _reindex(self) -> None:
        self.version += 1
        index: dict[str, _Index] = {}
        for device in self.devices.values():
            idx = index.setdefault(device.interface, _Index())
            for msg in device.messages:
                if msg.send:
                    continue  # frames this integration sends are not decoded
                if msg.pgn is not None:
                    idx.by_pgn.setdefault(msg.pgn, []).append((device, msg))
                    if msg.transport == "j1939_tp" and idx.tp is None:
                        idx.tp = J1939Transport()
                    if msg.transport == "n2k_fast":
                        idx.fast = idx.fast or FastPacket()
                        idx.fast_pgns.add(msg.pgn)
                elif msg.exact:
                    idx.exact.setdefault(msg.raw_id, []).append((device, msg))
                else:
                    idx.masked.append((device, msg))
        self._index = index
        self.scheduler.refresh()

    def interfaces_in_use(self) -> set[str]:
        return set(self._index)

    @callback
    def on_frame(self, entry_id: str, ts: float, raw: int, data: bytes, flags: int) -> None:
        """Every received frame of an interface that has devices (called by the hub)."""
        idx = self._index.get(entry_id)
        if idx is None:
            return
        targets = idx.exact.get(raw)
        if targets:
            for device, msg in targets:
                if not msg.filters or msg.matches(raw, data):
                    self._decode(device, msg, data)
        if raw & EFF_FLAG:
            pgn = j1939_pgn(raw)
            if idx.tp is not None and pgn in (J1939_TP_CM, J1939_TP_DT):
                done = idx.tp.feed(ts, raw, data)
                if done is not None:
                    inner_pgn, sa, payload = done
                    for device, msg in idx.by_pgn.get(inner_pgn, ()):
                        if msg.source is None or msg.source == sa:
                            if not msg.filters or msg.matches(EFF_FLAG | (inner_pgn << 8) | sa, payload):
                                self._decode(device, msg, payload)
            entries = idx.by_pgn.get(pgn)
            if entries:
                payload: bytes | None = data
                if pgn in idx.fast_pgns and idx.fast is not None:
                    payload = idx.fast.feed(raw, data)
                if payload is not None:
                    for device, msg in entries:
                        if msg.matches(raw, payload):
                            self._decode(device, msg, payload)
        for device, msg in idx.masked:
            if msg.matches(raw, data):
                self._decode(device, msg, data)

    @callback
    def _decode(self, device: Device, msg: Message, data: bytes) -> None:
        key = (device.id, msg.name)
        now = time.monotonic()
        if device.active:
            self.scheduler.on_message(device.id, msg.name)
        first = key not in self.last_seen
        self.last_seen[key] = now
        if self._last_data.get(key) == data and not first:
            self._touch(device, msg)
            return
        self._last_data[key] = data
        values = msg.decode(data)
        dev_values = self.values.setdefault(device.id, {})
        changed: dict[str, Any] = {}
        for name, value in values.items():
            full = f"{msg.name}.{name}"
            if dev_values.get(full, ...) != value:
                dev_values[full] = value
                changed[full] = value
        if msg.decoder == "j1939_dm1":
            from .signals import decode_dm1  # noqa: PLC0415

            self.extra.setdefault(device.id, {})[f"{msg.name}.dtcs"] = decode_dm1(data).get("dtcs", [])
        for sig in msg.signals:
            if sig.entity:
                entity = self._entities.get(f"{device.id}_{msg.name}_{sig.name}")
                if entity is not None:
                    entity.on_value(values.get(sig.name), first)
        if changed:
            self._queue_push(device.id, changed)

    @callback
    def _touch(self, device: Device, msg: Message) -> None:
        """Same data again: only availability may change."""
        for sig in msg.signals:
            if sig.entity:
                entity = self._entities.get(f"{device.id}_{msg.name}_{sig.name}")
                if entity is not None and not entity.available_now:
                    entity.on_value(self.values.get(device.id, {}).get(f"{msg.name}.{sig.name}"), False)

    @callback
    def _check_timeouts(self, _now: Any = None) -> None:
        now = time.monotonic()
        for entity in list(self._entities.values()):
            entity.check_timeout(now)
        changed = []
        for device in self.devices.values():  # the panel's "receiving / silent / never seen" per message
            mark = tuple((self.last_seen.get((device.id, m.name)) is not None, self.is_fresh(device.id, m, now))
                         for m in device.messages if not m.send)
            if self._status_marks.get(device.id, mark) != mark:
                changed.append(device)
            self._status_marks[device.id] = mark
        if changed and self._feed:
            self._push("devices", {"devices": [self.device_view(d) for d in changed], "removed": []})

    def is_fresh(self, device_id: str, message: Message, now: float | None = None) -> bool | None:
        """True / False when the message has a timeout; None when it has none (event-type messages)."""
        timeout = message.timeout
        seen = self.last_seen.get((device_id, message.name))
        if timeout is None:
            return None if seen is None else True
        if seen is None:
            return False
        return (now if now is not None else time.monotonic()) - seen <= timeout

    # ---- sending -------------------------------------------------------------------------
    async def async_send(self, entry_id: str, frame: CanFrame) -> None:
        if self.sender is None:
            raise HomeAssistantError("the interface is not loaded")
        await self.sender(entry_id, frame)

    @callback
    def push_requests(self) -> None:
        if self._feed and self.scheduler.by_device:
            self._push("requests", {"requests": {d: self.scheduler.status(d) for d in self.scheduler.by_device}})

    def seed_written(self, device_id: str, message: str, signal: str, value: Any) -> None:
        """A restored entity's last value, so the first write after a restart keeps the other signals of a shared
        command frame (eight relay outputs in one byte)."""
        device = self.devices.get(device_id)
        msg = device.message(message) if device else None
        if msg is None or not msg.send or signal not in msg.by_name:
            return
        key = (device_id, message)
        try:
            self._written[key] = msg.build({signal: value}, self._written.get(key))
        except DefinitionError:
            return
        self.values.setdefault(device_id, {})[f"{message}.{signal}"] = value

    async def async_write(self, device_id: str, message: str, signal: str, value: Any,
                          context: Context | None = None) -> bytes:
        """Write one signal: build its command frame over the last one sent and send it."""
        device = self.devices.get(device_id)
        if device is None:
            raise DefinitionError("unknown_device", device=device_id)
        if not device.allow_write:
            raise DefinitionError("write_not_allowed", device=device.name)
        msg = device.message(message)
        sig = msg.by_name.get(signal) if msg is not None else None
        if msg is None or sig is None:
            raise DefinitionError("unknown_signal", device=device.name, signal=f"{message}.{signal}")
        target, tsig = write_target(msg, sig, {m.name: m for m in device.messages})
        entity = sig.entity or {}
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            low, high = entity.get("min", tsig.minimum), entity.get("max", tsig.maximum)
            if (low is not None and value < low) or (high is not None and value > high):
                raise DefinitionError("out_of_range", signal=sig.name, value=value, minimum=low, maximum=high)
        key = (device.id, target.name)
        lock = self._write_locks.setdefault(key, asyncio.Lock())
        async with lock:
            wait = self._write_at.get(key, 0.0) + WRITE_GAP - time.monotonic()
            if wait > 0:
                await asyncio.sleep(wait)
            data = target.build({tsig.name: value}, self._written.get(key))
            await self.async_send(device.interface, CanFrame.from_raw(target.raw_id, data, 0))
            self._written[key] = data
            self._write_at[key] = time.monotonic()
        full = f"{target.name}.{tsig.name}"
        if target is msg:  # no feedback message: what was sent is the state
            self.values.setdefault(device.id, {})[full] = value
            self._queue_push(device.id, {full: value})
            live = self._entities.get(f"{device.id}_{msg.name}_{sig.name}")
            if live is not None:
                live.on_value(value, True)
        if self.on_written is not None:
            self.on_written(device, message, signal, value, context)
        return data

    # ---- panel feed ----------------------------------------------------------------------
    @callback
    def subscribe(self, cb: Callable[[str, dict[str, Any]], None]) -> CALLBACK_TYPE:
        self._feed.append(cb)
        return lambda: self._feed.remove(cb)

    @callback
    def _queue_push(self, device_id: str, changed: dict[str, Any]) -> None:
        if not self._feed:
            return
        self._changed.setdefault(device_id, {}).update(changed)
        if self._push_handle is None:
            self._push_handle = self.hass.loop.call_later(VALUES_PUSH, self._push_values)

    @callback
    def _push_values(self) -> None:
        self._push_handle = None
        changed, self._changed = self._changed, {}
        for cb in list(self._feed):
            cb("values", {"values": changed, "t": time.time()})

    @callback
    def _push(self, kind: str, payload: dict[str, Any]) -> None:
        for cb in list(self._feed):
            cb(kind, payload)

    # ---- entities -----------------------------------------------------------------------
    def desired_unique_ids(self) -> set[str]:
        return {f"{d.id}_{m.name}_{s.name}" for d in self.devices.values() for m, s in d.adopted()}

    @callback
    def prune_registry(self) -> int:
        """Remove registry rows of signals no longer adopted (not when the store looks lost)."""
        registry = er.async_get(self.hass)
        rows = er.async_entries_for_config_entry(registry, self.entry.entry_id)
        if not self.loaded or (not self.devices and rows):
            return 0
        keep = self.desired_unique_ids()
        removed = 0
        for row in rows:
            if row.unique_id not in keep:
                registry.async_remove(row.entity_id)
                removed += 1
        return removed

    @callback
    def register_platform(self, domain: str, add_entities: AddEntitiesCallback) -> None:
        from .managed import build  # noqa: PLC0415  (managed imports this module)

        self._adders[domain] = add_entities
        entities = [e for device in self.devices.values() for e in build(self, device, domain)]
        if entities:
            add_entities(entities)

    @callback
    def entity_added(self, entity: Any) -> None:
        self._entities[entity.unique_id] = entity

    @callback
    def entity_removed(self, entity: Any) -> None:
        if self._entities.get(entity.unique_id) is entity:
            self._entities.pop(entity.unique_id)

    async def _async_rebuild(self, device: Device | None, device_id: str) -> None:
        """Replace a device's entities after an edit (registry rows survive, so entity ids stay)."""
        from .managed import build  # noqa: PLC0415

        for uid, entity in list(self._entities.items()):
            if uid.startswith(f"{device_id}_"):
                await entity.async_remove()
        self.prune_registry()
        if device is None:
            return
        for domain, add_entities in self._adders.items():
            entities = build(self, device, domain)
            if entities:
                add_entities(entities)

    # ---- editing ------------------------------------------------------------------------
    def entity_ids(self, device_id: str) -> dict[str, str]:
        """"Message.Signal" -> entity id of the device's adopted signals."""
        registry = er.async_get(self.hass)
        out = {}
        for row in er.async_entries_for_config_entry(registry, self.entry.entry_id):
            if row.unique_id.startswith(f"{device_id}_"):
                rest = row.unique_id[len(device_id) + 1:]
                msg_name, _, sig_name = rest.partition("_")
                out[rest] = row.entity_id
        return out

    def device_view(self, device: Device, with_definition: bool = True) -> dict[str, Any]:
        from .managed import platform_of  # noqa: PLC0415  (managed imports this module)

        now = time.monotonic()
        registry = er.async_get(self.hass)
        values = self.values.get(device.id, {})
        messages = []
        for msg in device.messages:
            seen = self.last_seen.get((device.id, msg.name))
            signals = []
            for sig in msg.signals:
                uid = f"{device.id}_{msg.name}_{sig.name}"
                platform = platform_of(sig)
                entity_id = registry.async_get_entity_id(platform, DOMAIN, uid) if sig.entity else None
                row = registry.async_get(entity_id) if entity_id else None
                row_view = {"name": sig.name, "value": values.get(f"{msg.name}.{sig.name}"), "unit": sig.unit,
                            "adopted": bool(sig.entity), "entity_id": entity_id, "platform": platform,
                            "disabled": bool(row and row.disabled_by)}
                if is_write(sig):
                    row_view["write"] = write_view(sig)
                signals.append(row_view)
            messages.append({"name": msg.name, "id": msg.label(), "seen_s_ago": None if seen is None else
                             round(now - seen, 1), "fresh": self.is_fresh(device.id, msg, now), "signals": signals,
                             "send": msg.send})
        out = {"id": device.id, "name": device.name, "interface": device.interface, "template": device.template,
               "source": device.source, "manufacturer": device.manufacturer, "model": device.model,
               "params": device.params, "groups": device.groups, "status": messages,
               "extra": self.extra.get(device.id, {}), "active": device.active, "allow_write": device.allow_write,
               "has_requests": bool(device.requests), "writable": device.writable,
               "requests": self.scheduler.status(device.id)}
        if with_definition:
            out["definition"] = device.as_dict()
        return out

    async def async_save(self, raw: dict[str, Any]) -> Device:
        raw = dict(raw)
        raw["id"] = raw.get("id") or new_id()
        device = Device.from_dict(raw)
        if self.hass.config_entries.async_get_entry(device.interface) is None:
            raise DefinitionError("unknown_interface", interface=device.interface)
        for other in self.devices.values():
            if other.id != device.id and other.name.casefold() == device.name.casefold():
                raise DefinitionError("duplicate_name", name=device.name)
        old = self.devices.get(device.id)
        device.created = old.created if old is not None else (device.created or time.time())
        self.devices[device.id] = device
        self._forget(device.id)
        self._reindex()
        self._store.async_delay_save(self._data, SAVE_DELAY)
        await self._async_rebuild(device, device.id)
        self._update_registry_device(device)
        self._push("devices", {"devices": [self.device_view(device)], "removed": []})
        if self.on_frames_routed is not None:
            self.on_frames_routed(device.interface)
        return device

    async def async_delete(self, device_id: str) -> Device | None:
        device = self.devices.pop(device_id, None)
        if device is None:
            return None
        self._forget(device_id)
        for key in [k for k in self._written if k[0] == device_id]:  # kept across edits, not past a delete
            self._written.pop(key, None)
        self._status_marks.pop(device_id, None)
        self._reindex()
        self._store.async_delay_save(self._data, SAVE_DELAY)
        await self._async_rebuild(None, device_id)
        registry = dr.async_get(self.hass)
        entry = registry.async_get_device_by_identifier((DOMAIN, f"device_{device_id}"), self.entry.entry_id)
        if entry is not None:
            registry.async_remove_device(entry.id)
        self._push("devices", {"devices": [], "removed": [device_id]})
        if self.on_frames_routed is not None:
            self.on_frames_routed(device.interface)
        return device

    def _forget(self, device_id: str) -> None:
        for key in [k for k in self._last_data if k[0] == device_id]:
            self._last_data.pop(key, None)
        for key in [k for k in self.last_seen if k[0] == device_id]:
            self.last_seen.pop(key, None)
        self.values.pop(device_id, None)
        self.extra.pop(device_id, None)
        self._status_marks[device_id] = ()  # the panel was just sent "never seen": the next check sends the truth

    def _update_registry_device(self, device: Device) -> None:
        registry = dr.async_get(self.hass)
        entry = registry.async_get_device_by_identifier((DOMAIN, f"device_{device.id}"), self.entry.entry_id)
        if entry is not None and (entry.name != device.name):
            registry.async_update_device(entry.id, name=device.name)

    def resolve(self, ref: str) -> Device | None:
        want = ref.strip().casefold()
        for device in self.devices.values():
            if want in (device.id.casefold(), device.name.casefold()):
                return device
        return None
