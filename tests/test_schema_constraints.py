"""Tests for option constraints and their enforcement.

A type says what shape a value is; a constraint says whether that value is
acceptable. These tests cover both halves, at the option, schema and store
levels.
"""

from __future__ import annotations

import pytest

from gesso.config import ConfigError, ConfigStore, Option, Schema, Section

RESOLUTION = r"^\d{3,4}x\d{3,4}$"


@pytest.fixture
def schema() -> Schema:
    return Schema(
        [
            Section(
                "image",
                options=(
                    Option("resolution", str, "1920x1080", pattern=RESOLUTION),
                    Option("quality", int, 90, minimum=1, maximum=100),
                    Option("effect", str, "none", choices=["none", "blur", "vignette"]),
                ),
            ),
            Section("general", options=(Option("enabled", bool, True),)),
        ]
    )


# ----------------------------------------------------------------------
# Option.check
# ----------------------------------------------------------------------


def test_unconstrained_option_never_complains():
    option = Option("anything", str, "")
    assert option.check("whatever") == []
    assert option.check("") == []
    assert option.check(12345) == []


def test_choices_accepts_and_rejects():
    option = Option("effect", str, "none", choices=["none", "blur"])
    assert option.check("blur") == []
    problems = option.check("sepia")
    assert problems and "not one of" in problems[0]
    assert "none" in problems[0] and "blur" in problems[0]


def test_bounds_are_inclusive():
    option = Option("quality", int, 50, minimum=1, maximum=100)
    assert option.check(1) == []
    assert option.check(100) == []
    assert "below the minimum" in option.check(0)[0]
    assert "exceeds the maximum" in option.check(101)[0]


def test_bounds_ignore_non_numeric_values():
    # A range on a string option must not produce nonsense comparisons.
    option = Option("name", str, "", minimum=1, maximum=10)
    assert option.check("hello") == []


def test_bounds_ignore_booleans():
    # bool is an int subclass; True must not be judged as the number 1.
    option = Option("flag", bool, False, minimum=5)
    assert option.check(True) == []
    assert option.check(False) == []


def test_pattern_must_match_the_whole_value():
    option = Option("resolution", str, "", pattern=RESOLUTION)
    assert option.check("1920x1080") == []
    assert option.check("3840x2160") == []
    assert option.check("invalid")
    # fullmatch semantics: a valid prefix alone is not a match
    assert option.check("1920x1080px")


def test_coerce_and_check_reports_both_stages():
    option = Option("quality", int, 50, minimum=1, maximum=100)
    value, problems = option.coerce_and_check("42")
    assert value == 42 and problems == []

    value, problems = option.coerce_and_check("999")
    assert value == 999 and problems  # coerced fine, constraint fails

    with pytest.raises(ValueError):
        option.coerce_and_check("lots")


# ----------------------------------------------------------------------
# Schema level
# ----------------------------------------------------------------------


def test_validate_accepts_a_valid_config(schema):
    assert schema.validate(schema.defaults()) == []


def test_validate_reports_constraint_violations(schema):
    problems = schema.validate(
        {"image": {"resolution": "huge", "quality": 999, "effect": "sepia"}}
    )
    assert any(p.startswith("image.resolution:") for p in problems)
    assert any(p.startswith("image.quality:") and "maximum" in p for p in problems)
    assert any(p.startswith("image.effect:") and "not one of" in p for p in problems)


def test_validate_still_reports_type_errors_separately(schema):
    problems = schema.validate({"image": {"quality": "lots"}})
    assert any(p.startswith("image.quality:") and "cannot read" in p for p in problems)


def test_schema_check_passes_unknown_keys_through(schema):
    assert schema.check("image", "mystery", 5) == []
    assert schema.check("nope", "mystery", 5) == []


def test_defaults_satisfy_their_own_constraints(schema):
    # A schema whose defaults violate its own constraints would be a bug in
    # the schema, and it would fail validation on every fresh config.
    assert schema.validate(schema.defaults()) == []


# ----------------------------------------------------------------------
# Store level
# ----------------------------------------------------------------------


def test_set_accepts_a_valid_value(tmp_path, schema):
    store = ConfigStore.for_format(schema, tmp_path, "json").load()
    store.set("image.quality", "42")
    assert store.get("image.quality") == 42


def test_set_rejects_a_constraint_violation(tmp_path, schema):
    store = ConfigStore.for_format(schema, tmp_path, "json").load()
    with pytest.raises(ConfigError) as excinfo:
        store.set("image.quality", 999)
    assert "image.quality" in str(excinfo.value)
    assert "maximum" in str(excinfo.value)
    # The bad value must not have been stored.
    assert store.get("image.quality") == 90


def test_set_rejects_a_bad_choice(tmp_path, schema):
    store = ConfigStore.for_format(schema, tmp_path, "json").load()
    with pytest.raises(ConfigError):
        store.set("image.effect", "sepia")
    assert store.get("image.effect") == "none"


def test_set_rejects_a_bad_pattern(tmp_path, schema):
    store = ConfigStore.for_format(schema, tmp_path, "json").load()
    with pytest.raises(ConfigError):
        store.set("image.resolution", "huge")
    assert store.get("image.resolution") == "1920x1080"


def test_set_leaves_unconstrained_unknown_keys_alone(tmp_path, schema):
    store = ConfigStore.for_format(schema, tmp_path, "json").load()
    store.set("image.mystery", "anything")
    assert store.get("image.mystery") == "anything"
