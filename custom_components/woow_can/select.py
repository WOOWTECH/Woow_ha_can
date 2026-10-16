"""Selects: value-table signals written to devices that allow writing (modes)."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_KIND, KIND_HUB


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    if entry.data.get(CONF_KIND) == KIND_HUB:
        entry.runtime_data.devices.register_platform("select", async_add_entities)
