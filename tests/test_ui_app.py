"""Tests for the application shell and the bootstrap.

The shell is the piece an application's window is built from, so the things
worth asserting are the ones a screenshot will not tell you: that a page switch
moves the stack *and* the navigation, that collapsing keeps the labels
reachable as tooltips, and that a theme change repaints the navigation without
the application asking.

Anything that needs the event loop samples state from a zero-delay timer
*inside* the loop, rather than asserting after it has returned — by then the
world the window lived in is gone.
"""

from __future__ import annotations

import sys

import pytest
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget

from gesso.core.app import AppSpec
from gesso.ui.app import AppShell, create_app, install_exception_hook, run_app
from gesso.ui.app.shell import SIDEBAR_WIDTH_COLLAPSED, SIDEBAR_WIDTH_EXPANDED

#: An icon Gesso actually ships. A name that does not exist is covered by the
#: icon tests; using one here would only be noise.
ICON = "check"


@pytest.fixture(scope="module")
def qapp():
    application = QApplication.instance() or QApplication([])
    yield application
    application.setStyleSheet("")


@pytest.fixture
def spec():
    return AppSpec("Test App", app_id="test-app", org="Test", version="1.0.0")


@pytest.fixture
def themes(qapp):
    from gesso.ui.theme import ThemeManager

    manager = ThemeManager(qapp)
    manager.apply("dark")
    return manager


@pytest.fixture
def icons(themes):
    from gesso.ui.icons import ThemedIcons

    return ThemedIcons(theme_manager=themes)


@pytest.fixture
def shell(qapp, spec, themes, icons):
    return AppShell(spec, theme_manager=themes, icons=icons)


def _nav_buttons(shell):
    return [b for b in shell.findChildren(QPushButton) if b.objectName() == "navButton"]


def _sample(qapp, **callables):
    """Evaluate *callables* inside the event loop, then quit.

    Returns the collected results, so a test can assert on the state the window
    actually had while it was running.
    """
    results = {}

    def capture():
        for name, callback in callables.items():
            results[name] = callback()
        qapp.quit()

    QTimer.singleShot(0, capture)
    return results


def _silence_hook(monkeypatch):
    """Replace the hook we chain to with a no-op.

    Chaining to the real one hands the exception to whatever is already
    installed — under pytest-qt that reports it as a test failure.
    """
    monkeypatch.setattr(sys, "excepthook", lambda *args: None)


# ----------------------------------------------------------------------
# The shell
# ----------------------------------------------------------------------


def test_the_window_title_comes_from_the_spec(shell):
    assert shell.windowTitle() == "Test App"


def test_adding_a_page_adds_a_navigation_entry_too(shell):
    shell.add_page("home", "Home", QWidget(), icon=ICON)
    assert shell.pages() == ["home"]
    assert [button.text() for button in _nav_buttons(shell)] == ["Home"]


def test_the_first_page_is_shown_automatically(shell):
    shell.add_page("home", "Home", QWidget())
    shell.add_page("other", "Other", QWidget())
    assert shell.current_page() == "home"


def test_showing_a_page_moves_the_stack_and_the_navigation(shell):
    shell.add_page("home", "Home", QWidget())
    shell.add_page("other", "Other", QWidget())

    assert shell.show_page("other") is True

    assert shell.current_page() == "other"
    assert [b.text() for b in _nav_buttons(shell) if b.isChecked()] == ["Other"]


def test_showing_an_unknown_page_is_refused(shell):
    shell.add_page("home", "Home", QWidget())
    assert shell.show_page("nope") is False
    assert shell.current_page() == "home"


def test_a_duplicate_page_key_is_refused(shell):
    shell.add_page("home", "Home", QWidget())
    with pytest.raises(ValueError):
        shell.add_page("home", "Again", QWidget())


def test_page_changes_are_announced(shell):
    shell.add_page("home", "Home", QWidget())
    shell.add_page("other", "Other", QWidget())
    seen = []
    shell.pageChanged.connect(seen.append)

    shell.show_page("other")

    assert seen == ["other"]


def test_a_page_header_carries_the_title_and_comment(shell):
    shell.add_page("home", "Home", QWidget(), comment="What it is for")
    header = shell.header("home")
    assert header.title_label.text() == "Home"
    assert header.comment_label.text() == "What it is for"


def test_a_page_can_offer_actions(shell):
    action = QPushButton("Apply")
    shell.add_page("home", "Home", QWidget(), actions=[action])
    assert shell.header("home").actions == [action]


def test_the_brand_can_be_set(shell):
    shell.set_brand("My App", "does one thing")
    assert shell.brand_label.text() == "My App"
    assert shell.brand_subtitle.text() == "does one thing"


def test_status_messages_and_permanent_info_are_separate(shell):
    shell.set_message("Working…")
    shell.set_info("Image: none")
    # A transient message must not wipe the permanent information, which is why
    # they are two different widgets.
    assert shell.status_bar.currentMessage() == "Working…"
    assert shell.status_info.text() == "Image: none"


# ----------------------------------------------------------------------
# Collapsing
# ----------------------------------------------------------------------


def test_collapsing_narrows_the_sidebar_and_hides_the_labels(shell):
    shell.add_page("home", "Home", QWidget(), icon=ICON)

    shell.set_sidebar_collapsed(True)

    assert shell.sidebar_collapsed is True
    assert shell.sidebar.width() == SIDEBAR_WIDTH_COLLAPSED
    assert shell.brand_label.isHidden() is True
    assert _nav_buttons(shell)[0].text() == ""


def test_a_collapsed_entry_keeps_its_label_as_a_tooltip(shell):
    # Icon-only navigation with no labels and no tooltips is a memory test.
    shell.add_page("home", "Home", QWidget(), icon=ICON)
    shell.set_sidebar_collapsed(True)
    assert _nav_buttons(shell)[0].toolTip() == "Home"


def test_expanding_restores_the_labels(shell):
    shell.add_page("home", "Home", QWidget(), icon=ICON)
    shell.set_sidebar_collapsed(True)
    shell.set_sidebar_collapsed(False)

    assert shell.sidebar.width() == SIDEBAR_WIDTH_EXPANDED
    button = _nav_buttons(shell)[0]
    assert button.text() == "Home"
    assert button.toolTip() == ""
    assert shell.brand_label.isHidden() is False


def test_toggle_flips_the_state(shell):
    shell.toggle_sidebar()
    assert shell.sidebar_collapsed is True
    shell.toggle_sidebar()
    assert shell.sidebar_collapsed is False


# ----------------------------------------------------------------------
# Theme awareness
# ----------------------------------------------------------------------


def test_a_theme_change_repaints_the_navigation(shell, themes):
    shell.add_page("home", "Home", QWidget(), icon=ICON)
    button = _nav_buttons(shell)[0]

    before = button.icon().pixmap(18).toImage()
    themes.apply("light")
    after = button.icon().pixmap(18).toImage()

    # The checked entry takes the accent, so its pixels change — and the
    # application never asked for it.
    assert before != after


def test_apply_theme_goes_through_the_manager(shell):
    assert shell.apply_theme("light") is True
    assert shell.theme_manager.current.name == "light"


def test_apply_theme_without_a_manager_is_refused(spec):
    assert AppShell(spec).apply_theme("dark") is False


def test_the_shell_translates_its_own_strings(spec):
    """Gesso's own labels go through the application's translator.

    This is what the reserved ``gesso.`` domain is for: the framework owns
    those keys, the application owns the rest, and neither can collide.
    """
    shell = AppShell(spec, translate=lambda key, **kwargs: f"<{key}>")
    assert shell.drawer_button.toolTip() == "<gesso.shell.toggle_navigation>"


def test_the_shell_shows_the_key_when_it_cannot_translate(spec):
    # A missing translator shows the key rather than an empty tooltip: visible
    # on screen, and greppable in the source.
    assert AppShell(spec).drawer_button.toolTip() == "gesso.shell.toggle_navigation"


def test_gesso_ships_a_translation_for_its_own_key():
    from gesso.i18n import Translator

    for language in ("en", "fr"):
        translated = Translator(language=language).t("gesso.shell.toggle_navigation")
        assert translated != "gesso.shell.toggle_navigation"


# ----------------------------------------------------------------------
# The bootstrap
# ----------------------------------------------------------------------


def test_create_app_carries_the_identity(qapp, spec):
    app = create_app(spec)
    assert app.applicationName() == "test-app"
    assert app.applicationDisplayName() == "Test App"
    assert app.applicationVersion() == "1.0.0"
    assert app.organizationName() == "Test"


def test_run_app_builds_the_shell_and_returns_the_exit_code(qapp, themes, icons, spec):
    built = {}

    def build(shell):
        built["shell"] = shell
        QTimer.singleShot(0, qapp.quit)

    code = run_app(spec, build, theme_manager=themes, icons=icons)

    assert code == 0
    assert built["shell"].spec is spec


def test_run_app_shows_a_custom_window_when_build_returns_one(qapp, themes, icons, spec):
    window = QMainWindow()
    sampled = _sample(qapp, shown=window.isVisible)

    def build(shell):
        QTimer.singleShot(0, qapp.quit)
        return window

    run_app(spec, build, theme_manager=themes, icons=icons)

    assert sampled == {"shown": True}


def test_an_rtl_language_mirrors_the_interface(qapp, themes, icons, spec):
    """The one place the i18n tier meets the UI tier."""
    sampled = _sample(qapp, direction=qapp.layoutDirection)

    def build(shell):
        QTimer.singleShot(0, qapp.quit)

    try:
        run_app(spec, build, language="ar", theme_manager=themes, icons=icons)
    finally:
        qapp.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

    assert sampled == {"direction": Qt.LayoutDirection.RightToLeft}


def test_a_left_to_right_language_does_not_mirror(qapp, themes, icons, spec):
    sampled = _sample(qapp, direction=qapp.layoutDirection)

    def build(shell):
        QTimer.singleShot(0, qapp.quit)

    run_app(spec, build, language="en", theme_manager=themes, icons=icons)

    assert sampled == {"direction": Qt.LayoutDirection.LeftToRight}


def test_install_exception_hook_reports_and_delegates(monkeypatch):
    seen = []
    _silence_hook(monkeypatch)
    install_exception_hook(on_error=seen.append)

    try:
        raise ValueError("boom")
    except ValueError:
        sys.excepthook(*sys.exc_info())

    assert len(seen) == 1
    assert "boom" in seen[0]


def test_install_exception_hook_leaves_keyboard_interrupt_alone(monkeypatch):
    seen = []
    _silence_hook(monkeypatch)
    install_exception_hook(on_error=seen.append)

    try:
        raise KeyboardInterrupt
    except KeyboardInterrupt:
        sys.excepthook(*sys.exc_info())

    # Ctrl-C in a terminal should not raise an error dialog.
    assert seen == []


# ----------------------------------------------------------------------
# The object-name contract
# ----------------------------------------------------------------------


def test_the_shell_only_uses_object_names_the_stylesheet_styles(shell, themes):
    """The same drift check the widget library gets.

    The shell is styled entirely by the base stylesheet, so an object name it
    sets but the stylesheet does not know would leave a piece of chrome bare.
    """
    shell.add_page("home", "Home", QWidget(), comment="c", icon=ICON)
    shell.set_brand("Test App", "subtitle")

    declared = {
        widget.objectName()
        for widget in [shell] + shell.findChildren(QWidget)
        if widget.objectName()
    }

    sheet = themes.stylesheet("dark")
    missing = sorted(name for name in declared if f"#{name}" not in sheet)
    assert missing == [], f"these object names are not styled: {missing}"


# ----------------------------------------------------------------------
# Retitling, for changing language
# ----------------------------------------------------------------------


def test_a_page_can_be_retitled(shell):
    shell.add_page("home", "Home", QWidget(), comment="First")

    assert shell.set_page_title("home", "Accueil", "Premier") is True

    assert shell.page("home").title == "Accueil"
    assert shell.header("home").title_label.text() == "Accueil"
    assert shell.header("home").comment_label.text() == "Premier"
    # The navigation entry too — a window retitled in two places out of three is
    # worse than one not retitled at all.
    assert [b for b in shell.findChildren(QPushButton) if b.text() == "Accueil"]


def test_retitling_keeps_the_comment_it_already_had(shell):
    shell.add_page("home", "Home", QWidget(), comment="First")
    shell.set_page_title("home", "Accueil")
    assert shell.header("home").comment_label.text() == "First"
    assert shell.page("home").comment == "First"


def test_retitling_an_unknown_page_is_refused(shell):
    assert shell.set_page_title("nowhere", "Nowhere") is False


def test_the_shell_retranslates_its_own_strings(spec):
    shell = AppShell(spec, translate=lambda key, **kwargs: f"<{key}>")
    shell.drawer_button.setToolTip("something else")
    shell.retranslate()
    assert shell.drawer_button.toolTip() == "<gesso.shell.toggle_navigation>"


def test_run_app_refuses_a_build_that_returns_something_other_than_a_widget(
    monkeypatch, qapp, spec
):
    """A non-widget return is a mistake, and the message should say so.

    Without this the failure is `'dict' object has no attribute 'show'` from
    deep inside Qt's start-up, which names neither the cause nor the caller.
    """
    monkeypatch.setattr(QApplication, "exec", lambda self: 0)

    with pytest.raises(TypeError, match="expects a QWidget"):
        run_app(spec, lambda shell: {"pages": "not a window"})
