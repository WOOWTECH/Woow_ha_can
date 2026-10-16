"""Event entity: fires for received frames whose ID is in the interface's event filter."""

from __future__ import annotations

from homeassistant.components.event import EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback

from .entity import WoowCanEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    async_add_entities([Received(entry.runtime_data)])


class Received(WoowCanEntity, EventEntity):
    """frame / id / id_hex / data / length / extended / fd / brs / rtr."""

    _attr_event_types = ["frame"]
    _attr_icon = "mdi:message-arrow-left-outline"
    _updates_on = ("event",)
    _unrecorded_attributes = frozenset({"frame", "id", "id_hex", "data", "length", "extended", "fd", "brs", "rtr"})

    def __init__(self, hub) -> None:
        super().__init__(hub, "rx_frame", "event")

    @callback
    def _refresh(self, what: str = "") -> None:
        if what != "event" or not self.hub.last_event:
            return
        self._trigger_event("frame", self.hub.last_event)
