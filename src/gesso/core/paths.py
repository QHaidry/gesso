"""XDG base-directory resolution and per-application path layout.

Gesso never hard-codes ``~/.config/<app>``. Instead an application describes
itself with a :class:`~gesso.core.app.AppSpec`, and every path it needs is
derived from the XDG base directories plus that application's id. That is what
lets the same code serve Muralis, a second application, or a test suite with a
throwaway profile.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

__all__ = [
    "xdg_config_home",
    "xdg_data_home",
    "xdg_cache_home",
    "xdg_state_home",
    "AppPaths",
]


def _env_dir(var: str, default: str) -> Path:
    """Return an XDG base directory from the environment, or its default.

    Per the XDG Base Directory specification an unset *or empty* variable falls
    back to the default, and a relative path is invalid and therefore ignored.
    """
    value = os.environ.get(var, "").strip()
    if value and os.path.isabs(value):
        return Path(value)
    return Path(default).expanduser()


def xdg_config_home() -> Path:
    """``$XDG_CONFIG_HOME`` (default ``~/.config``)."""
    return _env_dir("XDG_CONFIG_HOME", "~/.config")


def xdg_data_home() -> Path:
    """``$XDG_DATA_HOME`` (default ``~/.local/share``)."""
    return _env_dir("XDG_DATA_HOME", "~/.local/share")


def xdg_cache_home() -> Path:
    """``$XDG_CACHE_HOME`` (default ``~/.cache``)."""
    return _env_dir("XDG_CACHE_HOME", "~/.cache")


def xdg_state_home() -> Path:
    """``$XDG_STATE_HOME`` (default ``~/.local/state``)."""
    return _env_dir("XDG_STATE_HOME", "~/.local/state")


@dataclass(frozen=True)
class AppPaths:
    """The XDG directories belonging to a single application.

    The base directories are stored explicitly rather than read from the
    environment on each access, so an application (or a test) can be pointed at
    an isolated tree without mutating ``os.environ``.
    """

    app_id: str
    config_home: Path
    data_home: Path
    cache_home: Path
    state_home: Path

    @classmethod
    def resolve(
        cls,
        app_id: str,
        *,
        config_home: Optional[Path] = None,
        data_home: Optional[Path] = None,
        cache_home: Optional[Path] = None,
        state_home: Optional[Path] = None,
    ) -> "AppPaths":
        """Build the layout for *app_id*, defaulting to the real XDG dirs.

        Explicit values win, which is how tests and portable installs redirect
        an application's files.
        """
        if not app_id:
            raise ValueError("app_id must not be empty")
        return cls(
            app_id=app_id,
            config_home=Path(config_home) if config_home is not None else xdg_config_home(),
            data_home=Path(data_home) if data_home is not None else xdg_data_home(),
            cache_home=Path(cache_home) if cache_home is not None else xdg_cache_home(),
            state_home=Path(state_home) if state_home is not None else xdg_state_home(),
        )

    # -- per-application directories -----------------------------------
    @property
    def config_dir(self) -> Path:
        """``<config_home>/<app_id>`` — user-editable settings, themes, locales."""
        return self.config_home / self.app_id

    @property
    def data_dir(self) -> Path:
        """``<data_home>/<app_id>`` — durable application data."""
        return self.data_home / self.app_id

    @property
    def cache_dir(self) -> Path:
        """``<cache_home>/<app_id>`` — regenerable caches."""
        return self.cache_home / self.app_id

    @property
    def state_dir(self) -> Path:
        """``<state_home>/<app_id>`` — logs and session state."""
        return self.state_home / self.app_id

    def all_dirs(self) -> Tuple[Path, Path, Path, Path]:
        """The four per-application directories, in a stable order."""
        return (self.config_dir, self.data_dir, self.cache_dir, self.state_dir)

    def ensure(self) -> None:
        """Create every per-application directory that does not yet exist."""
        for directory in self.all_dirs():
            directory.mkdir(parents=True, exist_ok=True)

    def subdir(self, base: str, *parts: str) -> Path:
        """Return a directory under one of the four bases.

        ``paths.subdir("config", "themes")`` is ``<config_dir>/themes``.
        """
        try:
            root = {
                "config": self.config_dir,
                "data": self.data_dir,
                "cache": self.cache_dir,
                "state": self.state_dir,
            }[base]
        except KeyError:
            raise ValueError(
                f"unknown base {base!r}; expected one of 'config', 'data', 'cache', 'state'"
            ) from None
        return root.joinpath(*parts)
