"""Home Assistant services for AI agents (and scripts): what the panel does, as actions.

Agents reach these over MCP (ha-mcp's service calls, or Home Assistant's own MCP server through
the "WOOW CAN" LLM API). Design rules, as in WOOW Serial:
- interfaces are named by config entry id, name (CAN0) or interface (can0);
- reads return data (SupportsResponse.ONLY); changes return data when asked (OPTIONAL);
- input is checked in the handler, not by Home Assistant's schema check: over REST a schema
  failure is a bare "400: Bad Request", a ServiceValidationError carries its message;
- sending and changing settings need an admin user; reading does not;
- every send and change is written to the activity log with the caller's user and its `note`.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
import time
from typing import TYPE_CHECKING, Any

import probatio
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.service import async_register_admin_service

from .can_port import CanFrame, IdMatcher, parse_id
from .capture import trace_matcher
from .const import ATTR_ENTRY, DOMAIN, PERIODIC_MIN_MS, SERVICE_SEND
from .periodic import PeriodicError

if TYPE_CHECKING:
    from .admin import AdminHub
    from .hub import CanHub

_NOTE = vol.Optional("note", default="")  # every change can say why; shown in the activity log
_LIMIT = vol.All(vol.Coerce(int), vol.Range(min=1, max=2000))
_WAIT = vol.All(vol.Coerce(int), vol.Range(min=0, max=60000))
ADMIN_SERVICES = {SERVICE_SEND, "save_periodic", "control_periodic", "capture", "clear_monitor"}
EXPECT_WAIT = 1.0  # s, when wait_id is given without wait_ms

SEND_SCHEMA = vol.Schema({
    vol.Exclusive(ATTR_ENTRY, "target"): cv.string,
    vol.Exclusive("interface", "target"): cv.string,  # a name (CAN0) or interface (can0), handy for agents
    vol.Exclusive("frame", "payload"): cv.string,  # cansend notation: 123#11223344
    vol.Exclusive("can_id", "payload"): cv.string,
    vol.Optional("data", default=""): cv.string,
    vol.Optional("extended"): cv.boolean,
    vol.Optional("fd", default=False): cv.boolean,
    vol.Optional("brs", default=False): cv.boolean,
    vol.Optional("rtr", default=False): cv.boolean,
    vol.Optional("wait_id"): cv.string,
    vol.Optional("wait_ms", default=0): _WAIT,
    _NOTE: cv.string,
})


def _invalid(key: str, **placeholders: str) -> ServiceValidationError:
    return ServiceValidationError(translation_domain=DOMAIN, translation_key=key,
                                  translation_placeholders=placeholders or None)


def _explain(err: Exception) -> str:
    """'value must be one of [...] at 'type'' for each problem, as Home Assistant's websocket API words it."""
    parts = []
    for error in getattr(err, "errors", None) or [err]:
        path = ".".join(str(p) for p in getattr(error, "path", None) or [])
        message = getattr(error, "msg", None) or str(error)
        parts.append(f"{message} at '{path}'" if path else message)
    return "; ".join(parts)


def validated(hass: HomeAssistant, schema: Callable[[dict[str, Any]], dict[str, Any]],
              handler: Callable[[ServiceCall], Awaitable[ServiceResponse]]) -> Callable[[ServiceCall], Awaitable[ServiceResponse]]:
    """Check a call's data in the handler, so every caller (REST included) is told what is wrong."""

    async def run(call: ServiceCall) -> ServiceResponse:
        try:
            data = schema(dict(call.data))
        except (vol.Invalid, probatio.Invalid) as err:
            raise _invalid("bad_input", error=_explain(err)) from err
        return await handler(ServiceCall(hass, call.domain, call.service, data, call.context, call.return_response))

    return run


def _admin(hass: HomeAssistant) -> AdminHub | None:
    return hass.data.get(DOMAIN, {}).get("admin")


def _need_admin(hass: HomeAssistant) -> AdminHub:
    admin = _admin(hass)
    if admin is None:
        raise _invalid("panel_not_loaded")
    return admin


def _hubs(hass: HomeAssistant) -> dict[str, CanHub]:
    return hass.data.get(DOMAIN, {}).get("hubs", {})


def resolve_interface(hass: HomeAssistant, ref: str) -> CanHub:
    """An interface by config entry id, name (CAN0) or interface name (can0)."""
    want = ref.strip().casefold()
    hubs = _hubs(hass)
    for hub in hubs.values():
        if want in (hub.entry.entry_id.casefold(), hub.name.casefold(), hub.port.casefold()):
            return hub
    raise _invalid("unknown_interface", interface=ref,
                   interfaces=", ".join(sorted(h.name for h in hubs.values())) or "-")


def _matcher(text: str | None) -> IdMatcher | None:
    if not text or not text.strip():
        return None
    try:
        return IdMatcher(text)
    except ValueError as err:
        raise _invalid("bad_ids", error=str(err)) from err


def _interface_view(hub: CanHub) -> dict[str, Any]:
    info = hub.info()
    status = info["status"]
    return {
        "name": info["name"], "interface": info["port"], "config_entry_id": info["id"], "driver": info["driver"],
        "available": info["available"], "virtual": info["virtual"], "can_send": info["can_send"],
        "settings": info["settings"],
        "state": status.get("state"),
        "error_counters": {"tx": status.get("tx_error_counter"), "rx": status.get("rx_error_counter")},
        "bus_load_percent": info["load"]["now"], "bus_load_1min": info["load"]["avg"][0],
        "frames_per_second": {"rx": info["load"]["rx_fps"], "tx": info["load"]["tx_fps"]},
        "controller_events": {k: status.get(k) for k in ("error_warning", "error_passive", "bus_off", "restarts")},
        "bus_errors": (status.get("bus_error") if status.get("berr_reporting") else
                       "bus error reporting is off" if status.get("berr_supported") else "not reported by this controller"),
        "drops": {"socket": status.get("socket_drops"), "rx_dropped": status.get("rx_dropped"),
                  "rx_overflow": status.get("rx_over_errors"), "events_over_rate": status.get("events_dropped")},
        "last_error_frame": info["errors"]["last"],
        "ids_seen": info["monitor"]["ids"],
        "recording": info["recording"],
    }


def describe(hass: HomeAssistant) -> dict[str, Any]:
    """Everything an agent needs to know to use this integration."""
    return {
        "integration": "woow_can",
        "purpose": "Watch and use CAN / CAN FD buses (SocketCAN interfaces such as can0 / can1 on the Pi) from "
                   "Home Assistant: per-ID monitor, time-ordered trace, sending, periodic sends, recordings.",
        "workflow": [
            "list_interfaces: state (error_active = healthy), bus load, error counters per interface.",
            "get_monitor: one row per CAN ID with count, rate, period and the latest data; data_changes tells "
            "which IDs carry changing values. Ask a person to operate the equipment and compare two calls to "
            "find the frame of an action.",
            "get_trace: frames in time order (newest first), e.g. a request and its reply.",
            "send (admin): one frame, optionally waiting for a reply ID. Interfaces in listen-only mode cannot "
            "send. Never send to vehicles or machinery unless the user asked for that exact frame.",
            "save_periodic / control_periodic (admin): frames sent every period_ms.",
            "capture (admin): record an interface to a candump log file under <config>/woow_can/captures.",
            "Give every change a short `note`: people read it in the panel's activity log.",
        ],
        "frame_notation": "cansend: 123#11223344 (11-bit), 18FF50E5#0102 (29-bit), 123#R (remote), "
                          "456##1AABBCC (CAN FD; the digit after ## is the flags, 1 = bit rate switch)",
        "id_lists": "comma separated: 123, 18FF50E5, 7E0/7F0 (ID/mask), 100-1FF (range), * (all)",
        "events": {"woow_can_frame": "received frames whose ID is in the interface's event filter (option "
                                     "'event filter'; empty = none): entry_id, name, interface, frame, id, id_hex, "
                                     "data, length, extended, fd, brs, rtr"},
        "safety": "Listen-only interfaces never acknowledge or send. Sends are logged with the user and note.",
        "interfaces": [_interface_view(h) for h in _hubs(hass).values()],
    }


async def async_send(hass: HomeAssistant, call: ServiceCall) -> ServiceResponse:
    """woow_can.send (registered in __init__ for the old service name and fields)."""
    if ATTR_ENTRY in call.data:
        hub = resolve_interface(hass, call.data[ATTR_ENTRY])
    elif "interface" in call.data:
        hub = resolve_interface(hass, call.data["interface"])
    else:
        raise _invalid("no_interface")
    try:
        if "frame" in call.data:
            frame = CanFrame.parse(call.data["frame"])
        elif "can_id" in call.data:
            can_id, extended = parse_id(call.data["can_id"])
            frame = CanFrame.build(can_id, bytes.fromhex(call.data["data"].replace(" ", "").replace(",", "")
                                                          .replace("0x", "").replace("0X", "")),
                                   call.data.get("extended", extended), call.data["fd"], call.data["brs"],
                                   call.data["rtr"])
        else:
            raise _invalid("no_frame")
        match = None
        if call.data.get("wait_id"):
            want_id, want_ext = parse_id(call.data["wait_id"])
            match = lambda f: f.can_id == want_id and f.extended == want_ext  # noqa: E731
    except ValueError as err:
        raise _invalid("bad_frame", error=str(err)) from err
    wait = call.data["wait_ms"] / 1000 or (EXPECT_WAIT if call.data.get("wait_id") else 0)
    admin = _admin(hass)
    started = time.monotonic()
    try:
        reply = await hub.async_send(frame, wait, match)
    except HomeAssistantError as err:
        if admin is not None and (call.context.user_id or call.data["note"]):
            await admin.activity.async_record("service", "send", "send_failed",
                                              {"frame": str(frame), "port": hub.name, "error": str(err)},
                                              context=call.context, note=call.data["note"], ok=False,
                                              port_id=hub.entry.entry_id)
        raise
    elapsed = round((time.monotonic() - started) * 1000)
    if admin is not None and (call.context.user_id or call.data["note"]):  # people / agents, not automations
        await admin.activity.async_record("service", "send", "sent", {"frame": str(frame), "port": hub.name},
                                          context=call.context, note=call.data["note"], port_id=hub.entry.entry_id)
    if not call.return_response:
        return None
    response: dict[str, Any] = {"interface": hub.name, "sent": frame.as_dict()}
    if wait > 0:
        response["reply"] = reply.as_dict() if reply is not None else None
        response["timeout"] = reply is None
        response["elapsed_ms"] = elapsed
    return response


def async_register(hass: HomeAssistant) -> None:
    """Register the services (they look the interfaces and the admin entry up per call)."""

    def register(name: str, handler: Callable[[ServiceCall], Awaitable[ServiceResponse]], schema: dict | vol.Schema,
                 response: SupportsResponse) -> None:
        run = validated(hass, schema if isinstance(schema, vol.Schema) else vol.Schema(schema), handler)
        if name in ADMIN_SERVICES:
            async_register_admin_service(hass, DOMAIN, name, run, schema=None, supports_response=response)
        else:
            hass.services.async_register(DOMAIN, name, run, schema=None, supports_response=response)

    async def record(call: ServiceCall, action: str, msg: str, args: dict[str, Any], **extra: Any) -> None:
        admin = _admin(hass)
        if admin is not None:
            await admin.activity.async_record("service", action, msg, args, context=call.context,
                                              note=call.data.get("note", ""), **extra)

    # ---- reads ------------------------------------------------------------------------------
    async def s_describe(call: ServiceCall) -> ServiceResponse:
        return describe(hass)

    async def s_list_interfaces(call: ServiceCall) -> ServiceResponse:
        return {"interfaces": [_interface_view(h) for h in _hubs(hass).values()]}

    async def s_get_monitor(call: ServiceCall) -> ServiceResponse:
        hubs = [resolve_interface(hass, call.data["interface"])] if call.data.get("interface") else list(_hubs(hass).values())
        match = _matcher(call.data.get("ids"))
        now = time.time()
        return {"interfaces": [{
            "interface": hub.name, "since": round(hub.monitor.since, 3), "frames": hub.monitor.frames,
            "ids_seen": len(hub.monitor.stats), "ids_beyond_limit_frames": hub.monitor.overflow,
            "ids": hub.monitor.summary(now, call.data["limit"], match),
        } for hub in hubs]}

    async def s_get_trace(call: ServiceCall) -> ServiceResponse:
        hub = resolve_interface(hass, call.data["interface"])
        match = trace_matcher(_matcher(call.data.get("ids")), call.data.get("direction"))
        since = time.time() - call.data["seconds"] if call.data.get("seconds") else None
        snapshot = hub.trace.snapshot()
        page = await hass.async_add_executor_job(snapshot.page, call.data.get("before"), call.data["limit"], match,
                                                 since)
        return {"interface": hub.name, "frames": [f.as_dict() for f in page["frames"]], "next_before": page["next"],
                "buffer": {"first": page["first"], "end": page["end"]}}

    async def s_get_activity(call: ServiceCall) -> ServiceResponse:
        return {"activity": _need_admin(hass).activity.recent(call.data["limit"])}

    async def s_list_periodic(call: ServiceCall) -> ServiceResponse:
        admin = _need_admin(hass)
        names = {e: h.name for e, h in _hubs(hass).items()}
        return {"periodic": [{**item, "interface": names.get(item["entry_id"], "?")} for item in admin.periodic.snapshot()]}

    async def s_list_captures(call: ServiceCall) -> ServiceResponse:
        admin = _need_admin(hass)
        return {"captures": await admin.async_list_captures(), "folder": admin.capture_dir}

    # ---- changes ----------------------------------------------------------------------------
    async def s_send(call: ServiceCall) -> ServiceResponse:
        return await async_send(hass, call)

    def _periodic_item(admin: AdminHub, ref: str):
        want = ref.strip().casefold()
        for item in admin.periodic.items.values():
            if want in (item.id.casefold(), item.name.casefold()):
                return item
        raise _invalid("unknown_periodic", item=ref,
                       items=", ".join(sorted(i.name for i in admin.periodic.items.values())) or "-")

    async def s_save_periodic(call: ServiceCall) -> ServiceResponse:
        admin = _need_admin(hass)
        hub = resolve_interface(hass, call.data["interface"])
        raw = {"entry_id": hub.entry.entry_id, "frame": call.data["frame"], "period_ms": call.data["period_ms"],
               "count": call.data["count"], "name": call.data.get("name", "")}
        if call.data.get("item"):
            raw["id"] = _periodic_item(admin, call.data["item"]).id
        try:
            item = admin.periodic.save(raw)
        except PeriodicError as err:
            raise _invalid("bad_periodic", error=str(err)) from err
        await record(call, "save_periodic", "periodic_saved", {"name": item.name, "frame": item.frame,
                                                                "period": item.period_ms, "port": hub.name},
                     port_id=hub.entry.entry_id)
        if call.data["start"]:
            hub.check_can_send(CanFrame.parse(item.frame))
            admin.periodic.start(item.id)
            await record(call, "start_periodic", "periodic_started", {"name": item.name, "port": hub.name},
                         port_id=hub.entry.entry_id)
        return {"periodic": admin.periodic.item_view(item.id)} if call.return_response else None

    async def s_control_periodic(call: ServiceCall) -> ServiceResponse:
        admin = _need_admin(hass)
        item = _periodic_item(admin, call.data["item"])
        hub = _hubs(hass).get(item.entry_id)
        action = call.data["action"]
        if action == "start":
            if hub is None:
                raise _invalid("unknown_interface", interface=item.entry_id, interfaces="-")
            hub.check_can_send(CanFrame.parse(item.frame))
            admin.periodic.start(item.id)
            await record(call, "start_periodic", "periodic_started", {"name": item.name, "port": hub.name},
                         port_id=item.entry_id)
        elif action == "stop":
            sent = admin.periodic.item_view(item.id)["sent"]
            admin.periodic.stop(item.id, "user")
            await record(call, "stop_periodic", "periodic_stopped", {"name": item.name, "sent": sent},
                         port_id=item.entry_id)
        else:
            admin.periodic.delete(item.id)
            await record(call, "delete_periodic", "periodic_deleted", {"name": item.name}, port_id=item.entry_id)
            return {"ok": True} if call.return_response else None
        return {"periodic": admin.periodic.item_view(item.id)} if call.return_response else None

    async def s_capture(call: ServiceCall) -> ServiceResponse:
        admin = _need_admin(hass)
        hub = resolve_interface(hass, call.data["interface"])
        if call.data["action"] == "start":
            rec = await admin.async_start_capture(hub.entry.entry_id)
            await record(call, "start_capture", "capture_started", {"file": rec.name, "port": hub.name},
                         port_id=hub.entry.entry_id)
            return {"recording": rec.name, "folder": admin.capture_dir} if call.return_response else None
        rec = await admin.async_stop_capture(hub.entry.entry_id)
        if rec is not None:
            await record(call, "stop_capture", "capture_stopped", {"file": rec.name, "frames": rec.frames},
                         port_id=hub.entry.entry_id)
        if not call.return_response:
            return None
        return {"stopped": rec.name if rec else None, "frames": rec.frames if rec else 0}

    async def s_clear_monitor(call: ServiceCall) -> ServiceResponse:
        hub = resolve_interface(hass, call.data["interface"])
        hub.monitor.clear()
        hub.load.reset_peak()
        await record(call, "clear_monitor", "monitor_cleared", {"port": hub.name}, port_id=hub.entry.entry_id)
        return {"ok": True} if call.return_response else None

    register("describe", s_describe, {}, SupportsResponse.ONLY)
    register("list_interfaces", s_list_interfaces, {}, SupportsResponse.ONLY)
    register("get_monitor", s_get_monitor, {vol.Optional("interface"): cv.string, vol.Optional("ids"): cv.string,
                                            vol.Optional("limit", default=200): _LIMIT}, SupportsResponse.ONLY)
    register("get_trace", s_get_trace, {vol.Required("interface"): cv.string, vol.Optional("ids"): cv.string,
                                        vol.Optional("direction"): vol.In(["rx", "tx"]),
                                        vol.Optional("limit", default=100): _LIMIT,
                                        vol.Optional("before"): vol.Coerce(int),
                                        vol.Optional("seconds"): vol.All(vol.Coerce(float), vol.Range(min=0.001))},
             SupportsResponse.ONLY)
    register("get_activity", s_get_activity, {vol.Optional("limit", default=50): _LIMIT}, SupportsResponse.ONLY)
    register("list_periodic", s_list_periodic, {}, SupportsResponse.ONLY)
    register("list_captures", s_list_captures, {}, SupportsResponse.ONLY)
    register(SERVICE_SEND, s_send, SEND_SCHEMA, SupportsResponse.OPTIONAL)
    register("save_periodic", s_save_periodic, {
        vol.Required("interface"): cv.string, vol.Required("frame"): cv.string,
        vol.Required("period_ms"): vol.All(vol.Coerce(int), vol.Range(min=PERIODIC_MIN_MS, max=3_600_000)),
        vol.Optional("count", default=0): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Optional("name", default=""): cv.string, vol.Optional("item"): cv.string,
        vol.Optional("start", default=False): cv.boolean, _NOTE: cv.string}, SupportsResponse.OPTIONAL)
    register("control_periodic", s_control_periodic, {
        vol.Required("item"): cv.string, vol.Required("action"): vol.In(["start", "stop", "delete"]), _NOTE: cv.string},
             SupportsResponse.OPTIONAL)
    register("capture", s_capture, {vol.Required("interface"): cv.string,
                                    vol.Required("action"): vol.In(["start", "stop"]), _NOTE: cv.string},
             SupportsResponse.OPTIONAL)
    register("clear_monitor", s_clear_monitor, {vol.Required("interface"): cv.string, _NOTE: cv.string},
             SupportsResponse.OPTIONAL)
