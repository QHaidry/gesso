"""Basket — a grocery list, with settings and translations.

The second rung of the example ladder. Where ``hello.py`` shows a single
setting, Basket shows what a real application's settings look like: **typed,
constrained, and validated**, plus **strings that are not English-only**.

Run it::

    PYTHONPATH=src:examples python -m basket add milk --price 1.20
    PYTHONPATH=src:examples python -m basket list
    PYTHONPATH=src:examples python -m basket --language fr list
    PYTHONPATH=src:examples python -m basket config --set display.language fr
    PYTHONPATH=src:examples python -m basket config --show

Both of Gesso's directories default under ``./basket-home``, standing in for
``$XDG_CONFIG_HOME`` and ``$XDG_DATA_HOME``, so the example never touches your
real profile.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from gesso.config import ConfigStore, Option, Schema, Section
from gesso.core import AppContext, AppSpec, AppPaths
from gesso.i18n import DEFAULT_LANGUAGE, Translator, detect_language

#: Where Basket's own translation catalogs live.
LOCALES_DIR = Path(__file__).parent / "locales"

# ----------------------------------------------------------------------
# 1. Who is this application?
# ----------------------------------------------------------------------
APP = AppSpec(
    name="Basket",
    app_id="basket",
    org="Gesso Examples",
    version="0.1.0",
    description="A grocery list that remembers your settings.",
    default_config_format="json",
)

# ----------------------------------------------------------------------
# 2. What does it store?
# ----------------------------------------------------------------------
# Note what the schema is *not* doing: it does not describe the shopping list.
# Settings are small, typed and hand-editable; the list is arbitrary
# application data. Gesso governs the first and stays out of the second.
SCHEMA = Schema(
    [
        Section(
            "display",
            title="Display",
            description="How the list is presented.",
            options=(
                Option(
                    "language",
                    str,
                    "auto",
                    "Interface language.",
                    choices=("auto", "en", "fr"),
                ),
                Option("currency", str, "\u20ac", "Symbol printed before a price."),
                Option("show_prices", bool, True, "Print a column of prices."),
                Option(
                    "width",
                    int,
                    24,
                    "Width of the item column, in characters.",
                    minimum=8,
                    maximum=60,
                ),
            ),
        ),
        Section(
            "list",
            title="List",
            description="Rules the list obeys.",
            options=(
                Option(
                    "max_items",
                    int,
                    50,
                    "Refuse to hold more than this many items.",
                    minimum=1,
                    maximum=500,
                ),
                Option(
                    "name_pattern",
                    str,
                    r"^[\w][\w \-']*$",
                    "What an item name may look like.",
                ),
            ),
        ),
    ]
)


def resolve_language(store: ConfigStore) -> str:
    """The language to use, following the system if the setting says ``auto``.

    Gesso cannot make this choice for you: a stored preference outranks a
    detected locale, but an *unset* one should defer to it, and only the
    application knows whether its setting means "unset" or means a literal
    value.
    """
    chosen = store.get("display.language")
    if chosen and chosen != "auto":
        return chosen
    return detect_language() or DEFAULT_LANGUAGE


# ----------------------------------------------------------------------
# 3. Let Gesso find the files
# ----------------------------------------------------------------------
@dataclass
class Profile:
    """A settings store and a translator, opened together.

    Settings and translations are separate concerns, but they meet at exactly
    one point — the language — so they are opened together here and never
    passed around as a pair.
    """

    context: AppContext
    store: ConfigStore
    translator: Translator

    @classmethod
    def open(
        cls,
        *,
        config_home: Optional[Path] = None,
        data_home: Optional[Path] = None,
        language: Optional[str] = None,
    ) -> "Profile":
        """Resolve both directories, load the settings, and pick a language."""
        paths = AppPaths.resolve(APP.app_id, config_home=config_home, data_home=data_home)
        context = AppContext(APP, paths)
        store = ConfigStore.for_app(SCHEMA, context).load()
        translator = Translator.for_app(
            context,
            language=language or resolve_language(store),
            locale_dir=LOCALES_DIR,
        )
        return cls(context=context, store=store, translator=translator)

    @property
    def data_dir(self) -> Path:
        """Where the application's own data goes — the config directory is for
        settings, and keeping a growing list in there would be a mistake."""
        return self.context.paths.data_dir

    def t(self, key: str, /, **kwargs: object) -> str:
        return self.translator.t(key, **kwargs)
