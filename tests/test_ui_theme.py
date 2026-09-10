"""Tests for the design-system tier.

The token contract and the renderer need no toolkit, so most of this file runs
without Qt at all. The manager tests create a single ``QApplication`` on
demand rather than pulling in a pytest plugin.
"""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

from gesso.ui.theme import (
    BASE_CONTRACT,
    BASE_QSS_PATH,
    EXTRA_KEYS,
    TOKEN_GROUPS,
    QssError,
    Token,
    TokenContract,
    missing_tokens,
    placeholders,
    render,
)

# ----------------------------------------------------------------------
# The token contract
# ----------------------------------------------------------------------


def test_the_contract_rejects_a_duplicate_token():
    with pytest.raises(ValueError):
        TokenContract([Token("a", "#000"), Token("a", "#111")])


def test_defaults_cover_every_token():
    defaults = BASE_CONTRACT.defaults()
    assert set(defaults) == set(BASE_CONTRACT.keys())


def test_every_default_is_a_colour():
    for key, value in BASE_CONTRACT.defaults().items():
        assert value.startswith("#") and len(value) in (4, 7, 9), f"{key} = {value!r}"


def test_tokens_declare_a_known_group():
    for token in BASE_CONTRACT:
        assert token.group in TOKEN_GROUPS, f"{token.key} has group {token.group!r}"


def test_unknown_reports_a_typo():
    # The reason this exists: a misspelt token is otherwise ignored, and the
    # accent silently stays at its default with nothing to explain why.
    assert BASE_CONTRACT.unknown({"accent": "#fff", "acccent": "#000"}) == ["acccent"]


def test_missing_reports_absent_tokens():
    assert "accent" in BASE_CONTRACT.missing({"window": "#000"})


def test_resolve_layers_later_values_over_earlier_ones():
    resolved = BASE_CONTRACT.resolve({"accent": "#111111"}, {"accent": "#222222"})
    assert resolved["accent"] == "#222222"
    # Everything not overridden still comes from the defaults.
    assert resolved["window"] == BASE_CONTRACT.token("window").default


def test_resolve_stringifies_values():
    assert BASE_CONTRACT.resolve({"accent": 42})["accent"] == "42"


def test_groups_are_ordered_and_complete():
    groups = BASE_CONTRACT.groups()
    assert list(groups)[0] == TOKEN_GROUPS[0]
    assert sum(len(tokens) for tokens in groups.values()) == len(BASE_CONTRACT)


# ----------------------------------------------------------------------
# The renderer (Qt-free)
# ----------------------------------------------------------------------


def test_the_stylesheet_exists_and_uses_tokens():
    assert BASE_QSS_PATH.exists()
    assert placeholders(), "the base stylesheet should be token-driven"


def test_every_placeholder_is_a_contract_token():
    # The stylesheet and the contract cannot drift apart unnoticed. `icon_dir`
    # is the one deliberate exception: a path, not a design token.
    unknown = [
        name
        for name in placeholders()
        if name not in BASE_CONTRACT and name not in EXTRA_KEYS
    ]
    assert unknown == []


def test_missing_tokens_reports_every_gap_at_once():
    # Qt's own substitute() raises on the first token it cannot find, which
    # turns one broken palette into a sequence of one-at-a-time discoveries.
    partial = {"window": "#000"}
    missing = missing_tokens(partial)
    assert "accent" in missing and "text" in missing
    assert len(missing) > 1


def test_render_produces_no_unsubstituted_placeholders():
    sheet = render(BASE_CONTRACT.defaults(), {"icon_dir": "/tmp/icons"})
    assert "${" not in sheet
    assert "QPushButton" in sheet


def test_render_names_every_missing_token_in_the_error():
    with pytest.raises(QssError) as excinfo:
        render({"window": "#000"})
    message = str(excinfo.value)
    assert "accent" in message and "text" in message


def test_render_accepts_extra_values_beyond_the_contract():
    sheet = render(BASE_CONTRACT.defaults(), {"icon_dir": "/somewhere"})
    assert "/somewhere/chevron-up.svg" in sheet


# ----------------------------------------------------------------------
# The manager (Qt-backed)
# ----------------------------------------------------------------------


@pytest.fixture(scope="module")
def qapp():
    """One QApplication for the whole module, created on demand."""
    from PySide6.QtWidgets import QApplication

    application = QApplication.instance() or QApplication([])
    yield application
    application.setStyleSheet("")


@pytest.fixture
def palettes(tmp_path):
    """A writable builtin directory and a user override directory."""
    builtin = tmp_path / "builtin"
    user = tmp_path / "user"
    builtin.mkdir()
    user.mkdir()
    (builtin / "sample.json").write_text(
        json.dumps({"description": "A sample", "colors": {"accent": "#111111"}}),
        encoding="utf-8",
    )
    return builtin, user


def test_the_built_in_themes_ship_with_the_package():
    from gesso.ui.theme import ThemeManager

    manager = ThemeManager()
    assert {"dark", "light"} <= set(manager.names())


def test_loading_resolves_every_contract_token():
    from gesso.ui.theme import ThemeManager

    theme = ThemeManager().load("dark")
    assert set(theme.colors) >= set(BASE_CONTRACT.keys())


def test_a_partial_theme_inherits_the_rest(palettes):
    from gesso.ui.theme import ThemeManager

    builtin, user = palettes
    theme = ThemeManager(builtin_dirs=[builtin], user_dir=user).load("sample")

    assert theme["accent"] == "#111111"  # the theme's own value
    assert theme["window"] == BASE_CONTRACT.token("window").default  # inherited
    assert theme.is_explicit("accent") is True
    assert theme.is_explicit("window") is False


def test_a_user_file_wins_over_the_builtin(palettes):
    from gesso.ui.theme import ThemeManager

    builtin, user = palettes
    (user / "sample.json").write_text(
        json.dumps({"colors": {"accent": "#222222"}}), encoding="utf-8"
    )
    theme = ThemeManager(builtin_dirs=[builtin], user_dir=user).load("sample")
    assert theme["accent"] == "#222222"


def test_a_typo_in_a_theme_is_reported(palettes):
    from gesso.ui.theme import ThemeManager

    builtin, user = palettes
    (builtin / "sample.json").write_text(
        json.dumps({"colors": {"acccent": "#111111"}}), encoding="utf-8"
    )
    problems = ThemeManager(builtin_dirs=[builtin], user_dir=user).problems("sample")
    assert any("acccent" in problem for problem in problems)


def test_coverage_separates_set_inherited_and_unknown(palettes):
    from gesso.ui.theme import ThemeManager

    builtin, user = palettes
    coverage = ThemeManager(builtin_dirs=[builtin], user_dir=user).coverage("sample")
    assert "accent" in coverage["explicit"]
    assert "window" in coverage["inherited"]
    assert coverage["unknown"] == []


def test_a_malformed_palette_does_not_break_loading(palettes):
    from gesso.ui.theme import ThemeManager

    builtin, user = palettes
    (builtin / "broken.json").write_text("{ not json", encoding="utf-8")
    theme = ThemeManager(builtin_dirs=[builtin], user_dir=user).load("broken")
    # It resolves to the contract defaults rather than raising.
    assert theme.colors == BASE_CONTRACT.defaults()


def test_apply_without_an_application_is_a_no_op(palettes):
    from gesso.ui.theme import ThemeManager

    builtin, user = palettes
    assert ThemeManager(builtin_dirs=[builtin], user_dir=user).apply("sample") is False


def test_apply_sets_both_stylesheet_and_palette(qapp, palettes):
    from gesso.ui.theme import ThemeManager

    builtin, user = palettes
    manager = ThemeManager(qapp, builtin_dirs=[builtin], user_dir=user)

    assert manager.apply("sample") is True

    sheet = qapp.styleSheet()
    assert "${" not in sheet
    assert "QPushButton" in sheet
    # The palette matters too: Qt draws tooltips and other native furniture
    # from it, not from the stylesheet.
    assert qapp.palette().color(qapp.palette().ColorRole.Window).name() != ""


def test_apply_emits_the_change_signal(qapp, palettes):
    from gesso.ui.theme import ThemeManager

    builtin, user = palettes
    manager = ThemeManager(qapp, builtin_dirs=[builtin], user_dir=user)
    seen = []
    manager.themeChanged.connect(seen.append)

    manager.apply("sample")

    assert seen == ["sample"]
    assert manager.current is not None
    assert manager.current.name == "sample"


def test_reapplying_the_same_theme_does_not_re_emit(qapp, palettes):
    from gesso.ui.theme import ThemeManager

    builtin, user = palettes
    manager = ThemeManager(qapp, builtin_dirs=[builtin], user_dir=user)
    seen = []
    manager.themeChanged.connect(seen.append)

    manager.apply("sample")
    manager.apply("sample")

    # Widgets re-tint on a *change*; a redundant signal would make every
    # application redraw for nothing.
    assert seen == ["sample"]


# ----------------------------------------------------------------------
# The tier boundary
# ----------------------------------------------------------------------


def test_importing_the_lower_tiers_does_not_import_qt():
    """`import gesso` must never pull in a toolkit.

    That is the whole point of the tiering, and it is easy to break by adding
    one eager import. A subprocess is the only honest way to check it: within
    this process Qt is already loaded.
    """
    code = (
        "import sys, gesso, gesso.core, gesso.config, gesso.i18n\n"
        "loaded = [m for m in sys.modules if m.split('.')[0] == 'PySide6']\n"
        "assert not loaded, f'Qt was imported: {loaded}'\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr


def test_the_token_contract_is_usable_without_qt():
    code = (
        "from gesso.ui.theme import BASE_CONTRACT, render\n"
        "sheet = render(BASE_CONTRACT.defaults(), {'icon_dir': '/tmp'})\n"
        "assert '${' not in sheet\n"
        "import sys\n"
        "assert not [m for m in sys.modules if m.split('.')[0] == 'PySide6']\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
