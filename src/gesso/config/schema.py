"""A declarative, typed configuration schema.

The schema is the contract between an application and its config file, and it
is deliberately independent of the file format: a codec hands back native
Python values (JSON, TOML and YAML all have real booleans, integers and
floats) and the schema coerces and validates them at the boundary.

This is a deliberate change from a stringly-typed config. A stringly-typed
config cannot survive contact with TOML, where ``auto_update = "true"`` is the
*string* ``"true"`` and ``auto_update = true`` is the *boolean* ``True``.

An option declares a **type** and, optionally, **constraints**. The split
matters: a type says what shape a value is, a constraint says whether that
value is acceptable. ``"nonsense"`` fails the type; ``99999`` passes the type
but fails the constraint.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

__all__ = ["SchemaError", "Option", "Section", "Schema"]

_TRUE = frozenset({"1", "true", "yes", "on", "enabled"})
_FALSE = frozenset({"0", "false", "no", "off", "disabled"})


class SchemaError(Exception):
    """Raised for a malformed schema *definition* (a programming error)."""


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        text = value.strip().lower()
        if text in _TRUE:
            return True
        if text in _FALSE:
            return False
    raise ValueError(f"cannot read {value!r} as a boolean")


def _to_int(value: Any) -> int:
    if isinstance(value, bool):
        raise ValueError(f"cannot read {value!r} as an integer")
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.strip(), 10)
        except ValueError:
            pass
    raise ValueError(f"cannot read {value!r} as an integer")


def _to_float(value: Any) -> float:
    if isinstance(value, bool):
        raise ValueError(f"cannot read {value!r} as a number")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            pass
    raise ValueError(f"cannot read {value!r} as a number")


def _to_str(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    raise ValueError(f"cannot read {value!r} as text")


def _is_number(value: Any) -> bool:
    """Whether *value* is a real number. ``bool`` is not (see ``_to_int``)."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


@dataclass(frozen=True)
class Option:
    """One setting: a type, a default, and optional constraints."""

    key: str
    type: type
    default: Any
    description: str = ""
    #: The only values considered acceptable, if given.
    choices: Optional[Sequence[Any]] = None
    #: Inclusive bounds for numeric options.
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    #: A regular expression the whole string value must match.
    pattern: Optional[str] = None

    def coerce(self, value: Any) -> Any:
        """Convert *value* to this option's declared type.

        Raises :class:`ValueError` if the value cannot be represented.
        """
        if self.type is bool:
            return _to_bool(value)
        if self.type is int:
            return _to_int(value)
        if self.type is float:
            return _to_float(value)
        if self.type is str:
            return _to_str(value)
        if self.type is list:
            if isinstance(value, (list, tuple)):
                return list(value)
            raise ValueError(f"cannot read {value!r} as a list")
        if self.type is dict:
            if isinstance(value, dict):
                return dict(value)
            raise ValueError(f"cannot read {value!r} as a table")
        raise SchemaError(f"unsupported option type {self.type!r} for {self.key!r}")

    def check(self, value: Any) -> List[str]:
        """Constraint problems with an already-coerced *value*.

        Returns human-readable problems; empty means acceptable. Type errors
        are :meth:`coerce`'s job — this is about a value being *wrong* rather
        than the wrong shape.
        """
        problems: List[str] = []

        if self.choices is not None and value not in self.choices:
            allowed = ", ".join(str(choice) for choice in self.choices)
            problems.append(f"{value!r} is not one of: {allowed}")

        if self.minimum is not None and _is_number(value) and value < self.minimum:
            problems.append(f"{value} is below the minimum of {self.minimum}")

        if self.maximum is not None and _is_number(value) and value > self.maximum:
            problems.append(f"{value} exceeds the maximum of {self.maximum}")

        if self.pattern is not None and isinstance(value, str):
            if re.fullmatch(self.pattern, value) is None:
                problems.append(f"{value!r} does not match the required format")

        return problems

    def coerce_and_check(self, value: Any) -> Tuple[Any, List[str]]:
        """Coerce *value*, then check it. Returns ``(value, problems)``.

        Raises :class:`ValueError` if the value cannot be coerced at all.
        """
        coerced = self.coerce(value)
        return coerced, self.check(coerced)


@dataclass(frozen=True)
class Section:
    """A group of related options (a table in the config file)."""

    name: str
    options: Tuple[Option, ...] = ()
    title: str = ""
    description: str = ""

    def __post_init__(self) -> None:
        seen = set()
        for option in self.options:
            if option.key in seen:
                raise SchemaError(f"duplicate option {option.key!r} in section {self.name!r}")
            seen.add(option.key)

    def option(self, key: str) -> Optional[Option]:
        for option in self.options:
            if option.key == key:
                return option
        return None

    def defaults(self) -> Dict[str, Any]:
        return {option.key: option.default for option in self.options}


class Schema:
    """An ordered collection of :class:`Section` definitions."""

    def __init__(self, sections: Sequence[Section]) -> None:
        seen = set()
        for section in sections:
            if section.name in seen:
                raise SchemaError(f"duplicate section {section.name!r}")
            seen.add(section.name)
        self._sections: Tuple[Section, ...] = tuple(sections)

    @property
    def sections(self) -> Tuple[Section, ...]:
        return self._sections

    def section(self, name: str) -> Optional[Section]:
        for section in self._sections:
            if section.name == name:
                return section
        return None

    def option(self, section: str, key: str) -> Optional[Option]:
        found = self.section(section)
        return found.option(key) if found is not None else None

    def defaults(self) -> Dict[str, Dict[str, Any]]:
        """A fresh default config — a new dict on every call."""
        return {section.name: section.defaults() for section in self._sections}

    def coerce(self, section: str, key: str, value: Any) -> Any:
        """Coerce *value* using the option's type, passing unknown keys through."""
        option = self.option(section, key)
        return value if option is None else option.coerce(value)

    def check(self, section: str, key: str, value: Any) -> List[str]:
        """Constraint problems for one already-coerced value.

        Unknown keys have no constraints to violate, so they pass.
        """
        option = self.option(section, key)
        return [] if option is None else option.check(value)

    def validate(self, data: Dict[str, Any]) -> List[str]:
        """Return human-readable problems with *data*; empty means valid.

        Missing keys are *not* problems — they are filled from the defaults.
        Unknown sections/keys, values that cannot be coerced, and values that
        violate a constraint all are.
        """
        problems: List[str] = []
        for section_name, options in data.items():
            section = self.section(section_name)
            if section is None:
                problems.append(f"unknown section [{section_name}]")
                continue
            if not isinstance(options, dict):
                problems.append(f"[{section_name}] must be a table, got {type(options).__name__}")
                continue
            for key, value in options.items():
                option = section.option(key)
                if option is None:
                    problems.append(f"unknown option {section_name}.{key}")
                    continue
                try:
                    coerced = option.coerce(value)
                except ValueError as exc:
                    problems.append(f"{section_name}.{key}: {exc}")
                    continue
                for problem in option.check(coerced):
                    problems.append(f"{section_name}.{key}: {problem}")
        return problems
