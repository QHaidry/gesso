"""Tracker must build, record, and change language without a restart.

The last rung has the most to go wrong: five tiers meeting at once, in a
window. These tests drive the real ``build()``, and two of them drive the real
``run()`` with only the event loop stubbed, so wiring that drifts from what
``run_app`` actually accepts cannot hide.
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any, Dict, Set

import pytest
from PySide6.QtWidgets import QPushButton

import tracker
from tracker.session import Session
from tracker.spec import APP, ICONS_DIR, LOCALES_DIR, THEMES_DIR


@pytest.fixture
def session(tmp_path):
    return Session.open(config_home=tmp_path, data_home=tmp_path)


def wire(session: Session, **overrides: Any) -> Any:
    """What ``run_app`` does around a shell, minus the event loop.

    Deliberately thin — ``test_run_accepts_what_it_passes`` below drives the
    real ``run()`` with only ``exec`` stubbed, so anything the two disagree
    about shows up there.
    """
    from gesso.ui.app import AppShell, create_app
    from gesso.ui.icons import IconRegistry, ThemedIcons
    from gesso.ui.theme import BUILTIN_PALETTES_DIR, ThemeManager

    app = create_app(APP, [])
    registry = IconRegistry()
    for directory in overrides.get("icon_dirs") or (ICONS_DIR,):
        registry.add_directory(directory)

    manager = ThemeManager(
        app,
        builtin_dirs=overrides.get("builtin_theme_dirs")
        or [THEMES_DIR, BUILTIN_PALETTES_DIR],
        user_dir=session.context.paths.config_dir / "themes",
        parent=app,
    )
    manager.apply(overrides.get("theme") or session.store.get("display.theme"))

    shell = AppShell(
        APP,
        theme_manager=manager,
        icons=ThemedIcons(registry, manager),
        translate=session.t,
    )
    tracker.build(shell, session)
    return shell


def labels(widget: Any) -> Set[str]:
    from PySide6.QtWidgets import QLabel

    return {child.text() for child in widget.findChildren(QLabel)}


def habit_controls(page: Any) -> Dict[str, QPushButton]:
    """Map each habit name to its toggle, read from the rendered rows.

    Reading what is on screen rather than the page's private bookkeeping, so a
    broken layout cannot pass.
    """
    from gesso.ui.widgets import SettingRow

    return {row.label.text(): row.control for row in page.findChildren(SettingRow)}


def description_of(page: Any, habit: str) -> str:
    from gesso.ui.widgets import SettingRow

    for row in page.findChildren(SettingRow):
        if row.label.text() == habit:
            return row.description.text()
    raise AssertionError(f"no row for {habit!r}")


# ----------------------------------------------------------------------
# It builds
# ----------------------------------------------------------------------


def test_every_page_is_added(session):
    assert wire(session).pages() == [key for key, *_ in tracker.PAGES]


def test_it_opens_on_today(session):
    assert wire(session).current_page() == "today"


def test_every_navigation_icon_resolves(session):
    """Two icons are Tracker's and two are Gesso's; all four must resolve."""
    registry = wire(session).icons.registry

    assert registry.has("streak"), "Tracker's own icon is missing"
    assert registry.has("settings"), "Tracker's own icon is missing"
    assert registry.has("check"), "Gesso's icons were replaced, not added to"
    assert registry.has("info"), "Gesso's icons were replaced, not added to"


def test_the_themes_are_trackers_and_gessos(session):
    names = wire(session).theme_manager.names()
    assert "midnight" in names, "Tracker's own palette is missing"
    assert "dark" in names, "Gesso's palettes were replaced, not added to"


def test_the_pages_get_their_headers(session):
    shell = wire(session)
    assert shell.header("today").title_label.text()
    # Today and History offer a reload button; the others offer none.
    assert shell.header("today").actions
    assert shell.header("history").actions
    assert shell.header("settings").actions == []


# ----------------------------------------------------------------------
# Recording a habit
# ----------------------------------------------------------------------


def test_ticking_a_habit_records_it(session):
    shell = wire(session)
    habit_controls(shell.page("today").widget)["read"].click()

    assert session.tracker.is_done("read", date.today())
    assert session.tracker.done_on(date.today()) == ["read"]


def test_ticking_is_written_to_the_data_file(session):
    shell = wire(session)
    habit_controls(shell.page("today").widget)["walk"].click()

    # A fresh session reads the same log back off disk.
    assert Session.open(
        config_home=session.context.paths.config_home,
        data_home=session.context.paths.data_home,
    ).tracker.is_done("walk", date.today())


def test_the_progress_line_follows(session):
    shell = wire(session)
    page = shell.page("today").widget

    habit_controls(page)["read"].click()

    assert "1 of 3" in page.progress.text()


def test_the_streak_appears_only_when_asked_for(session):
    shell = wire(session)
    page = shell.page("today").widget

    habit_controls(page)["read"].click()
    assert "1 day in a row" in description_of(page, "read")

    session.remember("display.show_streaks", False)
    page.reload()
    assert description_of(page, "read") == ""


def test_unticking_leaves_no_trace_of_the_day(session):
    shell = wire(session)
    control = habit_controls(shell.page("today").widget)["read"]

    control.click()
    control.click()

    assert not session.tracker.is_done("read", date.today())
    # A day with nothing done is not a day holding an empty list.
    assert session.tracker.done == {}


def test_the_status_line_reports_progress(session):
    shell = wire(session)
    habit_controls(shell.page("today").widget)["read"].click()
    assert "1 of 3" in shell.status_info.text()


def test_the_history_page_shows_the_day(session):
    shell = wire(session)
    habit_controls(shell.page("today").widget)["read"].click()
    shell.page("history").widget.reload()

    assert date.today().isoformat() in labels(shell.page("history").widget)


def test_a_profile_with_no_habits_says_so(session):
    session.tracker.habits = []
    page = wire(session).page("today").widget
    assert page.progress.text()


# ----------------------------------------------------------------------
# Changing language, live
# ----------------------------------------------------------------------


def french_button(page: Any) -> QPushButton:
    for button in page.findChildren(QPushButton):
        if button.isCheckable() and "Fran" in button.text():
            return button
    raise AssertionError("no French button on the settings page")


def test_changing_language_retitles_every_page(session):
    shell = wire(session)
    french_button(shell.page("settings").widget).click()

    assert shell.page("today").title == "Aujourd'hui"
    assert shell.page("history").title == "Historique"
    assert shell.page("about").title == "À propos"


def test_changing_language_retitles_the_brand(session):
    shell = wire(session)
    french_button(shell.page("settings").widget).click()

    assert shell.brand_subtitle.text() == "Une habitude par jour, retenue pour vous."


def test_changing_language_retitles_the_shells_own_string(session):
    """The shell's tooltip is *Gesso's* string, and it follows too.

    That is the reserved ``gesso.`` domain doing its job: the framework owns
    that key, Tracker owns the rest, and the shell speaks through whichever
    translator it was handed.
    """
    shell = wire(session)
    assert shell.drawer_button.toolTip() == "Show or hide the navigation"

    french_button(shell.page("settings").widget).click()

    assert shell.drawer_button.toolTip() == "Afficher ou masquer la navigation"


def test_changing_language_relabels_the_pages_own_controls(session):
    shell = wire(session)
    french_button(shell.page("settings").widget).click()

    texts = {button.text() for button in habit_controls(shell.page("today").widget).values()}
    assert texts == {"Fait"}


def test_changing_language_is_remembered(session):
    shell = wire(session)
    french_button(shell.page("settings").widget).click()
    assert session.store.get("display.language") == "fr"


def test_the_language_setting_can_still_mean_automatic(session):
    """Picking your system locale stores ``auto``, not today's answer."""
    session.set_language("fr")
    session.set_language("auto")
    assert session.store.get("display.language") == "auto"


# ----------------------------------------------------------------------
# Catalogues and palettes
# ----------------------------------------------------------------------


def keys_of(catalog: Dict[str, Any], prefix: str = "") -> Set[str]:
    found: Set[str] = set()
    for key, value in catalog.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            found |= keys_of(value, path)
        else:
            found.add(path)
    return found


def load_catalog(language: str) -> Dict[str, Any]:
    return json.loads((LOCALES_DIR / f"{language}.json").read_text(encoding="utf-8"))


def test_the_catalogs_cover_the_same_keys():
    assert keys_of(load_catalog("en")) == keys_of(load_catalog("fr"))


def test_every_catalog_key_resolves():
    """A key that is asked for but never defined comes back as itself.

    This is the test that catches a dotted *key name* written inside JSON, where
    ``"theme.help"`` is a literal key rather than a nested one — the lookup
    walks into the string ``"Palette"`` and gives up.
    """
    from gesso.i18n import DirectorySource, Translator

    translator = Translator(
        [DirectorySource(LOCALES_DIR)], language="en", include_framework=False
    )
    unresolved = [key for key in sorted(keys_of(load_catalog("en"))) if translator.t(key) == key]
    assert unresolved == []


def test_a_partial_palette_is_completed_by_the_contract(session):
    """Tracker's palette states only what it wants to change."""
    shell = wire(session)
    theme = shell.theme_manager.load("midnight")

    # A token Midnight does not state...
    assert not theme.is_explicit("scroll_handle")
    # ...still resolves, because the contract has a last-resort default.
    assert theme.get("scroll_handle")
    assert shell.theme_manager.problems("midnight") == []


# ----------------------------------------------------------------------
# The entry point
# ----------------------------------------------------------------------


def test_run_accepts_what_it_passes(monkeypatch, tmp_path):
    """``run()`` must pass ``run_app`` arguments ``run_app`` actually takes.

    Only the event loop is stubbed; everything else is the real thing, which is
    what makes this test worth having next to the hand-wired ones above.
    """
    from PySide6.QtWidgets import QApplication

    monkeypatch.setattr(QApplication, "exec", lambda self: 0)

    code = tracker.run(
        ["--config-home", str(tmp_path), "--data-home", str(tmp_path), "--theme", "light"]
    )
    assert code == 0


def test_the_language_flag_is_not_remembered(monkeypatch, tmp_path):
    """A command-line switch overrides for one run; it does not rewrite a
    stored preference. The Settings page is where preferences belong."""
    from PySide6.QtWidgets import QApplication

    monkeypatch.setattr(QApplication, "exec", lambda self: 0)

    tracker.run(
        ["--config-home", str(tmp_path), "--data-home", str(tmp_path), "--language", "fr"]
    )

    reopened = Session.open(config_home=tmp_path, data_home=tmp_path)
    assert reopened.store.get("display.language") == "auto"
