"""Tutorial: translate an application, and get plurals right.

Run it::

    PYTHONPATH=src python examples/tutorials/greeting.py
    PYTHONPATH=src python examples/tutorials/greeting.py --language fr
    LANGUAGE=fr_FR.UTF-8 PYTHONPATH=src python examples/tutorials/greeting.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from gesso.i18n import (
    DEFAULT_LANGUAGE,
    DirectorySource,
    MappingSource,
    Translator,
    detect_language,
    is_rtl,
    normalize_lang,
)

HERE = Path(__file__).parent
#: The application's catalogs, shipped with the code.
LOCALES = HERE / "locales"
#: A *user's* overrides. Real applications put this beside the user's settings
#: (`~/.config/<app>/i18n/`), not beside their own; it is next to the code here
#: only so the tutorial is self-contained.
USER_LOCALES = HERE / "user-locales"


def build_translator(language: str | None = None, *, user: bool = True) -> Translator:
    """A translator for this tutorial's catalogs.

    Source order is the whole lesson. Sources are consulted in **ascending
    priority**:

    1. Gesso's own `gesso.*` catalogs (skipped here — this app uses none);
    2. the application's, shipped with the code;
    3. the user's, read from beside their settings.

    So a user can override any string without touching the application — the
    same way a user theme overrides a built-in palette.
    """
    sources = [DirectorySource(LOCALES, name="application")]
    if user:
        sources.append(DirectorySource(USER_LOCALES, name="user"))

    return Translator(
        sources,
        language=language or detect_language() or DEFAULT_LANGUAGE,
        fallback=DEFAULT_LANGUAGE,
        include_framework=False,
    )


def count_of(translator: Translator, key: str, count: int) -> str:
    """Choose the ``.one`` or ``.other`` form of *key* for *count*.

    Gesso does not guess plural rules, and this function is the honest
    consequence. English and French really do have two forms; Russian has
    three and Arabic six, and getting those right needs real CLDR data. So the
    catalogs carry the forms and the application picks — which also means the
    rule stays visible in your code instead of hiding in a library's tables.
    """
    form = "one" if count == 1 else "other"
    return translator.t(f"{key}.{form}", count=count)


def main(argv: list) -> int:
    requested = None
    if "--language" in argv:
        requested = argv[argv.index("--language") + 1]

    print(f"detected from the environment: {detect_language() or '(nothing)'}")
    print(f"normalised:                    {normalize_lang('fr_FR.UTF-8')!r}")
    print()

    translator = build_translator(requested)
    print(f"active language:  {translator.language}")
    print(f"right to left?    {is_rtl(translator.language)}")
    print(f"catalogs provide: {translator.languages()}")
    print()

    print(f"  title    {translator.t('greeting.title')}")
    print(f"  hello    {translator.t('greeting.hello', name='Ada')}")
    print(f"  goodbye  {translator.t('greeting.goodbye', name='Ada')}")

    # A placeholder called `key` is safe, because the translation key is
    # positional-only. That is what `t(key_name, /, **kwargs)` is for.
    print(f"  labelled {translator.t('greeting.labelled', key='Ctrl+K')}")

    print("  counts:")
    for count in (0, 1, 2):
        print(f"    {count} -> {count_of(translator, 'greeting.items', count)}")

    # A key nobody defined comes back as *itself*: visible on screen, greppable
    # in the source, and never an empty string that looks like a layout bug.
    print(f"  missing  {translator.t('greeting.untitled')!r}")

    # ------------------------------------------------------------------
    # The user's overrides, which win because they were consulted last
    # ------------------------------------------------------------------
    application_only = build_translator(requested, user=False)
    print(f"\napplication only: {application_only.t('greeting.title')}")
    print(f"with the user's:  {translator.t('greeting.title')}")

    # A catalog can also live in memory: handy for tests, and for strings that
    # are generated rather than written.
    in_memory = Translator(
        [MappingSource({"en": {"greeting": {"hello": "Hi {name}!"}}})],
        language="en",
        include_framework=False,
    )
    print(f"in memory:        {in_memory.t('greeting.hello', name='Ada')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
