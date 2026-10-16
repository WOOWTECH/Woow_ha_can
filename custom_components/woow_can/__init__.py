"""WOOW CAN: the Pi's SocketCAN interfaces (CAN / CAN FD) as Home Assistant devices."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import ConfigEntryNotReady, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .can_port import CanFrame, parse_id
from .codec import parse_hex
from .const import ATTR_ENTRY, DOMAIN, SERVICE_SEND
from .hub import CanHub

PLATFORMS = [Platform.EVENT, Platform.SENSOR, Platform.TEXT]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

_WAIT = vol.All(vol.Coerce(int), vol.Range(min=0, max=60000))
SEND_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTRY): cv.string,
    vol.Required("can_id"): cv.string,
    vol.Optional("data", default=""): cv.string,
    vol.Optional("extended"): cv.boolean,
    vol.Optional("fd", default=False): cv.boolean,
    vol.Optional("brs", default=False): cv.boolean,
    vol.Optional("rtr", default=False): cv.boolean,
    vol.Optional("wait_id"): cv.string,
    vol.Optional("wait_ms", default=0): _WAIT,
})


def _invalid(key: str, **placeholders: str) -> ServiceValidationError:
    return ServiceValidationError(translation_domain=DOMAIN, translation_key=key,
                                  translation_placeholders=placeholders or None)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the send service (it looks the interface up per call)."""

    async def send(call: ServiceCall) -> ServiceResponse:
        entry = hass.config_entries.async_get_entry(call.data[ATTR_ENTRY])
        if entry is None or entry.domain != DOMAIN or entry.state is not ConfigEntryState.LOADED:
            raise _invalid("not_loaded", entry=call.data[ATTR_ENTRY])
        hub: CanHub = entry.runtime_data
        try:
            can_id, extended = parse_id(call.data["can_id"])
            frame = CanFrame.build(can_id, parse_hex(call.data["data"]),
                                   call.data.get("extended", extended),
                                   call.data["fd"], call.data["brs"], call.data["rtr"])
            match = None
            if "wait_id" in call.data:
                want_id, want_ext = parse_id(call.data["wait_id"])
                match = lambda f: f.can_id == want_id and f.extended == want_ext  # noqa: E731
        except ValueError as err:
            raise _invalid("bad_frame", error=str(err)) from err
        wait = call.data["wait_ms"] / 1000
        reply = await hub.async_send(frame, wait, match)
        if not call.return_response:
            return None
        response: dict = {"sent": frame.as_dict()}
        if wait > 0:
            response["reply"] = reply.as_dict() if reply is not None else None
            response["timeout"] = reply is None
        return response

    hass.services.async_register(DOMAIN, SERVICE_SEND, send, schema=SEND_SCHEMA,
                                 supports_response=SupportsResponse.OPTIONAL)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hub = CanHub(hass, entry)
    try:
        await hub.async_start()
    except (OSError, ValueError) as err:
        await hub.async_stop()
        raise ConfigEntryNotReady(f"{entry.title} ({hub.port}): {err}") from err
    entry.runtime_data = hub
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.async_stop()
    return unloaded


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
