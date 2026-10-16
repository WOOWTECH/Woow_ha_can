"""Sensors: last received / sent frame, bus state, counters, bus load."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.core import HomeAssistant, callback

from .can_port import CAN_STATES
from .const import CONF_KIND, KIND_HUB
from .entity import WoowCanEntity

_FRAME_ATTRS = frozenset({"frame", "id", "id_hex", "data", "length", "extended", "fd", "brs", "rtr"})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    if entry.data.get(CONF_KIND) == KIND_HUB:  # the admin entry: sensors of the devices
        entry.runtime_data.devices.register_platform("sensor", async_add_entities)
        return
    hub = entry.runtime_data
    async_add_entities([
        LastFrame(hub, "last_frame"), LastFrame(hub, "last_sent_frame"), BusState(hub),
        Counter(hub, "rx_frames", "rx_packets"), Counter(hub, "tx_frames", "tx_packets"),
        Counter(hub, "bus_errors", "rx_errors", "tx_errors"), BusLoadSensor(hub),
    ])


class _Sensor(WoowCanEntity, SensorEntity):
    def __init__(self, hub, key: str) -> None:
        super().__init__(hub, key, "sensor")


class LastFrame(_Sensor):
    """Last received (or sent) frame in candump notation, at most one update a second.

    Off by default for new interfaces: the panel's monitor shows the bus far better, and a busy
    bus would otherwise write a row a second to the history database.
    """

    _attr_icon = "mdi:swap-horizontal"
    _attr_entity_registry_enabled_default = False
    _unrecorded_attributes = _FRAME_ATTRS

    def __init__(self, hub, key: str) -> None:
        super().__init__(hub, key)
        self._updates_on = ("rx",) if key == "last_frame" else ("tx",)

    @callback
    def _refresh(self, what: str = "") -> None:
        last = self.hub.last_rx_frame() if self._attr_translation_key == "last_frame" else self.hub.last_tx
        if last:
            frame, _when = last
            self._attr_native_value = str(frame)
            self._attr_extra_state_attributes = frame.as_dict()


class BusState(_Sensor):
    """Controller state: error active / warning / passive / bus-off / stopped (virtual for vcan)."""

    _attr_icon = "mdi:lan"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [*CAN_STATES, "virtual"]
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
                "dropped_by_rate_limit": status.get("events_dropped", 0),
                "socket_drops": status.get("socket_drops", 0),
                "rx_dropped": status.get("rx_dropped", 0),
            }


class BusLoadSensor(_Sensor):
    """Estimated bus load (worst-case bit stuffing; can exceed 100 %). Off by default."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_suggested_display_precision = 1
    _attr_icon = "mdi:gauge"
    _attr_entity_registry_enabled_default = False
    _updates_on = ("stats",)

    def __init__(self, hub) -> None:
        super().__init__(hub, "bus_load")

    @callback
    def _refresh(self, what: str = "") -> None:
        avg = self.hub.load.avg[0]  # one-minute average: steadier than the last second
        self._attr_native_value = None if avg is None else round(avg, 2)
