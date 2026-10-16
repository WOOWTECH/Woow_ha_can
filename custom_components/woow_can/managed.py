"""Entities of devices: one per adopted signal (sensor or binary_sensor).

Values arrive from DeviceManager whenever a message's data changes. An entity writes its state at most
once per `min_interval` (1 s for numbers, 0.2 s for on/off and value lists), skips changes smaller than
its `tolerance` (half a resolution step unless set), and turns unavailable when its message has been
silent longer than the message's timeout (max(3 cycles, 5 s)); `on_timeout: "off"` makes a binary
sensor go off instead (a node's "online" state). Settings live in the signal's `entity` block.
"""

from __future__ import annotations

import math
import re
import time
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import EntityCategory
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_call_later
from homeassistant.util import slugify

from .const import DOMAIN
from .devices import Device, DeviceManager
from .signals import Message, Signal, decimals

# unit -> (device class, unit Home Assistant expects)
UNITS: dict[str, tuple[str | None, str]] = {
    "V": ("voltage", "V"), "mV": ("voltage", "mV"), "kV": ("voltage", "kV"),
    "A": ("current", "A"), "mA": ("current", "mA"),
    "W": ("power", "W"), "kW": ("power", "kW"),
    "Wh": ("energy", "Wh"), "kWh": ("energy", "kWh"), "MWh": ("energy", "MWh"),
    "degC": ("temperature", "°C"), "°C": ("temperature", "°C"), "deg C": ("temperature", "°C"),
    "degF": ("temperature", "°F"), "°F": ("temperature", "°F"), "K": ("temperature", "K"),
    "Hz": ("frequency", "Hz"), "kHz": ("frequency", "kHz"),
    "Pa": ("pressure", "Pa"), "kPa": ("pressure", "kPa"), "hPa": ("pressure", "hPa"), "bar": ("pressure", "bar"),
    "mbar": ("pressure", "mbar"), "psi": ("pressure", "psi"),
    "km/h": ("speed", "km/h"), "kph": ("speed", "km/h"), "m/s": ("speed", "m/s"), "mph": ("speed", "mph"),
    "km": ("distance", "km"), "m": ("distance", "m"), "mi": ("distance", "mi"),
    "h": ("duration", "h"), "min": ("duration", "min"), "s": ("duration", "s"), "ms": ("duration", "ms"),
    "L": ("volume", "L"), "l": ("volume", "L"),
}


def platform_of(sig: Signal) -> str:
    entity = sig.entity or {}
    if entity.get("platform") in ("sensor", "binary_sensor"):
        return entity["platform"]
    if sig.decoder_field is None and sig.length == 1 and not sig.values and sig.kind == "int" and not sig.derive:
        return "binary_sensor"
    return "sensor"


def snake(name: str) -> str:
    """EngineSpeed -> engine_speed, battery.soc -> battery_soc."""
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name.replace(".", "_"))
    return slugify(text) or "signal"


def label(value: Any, language: str) -> str | None:
    if isinstance(value, dict):
        if language.lower().startswith("zh"):
            return value.get("zh-Hant") or value.get("zh") or value.get("en")
        return value.get("en") or next(iter(value.values()), None)
    return value or None


def build(manager: DeviceManager, device: Device, domain: str) -> list[Entity]:
    """Fresh entity objects of one platform for one device."""
    out: list[Entity] = []
    for msg, sig in device.adopted():
        if platform_of(sig) != domain:
            continue
        out.append((SignalBinarySensor if domain == "binary_sensor" else SignalSensor)(manager, device, msg, sig))
    return out


class SignalEntity(Entity):
    """One adopted signal of a device."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, manager: DeviceManager, device: Device, msg: Message, sig: Signal, domain: str) -> None:
        self.manager = manager
        self.device_id = device.id
        self.message = msg
        self.signal = sig
        cfg = sig.entity or {}
        self.cfg = cfg
        language = manager.hass.config.language or "en"
        self._attr_unique_id = f"{device.id}_{msg.name}_{sig.name}"
        self._attr_name = label(cfg.get("name"), language) or sig.name
        self.entity_id = f"{domain}.{slugify(device.name) or 'woow_can'}_{snake(cfg.get('key') or sig.name)}"
        self._attr_entity_registry_enabled_default = bool(cfg.get("enabled", True))
        if cfg.get("icon"):
            self._attr_icon = cfg["icon"]
        if cfg.get("category") == "diagnostic":
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"device_{device.id}")},
            name=device.name,
            manufacturer=device.manufacturer or "WOOWTECH",
            model=device.model or None,
        )
        interface = dr.async_get(manager.hass).async_get_device_by_identifier((DOMAIN, device.interface),
                                                                              device.interface)
        if interface is not None:  # shown under the interface it is on
            self._attr_device_info["via_device_id"] = interface.id
        numeric = platform_of(sig) == "sensor" and not sig.values and sig.kind != "ascii"
        default_interval = 1.0 if numeric else 0.2
        self._min_interval = float(cfg.get("min_interval", default_interval))
        self._tolerance = float(cfg.get("tolerance", abs(sig.factor) / 2 if numeric and sig.factor else 0))
        self._timeout = cfg.get("timeout", msg.timeout)
        if self._timeout is not None:
            self._timeout = float(self._timeout)
        self._value: Any = None
        self._pending: Any = None
        self._written_at: float | None = None
        self._seen = False
        self._stale = False
        self._timer: Any = None

    # ---- life cycle ----------------------------------------------------------------------
    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.manager.entity_added(self)
        known = self.manager.values.get(self.device_id, {}).get(f"{self.message.name}.{self.signal.name}", ...)
        if known is not ...:  # re-created after an edit: show what is known right away
            self._seen = self.manager.is_fresh(self.device_id, self.message) is not False
            self._value = self._pending = known
            self._written_at = time.monotonic()

    async def async_will_remove_from_hass(self) -> None:
        self.manager.entity_removed(self)
        if self._timer is not None:
            self._timer()
            self._timer = None
        await super().async_will_remove_from_hass()

    # ---- values ------------------------------------------------------------------------
    @property
    def available_now(self) -> bool:
        return self._seen and not self._stale

    @property
    def available(self) -> bool:
        if self._timeout is None:
            return True
        return self._seen and not self._stale

    def _same(self, a: Any, b: Any) -> bool:
        if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
            return abs(a - b) < self._tolerance if self._tolerance else a == b
        return a == b

    @callback
    def on_value(self, value: Any, first: bool) -> None:
        now = time.monotonic()
        came_back = self._stale or not self._seen
        self._seen = True
        self._stale = False
        self._pending = value
        if came_back or first or self._written_at is None:
            self._write(now)
            return
        if self._same(value, self._value):
            return
        wait = self._written_at + self._min_interval - now
        if wait <= 0:
            self._write(now)
        elif self._timer is None:
            self._timer = async_call_later(self.hass, wait, self._flush)

    @callback
    def _flush(self, _now: Any) -> None:
        self._timer = None
        if not self._same(self._pending, self._value):
            self._write(time.monotonic())

    @callback
    def _write(self, now: float) -> None:
        if self._timer is not None:
            self._timer()
            self._timer = None
        self._value = self._pending
        self._written_at = now
        if self.hass is not None:
            self.async_write_ha_state()

    @callback
    def check_timeout(self, now: float) -> None:
        if self._timeout is None or not self._seen or self._stale:
            return
        seen = self.manager.last_seen.get((self.device_id, self.message.name))
        if seen is not None and now - seen > self._timeout:
            self._stale = True
            if self.hass is not None:
                self.async_write_ha_state()


class SignalSensor(SignalEntity, SensorEntity):
    def __init__(self, manager: DeviceManager, device: Device, msg: Message, sig: Signal) -> None:
        super().__init__(manager, device, msg, sig, "sensor")
        cfg = self.cfg
        unit = cfg.get("unit", sig.unit)
        device_class, ha_unit = UNITS.get(unit, (None, unit)) if unit else (None, None)
        self._format = cfg.get("format")
        if sig.values or cfg.get("options"):
            self._attr_device_class = SensorDeviceClass.ENUM
            self._attr_options = list(cfg.get("options") or dict.fromkeys(sig.values.values()))
            return
        if sig.kind == "ascii" or self._format or sig.decoder_field in ("dtc_text",):
            return
        if cfg.get("device_class"):
            device_class = cfg["device_class"]
        if device_class:
            try:
                self._attr_device_class = SensorDeviceClass(device_class)
            except ValueError:
                pass
        self._attr_native_unit_of_measurement = ha_unit or None
        state_class = cfg.get("state_class", "total_increasing" if device_class == "energy" else "measurement")
        if state_class and state_class != "none":
            self._attr_state_class = SensorStateClass(state_class)
        precision = cfg.get("precision")
        if precision is None and not sig.decoder_field:
            precision = decimals(sig.factor) if not sig.derive else 0
        if precision is not None:
            self._attr_suggested_display_precision = int(precision)

    @property
    def native_value(self) -> Any:
        value = self._value
        if value is None:
            return None
        if self._format == "hex" and isinstance(value, (int, float)):
            return f"{int(value):0{max(1, math.ceil(self.signal.length / 4))}X}"
        if getattr(self, "_attr_device_class", None) == SensorDeviceClass.ENUM:
            return str(value) if str(value) in self._attr_options else None
        if isinstance(value, bool):
            return int(value)
        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        names = self.cfg.get("attributes")
        if not names:
            return None
        extra = self.manager.extra.get(self.device_id, {})
        return {name: extra.get(f"{self.message.name}.{name}") for name in names}


class SignalBinarySensor(SignalEntity, BinarySensorEntity):
    def __init__(self, manager: DeviceManager, device: Device, msg: Message, sig: Signal) -> None:
        super().__init__(manager, device, msg, sig, "binary_sensor")
        cfg = self.cfg
        if cfg.get("device_class"):
            try:
                self._attr_device_class = BinarySensorDeviceClass(cfg["device_class"])
            except ValueError:
                pass
        self._on = [v for v in cfg.get("on", [1])]
        self._off = [v for v in cfg.get("off", [0])]
        self._off_on_timeout = cfg.get("on_timeout") == "off"

    @property
    def available(self) -> bool:
        if self._off_on_timeout:
            return True
        return super().available

    @property
    def is_on(self) -> bool | None:
        if self._off_on_timeout and (self._stale or not self._seen):
            return False
        value = self._value
        if isinstance(value, bool):
            return value
        if value in self._on:
            return True
        if value in self._off:
            return False
        if self.cfg.get("nonzero") and isinstance(value, (int, float)):
            return value != 0
        return None
