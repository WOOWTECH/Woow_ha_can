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
from homeassistant.util import dt as dt_util

from .can_port import IdMatcher
from .capture import export_text, safe_name, trace_matcher
from .const import DOMAIN

MAX_UPLOAD = 100 * 1024 * 1024


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
        return web.FileResponse(path, headers={
            "Content-Disposition": f'attachment; filename="{os.path.basename(path)}"',
            "Content-Type": "text/plain; charset=us-ascii"})


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
    """The trace buffer of an interface (or opened capture) as a candump log."""

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
        match = trace_matcher(ids, request.query.get("direction") or None)
        snapshot = src.trace.snapshot()
        text = await request.app[KEY_HASS].async_add_executor_job(export_text, snapshot, src.port, match)
        filename = f"{src.port}_{dt_util.now().strftime('%Y%m%d-%H%M%S')}.log"
        return web.Response(text=text, content_type="text/plain", charset="us-ascii",
                            headers={"Content-Disposition": f'attachment; filename="{filename}"'})


def async_register(hass) -> None:
    if hass.data.setdefault(DOMAIN, {}).get("http_views"):
        return
    hass.http.register_view(CaptureFileView)
    hass.http.register_view(CaptureUploadView)
    hass.http.register_view(TraceExportView)
    hass.data[DOMAIN]["http_views"] = True
