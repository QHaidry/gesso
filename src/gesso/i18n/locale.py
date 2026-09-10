"""Language codes, detection and text direction.

Gesso keeps this deliberately small and dependency-free: a locale string is
reduced to a two-letter code, the user's preference is read from the
environment, and direction comes from a static table.

Anything needing real CLDR data — plural rules, number and date formatting — is
left to an optional backend rather than guessed at here. A wrong date format
shipped as a "feature" is worse than an honest absence.
"""

from __future__ import annotations

import locale as _locale
import os
from typing import Mapping, Optional

__all__ = [
    "DEFAULT_LANGUAGE",
    "RTL_LANGUAGES",
    "normalize_lang",
    "detect_language",
    "is_rtl",
]

#: Used when nothing better can be determined, and as the translation fallback.
DEFAULT_LANGUAGE = "en"

#: Languages written right-to-left. Both the modern and legacy ISO codes for
#: Hebrew and Persian/Kurdish are listed, because either may appear in a locale.
RTL_LANGUAGES = frozenset(
    {"ar", "ckb", "dv", "fa", "he", "iw", "ku", "ps", "sd", "ug", "ur", "yi"}
)

#: Environment variables consulted, in order of precedence. ``LANGUAGE`` wins
#: because it is the only one intended as an explicit priority list.
_LANGUAGE_VARS = ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG")

#: Values meaning "no locale chosen", which are not languages at all.
_UNSET_LOCALES = frozenset({"", "c", "posix"})


def normalize_lang(code: Optional[str]) -> str:
    """Reduce a locale string to a lowercase two-letter language code.

    Returns ``""`` when there is no language to find, so callers can tell
    "unspecified" apart from a genuine fallback.

    >>> normalize_lang("en_US.UTF-8")
    'en'
    >>> normalize_lang("pt-BR")
    'pt'
    >>> normalize_lang("sr_RS@latin")
    'sr'
    >>> normalize_lang("C")
    ''
    """
    if not code:
        return ""
    text = code.strip()
    if not text:
        return ""
    # LANGUAGE is a colon-separated priority list; take the first entry.
    text = text.split(":")[0]
    # Strip an encoding (en_US.UTF-8) and a modifier (sr_RS@latin).
    text = text.split(".")[0]
    text = text.split("@")[0]
    # Territory may be separated by an underscore or a hyphen.
    text = text.replace("-", "_").split("_")[0]
    text = text.strip().lower()
    return "" if text in _UNSET_LOCALES else text


def detect_language(env: Optional[Mapping[str, str]] = None) -> str:
    """Detect the user's preferred language, falling back to English.

    *env* defaults to :data:`os.environ`; passing a mapping makes this testable
    without mutating the process environment.
    """
    environment = os.environ if env is None else env

    for var in _LANGUAGE_VARS:
        code = normalize_lang(environment.get(var, ""))
        if code:
            return code

    # Last resort: whatever the C library thinks, which is what every other
    # application on the system will be using.
    try:
        code = normalize_lang(_locale.getlocale()[0])
    except (TypeError, ValueError):
        code = ""
    if code:
        return code

    return DEFAULT_LANGUAGE


def is_rtl(language: Optional[str]) -> bool:
    """Whether *language* is written right-to-left."""
    return normalize_lang(language) in RTL_LANGUAGES
