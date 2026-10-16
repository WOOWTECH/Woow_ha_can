"""Config flow: add a CAN interface (or a virtual one for testing), or the admin panel; options edit an interface."""

from __future__ import annotations

import os
import re
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)

from .can_port import FD_DRIVERS, IdMatcher, link_exists, parse_filters, vcan_add
from .const import (
    BITRATES,
    CAN_DEFAULTS,
    CONF_BITRATE,
    CONF_DBITRATE,
    CONF_EVENT_FILTER,
    CONF_FD,
    CONF_FILTERS,
    CONF_KIND,
    CONF_LISTEN_ONLY,
    CONF_MAX_RATE,
    CONF_PORT,
    CONF_RESTART_MS,
    CONF_VIRTUAL,
    DBITRATES,
    DOMAIN,
    KIND_CAN,
    KIND_HUB,
)

_INTS = (CONF_BITRATE, CONF_DBITRATE, CONF_RESTART_MS, CONF_MAX_RATE)
_VCAN_NAME = re.compile(r"^vcan\d{1,3}$")


def _driver(device: str) -> str:
    """Hardware driver of a sysfs device."""
    path = os.path.realpath(device)
    while path.startswith("/sys/devices/"):
        link = os.path.join(path, "driver")
        if os.path.exists(link):
            return os.path.basename(os.path.realpath(link))
        path = os.path.dirname(path)
    return ""


def scan_interfaces() -> dict[str, str]:
    """CAN interfaces (ARPHRD_CAN) and their drivers ("vcan" for virtual ones). Blocking."""
    found: dict[str, str] = {}
    for ifname in sorted(os.listdir("/sys/class/net")):
        try:
            with open(f"/sys/class/net/{ifname}/type", encoding="ascii") as fh:
                if fh.read().strip() != "280":
                    continue
        except OSError:
            continue
        found[ifname] = _driver(f"/sys/class/net/{ifname}/device") or ("vcan" if ifname.startswith("vcan") else "")
    return found


def _select(options: list[str]) -> SelectSelector:
    return SelectSelector(SelectSelectorConfig(options=options, mode=SelectSelectorMode.DROPDOWN))


def _number(low: int, high: int, step: int, unit: str) -> NumberSelector:
    return NumberSelector(NumberSelectorConfig(min=low, max=high, step=step,
                                               unit_of_measurement=unit, mode=NumberSelectorMode.BOX))


def can_schema(values: dict[str, Any], with_name: bool, fd_capable: bool, virtual: bool = False) -> vol.Schema:
    fields: dict[Any, Any] = {}
    if with_name:
        fields[vol.Required(CONF_NAME, default=values[CONF_NAME])] = TextSelector()
    if not virtual:  # a vcan has no bit timing, no listen-only and never goes bus-off
        fields[vol.Required(CONF_BITRATE, default=str(values[CONF_BITRATE]))] = _select([str(b) for b in BITRATES])
        if fd_capable:
            fields[vol.Required(CONF_FD, default=values[CONF_FD])] = BooleanSelector()
            fields[vol.Required(CONF_DBITRATE, default=str(values[CONF_DBITRATE]))] = _select([str(b) for b in DBITRATES])
        fields.update({
            vol.Required(CONF_LISTEN_ONLY, default=values[CONF_LISTEN_ONLY]): BooleanSelector(),
            vol.Required(CONF_RESTART_MS, default=values[CONF_RESTART_MS]): _number(0, 10000, 10, "ms"),
        })
    fields.update({
        vol.Optional(CONF_FILTERS, default=values[CONF_FILTERS]): TextSelector(),
        vol.Optional(CONF_EVENT_FILTER, default=values[CONF_EVENT_FILTER]): TextSelector(),
        vol.Required(CONF_MAX_RATE, default=values[CONF_MAX_RATE]): _number(1, 1000, 1, "/s"),
    })
    return vol.Schema(fields)


def coerce(data: dict[str, Any]) -> dict[str, Any]:
    out = dict(data)
    for key in _INTS:
        if key in out:
            out[key] = int(float(out[key]))
    out.setdefault(CONF_FILTERS, "")
    out.setdefault(CONF_EVENT_FILTER, "")
    out[CONF_FILTERS] = out[CONF_FILTERS].strip()
    out[CONF_EVENT_FILTER] = out[CONF_EVENT_FILTER].strip()
    return out


def filters_error(opts: dict[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}
    try:
        parse_filters(opts.get(CONF_FILTERS, ""))
    except ValueError:
        errors[CONF_FILTERS] = "bad_filter"
    try:
        IdMatcher(opts.get(CONF_EVENT_FILTER, ""))
    except ValueError:
        errors[CONF_EVENT_FILTER] = "bad_event_filter"
    return errors


class WoowCanConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add one CAN interface, a virtual one, or the admin panel."""

    VERSION = 1
    MINOR_VERSION = 2

    def __init__(self) -> None:
        self._port = ""
        self._driver = ""

    def _has_hub(self) -> bool:
        return any(e.data.get(CONF_KIND) == KIND_HUB for e in self._async_current_entries(include_ignore=False))

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        options = ["interface", "virtual"] + ([] if self._has_hub() else ["hub"])
        return self.async_show_menu(step_id="user", menu_options=options)

    # ---- the admin panel ------------------------------------------------------------
    async def async_step_hub(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        await self.async_set_unique_id(KIND_HUB)
        self._abort_if_unique_id_configured()
        chinese = (self.hass.config.language or "").lower().startswith("zh")
        return self.async_create_entry(title="管理面板" if chinese else "Admin panel", data={CONF_KIND: KIND_HUB})

    async def async_step_system(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Created once on first run (see __init__._async_offer_panel)."""
        return await self.async_step_hub()

    # ---- interfaces on the host -------------------------------------------------------
    async def async_step_interface(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        found = await self.hass.async_add_executor_job(scan_interfaces)
        free = {name: driver for name, driver in found.items() if name not in self._async_current_ids()}
        if not free:
            return self.async_abort(reason="no_interfaces")
        if user_input is not None and user_input[CONF_PORT] in free:
            self._port = user_input[CONF_PORT]
            self._driver = free[self._port]
            return await self.async_step_can()
        options = [SelectOptionDict(value=n, label=f"{n} · {d or '?'}") for n, d in free.items()]
        return self.async_show_form(step_id="interface", data_schema=vol.Schema({
            vol.Required(CONF_PORT): SelectSelector(SelectSelectorConfig(options=options, mode=SelectSelectorMode.LIST)),
        }))

    async def async_step_can(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        virtual = self._driver == "vcan"
        if user_input is not None:
            opts = coerce(user_input)
            name = opts.pop(CONF_NAME).strip() or self._port.upper()
            errors = filters_error(opts)
            if not errors:
                await self.async_set_unique_id(self._port)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=name, options=opts, data={
                    CONF_KIND: KIND_CAN, CONF_PORT: self._port, "driver": self._driver,
                    CONF_VIRTUAL: virtual})
        values = {**CAN_DEFAULTS, CONF_NAME: self._port.upper(), **(user_input or {})}
        return self.async_show_form(step_id="can", data_schema=can_schema(values, True, self._driver in FD_DRIVERS,
                                                                          virtual),
                                    errors=errors, description_placeholders={"port": self._port,
                                                                             "driver": self._driver or "?"})

    # ---- a virtual interface (vcan) for trying things without wiring -------------------
    async def async_step_virtual(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        taken = set(self._async_current_ids())
        default = next(f"vcan{i}" for i in range(100) if f"vcan{i}" not in taken)
        if user_input is not None:
            name = user_input[CONF_PORT].strip()
            if not _VCAN_NAME.match(name):
                errors[CONF_PORT] = "bad_vcan_name"
            elif name in taken:
                return self.async_abort(reason="already_configured")
            else:
                try:
                    if not await self.hass.async_add_executor_job(link_exists, name):
                        await self.hass.async_add_executor_job(vcan_add, name)
                except OSError:
                    errors["base"] = "vcan_failed"
                else:
                    self._port, self._driver = name, "vcan"
                    return await self.async_step_can()
        return self.async_show_form(step_id="virtual", errors=errors, data_schema=vol.Schema({
            vol.Required(CONF_PORT, default=(user_input or {}).get(CONF_PORT, default)): TextSelector(),
        }))

    @classmethod
    @callback
    def async_supports_options(cls, config_entry: ConfigEntry) -> bool:
        return config_entry.data.get(CONF_KIND, KIND_CAN) != KIND_HUB

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return WoowCanOptionsFlow()


class WoowCanOptionsFlow(OptionsFlow):
    """Change bus parameters (the interface restarts) or the event filter (applies at once)."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        entry = self.config_entry
        virtual = bool(entry.data.get(CONF_VIRTUAL)) or entry.data.get("driver") == "vcan"
        errors: dict[str, str] = {}
        if user_input is not None:
            opts = {**entry.options, **coerce(user_input)}
            errors = filters_error(opts)
            if not errors:
                return self.async_create_entry(data=opts)
        values = {**CAN_DEFAULTS, **entry.options, **(user_input or {})}
        return self.async_show_form(step_id="init", errors=errors,
                                    data_schema=can_schema(values, False, entry.data.get("driver") in FD_DRIVERS,
                                                           virtual),
                                    description_placeholders={"port": entry.data[CONF_PORT]})
