"""Tests for catalog merging, override ordering and lookup."""

from __future__ import annotations

import json

import pytest

from gesso.core import AppContext, AppSpec
from gesso.core.paths import AppPaths
from gesso.i18n import DirectorySource, MappingSource, Translator


def catalog(**catalogs):
    """Build an in-memory source; ``catalog(en={...}, fr={...})``."""
    return MappingSource(catalogs)


# ----------------------------------------------------------------------
# Lookup
# ----------------------------------------------------------------------


def test_translates_a_dotted_key():
    source = catalog(en={"app": {"greeting": "Hello"}})
    translator = Translator([source], language="en", include_framework=False)
    assert translator.t("app.greeting") == "Hello"


def test_missing_key_returns_the_key_itself():
    translator = Translator([], language="en", include_framework=False)
    # Visible in the UI and findable with grep — better than an empty string.
    assert translator.t("app.nope") == "app.nope"


def test_missing_key_returns_the_given_default():
    translator = Translator([], language="en", include_framework=False)
    assert translator.t("app.nope", default="Fallback") == "Fallback"


def test_a_non_string_value_is_not_a_translation():
    source = catalog(en={"app": {"section": {"a": "1"}}})
    translator = Translator([source], language="en", include_framework=False)
    assert translator.t("app.section") == "app.section"
    assert translator.t("app.section", default="x") == "x"


def test_placeholders_are_formatted():
    source = catalog(en={"app": {"greeting": "Hello, {name}!"}})
    translator = Translator([source], language="en", include_framework=False)
    assert translator.t("app.greeting", name="Ada") == "Hello, Ada!"


def test_a_broken_placeholder_does_not_raise():
    # A stray brace in a translation must not take down the interface.
    source = catalog(en={"app": {"greeting": "Hello, {name"}})
    translator = Translator([source], language="en", include_framework=False)
    assert translator.t("app.greeting", name="Ada") == "Hello, {name"


def test_has_reports_resolvable_keys():
    source = catalog(en={"app": {"greeting": "Hello"}})
    translator = Translator([source], language="en", include_framework=False)
    assert translator.has("app.greeting") is True
    assert translator.has("app.missing") is False


def test_a_placeholder_may_be_named_key():
    # Regression: Muralis's API-key messages use {key}, which collided with the
    # translator's own parameter name and raised
    # "t() got multiple values for argument 'key'". The key is positional-only
    # now, so no placeholder can be shadowed by the signature.
    source = catalog(en={"app": {"hint": "Your key is {key}"}})
    translator = Translator([source], language="en", include_framework=False)
    assert translator.t("app.hint", key="abc123") == "Your key is abc123"


# ----------------------------------------------------------------------
# Fallback and override
# ----------------------------------------------------------------------


def test_missing_keys_fall_back_to_the_fallback_language():
    source = catalog(
        en={"app": {"greeting": "Hello", "farewell": "Goodbye"}},
        fr={"app": {"greeting": "Bonjour"}},
    )
    translator = Translator([source], language="fr", include_framework=False, fallback="en")
    assert translator.t("app.greeting") == "Bonjour"
    assert translator.t("app.farewell") == "Goodbye"  # not in fr


def test_partial_translations_merge_rather_than_replace():
    source = catalog(
        en={"app": {"menu": {"file": "File", "edit": "Edit"}}},
        fr={"app": {"menu": {"file": "Fichier"}}},
    )
    translator = Translator([source], language="fr", include_framework=False, fallback="en")
    assert translator.t("app.menu.file") == "Fichier"
    assert translator.t("app.menu.edit") == "Edit"  # sibling survives the merge


def test_later_sources_win():
    low = catalog(en={"app": {"greeting": "low"}})
    high = catalog(en={"app": {"greeting": "high"}})
    translator = Translator([low, high], language="en", include_framework=False)
    assert translator.t("app.greeting") == "high"


def test_later_sources_still_inherit_earlier_keys():
    low = catalog(en={"app": {"a": "1", "b": "2"}})
    high = catalog(en={"app": {"a": "override"}})
    translator = Translator([low, high], language="en", include_framework=False)
    assert translator.t("app.a") == "override"
    assert translator.t("app.b") == "2"


# ----------------------------------------------------------------------
# Language switching
# ----------------------------------------------------------------------


def test_set_language_reloads():
    source = catalog(en={"app": {"greeting": "Hello"}}, fr={"app": {"greeting": "Bonjour"}})
    translator = Translator([source], language="en", include_framework=False)
    assert translator.t("app.greeting") == "Hello"
    translator.set_language("fr")
    assert translator.language == "fr"
    assert translator.t("app.greeting") == "Bonjour"


def test_languages_lists_every_source():
    source = catalog(en={}, fr={}, de={})
    translator = Translator([source], language="en", include_framework=False)
    assert translator.languages() == ["de", "en", "fr"]


def test_catalogs_returns_a_copy():
    source = catalog(en={"app": {"greeting": "Hello"}})
    translator = Translator([source], language="en", include_framework=False)
    snapshot = translator.catalogs()
    snapshot["app"]["greeting"] = "mutated"
    assert translator.t("app.greeting") == "Hello"


# ----------------------------------------------------------------------
# Directory sources
# ----------------------------------------------------------------------


def test_directory_source_reads_language_files(tmp_path):
    (tmp_path / "en.json").write_text(json.dumps({"app": {"greeting": "Hello"}}))
    source = DirectorySource(tmp_path)
    assert source.catalog("en") == {"app": {"greeting": "Hello"}}
    assert source.catalog("fr") == {}
    assert source.languages() == ["en"]


def test_directory_source_tolerates_broken_json(tmp_path):
    (tmp_path / "en.json").write_text("{ not json")
    assert DirectorySource(tmp_path).catalog("en") == {}


def test_directory_source_missing_directory_is_empty(tmp_path):
    source = DirectorySource(tmp_path / "nope")
    assert source.catalog("en") == {}
    assert source.languages() == []


# ----------------------------------------------------------------------
# Framework catalogs
# ----------------------------------------------------------------------


def test_framework_strings_are_available_by_default():
    translator = Translator(language="en")
    assert translator.t("gesso.button.cancel") == "Cancel"


def test_framework_strings_are_translated():
    translator = Translator(language="fr")
    assert translator.t("gesso.button.cancel") == "Annuler"


def test_unknown_language_falls_back_to_english_framework_strings():
    translator = Translator(language="de")
    assert translator.t("gesso.button.cancel") == "Cancel"


def test_framework_can_be_excluded():
    translator = Translator(language="en", include_framework=False)
    assert translator.t("gesso.button.cancel") == "gesso.button.cancel"


# ----------------------------------------------------------------------
# Application wiring
# ----------------------------------------------------------------------


def test_for_app_layers_application_and_user_sources(tmp_path):
    app_locales = tmp_path / "locales"
    app_locales.mkdir()
    (app_locales / "en.json").write_text(json.dumps({"app": {"greeting": "Hello", "a": "1"}}))

    context = AppContext(AppSpec("Demo"), AppPaths.resolve("demo", config_home=tmp_path))
    # The user's override directory sits beside their settings.
    user_dir = context.paths.subdir("config", "i18n")
    user_dir.mkdir(parents=True)
    (user_dir / "en.json").write_text(json.dumps({"app": {"a": "user"}}))

    translator = Translator.for_app(context, language="en", locale_dir=app_locales)

    assert translator.t("app.greeting") == "Hello"  # from the application
    assert translator.t("app.a") == "user"  # user override wins
    assert translator.t("gesso.button.ok") == "OK"  # framework still present


def test_for_app_accepts_an_in_memory_source(tmp_path):
    context = AppContext(AppSpec("Demo"), AppPaths.resolve("demo", config_home=tmp_path))
    translator = Translator.for_app(context, language="en", source=catalog(en={"app": {"g": "x"}}))
    assert translator.t("app.g") == "x"


def test_for_app_works_when_no_directories_exist(tmp_path):
    context = AppContext(AppSpec("Demo"), AppPaths.resolve("demo", config_home=tmp_path))
    translator = Translator.for_app(context, language="en")
    assert translator.t("gesso.button.ok") == "OK"


def test_invalid_language_argument_falls_back(tmp_path):
    translator = Translator([], language="C", include_framework=False, fallback="en")
    assert translator.language == "en"
