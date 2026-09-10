"""Tests for language normalisation, detection and direction."""

from __future__ import annotations

import pytest

from gesso.i18n import locale as gi18n


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("en", "en"),
        ("EN", "en"),
        ("en_US", "en"),
        ("en_US.UTF-8", "en"),
        ("en-US", "en"),
        ("pt_BR", "pt"),
        ("sr_RS@latin", "sr"),
        ("fr_FR.UTF-8:de_DE", "fr"),  # LANGUAGE is a priority list
        ("  de  ", "de"),
    ],
)
def test_normalize_lang(raw, expected):
    assert gi18n.normalize_lang(raw) == expected


@pytest.mark.parametrize("raw", ["", "   ", "C", "c", "POSIX", "posix", None])
def test_normalize_lang_reports_no_language(raw):
    # Returning "" (rather than a default) lets callers tell "unspecified"
    # apart from a deliberate fallback.
    assert gi18n.normalize_lang(raw) == ""


def test_detect_language_prefers_language_variable():
    env = {"LANGUAGE": "fr_FR:de_DE", "LC_ALL": "de_DE.UTF-8", "LANG": "es_ES.UTF-8"}
    assert gi18n.detect_language(env) == "fr"


def test_detect_language_takes_first_of_the_language_list():
    assert gi18n.detect_language({"LANGUAGE": "it_IT:fr"}) == "it"


def test_detect_language_falls_through_to_the_next_variable():
    env = {"LANGUAGE": "", "LC_ALL": "", "LC_MESSAGES": "de_DE.UTF-8", "LANG": "es_ES.UTF-8"}
    assert gi18n.detect_language(env) == "de"


def test_detect_language_ignores_an_unset_c_locale(monkeypatch):
    # "C"/"POSIX" mean "no locale", not English, so they must not stop the
    # search; with nothing else available we land on the default.
    monkeypatch.setattr(gi18n._locale, "getlocale", lambda: (None, None))
    assert gi18n.detect_language({"LANG": "C"}) == "en"


def test_detect_language_uses_the_process_environment(monkeypatch):
    monkeypatch.setenv("LANGUAGE", "pt_BR.UTF-8")
    assert gi18n.detect_language() == "pt"


def test_detect_language_defaults_to_english(monkeypatch):
    monkeypatch.setattr(gi18n._locale, "getlocale", lambda: (None, None))
    assert gi18n.detect_language({}) == "en"


@pytest.mark.parametrize("code", ["ar", "he", "fa", "ur", "ar_EG", "iw"])
def test_is_rtl_true(code):
    assert gi18n.is_rtl(code) is True


@pytest.mark.parametrize("code", ["en", "fr", "de", "ja", "", None])
def test_is_rtl_false(code):
    assert gi18n.is_rtl(code) is False
