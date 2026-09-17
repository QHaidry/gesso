"""The ``gesso`` command.

One command so far — ``gesso new``, which writes a working application rather
than an empty directory — plus ``--version``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from . import __version__
from .core.app import AppSpec, slugify
from .generator import ScaffoldError, create

__all__ = ["build_parser", "main"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gesso",
        description="Tools for building applications with Gesso.",
    )
    parser.add_argument("--version", action="version", version=f"gesso {__version__}")

    commands = parser.add_subparsers(dest="command")

    new = commands.add_parser("new", help="Create a new application.")
    new.add_argument("directory", type=Path, help="Where to write the project.")
    new.add_argument(
        "--name",
        default=None,
        help="The display name (default: the directory name).",
    )
    new.add_argument(
        "--app-id",
        default=None,
        help="The application id (default: derived from the name).",
    )
    new.add_argument("--org", default="", help="The organisation, for desktop integration.")
    new.add_argument("--description", default="", help="A one-line description.")
    new.add_argument(
        "--overwrite",
        action="store_true",
        help="Write into a directory that is not empty.",
    )

    return parser


def _new(args: argparse.Namespace) -> int:
    name = args.name or args.directory.name
    spec = AppSpec(
        name=name,
        app_id=args.app_id or slugify(name),
        org=args.org,
        description=args.description,
    )

    try:
        written = create(spec, args.directory, overwrite=args.overwrite)
    except ScaffoldError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    root = Path(args.directory)
    package = spec.app_id.replace("-", "_")

    print(f"Created {spec.display_name} ({spec.app_id}) in {root}")
    print()
    for path in written:
        print(f"  {path.relative_to(root)}")
    print()
    print("Next:")
    print(f"  cd {root}")
    print('  pip install -e ".[dev]"')
    print("  pytest")
    print(f"  python -m {package}.main      (with PYTHONPATH=src, or once installed)")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "new":
        return _new(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
