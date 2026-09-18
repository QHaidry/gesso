"""Tracker — the last rung: every Gesso feature in one application.

The ladder so far: ``hello`` shows a schema, ``basket`` adds translations, and
``gallery`` puts the widget set and theming on screen. Tracker is what you get
when all of it is an actual application:

* **Identity** — an ``AppSpec``, including the ``org`` that XDG paths use.
* **Configuration** — a schema with choices, bounds and defaults, in a file
  Gesso finds and whose format Gesso works out.
* **Data, kept apart from it** — the habit log is plain Python in the data
  directory, because a schema is for settings, not for everything.
* **Internationalisation** — two catalogs, plural forms chosen by the
  application, a language setting, and Gesso's own shell strings routed through
  Tracker's translator under the reserved ``gesso.`` domain.
* **Theming** — a palette of Tracker's own, deliberately *partial*, so the
  contract supplies the rest; plus Gesso's, plus whatever the user drops into
  their config.
* **Icons** — two of Tracker's own layered over Gesso's, in one registry.
* **Widgets and the shell** — pages, navigation, a header with actions and a
  live status line, assembled by ``AppShell`` from ``add_page`` calls.

Run it::

    PYTHONPATH=src:examples python -m tracker
    PYTHONPATH=src:examples python -m tracker --language fr
    PYTHONPATH=src:examples python -m tracker --theme light
    PYTHONPATH=src:examples python -m tracker --config-home ./tracker-home

``--config-home`` and ``--data-home`` both default to ``./tracker-home``, so
the example never touches your real profile.

Compare this with Gallery. Gallery builds its own window and lays out a
sidebar-shaped thing by hand. Tracker does not, and is *shorter* despite having
far more in it. That is the trade the application shell exists to make.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from gesso.ui.app import run_app
from gesso.ui.theme import BUILTIN_PALETTES_DIR

from .pages import AboutPage, HistoryPage, SettingsPage, TodayPage
from .session import Session
from .spec import APP, ICONS_DIR, THEMES_DIR

#: The pages, in navigation order: ``(key, label key, comment key, icon)``.
#: Two icons are Gesso's and two are Tracker's own — all four resolve through
#: one registry, because Tracker's directory is appended to Gesso's rather than
#: replacing it.
PAGES = (
    ("today", "tracker.nav.today", "tracker.page.today", "check"),
    ("history", "tracker.nav.history", "tracker.page.history", "streak"),
    ("settings", "tracker.nav.settings", "tracker.page.settings", "settings"),
    ("about", "tracker.nav.about", "", "info"),
)


def build(shell: Any, session: Session) -> None:
    """Populate *shell* from *session*.

    Module-level and session-taking rather than a closure inside :func:`run`,
    so a test can build a window without starting an event loop.

    ``shell`` is an ``AppShell`` the caller already made. Gesso supplies the
    navigator, the content stack, the header and the status line; this function
    only says what goes in them.

    Returns nothing, which ``run_app`` requires: a non-``None`` return means
    "show this window instead of the shell". The pages are reachable through
    ``shell.page(key).widget``, so nothing needs handing back.
    """
    icons = shell.icons
    manager = shell.theme_manager
    pages: Dict[str, Any] = {}

    def refresh_status() -> None:
        tracker = session.tracker
        today = date.today()
        done = sum(1 for name in tracker.habits if tracker.is_done(name, today))
        shell.set_info(
            session.t("tracker.status.progress", done=done, total=len(tracker.habits))
        )

    def retranslate() -> None:
        """Re-say everything that came from a catalog.

        A page's title lives in three places — the ``Page`` record, its
        navigation button, and the header — which is why the shell retitles all
        three at once rather than leaving a half-translated window.
        """
        shell.set_brand(APP.display_name, session.t("tracker.tagline"))
        shell.set_message(session.t("tracker.status.ready"))
        # Gesso's own strings — the shell's tooltip — are Tracker's to re-say
        # too, because Tracker handed the shell its translator.
        shell.retranslate()
        for key, label, comment, _icon in PAGES:
            shell.set_page_title(key, session.t(label), session.t(comment) if comment else "")
        for page in pages.values():
            page.retranslate()
        refresh_status()

    def change_language(code: str) -> None:
        session.set_language(code)
        retranslate()

    def change_theme(name: str) -> None:
        # `apply_theme` answers "is the palette I asked for the one in force",
        # not "did anything happen" — a palette with no file installed falls
        # back rather than failing. Only remember the palette that took.
        if shell.apply_theme(name):
            session.remember("display.theme", name)

    def on_settings_change() -> None:
        pages["today"].reload()
        refresh_status()

    pages["today"] = TodayPage(session, icons, on_change=refresh_status)
    pages["history"] = HistoryPage(session, icons)
    pages["settings"] = SettingsPage(
        session,
        icons,
        theme_names=manager.names(),
        current_theme=manager.current.name if manager.current else None,
        on_theme_change=change_theme,
        on_language_change=change_language,
        on_settings_change=on_settings_change,
    )
    pages["about"] = AboutPage(session, icons)

    for key, label, comment, icon in PAGES:
        page = pages[key]
        shell.add_page(
            key,
            session.t(label),
            page,
            comment=session.t(comment) if comment else "",
            icon=icon,
            # The page says which buttons it wants; the shell decides where they
            # go, and the page never learns where that was.
            actions=page.header_actions(),
        )

    shell.set_brand(APP.display_name, session.t("tracker.tagline"))
    shell.set_message(session.t("tracker.status.ready"))
    shell.show_page("today")
    refresh_status()


def run(argv: Optional[Sequence[str]] = None) -> int:
    """Open Tracker. Returns the event loop's exit code."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="tracker", description=f"{APP.display_name} — {APP.description}"
    )
    parser.add_argument(
        "--config-home",
        type=Path,
        default=Path("tracker-home"),
        help="Stands in for $XDG_CONFIG_HOME (default: ./tracker-home)",
    )
    parser.add_argument(
        "--data-home",
        type=Path,
        default=Path("tracker-home"),
        help="Stands in for $XDG_DATA_HOME (default: ./tracker-home)",
    )
    parser.add_argument(
        "--language",
        choices=("auto", "en", "fr"),
        help="Use this language for this run, without changing the setting",
    )
    parser.add_argument(
        "--theme", help="Start with this palette, without changing the setting"
    )
    args = parser.parse_args(argv)

    session = Session.open(
        config_home=args.config_home,
        data_home=args.data_home,
        language=args.language,
    )

    return run_app(
        APP,
        lambda shell: build(shell, session),
        # Tracker parses its own arguments, so the QApplication gets none.
        argv=[],
        # Both flags override for this run only. A command-line switch that
        # quietly rewrites a stored preference is a surprise, and the Settings
        # page is where preferences belong. `Session.open` is what applies the
        # language, and it is told not to persist.
        theme=args.theme or session.store.get("display.theme"),
        # Tracker's palette ships with the application, so it is a *built-in*
        # rather than a user theme. Note that this list REPLACES Gesso's — it
        # does not extend it, unlike `icon_dirs`, which appends. The asymmetry
        # is deliberate: the stylesheet references Gesso's icon *names*, so
        # those directories must stay resolvable, whereas nothing breaks if a
        # palette is absent. An application that wants its own palette and
        # Gesso's names both.
        builtin_theme_dirs=[THEMES_DIR, BUILTIN_PALETTES_DIR],
        user_theme_dir=session.context.paths.config_dir / "themes",
        icon_dirs=[ICONS_DIR],
        # Gesso's own shell strings go through Tracker's translator, under the
        # reserved `gesso.` domain, so nothing in the framework is stuck in
        # English.
        translate=session.t,
    )


__all__: List[str] = ["APP", "PAGES", "build", "run"]
