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
from .signals import DefinitionError, Signal

if TYPE_CHECKING:
    from .admin import AdminHub
    from .hub import CanHub

_NOTE = vol.Optional("note", default="")  # every change can say why; shown in the activity log
_LIMIT = vol.All(vol.Coerce(int), vol.Range(min=1, max=2000))
_WAIT = vol.All(vol.Coerce(int), vol.Range(min=0, max=60000))
ADMIN_SERVICES = {SERVICE_SEND, "save_periodic", "control_periodic", "capture", "clear_monitor", "create_from_template",
                  "save_device", "delete_device", "set_signal", "import_dbc", "attach_dbc", "create_from_dbc"}
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
            "capture (admin): record an interface to a candump log file in the config folder's woow_can/captures.",
            "Devices turn signals into Home Assistant entities. Known equipment: list_templates, then "
            "create_from_template {template, interface, params}; without groups it includes the protocol groups "
            "whose IDs the interface has seen. DBC files: import_dbc, attach_dbc (names and decodes frames), "
            "create_from_dbc. Unknown frames: test_signal tries a bit field on recent frames; save_device stores "
            "a definition (get_device shows the shape); set_signal adopts a signal or tunes its entity.",
            "decode_frame shows what the definitions make of one frame; list_devices / get_device show current values.",
            "Give every change a short `note`: people read it in the panel's activity log.",
        ],
        "device_definition": {
            "name": "unique", "interface": "interface name or config entry id",
            "messages": "[{name, can_id (hex text, 1-3 digits = 11-bit) or pgn (J1939 / NMEA 2000, decimal), "
                        "source (J1939 source address), length, cycle_ms (timeout = max(3 cycles, 5 s)), "
                        "filters [{byte, value}], transport (j1939_tp | n2k_fast), signals}]",
            "signals": "[{name, start, length, byte_order little (Intel, start = LSB) | big (Motorola, start = MSB, "
                       "DBC numbering), signed, kind int | float | ascii, factor, offset, unit, values {raw: label}, "
                       "invalid j1939 | n2k | sma | [raw values], mux_by, mux_values, derive {op: product | sum | "
                       "difference | any | nonzero | present, of: [signal names]}, entity}]",
            "entity": "{name, key, platform sensor | binary_sensor, device_class, state_class, unit, precision, "
                      "enabled, min_interval (s), tolerance, timeout (s), on [raw], off [raw], format hex, icon}",
        },
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

    # ---- devices, templates, DBC (0.3) ------------------------------------------------------
    def _bad(err: DefinitionError) -> ServiceValidationError:
        return _invalid("bad_definition", code=err.code, detail=str(err))

    def _device(admin: AdminHub, ref: str):
        device = admin.devices.resolve(ref)
        if device is None:
            raise _invalid("unknown_device", device=ref,
                           devices=", ".join(sorted(d.name for d in admin.devices.devices.values())) or "-")
        return device

    def _device_out(admin: AdminHub, device, definition: bool) -> dict[str, Any]:
        view = admin.devices.device_view(device, with_definition=definition)
        view["interface_name"] = _hubs(hass)[device.interface].name if device.interface in _hubs(hass) else None
        return view

    async def s_list_templates(call: ServiceCall) -> ServiceResponse:
        admin = _need_admin(hass)
        return {"templates": admin.templates.summaries(hass.config.language or "en", call.data.get("category"))}

    async def s_create_from_template(call: ServiceCall) -> ServiceResponse:
        admin = _need_admin(hass)
        hub = resolve_interface(hass, call.data["interface"])
        try:
            device = await admin.async_create_from_template(call.data["template"], hub.entry.entry_id,
                                                            call.data["name"], call.data["params"],
                                                            call.data.get("groups"))
        except DefinitionError as err:
            raise _bad(err) from err
        await record(call, "create_from_template", "device_from_template",
                     {"device": device.name, "port": hub.name, "template": device.template or "?"},
                     device_id=device.id, port_id=hub.entry.entry_id)
        return {"device": _device_out(admin, device, False)} if call.return_response else None

    async def s_list_devices(call: ServiceCall) -> ServiceResponse:
        admin = _need_admin(hass)
        entry_id = resolve_interface(hass, call.data["interface"]).entry.entry_id if call.data.get("interface") else None
        return {"devices": [_device_out(admin, d, False) for d in admin.devices.devices.values()
                            if entry_id is None or d.interface == entry_id]}

    async def s_get_device(call: ServiceCall) -> ServiceResponse:
        admin = _need_admin(hass)
        return {"device": _device_out(admin, _device(admin, call.data["device"]), True)}

    async def s_save_device(call: ServiceCall) -> ServiceResponse:
        admin = _need_admin(hass)
        raw = dict(call.data["device"])
        if raw.get("interface"):
            raw["interface"] = resolve_interface(hass, str(raw["interface"])).entry.entry_id
        if not raw.get("id") and raw.get("name"):  # the same name updates that device
            same = admin.devices.resolve(str(raw["name"]))
            if same is not None:
                raw["id"] = same.id
        existing = raw.get("id") in admin.devices.devices
        try:
            device = await admin.devices.async_save(raw)
        except DefinitionError as err:
            raise _bad(err) from err
        await record(call, "save_device", "device_updated" if existing else "device_created",
                     {"device": device.name, "port": _hubs(hass)[device.interface].name
                      if device.interface in _hubs(hass) else "?"}, device_id=device.id, port_id=device.interface)
        return {"device": _device_out(admin, device, True)} if call.return_response else None

    async def s_delete_device(call: ServiceCall) -> ServiceResponse:
        admin = _need_admin(hass)
        device = _device(admin, call.data["device"])
        await admin.devices.async_delete(device.id)
        await record(call, "delete_device", "device_deleted", {"device": device.name}, device_id=device.id,
                     port_id=device.interface)
        return {"ok": True} if call.return_response else None

    async def s_set_signal(call: ServiceCall) -> ServiceResponse:
        admin = _need_admin(hass)
        device = _device(admin, call.data["device"])
        entity = {k: call.data[k] for k in ("min_interval", "tolerance", "timeout", "enabled", "name", "device_class",
                                           "unit", "precision") if k in call.data}
        try:
            device = await admin.async_set_signal(device.id, call.data["message"], call.data["signal"],
                                                  call.data.get("adopted"), entity or None)
        except DefinitionError as err:
            raise _bad(err) from err
        await record(call, "set_signal", "signal_changed",
                     {"device": device.name, "signal": f"{call.data['message']}.{call.data['signal']}"},
                     device_id=device.id, port_id=device.interface)
        return {"device": _device_out(admin, device, False)} if call.return_response else None

    async def s_decode_frame(call: ServiceCall) -> ServiceResponse:
        admin = _need_admin(hass)
        hub = resolve_interface(hass, call.data["interface"])
        try:
            frame = CanFrame.parse(call.data["frame"])
        except ValueError as err:
            raise _invalid("bad_frame", error=str(err)) from err
        return {"frame": str(frame), "decoded": admin.decode(hub.entry.entry_id, frame.raw_id, frame.data)}

    async def s_test_signal(call: ServiceCall) -> ServiceResponse:
        """Try a candidate bit field on the recent frames of one ID (reverse engineering)."""
        hub = resolve_interface(hass, call.data["interface"])
        try:
            can_id, extended = parse_id(call.data["can_id"])
            sig = Signal(name="candidate", start=call.data["start"], length=call.data["length"],
                         byte_order=call.data["byte_order"], signed=call.data["signed"], factor=call.data["factor"],
                         offset=call.data["offset"])
        except (ValueError, DefinitionError) as err:
            raise _invalid("bad_ids", error=str(err)) from err
        raw_id = can_id | (0x80000000 if extended else 0)
        match = trace_matcher(lambda raw: raw & 0xDFFFFFFF == raw_id, None, errors=False)
        snapshot = hub.trace.snapshot()
        page = await hass.async_add_executor_job(snapshot.page, None, call.data["limit"], match,
                                                 time.time() - call.data["seconds"])
        series = [(f.t, sig.decode_raw(f.data)[1]) for f in reversed(page["frames"])]
        numbers = [v for _, v in series if isinstance(v, (int, float))]
        changes = sum(1 for (_, a), (_, b) in zip(series, series[1:]) if a != b)
        return {"interface": hub.name, "frames": len(series), "distinct_values": len({v for _, v in series}),
                "changes": changes, "min": min(numbers) if numbers else None, "max": max(numbers) if numbers else None,
                "first": series[0][1] if series else None, "last": series[-1][1] if series else None,
                "samples": [{"time": round(t, 3), "value": v} for t, v in series[-20:]]}

    async def s_import_dbc(call: ServiceCall) -> ServiceResponse:
        admin = _need_admin(hass)
        interfaces = [resolve_interface(hass, ref).entry.entry_id if ref != "*" else "*"
                      for ref in call.data["attach"]]
        try:
            summary = await admin.databases.async_import(call.data["name"], call.data["content"].encode("utf-8"),
                                                         interfaces)
        except DefinitionError as err:
            raise _bad(err) from err
        await record(call, "import_dbc", "dbc_imported", {"file": summary["name"], "messages": summary["messages"]})
        admin.databases_changed()
        return {"database": summary} if call.return_response else None

    async def s_list_databases(call: ServiceCall) -> ServiceResponse:
        return {"databases": _need_admin(hass).databases.summaries()}

    async def s_attach_dbc(call: ServiceCall) -> ServiceResponse:
        admin = _need_admin(hass)
        name = admin.databases.resolve(call.data["name"])
        if name is None:
            raise _invalid("bad_definition", code="unknown_dbc", detail=call.data["name"])
        interfaces = [resolve_interface(hass, ref).entry.entry_id if ref != "*" else "*"
                      for ref in call.data["interfaces"]]
        await admin.databases.async_set_attach(name, interfaces)
        await record(call, "attach_dbc", "dbc_attached", {"file": name, "ports": ", ".join(call.data["interfaces"]) or "-"})
        admin.databases_changed()
        return {"database": admin.databases.summary(name)} if call.return_response else None

    async def s_create_from_dbc(call: ServiceCall) -> ServiceResponse:
        admin = _need_admin(hass)
        hub = resolve_interface(hass, call.data["interface"])
        try:
            device = await admin.async_create_from_dbc(call.data["dbc"], hub.entry.entry_id, call.data["name"],
                                                       call.data.get("messages"))
        except DefinitionError as err:
            raise _bad(err) from err
        await record(call, "create_from_dbc", "device_from_dbc",
                     {"device": device.name, "port": hub.name, "file": call.data["dbc"]}, device_id=device.id,
                     port_id=hub.entry.entry_id)
        return {"device": _device_out(admin, device, False)} if call.return_response else None

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
    register("list_templates", s_list_templates, {vol.Optional("category"): cv.string}, SupportsResponse.ONLY)
    register("create_from_template", s_create_from_template, {
        vol.Required("template"): cv.string, vol.Required("interface"): cv.string,
        vol.Optional("name", default=""): cv.string, vol.Optional("params", default={}): dict,
        vol.Optional("groups"): [cv.string], _NOTE: cv.string}, SupportsResponse.OPTIONAL)
    register("list_devices", s_list_devices, {vol.Optional("interface"): cv.string}, SupportsResponse.ONLY)
    register("get_device", s_get_device, {vol.Required("device"): cv.string}, SupportsResponse.ONLY)
    register("save_device", s_save_device, {vol.Required("device"): dict, _NOTE: cv.string}, SupportsResponse.OPTIONAL)
    register("delete_device", s_delete_device, {vol.Required("device"): cv.string, _NOTE: cv.string},
             SupportsResponse.OPTIONAL)
    register("set_signal", s_set_signal, {
        vol.Required("device"): cv.string, vol.Required("message"): cv.string, vol.Required("signal"): cv.string,
        vol.Optional("adopted"): cv.boolean, vol.Optional("enabled"): cv.boolean,
        vol.Optional("min_interval"): vol.All(vol.Coerce(float), vol.Range(min=0, max=3600)),
        vol.Optional("tolerance"): vol.All(vol.Coerce(float), vol.Range(min=0)),
        vol.Optional("timeout"): vol.Any(None, vol.All(vol.Coerce(float), vol.Range(min=0.1, max=86400))),
        vol.Optional("name"): cv.string, vol.Optional("device_class"): cv.string, vol.Optional("unit"): cv.string,
        vol.Optional("precision"): vol.All(vol.Coerce(int), vol.Range(min=0, max=12)), _NOTE: cv.string},
        SupportsResponse.OPTIONAL)
    register("decode_frame", s_decode_frame, {vol.Required("interface"): cv.string, vol.Required("frame"): cv.string},
             SupportsResponse.ONLY)
    register("test_signal", s_test_signal, {
        vol.Required("interface"): cv.string, vol.Required("can_id"): cv.string,
        vol.Required("start"): vol.All(vol.Coerce(int), vol.Range(min=0, max=511)),
        vol.Required("length"): vol.All(vol.Coerce(int), vol.Range(min=1, max=64)),
        vol.Optional("byte_order", default="little"): vol.In(["little", "big"]),
        vol.Optional("signed", default=False): cv.boolean, vol.Optional("factor", default=1.0): vol.Coerce(float),
        vol.Optional("offset", default=0.0): vol.Coerce(float),
        vol.Optional("seconds", default=60.0): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=86400)),
        vol.Optional("limit", default=2000): _LIMIT}, SupportsResponse.ONLY)
    register("import_dbc", s_import_dbc, {vol.Required("name"): cv.string, vol.Required("content"): cv.string,
                                          vol.Optional("attach", default=[]): [cv.string], _NOTE: cv.string},
             SupportsResponse.OPTIONAL)
    register("list_databases", s_list_databases, {}, SupportsResponse.ONLY)
    register("attach_dbc", s_attach_dbc, {vol.Required("name"): cv.string, vol.Required("interfaces"): [cv.string],
                                          _NOTE: cv.string}, SupportsResponse.OPTIONAL)
    register("create_from_dbc", s_create_from_dbc, {
        vol.Required("dbc"): cv.string, vol.Required("interface"): cv.string, vol.Optional("name", default=""): cv.string,
        vol.Optional("messages"): [cv.string], _NOTE: cv.string}, SupportsResponse.OPTIONAL)
