"""The documented example must actually run.

Documentation that cannot drift: these tests drive the very same
``examples/hello.py`` that the guides embed via ``pymdownx.snippets``. If the
example breaks, the docs are wrong too, and this suite says so.
"""

from __future__ import annotations

import json

import hello


def run(tmp_path, *args) -> int:
    """Invoke the example, redirecting its config home into *tmp_path*."""
    return hello.main(["--config-home", str(tmp_path), *args])


def app_dir(tmp_path):
    """Where Gesso actually writes — note the app-id nesting."""
    return tmp_path / "gesso-hello"


def test_prints_the_default_greeting(tmp_path, capsys):
    assert run(tmp_path) == 0
    assert capsys.readouterr().out.strip() == "Hello, World!"


def test_config_is_nested_under_the_app_id(tmp_path, capsys):
    run(tmp_path, "--set", "greeting.name", "Ada")
    capsys.readouterr()
    assert (app_dir(tmp_path) / "config.json").exists()


def test_set_persists_across_runs(tmp_path, capsys):
    run(tmp_path, "--set", "greeting.name", "Ada")
    capsys.readouterr()
    run(tmp_path)
    assert capsys.readouterr().out.strip() == "Hello, Ada!"


def test_values_are_coerced_to_the_declared_type(tmp_path, capsys):
    # Passed as the *string* "true"; the schema turns it into a real bool.
    run(tmp_path, "--set", "greeting.shout", "true")
    capsys.readouterr()
    run(tmp_path)
    assert capsys.readouterr().out.strip() == "HELLO, WORLD!"


def test_repeat_is_stored_as_an_integer(tmp_path, capsys):
    run(tmp_path, "--set", "greeting.repeat", "3")
    capsys.readouterr()
    run(tmp_path)
    assert len(capsys.readouterr().out.strip().splitlines()) == 3


def test_a_bad_value_is_reported_not_silently_accepted(tmp_path, capsys):
    assert run(tmp_path, "--set", "greeting.repeat", "lots") == 2
    assert "cannot read" in capsys.readouterr().err


def test_show_prints_the_whole_configuration(tmp_path, capsys):
    run(tmp_path, "--show")
    payload = json.loads(capsys.readouterr().out)
    assert payload["greeting"]["name"] == "World"


def test_format_flag_selects_the_file_extension(tmp_path, capsys):
    run(tmp_path, "--format", "yaml", "--set", "greeting.name", "Ada")
    capsys.readouterr()
    assert (app_dir(tmp_path) / "config.yaml").exists()


def test_discovery_adopts_an_existing_file_whatever_its_format(tmp_path, capsys):
    # Write YAML first; a later run with no --format must find it rather than
    # creating a second JSON config alongside it.
    run(tmp_path, "--format", "yaml", "--set", "greeting.name", "Ada")
    capsys.readouterr()
    run(tmp_path)
    assert capsys.readouterr().out.strip() == "Hello, Ada!"
    assert not (app_dir(tmp_path) / "config.json").exists()


def test_convert_rewrites_in_another_format(tmp_path):
    run(tmp_path, "--set", "greeting.name", "Ada")
    run(tmp_path, "--convert", "yaml")
    assert (app_dir(tmp_path) / "config.yaml").exists()
    assert (app_dir(tmp_path) / "config.json.bak").exists()
