"""WOOW CAN: the host's SocketCAN interfaces (CAN / CAN FD) in Home Assistant, with an admin panel."""

from __future__ import annotations

import logging

from homeassistant.config_entries import SOURCE_SYSTEM, ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType

from . import llm_api, services, views, websocket_api
from .admin import AdminHub, hubs
from .can_port import link_exists, vcan_add, vcan_del
from .const import (
    CONF_EVENT_FILTER,
    CONF_KIND,
    CONF_MAX_RATE,
    CONF_PORT,
    CONF_VIRTUAL,
    DOMAIN,
    KIND_CAN,
    KIND_HUB,
    LIVE_OPTIONS,
)
from .hub import CanHub
from .services import SEND_SCHEMA  # noqa: F401  (imported by the tests)

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.EVENT, Platform.SENSOR, Platform.TEXT]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the services, the panel's websocket commands and file views; offer the panel once."""
    hubs(hass)
    websocket_api.async_register(hass)
    views.async_register(hass)
    services.async_register(hass)
    llm_api.async_register(hass)  # the same services as tools for Home Assistant's MCP server
    hass.async_create_task(_async_offer_panel(hass))
    return True


async def _async_offer_panel(hass: HomeAssistant) -> None:
    """Add the panel entry the first time the integration runs; a user who removes it keeps it removed."""
    if any(e.data.get(CONF_KIND) == KIND_HUB for e in hass.config_entries.async_entries(DOMAIN)):
        return
    store: Store[dict] = Store(hass, 1, f"{DOMAIN}.meta")
    meta = await store.async_load() or {}
    if meta.get("panel_offered"):
        return
    await store.async_save({**meta, "panel_offered": True})
    await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_SYSTEM})


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """1.1 -> 1.2: entries say what they are; interfaces keep firing an event for every frame as before."""
    if entry.version > 1:
        return False
    if entry.minor_version < 2:
        data = {**entry.data}
        data.setdefault(CONF_KIND, KIND_CAN)
        options = {**entry.options}
        if data[CONF_KIND] == KIND_CAN:
            options.setdefault(CONF_EVENT_FILTER, "*")
        hass.config_entries.async_update_entry(entry, data=data, options=options, minor_version=2)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if entry.data.get(CONF_KIND, KIND_CAN) == KIND_HUB:
        admin = AdminHub(hass, entry)
        await admin.async_start()
        entry.runtime_data = admin
        hass.data[DOMAIN]["admin"] = admin
        return True
    port = entry.data[CONF_PORT]
    if entry.data.get(CONF_VIRTUAL) and not await hass.async_add_executor_job(link_exists, port):
        try:  # virtual interfaces do not survive a reboot of the host
            await hass.async_add_executor_job(vcan_add, port)
        except OSError as err:
            raise ConfigEntryNotReady(f"{entry.title}: cannot create {port}: {err}") from err
    hub = CanHub(hass, entry)
    try:
        await hub.async_start()
    except (OSError, ValueError) as err:
        await hub.async_stop()
        raise ConfigEntryNotReady(f"{entry.title} ({hub.port}): {err}") from err
    entry.runtime_data = hub
    hubs(hass)[entry.entry_id] = hub
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    if (admin := hass.data[DOMAIN].get("admin")) is not None:
        admin.hub_added(hub)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if entry.data.get(CONF_KIND, KIND_CAN) == KIND_HUB:
        await entry.runtime_data.async_stop()
        hass.data[DOMAIN].pop("admin", None)
        return True
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    if (admin := hass.data[DOMAIN].get("admin")) is not None:
        await admin.async_stop_capture(entry.entry_id)
        admin.hub_removed(entry.entry_id)
    hubs(hass).pop(entry.entry_id, None)
    await entry.runtime_data.async_stop()
    return True


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """A removed virtual interface is deleted from the host too."""
    if entry.data.get(CONF_VIRTUAL):
        try:
            await hass.async_add_executor_job(vcan_del, entry.data[CONF_PORT])
        except OSError:
            pass


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    hub: CanHub = entry.runtime_data
    changed = {k for k in set(entry.options) | set(hub.options) if entry.options.get(k) != hub.options.get(k)}
    if changed and changed <= LIVE_OPTIONS:  # the event filter: no need to restart the interface
        hub.apply_live_options(entry.options.get(CONF_EVENT_FILTER, ""), int(entry.options.get(CONF_MAX_RATE, 20)))
        hub.options = dict(entry.options)
        if (admin := hass.data[DOMAIN].get("admin")) is not None:
            admin.hub_added(hub)  # pushes the new settings to the panel
        return
    await hass.config_entries.async_reload(entry.entry_id)
