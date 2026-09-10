"""Tests for the ConfigStore: discovery, typing, atomic writes, conversion."""

from __future__ import annotations

import json

import pytest

from gesso.config import ConfigError, ConfigStore, TomlCodec
from gesso.core import AppContext, AppSpec
from gesso.core.paths import AppPaths


def _loaded(tmp_path, schema) -> ConfigStore:
    return ConfigStore.discover(schema, tmp_path).load()


# ----------------------------------------------------------------------
# Discovery
# ----------------------------------------------------------------------


def test_discover_plans_to_create_preferred_format(tmp_path, schema):
    store = ConfigStore.discover(schema, tmp_path)
    assert store.path == tmp_path / "config.json"
    assert store.format == "json"
    assert store.exists() is False
    assert store.others == ()


def test_discover_finds_existing_file(tmp_path, schema):
    (tmp_path / "config.json").write_text("{}")
    store = ConfigStore.discover(schema, tmp_path)
    assert store.path == tmp_path / "config.json"
    assert store.exists() is True


def test_discover_honours_preferred_format_and_reports_others(tmp_path, schema):
    (tmp_path / "config.json").write_text("{}")
    (tmp_path / "config.yaml").write_text("{}")
    store = ConfigStore.discover(schema, tmp_path, preferred="yaml")
    assert store.format == "yaml"
    assert store.others == (tmp_path / "config.json",)


def test_discover_errors_when_backend_for_existing_file_is_missing(tmp_path, schema):
    if TomlCodec().available():
        pytest.skip("tomli-w is installed")
    (tmp_path / "config.toml").write_text("[general]\nprovider = 'bing'\n")
    # Silently creating config.json next to an unreadable config.toml would
    # leave two live configs; failing loudly is the point.
    with pytest.raises(ConfigError) as excinfo:
        ConfigStore.discover(schema, tmp_path)
    assert "tomli-w" in str(excinfo.value)


def test_for_path_rejects_unknown_suffix(tmp_path, schema):
    with pytest.raises(ConfigError):
        ConfigStore.for_path(schema, tmp_path / "config.ini")


def test_for_format_selects_extension(tmp_path, schema):
    assert ConfigStore.for_format(schema, tmp_path, "json").path == tmp_path / "config.json"
    assert ConfigStore.for_format(schema, tmp_path, "yaml").path == tmp_path / "config.yaml"


def test_for_app_uses_context_directories(tmp_path, schema):
    context = AppContext(AppSpec("Demo"), AppPaths.resolve("demo", config_home=tmp_path))
    store = ConfigStore.for_app(schema, context).load()
    assert store.path == tmp_path / "demo" / "config.json"
    store.set("general.provider", "nasa")
    store.save()
    assert (tmp_path / "demo" / "config.json").exists()


# ----------------------------------------------------------------------
# Defaults and typing
# ----------------------------------------------------------------------


def test_load_without_file_yields_defaults(tmp_path, schema):
    store = _loaded(tmp_path, schema)
    assert store.get("general.provider") == "bing"
    assert store.get("general.auto_update") is True
    assert store.validate() == []


def test_set_coerces_to_declared_type(tmp_path, schema):
    store = _loaded(tmp_path, schema)
    store.set("general.auto_update", "false")
    store.set("general.interval", "3600")
    assert store.get("general.auto_update") is False
    assert store.get("general.interval") == 3600


def test_set_rejects_uncoercible_value(tmp_path, schema):
    store = _loaded(tmp_path, schema)
    with pytest.raises(ConfigError):
        store.set("general.interval", "not-a-number")


def test_set_requires_dotted_key(tmp_path, schema):
    store = _loaded(tmp_path, schema)
    with pytest.raises(ConfigError):
        store.set("general", "value")


def test_get_returns_whole_section(tmp_path, schema):
    store = _loaded(tmp_path, schema)
    assert store.get("general")["provider"] == "bing"


def test_load_coerces_on_disk_values(tmp_path, schema):
    (tmp_path / "config.json").write_text(json.dumps({"general": {"auto_update": "false"}}))
    store = _loaded(tmp_path, schema)
    assert store.get("general.auto_update") is False


def test_load_preserves_unknown_keys_and_reports_them(tmp_path, schema):
    (tmp_path / "config.json").write_text(json.dumps({"general": {"mystery": 7}}))
    store = _loaded(tmp_path, schema)
    # Preserved, not dropped — loading a config must never destroy user data.
    assert store.get("general.mystery") == 7
    assert any("unknown option general.mystery" in p for p in store.validate())


def test_reset_restores_defaults(tmp_path, schema):
    store = _loaded(tmp_path, schema)
    store.set("general.provider", "nasa")
    store.reset()
    assert store.get("general.provider") == "bing"


def test_as_dict_is_a_copy(tmp_path, schema):
    store = _loaded(tmp_path, schema)
    snapshot = store.as_dict()
    snapshot["general"]["provider"] = "mutated"
    assert store.get("general.provider") == "bing"


# ----------------------------------------------------------------------
# Persistence
# ----------------------------------------------------------------------


def test_save_then_load_round_trip(tmp_path, schema):
    store = _loaded(tmp_path, schema)
    store.set("general.provider", "nasa")
    store.save()
    assert store.path.exists()
    reloaded = ConfigStore.for_path(schema, store.path).load()
    assert reloaded.get("general.provider") == "nasa"


def test_save_creates_parent_directory(tmp_path, schema):
    target = tmp_path / "nested" / "config.json"
    store = ConfigStore.for_path(schema, target).load()
    store.save()
    assert target.exists()


def test_save_is_atomic_and_leaves_no_temp_files(tmp_path, schema):
    store = _loaded(tmp_path, schema)
    store.save()
    leftovers = [p.name for p in tmp_path.iterdir() if p.name.startswith(".")]
    assert leftovers == []


def test_reload_picks_up_external_edits(tmp_path, schema):
    store = _loaded(tmp_path, schema)
    store.save()
    (tmp_path / "config.json").write_text(json.dumps({"general": {"provider": "pexels"}}))
    store.reload()
    assert store.get("general.provider") == "pexels"


def test_malformed_file_raises_config_error(tmp_path, schema):
    (tmp_path / "config.json").write_text("{ not json")
    with pytest.raises(ConfigError):
        _loaded(tmp_path, schema)


# ----------------------------------------------------------------------
# Format conversion
# ----------------------------------------------------------------------


def test_convert_to_yaml_keeps_a_backup(tmp_path, schema):
    store = _loaded(tmp_path, schema)
    store.set("general.provider", "nasa")
    store.save()

    new_path = store.convert_to("yaml")

    assert new_path == tmp_path / "config.yaml"
    assert store.format == "yaml"
    assert store.path == new_path
    assert (tmp_path / "config.json.bak").exists()
    # The values survive the format change.
    assert ConfigStore.for_path(schema, new_path).load().get("general.provider") == "nasa"


def test_convert_without_backup_removes_original(tmp_path, schema):
    store = _loaded(tmp_path, schema)
    store.save()
    store.convert_to("yaml", keep_backup=False)
    assert not (tmp_path / "config.json").exists()
    assert not (tmp_path / "config.json.bak").exists()
    assert (tmp_path / "config.yaml").exists()


def test_convert_refuses_to_overwrite_existing_file(tmp_path, schema):
    (tmp_path / "config.yaml").write_text("{}")
    # Bind to JSON explicitly: discovery would otherwise adopt the YAML file.
    store = ConfigStore.for_format(schema, tmp_path, "json").load()
    with pytest.raises(ConfigError):
        store.convert_to("yaml")


def test_convert_to_same_format_is_a_no_op(tmp_path, schema):
    store = _loaded(tmp_path, schema)
    assert store.convert_to("json") == store.path
    assert store.format == "json"
