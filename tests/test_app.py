"""Tests for application identity (AppSpec) and its bound context."""

from __future__ import annotations

import pytest

from gesso.core import AppContext, AppSpec, slugify
from gesso.core.paths import AppPaths


def test_slugify():
    assert slugify("Muralis") == "muralis"
    assert slugify("My Fancy App") == "my-fancy-app"
    assert slugify("  spaced  out  ") == "spaced-out"
    assert slugify("!!!") == "app"


def test_minimal_spec_derives_id_and_display_name():
    spec = AppSpec("Muralis")
    assert spec.app_id == "muralis"
    assert spec.display_name == "Muralis"
    assert spec.default_config_format == "json"


def test_explicit_fields_win():
    spec = AppSpec("Muralis", app_id="org.quoxiom.muralis", display_name="Muralis Wallpapers")
    assert spec.app_id == "org.quoxiom.muralis"
    assert spec.display_name == "Muralis Wallpapers"


def test_blank_name_is_rejected():
    with pytest.raises(ValueError):
        AppSpec("   ")


def test_spec_is_immutable():
    spec = AppSpec("Muralis")
    with pytest.raises(Exception):
        spec.name = "Other"  # type: ignore[misc]


def test_context_uses_injected_paths(tmp_path):
    spec = AppSpec("Muralis")
    paths = AppPaths.resolve("muralis", config_home=tmp_path)
    context = AppContext(spec, paths)
    assert context.app_id == "muralis"
    assert context.name == "Muralis"
    assert context.config_dir == tmp_path / "muralis"


def test_config_file_follows_spec_format(tmp_path):
    spec = AppSpec("Muralis", default_config_format="toml")
    context = AppContext(spec, AppPaths.resolve("muralis", config_home=tmp_path))
    assert context.config_file() == tmp_path / "muralis" / "config.toml"


def test_config_file_accepts_explicit_extension(tmp_path):
    context = AppContext(AppSpec("Muralis"), AppPaths.resolve("muralis", config_home=tmp_path))
    assert context.config_file("yaml") == tmp_path / "muralis" / "config.yaml"
    assert context.config_file(".yaml") == tmp_path / "muralis" / "config.yaml"
