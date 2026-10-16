"""Sensors: last received / sent frame, bus state, counters."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback

from .can_port import CAN_STATES
from .entity import WoowCanEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    hub = entry.runtime_data
    async_add_entities([
        LastFrame(hub, "last_frame"), LastFrame(hub, "last_sent_frame"), BusState(hub),
        Counter(hub, "rx_frames", "rx_packets"), Counter(hub, "tx_frames", "tx_packets"),
        Counter(hub, "bus_errors", "rx_errors", "tx_errors"),
    ])


class _Sensor(WoowCanEntity, SensorEntity):
    def __init__(self, hub, key: str) -> None:
        super().__init__(hub, key, "sensor")


class LastFrame(_Sensor):
    """Last received (or sent) frame in candump notation, details in the attributes."""

    _attr_icon = "mdi:swap-horizontal"

    def __init__(self, hub, key: str) -> None:
        super().__init__(hub, key)
        self._updates_on = ("rx",) if key == "last_frame" else ("tx",)

    @callback
    def _refresh(self, what: str = "") -> None:
        last = self.hub.last_rx if self._attr_translation_key == "last_frame" else self.hub.last_tx
        if last:
            frame, when = last
            self._attr_native_value = str(frame)
            self._attr_extra_state_attributes = {**frame.as_dict(), "time": when.isoformat()}


class BusState(_Sensor):
    """Controller state: error active / warning / passive / bus-off / stopped."""

    _attr_icon = "mdi:lan"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = CAN_STATES
    _updates_on = ("stats",)
    _ATTRS = ("bitrate", "sample_point", "dbitrate", "fd", "listen_only", "restart_ms",
              "tx_error_counter", "rx_error_counter", "clock")

    def __init__(self, hub) -> None:
        super().__init__(hub, "bus_state")

    @callback
    def _refresh(self, what: str = "") -> None:
        status = self.hub.status
        self._attr_native_value = status.get("state")
        self._attr_extra_state_attributes = {k: status[k] for k in self._ATTRS if k in status}


class Counter(_Sensor):
    """Interface statistics from the kernel (since the interface came up)."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _updates_on = ("stats",)

    def __init__(self, hub, key: str, *stat_keys: str) -> None:
        super().__init__(hub, key)
        self._stat_keys = stat_keys
        self._attr_icon = "mdi:alert-circle-outline" if key == "bus_errors" else "mdi:counter"

    @callback
    def _refresh(self, what: str = "") -> None:
        status = self.hub.status
        if all(k in status for k in self._stat_keys):
            self._attr_native_value = sum(status[k] for k in self._stat_keys)
        if self._attr_translation_key == "rx_frames":
            self._attr_extra_state_attributes = {
                "dropped_by_rate_limit": status.get("dropped_by_rate_limit", 0),
                "rx_dropped": status.get("rx_dropped", 0),
            }
