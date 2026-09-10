"""Tests for the JSON / TOML / YAML codecs and the codec registry.

The TOML and YAML tests are capability-gated: an optional backend that is not
installed must degrade to a clear, actionable message rather than a crash, and
that behaviour is itself asserted.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from gesso.config import codecs
from gesso.config.codecs import (
    CodecError,
    JsonCodec,
    TomlCodec,
    YamlCodec,
    codec_for_extension,
    codec_for_name,
    codec_for_path,
)

# ----------------------------------------------------------------------
# JSON — always available
# ----------------------------------------------------------------------


def test_json_round_trip_preserves_native_types():
    data = {"general": {"provider": "bing", "auto_update": True, "interval": 86400}}
    codec = JsonCodec()
    assert codec.loads(codec.dumps(data)) == data


def test_json_dumps_ends_with_newline():
    assert JsonCodec().dumps({"a": 1}).endswith("\n")


def test_json_empty_document_is_empty_mapping():
    codec = JsonCodec()
    assert codec.loads("") == {}
    assert codec.loads("   \n") == {}


def test_json_rejects_non_object_document():
    with pytest.raises(CodecError):
        JsonCodec().loads("[1, 2, 3]")


def test_json_rejects_malformed_document():
    with pytest.raises(CodecError):
        JsonCodec().loads("{ not json")


def test_json_is_always_available():
    assert JsonCodec().available() is True
    assert JsonCodec().unavailable_reason() == ""


# ----------------------------------------------------------------------
# TOML — available only when tomli-w is installed
# ----------------------------------------------------------------------


def test_toml_round_trip_when_available():
    codec = TomlCodec()
    if not codec.available():
        pytest.skip("tomli-w is not installed")
    data = {"general": {"provider": "bing", "auto_update": True, "interval": 86400}}
    assert codec.loads(codec.dumps(data)) == data


def test_toml_rejects_non_object_document_when_available():
    codec = TomlCodec()
    if not codec.available():
        pytest.skip("tomli-w is not installed")
    with pytest.raises(CodecError):
        codec.loads("answer = 42")


def test_toml_without_writer_reports_actionable_reason():
    codec = TomlCodec()
    if codec.available():
        pytest.skip("tomli-w is installed")
    assert "tomli-w" in codec.unavailable_reason()
    with pytest.raises(CodecError):
        codec.dumps({"a": 1})
    with pytest.raises(CodecError):
        codec.loads("a = 1")


# ----------------------------------------------------------------------
# YAML — available only when PyYAML is installed
# ----------------------------------------------------------------------


def test_yaml_round_trip_when_available():
    codec = YamlCodec()
    if not codec.available():
        pytest.skip("PyYAML is not installed")
    data = {"general": {"provider": "bing", "auto_update": True, "interval": 86400}}
    assert codec.loads(codec.dumps(data)) == data


def test_yaml_empty_document_is_empty_mapping():
    codec = YamlCodec()
    if not codec.available():
        pytest.skip("PyYAML is not installed")
    assert codec.loads("") == {}
    assert codec.loads("# only a comment\n") == {}


def test_yaml_rejects_non_object_document():
    codec = YamlCodec()
    if not codec.available():
        pytest.skip("PyYAML is not installed")
    with pytest.raises(CodecError):
        codec.loads("- one\n- two\n")


# ----------------------------------------------------------------------
# Registry
# ----------------------------------------------------------------------


def test_codec_for_name_accepts_dotted_and_cased_forms():
    assert codec_for_name("json").name == "json"
    assert codec_for_name("JSON").name == "json"
    assert codec_for_name(".yaml").name == "yaml"


def test_codec_for_name_rejects_unknown():
    with pytest.raises(LookupError):
        codec_for_name("nonsense")


def test_codec_for_extension_and_path():
    assert codec_for_extension(".yml").name == "yaml"
    assert codec_for_extension("toml").name == "toml"
    assert codec_for_extension(".JSON").name == "json"
    assert codec_for_extension(".ini") is None
    assert codec_for_path(Path("config.yaml")).name == "yaml"
    assert codec_for_path(Path("config.ini")) is None


def test_every_registered_extension_resolves_back_to_its_codec():
    for codec in codecs.builtin_codecs():
        for extension in codec.extensions:
            assert codec_for_extension(extension) is codec
