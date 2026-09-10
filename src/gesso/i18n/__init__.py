"""Internationalisation: catalogs, language detection and lookup.

Translation catalogs are JSON, looked up by dotted key. They are searched in
priority order — framework, then application, then the user's overrides — with
the fallback language filling any gaps.

    >>> from gesso.i18n import MappingSource, Translator
    >>> source = MappingSource({"en": {"app": {"greeting": "Hello, {name}!"}}})
    >>> Translator([source], language="en", include_framework=False).t(
    ...     "app.greeting", name="Ada"
    ... )
    'Hello, Ada!'

No Qt, no third-party dependencies. Plural rules and locale-aware number and
date formatting need real CLDR data and are not implemented here; see the
roadmap for the planned optional backend.
"""

from .locale import (
    DEFAULT_LANGUAGE,
    RTL_LANGUAGES,
    detect_language,
    is_rtl,
    normalize_lang,
)
from .sources import DirectorySource, MappingSource
from .translator import FRAMEWORK_LOCALES_DIR, Translator

__all__ = [
    "DEFAULT_LANGUAGE",
    "RTL_LANGUAGES",
    "normalize_lang",
    "detect_language",
    "is_rtl",
    "DirectorySource",
    "MappingSource",
    "Translator",
    "FRAMEWORK_LOCALES_DIR",
]
