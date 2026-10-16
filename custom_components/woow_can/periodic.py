"""Periodic sends: frames sent every N ms, like the transmit lists of PCAN-View or CanKing.

The list is kept; whether an item runs is not. After a restart every item is stopped, so a
reboot never starts transmitting on its own. An item stops by itself after `count` sends, or when
a send fails (interface gone, listen-only, transmit queue full: usually nobody acknowledges).
Timing runs on Home Assistant's event loop at a fixed rate; expect a few ms of jitter.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass, field
import time
from typing import Any
import uuid

from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.storage import Store

from .can_port import CanFrame
from .const import DOMAIN, LIVE_PUSH, PERIODIC_MAX_ITEMS, PERIODIC_MIN_MS

SAVE_DELAY = 5


class PeriodicError(ValueError):
    """An item that cannot be saved; `code` names the problem for the panel and agents."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass
class PeriodicItem:
    id: str
    entry_id: str  # the interface
    name: str
    frame: str  # cansend notation: 123#11223344, 18FF50E5#01, 456##1AABB
    period_ms: int
    count: int = 0  # sends before it stops by itself; 0 = until stopped


@dataclass
class Running:
    started: float
    next_at: float  # loop time of the next send
    sent: int = 0
    handle: Any = None


@dataclass
class ItemState:
    running: bool = False
    sent: int = 0
    started: float | None = None
    error: str | None = None
    stopped_by: str | None = None  # "count", "error", "user", "interface"
    extra: dict[str, Any] = field(default_factory=dict)


Sender = Callable[[str, CanFrame], Awaitable[None]]


class PeriodicManager:
    def __init__(self, hass: HomeAssistant, sender: Sender) -> None:
        self.hass = hass
        self._send = sender
        self._store: Store[dict[str, Any]] = Store(hass, 1, f"{DOMAIN}.periodic")
        self.items: dict[str, PeriodicItem] = {}
        self.states: dict[str, ItemState] = {}
        self._running: dict[str, Running] = {}
        self._listeners: list[Callable[[dict[str, Any]], None]] = []
        self._pending: set[str] = set()
        self._push_handle: Any = None
        self.on_stopped: Callable[[PeriodicItem, ItemState], None] | None = None

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        names = set(PeriodicItem.__dataclass_fields__)
        for raw in data.get("items", []):
            item = PeriodicItem(**{k: v for k, v in raw.items() if k in names})
            self.items[item.id] = item
            self.states[item.id] = ItemState()

    def _data(self) -> dict[str, Any]:
        return {"items": [asdict(i) for i in self.items.values()]}

    async def async_flush(self) -> None:
        await self._store.async_save(self._data())

    # ---- list -------------------------------------------------------------------------
    @staticmethod
    def validate(raw: dict[str, Any]) -> PeriodicItem:
        try:
            frame = CanFrame.parse(str(raw.get("frame", "")))
        except ValueError as err:
            raise PeriodicError("bad_frame", str(err)) from err
        try:
            period = int(raw.get("period_ms", 0))
            count = int(raw.get("count", 0) or 0)
        except (TypeError, ValueError) as err:
            raise PeriodicError("bad_number", str(err)) from err
        if period < PERIODIC_MIN_MS or period > 3_600_000:
            raise PeriodicError("bad_period", f"period must be {PERIODIC_MIN_MS} ms to 1 hour")
        if count < 0:
            raise PeriodicError("bad_count", "count must be 0 (until stopped) or more")
        if not raw.get("entry_id"):
            raise PeriodicError("no_interface", "choose the interface to send on")
        name = str(raw.get("name") or "").strip() or str(frame)
        return PeriodicItem(id=str(raw.get("id") or uuid.uuid4().hex[:12]), entry_id=str(raw["entry_id"]),
                            name=name[:80], frame=str(frame), period_ms=period, count=count)

    @callback
    def save(self, raw: dict[str, Any]) -> PeriodicItem:
        item = self.validate(raw)
        if item.id not in self.items and len(self.items) >= PERIODIC_MAX_ITEMS:
            raise PeriodicError("too_many", f"at most {PERIODIC_MAX_ITEMS} periodic sends")
        was_running = item.id in self._running
        if was_running:
            self.stop(item.id, "user")
        self.items[item.id] = item
        self.states.setdefault(item.id, ItemState())
        self._store.async_delay_save(self._data, SAVE_DELAY)
        if was_running:
            self.start(item.id)
        self._changed(item.id)
        return item

    @callback
    def delete(self, item_id: str) -> PeriodicItem | None:
        self.stop(item_id, "user")
        item = self.items.pop(item_id, None)
        self.states.pop(item_id, None)
        self._store.async_delay_save(self._data, SAVE_DELAY)
        self._changed(item_id)
        return item

    # ---- running ----------------------------------------------------------------------
    @callback
    def start(self, item_id: str) -> None:
        item = self.items[item_id]
        if item_id in self._running:
            return
        now = self.hass.loop.time()
        run = self._running[item_id] = Running(started=time.time(), next_at=now)
        self.states[item_id] = ItemState(running=True, started=run.started)
        run.handle = self.hass.loop.call_at(now, self._tick, item_id)
        self._changed(item.id)

    @callback
    def stop(self, item_id: str, reason: str = "user", error: str | None = None) -> None:
        run = self._running.pop(item_id, None)
        if run is None:
            return
        if run.handle is not None:
            run.handle.cancel()
        state = self.states.setdefault(item_id, ItemState())
        state.running = False
        state.sent = run.sent
        state.stopped_by = reason
        state.error = error
        self._changed(item_id)
        item = self.items.get(item_id)
        if item is not None and self.on_stopped is not None:
            self.on_stopped(item, state)

    @callback
    def stop_interface(self, entry_id: str) -> None:
        for item in list(self.items.values()):
            if item.entry_id == entry_id:
                self.stop(item.id, "interface")

    @callback
    def stop_all(self) -> None:
        for item_id in list(self._running):
            self.stop(item_id, "user")

    @callback
    def _tick(self, item_id: str) -> None:
        run = self._running.get(item_id)
        item = self.items.get(item_id)
        if run is None or item is None:
            return
        run.handle = None
        self.hass.async_create_task(self._async_send(item, run), eager_start=True)

    async def _async_send(self, item: PeriodicItem, run: Running) -> None:
        try:
            await self._send(item.entry_id, CanFrame.parse(item.frame))
        except (HomeAssistantError, ValueError, OSError) as err:
            if self._running.get(item.id) is run:
                self.stop(item.id, "error", str(err))
            return
        if self._running.get(item.id) is not run:
            return
        run.sent += 1
        self.states[item.id].sent = run.sent
        if item.count and run.sent >= item.count:
            self.stop(item.id, "count")
            return
        now = self.hass.loop.time()
        run.next_at += item.period_ms / 1000
        if run.next_at < now:  # fell behind (busy loop, slow send): skip ahead, do not burst
            run.next_at = now
        run.handle = self.hass.loop.call_at(run.next_at, self._tick, item.id)
        if run.sent == 1 or run.sent % 50 == 0:
            self._changed(item.id)

    # ---- views ------------------------------------------------------------------------
    def item_view(self, item_id: str) -> dict[str, Any]:
        item = self.items[item_id]
        state = self.states.get(item_id, ItemState())
        run = self._running.get(item_id)
        return {**asdict(item), "running": run is not None, "sent": run.sent if run else state.sent,
                "started": run.started if run else state.started, "error": state.error,
                "stopped_by": state.stopped_by}

    def snapshot(self) -> list[dict[str, Any]]:
        return [self.item_view(i) for i in self.items]

    def running_count(self, entry_id: str | None = None) -> int:
        return sum(1 for i in self._running if entry_id is None or self.items[i].entry_id == entry_id)

    @callback
    def subscribe(self, cb: Callable[[dict[str, Any]], None]) -> CALLBACK_TYPE:
        self._listeners.append(cb)
        return lambda: self._listeners.remove(cb)

    @callback
    def _changed(self, item_id: str) -> None:
        if not self._listeners:
            return
        self._pending.add(item_id)
        if self._push_handle is None:
            self._push_handle = self.hass.loop.call_later(LIVE_PUSH, self._push)

    @callback
    def _push(self) -> None:
        self._push_handle = None
        pending, self._pending = self._pending, set()
        items = [self.item_view(i) for i in pending if i in self.items]
        removed = [i for i in pending if i not in self.items]
        for cb in list(self._listeners):
            cb({"items": items, "removed": removed})

    @callback
    def shutdown(self) -> None:
        self.stop_all()
        if self._push_handle is not None:
            self._push_handle.cancel()
            self._push_handle = None
