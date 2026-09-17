"""Tests for the icon tier.

Rendering is checked by reading pixels back, because "the icon appeared" and
"the icon was tinted" are different claims and only the second one is the point
of the module.
"""

from __future__ import annotations

import re

import pytest

from gesso.ui.icons import (
    DEFAULT_SIZE,
    DEFAULT_TINT,
    ICONS_DIR,
    ROLE_TOKENS,
    IconError,
    IconRegistry,
    ThemedIcons,
)

SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
    'viewBox="0 0 24 24" fill="none" stroke="#000" stroke-width="4">'
    '<line x1="2" y1="12" x2="22" y2="12" /></svg>'
)


def strongest_color(pixmap):
    """The most opaque pixel, which for a stroked icon is the pure tint."""
    image = pixmap.toImage()
    best = None
    best_alpha = -1
    for y in range(image.height()):
        for x in range(image.width()):
            colour = image.pixelColor(x, y)
            if colour.alpha() > best_alpha:
                best, best_alpha = colour, colour.alpha()
    return best


@pytest.fixture(scope="module")
def qapp():
    from PySide6.QtWidgets import QApplication

    application = QApplication.instance() or QApplication([])
    yield application
    application.setStyleSheet("")


# ----------------------------------------------------------------------
# The registry
# ----------------------------------------------------------------------


def test_the_shipped_icons_are_found():
    names = IconRegistry().names()
    assert {"chevron-up", "chevron-down", "check", "close", "warning", "info"} <= set(names)


def test_the_icon_set_contains_no_stray_assets():
    """Everything in the icon directory is an SVG, or the module itself.

    A stray file here is usually a forgotten export or a copied asset that
    never made it into the registry.
    """
    unexpected = [
        path.name
        for path in ICONS_DIR.iterdir()
        if path.is_file() and path.suffix not in (".svg", ".py")
    ]
    assert unexpected == []


def test_has_and_path_agree():
    registry = IconRegistry()
    assert registry.has("check")
    assert registry.path("check").is_file()


def test_an_unknown_icon_names_the_alternatives():
    # "no icon called 'refrsh'" is a typo you want to see immediately, with the
    # list of what does exist.
    with pytest.raises(IconError) as excinfo:
        IconRegistry().render_pixmap("refrsh")
    message = str(excinfo.value)
    assert "refrsh" in message and "refresh" in message


def test_source_returns_the_svg():
    assert IconRegistry().source("check").lstrip().startswith("<svg")


def test_later_directories_win(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    (first / "shared.svg").write_text(SVG, encoding="utf-8")
    (second / "shared.svg").write_text(SVG, encoding="utf-8")

    registry = IconRegistry([first, second])

    assert registry.path("shared").parent == second


def test_add_directory_gives_the_new_one_priority(tmp_path):
    override = tmp_path / "override"
    override.mkdir()
    (override / "check.svg").write_text(SVG, encoding="utf-8")

    registry = IconRegistry()
    registry.add_directory(override)

    assert registry.path("check").parent == override
    # Gesso's own icons are still reachable.
    assert registry.has("close")


def test_an_application_can_add_icons_without_forking_the_set(tmp_path):
    custom = tmp_path / "icons"
    custom.mkdir()
    (custom / "sparkle.svg").write_text(SVG, encoding="utf-8")

    registry = IconRegistry()
    registry.add_directory(custom)

    assert "sparkle" in registry.names()
    assert "check" in registry.names()


# ----------------------------------------------------------------------
# Rendering and tinting
# ----------------------------------------------------------------------


def test_render_produces_a_pixmap_of_the_requested_size(qapp):
    pixmap = IconRegistry().render_pixmap("check", size=32)
    assert pixmap.width() == 32 and pixmap.height() == 32


def test_render_tints_the_artwork(qapp):
    # The whole point: the SVG's own stroke colour is irrelevant.
    pixmap = IconRegistry().render_pixmap("check", size=24, tint="#ff0000")
    colour = strongest_color(pixmap)
    assert colour.alpha() > 0
    assert colour.red() > 200 and colour.green() < 60 and colour.blue() < 60


def test_render_without_a_tint_keeps_the_original_colours(qapp):
    pixmap = IconRegistry().render_pixmap("check", size=24, tint=None)
    colour = strongest_color(pixmap)
    assert colour.alpha() > 0
    # The shipped artwork is grey, so the channels agree.
    assert abs(colour.red() - colour.green()) < 12
    assert abs(colour.green() - colour.blue()) < 12


def test_the_background_is_transparent(qapp):
    pixmap = IconRegistry().render_pixmap("check", size=24, tint="#ffffff")
    image = pixmap.toImage()
    assert image.pixelColor(0, 0).alpha() == 0


def test_make_icon_can_add_several_sizes(qapp):
    icon = IconRegistry().make_icon("check", size=16, sizes=(16, 32, 64))
    assert not icon.isNull()
    sizes = {(size.width(), size.height()) for size in icon.availableSizes()}
    assert (32, 32) in sizes and (64, 64) in sizes


# ----------------------------------------------------------------------
# Theme-following icons
# ----------------------------------------------------------------------


@pytest.fixture
def themes(qapp):
    from gesso.ui.theme import ThemeManager

    return ThemeManager(qapp)


def test_every_role_maps_to_a_real_contract_token():
    from gesso.ui.theme import BASE_CONTRACT

    for role, token in ROLE_TOKENS.items():
        assert token in BASE_CONTRACT, f"role {role!r} points at unknown token {token!r}"


def test_an_unknown_role_names_the_alternatives(themes):
    with pytest.raises(IconError) as excinfo:
        ThemedIcons(theme_manager=themes).color("sideways")
    assert "sideways" in str(excinfo.value)


def test_roles_resolve_to_the_contract_defaults_before_a_theme_is_applied(themes):
    # An icon built before the first apply() must still come out the colour the
    # stylesheet will use.
    from gesso.ui.theme import BASE_CONTRACT

    icons = ThemedIcons(theme_manager=themes)
    assert icons.color("idle") == BASE_CONTRACT.token("text_muted").default
    assert icons.color("active") == BASE_CONTRACT.token("accent").default


def test_roles_follow_the_applied_theme(themes):
    themes.apply("light")
    icons = ThemedIcons(theme_manager=themes)
    assert icons.color("active") == themes.current["accent"]


def test_make_icon_uses_the_role_colour(qapp, themes):
    themes.apply("dark")
    icons = ThemedIcons(theme_manager=themes)
    pixmap = icons.render_pixmap("check", role="active", size=24)
    expected = themes.current["accent"]

    colour = strongest_color(pixmap)
    assert f"#{colour.red():02x}{colour.green():02x}{colour.blue():02x}" == expected.lower()


def test_an_unknown_icon_still_raises_through_themed_icons(themes):
    with pytest.raises(IconError):
        ThemedIcons(theme_manager=themes).make_icon("nope")


def test_changing_theme_fires_icons_changed(themes):
    icons = ThemedIcons(theme_manager=themes)
    seen = []
    icons.iconsChanged.connect(lambda: seen.append(True))

    themes.apply("light")

    assert seen, "widgets holding icons need telling so they can rebuild them"


def test_icons_work_without_a_theme_manager():
    # The manager is optional: an application with no theming still renders.
    icons = ThemedIcons()
    assert icons.color("idle") == DEFAULT_TINT
    assert not icons.make_icon("check", size=DEFAULT_SIZE).isNull()


# ----------------------------------------------------------------------
# The stylesheet's icon references
# ----------------------------------------------------------------------


def test_every_icon_the_stylesheet_references_exists():
    """The stylesheet and the icon set cannot drift apart unnoticed.

    The same idea as the token check in the theme tests: a reference to an icon
    that is not shipped renders as *nothing at all*, with no error.
    """
    from gesso.ui.theme import BASE_QSS_PATH

    source = BASE_QSS_PATH.read_text(encoding="utf-8")
    referenced = set(re.findall(r"\$\{icon_dir\}/([\w-]+)\.svg", source))
    assert referenced, "the stylesheet should reference at least one icon"

    registry = IconRegistry()
    missing = sorted(name for name in referenced if not registry.has(name))
    assert missing == []
