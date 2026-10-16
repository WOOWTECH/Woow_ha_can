"""Device templates: built-in ones (templates/*.json) and the user's own (<config>/woow_can/templates/*.json).

A template is a device definition with parameters (a node ID, a source address, an instance) and optional
message groups (protocol families: Pylontech, SMA, Victron extensions). Every template names its sources,
license, what it was verified against and how confident the facts are. Creating a device with groups left
open picks the groups whose IDs the interface's monitor has already seen.
"""

from __future__ import annotations

import copy
import json
import logging
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant

from .signals import DefinitionError, Message

_LOGGER = logging.getLogger(__name__)
BUILTIN = Path(__file__).parent / "templates"
LOCAL_DIR = "woow_can/templates"
SUMMARY_KEYS = ("id", "category", "bitrate", "transmits", "source", "license", "verified", "confidence",
                "manufacturer", "model")


def text(value: Any, language: str) -> Any:
    """{"en": .., "zh-Hant": ..} in the user's language; anything else unchanged."""
    if isinstance(value, dict) and ("en" in value or "zh-Hant" in value):
        if language.lower().startswith("zh"):
            return value.get("zh-Hant") or value.get("en")
        return value.get("en") or value.get("zh-Hant")
    return value


def defaults(template: dict[str, Any]) -> dict[str, Any]:
    return {p["key"]: p.get("default") for p in template.get("params") or []}


def validate(template: dict[str, Any]) -> None:
    """Every message compiles with the default parameters (raises DefinitionError)."""
    if not template.get("id") or not template.get("messages"):
        raise DefinitionError("bad_template", template=template.get("id", "?"))
    params = defaults(template)
    group_ids = {g["id"] for g in template.get("groups") or []}
    for msg in template["messages"]:
        if msg.get("group") and msg["group"] not in group_ids:
            raise DefinitionError("unknown_group", template=template["id"], group=msg["group"])
        Message.from_dict(msg, params)


class TemplateLibrary:
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.templates: dict[str, dict[str, Any]] = {}
        self.origin: dict[str, str] = {}  # id -> "builtin" / "local"

    async def async_load(self) -> None:
        local = Path(self.hass.config.path(LOCAL_DIR))
        found = await self.hass.async_add_executor_job(self._read, [(BUILTIN, "builtin"), (local, "local")])
        self.templates = {t["id"]: t for t, _ in found}
        self.origin = {t["id"]: origin for t, origin in found}

    @staticmethod
    def _read(folders: list[tuple[Path, str]]) -> list[tuple[dict[str, Any], str]]:
        out: list[tuple[dict[str, Any], str]] = []
        for folder, origin in folders:
            if not folder.is_dir():
                continue
            for path in sorted(folder.glob("*.json")):
                try:
                    template = json.loads(path.read_text(encoding="utf-8"))
                    validate(template)
                except (OSError, ValueError, KeyError, TypeError) as err:
                    _LOGGER.warning("Skipping template %s: %s", path.name, err)
                    continue
                out = [(t, o) for t, o in out if t["id"] != template["id"]]  # a local one overrides
                out.append((template, origin))
        return out

    def summaries(self, language: str, category: str | None = None) -> list[dict[str, Any]]:
        out = []
        for tid, t in self.templates.items():
            if category and t.get("category") != category:
                continue
            item = {k: t.get(k) for k in SUMMARY_KEYS}
            item.update(
                name=text(t.get("name"), language),
                description=text(t.get("description"), language),
                notes=text(t.get("notes"), language),
                default_name=text(t.get("default_name"), language),
                params=[{"key": p["key"], "default": p.get("default"), "description": text(p.get("description"), language)}
                        for p in t.get("params") or []],
                groups=[{"id": g["id"], "name": text(g.get("name"), language)} for g in t.get("groups") or []],
                messages=[{"name": m["name"], "id": m.get("can_id") or f"PGN {m.get('pgn')}", "group": m.get("group"),
                           "entities": sum(1 for s in m.get("signals", []) if s.get("entity"))}
                          for m in t["messages"]],
                origin=self.origin.get(tid, "builtin"),
            )
            out.append(item)
        return out

    def get(self, ref: str) -> dict[str, Any] | None:
        want = ref.strip().casefold()
        for tid, t in self.templates.items():
            if want in (tid.casefold(), str(text(t.get("name"), "en")).casefold(),
                        str(text(t.get("name"), "zh")).casefold()):
                return t
        return None

    def instantiate(self, template: dict[str, Any], interface: str, name: str, params: dict[str, Any] | None,
                    groups: list[str] | None, language: str, seen: set[int] | None = None) -> dict[str, Any]:
        """A device definition from a template. groups=None: the groups whose IDs `seen` contains."""
        values = defaults(template)
        for key, value in (params or {}).items():
            if key not in values:
                raise DefinitionError("unknown_param", template=template["id"], param=key,
                                      params=", ".join(values) or "-")
            values[key] = value
        group_ids = [g["id"] for g in template.get("groups") or []]
        if groups is None:
            chosen = set()
            for msg in template["messages"]:
                group = msg.get("group")
                if group and group not in chosen and seen and any(
                        Message.from_dict(msg, values).matches(raw) for raw in seen):
                    chosen.add(group)
        else:
            unknown = [g for g in groups if g not in group_ids]
            if unknown:
                raise DefinitionError("unknown_group", template=template["id"], group=", ".join(unknown),
                                      groups=", ".join(group_ids) or "-")
            chosen = set(groups)
        messages = []
        for msg in template["messages"]:
            if msg.get("group") and msg["group"] not in chosen:
                continue
            msg = copy.deepcopy(msg)
            msg.pop("group", None)
            messages.append(msg)
        return {
            "name": name.strip() or text(template.get("default_name"), language) or template["id"],
            "interface": interface,
            "template": template["id"],
            "params": values,
            "groups": [g for g in group_ids if g in chosen],
            "manufacturer": template.get("manufacturer", ""),
            "model": template.get("model", ""),
            "source": "template",
            "messages": messages,
        }
