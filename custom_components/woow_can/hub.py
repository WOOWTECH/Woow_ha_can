"""Runtime object tying one CAN interface to Home Assistant.

Every received frame goes to the per-ID monitor and the trace buffer (both cheap and in memory),
and to a recording when one runs. Only frames whose ID is in the interface's event filter become
`woow_can_frame` events, at most max_events_per_sec of them; the last-frame sensors update at most
once a second. That keeps a busy bus out of Home Assistant's database.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
import errno
import logging
import math
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.event import async_call_later
from homeassistant.util import dt as dt_util, slugify

from .can_port import (
    F_OWN,
    CanConfig,
    CanFrame,
    CanPort,
    IdMatcher,
    decode_error,
    frame_text,
    parse_filters,
)
from .capture import Recording, TraceBuffer
from .const import (
    CAN_DEFAULTS,
    CONF_BITRATE,
    CONF_DBITRATE,
    CONF_EVENT_FILTER,
    CONF_FD,
    CONF_FILTERS,
    CONF_LISTEN_ONLY,
    CONF_MAX_RATE,
    CONF_PORT,
    CONF_RESTART_MS,
    DOMAIN,
    ENTITY_MIN_INTERVAL,
    EVENT_FRAME,
    STATUS_FAST,
    STATUS_SLOW,
    TRACE_CAPACITY,
)
from .monitor import Monitor

_LOGGER = logging.getLogger(__name__)
RETRY = 10  # seconds between reopen attempts after the interface is lost
STATUS_KEYS = (
    "up", "kind", "virtual", "state", "bitrate", "sample_point", "dbitrate", "fd", "listen_only", "loopback",
    "berr_reporting", "berr_supported", "fd_supported", "tx_error_counter", "rx_error_counter", "restart_ms",
    "clock", "bus_error", "error_warning", "error_passive", "bus_off", "arbitration_lost", "restarts",
    "rx_packets", "tx_packets", "rx_bytes", "tx_bytes", "rx_errors", "tx_errors", "rx_dropped", "tx_dropped",
    "rx_over_errors",
)


class EventGate:
    """Which received frames become woow_can_frame events, and at most how many per second."""

    def __init__(self, text: str, max_rate: int) -> None:
        self.matcher = IdMatcher(text)
        self.max_rate = max_rate
        self.dropped = 0  # matching frames beyond the rate
        self._window = 0.0
        self._count = 0

    def wants(self, raw: int) -> bool:
        return not self.matcher.empty and self.matcher(raw)

    def allow(self) -> bool:
        now = time.monotonic()
        if now - self._window >= 1.0:
            self._window, self._count = now, 0
        self._count += 1
        if self._count > self.max_rate:
            self.dropped += 1
            return False
        return True


class BusLoad:
    """Bus load from the interface counters, as canbusload estimates it (worst-case bit stuffing).

    A classic frame with n data bytes takes at most 55 + 10n bits (11-bit ID) or 80 + 10n (29-bit);
    with bit rate switching the data phase runs at the data bitrate. The estimate can exceed 100 %.
    """

    WINDOWS = (60.0, 300.0, 900.0)

    def __init__(self) -> None:
        self.now: float | None = None
        self.peak = 0.0
        self.avg: list[float | None] = [None, None, None]
        self.rx_fps: float | None = None
        self.tx_fps: float | None = None
        self._prev: tuple[float, dict[str, int]] | None = None

    def update(self, t: float, counters: dict[str, int], mix: tuple[int, int, int], bitrate: int,
               dbitrate: int) -> None:
        prev, self._prev = self._prev, (t, counters)
        if prev is None:
            return
        dt = t - prev[0]
        if dt <= 0:
            return
        delta = {k: max(0, counters[k] - prev[1].get(k, counters[k])) for k in counters}
        self.rx_fps = delta["rx_packets"] / dt
        self.tx_fps = delta["tx_packets"] / dt
        if not bitrate:
            return
        packets = delta["rx_packets"] + delta["tx_packets"]
        data_bytes = delta["rx_bytes"] + delta["tx_bytes"]
        total, eff, brs = mix
        eff_share = eff / total if total else 0.0
        brs_share = brs / total if total and dbitrate else 0.0
        seconds = packets * (55 + 25 * eff_share) / bitrate + data_bytes * 10 * (
            (1 - brs_share) / bitrate + (brs_share / dbitrate if dbitrate else 0.0))
        load = 100 * seconds / dt
        self.now = load
        self.peak = max(self.peak, load)
        for i, window in enumerate(self.WINDOWS):
            avg = self.avg[i]
            self.avg[i] = load if avg is None else avg + (load - avg) * (1 - math.exp(-dt / window))

    def reset_peak(self) -> None:
        self.peak = self.now or 0.0

    def as_dict(self) -> dict[str, Any]:
        def r(v: float | None) -> float | None:
            return None if v is None else round(v, 2)

        return {"now": r(self.now), "peak": r(self.peak) if self.now is not None else None,
                "avg": [r(a) for a in self.avg], "rx_fps": r(self.rx_fps), "tx_fps": r(self.tx_fps)}


class ErrorLog:
    """Error frames since the interface came up: counts per kind and the last one."""

    def __init__(self) -> None:
        self.counts: dict[str, int] = {}
        self.total = 0
        self.last: dict[str, Any] | None = None

    def add(self, ts: float, raw: int, data: bytes, flags: int) -> list[str]:
        codes = decode_error(raw, data)
        self.total += 1
        for code in codes:
            self.counts[code] = self.counts.get(code, 0) + 1
        self.last = {"t": round(ts, 6), "codes": codes, "frame": frame_text(raw, data, flags),
                     "tx_error_counter": data[6] if len(data) > 7 else None,
                     "rx_error_counter": data[7] if len(data) > 7 else None}
        return codes

    def as_dict(self) -> dict[str, Any]:
        return {"total": self.total, "counts": dict(self.counts), "last": self.last}


class CanHub:
    """A SocketCAN interface."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.available = False
        opts = {**CAN_DEFAULTS, **entry.options}
        self.cfg = CanConfig(
            ifname=self.port,
            bitrate=int(opts[CONF_BITRATE]),
            fd=bool(opts[CONF_FD]),
            dbitrate=int(opts[CONF_DBITRATE]),
            listen_only=bool(opts[CONF_LISTEN_ONLY]),
            restart_ms=int(opts[CONF_RESTART_MS]),
            filters=parse_filters(opts[CONF_FILTERS]),
        )
        self.filters_text = opts[CONF_FILTERS]
        self.options = dict(entry.options)  # to tell a live change (event filter) from one that needs a restart
        self.events = EventGate(opts[CONF_EVENT_FILTER], int(opts[CONF_MAX_RATE]))
        self.io = CanPort(hass.loop, self.cfg, self._on_frame, self._on_error, self._on_lost)
        self.monitor = Monitor()
        self.trace = TraceBuffer(TRACE_CAPACITY)
        self.load = BusLoad()
        self.errors = ErrorLog()
        self.recording: Recording | None = None
        self.started = time.time()
        self.last_rx: tuple[float, int, bytes, int] | None = None  # time, raw id, data, flags
        self.last_tx: tuple[CanFrame, datetime] | None = None
        self.last_event: dict[str, Any] | None = None
        self.sent = 0
        self.status: dict[str, Any] = {}
        self.fast = 0  # viewers that want the status every second
        self._listeners: list[Callable[[str], None]] = []
        self._status_listeners: list[Callable[[CanHub], None]] = []
        self._poll: CALLBACK_TYPE | None = None
        self._retry: CALLBACK_TYPE | None = None
        self._refresh: CALLBACK_TYPE | None = None
        self._throttle: dict[str, tuple[float, CALLBACK_TYPE | None]] = {}
        self._stats_notified = 0.0
        self._stopped = False
        self._polling = False  # a status read is in flight; it schedules the next one itself

    @property
    def name(self) -> str:
        return self.entry.title

    @property
    def port(self) -> str:
        return self.entry.data[CONF_PORT]

    @property
    def slug(self) -> str:
        return slugify(self.entry.title) or slugify(self.port)

    @property
    def driver(self) -> str:
        return self.entry.data.get("driver") or ("vcan" if self.io.virtual else "")

    @property
    def model(self) -> str:
        return f"{self.port} ({self.driver or 'unknown'})"

    @callback
    def add_listener(self, cb: Callable[[str], None]) -> CALLBACK_TYPE:
        self._listeners.append(cb)
        return lambda: self._listeners.remove(cb)

    @callback
    def add_status_listener(self, cb: Callable[[CanHub], None]) -> CALLBACK_TYPE:
        """Called after every status read (every second while the panel shows the health cards)."""
        self._status_listeners.append(cb)
        return lambda: self._status_listeners.remove(cb)

    @callback
    def notify(self, what: str) -> None:
        for cb in list(self._listeners):
            cb(what)

    def _error(self, key: str, **placeholders: str) -> HomeAssistantError:
        return HomeAssistantError(translation_domain=DOMAIN, translation_key=key,
                                  translation_placeholders={"name": self.name, **placeholders})

    # ---- lifecycle ----------------------------------------------------------------------
    async def async_start(self) -> None:
        await self.io.open()
        self.available = True
        await self._async_poll()

    async def async_stop(self) -> None:
        self._stopped = True
        for handle in (self._poll, self._retry, self._refresh):
            if handle:
                handle()
        for _, handle in self._throttle.values():
            if handle:
                handle()
        self._throttle.clear()
        self._poll = self._retry = self._refresh = None
        await self.io.close()

    @callback
    def apply_live_options(self, event_filter: str, max_rate: int) -> None:
        """Options that apply without reopening the interface."""
        self.events = EventGate(event_filter, max_rate)

    @callback
    def _on_lost(self, err: Exception) -> None:
        _LOGGER.warning("%s (%s) stopped working: %s; retrying every %ss", self.name, self.port, err, RETRY)
        self.available = False
        self.notify("availability")
        self._retry = async_call_later(self.hass, RETRY, self._async_retry)

    async def _async_retry(self, _now: datetime) -> None:
        self._retry = None
        try:
            await self.io.close()
            await self.io.open()
        except (OSError, ValueError) as err:
            _LOGGER.debug("%s: reopen failed: %s", self.name, err)
            self._retry = async_call_later(self.hass, RETRY, self._async_retry)
            return
        _LOGGER.info("%s (%s) is back", self.name, self.port)
        self.available = True
        self.notify("availability")

    # ---- status -------------------------------------------------------------------------
    @callback
    def set_fast(self, on: bool) -> None:
        """The panel shows live health: read the status every second instead of every ten."""
        self.fast = max(0, self.fast + (1 if on else -1))
        if on and self.fast == 1 and not self._stopped and not self._polling:
            if self._poll:
                self._poll()
            self._poll = async_call_later(self.hass, 0, self._async_poll)

    async def _async_poll(self, _now: datetime | None = None) -> None:
        self._poll = None
        self._polling = True
        try:
            status = await self.hass.async_add_executor_job(self.io.status)
        except OSError as err:
            _LOGGER.debug("%s: status read failed: %s", self.name, err)
        else:
            self._apply_status(status)
        finally:
            self._polling = False
        if not self._stopped:
            self._poll = async_call_later(self.hass, STATUS_FAST if self.fast else STATUS_SLOW, self._async_poll)

    @callback
    def _apply_status(self, status: dict[str, Any]) -> None:
        t = time.monotonic()
        counters = {k: status.get(k, 0) for k in ("rx_packets", "tx_packets", "rx_bytes", "tx_bytes")}
        virtual = bool(status.get("virtual"))
        self.load.update(t, counters, self.monitor.take_mix(), 0 if virtual else self.cfg.bitrate,
                         self.cfg.dbitrate if self.cfg.fd else 0)
        status = {k: status[k] for k in STATUS_KEYS if k in status}
        status["socket_drops"] = self.io.socket_drops
        status["events_dropped"] = self.events.dropped
        status["dropped_by_rate_limit"] = self.events.dropped  # name used up to 0.1.x
        status["monitor_overflow"] = self.monitor.overflow
        changed = status.get("state") != self.status.get("state")
        self.status = status
        for cb in list(self._status_listeners):
            cb(self)
        if changed or t - self._stats_notified >= STATUS_SLOW - 0.5:
            self._stats_notified = t
            self.notify("stats")

    @callback
    def _schedule_refresh(self) -> None:
        if self._refresh is None and not self._stopped:
            self._refresh = async_call_later(self.hass, 0.5, self._async_error_refresh)

    async def _async_error_refresh(self, _now: datetime) -> None:
        self._refresh = None
        try:
            status = await self.hass.async_add_executor_job(self.io.status)
        except OSError:
            return
        self._apply_status(status)

    # ---- frames -------------------------------------------------------------------------
    @callback
    def _on_frame(self, ts: float, raw: int, data: bytes, flags: int) -> None:
        self.monitor.add(ts, raw, data, flags)
        self.trace.append(ts, raw, data, flags)
        if self.recording is not None:
            self.recording.add(ts, raw, data, flags)
        if flags & F_OWN:
            return
        self.last_rx = (ts, raw, data, flags)
        self._throttled("rx")
        if self.events.wants(raw) and self.events.allow():
            frame = CanFrame.from_raw(raw, data, flags)
            self.last_event = frame.as_dict()
            self.hass.bus.async_fire(EVENT_FRAME, {
                "entry_id": self.entry.entry_id, "name": self.name, "interface": self.port, **self.last_event,
            })
            self.notify("event")

    @callback
    def _on_error(self, ts: float, raw: int, data: bytes, flags: int) -> None:
        self.trace.append(ts, raw, data, flags)
        if self.recording is not None:
            self.recording.add(ts, raw, data, flags)
        codes = self.errors.add(ts, raw, data, flags)
        if any(c.startswith("controller") or c in ("bus_off", "restarted") for c in codes):
            self._schedule_refresh()

    @callback
    def _throttled(self, what: str) -> None:
        """notify(what) at most once per ENTITY_MIN_INTERVAL, the last change always delivered."""
        last, handle = self._throttle.get(what, (0.0, None))
        if handle is not None:
            return
        now = time.monotonic()
        wait = last + ENTITY_MIN_INTERVAL - now
        if wait <= 0:
            self._throttle[what] = (now, None)
            self.notify(what)
            return

        @callback
        def fire(_now: datetime) -> None:
            self._throttle[what] = (time.monotonic(), None)
            self.notify(what)

        self._throttle[what] = (last, async_call_later(self.hass, wait, fire))

    def last_rx_frame(self) -> tuple[CanFrame, datetime] | None:
        if self.last_rx is None:
            return None
        ts, raw, data, flags = self.last_rx
        return CanFrame.from_raw(raw, data, flags), dt_util.utc_from_timestamp(ts)

    # ---- sending ------------------------------------------------------------------------
    def check_can_send(self, frame: CanFrame | None = None) -> None:
        if not self.io.is_open:
            raise self._error("not_available")
        if self.cfg.listen_only and not self.io.virtual:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="listen_only",
                                         translation_placeholders={"name": self.name})
        if frame is not None and frame.fd and not (self.cfg.fd or self.io.virtual):
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="fd_off",
                                         translation_placeholders={"name": self.name})

    async def async_send(self, frame: CanFrame, wait: float = 0,
                         match: Callable[[CanFrame], bool] | None = None) -> CanFrame | None:
        """Send a frame; with wait > 0 return the first matching reply (None on timeout)."""
        self.check_can_send(frame)
        try:
            if wait > 0:
                reply = await self.io.request(frame, match or (lambda _f: True), wait)
            else:
                await self.io.send(frame)
                reply = None
        except ValueError as err:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="bad_frame",
                                         translation_placeholders={"error": str(err)}) from err
        except OSError as err:
            if err.errno == errno.ENOBUFS:
                raise self._error("tx_queue_full") from err
            raise self._error("send_failed", error=str(err)) from err
        self.sent += 1
        self.last_tx = (frame, dt_util.utcnow())
        self._throttled("tx")
        return reply

    # ---- views --------------------------------------------------------------------------
    def settings(self) -> dict[str, Any]:
        return {
            "bitrate": self.cfg.bitrate, "fd": self.cfg.fd, "dbitrate": self.cfg.dbitrate,
            "listen_only": self.cfg.listen_only, "restart_ms": self.cfg.restart_ms, "filters": self.filters_text,
            "event_filter": self.events.matcher.text, "max_events_per_sec": self.events.max_rate,
        }

    def info(self) -> dict[str, Any]:
        """The interface as the panel and the agents see it."""
        rec = self.recording
        return {
            "id": self.entry.entry_id,
            "name": self.name,
            "port": self.port,
            "driver": self.driver,
            "model": self.model,
            "available": self.available,
            "virtual": self.io.virtual,
            "can_send": self.io.is_open and (self.io.virtual or not self.cfg.listen_only),
            "settings": self.settings(),
            "status": self.status,
            "load": self.load.as_dict(),
            "errors": self.errors.as_dict(),
            "monitor": {"ids": len(self.monitor.stats), "frames": self.monitor.frames,
                        "overflow": self.monitor.overflow, "since": round(self.monitor.since, 3)},
            "trace": {"first": self.trace.first, "end": self.trace.seq, "capacity": self.trace.capacity},
            "recording": None if rec is None else {"name": rec.name, "frames": rec.frames, "bytes": rec.bytes,
                                                   "full": rec.full},
            "sent": self.sent,
            "started": round(self.started, 3),
        }
