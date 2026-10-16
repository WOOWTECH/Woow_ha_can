"""Runtime object tying one CAN interface to Home Assistant: state, bus events, listeners."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
import errno
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.event import async_call_later, async_track_time_interval
from homeassistant.util import dt as dt_util, slugify

from .can_port import CanConfig, CanFrame, CanPort, parse_filters
from .const import (
    CAN_DEFAULTS,
    CONF_BITRATE,
    CONF_DBITRATE,
    CONF_FD,
    CONF_FILTERS,
    CONF_LISTEN_ONLY,
    CONF_MAX_RATE,
    CONF_PORT,
    CONF_RESTART_MS,
    DOMAIN,
    EVENT_FRAME,
)

_LOGGER = logging.getLogger(__name__)
RETRY = 10  # seconds between reopen attempts after the interface is lost


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
            max_rate=int(opts[CONF_MAX_RATE]),
        )
        self.io = CanPort(hass.loop, self.cfg, self._on_frame, self._on_tx, self._on_error, self._on_lost)
        self.last_rx: tuple[CanFrame, datetime] | None = None
        self.last_tx: tuple[CanFrame, datetime] | None = None
        self.status: dict = {}
        self._listeners: list[Callable[[str], None]] = []
        self._unsubs: list[CALLBACK_TYPE] = []
        self._retry: CALLBACK_TYPE | None = None
        self._refresh: CALLBACK_TYPE | None = None

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
    def model(self) -> str:
        return f"{self.port} ({self.entry.data.get('driver') or 'unknown'})"

    @callback
    def add_listener(self, cb: Callable[[str], None]) -> CALLBACK_TYPE:
        self._listeners.append(cb)
        return lambda: self._listeners.remove(cb)

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
        self._unsubs.append(async_track_time_interval(self.hass, self._async_poll, timedelta(seconds=10)))
        await self._async_poll()

    async def async_stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        for handle in (self._retry, self._refresh):
            if handle:
                handle()
        self._retry = self._refresh = None
        await self.io.close()

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
    async def _async_poll(self, _now: datetime | None = None) -> None:
        try:
            self.status = await self.hass.async_add_executor_job(self.io.status)
        except OSError as err:
            _LOGGER.debug("%s: status read failed: %s", self.name, err)
            return
        self.status["dropped_by_rate_limit"] = self.io.dropped
        self.notify("stats")

    @callback
    def _on_error(self, error_class: int) -> None:
        # Controller warning / passive / bus-off / restart: refresh the state shortly.
        if self._refresh is None:
            self._refresh = async_call_later(self.hass, 0.5, self._async_error_refresh)

    async def _async_error_refresh(self, _now: datetime) -> None:
        self._refresh = None
        await self._async_poll()

    # ---- frames -------------------------------------------------------------------------
    @callback
    def _on_frame(self, frame: CanFrame, over_limit: bool = False) -> None:
        if over_limit:  # beyond max_events_per_sec: counted only
            return
        self.last_rx = (frame, dt_util.utcnow())
        self.hass.bus.async_fire(EVENT_FRAME, {
            "entry_id": self.entry.entry_id, "name": self.name, "interface": self.port, **frame.as_dict(),
        })
        self.notify("rx")

    @callback
    def _on_tx(self, frame: CanFrame) -> None:
        self.last_tx = (frame, dt_util.utcnow())
        self.notify("tx")

    async def async_send(self, frame: CanFrame, wait: float = 0,
                         match: Callable[[CanFrame], bool] | None = None) -> CanFrame | None:
        """Send a frame; with wait > 0 return the first matching reply (None on timeout)."""
        if not self.io.is_open:
            raise self._error("not_available")
        try:
            if wait > 0:
                return await self.io.request(frame, match or (lambda _f: True), wait)
            await self.io.send(frame)
        except ValueError as err:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="bad_frame",
                                         translation_placeholders={"error": str(err)}) from err
        except OSError as err:
            if err.errno == errno.ENOBUFS:
                raise self._error("tx_queue_full") from err
            raise self._error("send_failed", error=str(err)) from err
        return None
