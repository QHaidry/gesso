"""Application identity and path resolution — no third-party dependencies."""

from .app import AppContext, AppSpec, slugify
from .paths import (
    AppPaths,
    xdg_cache_home,
    xdg_config_home,
    xdg_data_home,
    xdg_state_home,
)

__all__ = [
    "AppContext",
    "AppSpec",
    "slugify",
    "AppPaths",
    "xdg_config_home",
    "xdg_data_home",
    "xdg_cache_home",
    "xdg_state_home",
]
