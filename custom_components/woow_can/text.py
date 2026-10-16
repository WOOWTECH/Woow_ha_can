"""Text entity: type a frame in cansend notation and it is sent."""

from __future__ import annotations

from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError

from .can_port import CanFrame
from .const import DOMAIN
from .entity import WoowCanEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    async_add_entities([SendFrame(entry.runtime_data)])


class SendFrame(WoowCanEntity, TextEntity):
    """CAN frame in cansend notation: 123#11223344, 18FF50E5#01, 456##1AABB (FD)."""

    _attr_native_max = 255
    _attr_icon = "mdi:send"
    # Empty must match too: HA 2026.10 checks the current value against the pattern.
    _attr_pattern = r"^(\s*(0[xX])?[0-9A-Fa-f]{1,8}#(#[0-9A-Fa-f])?[0-9A-Fa-fRr. ]*\s*)?$"

    def __init__(self, hub) -> None:
        super().__init__(hub, "send_frame", "text")
        self._attr_native_value = ""

    async def async_set_value(self, value: str) -> None:
        try:
            frame = CanFrame.parse(value)
        except ValueError as err:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="bad_frame",
                                         translation_placeholders={"error": str(err)}) from err
        await self.hub.async_send(frame)
        self._attr_native_value = str(frame)
        self.async_write_ha_state()
