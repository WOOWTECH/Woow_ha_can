"""HTTP views for files: capture downloads and uploads, trace exports (admin users only).

Downloads are plain GETs, so the panel can open them through a signed path (auth/sign_path)
and let the browser save the file.
"""

from __future__ import annotations

from http import HTTPStatus
import os

from aiohttp import web

from homeassistant.components.http import KEY_HASS, KEY_HASS_USER, HomeAssistantView
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util, slugify

from .can_port import IdMatcher
from .capture import export_frames, safe_name, trace_matcher
from . import dbc, formats
from .const import DOMAIN
from .signals import DefinitionError

MAX_UPLOAD = 100 * 1024 * 1024


def safe_port(port: str) -> str:
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in port) or "can"


def _admin(request: web.Request):
    user = request.get(KEY_HASS_USER)
    if user is None or not user.is_admin:
        raise web.HTTPForbidden(text="admin only")
    admin = request.app[KEY_HASS].data.get(DOMAIN, {}).get("admin")
    if admin is None:
        raise web.HTTPNotFound(text="the WOOW CAN panel entry is not loaded")
    return admin


class CaptureFileView(HomeAssistantView):
    url = "/api/woow_can/captures/{name}"
    name = "api:woow_can:capture"
    requires_auth = True

    async def get(self, request: web.Request, name: str) -> web.StreamResponse:
        admin = _admin(request)
        try:
            path = admin._capture_path(name)  # noqa: SLF001
        except ValueError as err:
            raise web.HTTPBadRequest(text=str(err)) from err
        if not os.path.isfile(path):
            raise web.HTTPNotFound(text="no such capture")
        ext = os.path.splitext(path)[1].lstrip(".").lower()
        content_type = formats.CONTENT_TYPES.get(ext, "text/plain")
        return web.FileResponse(path, headers={
            "Content-Disposition": f'attachment; filename="{os.path.basename(path)}"',
            "Content-Type": content_type if ext == "pcap" else f"{content_type}; charset=us-ascii"})


class CaptureUploadView(HomeAssistantView):
    url = "/api/woow_can/captures"
    name = "api:woow_can:capture_upload"
    requires_auth = True

    async def post(self, request: web.Request) -> web.Response:
        admin = _admin(request)
        if (request.content_length or 0) > MAX_UPLOAD:
            raise web.HTTPRequestEntityTooLarge(max_size=MAX_UPLOAD, actual_size=request.content_length or 0)
        data = await request.read()
        if len(data) > MAX_UPLOAD:
            raise web.HTTPRequestEntityTooLarge(max_size=MAX_UPLOAD, actual_size=len(data))
        try:
            name = await admin.async_save_upload(safe_name(request.query.get("name", "upload.log")), data)
        except ValueError as err:
            raise web.HTTPBadRequest(text=str(err)) from err
        await admin.activity.async_record("panel", "upload_capture", "capture_uploaded", {"file": name},
                                          user=request[KEY_HASS_USER].name)
        return self.json({"name": name}, HTTPStatus.CREATED)


class TraceExportView(HomeAssistantView):
    """The trace buffer of an interface (or opened capture) as a file: ?format=log (default), asc, csv, pcap."""

    url = "/api/woow_can/export/{source}"
    name = "api:woow_can:export"
    requires_auth = True

    async def get(self, request: web.Request, source: str) -> web.Response:
        admin = _admin(request)
        try:
            src = admin.source(source)
            ids = IdMatcher(request.query.get("ids", "")) if request.query.get("ids") else None
        except (HomeAssistantError, ValueError) as err:
            raise web.HTTPBadRequest(text=str(err)) from err
        fmt = request.query.get("format", "log")
        if fmt not in formats.WRITE_FORMATS:
            raise web.HTTPBadRequest(text=f"format: one of {', '.join(formats.WRITE_FORMATS)}")
        match = trace_matcher(ids, request.query.get("direction") or None)
        snapshot = src.trace.snapshot()

        def build() -> bytes:
            return formats.write(fmt, {src.port: export_frames(snapshot, match)})

        body = await request.app[KEY_HASS].async_add_executor_job(build)
        filename = f"{safe_port(src.port)}_{dt_util.now().strftime('%Y%m%d-%H%M%S')}.{fmt}"
        return web.Response(body=body, content_type=formats.CONTENT_TYPES[fmt],
                            charset=None if fmt == "pcap" else "us-ascii",
                            headers={"Content-Disposition": f'attachment; filename="{filename}"'})


class DbcUploadView(HomeAssistantView):
    """POST a DBC file: /api/woow_can/dbc?name=car.dbc&attach=<entry id>,<entry id> (or *)."""

    url = "/api/woow_can/dbc"
    name = "api:woow_can:dbc_upload"
    requires_auth = True

    async def post(self, request: web.Request) -> web.Response:
        admin = _admin(request)
        data = await request.read()
        if len(data) > MAX_UPLOAD:
            raise web.HTTPRequestEntityTooLarge(max_size=MAX_UPLOAD, actual_size=len(data))
        attach = [a for a in request.query.get("attach", "").split(",") if a.strip()] or None
        try:
            summary = await admin.databases.async_import(request.query.get("name", "upload.dbc"), data, attach)
        except DefinitionError as err:
            raise web.HTTPBadRequest(text=str(err)) from err
        await admin.activity.async_record("panel", "import_dbc", "dbc_imported",
                                          {"file": summary["name"], "messages": summary["messages"]},
                                          user=request[KEY_HASS_USER].name)
        admin.databases_changed()
        return self.json(summary, HTTPStatus.CREATED)


class DbcFileView(HomeAssistantView):
    url = "/api/woow_can/dbc/{name}"
    name = "api:woow_can:dbc_file"
    requires_auth = True

    async def get(self, request: web.Request, name: str) -> web.StreamResponse:
        admin = _admin(request)
        found = admin.databases.resolve(name)
        if found is None:
            raise web.HTTPNotFound(text="no such DBC file")
        return web.FileResponse(os.path.join(admin.databases.folder, found), headers={
            "Content-Disposition": f'attachment; filename="{found}"', "Content-Type": "text/plain"})


class DeviceDbcView(HomeAssistantView):
    """A device's messages as a DBC file (to open in SavvyCAN, cabana, CANalyzer...)."""

    url = "/api/woow_can/devices/{device_id}/dbc"
    name = "api:woow_can:device_dbc"
    requires_auth = True

    async def get(self, request: web.Request, device_id: str) -> web.Response:
        admin = _admin(request)
        device = admin.devices.resolve(device_id)
        if device is None:
            raise web.HTTPNotFound(text="no such device")
        text = dbc.dump(device.messages, comment=f"WOOW CAN device {device.name}")
        filename = f"{slugify(device.name) or device.id}.dbc"
        return web.Response(text=text, content_type="text/plain", charset="utf-8",
                            headers={"Content-Disposition": f'attachment; filename="{filename}"'})


def async_register(hass) -> None:
    if hass.data.setdefault(DOMAIN, {}).get("http_views"):
        return
    hass.http.register_view(CaptureFileView)
    hass.http.register_view(CaptureUploadView)
    hass.http.register_view(TraceExportView)
    hass.http.register_view(DbcUploadView)
    hass.http.register_view(DbcFileView)
    hass.http.register_view(DeviceDbcView)
    hass.data[DOMAIN]["http_views"] = True
