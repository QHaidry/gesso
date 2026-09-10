"""The design system: a token contract, a stylesheet, and a theme manager.

The token contract and the renderer are **Qt-free**, so a palette can be
checked without opening a window — or installing a toolkit. The manager, which
touches ``QApplication`` and ``QPalette``, is imported lazily on first use:

    >>> from gesso.ui.theme import BASE_CONTRACT, render   # no Qt needed
    >>> from gesso.ui.theme import ThemeManager            # needs Qt

That split is why the imports below stop where they do.
"""

from .qss import (
    BASE_QSS_PATH,
    EXTRA_KEYS,
    QssError,
    missing_tokens,
    placeholders,
    render,
    template,
)
from .tokens import BASE_CONTRACT, TOKEN_GROUPS, Token, TokenContract

__all__ = [
    # Qt-free
    "Token",
    "TokenContract",
    "BASE_CONTRACT",
    "TOKEN_GROUPS",
    "render",
    "template",
    "placeholders",
    "missing_tokens",
    "QssError",
    "BASE_QSS_PATH",
    "EXTRA_KEYS",
    # Qt-backed, resolved on first access
    "Theme",
    "ThemeManager",
    "DEFAULT_THEME",
    "BUILTIN_PALETTES_DIR",
    "ICONS_DIR",
]

_QT_BACKED = frozenset(
    {"Theme", "ThemeManager", "DEFAULT_THEME", "BUILTIN_PALETTES_DIR", "ICONS_DIR"}
)


def __getattr__(name: str):
    """Resolve the Qt-backed names on first use.

    Deferring the import keeps this package importable without PySide6, which
    is what lets the token contract live in the same module tree as the
    manager without dragging Qt into every consumer.
    """
    if name in _QT_BACKED:
        from . import manager

        return getattr(manager, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(list(globals().keys()) + list(_QT_BACKED))
