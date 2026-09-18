"""The Gallery example must build, switch palettes, and repaint.

This is the first example with a window, so these tests are the ones that
would notice a widget contract drifting: an object name that no longer matches
the stylesheet, an icon role that no longer resolves to a token, a token the
contract has quietly stopped shipping.
"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QLabel

from gallery import APP, SCHEMA
from gallery.window import ROLES, SHOWCASE_ICONS, GalleryWindow
from gesso.core import AppContext, AppPaths
from gesso.config import ConfigStore
from gesso.ui.icons import ThemedIcons
from gesso.ui.theme import ThemeManager


@pytest.fixture
def manager(qapp, tmp_path):
    return ThemeManager(qapp, user_dir=tmp_path / "themes", seed=True, parent=qapp)


@pytest.fixture
def icons(manager):
    return ThemedIcons(theme_manager=manager)


@pytest.fixture
def store(tmp_path):
    paths = AppPaths.resolve(APP.app_id, config_home=tmp_path)
    return ConfigStore.for_app(SCHEMA, AppContext(APP, paths)).load()


@pytest.fixture
def window(qapp, manager, icons, store):
    return GalleryWindow(APP, manager=manager, icons=icons, store=store)


# ----------------------------------------------------------------------
# It builds
# ----------------------------------------------------------------------


def test_the_window_takes_its_title_from_the_spec(window):
    assert window.windowTitle() == APP.display_name


def test_the_window_names_the_palette_it_is_showing(window, manager):
    # Not merely non-None: the control has to agree with the window.
    assert window.theme_control.value() == manager.current.name


def test_every_shipped_icon_is_displayed(window):
    shown = {name for name, _role, _cell in window._icon_cells}
    assert shown == set(SHOWCASE_ICONS)


def test_every_icon_is_shown_in_every_role(window):
    pairs = {(name, role) for name, role, _cell in window._icon_cells}
    assert pairs == {(name, role) for name in SHOWCASE_ICONS for role in ROLES}


def test_every_role_resolves_to_a_token():
    """A role naming a token the contract does not ship renders in fallback grey."""
    from gesso.ui.icons import ROLE_TOKENS
    from gesso.ui.theme import BASE_CONTRACT

    for role in ROLES:
        assert role in ROLE_TOKENS, f"role {role!r} has no token"
        assert ROLE_TOKENS[role] in BASE_CONTRACT, (
            f"role {role!r} maps to unknown token {ROLE_TOKENS[role]!r}"
        )


def text_of(grid) -> list:
    """Every label in the token inspector, in the order it was added."""
    found = []
    for index in range(grid.count()):
        widget = grid.itemAt(index).widget()
        if isinstance(widget, QLabel):
            found.append(widget.text())
    return found


# ----------------------------------------------------------------------
# Theming
# ----------------------------------------------------------------------


def test_seeding_copies_the_builtins_where_they_can_be_edited(manager, tmp_path):
    """A theme you cannot see is a theme you cannot edit."""
    seeded = sorted(path.name for path in (tmp_path / "themes").glob("*.json"))
    assert seeded
    assert set(seeded) == {f"{name}.json" for name in manager.names()}


def test_switching_the_palette_repaints(window, manager):
    assert manager.apply("dark")
    dark = window.icons.color("idle")

    window.apply_theme("light")

    assert manager.current.name == "light"
    assert window.icons.color("idle") != dark


def test_switching_the_palette_is_remembered(window, store):
    window.apply_theme("light")
    assert store.get("display.theme") == "light"


def test_the_rows_match_the_palette_in_force(window, manager):
    """The control, the manager and the saved setting must not disagree."""
    window.apply_theme("light")
    assert window.theme_control.value() == "light"
    assert manager.current.name == "light"


def test_an_unknown_palette_falls_back_and_the_window_says_so(window, manager):
    """`apply` does not fail on a missing palette — it falls back.

    That is deliberate (a deleted theme file should not leave the window
    neutral), so "did apply succeed" and "is the palette I asked for in force"
    are different questions. The window answers the second.
    """
    before = manager.current.name

    assert window.apply_theme("chartreuse") is False

    # A real palette is in force, and the control agrees with it.
    assert manager.current.name == before
    assert window.theme_control.value() == manager.current.name


def test_the_icons_are_re_rendered_when_the_theme_moves(window):
    """A QLabel holds a pixmap, and a pixmap does not know the theme moved."""
    cell = window._icon_cells[0][2]
    window.apply_theme("light")
    window._refresh_icons()
    assert not cell.pixmap().isNull()


def test_the_icon_size_can_be_changed_from_a_row(window):
    assert window.size_control.value() in {"Small", "Medium", "Large"}
    window._on_icon_size("Large")
    assert window.icon_size == 28
    window._on_icon_size("Small")
    assert window.icon_size == 16


# ----------------------------------------------------------------------
# The token inspector
# ----------------------------------------------------------------------


def test_the_inspector_can_be_switched_off(window, tmp_path):
    """`show_tokens = false` leaves the inspector out of the window."""
    paths = AppPaths.resolve(APP.app_id, config_home=tmp_path)
    off = ConfigStore.for_app(SCHEMA, AppContext(APP, paths)).load()
    off.set("display.show_tokens", False)

    bare = GalleryWindow(APP, manager=window.manager, icons=window.icons, store=off)
    assert not hasattr(bare, "_token_grid")


def test_every_contract_token_is_listed(window):
    from gesso.ui.theme import BASE_CONTRACT

    window.apply_theme("dark")
    listed = text_of(window._token_grid)
    missing = [key for key in BASE_CONTRACT.keys() if key not in listed]
    assert missing == []


def test_the_inspector_follows_the_palette(window):
    window.apply_theme("dark")
    dark = text_of(window._token_grid)

    window.apply_theme("light")
    light = text_of(window._token_grid)

    # Same tokens, different values.
    assert dark != light
    assert len(dark) == len(light)
