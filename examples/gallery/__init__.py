"""Gallery — the design system, on screen.

The third rung, and the first with a window. It is also the last example that
builds its own layout: rung four hands all of this to ``AppShell``, which does
it for you. Seeing the parts first is the point — the shell is a convenience,
not a requirement, and knowing what it assembles makes its behaviour much less
mysterious when something is not where you expected it.

What it puts on screen:

* ``create_app`` — the ``QApplication``, carrying the application's identity
* ``ThemeManager`` — loading palettes, applying one, and switching at runtime
* ``ThemedIcons`` — icons re-tinted when the theme moves
* the widget set — ``Card``, ``PageHeader``, ``SettingRow``, ``SegmentedControl``,
  ``ToggleButton``, ``IconButton``, ``EmptyState``
* the token contract — every token, its group, and what it resolves to

Run it::

    PYTHONPATH=src:examples python -m gallery
    PYTHONPATH=src:examples python -m gallery --theme light
    PYTHONPATH=src:examples python -m gallery --list-themes
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Sequence

from gesso.config import ConfigStore, Option, Schema, Section
from gesso.core import AppContext, AppSpec, AppPaths
from gesso.ui.app import create_app
from gesso.ui.icons import ThemedIcons
from gesso.ui.theme import ThemeManager

from .window import GalleryWindow

#: Where Gallery's user themes live, once seeded.
THEMES_SUBDIR = "themes"

APP = AppSpec(
    name="Gallery",
    app_id="gallery",
    org="Gesso Examples",
    version="0.1.0",
    description="The Gesso design system, shown on itself.",
    default_config_format="json",
)

SCHEMA = Schema(
    [
        Section(
            "display",
            title="Display",
            description="What the window starts with.",
            options=(
                # No `choices` here: the valid values are whichever palettes
                # Gesso finds, which is only known once a QApplication exists.
                # The schema constrains what it can and stays out of the rest.
                Option("theme", str, "dark", "Palette to start with."),
                Option(
                    "icon_size",
                    int,
                    20,
                    "Icon size in the showcase, in pixels.",
                    minimum=12,
                    maximum=48,
                ),
                Option("show_tokens", bool, True, "Show the token inspector."),
            ),
        )
    ]
)


def open_store(config_home: Path) -> ConfigStore:
    """Load Gallery's settings, creating the config directory if needed."""
    paths = AppPaths.resolve(APP.app_id, config_home=config_home)
    return ConfigStore.for_app(SCHEMA, AppContext(APP, paths)).load()


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Open the window. Returns the event loop's exit code."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="gallery",
        description=f"{APP.display_name} — {APP.description}",
    )
    parser.add_argument(
        "--config-home",
        type=Path,
        default=Path("gallery-home"),
        help="Stands in for $XDG_CONFIG_HOME (default: ./gallery-home)",
    )
    parser.add_argument("--theme", help="Start with this palette instead of the stored one")
    parser.add_argument("--list-themes", action="store_true", help="Print the palettes and exit")
    args = parser.parse_args(argv)

    paths = AppPaths.resolve(APP.app_id, config_home=args.config_home)
    store = ConfigStore.for_app(SCHEMA, AppContext(APP, paths)).load()

    app = create_app(APP, [])

    manager = ThemeManager(
        app,
        user_dir=paths.config_dir / THEMES_SUBDIR,
        # Seeding copies each built-in palette into the user's directory once.
        # A theme you cannot see is a theme you cannot edit.
        seed=True,
        parent=app,
    )

    if args.list_themes:
        for name in manager.names():
            print(name)
        return 0

    requested = args.theme or store.get("display.theme")
    if not manager.apply(requested):
        # An unknown palette in the config is not fatal; land on the default.
        manager.apply(manager.names()[0] if manager.names() else None)

    icons = ThemedIcons(theme_manager=manager)
    window = GalleryWindow(APP, manager=manager, icons=icons, store=store)
    window.show()
    return app.exec()


__all__: List[str] = ["APP", "SCHEMA", "THEMES_SUBDIR", "main", "open_store"]
