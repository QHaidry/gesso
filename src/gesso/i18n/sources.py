"""Where translations come from.

A source yields a catalog — a plain nested ``dict`` — for a given language.
Drawing the boundary here is what lets the rest of the layer stay ignorant of
the filesystem: the :class:`~gesso.i18n.translator.Translator` merges catalogs
and never cares whether one came from a directory, from memory, or (later) from
gettext.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping

__all__ = ["DirectorySource", "MappingSource"]


def _read_json(path: Path) -> Dict[str, Any]:
    """Load a JSON catalog, tolerating anything that goes wrong.

    A missing, unreadable or malformed translation file degrades the
    application to the fallback language rather than preventing it from
    starting. Translations are not worth a traceback.
    """
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


@dataclass(frozen=True)
class DirectorySource:
    """A directory of ``<language>.json`` catalogs.

    Typically the application's own ``locales/`` directory, or the user's
    override directory under ``$XDG_CONFIG_HOME``.
    """

    path: Path
    name: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", Path(self.path))

    def catalog(self, language: str) -> Dict[str, Any]:
        """The catalog for *language*, or ``{}`` if there is not one."""
        if not language:
            return {}
        return _read_json(self.path / f"{language}.json")

    def languages(self) -> List[str]:
        """Languages this source provides, sorted."""
        if not self.path.is_dir():
            return []
        return sorted(entry.stem for entry in self.path.glob("*.json"))

    def __str__(self) -> str:
        return self.name or str(self.path)


@dataclass(frozen=True)
class MappingSource:
    """An in-memory catalog, keyed by language.

    Useful for tests, and for applications that embed a handful of strings
    rather than shipping a directory of files.
    """

    catalogs: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    name: str = "<memory>"

    def catalog(self, language: str) -> Dict[str, Any]:
        return dict(self.catalogs.get(language, {}))

    def languages(self) -> List[str]:
        return sorted(self.catalogs)

    def __str__(self) -> str:
        return self.name
