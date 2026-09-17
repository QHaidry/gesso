"""Scaffolding a new project.

``gesso new myapp`` writes a *working* application — config schema, palette,
translations, a window and a passing test — rather than a directory of
placeholders to fill in. A scaffold that does not run makes a new project's
first experience "debug somebody else's boilerplate", which is a poor way to
introduce an SDK.

The scaffolding is headless: it writes files and needs no toolkit.
"""

from __future__ import annotations

import string
from datetime import date
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Tuple

from .core.app import AppSpec

__all__ = [
    "ScaffoldError",
    "TEMPLATES",
    "TEMPLATE_DIR",
    "create",
    "plan",
    "render",
    "values_for",
]

#: Where the templates live inside the package.
TEMPLATE_DIR = Path(__file__).parent / "templates"

#: ``(template, destination)`` pairs. Both are rendered, so a destination may
#: contain ``${package}`` — which is how one template tree lands in a package
#: named after the application.
TEMPLATES: Tuple[Tuple[str, str], ...] = (
    ("pyproject.toml.tmpl", "pyproject.toml"),
    ("README.md.tmpl", "README.md"),
    ("gitignore.tmpl", ".gitignore"),
    ("src/__init__.py.tmpl", "src/${package}/__init__.py"),
    ("src/app.py.tmpl", "src/${package}/app.py"),
    ("src/config.py.tmpl", "src/${package}/config.py"),
    ("src/home.py.tmpl", "src/${package}/home.py"),
    ("src/main.py.tmpl", "src/${package}/main.py"),
    ("src/locales/en.json.tmpl", "src/${package}/locales/en.json"),
    ("src/themes/default.json.tmpl", "src/${package}/themes/default.json"),
    ("tests/conftest.py.tmpl", "tests/conftest.py"),
    ("tests/test_app.py.tmpl", "tests/test_app.py"),
)


class ScaffoldError(Exception):
    """Raised when a project cannot be created."""


def values_for(spec: AppSpec, *, year: Optional[int] = None) -> Dict[str, str]:
    """The substitutions a project's templates are rendered with."""
    return {
        "name": spec.name,
        "app_id": spec.app_id,
        "package": spec.app_id.replace("-", "_"),
        "org": spec.org,
        "version": spec.version,
        "description": spec.description or f"{spec.name} - built with Gesso.",
        "year": str(year if year is not None else date.today().year),
    }


def render(text: str, values: Mapping[str, str]) -> str:
    """Substitute ``${name}`` placeholders in *text*.

    A literal dollar sign must be written ``$$``; a template that leaves a
    placeholder unfilled, or contains a bare ``$``, is reported rather than
    written out broken.
    """
    try:
        return string.Template(text).substitute(values)
    except KeyError as exc:
        raise ScaffoldError(f"a template needs a value for {exc.args[0]!r}") from exc
    except ValueError as exc:
        raise ScaffoldError(f"a template is malformed: {exc}") from exc


def plan(spec: AppSpec, *, year: Optional[int] = None) -> List[Tuple[Path, str]]:
    """The files a scaffold would write, relative to the project root.

    Separate from :func:`create` so a caller — or a test — can inspect a
    project before anything is written to disk.
    """
    values = values_for(spec, year=year)
    planned: List[Tuple[Path, str]] = []

    for template, destination in TEMPLATES:
        source = TEMPLATE_DIR / template
        try:
            text = source.read_text(encoding="utf-8")
        except OSError as exc:
            raise ScaffoldError(f"cannot read template {source}: {exc}") from exc
        planned.append((Path(render(destination, values)), render(text, values)))

    return planned


def create(
    spec: AppSpec,
    directory: Path,
    *,
    year: Optional[int] = None,
    overwrite: bool = False,
) -> List[Path]:
    """Write a new project into *directory*, returning the files written.

    Refuses a directory that already has something in it unless *overwrite* is
    set: writing a scaffold over an existing project is never what was meant.
    """
    directory = Path(directory)

    if directory.exists() and any(directory.iterdir()) and not overwrite:
        raise ScaffoldError(
            f"{directory} already exists and is not empty "
            "(pass --overwrite to write into it anyway)"
        )

    written: List[Path] = []
    for relative, text in plan(spec, year=year):
        target = directory / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            target.write_text(text, encoding="utf-8")
        except OSError as exc:
            raise ScaffoldError(f"cannot write {target}: {exc}") from exc
        written.append(target)

    return written
