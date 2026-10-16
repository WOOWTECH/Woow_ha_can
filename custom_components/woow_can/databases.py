"""Imported DBC files: kept in <config>/woow_can/dbc, attached to interfaces to name and decode frames.

An attached file names the monitor's rows and decodes them in the panel; making a device from some of its
messages copies those definitions into the device (entities come from devices, not from files).
"""

from __future__ import annotations

import logging
import os
import re
import time
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from . import dbc
from .const import DOMAIN
from .signals import DefinitionError, Message

_LOGGER = logging.getLogger(__name__)
DBC_DIR = "woow_can/dbc"
SAFE = re.compile(r"^[\w.\-]{1,120}\.dbc$", re.IGNORECASE)
ALL = "*"


def safe_dbc_name(name: str) -> str:
    name = name.strip()
    if not name.lower().endswith(".dbc"):
        name += ".dbc"
    if not SAFE.match(name) or name.startswith("."):
        raise DefinitionError("bad_file_name", name=name)
    return name


class DatabaseLibrary:
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.folder = hass.config.path(DBC_DIR)
        self._store: Store[dict[str, Any]] = Store(hass, 1, f"{DOMAIN}.databases")
        self.attach: dict[str, list[str]] = {}  # file -> interface entry ids ("*" = all)
        self.files: dict[str, dict[str, Any]] = {}  # file -> {"report", "definitions", "messages", "imported"}
        self.version = 0  # bumps on every change (callers cache by it)

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        self.attach = {k: list(v) for k, v in (data.get("attach") or {}).items()}
        self.files = await self.hass.async_add_executor_job(self._read_all)
        self.version += 1

    def _read_all(self) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        if not os.path.isdir(self.folder):
            return out
        for name in sorted(os.listdir(self.folder)):
            if not SAFE.match(name):
                continue
            try:
                with open(os.path.join(self.folder, name), "rb") as fh:
                    out[name] = self._compile(dbc.parse(fh.read()), os.path.getmtime(fh.name))
            except OSError as err:
                _LOGGER.warning("Cannot read %s: %s", name, err)
        return out

    @staticmethod
    def _compile(parsed: dbc.DbcFile, imported: float) -> dict[str, Any]:
        messages = []
        for definition in parsed.messages:
            try:
                messages.append(Message.from_dict(definition))
            except DefinitionError:
                continue
        return {"report": parsed.report(), "definitions": parsed.messages, "messages": messages, "imported": imported}

    async def _async_save(self) -> None:
        await self._store.async_save({"attach": self.attach})

    async def async_import(self, name: str, content: bytes, interfaces: list[str] | None = None) -> dict[str, Any]:
        name = safe_dbc_name(name)
        parsed = await self.hass.async_add_executor_job(dbc.parse, content)
        if not parsed.messages:
            raise DefinitionError("no_messages_in_dbc", name=name, warnings="; ".join(parsed.warnings[:3]))

        def write() -> None:
            os.makedirs(self.folder, 0o755, exist_ok=True)
            with open(os.path.join(self.folder, name), "wb") as fh:
                fh.write(content)

        await self.hass.async_add_executor_job(write)
        self.files[name] = self._compile(parsed, time.time())
        if interfaces is not None:
            self.attach[name] = list(interfaces)
        self.attach.setdefault(name, [])
        await self._async_save()
        self.version += 1
        return self.summary(name)

    async def async_set_attach(self, name: str, interfaces: list[str]) -> None:
        if name not in self.files:
            raise DefinitionError("unknown_dbc", name=name)
        self.attach[name] = list(interfaces)
        await self._async_save()
        self.version += 1

    async def async_delete(self, name: str) -> None:
        if name not in self.files:
            raise DefinitionError("unknown_dbc", name=name)
        self.files.pop(name)
        self.attach.pop(name, None)
        path = os.path.join(self.folder, name)
        await self.hass.async_add_executor_job(lambda: os.path.exists(path) and os.remove(path))
        await self._async_save()
        self.version += 1

    def summary(self, name: str) -> dict[str, Any]:
        item = self.files[name]
        return {"name": name, **item["report"], "attached": self.attach.get(name, []), "imported": item["imported"],
                "message_names": [m["name"] for m in item["definitions"]]}

    def summaries(self) -> list[dict[str, Any]]:
        return [self.summary(n) for n in self.files]

    def resolve(self, ref: str) -> str | None:
        want = ref.strip().casefold()
        for name in self.files:
            if want in (name.casefold(), name.casefold().removesuffix(".dbc")):
                return name
        return None

    def messages_for(self, entry_id: str | None) -> list[tuple[str, Message]]:
        out = []
        for name, item in self.files.items():
            attached = self.attach.get(name, [])
            if ALL in attached or (entry_id is not None and entry_id in attached):
                out.extend((name, m) for m in item["messages"])
        return out

    def definitions(self, name: str, wanted: list[str] | None) -> list[dict[str, Any]]:
        item = self.files.get(name)
        if item is None:
            raise DefinitionError("unknown_dbc", name=name)
        defs = item["definitions"]
        if not wanted:
            return list(defs)
        by_name = {d["name"]: d for d in defs}
        missing = [w for w in wanted if w not in by_name]
        if missing:
            raise DefinitionError("unknown_message", dbc=name, message=", ".join(missing))
        return [by_name[w] for w in wanted]
