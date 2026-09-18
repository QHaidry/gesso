"""The tutorials must run, exactly as the pages tell a reader to run them.

Every one is driven as a **subprocess**, not imported. That is the point: the
documentation shows a command line, so the thing under test should be that
command line. It also lets `palette.py` honestly report that it never imported
PySide6 — which it could not do inside a suite where other tests already have.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TUTORIALS = REPO / "examples" / "tutorials"


def run(*args: str, cwd: Path, expect: int = 0) -> subprocess.CompletedProcess:
    """Run a tutorial the way the page says to."""
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(REPO / "src"), str(TUTORIALS), env.get("PYTHONPATH", "")]
    )
    # No display, and no window: every one of these either prints or checks.
    env["QT_QPA_PLATFORM"] = "offscreen"

    result = subprocess.run(
        [sys.executable, str(TUTORIALS / args[0]), *args[1:]],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == expect, (
        f"{' '.join(args)} exited {result.returncode}\n"
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )
    return result


# ----------------------------------------------------------------------
# Store a setting
# ----------------------------------------------------------------------


def test_settings_runs(tmp_path):
    out = run("settings.py", cwd=tmp_path).stdout
    assert "settings live in" in out
    assert "minutes: 25 (int)" in out


def test_settings_coerces_and_writes(tmp_path):
    run("settings.py", cwd=tmp_path)
    written = json.loads((tmp_path / "pomodoro-home" / "pomodoro" / "config.json").read_text())
    # "50" was a string and "no" was not a boolean; both arrived typed.
    assert written["timer"]["minutes"] == 50
    assert written["timer"]["chime"] is False


def test_settings_refuses_an_out_of_range_value(tmp_path):
    out = run("settings.py", "--break", cwd=tmp_path).stdout
    assert "exceeds the maximum of 180" in out
    # ...and the refusal is specific, not just "invalid".
    assert "is not one of: work, break" in out

    written = json.loads((tmp_path / "pomodoro-home" / "pomodoro" / "config.json").read_text())
    assert written["timer"]["minutes"] == 50


def test_settings_reports_a_missing_codec_rather_than_working_around_it(tmp_path):
    """`--toml` may not have a writer installed; either way it must not crash.

    The tutorial runs on whatever the reader has, so both outcomes are correct
    — and the failure names the package to install.
    """
    out = run("settings.py", "--toml", cwd=tmp_path).stdout
    assert "rewritten as toml" in out or "tomli-w" in out


# ----------------------------------------------------------------------
# Translate
# ----------------------------------------------------------------------


def test_greeting_translates(tmp_path):
    out = run("greeting.py", cwd=tmp_path).stdout
    assert "hello    Hello, Ada!" in out
    assert "1 -> 1 item" in out
    assert "2 -> 2 items" in out


def test_greeting_picks_the_language_it_was_given(tmp_path):
    out = run("greeting.py", "--language", "fr", cwd=tmp_path).stdout
    assert "hello    Bonjour, Ada !" in out
    assert "1 -> 1 article" in out
    assert "2 -> 2 articles" in out


def test_greeting_lets_the_user_override_a_string(tmp_path):
    """The user's catalog is consulted last, so it wins."""
    out = run("greeting.py", "--language", "fr", cwd=tmp_path).stdout
    assert "application only: Pomodoro" in out
    assert "with the user's:  Pomodoro (personnalisé)" in out


def test_greeting_returns_a_missing_key_rather_than_an_empty_string(tmp_path):
    out = run("greeting.py", cwd=tmp_path).stdout
    assert "'greeting.untitled'" in out


# ----------------------------------------------------------------------
# The token contract
# ----------------------------------------------------------------------


def test_palette_never_imports_qt(tmp_path):
    """The Qt-free half of the design system really is Qt-free."""
    out = run("palette.py", cwd=tmp_path).stdout
    assert "PySide6 modules loaded: none" in out


def test_palette_reports_the_contract(tmp_path):
    out = run("palette.py", cwd=tmp_path).stdout
    assert "the contract declares 30 tokens in 9 groups" in out
    assert "6 given + contract defaults = 30 tokens" in out


def test_palette_names_a_typo(tmp_path):
    out = run("palette.py", cwd=tmp_path).stdout
    assert "unknown tokens: ['acccent']" in out


def test_palette_reports_the_one_placeholder_that_is_not_a_token(tmp_path):
    out = run("palette.py", cwd=tmp_path).stdout
    assert "render refused" in out
    assert "icon_dir" in out


# ----------------------------------------------------------------------
# Icons, widgets, the shell
# ----------------------------------------------------------------------


def test_icons_layers_rather_than_replaces(tmp_path):
    out = run("icons.py", cwd=tmp_path).stdout
    # The tutorial's own icon, and Gesso's, in one registry.
    assert "knows 'star'?   True" in out
    assert "knows 'check'?  True" in out


def test_icons_shows_what_replacing_would_cost(tmp_path):
    out = run("icons.py", cwd=tmp_path).stdout
    assert "my directory alone provides: ['star']" in out
    assert "knows 'check'?  False" in out


def test_icons_names_the_alternatives_on_a_typo(tmp_path):
    out = run("icons.py", cwd=tmp_path).stdout
    assert "no icon named 'str'" in out
    assert "star" in out


def test_pane_is_styled_entirely_by_object_name(tmp_path):
    out = run("pane.py", "--check", cwd=tmp_path).stdout
    assert "unstyled: none - every name has a rule" in out
    for name in ("#card", "#emptyState", "#segGroup", "#rowLabel", "#pageHeader"):
        assert name in out


def test_window_builds_and_closes(tmp_path):
    result = run("window.py", "--check", cwd=tmp_path)
    assert result.returncode == 0
