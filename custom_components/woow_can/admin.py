"""The admin layer (one per Home Assistant): panel feed, monitor viewers, periodic sends, captures.

The interfaces are separate config entries (CanHub); this layer finds them in the registry kept
in hass.data[DOMAIN]["hubs"]. Capture files opened in the panel become read-only sources with the
same monitor and trace views as a live interface.
"""

from __future__ import annotations

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

from .activity import ActivityLog
from .can_port import F_ERR, CanFrame
from .capture import Recording, TraceBuffer, read_log, safe_name
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


def hubs(hass: HomeAssistant) -> dict[str, CanHub]:
    """Loaded interfaces by config entry id."""
    return hass.data.setdefault(DOMAIN, {}).setdefault("hubs", {})


class OfflineSource:
    """A capture file opened in the panel: the monitor and trace of one of its interfaces."""

    live = False

    def __init__(self, source_id: str, file: str, ifname: str, frames: list[tuple[float, int, bytes, int]],
                 truncated: bool) -> None:
        self.id = source_id
        self.file = file
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

    @property
    def hubs(self) -> dict[str, CanHub]:
        return hubs(self.hass)

    async def async_start(self) -> None:
        await self.activity.async_load()
        await self.periodic.async_load()
        self._unsubs += [
            self.activity.subscribe(lambda payload: self._send("activity", payload)),
            self.periodic.subscribe(lambda payload: self._send("periodic", payload)),
            self.hass.bus.async_listen(EVENT_HOMEASSISTANT_FINAL_WRITE, self._async_final_write),
        ]
        await async_register_panel(self.hass)

    async def async_stop(self) -> None:
        self.periodic.shutdown()
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

    async def _async_final_write(self, _event: Event) -> None:
        await self.activity.async_flush()
        await self.periodic.async_flush()

    # ---- interfaces coming and going ---------------------------------------------------
    @callback
    def hub_added(self, hub: CanHub) -> None:
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
        return {
            "interfaces": [hub.info() for hub in self.hubs.values()],
            "offline": [src.info() for src in self.offline.values()],
            "periodic": self.periodic.snapshot(),
            "activity": self.activity.recent(200),
            "now": time.time(),
        }

    # ---- monitor viewers ---------------------------------------------------------------
    @callback
    def subscribe_monitor(self, source_id: str, send: Callable[[dict[str, Any]], None]) -> tuple[Viewer, CALLBACK_TYPE]:
        src = self.source(source_id)
        viewer = Viewer(send)
        detach = src.monitor.attach(viewer)
        send({"seq": 0, "t": round(time.time(), 6), "full": True, "rows": src.monitor.full(),
              "overflow": src.monitor.overflow, "frames": src.monitor.frames, "trace_end": src.trace.seq,
              "trace_first": src.trace.first})
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
        if not name.endswith((".log", ".txt")):
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
        by_iface, _lines, skipped = await self.hass.async_add_executor_job(read_log, path, TRACE_CAPACITY + 1)
        opened = []
        for ifname, frames in by_iface.items():
            truncated = len(frames) > TRACE_CAPACITY
            frames = frames[-TRACE_CAPACITY:]
            source_id = f"file:{name}:{ifname}"
            src = await self.hass.async_add_executor_job(OfflineSource, source_id, name, ifname, frames, truncated)
            self.offline[source_id] = src
            opened.append(src)
        if not opened:
            raise HomeAssistantError(f"{name}: no CAN frames found ({skipped} lines not understood); "
                                     "use candump's log format, e.g. (1760600000.123456) can0 123#DEADBEEF")
        self._send("offline", {"offline": [s.info() for s in self.offline.values()]})
        return opened

    @callback
    def close_offline(self, source_id: str) -> None:
        self.offline.pop(source_id, None)
        self._viewers = [(src, v) for src, v in self._viewers if getattr(src, "id", None) != source_id]
        self._send("offline", {"offline": [s.info() for s in self.offline.values()]})
