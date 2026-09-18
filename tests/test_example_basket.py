"""The Basket example must actually work, in both languages.

Like ``test_example.py`` for ``hello.py``, this drives the real example rather
than a copy of it — and it checks the thing an i18n bug hides behind: a catalog
that is missing a key still *runs*, it just quietly prints English.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Set

from basket import APP, LOCALES_DIR
from basket.cli import main


def run(tmp_path, *args) -> int:
    """Invoke Basket with both homes redirected into *tmp_path*."""
    return main(
        [
            "--config-home",
            str(tmp_path),
            "--data-home",
            str(tmp_path),
            *args,
        ]
    )


def config_file(tmp_path):
    return tmp_path / APP.app_id / "config.json"


def data_file(tmp_path):
    return tmp_path / APP.app_id / "items.json"


def keys_of(catalog: Dict[str, Any], prefix: str = "") -> Set[str]:
    """Every leaf key in a catalog, dotted."""
    found: Set[str] = set()
    for key, value in catalog.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            found |= keys_of(value, path)
        else:
            found.add(path)
    return found


def load_catalog(language: str) -> Dict[str, Any]:
    return json.loads((LOCALES_DIR / f"{language}.json").read_text(encoding="utf-8"))


# ----------------------------------------------------------------------
# The list
# ----------------------------------------------------------------------


def test_an_empty_list_says_so(tmp_path, capsys):
    assert run(tmp_path, "list") == 0
    assert "empty" in capsys.readouterr().out


def test_adding_and_listing(tmp_path, capsys):
    assert run(tmp_path, "add", "milk") == 0
    capsys.readouterr()

    assert run(tmp_path, "list") == 0
    assert "milk" in capsys.readouterr().out


def test_the_list_is_sorted_by_name(tmp_path, capsys):
    for name in ("zucchini", "apple", "milk"):
        run(tmp_path, "add", name)
    capsys.readouterr()

    run(tmp_path, "list")
    out = capsys.readouterr().out
    assert out.index("apple") < out.index("milk") < out.index("zucchini")


def test_prices_are_totalled(tmp_path, capsys):
    run(tmp_path, "add", "milk", "--price", "1.20")
    run(tmp_path, "add", "bread", "--price", "2.30")
    capsys.readouterr()

    run(tmp_path, "list")
    assert "3.50" in capsys.readouterr().out


def test_a_duplicate_is_refused(tmp_path, capsys):
    run(tmp_path, "add", "milk")
    capsys.readouterr()

    assert run(tmp_path, "add", "MILK") == 1
    assert "already" in capsys.readouterr().out


def test_a_name_the_pattern_rejects_is_refused(tmp_path, capsys):
    assert run(tmp_path, "add", "!!!") == 1
    assert "not a usable name" in capsys.readouterr().err


def test_clearing_an_empty_list_is_not_an_error(tmp_path, capsys):
    assert run(tmp_path, "clear") == 0
    assert "already empty" in capsys.readouterr().out


def test_removing_something_that_is_not_there(tmp_path, capsys):
    assert run(tmp_path, "remove", "ghost") == 1
    assert "not on the list" in capsys.readouterr().out


# ----------------------------------------------------------------------
# Settings
# ----------------------------------------------------------------------


def test_the_list_is_capped_by_a_setting(tmp_path, capsys):
    run(tmp_path, "config", "--set", "list.max_items", "2")
    capsys.readouterr()

    run(tmp_path, "add", "one")
    run(tmp_path, "add", "two")
    capsys.readouterr()

    assert run(tmp_path, "add", "three") == 1
    assert "full" in capsys.readouterr().err


def test_the_schema_rejects_an_out_of_range_setting(tmp_path, capsys):
    # 9999 is a perfectly good integer; the *schema* is what refuses it.
    assert run(tmp_path, "config", "--set", "list.max_items", "9999") == 2
    assert "maximum" in capsys.readouterr().err


def test_a_setting_is_coerced_to_its_declared_type(tmp_path, capsys):
    # Passed as the string "false"; the schema stores a real bool.
    run(tmp_path, "config", "--set", "display.show_prices", "false")
    run(tmp_path, "add", "milk", "--price", "1.20")
    capsys.readouterr()

    run(tmp_path, "list")
    assert "1.20" not in capsys.readouterr().out


def test_the_listing_shows_the_declared_defaults(tmp_path, capsys):
    run(tmp_path, "config", "--show")
    out = capsys.readouterr().out
    # Every option, with the description from the schema.
    assert "show_prices" in out
    assert "Refuse to hold more than this many items." in out


def test_nothing_is_written_until_a_setting_changes(tmp_path, capsys):
    """Reading settings must not create a file the user did not ask for."""
    run(tmp_path, "list")
    capsys.readouterr()
    assert not config_file(tmp_path).exists()

    run(tmp_path, "config", "--set", "display.width", "40")
    assert config_file(tmp_path).exists()


def test_the_list_is_data_and_the_settings_are_configuration(tmp_path, capsys):
    run(tmp_path, "add", "milk")
    run(tmp_path, "config", "--set", "display.width", "40")
    capsys.readouterr()

    assert config_file(tmp_path).is_file()
    assert data_file(tmp_path).is_file()
    # The settings file does not contain the list, and vice versa.
    assert "milk" not in config_file(tmp_path).read_text(encoding="utf-8")
    assert "width" not in data_file(tmp_path).read_text(encoding="utf-8")


def test_converting_rewrites_the_settings_in_another_format(tmp_path, capsys):
    run(tmp_path, "config", "--set", "display.width", "40")
    capsys.readouterr()

    run(tmp_path, "config", "--convert", "yaml")
    assert (tmp_path / APP.app_id / "config.yaml").is_file()
    assert not config_file(tmp_path).exists()


# ----------------------------------------------------------------------
# Translations
# ----------------------------------------------------------------------


def test_a_language_flag_translates_for_one_run(tmp_path, capsys):
    run(tmp_path, "add", "milk")
    capsys.readouterr()

    run(tmp_path, "--language", "fr", "list")
    assert "Liste de courses" in capsys.readouterr().out

    # ...and the setting was not changed by it.
    run(tmp_path, "list")
    assert "Shopping list" in capsys.readouterr().out


def test_a_language_setting_persists(tmp_path, capsys):
    run(tmp_path, "config", "--set", "display.language", "fr")
    capsys.readouterr()

    run(tmp_path, "add", "milk")
    assert "Ajouté milk" in capsys.readouterr().out


def test_the_count_is_pluralised_in_both_languages(tmp_path, capsys):
    run(tmp_path, "add", "milk")
    capsys.readouterr()

    run(tmp_path, "list")
    english = capsys.readouterr().out
    assert "1 item, sorted by name." in english

    run(tmp_path, "--language", "fr", "list")
    french = capsys.readouterr().out
    assert "1 article, trié par nom." in french


def test_plural_forms_are_chosen_by_count(tmp_path, capsys):
    run(tmp_path, "add", "milk")
    capsys.readouterr()
    run(tmp_path, "list")
    assert "1 item" in capsys.readouterr().out

    run(tmp_path, "add", "bread")
    capsys.readouterr()
    run(tmp_path, "list")
    assert "2 items" in capsys.readouterr().out


def test_the_catalogs_cover_the_same_keys():
    """A missing translation is silent: English still prints, so nothing fails.

    Comparing the key sets is the only cheap way to catch it.
    """
    assert keys_of(load_catalog("en")) == keys_of(load_catalog("fr"))


def test_every_catalog_key_resolves(tmp_path):
    """A key that is asked for but never defined comes back as itself."""
    from gesso.i18n import DirectorySource, Translator

    translator = Translator(
        [DirectorySource(LOCALES_DIR)], language="en", include_framework=False
    )
    unresolved = [key for key in sorted(keys_of(load_catalog("en"))) if translator.t(key) == key]
    assert unresolved == []
