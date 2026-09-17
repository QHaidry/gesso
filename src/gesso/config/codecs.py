"""Document codecs — JSON, TOML and YAML behind one interface.

The configuration *schema* knows nothing about file formats. A codec turns a
document on disk into a plain ``dict`` and back, so which format is in use is a
property of the *file* (its extension) rather than of its contents. That is
what sidesteps the chicken-and-egg of storing "my format is YAML" inside the
config file itself.

TOML and YAML are optional capabilities. A codec whose third-party dependency
is missing reports :meth:`Codec.available` as ``False`` with an actionable
reason, instead of raising ``ImportError`` somewhere unrelated later.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

__all__ = [
    "CodecError",
    "Codec",
    "JsonCodec",
    "TomlCodec",
    "YamlCodec",
    "builtin_codecs",
    "codec_for_name",
    "codec_for_extension",
    "codec_for_path",
    "DISCOVERY_PRECEDENCE",
]


class CodecError(Exception):
    """Raised when a document cannot be decoded or encoded."""


class Codec:
    """Base class for document encodings.

    Subclasses must define :attr:`name`, :attr:`extensions` and the
    :meth:`loads` / :meth:`dumps` pair.
    """

    name: str = ""
    extensions: Tuple[str, ...] = ()

    # -- capability ----------------------------------------------------
    def available(self) -> bool:
        """Whether this codec can both read *and* write right now."""
        return True

    def unavailable_reason(self) -> str:
        """A user-facing explanation for why :meth:`available` is ``False``."""
        return ""

    # -- document I/O --------------------------------------------------
    def loads(self, text: str) -> Dict[str, Any]:
        """Decode *text* into a mapping. An empty document is ``{}``."""
        raise NotImplementedError

    def dumps(self, data: Dict[str, Any]) -> str:
        """Encode *data* into text, ending with a trailing newline."""
        raise NotImplementedError

    # -- helpers -------------------------------------------------------
    @staticmethod
    def _require_table(data: Any, origin: str) -> Dict[str, Any]:
        """Guard the invariant that a config document is a table/object."""
        if not isinstance(data, dict):
            raise CodecError(
                f"{origin}: expected a table/object at the top level, "
                f"got {type(data).__name__}"
            )
        return data


class JsonCodec(Codec):
    """UTF-8 JSON. Always available (stdlib), but cannot carry comments."""

    name = "json"
    extensions = (".json",)

    def loads(self, text: str) -> Dict[str, Any]:
        if not text.strip():
            return {}
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise CodecError(f"invalid JSON: {exc}") from exc
        return self._require_table(data, "JSON")

    def dumps(self, data: Dict[str, Any]) -> str:
        return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


class TomlCodec(Codec):
    """TOML. Reading uses stdlib ``tomllib`` on 3.11+ (else ``tomli``);
    writing always needs the third-party ``tomli-w``."""

    name = "toml"
    extensions = (".toml",)

    def __init__(self) -> None:
        self._reader = None
        self._writer = None
        self._reason = ""

    def _resolve(self) -> None:
        """Import the backends once, recording *why* if that fails."""
        if self._reader is not None or self._reason:
            return
        try:
            import tomllib as reader  # Python 3.11+
        except ModuleNotFoundError:  # pragma: no cover - only on <=3.10
            try:
                import tomli as reader  # type: ignore[no-redef]
            except ModuleNotFoundError:
                self._reason = (
                    "TOML requires Python 3.11+ or the 'tomli' package "
                    "(pip install 'gesso-sdk[toml]')"
                )
                return
        try:
            import tomli_w as writer
        except ModuleNotFoundError:
            self._reason = (
                "writing TOML requires the 'tomli-w' package "
                "(pip install 'gesso-sdk[toml]')"
            )
            return
        self._reader = reader
        self._writer = writer

    def available(self) -> bool:
        self._resolve()
        return self._reader is not None and self._writer is not None

    def unavailable_reason(self) -> str:
        self._resolve()
        return self._reason

    def loads(self, text: str) -> Dict[str, Any]:
        if not self.available():
            raise CodecError(self._reason)
        if not text.strip():
            return {}
        try:
            data = self._reader.loads(text)
        except ValueError as exc:  # TOMLDecodeError subclasses ValueError
            raise CodecError(f"invalid TOML: {exc}") from exc
        return self._require_table(data, "TOML")

    def dumps(self, data: Dict[str, Any]) -> str:
        if not self.available():
            raise CodecError(self._reason)
        return self._writer.dumps(data)


class YamlCodec(Codec):
    """YAML via ``PyYAML``.

    Only :func:`yaml.safe_load` is ever used. Note that YAML is the loosest of
    the three: unquoted ``no`` decodes to ``False`` and PyYAML does not
    preserve comments on a round-trip. The typed schema is what keeps that
    looseness from reaching the application.
    """

    name = "yaml"
    extensions = (".yaml", ".yml")

    def __init__(self) -> None:
        self._yaml = None
        self._reason = ""

    def _resolve(self) -> None:
        if self._yaml is not None or self._reason:
            return
        try:
            import yaml
        except ModuleNotFoundError:
            self._reason = (
                "YAML requires the 'PyYAML' package "
                "(pip install 'gesso-sdk[yaml]')"
            )
            return
        self._yaml = yaml

    def available(self) -> bool:
        self._resolve()
        return self._yaml is not None

    def unavailable_reason(self) -> str:
        self._resolve()
        return self._reason

    def loads(self, text: str) -> Dict[str, Any]:
        if not self.available():
            raise CodecError(self._reason)
        if not text.strip():
            return {}
        try:
            data = self._yaml.safe_load(text)
        except self._yaml.YAMLError as exc:
            raise CodecError(f"invalid YAML: {exc}") from exc
        if data is None:
            return {}
        return self._require_table(data, "YAML")

    def dumps(self, data: Dict[str, Any]) -> str:
        if not self.available():
            raise CodecError(self._reason)
        return self._yaml.safe_dump(
            data, sort_keys=False, allow_unicode=True, default_flow_style=False
        )


# Order in which formats are considered when more than one config file exists
# in a directory. A store may nominate a preferred format, which is tried first.
DISCOVERY_PRECEDENCE: Tuple[str, ...] = ("json", "toml", "yaml")

# A single shared set of codec instances: they cache whether their optional
# backend could be imported, so re-creating them per call would be wasteful.
_CODECS: Tuple[Codec, ...] = (JsonCodec(), TomlCodec(), YamlCodec())


def builtin_codecs() -> Tuple[Codec, ...]:
    """The codecs Gesso ships with."""
    return _CODECS


def codec_for_name(name: str) -> Codec:
    """Look a codec up by format name (``"json"``, ``".toml"``, ...)."""
    wanted = name.strip().lower().lstrip(".")
    for codec in _CODECS:
        if codec.name == wanted:
            return codec
    known = ", ".join(codec.name for codec in _CODECS)
    raise LookupError(f"unknown configuration format {name!r}; known formats: {known}")


def codec_for_extension(extension: str) -> Optional[Codec]:
    """Look a codec up by file extension, or ``None`` if unrecognised."""
    wanted = extension if extension.startswith(".") else f".{extension}"
    wanted = wanted.lower()
    for codec in _CODECS:
        if wanted in codec.extensions:
            return codec
    return None


def codec_for_path(path: Any) -> Optional[Codec]:
    """Look a codec up from a path's suffix, or ``None`` if unrecognised."""
    return codec_for_extension(Path(path).suffix)
