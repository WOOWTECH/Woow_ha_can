"""Requests: frames some equipment must be asked for (OBD-II, CANopen SDO, Daly BMS), sent politely.

A device's requests go out only while the device is active (off by default) and its interface can send
(not listen-only, open, not bus-off). Per device one request waits for its reply at a time, as OBD-II and
CANopen SDO expect; a device sends at most `max_rate` requests a second and an interface at most
INTERFACE_RATE. A request whose reply stays away MISS_LIMIT times in a row backs off: its period doubles
with every further miss, up to MAX_PERIOD (an engine that was switched off, a PID the car does not have);
the first reply brings it back to its own period.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import time
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError

from .can_port import CanFrame

if TYPE_CHECKING:
    from .devices import Device, DeviceManager, Request

_LOGGER = logging.getLogger(__name__)
TICK = 0.05  # s
INTERFACE_RATE = 50.0  # requests a second per interface, all devices together
MISS_LIMIT = 3
MAX_PERIOD = 60.0  # s, the longest a backed-off request waits
STATUS_PUSH = 2.0  # s between request statistics pushed to the panel
PAUSE = 1.0  # s to wait when the interface cannot send


class Bucket:
    """At most `rate` takes a second, with a burst of one second's worth."""

    def __init__(self, rate: float) -> None:
        self.rate = rate
        self.tokens = min(rate, 1.0)
        self.at = time.monotonic()

    def take(self, now: float) -> bool:
        self.tokens = min(max(self.rate, 1.0), self.tokens + (now - self.at) * self.rate)
        self.at = now
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False


@dataclass
class RequestState:
    device_id: str
    request: Request
    next_due: float
    misses: int = 0
    backoff: int = 0  # doublings of the period
    sent: int = 0
    replies: int = 0
    pending_since: float | None = None
    last_reply: float | None = None
    error: str | None = None
    paused: bool = False

    @property
    def period(self) -> float:
        own = self.request.period_ms / 1000
        return min(own * (2 ** self.backoff), max(MAX_PERIOD, own))

    def status(self, now: float) -> dict[str, Any]:
        if self.paused:
            state = "paused"
        elif self.error:
            state = "error"
        elif self.misses >= MISS_LIMIT:
            state = "no_reply"
        elif self.request.reply and self.last_reply is None:
            state = "waiting"
        else:
            state = "ok"
        return {"name": self.request.name, "period_ms": self.request.period_ms,
                "effective_ms": round(self.period * 1000), "sent": self.sent, "replies": self.replies,
                "misses": self.misses, "state": state, "error": self.error,
                "last_reply_s_ago": None if self.last_reply is None else round(now - self.last_reply, 1)}


class RequestScheduler:
    def __init__(self, hass: HomeAssistant, manager: DeviceManager) -> None:
        self.hass = hass
        self.manager = manager
        self.states: dict[tuple[str, str], RequestState] = {}
        self.by_device: dict[str, list[RequestState]] = {}
        self._device_buckets: dict[str, Bucket] = {}
        self._interface_buckets: dict[str, Bucket] = {}
        self._handle: Any = None
        self._pushed = 0.0
        self.running = False

    # ---- life cycle ----------------------------------------------------------------------
    @callback
    def start(self) -> None:
        self.running = True
        self.refresh()

    @callback
    def stop(self) -> None:
        self.running = False
        if self._handle is not None:
            self._handle.cancel()
            self._handle = None

    @callback
    def refresh(self) -> None:
        """Follow the devices: active ones get their requests (counters kept), others none."""
        now = time.monotonic()
        states: dict[tuple[str, str], RequestState] = {}
        for device in self.manager.devices.values():
            if not device.active or not device.requests:
                continue
            bucket = self._device_buckets.get(device.id)
            if bucket is None or bucket.rate != device.max_rate:
                self._device_buckets[device.id] = Bucket(device.max_rate)
            for i, req in enumerate(device.requests):
                key = (device.id, req.name)
                old = self.states.get(key)
                if old is not None and old.request == req:
                    states[key] = old
                else:  # spread the first sends a little
                    states[key] = RequestState(device.id, req, now + 0.2 + i * 0.05)
        self.states = states
        self.by_device = {}
        for st in states.values():
            self.by_device.setdefault(st.device_id, []).append(st)
        for device_id in [d for d in self._device_buckets if d not in self.by_device]:
            del self._device_buckets[device_id]
        if states and self.running:
            self._schedule()
        elif self._handle is not None:
            self._handle.cancel()
            self._handle = None

    def _schedule(self) -> None:
        if self._handle is None:
            self._handle = self.hass.loop.call_later(TICK, self._tick)

    # ---- sending -------------------------------------------------------------------------
    @callback
    def _tick(self) -> None:
        self._handle = None
        if not self.states or not self.running:
            return
        now = time.monotonic()
        for st in self.states.values():
            if st.pending_since is not None and now - st.pending_since > st.request.timeout_ms / 1000:
                st.pending_since = None
                st.misses += 1
                if st.misses >= MISS_LIMIT:
                    st.backoff = min(st.backoff + 1, 16)
                    st.next_due = now + st.period
        busy = {st.device_id for st in self.states.values() if st.pending_since is not None}
        for st in sorted(self.states.values(), key=lambda s: s.next_due):
            if st.next_due > now:
                break
            if st.device_id in busy:
                continue
            device = self.manager.devices.get(st.device_id)
            if device is None:
                continue
            reason = self.manager.cannot_send(device.interface)
            if reason:
                st.paused, st.error = True, reason
                st.next_due = now + PAUSE
                continue
            st.paused = False
            iface = self._interface_buckets.setdefault(device.interface, Bucket(INTERFACE_RATE))
            if not self._device_buckets[device.id].take(now) or not iface.take(now):
                continue  # stays due: goes out when the budget allows
            self._send(device, st, now)
            if st.request.reply:
                busy.add(st.device_id)
        if now - self._pushed >= STATUS_PUSH:
            self._pushed = now
            self.manager.push_requests()
        self._schedule()

    @callback
    def _send(self, device: Device, st: RequestState, now: float) -> None:
        req = st.request
        st.sent += 1
        st.next_due = now + st.period
        st.pending_since = now if req.reply else None
        frame = CanFrame.from_raw(req.raw_id, req.data, 0)

        async def run() -> None:
            try:
                await self.manager.async_send(device.interface, frame)
                st.error = None
            except HomeAssistantError as err:
                st.error = str(err)
                st.pending_since = None
                _LOGGER.debug("Request %s of %s failed: %s", req.name, device.name, err)

        self.hass.async_create_task(run(), f"woow_can request {device.name} {req.name}", eager_start=True)

    @callback
    def on_message(self, device_id: str, message: str) -> None:
        """A message of a device arrived: it answers that device's pending request for it."""
        for st in self.by_device.get(device_id, ()):
            if st.request.reply == message and st.pending_since is not None:
                st.pending_since = None
                st.replies += 1
                st.last_reply = time.monotonic()
                st.misses = 0
                if st.backoff:
                    st.backoff = 0
                    st.next_due = min(st.next_due, st.last_reply + st.period)
                st.error = None
                return

    def status(self, device_id: str) -> list[dict[str, Any]]:
        now = time.monotonic()
        return [st.status(now) for st in self.by_device.get(device_id, ())]
