"""Tests for the project generator and the ``gesso`` command.

The one that matters most is
:func:`test_the_generated_project_passes_its_own_tests`. A scaffold that merely
*looks* plausible is worse than none, because a new project's first experience
becomes debugging somebody else's boilerplate. Generating a project and running
its suite is the only way to claim otherwise.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from gesso.cli import main
from gesso.core.app import AppSpec
from gesso.generator import TEMPLATES, ScaffoldError, create, plan, render


def a_spec() -> AppSpec:
    return AppSpec(
        "My App",
        app_id="my-app",
        org="Acme",
        version="2.0.0",
        description="Does one thing well.",
    )


# ----------------------------------------------------------------------
# Planning
# ----------------------------------------------------------------------


def test_plan_covers_every_template():
    planned = plan(a_spec(), year=2026)
    assert len(planned) == len(TEMPLATES)


def test_plan_renders_the_package_name_into_the_paths():
    names = {str(path) for path, _ in plan(a_spec(), year=2026)}
    assert "src/my_app/app.py" in names
    assert "src/my_app/config.py" in names
    assert "tests/test_app.py" in names


def test_a_dotfile_lands_with_its_dot():
    names = {str(path) for path, _ in plan(a_spec(), year=2026)}
    assert ".gitignore" in names
    assert "gitignore" not in names


def test_no_template_leaves_a_placeholder_behind():
    for path, text in plan(a_spec(), year=2026):
        assert "${" not in text, f"{path} still contains a placeholder"


def test_the_substituted_values_reach_the_files():
    planned = dict(plan(a_spec(), year=2026))
    assert "My App" in planned[Path("README.md")]
    assert "Acme" in planned[Path("README.md")]
    assert 'app_id="my-app"' in planned[Path("src/my_app/app.py")]
    assert 'name = "my-app"' in planned[Path("pyproject.toml")]


def test_the_json_templates_are_valid_json():
    # A scaffold that produces an unparseable palette or locale fails at
    # runtime, in the new project, which is the worst place to find out.
    for path, text in plan(a_spec(), year=2026):
        if path.suffix == ".json":
            json.loads(text)


def test_the_rendered_python_compiles():
    for path, text in plan(a_spec(), year=2026):
        if path.suffix == ".py":
            compile(text, str(path), "exec")


def test_the_generated_palette_is_a_partial_theme():
    # Only the tokens worth changing: the rest come from the contract, which is
    # the property that lets a user override three colours and inherit the rest.
    planned = dict(plan(a_spec(), year=2026))
    colours = json.loads(planned[Path("src/my_app/themes/default.json")])["colors"]
    assert colours
    assert len(colours) < 10, "a scaffold palette should stay small"


# ----------------------------------------------------------------------
# Rendering
# ----------------------------------------------------------------------


def test_render_reports_an_unknown_placeholder():
    with pytest.raises(ScaffoldError):
        render("hello ${nope}", {})


def test_render_reports_a_bare_dollar():
    with pytest.raises(ScaffoldError):
        render("costs 5$", {})


def test_render_escapes_a_literal_dollar():
    assert render("costs 5$$", {}) == "costs 5$"


# ----------------------------------------------------------------------
# Writing
# ----------------------------------------------------------------------


def test_create_writes_the_project(tmp_path):
    written = create(a_spec(), tmp_path / "my-app")
    assert len(written) == len(TEMPLATES)
    assert (tmp_path / "my-app" / "pyproject.toml").is_file()
    assert (tmp_path / "my-app" / "src" / "my_app" / "main.py").is_file()


def test_create_refuses_a_directory_that_is_not_empty(tmp_path):
    target = tmp_path / "my-app"
    target.mkdir()
    (target / "something-important").write_text("do not clobber me")

    with pytest.raises(ScaffoldError):
        create(a_spec(), target)

    assert (target / "something-important").exists()


def test_create_can_overwrite_when_asked(tmp_path):
    target = tmp_path / "my-app"
    target.mkdir()
    (target / "something-important").write_text("do not clobber me")

    create(a_spec(), target, overwrite=True)

    assert (target / "pyproject.toml").is_file()


# ----------------------------------------------------------------------
# The command line
# ----------------------------------------------------------------------


def test_the_cli_creates_a_project(tmp_path, capsys):
    assert main(["new", str(tmp_path / "my-app")]) == 0

    assert (tmp_path / "my-app" / "pyproject.toml").is_file()
    assert "Next:" in capsys.readouterr().out


def test_the_cli_reports_a_failure_without_a_traceback(tmp_path, capsys):
    target = tmp_path / "my-app"
    target.mkdir()
    (target / "x").write_text("x")

    assert main(["new", str(target)]) == 1
    assert "error:" in capsys.readouterr().err


def test_the_cli_takes_the_name_from_the_directory(tmp_path):
    main(["new", str(tmp_path / "my-app")])
    pyproject = (tmp_path / "my-app" / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "my-app"' in pyproject


def test_the_cli_accepts_a_name_and_an_id(tmp_path):
    main(["new", str(tmp_path / "here"), "--name", "My App", "--org", "Acme"])
    readme = (tmp_path / "here" / "README.md").read_text(encoding="utf-8")
    assert "My App" in readme
    assert "Acme" in readme


def test_the_cli_without_a_command_prints_help(capsys):
    assert main([]) == 1
    assert "usage" in capsys.readouterr().out.lower()


# ----------------------------------------------------------------------
# The scaffold has to work
# ----------------------------------------------------------------------


def test_the_generated_project_passes_its_own_tests(tmp_path):
    """The scaffold has to run, not merely look right.

    This is the assertion the whole tier exists for: everything else here can
    pass while the generated application is broken.
    """
    project = tmp_path / "my-app"
    create(a_spec(), project)

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=project,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
