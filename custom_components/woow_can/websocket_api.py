"""Websocket commands behind the panel (admin only)."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError

from . import analysis
from .admin import AdminHub
from .can_port import CanFrame, IdMatcher, parse_id
from .capture import trace_matcher
from .const import CONF_EVENT_FILTER, CONF_MAX_RATE, DOMAIN, TRACE_PAGE
from .periodic import PeriodicError
from .signals import DefinitionError, Signal

_COMMANDS: list[Any] = []


def _command(func: Any) -> Any:
    _COMMANDS.append(func)
    return func


@callback
def async_register(hass: HomeAssistant) -> None:
    for handler in _COMMANDS:
        websocket_api.async_register_command(hass, handler)


def _admin(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> AdminHub | None:
    admin = hass.data.get(DOMAIN, {}).get("admin")
    if admin is None:
        connection.send_error(msg["id"], "not_loaded", "The WOOW CAN panel entry is not loaded")
    return admin


async def _log(admin: AdminHub, connection: websocket_api.ActiveConnection, action: str, msg: str,
               args: dict[str, Any], **extra: Any) -> None:
    """Panel changes go to the activity log next to the agents' ones."""
    user = connection.user.name if connection.user is not None else None
    await admin.activity.async_record("panel", action, msg, args, user=user, **extra)


def _name(admin: AdminHub, entry_id: str) -> str:
    hub = admin.hubs.get(entry_id)
    return hub.name if hub else "?"


@_command
@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "woow_can/snapshot"})
@callback
def ws_snapshot(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    if (admin := _admin(hass, connection, msg)) is not None:
        connection.send_result(msg["id"], admin.snapshot())


@_command
@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "woow_can/subscribe"})
@callback
def ws_subscribe(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Live feed: {"kind": "interfaces" | "periodic" | "activity" | "captures" | "offline", ...}."""
    if (admin := _admin(hass, connection, msg)) is None:
        return

    @callback
    def forward(kind: str, payload: dict[str, Any]) -> None:
        connection.send_message(websocket_api.event_message(msg["id"], {"kind": kind, **payload}))

    connection.subscriptions[msg["id"]] = admin.subscribe(forward)
    connection.send_result(msg["id"])


# ---- monitor -------------------------------------------------------------------------------
def _viewers(hass: HomeAssistant) -> dict[tuple[int, str], Any]:
    return hass.data.setdefault(DOMAIN, {}).setdefault("ws_viewers", {})


@_command
@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "woow_can/monitor/subscribe",
    vol.Required("source"): str,
    vol.Required("token"): vol.All(str, vol.Length(min=1, max=64)),
})
@callback
def ws_monitor_subscribe(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Per-ID batches of one interface; acknowledge each with woow_can/monitor/ack and the same token."""
    if (admin := _admin(hass, connection, msg)) is None:
        return

    @callback
    def forward(payload: dict[str, Any]) -> None:
        connection.send_message(websocket_api.event_message(msg["id"], payload))

    connection.send_result(msg["id"])
    try:
        viewer, unsub = admin.subscribe_monitor(msg["source"], forward)
    except HomeAssistantError as err:
        forward({"gone": True, "error": str(err)})
        return
    key = (id(connection), msg["token"])
    _viewers(hass)[key] = viewer

    @callback
    def cancel() -> None:
        unsub()
        _viewers(hass).pop(key, None)

    connection.subscriptions[msg["id"]] = cancel


@_command
@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "woow_can/monitor/ack",
    vol.Required("token"): str,
    vol.Required("seq"): int,
})
@callback
def ws_monitor_ack(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    viewer = _viewers(hass).get((id(connection), msg["token"]))
    if viewer is not None:
        viewer.acked = max(viewer.acked, min(msg["seq"], viewer.seq))
    connection.send_result(msg["id"])


@_command
@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "woow_can/monitor/clear", vol.Required("source"): str})
@websocket_api.async_response
async def ws_monitor_clear(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    if (admin := _admin(hass, connection, msg)) is None:
        return
    try:
        src = admin.source(msg["source"])
    except HomeAssistantError as err:
        connection.send_error(msg["id"], "not_found", str(err))
        return
    src.monitor.clear()
    if getattr(src, "live", True):
        src.load.reset_peak()
        await _log(admin, connection, "clear_monitor", "monitor_cleared", {"port": src.name}, port_id=msg["source"])
    connection.send_result(msg["id"])


@_command
@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "woow_can/trace",
    vol.Required("source"): str,
    vol.Optional("before"): vol.Any(None, int),
    vol.Optional("limit", default=TRACE_PAGE): vol.All(int, vol.Range(min=1, max=2000)),
    vol.Optional("ids", default=""): str,
    vol.Optional("direction"): vol.Any(None, "rx", "tx"),
    vol.Optional("errors", default=True): bool,
})
@websocket_api.async_response
async def ws_trace(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """A page of the time-ordered view, newest first: [seq, time, raw id, flags, data hex] per frame."""
    if (admin := _admin(hass, connection, msg)) is None:
        return
    try:
        src = admin.source(msg["source"])
        ids = IdMatcher(msg["ids"]) if msg["ids"].strip() else None
    except (HomeAssistantError, ValueError) as err:
        connection.send_error(msg["id"], "invalid", str(err))
        return
    match = trace_matcher(ids, msg.get("direction"), msg["errors"])
    snapshot = src.trace.snapshot()
    page = await hass.async_add_executor_job(snapshot.page, msg.get("before"), msg["limit"], match)
    connection.send_result(msg["id"], {**page, "frames": [f.as_list() for f in page["frames"]]})


# ---- sending -------------------------------------------------------------------------------
@_command
@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "woow_can/send",
    vol.Required("entry_id"): str,
    vol.Required("frame"): str,
    vol.Optional("wait_ms", default=0): vol.All(int, vol.Range(min=0, max=60000)),
    vol.Optional("wait_id"): str,
})
@websocket_api.async_response
async def ws_send(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    if (admin := _admin(hass, connection, msg)) is None:
        return
    hub = admin.hubs.get(msg["entry_id"])
    if hub is None:
        connection.send_error(msg["id"], "not_found", "The interface is not loaded")
        return
    try:
        frame = CanFrame.parse(msg["frame"])
        match = None
        if msg.get("wait_id"):
            want_id, want_ext = parse_id(msg["wait_id"])
            match = lambda f: f.can_id == want_id and f.extended == want_ext  # noqa: E731
    except ValueError as err:
        connection.send_error(msg["id"], "invalid_format", str(err))
        return
    wait = msg["wait_ms"] / 1000
    try:
        reply = await hub.async_send(frame, wait, match)
    except HomeAssistantError as err:
        await _log(admin, connection, "send", "send_failed", {"frame": str(frame), "port": hub.name,
                                                               "error": str(err)}, ok=False, port_id=hub.entry.entry_id)
        connection.send_error(msg["id"], "send_failed", str(err))
        return
    await _log(admin, connection, "send", "sent", {"frame": str(frame), "port": hub.name}, port_id=hub.entry.entry_id)
    connection.send_result(msg["id"], {"sent": frame.as_dict(), "reply": reply.as_dict() if reply else None,
                                       "timeout": wait > 0 and reply is None})


@_command
@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "woow_can/interface/events",
    vol.Required("entry_id"): str,
    vol.Required("event_filter"): str,
    vol.Optional("max_events_per_sec"): vol.All(int, vol.Range(min=1, max=1000)),
})
@callback
def ws_interface_events(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Change which IDs fire woow_can_frame events (applies without restarting the interface)."""
    entry = hass.config_entries.async_get_entry(msg["entry_id"])
    if entry is None or entry.domain != DOMAIN:
        connection.send_error(msg["id"], "not_found", "No such interface")
        return
    try:
        IdMatcher(msg["event_filter"])
    except ValueError as err:
        connection.send_error(msg["id"], "invalid_format", str(err))
        return
    options = {**entry.options, CONF_EVENT_FILTER: msg["event_filter"].strip()}
    if "max_events_per_sec" in msg:
        options[CONF_MAX_RATE] = msg["max_events_per_sec"]
    hass.config_entries.async_update_entry(entry, options=options)
    connection.send_result(msg["id"])


# ---- periodic sends ------------------------------------------------------------------------
@_command
@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "woow_can/periodic/save", vol.Required("item"): dict})
@websocket_api.async_response
async def ws_periodic_save(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    if (admin := _admin(hass, connection, msg)) is None:
        return
    try:
        item = admin.periodic.save(msg["item"])
    except PeriodicError as err:
        connection.send_error(msg["id"], err.code, str(err))
        return
    await _log(admin, connection, "save_periodic", "periodic_saved",
               {"name": item.name, "frame": item.frame, "period": item.period_ms, "port": _name(admin, item.entry_id)},
               port_id=item.entry_id)
    connection.send_result(msg["id"], admin.periodic.item_view(item.id))


@_command
@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "woow_can/periodic/control",
    vol.Required("item_id"): str,
    vol.Required("action"): vol.In(["start", "stop", "delete"]),
})
@websocket_api.async_response
async def ws_periodic_control(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    if (admin := _admin(hass, connection, msg)) is None:
        return
    item = admin.periodic.items.get(msg["item_id"])
    if item is None:
        connection.send_error(msg["id"], "not_found", "No such periodic send")
        return
    action = msg["action"]
    if action == "start":
        hub = admin.hubs.get(item.entry_id)
        if hub is None:
            connection.send_error(msg["id"], "not_found", "The interface is not loaded")
            return
        try:
            hub.check_can_send(CanFrame.parse(item.frame))
        except HomeAssistantError as err:
            connection.send_error(msg["id"], "cannot_send", str(err))
            return
        admin.periodic.start(item.id)
        await _log(admin, connection, "start_periodic", "periodic_started", {"name": item.name, "port": hub.name},
                   port_id=item.entry_id)
    elif action == "stop":
        sent = admin.periodic.item_view(item.id)["sent"]
        admin.periodic.stop(item.id, "user")
        await _log(admin, connection, "stop_periodic", "periodic_stopped", {"name": item.name, "sent": sent},
                   port_id=item.entry_id)
    else:
        admin.periodic.delete(item.id)
        await _log(admin, connection, "delete_periodic", "periodic_deleted", {"name": item.name}, port_id=item.entry_id)
    connection.send_result(msg["id"])


# ---- captures ------------------------------------------------------------------------------
@_command
@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "woow_can/capture/list"})
@websocket_api.async_response
async def ws_capture_list(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    if (admin := _admin(hass, connection, msg)) is None:
        return
    connection.send_result(msg["id"], {"captures": await admin.async_list_captures(),
                                       "offline": [s.info() for s in admin.offline.values()]})


@_command
@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "woow_can/capture/control",
    vol.Required("action"): vol.In(["start", "stop", "delete", "open", "close", "convert"]),
    vol.Optional("entry_id"): str,
    vol.Optional("name"): str,
    vol.Optional("source"): str,
    vol.Optional("format"): str,
})
@websocket_api.async_response
async def ws_capture_control(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    if (admin := _admin(hass, connection, msg)) is None:
        return
    action = msg["action"]
    result: dict[str, Any] = {}
    try:
        if action in ("start", "stop"):
            entry_id = msg.get("entry_id") or ""
            hub = admin.hubs.get(entry_id)
            if hub is None:
                raise HomeAssistantError("The interface is not loaded")
            if action == "start":
                rec = await admin.async_start_capture(entry_id)
                result["name"] = rec.name
                await _log(admin, connection, "start_capture", "capture_started", {"file": rec.name, "port": hub.name},
                           port_id=entry_id)
            else:
                rec = await admin.async_stop_capture(entry_id)
                if rec is not None:
                    result["name"] = rec.name
                    await _log(admin, connection, "stop_capture", "capture_stopped",
                               {"file": rec.name, "frames": rec.frames}, port_id=entry_id)
        elif action == "delete":
            await admin.async_delete_capture(msg.get("name") or "")
            await _log(admin, connection, "delete_capture", "capture_deleted", {"file": msg.get("name")})
        elif action == "open":
            opened = await admin.async_open_capture(msg.get("name") or "")
            result["sources"] = [s.info() for s in opened]
        elif action == "convert":
            result = await admin.async_convert_capture(msg.get("name") or "", msg.get("format") or "")
            await _log(admin, connection, "convert_capture", "capture_converted",
                       {"file": msg.get("name"), "target": result["name"], "frames": result["frames"]})
        else:
            admin.close_offline(msg.get("source") or "")
    except (HomeAssistantError, ValueError, OSError) as err:
        connection.send_error(msg["id"], "failed", str(err))
        return
    connection.send_result(msg["id"], result)


# ---- devices, templates, DBC files -----------------------------------------------------------
def _definition_error(connection: websocket_api.ActiveConnection, msg: dict, err: DefinitionError) -> None:
    connection.send_error(msg["id"], err.code, str(err))


def _device_args(admin: AdminHub, device) -> dict[str, Any]:
    return {"device": device.name, "port": _name(admin, device.interface)}


@_command
@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "woow_can/devices/save", vol.Required("device"): dict})
@websocket_api.async_response
async def ws_device_save(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    if (admin := _admin(hass, connection, msg)) is None:
        return
    existing = admin.devices.devices.get(msg["device"].get("id", ""))
    try:
        device = await admin.devices.async_save(msg["device"])
    except DefinitionError as err:
        _definition_error(connection, msg, err)
        return
    await _log(admin, connection, "save_device", "device_updated" if existing else "device_created",
               _device_args(admin, device), device_id=device.id, port_id=device.interface)
    connection.send_result(msg["id"], admin.devices.device_view(device))


@_command
@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "woow_can/devices/delete", vol.Required("device_id"): str})
@websocket_api.async_response
async def ws_device_delete(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    if (admin := _admin(hass, connection, msg)) is None:
        return
    device = await admin.devices.async_delete(msg["device_id"])
    if device is not None:
        await _log(admin, connection, "delete_device", "device_deleted", {"device": device.name},
                   device_id=device.id, port_id=device.interface)
    connection.send_result(msg["id"])


@_command
@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "woow_can/devices/signal",
    vol.Required("device_id"): str,
    vol.Required("message"): str,
    vol.Required("signal"): str,
    vol.Optional("adopted"): bool,
    vol.Optional("entity"): dict,
})
@websocket_api.async_response
async def ws_device_signal(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Adopt / drop one signal as an entity, or change its entity settings (min_interval, tolerance, timeout...)."""
    if (admin := _admin(hass, connection, msg)) is None:
        return
    try:
        device = await admin.async_set_signal(msg["device_id"], msg["message"], msg["signal"], msg.get("adopted"),
                                              msg.get("entity"))
    except DefinitionError as err:
        _definition_error(connection, msg, err)
        return
    await _log(admin, connection, "set_signal", "signal_changed",
               {"device": device.name, "signal": f"{msg['message']}.{msg['signal']}"}, device_id=device.id,
               port_id=device.interface)
    connection.send_result(msg["id"], admin.devices.device_view(device))


@_command
@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "woow_can/templates/create",
    vol.Required("template"): str,
    vol.Required("entry_id"): str,
    vol.Optional("name", default=""): str,
    vol.Optional("params", default={}): dict,
    vol.Optional("groups"): vol.Any(None, [str]),
})
@websocket_api.async_response
async def ws_template_create(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    if (admin := _admin(hass, connection, msg)) is None:
        return
    try:
        device = await admin.async_create_from_template(msg["template"], msg["entry_id"], msg["name"], msg["params"],
                                                        msg.get("groups"))
    except DefinitionError as err:
        _definition_error(connection, msg, err)
        return
    await _log(admin, connection, "create_from_template", "device_from_template",
               {**_device_args(admin, device), "template": device.template or "?"}, device_id=device.id,
               port_id=device.interface)
    connection.send_result(msg["id"], admin.devices.device_view(device))


@_command
@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "woow_can/decode",
    vol.Required("source"): str,
    vol.Required("raw"): int,
    vol.Required("data"): str,
})
@callback
def ws_decode(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    if (admin := _admin(hass, connection, msg)) is None:
        return
    try:
        data = bytes.fromhex(msg["data"])
        result = admin.decode(msg["source"], msg["raw"], data)
    except (ValueError, HomeAssistantError) as err:
        connection.send_error(msg["id"], "invalid", str(err))
        return
    connection.send_result(msg["id"], {"decoded": result})


@_command
@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "woow_can/dbc/control",
    vol.Required("action"): vol.In(["attach", "delete", "create_device"]),
    vol.Required("name"): str,
    vol.Optional("interfaces"): [str],
    vol.Optional("entry_id"): str,
    vol.Optional("device_name", default=""): str,
    vol.Optional("messages"): [str],
})
@websocket_api.async_response
async def ws_dbc_control(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    if (admin := _admin(hass, connection, msg)) is None:
        return
    action = msg["action"]
    result: dict[str, Any] = {}
    try:
        if action == "attach":
            await admin.databases.async_set_attach(msg["name"], msg.get("interfaces") or [])
            await _log(admin, connection, "attach_dbc", "dbc_attached",
                       {"file": msg["name"], "ports": ", ".join(_name(admin, e) if e != "*" else "*"
                                                                for e in msg.get("interfaces") or []) or "-"})
        elif action == "delete":
            await admin.databases.async_delete(msg["name"])
            await _log(admin, connection, "delete_dbc", "dbc_deleted", {"file": msg["name"]})
        else:
            device = await admin.async_create_from_dbc(msg["name"], msg.get("entry_id") or "", msg["device_name"],
                                                       msg.get("messages"))
            await _log(admin, connection, "create_from_dbc", "device_from_dbc",
                       {**_device_args(admin, device), "file": msg["name"]}, device_id=device.id,
                       port_id=device.interface)
            result = admin.devices.device_view(device)
    except DefinitionError as err:
        _definition_error(connection, msg, err)
        return
    admin.databases_changed()
    connection.send_result(msg["id"], result)


# ---- reverse engineering -----------------------------------------------------------------------
_SIGNAL_SPEC = vol.Schema({
    vol.Required("start"): vol.All(int, vol.Range(min=0, max=511)),
    vol.Required("length"): vol.All(int, vol.Range(min=1, max=64)),
    vol.Optional("byte_order", default="little"): vol.In(["little", "big"]),
    vol.Optional("signed", default=False): bool,
    vol.Optional("factor", default=1.0): vol.Coerce(float),
    vol.Optional("offset", default=0.0): vol.Coerce(float),
    vol.Optional("name", default="candidate"): str,
    vol.Optional("unit", default=""): str,
}, extra=vol.REMOVE_EXTRA)


def _signal(spec: dict[str, Any]) -> Signal:
    return Signal(name=spec["name"], start=spec["start"], length=spec["length"], byte_order=spec["byte_order"],
                  signed=spec["signed"], factor=spec["factor"], offset=spec["offset"], unit=spec["unit"])


@_command
@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "woow_can/analyze/bits",
    vol.Required("source"): str,
    vol.Required("key"): int,
    vol.Optional("seconds"): vol.Any(None, vol.Coerce(float)),
    vol.Optional("limit", default=2000): vol.All(int, vol.Range(min=2, max=20000)),
})
@websocket_api.async_response
async def ws_analyze_bits(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Per bit of one ID: changes and ones over its recent frames (the heat map)."""
    if (admin := _admin(hass, connection, msg)) is None:
        return
    try:
        result = await admin.async_bits(msg["source"], msg["key"], msg.get("seconds"), msg["limit"])
    except HomeAssistantError as err:
        connection.send_error(msg["id"], "failed", str(err))
        return
    connection.send_result(msg["id"], result)


@_command
@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "woow_can/analyze/try",
    vol.Required("source"): str,
    vol.Required("key"): int,
    vol.Required("signal"): dict,
    vol.Optional("seconds"): vol.Any(None, vol.Coerce(float)),
    vol.Optional("limit", default=2000): vol.All(int, vol.Range(min=1, max=20000)),
})
@websocket_api.async_response
async def ws_analyze_try(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """A candidate field decoded over the recent frames of one ID."""
    if (admin := _admin(hass, connection, msg)) is None:
        return
    try:
        sig = _signal(_SIGNAL_SPEC(msg["signal"]))
        result = await admin.async_try_signal(msg["source"], msg["key"], sig, msg.get("seconds"), msg["limit"])
    except (vol.Invalid, DefinitionError, HomeAssistantError) as err:
        connection.send_error(msg["id"], "failed", str(err))
        return
    connection.send_result(msg["id"], result)


@_command
@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "woow_can/analyze/find",
    vol.Required("source"): str,
    vol.Required("action"): vol.In(["start", "narrow", "clear", "status"]),
    vol.Optional("mode"): vol.In(list(analysis.MODES)),
    vol.Optional("value"): vol.Any(None, vol.Coerce(float)),
    vol.Optional("tolerance"): vol.Any(None, vol.All(vol.Coerce(float), vol.Range(min=0))),
    vol.Optional("limit", default=30): vol.All(int, vol.Range(min=1, max=500)),
})
@websocket_api.async_response
async def ws_analyze_find(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Find the field holding a value, step by step."""
    if (admin := _admin(hass, connection, msg)) is None:
        return
    try:
        result = await admin.async_find(msg["source"], msg["action"], msg.get("mode"), msg.get("value"),
                                        msg.get("tolerance"), msg["limit"])
    except HomeAssistantError as err:
        connection.send_error(msg["id"], "failed", str(err))
        return
    connection.send_result(msg["id"], result)


@_command
@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "woow_can/analyze/guided",
    vol.Required("source"): str,
    vol.Required("action"): vol.In(["start", "next", "finish", "cancel", "status"]),
    vol.Optional("label"): vol.Any(None, str),
    vol.Optional("limit", default=20): vol.All(int, vol.Range(min=1, max=200)),
})
@websocket_api.async_response
async def ws_analyze_guided(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Guided capture: idle, action, (idle again), then what differs."""
    if (admin := _admin(hass, connection, msg)) is None:
        return
    try:
        result = await admin.async_guided(msg["source"], msg["action"], msg.get("label"), msg["limit"])
    except HomeAssistantError as err:
        connection.send_error(msg["id"], "failed", str(err))
        return
    connection.send_result(msg["id"], result)


@_command
@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "woow_can/devices/add_signal",
    vol.Required("entry_id"): str,
    vol.Required("key"): int,
    vol.Required("signal"): dict,
    vol.Optional("device_id"): vol.Any(None, str),
    vol.Optional("device_name"): vol.Any(None, str),
    vol.Optional("message"): vol.Any(None, str),
    vol.Optional("adopt", default=True): bool,
})
@websocket_api.async_response
async def ws_device_add_signal(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """A field found with the analysis tools, into a device (new or existing) and adopted as an entity."""
    if (admin := _admin(hass, connection, msg)) is None:
        return
    try:
        spec = _SIGNAL_SPEC(msg["signal"])
        if not spec["name"].strip() or spec["name"] == "candidate":
            raise vol.Invalid("give the signal a name")
        signal = {k: spec[k] for k in ("name", "start", "length", "byte_order", "signed", "factor", "offset", "unit")}
        device, message = await admin.async_add_signal(msg["entry_id"], msg["key"], signal, msg.get("device_id"),
                                                       msg.get("device_name"), msg.get("message"), msg["adopt"])
    except DefinitionError as err:
        _definition_error(connection, msg, err)
        return
    except (vol.Invalid, HomeAssistantError) as err:
        connection.send_error(msg["id"], "failed", str(err))
        return
    await _log(admin, connection, "add_signal", "signal_added",
               {"device": device.name, "signal": f"{message}.{signal['name']}"}, device_id=device.id,
               port_id=device.interface)
    connection.send_result(msg["id"], admin.devices.device_view(device))
