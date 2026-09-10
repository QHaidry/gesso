"""Tests for the typed schema: coercion and validation."""

from __future__ import annotations

import pytest

from gesso.config import Option, Schema, SchemaError, Section


def test_defaults_are_a_fresh_copy_each_call():
    schema = Schema([Section("general", options=(Option("a", list, []),))])
    first = schema.defaults()
    second = schema.defaults()
    assert first == second
    assert first is not second
    assert first["general"] is not second["general"]


@pytest.mark.parametrize("value", ["true", "yes", "on", "1", "enabled", True, 1])
def test_bool_accepts_truthy_forms(value):
    assert Option("b", bool, False).coerce(value) is True


@pytest.mark.parametrize("value", ["false", "no", "off", "0", "disabled", False, 0])
def test_bool_accepts_falsey_forms(value):
    assert Option("b", bool, True).coerce(value) is False


def test_bool_rejects_ambiguous_text():
    with pytest.raises(ValueError):
        Option("b", bool, False).coerce("maybe")


def test_int_accepts_string_and_integral_float():
    assert Option("i", int, 0).coerce("42") == 42
    assert Option("i", int, 0).coerce(3.0) == 3


def test_int_rejects_non_numeric_and_bool():
    with pytest.raises(ValueError):
        Option("i", int, 0).coerce("abc")
    with pytest.raises(ValueError):
        Option("i", int, 0).coerce(True)


def test_float_accepts_int_and_string():
    assert Option("f", float, 0.0).coerce(2) == 2.0
    assert Option("f", float, 0.0).coerce("1.5") == 1.5


def test_str_normalises_other_scalars():
    option = Option("s", str, "")
    assert option.coerce("x") == "x"
    assert option.coerce(True) == "true"
    assert option.coerce(7) == "7"


def test_container_types():
    assert Option("l", list, []).coerce(("a", "b")) == ["a", "b"]
    assert Option("d", dict, {}).coerce({"k": 1}) == {"k": 1}
    with pytest.raises(ValueError):
        Option("l", list, []).coerce("not-a-list")


def test_unsupported_type_is_a_schema_error():
    with pytest.raises(SchemaError):
        Option("x", object, None).coerce("anything")


# ----------------------------------------------------------------------
# Schema validation
# ----------------------------------------------------------------------


def test_valid_data_has_no_problems(schema):
    assert schema.validate(schema.defaults()) == []


def test_missing_keys_are_not_problems(schema):
    # Defaults fill the gaps, so a partial document is perfectly legal.
    assert schema.validate({"general": {"provider": "nasa"}}) == []


def test_unknown_section_is_reported(schema):
    problems = schema.validate({"nonsense": {"a": 1}})
    assert any("unknown section [nonsense]" in problem for problem in problems)


def test_unknown_option_is_reported(schema):
    problems = schema.validate({"general": {"provider": "bing", "mystery": 1}})
    assert any("unknown option general.mystery" in problem for problem in problems)


def test_uncoercible_value_is_reported(schema):
    problems = schema.validate({"general": {"interval": "not-a-number"}})
    assert any(problem.startswith("general.interval:") for problem in problems)


def test_non_table_section_is_reported(schema):
    problems = schema.validate({"general": "oops"})
    assert any("must be a table" in problem for problem in problems)


def test_coerce_passes_unknown_keys_through(schema):
    assert schema.coerce("general", "mystery", 5) == 5


# ----------------------------------------------------------------------
# Schema definition errors
# ----------------------------------------------------------------------


def test_duplicate_option_in_section_is_rejected():
    with pytest.raises(SchemaError):
        Section("general", options=(Option("a", int, 1), Option("a", int, 2)))


def test_duplicate_section_is_rejected():
    with pytest.raises(SchemaError):
        Schema([Section("general"), Section("general")])


def test_option_and_section_lookups(schema):
    assert schema.section("general") is not None
    assert schema.section("nope") is None
    assert schema.option("general", "provider") is not None
    assert schema.option("general", "nope") is None
    assert schema.option("nope", "provider") is None
    assert Section("general", options=(Option("a", int, 1),)).option("a") is not None
