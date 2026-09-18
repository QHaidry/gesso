"""What Tracker's pages share: the settings, the data, and a translator.

Gesso never hands an application a global. There is no ``get_translator()`` to
call from anywhere, because a global would make two windows in one process
impossible and would hide a dependency that is better passed. So Tracker makes
the object it needs and passes it down — the same thing ``AppContext`` is for.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from gesso.config import ConfigStore
from gesso.core import AppContext, AppPaths
from gesso.i18n import DEFAULT_LANGUAGE, Translator, detect_language

from .spec import APP, DATA_FILE, LOCALES_DIR, SCHEMA, resolve_language
from .store import Tracker


class Session:
    """Tracker's state, opened once and handed to every page."""

    def __init__(self, context: AppContext, store: ConfigStore, tracker: Tracker) -> None:
        self.context = context
        self.store = store
        self.tracker = tracker
        self._translator = Translator.for_app(context, locale_dir=LOCALES_DIR)

    @classmethod
    def open(
        cls,
        *,
        config_home: Optional[Path] = None,
        data_home: Optional[Path] = None,
        language: Optional[str] = None,
    ) -> "Session":
        """Resolve both directories, load the settings and the log."""
        paths = AppPaths.resolve(APP.app_id, config_home=config_home, data_home=data_home)
        context = AppContext(APP, paths)
        store = ConfigStore.for_app(SCHEMA, context).load()
        session = cls(context, store, Tracker.load(paths.data_dir / DATA_FILE))
        session.set_language(language or resolve_language(store), persist=False)
        return session

    # ------------------------------------------------------------------
    # Language
    # ------------------------------------------------------------------
    @property
    def translator(self) -> Translator:
        return self._translator

    def set_language(self, language: str, *, persist: bool = True) -> str:
        """Switch language, returning the code actually used.

        ``"auto"`` follows the system locale — and is stored *as* ``auto``, so
        the preference keeps meaning "whatever my system says" rather than
        freezing today's answer.
        """
        chosen = language or "auto"
        resolved = chosen if chosen != "auto" else (detect_language() or DEFAULT_LANGUAGE)

        self._translator = Translator.for_app(
            self.context, language=resolved, locale_dir=LOCALES_DIR
        )
        if persist:
            self.store.set("display.language", chosen)
            self.store.save()
        return resolved

    def t(self, key: str, /, **kwargs: Any) -> str:
        """Translate, in the active language."""
        return self._translator.t(key, **kwargs)

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------
    @property
    def data_path(self) -> Path:
        return self.context.paths.data_dir / DATA_FILE

    def save(self) -> None:
        self.tracker.save(self.data_path)

    def remember(self, key: str, value: Any) -> None:
        """Set a setting, tolerating a config file that cannot be written."""
        from gesso.config import ConfigError

        try:
            self.store.set(key, value)
            self.store.save()
        except ConfigError:
            # A settings file we cannot write costs the user a preference, not
            # the session.
            pass
