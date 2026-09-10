"""Tests for XDG base-directory resolution and per-application paths."""

from __future__ import annotations

from pathlib import Path

import pytest

from gesso.core import paths
from gesso.core.paths import AppPaths

XDG_VARS = ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME")


def _clear_xdg(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in XDG_VARS:
        monkeypatch.delenv(var, raising=False)


def test_defaults_when_unset(monkeypatch):
    _clear_xdg(monkeypatch)
    home = Path.home()
    assert paths.xdg_config_home() == home / ".config"
    assert paths.xdg_data_home() == home / ".local/share"
    assert paths.xdg_cache_home() == home / ".cache"
    assert paths.xdg_state_home() == home / ".local/state"


def test_env_overrides_default(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    assert paths.xdg_config_home() == tmp_path / "cfg"


def test_empty_env_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", "")
    assert paths.xdg_config_home() == Path.home() / ".config"


def test_relative_env_is_ignored(monkeypatch):
    # The XDG spec requires absolute paths; a relative one must be discarded
    # rather than resolved against the current working directory.
    monkeypatch.setenv("XDG_CONFIG_HOME", "relative/config")
    assert paths.xdg_config_home() == Path.home() / ".config"


@pytest.fixture
def layout(tmp_path):
    return AppPaths.resolve(
        "demo",
        config_home=tmp_path / "cfg",
        data_home=tmp_path / "data",
        cache_home=tmp_path / "cache",
        state_home=tmp_path / "state",
    )


def test_directory_layout(layout, tmp_path):
    assert layout.config_dir == tmp_path / "cfg" / "demo"
    assert layout.data_dir == tmp_path / "data" / "demo"
    assert layout.cache_dir == tmp_path / "cache" / "demo"
    assert layout.state_dir == tmp_path / "state" / "demo"


def test_all_dirs_is_stable_order(layout):
    assert layout.all_dirs() == (
        layout.config_dir,
        layout.data_dir,
        layout.cache_dir,
        layout.state_dir,
    )


def test_ensure_creates_every_directory(layout):
    layout.ensure()
    for directory in layout.all_dirs():
        assert directory.is_dir()


def test_subdir(layout):
    assert layout.subdir("config", "themes") == layout.config_dir / "themes"
    assert layout.subdir("data") == layout.data_dir


def test_subdir_rejects_unknown_base(layout):
    with pytest.raises(ValueError):
        layout.subdir("nonsense")


def test_empty_app_id_is_rejected():
    with pytest.raises(ValueError):
        AppPaths.resolve("")
