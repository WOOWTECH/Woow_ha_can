"""The admin layer (one per Home Assistant): panel feed, monitor viewers, periodic sends, captures.

The interfaces are separate config entries (CanHub); this layer finds them in the registry kept
in hass.data[DOMAIN]["hubs"]. Capture files opened in the panel become read-only sources with the
same monitor and trace views as a live interface.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import logging
import os
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_FINAL_WRITE
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util, slugify

from . import analysis
from .activity import ActivityLog
from .can_port import CAN_RTR_FLAG, F_ERR, F_OWN, CanFrame, id_hex
from .capture import Recording, TraceBuffer, TraceFrame, TraceSnapshot, safe_name, trace_matcher
from .databases import DatabaseLibrary
from .devices import DeviceManager
from . import formats
from .monitor import TX_KEY
from .signals import DefinitionError, j1939_pgn
from .templates import TemplateLibrary
from .const import (
    CAPTURE_DIR,
    CAPTURE_FLUSH,
    CAPTURE_MAX_BYTES,
    DOMAIN,
    KIND_HUB,
    MONITOR_PUSH,
    TRACE_CAPACITY,
)
from .hub import CanHub
from .monitor import Monitor, Viewer
from .panel import async_register_panel, async_remove_panel
from .periodic import ItemState, PeriodicItem, PeriodicManager

_LOGGER = logging.getLogger(__name__)


# J1939 / NMEA 2000 network management a monitor row can be named after, with or without a device
J1939_NAMES = {0xEC00: "J1939 TP.CM", 0xEB00: "J1939 TP.DT", 0xEA00: "J1939 Request", 0xEE00: "J1939 Address Claimed",
               0xE800: "J1939 Acknowledgment", 0xFECA: "J1939 DM1", 0xFECB: "J1939 DM2", 126996: "N2K Product Information",
               126993: "N2K Heartbeat", 126208: "N2K Group Function", 126464: "N2K PGN List"}


def hubs(hass: HomeAssistant) -> dict[str, CanHub]:
    """Loaded interfaces by config entry id."""
    return hass.data.setdefault(DOMAIN, {}).setdefault("hubs", {})


class OfflineSource:
    """A capture file opened in the panel: the monitor and trace of one of its interfaces."""

    live = False

    def __init__(self, source_id: str, file: str, ifname: str, frames: list[tuple[float, int, bytes, int]],
                 truncated: bool, fmt: str = "log") -> None:
        self.id = source_id
        self.file = file
        self.format = fmt
        self.port = ifname
        self.name = f"{file} · {ifname}"
        self.monitor = Monitor()
        self.trace = TraceBuffer(max(1, min(len(frames), TRACE_CAPACITY)))
        self.truncated = truncated
        for ts, raw, data, flags in frames:
            self.trace.append(ts, raw, data, flags)
            if not flags & F_ERR:  # error frames only go to the trace
                self.monitor.add(ts, raw, data, flags)
        self.start = frames[0][0] if frames else None
        self.end = frames[-1][0] if frames else None

    def info(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "file": self.file, "port": self.port, "offline": True,
                "format": self.format,
                "frames": self.trace.seq, "truncated": self.truncated, "start": self.start, "end": self.end,
                "monitor": {"ids": len(self.monitor.stats), "frames": self.monitor.frames, "overflow": self.monitor.overflow},
                "trace": {"first": self.trace.first, "end": self.trace.seq, "capacity": self.trace.capacity}}


class AdminHub:
    """Owns the panel and the shared lists; streams interface health and changes to the panel."""

    kind = KIND_HUB

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.activity = ActivityLog(hass)
        self.devices = DeviceManager(hass, entry)
        self.templates = TemplateLibrary(hass)
        self.databases = DatabaseLibrary(hass)
        self._names: dict[str, dict[int, str | None]] = {}  # entry id -> raw id -> message name
        self._names_version: tuple[int, int] = (0, 0)
        self.periodic = PeriodicManager(hass, self._periodic_send)
        self.periodic.on_stopped = self._periodic_stopped
        self.capture_dir = hass.config.path(CAPTURE_DIR)
        self.offline: dict[str, OfflineSource] = {}
        self._subs: list[Callable[[str, dict[str, Any]], None]] = []
        self._viewers: list[tuple[Any, Viewer]] = []
        self._viewer_handle: Any = None
        self._status_unsubs: dict[str, CALLBACK_TYPE] = {}
        self._flush_handle: Any = None
        self._unsubs: list[CALLBACK_TYPE] = []
        self.searches: dict[str, analysis.Search] = {}  # source id -> the value search of the panel / agents
        self.guided: dict[str, list[analysis.Phase]] = {}  # source id -> guided capture phases
        self._analysis_lock = asyncio.Lock()

    @property
    def hubs(self) -> dict[str, CanHub]:
        return hubs(self.hass)

    async def async_start(self) -> None:
        await self.activity.async_load()
        await self.periodic.async_load()
        await self.devices.async_load()
        await self.templates.async_load()
        await self.databases.async_load()
        # Entity rows of signals no longer adopted; before any platform registers.
        self.devices.prune_registry()
        self._unsubs += [
            self.activity.subscribe(lambda payload: self._send("activity", payload)),
            self.periodic.subscribe(lambda payload: self._send("periodic", payload)),
            self.devices.subscribe(self._send),
            self.hass.bus.async_listen(EVENT_HOMEASSISTANT_FINAL_WRITE, self._async_final_write),
        ]
        self.devices.cannot_send = self._cannot_send
        self.devices.sender = self._device_send
        self.devices.on_written = self._on_written
        self.devices.start()
        for hub in self.hubs.values():
            hub.frame_hook = self.devices.on_frame
        await async_register_panel(self.hass)

    # ---- devices that send ----------------------------------------------------------------
    def _cannot_send(self, entry_id: str) -> str | None:
        """Why a device's interface cannot send right now (None: it can)."""
        hub = self.hubs.get(entry_id)
        if hub is None:
            return "interface not loaded"
        if not hub.io.is_open:
            return "interface down"
        if hub.cfg.listen_only and not hub.io.virtual:
            return "listen-only"
        if hub.status.get("state") in ("bus_off", "stopped"):
            return f"bus state {hub.status['state']}"
        return None

    async def _device_send(self, entry_id: str, frame: CanFrame) -> None:
        hub = self.hubs.get(entry_id)
        if hub is None:
            raise HomeAssistantError("the interface is not loaded")
        await hub.async_send(frame)

    @callback
    def _on_written(self, device: Any, message: str, signal: str, value: Any, context: Any) -> None:
        self.hass.async_create_task(self.activity.async_record(
            "entity", "write_signal", "signal_written", {"device": device.name, "signal": f"{message}.{signal}",
                                                         "value": value},
            context=context, device_id=device.id, port_id=device.interface))

    async def async_stop(self) -> None:
        self.periodic.shutdown()
        self.devices.stop()
        for hub in self.hubs.values():
            hub.frame_hook = None
        for hub in list(self.hubs.values()):
            await self.async_stop_capture(hub.entry.entry_id, log=False)
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        for unsub in self._status_unsubs.values():
            unsub()
        self._status_unsubs.clear()
        if self._viewer_handle is not None:
            self._viewer_handle.cancel()
            self._viewer_handle = None
        async_remove_panel(self.hass)
        await self.activity.async_flush()
        await self.periodic.async_flush()
        await self.devices.async_flush()

    async def _async_final_write(self, _event: Event) -> None:
        await self.activity.async_flush()
        await self.periodic.async_flush()
        await self.devices.async_flush()

    # ---- interfaces coming and going ---------------------------------------------------
    @callback
    def hub_added(self, hub: CanHub) -> None:
        hub.frame_hook = self.devices.on_frame
        if self._subs:
            self._watch_status(hub)
        self._send("interfaces", {"interfaces": [hub.info()], "removed": []})

    @callback
    def hub_removed(self, entry_id: str) -> None:
        self.periodic.stop_interface(entry_id)
        for pair in [p for p in self._viewers if getattr(p[0], "entry", None) is not None
                     and p[0].entry.entry_id == entry_id]:
            self._viewers.remove(pair)
            pair[1].send({"gone": True})
        if unsub := self._status_unsubs.pop(entry_id, None):
            unsub()
        self._send("interfaces", {"interfaces": [], "removed": [entry_id]})

    def resolve(self, ref: str) -> CanHub:
        """An interface by config entry id, name (CAN0) or interface name (can0)."""
        want = ref.strip().casefold()
        for hub in self.hubs.values():
            if want in (hub.entry.entry_id.casefold(), hub.name.casefold(), hub.port.casefold()):
                return hub
        raise HomeAssistantError(f"no WOOW CAN interface {ref!r} (have: "
                                 f"{', '.join(sorted(h.name for h in self.hubs.values())) or 'none'})")

    def source(self, source_id: str) -> CanHub | OfflineSource:
        if source_id in self.offline:
            return self.offline[source_id]
        hub = self.hubs.get(source_id)
        if hub is None:
            raise HomeAssistantError(f"unknown source {source_id}")
        return hub

    # ---- panel feed --------------------------------------------------------------------
    @callback
    def subscribe(self, cb: Callable[[str, dict[str, Any]], None]) -> CALLBACK_TYPE:
        first = not self._subs
        self._subs.append(cb)
        if first:
            for hub in self.hubs.values():
                self._watch_status(hub)

        @callback
        def unsub() -> None:
            self._subs.remove(cb)
            if not self._subs:
                for entry_id in list(self._status_unsubs):
                    self._status_unsubs.pop(entry_id)()

        return unsub

    @callback
    def _watch_status(self, hub: CanHub) -> None:
        """Health every second while someone has the panel open."""
        entry_id = hub.entry.entry_id
        if entry_id in self._status_unsubs:
            return
        remove = hub.add_status_listener(lambda h: self._send("interfaces", {"interfaces": [h.info()],
                                                                             "removed": []}))
        hub.set_fast(True)

        @callback
        def unwatch() -> None:
            remove()
            hub.set_fast(False)

        self._status_unsubs[entry_id] = unwatch

    @callback
    def _send(self, kind: str, payload: dict[str, Any]) -> None:
        for cb in list(self._subs):
            cb(kind, payload)

    def snapshot(self) -> dict[str, Any]:
        language = self.hass.config.language or "en"
        return {
            "interfaces": [hub.info() for hub in self.hubs.values()],
            "offline": [src.info() for src in self.offline.values()],
            "periodic": self.periodic.snapshot(),
            "activity": self.activity.recent(200),
            "devices": [self.devices.device_view(d) for d in self.devices.devices.values()],
            "values": self.devices.values,
            "templates": self.templates.summaries(language),
            "databases": self.databases.summaries(),
            "now": time.time(),
        }

    # ---- names and decoding (monitor) ------------------------------------------------------
    def _definitions(self, entry_id: str | None) -> list[tuple[str, Any]]:
        """(where from, Message) for an interface: its devices first, then attached DBC files."""
        out: list[tuple[str, Any]] = []
        for device in self.devices.devices.values():
            if entry_id is not None and device.interface == entry_id:
                out.extend((device.name, m) for m in device.messages)
        out.extend(self.databases.messages_for(entry_id))
        return out

    def message_name(self, entry_id: str | None, raw: int) -> str | None:
        version = (self.devices.version, self.databases.version)
        if version != self._names_version:
            self._names.clear()
            self._names_version = version
        cache = self._names.setdefault(entry_id or "", {})
        if raw not in cache:
            name = next((m.name for _src, m in self._definitions(entry_id) if m.matches(raw)), None)
            if name is None and raw & 0x80000000:
                name = J1939_NAMES.get(j1939_pgn(raw))
            cache[raw] = name
        return cache[raw]

    def names_for(self, source: Any, keys: list[int]) -> dict[int, str]:
        entry_id = source.entry.entry_id if hasattr(source, "entry") else None
        out = {}
        for key in keys:
            name = self.message_name(entry_id, key % TX_KEY if key >= TX_KEY else key)
            if name:
                out[key] = name
        return out

    def decode(self, source_id: str, raw: int, data: bytes) -> list[dict[str, Any]]:
        """What the definitions on an interface make of one frame."""
        src = self.source(source_id)
        entry_id = src.entry.entry_id if hasattr(src, "entry") else None
        out = []
        for origin, msg in self._definitions(entry_id):
            if msg.transport == "n2k_fast" or not msg.matches(raw, data):  # a single fast-packet frame says little
                continue
            values = msg.decode(data)
            out.append({"source": origin, "message": msg.name, "signals": [
                {"name": sig.name, "value": values.get(sig.name), "unit": sig.unit, "adopted": bool(sig.entity),
                 "start": sig.start, "length": sig.length, "byte_order": sig.byte_order}
                for sig in msg.signals if sig.name in values]})
        return out

    # ---- devices -----------------------------------------------------------------------------
    @callback
    def databases_changed(self) -> None:
        self._send("databases", {"databases": self.databases.summaries()})

    async def async_set_signal(self, device_ref: str, message: str, signal: str, adopted: bool | None,
                               entity: dict[str, Any] | None):
        """Adopt or drop a signal, or merge new entity settings into it."""
        device = self.devices.resolve(device_ref)
        if device is None:
            raise DefinitionError("unknown_device", device=device_ref)
        raw = device.as_dict()
        msg = next((m for m in raw["messages"] if m["name"] == message), None)
        if msg is None:
            raise DefinitionError("unknown_message", device=device.name, message=message)
        sig = next((s for s in msg["signals"] if s["name"] == signal), None)
        if sig is None:
            raise DefinitionError("unknown_signal", device=device.name, signal=signal)
        if adopted is False:
            sig.pop("entity", None)
        else:
            current = dict(sig.get("entity") or {})
            if adopted or entity:
                for key, value in (entity or {}).items():
                    if value is None:
                        current.pop(key, None)
                    else:
                        current[key] = value
                current.setdefault("enabled", True)
                sig["entity"] = current
        return await self.devices.async_save(raw)

    async def async_device_options(self, device_ref: str, active: bool | None = None,
                                   allow_write: bool | None = None):
        """Turn a device's requests (polling) and writing on or off."""
        device = self.devices.resolve(device_ref)
        if device is None:
            raise DefinitionError("unknown_device", device=device_ref)
        raw = device.as_dict()
        if active is not None:
            if active and not device.requests:
                raise DefinitionError("no_requests", device=device.name)
            raw["active"] = active
        if allow_write is not None:
            if allow_write and not device.writable:
                raise DefinitionError("nothing_to_write", device=device.name)
            raw["allow_write"] = allow_write
        return await self.devices.async_save(raw)

    def seen_ids(self, entry_id: str) -> set[int]:
        """IDs the interface has received lately: its monitor, and the trace buffer (which a cleared monitor keeps)."""
        hub = self.hubs.get(entry_id)
        if hub is None:
            return set()
        return {key for key in hub.monitor.stats if key < TX_KEY} | hub.trace.recent_ids()

    async def async_create_from_template(self, template_ref: str, entry_id: str, name: str,
                                         params: dict[str, Any] | None, groups: list[str] | None):
        template = self.templates.get(template_ref)
        if template is None:
            raise DefinitionError("unknown_template", template=template_ref,
                                  templates=", ".join(sorted(self.templates.templates)))
        raw = self.templates.instantiate(template, entry_id, name, params, groups, self.hass.config.language or "en",
                                         self.seen_ids(entry_id))
        return await self.devices.async_save(raw)

    async def async_create_from_dbc(self, dbc_ref: str, entry_id: str, name: str, messages: list[str] | None):
        dbc_name = self.databases.resolve(dbc_ref)
        if dbc_name is None:
            raise DefinitionError("unknown_dbc", name=dbc_ref)
        definitions = self.databases.definitions(dbc_name, messages)
        adopted = []
        for definition in definitions:
            definition = {**definition, "signals": [
                {**sig, "entity": sig.get("entity") or {"enabled": True}} if not sig.get("multiplexor") else sig
                for sig in definition["signals"]]}
            adopted.append(definition)
        raw = {"name": name.strip() or dbc_name.removesuffix(".dbc"), "interface": entry_id, "source": f"dbc:{dbc_name}",
               "manufacturer": "DBC", "model": dbc_name, "messages": adopted}
        return await self.devices.async_save(raw)

    # ---- monitor viewers ---------------------------------------------------------------
    @callback
    def subscribe_monitor(self, source_id: str, send: Callable[[dict[str, Any]], None]) -> tuple[Viewer, CALLBACK_TYPE]:
        src = self.source(source_id)
        viewer = Viewer(send)
        detach = src.monitor.attach(viewer)
        viewer.named = set(src.monitor.stats)
        send({"seq": 0, "t": round(time.time(), 6), "full": True, "rows": src.monitor.full(),
              "overflow": src.monitor.overflow, "frames": src.monitor.frames, "trace_end": src.trace.seq,
              "trace_first": src.trace.first, "names": self.names_for(src, list(src.monitor.stats))})
        pair = (src, viewer)
        self._viewers.append(pair)
        if self._viewer_handle is None:
            self._viewer_handle = self.hass.loop.call_later(MONITOR_PUSH, self._push_viewers)

        @callback
        def unsub() -> None:
            detach()
            if pair in self._viewers:
                self._viewers.remove(pair)

        return viewer, unsub

    @callback
    def _push_viewers(self) -> None:
        self._viewer_handle = None
        if not self._viewers:
            return
        now = time.time()
        for src, viewer in list(self._viewers):
            payload = src.monitor.batch(viewer, now, {"trace_end": src.trace.seq, "trace_first": src.trace.first})
            if payload is not None:
                fresh = [row[0] for row in payload["rows"] if row[0] not in viewer.named]
                if fresh or payload.get("clear"):
                    viewer.named.update(fresh)
                    payload["names"] = self.names_for(src, fresh)
                viewer.send(payload)
        self._viewer_handle = self.hass.loop.call_later(MONITOR_PUSH, self._push_viewers)

    # ---- sending -----------------------------------------------------------------------
    async def _periodic_send(self, entry_id: str, frame: CanFrame) -> None:
        hub = self.hubs.get(entry_id)
        if hub is None:
            raise HomeAssistantError("the interface is not loaded")
        await hub.async_send(frame)

    @callback
    def _periodic_stopped(self, item: PeriodicItem, state: ItemState) -> None:
        if state.stopped_by == "error":
            self.hass.async_create_task(self.activity.async_record(
                "panel", "periodic", "periodic_failed", {"name": item.name, "error": state.error or "?"},
                user=None, ok=False, port_id=item.entry_id))

    # ---- captures ----------------------------------------------------------------------
    def _capture_path(self, name: str) -> str:
        return os.path.join(self.capture_dir, safe_name(name))

    def list_captures_blocking(self) -> list[dict[str, Any]]:
        recording = {hub.recording.name for hub in self.hubs.values() if hub.recording is not None}
        out = []
        if os.path.isdir(self.capture_dir):
            for name in sorted(os.listdir(self.capture_dir)):
                path = os.path.join(self.capture_dir, name)
                if not os.path.isfile(path) or name.startswith("."):
                    continue
                stat = os.stat(path)
                out.append({"name": name, "size": stat.st_size, "modified": round(stat.st_mtime, 3),
                            "recording": name in recording})
        out.sort(key=lambda c: -c["modified"])
        return out

    async def async_list_captures(self) -> list[dict[str, Any]]:
        return await self.hass.async_add_executor_job(self.list_captures_blocking)

    async def async_start_capture(self, entry_id: str) -> Recording:
        hub = self.hubs.get(entry_id)
        if hub is None:
            raise HomeAssistantError("the interface is not loaded")
        if hub.recording is not None:
            return hub.recording
        stamp = dt_util.now().strftime("%Y%m%d-%H%M%S")
        name = f"{slugify(hub.name) or hub.port}_{stamp}.log"
        path = self._capture_path(name)
        await self.hass.async_add_executor_job(os.makedirs, self.capture_dir, 0o755, True)
        await self.hass.async_add_executor_job(Recording.write, path, [])
        hub.recording = Recording(path, hub.port, entry_id, CAPTURE_MAX_BYTES)
        if self._flush_handle is None:
            self._flush_handle = self.hass.loop.call_later(CAPTURE_FLUSH, self._flush_recordings)
        self._send("captures", {"changed": True})
        return hub.recording

    async def async_stop_capture(self, entry_id: str, log: bool = True) -> Recording | None:
        hub = self.hubs.get(entry_id)
        if hub is None or hub.recording is None:
            return None
        rec, hub.recording = hub.recording, None
        lines = rec.take()
        if lines:
            await self.hass.async_add_executor_job(Recording.write, rec.path, lines)
        if log:
            self._send("captures", {"changed": True})
        return rec

    @callback
    def _flush_recordings(self) -> None:
        self._flush_handle = None
        active = [hub.recording for hub in self.hubs.values() if hub.recording is not None]
        for rec in active:
            lines = rec.take()
            if lines:
                self.hass.async_add_executor_job(Recording.write, rec.path, lines)
            if rec.full:
                hub = self.hubs.get(rec.entry_id)
                if hub is not None and hub.recording is rec:
                    hub.recording = None
                    self._send("captures", {"changed": True})
        if any(hub.recording is not None for hub in self.hubs.values()):
            self._flush_handle = self.hass.loop.call_later(CAPTURE_FLUSH, self._flush_recordings)

    async def async_delete_capture(self, name: str) -> None:
        path = self._capture_path(name)
        if any(hub.recording is not None and hub.recording.path == path for hub in self.hubs.values()):
            raise HomeAssistantError("stop the recording first")
        await self.hass.async_add_executor_job(os.remove, path)
        for source_id in [s for s, src in self.offline.items() if src.file == name]:
            self.offline.pop(source_id)
        self._send("captures", {"changed": True})
        self._send("offline", {"offline": [s.info() for s in self.offline.values()]})

    async def async_save_upload(self, name: str, data: bytes) -> str:
        name = safe_name(name)
        if not name.lower().endswith(formats.EXTENSIONS):
            name += ".log"
        path = self._capture_path(name)

        def write() -> None:
            os.makedirs(self.capture_dir, 0o755, exist_ok=True)
            with open(path, "wb") as fh:
                fh.write(data)

        await self.hass.async_add_executor_job(write)
        self._send("captures", {"changed": True})
        return name

    async def async_open_capture(self, name: str) -> list[OfflineSource]:
        path = self._capture_path(name)
        by_iface, skipped, fmt = await self.hass.async_add_executor_job(formats.read_file, path, TRACE_CAPACITY + 1)
        opened = []
        for ifname, frames in by_iface.items():
            truncated = len(frames) > TRACE_CAPACITY
            frames = frames[-TRACE_CAPACITY:]
            source_id = f"file:{name}:{ifname}"
            src = await self.hass.async_add_executor_job(OfflineSource, source_id, name, ifname, frames, truncated,
                                                          fmt)
            self.offline[source_id] = src
            opened.append(src)
        if not opened:
            raise HomeAssistantError(f"{name}: no CAN frames found ({skipped} lines not understood); readable: "
                                     f"{', '.join(formats.READ_FORMATS.values())}")
        self._send("offline", {"offline": [s.info() for s in self.offline.values()]})
        return opened

    async def async_convert_capture(self, name: str, fmt: str) -> dict[str, Any]:
        """Write a capture (any readable format) as `fmt` next to it: <name>.<ext>, -2, -3 ... if taken."""
        if fmt not in formats.WRITE_FORMATS:
            raise HomeAssistantError(f"unknown format {fmt!r}: use one of {', '.join(formats.WRITE_FORMATS)}")
        src = self._capture_path(name)
        if any(hub.recording is not None and hub.recording.path == src for hub in self.hubs.values()):
            raise HomeAssistantError("stop the recording first")
        stem = os.path.splitext(os.path.basename(src))[0]

        def run() -> dict[str, Any]:
            if not os.path.isfile(src):
                raise HomeAssistantError(f"no capture named {name!r}")
            target, n = f"{stem}.{fmt}", 1
            while os.path.exists(self._capture_path(target)):
                n += 1
                target = f"{stem}-{n}.{fmt}"
            dst = self._capture_path(target)
            try:
                result = formats.convert_file(src, dst, fmt)
            except ValueError as err:
                if os.path.exists(dst):
                    os.remove(dst)
                raise HomeAssistantError(f"{name}: {err}") from err
            return {"name": target, "size": os.path.getsize(dst), **result}

        result = await self.hass.async_add_executor_job(run)
        self._send("captures", {"changed": True})
        return result

    @callback
    def close_offline(self, source_id: str) -> None:
        self.offline.pop(source_id, None)
        self.searches.pop(source_id, None)
        self._viewers = [(src, v) for src, v in self._viewers if getattr(src, "id", None) != source_id]
        self._send("offline", {"offline": [s.info() for s in self.offline.values()]})

    # ---- reverse engineering -----------------------------------------------------------
    @staticmethod
    def key_text(key: int) -> str:
        """A monitor key as people read it: 18FF50E5, or 123 (tx) for frames WOOW CAN sent."""
        return id_hex(key & 0xFFFFFFFF) + (" (tx)" if key & TX_KEY else "")

    @staticmethod
    def _now(src: Any) -> float:
        """'Now' of a source: the clock for interfaces, the last frame for files."""
        return time.time() if getattr(src, "live", True) else (src.end or 0.0)

    def _frames_of(self, src: Any, snapshot: TraceSnapshot, key: int, seconds: float | None,
                   limit: int) -> list[TraceFrame]:
        """Blocking: the newest frames of one monitor key, oldest first."""
        raw = key & 0xFFFFFFFF
        match = trace_matcher(lambda r: r == raw, "tx" if key & TX_KEY else "rx", errors=False)
        since = self._now(src) - seconds if seconds else None
        return list(reversed(snapshot.page(None, limit, match, since)["frames"]))

    async def async_bits(self, source_id: str, key: int, seconds: float | None = None,
                         limit: int = 2000) -> dict[str, Any]:
        src = self.source(source_id)
        snapshot = src.trace.snapshot()

        def run() -> dict[str, Any]:
            frames = self._frames_of(src, snapshot, key, seconds, limit)
            out = analysis.bit_activity([f.data for f in frames])
            out.update({"id": self.key_text(key), "key": key, "from": frames[0].t if frames else None,
                        "to": frames[-1].t if frames else None})
            return out

        return await self.hass.async_add_executor_job(run)

    async def async_try_signal(self, source_id: str, key: int, sig: Any, seconds: float | None = 60.0,
                               limit: int = 2000, samples: int = 300) -> dict[str, Any]:
        """A candidate field decoded over the recent frames of one ID."""
        src = self.source(source_id)
        snapshot = src.trace.snapshot()

        def run() -> dict[str, Any]:
            frames = self._frames_of(src, snapshot, key, seconds, limit)
            return {"id": self.key_text(key), **analysis.series([(f.t, f.data) for f in frames], sig, samples)}

        return await self.hass.async_add_executor_job(run)

    def _latest(self, src: Any) -> dict[int, bytes]:
        return {key: st.data for key, st in src.monitor.stats.items() if st.data and not st.raw & CAN_RTR_FLAG}

    async def async_find(self, source_id: str, action: str, mode: str | None = None, value: float | None = None,
                         tolerance: float | None = None, limit: int = 20) -> dict[str, Any]:
        """Find the field holding a value: start (with the value, or without for a relative search), then narrow
        (equals a new value, increased, decreased, changed, unchanged) as the equipment changes."""
        src = self.source(source_id)
        async with self._analysis_lock:
            search = self.searches.get(source_id)
            if action == "start":
                search = self.searches[source_id] = analysis.Search()
                await self.hass.async_add_executor_job(search.start, self._latest(src), value, tolerance)
            elif action == "narrow":
                if search is None:
                    raise HomeAssistantError("no search on this interface: start one first")
                try:
                    await self.hass.async_add_executor_job(search.narrow, self._latest(src), mode or "equals", value,
                                                           tolerance)
                except ValueError as err:
                    raise HomeAssistantError(str(err)) from err
            elif action == "clear":
                self.searches.pop(source_id, None)
                search = None
            elif action != "status":
                raise HomeAssistantError(f"unknown action {action!r}")
            if search is None:
                return {"left": 0, "ids": 0, "truncated": False, "steps": [], "candidates": []}
            return search.summary(limit, self.key_text)

    async def async_guided(self, source_id: str, action: str, label: str | None = None,
                           limit: int = 20) -> dict[str, Any]:
        """Guided capture: start (idle), next (do the action), next (undo it), ... finish -> what differs.
        Phases alternate idle / action; repeating the action rules out changes that only coincided."""
        src = self.source(source_id)
        if not getattr(src, "live", True):
            raise HomeAssistantError("a guided capture needs a live interface")
        now = time.time()
        phases = self.guided.get(source_id)
        result: dict[str, Any] = {}
        if action == "start":
            phases = self.guided[source_id] = [analysis.Phase(label or "idle", now)]
        elif action in ("next", "finish"):
            if not phases or phases[-1].end is not None:
                raise HomeAssistantError("no guided capture running on this interface: start one first")
            if action == "next":
                if len(phases) >= analysis.MAX_PHASES:
                    raise HomeAssistantError(f"{analysis.MAX_PHASES} phases at most: finish now")
                phases[-1].end = now
                phases.append(analysis.Phase(label or ("action" if len(phases) % 2 else "idle"), now))
            else:
                if len(phases) < 2:
                    raise HomeAssistantError("finish needs two phases: start (idle), next (action), then finish")
                phases[-1].end = now
                result = await self._async_compare(src, phases, limit)
        elif action == "cancel":
            self.guided.pop(source_id, None)
            phases = None
        elif action != "status":
            raise HomeAssistantError(f"unknown action {action!r}")
        status = [{"label": p.label, "start": round(p.start, 3), "end": None if p.end is None else round(p.end, 3),
                   "seconds": round((p.end or now) - p.start, 1)} for p in phases or []]
        running = bool(phases) and phases[-1].end is None
        return {"phases": status, "running": running, **result}

    async def _async_compare(self, src: Any, phases: list[analysis.Phase], limit: int) -> dict[str, Any]:
        snapshot = src.trace.snapshot()

        def run() -> dict[str, Any]:
            buckets: list[dict[int, list[bytes]]] = [{} for _ in phases]
            seq = snapshot.seq_at(phases[0].start)
            lost = seq == snapshot.first and snapshot.first > 0
            ends = [p.end or time.time() for p in phases]
            for frame in snapshot.frames(seq):
                if frame.flags & F_ERR or frame.raw & CAN_RTR_FLAG:
                    continue
                index = next((i for i, p in enumerate(phases) if p.start <= frame.t < ends[i]), None)
                if index is None:
                    if frame.t >= ends[-1]:
                        break
                    continue
                key = frame.raw | (TX_KEY if frame.flags & F_OWN else 0)
                buckets[index].setdefault(key, []).append(frame.data)
            out: dict[str, Any] = {"results": analysis.compare(buckets, self.key_text, limit),
                                   "frames": [sum(len(v) for v in b.values()) for b in buckets]}
            if lost:
                out["warning"] = "the start of the first phase is no longer in the buffer: keep the phases shorter"
            return out

        return await self.hass.async_add_executor_job(run)

    async def async_add_signal(self, entry_id: str, key: int, signal: dict[str, Any], device_ref: str | None = None,
                               device_name: str | None = None, message: str | None = None, adopt: bool = True):
        """Put a field found by the tools above into a device (a new one unless device_ref names one)."""
        hub = self.hubs.get(entry_id)
        if hub is None:
            raise HomeAssistantError("the interface is not loaded")
        raw_id = key & 0xFFFFFFFF
        extended = bool(raw_id & 0x80000000)
        can_id = raw_id & 0x1FFFFFFF
        id_text = f"{can_id:08X}" if extended else f"{can_id:03X}"
        if device_ref:
            device = self.devices.resolve(device_ref)
            if device is None:
                raise DefinitionError("unknown_device", device=device_ref)
            if device.interface != entry_id:
                raise DefinitionError("other_interface", device=device.name)
            definition = device.as_dict()
        else:
            definition = {"name": device_name or f"{hub.name} {id_text}", "interface": entry_id, "messages": [],
                          "source": "custom"}
        msg = next((m for m in definition["messages"] if m.get("can_id") is not None and not m.get("id_mask")
                    and not m.get("filters") and int(str(m["can_id"]), 16) == can_id
                    and bool(m.get("extended")) == extended), None)
        if msg is None:
            stat = hub.monitor.stats.get(key)
            msg = {"name": message or f"ID_{id_text}", "can_id": id_text, "extended": extended,
                   "length": len(stat.data) if stat and stat.data else 8, "signals": []}
            if stat and stat.period:
                msg["cycle_ms"] = max(1, round(stat.period * 1000))
            definition["messages"].append(msg)
        if any(s["name"] == signal["name"] for s in msg["signals"]):
            raise DefinitionError("duplicate_signal", message=msg["name"])
        entry = {k: v for k, v in signal.items() if v not in (None, "")}
        if adopt:
            entry["entity"] = {"enabled": True}
        msg["signals"].append(entry)
        return await self.devices.async_save(definition), msg["name"]
