"""Schema-typed, format-agnostic configuration management.

JSON, TOML and YAML are all first-class: the format is chosen per file (by
extension), never baked into the application. The schema is what keeps that
flexibility safe, because every value is coerced to its declared type at the
boundary.
"""

from .codecs import (
    DISCOVERY_PRECEDENCE,
    Codec,
    CodecError,
    JsonCodec,
    TomlCodec,
    YamlCodec,
    builtin_codecs,
    codec_for_extension,
    codec_for_name,
    codec_for_path,
)
from .schema import Option, Schema, SchemaError, Section
from .store import ConfigError, ConfigStore

__all__ = [
    "Codec",
    "CodecError",
    "JsonCodec",
    "TomlCodec",
    "YamlCodec",
    "builtin_codecs",
    "codec_for_name",
    "codec_for_extension",
    "codec_for_path",
    "DISCOVERY_PRECEDENCE",
    "Option",
    "Schema",
    "SchemaError",
    "Section",
    "ConfigStore",
    "ConfigError",
]
