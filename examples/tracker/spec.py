"""Tracker's identity, its settings schema, and where it keeps things."""

from __future__ import annotations

from pathlib import Path

from gesso.config import Option, Schema, Section
from gesso.core import AppSpec
from gesso.i18n import DEFAULT_LANGUAGE, detect_language

#: Tracker's own assets. Rung four is the first example with all three: a
#: palette, an icon, and translation catalogs.
THEMES_DIR = Path(__file__).parent / "themes"
ICONS_DIR = Path(__file__).parent / "icons"
LOCALES_DIR = Path(__file__).parent / "locales"

#: Tracker's data. Settings are Gesso's business; this is not.
DATA_FILE = "tracker.json"

APP = AppSpec(
    name="Tracker",
    app_id="tracker",
    org="Gesso Examples",
    version="0.1.0",
    description="A small habit tracker: the last rung of the example ladder.",
    default_config_format="json",
)

SCHEMA = Schema(
    [
        Section(
            "display",
            title="Display",
            description="How the window looks and reads.",
            options=(
                Option(
                    "language",
                    str,
                    "auto",
                    "Interface language. 'auto' follows your system locale.",
                    choices=("auto", "en", "fr"),
                ),
                # No `choices`: the valid palettes are the ones Gesso can find,
                # which the schema cannot know. It also cannot stop a user from
                # deleting a theme file, and should not try.
                Option("theme", str, "midnight", "Palette to use."),
                Option("show_streaks", bool, True, "Show how many days in a row each habit runs."),
                Option(
                    "week_starts_on",
                    str,
                    "monday",
                    "First day of the week, in the history view.",
                    choices=("monday", "sunday"),
                ),
            ),
        ),
        Section(
            "today",
            title="Today",
            description="What the Today page aims at.",
            options=(
                Option(
                    "target",
                    int,
                    3,
                    "Habits to aim for each day. Shown as progress, never enforced.",
                    minimum=1,
                    maximum=20,
                ),
                Option(
                    "history_days",
                    int,
                    7,
                    "How many days the History page shows.",
                    minimum=1,
                    maximum=60,
                ),
            ),
        ),
    ]
)


def resolve_language(store) -> str:
    """The configured language, or the system's if the setting says ``auto``.

    A stored preference outranks a detected locale; an *unset* one should defer
    to it. Only the application knows which its setting means, so Gesso does
    not guess.
    """
    chosen = store.get("display.language")
    if chosen and chosen != "auto":
        return chosen
    return detect_language() or DEFAULT_LANGUAGE
