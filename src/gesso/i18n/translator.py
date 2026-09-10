"""The Translator: merging catalogs and looking translations up.

Sources are merged in order with later ones winning, and the result is layered
over the fallback language. That gives three levels of override with no special
cases:

1. the framework's own strings, in the reserved ``gesso.*`` domain,
2. the application's built-in strings,
3. the user's overrides on disk.

A key missing from the selected language falls back to the fallback language. A
key missing everywhere returns the key itself — which is visible in the UI and
findable with a grep, exactly what you want while developing.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence

from .locale import DEFAULT_LANGUAGE, detect_language, normalize_lang
from .sources import DirectorySource

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..core.app import AppContext

__all__ = ["Translator", "FRAMEWORK_LOCALES_DIR"]

#: The framework's own catalogs, shipped inside the package.
FRAMEWORK_LOCALES_DIR = Path(__file__).parent / "locales"


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge *override* onto *base*, returning a new dict.

    Every container in the result is a fresh copy. That matters: sources hand
    out their own nested dicts, so merging by reference would let a later
    mutation — including through ``catalogs()`` — reach back into a source's
    data.
    """
    result = {key: copy.deepcopy(value) for key, value in base.items()}
    for key, value in override.items():
        existing = result.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            result[key] = _deep_merge(existing, value)
        else:
            result[key] = copy.deepcopy(value)
    return result


class Translator:
    """Loads and looks up translations for one language.

    Build one per application (or per test) and pass it around; Gesso does not
    keep a process-wide instance, because a hidden global is exactly the kind
    of thing that makes an application hard to test.
    """

    def __init__(
        self,
        sources: Sequence[Any] = (),
        *,
        language: Optional[str] = None,
        fallback: str = DEFAULT_LANGUAGE,
        include_framework: bool = True,
        framework_dir: Optional[Path] = None,
    ) -> None:
        self._sources: List[Any] = []
        if include_framework:
            self._sources.append(
                DirectorySource(framework_dir or FRAMEWORK_LOCALES_DIR, name="gesso")
            )
        self._sources.extend(sources)

        self._fallback = normalize_lang(fallback) or DEFAULT_LANGUAGE
        self._language = normalize_lang(language) if language else detect_language()
        self._language = self._language or self._fallback
        self._strings: Dict[str, Any] = {}
        self._reload()

    # -- construction --------------------------------------------------
    @classmethod
    def for_app(
        cls,
        context: "AppContext",
        *,
        language: Optional[str] = None,
        locale_dir: Optional[Path] = None,
        source: Optional[Any] = None,
        fallback: str = DEFAULT_LANGUAGE,
        include_framework: bool = True,
    ) -> "Translator":
        """Build a translator for an application.

        Sources are consulted in ascending priority: *locale_dir* (the
        application's own catalogs), then the user's override directory beside
        their settings, then *source* if given — handy for tests, and for
        strings that live in memory rather than on disk.
        """
        sources: List[Any] = []
        if locale_dir is not None:
            sources.append(DirectorySource(locale_dir, name="application"))
        # The user's overrides live beside their settings.
        sources.append(DirectorySource(context.paths.subdir("config", "i18n"), name="user"))
        if source is not None:
            sources.append(source)
        return cls(
            sources,
            language=language,
            fallback=fallback,
            include_framework=include_framework,
        )

    # -- introspection -------------------------------------------------
    @property
    def language(self) -> str:
        """The active language code."""
        return self._language

    @property
    def fallback(self) -> str:
        """The language used for keys missing from the active language."""
        return self._fallback

    @property
    def sources(self) -> Sequence[Any]:
        """The sources being consulted, in priority order (last wins)."""
        return tuple(self._sources)

    def languages(self) -> List[str]:
        """Every language any source can provide, sorted."""
        found: set = set()
        for source in self._sources:
            found.update(source.languages())
        return sorted(found)

    def catalogs(self) -> Dict[str, Any]:
        """A copy of the merged catalog, for inspection and debugging."""
        return _deep_merge({}, self._strings)

    # -- language switching --------------------------------------------
    def set_language(self, language: str) -> None:
        """Switch language and reload every catalog."""
        self._language = normalize_lang(language) or self._fallback
        self._reload()

    # -- lookup --------------------------------------------------------
    def t(self, key: str, default: Optional[str] = None, **kwargs: Any) -> str:
        """Translate a dotted *key*, formatting ``{placeholders}`` with *kwargs*.

        Returns *default* if given, otherwise the key itself, when nothing
        matches. Formatting failures are swallowed rather than raising: a
        stray brace in a translation should not take down the interface.
        """
        value = self._lookup(key)
        if not isinstance(value, str):
            value = default if default is not None else key
        if kwargs:
            try:
                value = value.format(**kwargs)
            except (KeyError, IndexError, ValueError):
                pass
        return value

    def has(self, key: str) -> bool:
        """Whether *key* resolves to a string."""
        return isinstance(self._lookup(key), str)

    # -- internals -----------------------------------------------------
    def _lookup(self, key: str) -> Any:
        value: Any = self._strings
        for part in key.split("."):
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        return value

    def _read(self, language: str) -> Dict[str, Any]:
        """Merge every source's catalog for *language*, later sources winning."""
        merged: Dict[str, Any] = {}
        for source in self._sources:
            merged = _deep_merge(merged, source.catalog(language))
        return merged

    def _reload(self) -> None:
        """Rebuild the catalog: fallback first, then the active language on top."""
        merged = self._read(self._fallback)
        if self._language != self._fallback:
            merged = _deep_merge(merged, self._read(self._language))
        self._strings = merged

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"Translator(language={self._language!r}, sources={len(self._sources)})"
