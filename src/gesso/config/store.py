"""Schema-typed, format-agnostic configuration store.

A :class:`ConfigStore` answers one question — *where is this application's
config, and in which format?* — and then keeps a schema-validated copy of it in
memory. The format is a property of the file, resolved once at construction:

1. an explicit path (format taken from its suffix),
2. otherwise a scan of the config directory, using a precedence order,
3. otherwise the application's preferred format, which is then created.

TOML and YAML are only *discoverable* when their optional backend is installed.
If a config file exists whose backend is missing, the store raises
:class:`ConfigError` rather than silently starting a second config file in a
different format — the failure mode that makes "which file is live?" ambiguous.
"""

from __future__ import annotations

import copy
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from .codecs import (
    DISCOVERY_PRECEDENCE,
    Codec,
    CodecError,
    builtin_codecs,
    codec_for_extension,
    codec_for_name,
)
from .schema import Schema

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..core.app import AppContext

__all__ = ["ConfigError", "ConfigStore"]


class ConfigError(Exception):
    """Raised when a configuration cannot be located, read or written."""


def _ordered_codecs(preferred: str) -> List[Codec]:
    """Built-in codecs with *preferred* first, then the default precedence."""
    codecs = list(builtin_codecs())
    by_name = {codec.name: codec for codec in codecs}
    ordered: List[Codec] = []
    for name in (preferred,) + tuple(DISCOVERY_PRECEDENCE):
        codec = by_name.get(name)
        if codec is not None and codec not in ordered:
            ordered.append(codec)
    for codec in codecs:
        if codec not in ordered:
            ordered.append(codec)
    return ordered


def _atomic_write(path: Path, text: str) -> None:
    """Write *text* to *path* through a temp file + rename.

    A crash or full disk can therefore never leave a half-written config behind
    for the next run to trip over.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    handle_fd, tmp_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp"
    )
    tmp = Path(tmp_name)
    try:
        with os.fdopen(handle_fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise


def _merge_defaults(schema: Schema, raw: Dict[str, Any]) -> Dict[str, Any]:
    """Overlay *raw* onto the schema defaults.

    Values that coerce cleanly are stored in their declared type. Values that
    do not — and keys the schema has never heard of — are *preserved* rather
    than dropped, so loading a config never destroys a user's data; the
    problems surface through :meth:`ConfigStore.validate` instead.
    """
    merged = schema.defaults()
    for section_name, options in raw.items():
        if not isinstance(options, dict):
            merged[section_name] = options
            continue
        target = merged.setdefault(section_name, {})
        for key, value in options.items():
            option = schema.option(section_name, key)
            if option is None:
                target[key] = value
                continue
            try:
                target[key] = option.coerce(value)
            except ValueError:
                target[key] = value
    return merged


class ConfigStore:
    """An application's configuration file, bound to a schema."""

    def __init__(self, schema: Schema, path: Path, codec: Codec) -> None:
        self._schema = schema
        self._path = Path(path)
        self._codec = codec
        self._data: Dict[str, Any] = schema.defaults()
        #: Other config files found alongside this one during discovery.
        self.others: Tuple[Path, ...] = ()

    # -- construction --------------------------------------------------
    @classmethod
    def for_path(cls, schema: Schema, path: Any) -> "ConfigStore":
        """Bind to an explicit *path*, taking the format from its suffix."""
        path = Path(path)
        codec = codec_for_extension(path.suffix)
        if codec is None:
            known = ", ".join(ext for c in builtin_codecs() for ext in c.extensions)
            raise ConfigError(
                f"cannot tell which format {path} is (suffix {path.suffix!r}); "
                f"known suffixes: {known}"
            )
        if not codec.available():
            raise ConfigError(codec.unavailable_reason())
        return cls(schema, path, codec)

    @classmethod
    def for_format(
        cls, schema: Schema, directory: Any, fmt: str, *, stem: str = "config"
    ) -> "ConfigStore":
        """Bind to ``<directory>/<stem>.<ext>`` for an explicitly chosen format."""
        codec = codec_for_name(fmt)
        if not codec.available():
            raise ConfigError(codec.unavailable_reason())
        return cls(schema, Path(directory) / f"{stem}{codec.extensions[0]}", codec)

    @classmethod
    def discover(
        cls,
        schema: Schema,
        directory: Any,
        *,
        stem: str = "config",
        preferred: str = "json",
    ) -> "ConfigStore":
        """Find the config in *directory*, or plan to create one in *preferred*.

        ``others`` is populated when more than one config file is present, so
        the caller can warn about the ambiguity instead of guessing silently.
        """
        directory = Path(directory)
        matches: List[Tuple[Path, Codec]] = []
        for codec in _ordered_codecs(preferred):
            for extension in codec.extensions:
                candidate = directory / f"{stem}{extension}"
                if not candidate.exists():
                    continue
                if not codec.available():
                    raise ConfigError(f"found {candidate} but {codec.unavailable_reason()}")
                matches.append((candidate, codec))
                break
        if not matches:
            return cls.for_format(schema, directory, preferred, stem=stem)
        path, codec = matches[0]
        store = cls(schema, path, codec)
        store.others = tuple(other for other, _ in matches[1:])
        return store

    @classmethod
    def for_app(
        cls, schema: Schema, context: "AppContext", *, preferred: Optional[str] = None
    ) -> "ConfigStore":
        """Discover the config for an :class:`~gesso.core.app.AppContext`."""
        return cls.discover(
            schema,
            context.config_dir,
            stem=context.spec.config_stem,
            preferred=preferred or context.spec.default_config_format,
        )

    # -- introspection -------------------------------------------------
    @property
    def schema(self) -> Schema:
        return self._schema

    @property
    def path(self) -> Path:
        return self._path

    @property
    def codec(self) -> Codec:
        return self._codec

    @property
    def format(self) -> str:
        return self._codec.name

    def exists(self) -> bool:
        return self._path.exists()

    # -- document I/O --------------------------------------------------
    def load(self) -> "ConfigStore":
        """Read the file (if present), apply defaults, and return ``self``."""
        raw: Dict[str, Any] = {}
        if self._path.exists():
            try:
                text = self._path.read_text(encoding="utf-8")
            except OSError as exc:
                raise ConfigError(f"cannot read {self._path}: {exc}") from exc
            try:
                raw = self._codec.loads(text)
            except CodecError as exc:
                raise ConfigError(f"{self._path}: {exc}") from exc
        self._data = _merge_defaults(self._schema, raw)
        return self

    def reload(self) -> "ConfigStore":
        """Re-read from disk, picking up external edits."""
        return self.load()

    def save(self) -> None:
        """Write the configuration to disk, atomically."""
        try:
            text = self._codec.dumps(self._data)
        except CodecError as exc:
            raise ConfigError(f"cannot encode {self._path}: {exc}") from exc
        _atomic_write(self._path, text)

    # -- values --------------------------------------------------------
    def get(self, dotted: str, default: Any = None) -> Any:
        """Read ``"section.key"`` (or ``"section"`` for a whole table)."""
        section, separator, key = dotted.partition(".")
        if not separator:
            return self._data.get(section, default)
        table = self._data.get(section)
        if not isinstance(table, dict):
            return default
        return table.get(key, default)

    def set(self, dotted: str, value: Any) -> None:
        """Write ``"section.key"``, coercing to the schema's declared type."""
        section, separator, key = dotted.partition(".")
        if not separator:
            raise ConfigError(f"expected 'section.key', got {dotted!r}")
        option = self._schema.option(section, key)
        if option is not None:
            try:
                value = option.coerce(value)
            except ValueError as exc:
                raise ConfigError(f"{dotted}: {exc}") from exc
        table = self._data.setdefault(section, {})
        if not isinstance(table, dict):
            raise ConfigError(f"[{section}] is not a table, so {dotted} cannot be set")
        table[key] = value

    def as_dict(self) -> Dict[str, Any]:
        """A deep copy of the whole configuration."""
        return copy.deepcopy(self._data)

    def validate(self) -> List[str]:
        """Problems with the current values; empty means valid."""
        return self._schema.validate(self._data)

    def reset(self) -> None:
        """Restore every value to the schema default (does not write)."""
        self._data = self._schema.defaults()

    # -- format migration ----------------------------------------------
    def convert_to(self, fmt: str, *, keep_backup: bool = True) -> Path:
        """Rewrite the config in another format and return the new path.

        The previous file is kept as ``<name>.bak`` unless *keep_backup* is
        False, so a conversion is never silently destructive.
        """
        target = codec_for_name(fmt)
        if not target.available():
            raise ConfigError(target.unavailable_reason())
        new_path = self._path.with_suffix(target.extensions[0])
        if new_path == self._path:
            return self._path
        if new_path.exists():
            raise ConfigError(f"refusing to overwrite existing {new_path}")
        try:
            text = target.dumps(self._data)
        except CodecError as exc:
            raise ConfigError(f"cannot encode {new_path}: {exc}") from exc
        _atomic_write(new_path, text)
        if self._path.exists():
            if keep_backup:
                os.replace(self._path, Path(str(self._path) + ".bak"))
            else:
                self._path.unlink()
        self._path = new_path
        self._codec = target
        return new_path
