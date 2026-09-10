"""Application identity: what an application *is*, and where it keeps files.

An :class:`AppSpec` is the single place an application declares its name, id
and version. Everything downstream — config paths, window titles, QSettings
organisation, the systemd unit name — reads from it, so renaming an app is a
one-line change rather than a grep-and-replace across the codebase.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .paths import AppPaths

__all__ = ["AppSpec", "AppContext", "slugify"]

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(name: str) -> str:
    """Reduce *name* to a lowercase, hyphen-separated identifier.

    ``"Muralis"`` -> ``"muralis"``; ``"My Fancy App"`` -> ``"my-fancy-app"``.
    """
    slug = _SLUG_RE.sub("-", name.strip().lower()).strip("-")
    return slug or "app"


@dataclass(frozen=True)
class AppSpec:
    """A declarative description of an application.

    Only :attr:`name` is required; the remaining fields have sensible defaults
    derived from it, so a minimal spec is ``AppSpec("Muralis")``.
    """

    name: str
    app_id: str = ""
    org: str = ""
    version: str = "0.0.0"
    display_name: str = ""
    description: str = ""
    default_config_format: str = "json"
    config_stem: str = "config"

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("AppSpec.name must not be empty")
        # frozen dataclass: derive the unset fields via object.__setattr__.
        if not self.app_id:
            object.__setattr__(self, "app_id", slugify(self.name))
        if not self.display_name:
            object.__setattr__(self, "display_name", self.name)

    @property
    def config_filename_stem(self) -> str:
        """The config file stem, e.g. ``config`` in ``config.json``."""
        return self.config_stem


class AppContext:
    """An :class:`AppSpec` bound to a resolved set of directories.

    This is the object Gesso's other layers accept instead of reaching for
    ``Path.home()`` themselves.
    """

    def __init__(self, spec: AppSpec, paths: Optional[AppPaths] = None) -> None:
        self.spec = spec
        self.paths = paths if paths is not None else AppPaths.resolve(spec.app_id)

    # -- convenience passthroughs --------------------------------------
    @property
    def app_id(self) -> str:
        return self.spec.app_id

    @property
    def name(self) -> str:
        return self.spec.name

    @property
    def config_dir(self) -> Path:
        return self.paths.config_dir

    @property
    def data_dir(self) -> Path:
        return self.paths.data_dir

    @property
    def cache_dir(self) -> Path:
        return self.paths.cache_dir

    @property
    def state_dir(self) -> Path:
        return self.paths.state_dir

    def config_file(self, extension: Optional[str] = None) -> Path:
        """The config file path for *extension* (default: the app's format).

        ``extension`` may be given with or without a leading dot.
        """
        if extension is None:
            extension = self.spec.default_config_format
        extension = extension.lstrip(".")
        return self.config_dir / f"{self.spec.config_stem}.{extension}"

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"AppContext(app_id={self.app_id!r}, config_dir={str(self.config_dir)!r})"
