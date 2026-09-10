"""Rendering the base stylesheet from a theme's tokens.

Deliberately **Qt-free**: substituting tokens into text needs no toolkit, so
this half of the design system is testable without a display, and a mistake in
a palette is caught before any window is opened.

The important behaviour here is :func:`missing_tokens`. Qt's own
``string.Template.substitute`` raises on the *first* token it cannot find,
which turns one broken palette into a sequence of one-at-a-time discoveries.
Gesso reports every missing token at once, because that is the list you need.
"""

from __future__ import annotations

import re
import string
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Tuple

__all__ = [
    "BASE_QSS_PATH",
    "EXTRA_KEYS",
    "QssError",
    "template",
    "placeholders",
    "missing_tokens",
    "render",
]

#: The stylesheet shipped with the package.
BASE_QSS_PATH = Path(__file__).parent / "base.qss"

#: Placeholders the stylesheet needs that are not design tokens. ``icon_dir``
#: is a filesystem path rather than a colour, so it has no place in the token
#: contract - but the stylesheet still cannot render without it.
EXTRA_KEYS: Tuple[str, ...] = ("icon_dir",)

_PLACEHOLDER_RE = re.compile(r"\$\{(\w+)\}")

_template: Optional[string.Template] = None


class QssError(Exception):
    """Raised when a stylesheet cannot be rendered."""


def template() -> string.Template:
    """The base stylesheet as a template, read once and cached."""
    global _template
    if _template is None:
        try:
            text = BASE_QSS_PATH.read_text(encoding="utf-8")
        except OSError as exc:  # pragma: no cover - a broken installation
            raise QssError(f"cannot read the base stylesheet: {exc}") from exc
        _template = string.Template(text)
    return _template


def placeholders(text: Optional[str] = None) -> Tuple[str, ...]:
    """Every token name the stylesheet references, sorted.

    This is the *real* required-token list — derived from the stylesheet rather
    than maintained alongside it, so the two cannot disagree.
    """
    source = template().template if text is None else text
    return tuple(sorted(set(_PLACEHOLDER_RE.findall(source))))


def missing_tokens(colors: Mapping[str, str]) -> List[str]:
    """Tokens the stylesheet needs but *colors* does not supply, sorted."""
    return [name for name in placeholders() if name not in colors]


def render(colors: Mapping[str, str], extra: Optional[Mapping[str, str]] = None) -> str:
    """Substitute *colors* (plus any *extra* values) into the base stylesheet.

    Raises :class:`QssError` naming **every** token that was missing.
    """
    values: Dict[str, str] = {str(key): str(value) for key, value in colors.items()}
    if extra:
        values.update({str(key): str(value) for key, value in extra.items()})

    missing = missing_tokens(values)
    if missing:
        raise QssError(
            "the stylesheet needs tokens that were not provided: " + ", ".join(missing)
        )
    return template().substitute(values)
