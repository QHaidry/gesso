"""A complete, runnable Gesso application — in a single file.

Gesso's whole job is to get out of the way, so this example is deliberately
small. It declares *who the application is* (an :class:`~gesso.core.AppSpec`),
*what it stores* (a :class:`~gesso.config.Schema`), and lets Gesso work out
*where* that lives and *in what format*.

Try it::

    PYTHONPATH=src python examples/hello.py
    PYTHONPATH=src python examples/hello.py --set greeting.name Ada
    PYTHONPATH=src python examples/hello.py --format toml --show
    PYTHONPATH=src python examples/hello.py --convert yaml

``--config-home`` stands in for ``$XDG_CONFIG_HOME`` and defaults to
``./hello-config``, so the example never touches your real ``~/.config``. Note
where the files actually land — Gesso nests them under the application id::

    hello-config/
    └── gesso-hello/
        └── config.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from gesso.config import ConfigError, ConfigStore, Option, Schema, Section
from gesso.core import AppContext, AppSpec
from gesso.core.paths import AppPaths

# ----------------------------------------------------------------------
# 1. Who is this application?
# ----------------------------------------------------------------------
APP = AppSpec(
    name="Gesso Hello",
    app_id="gesso-hello",
    version="0.1.0",
    description="A tiny example application built on Gesso.",
    default_config_format="json",
)

# ----------------------------------------------------------------------
# 2. What does it store?
# ----------------------------------------------------------------------
SCHEMA = Schema(
    [
        Section(
            "greeting",
            title="Greeting",
            description="How the application greets you.",
            options=(
                Option("name", str, "World", "Who to greet."),
                Option("punctuation", str, "!", "Appended to the greeting."),
                Option("shout", bool, False, "Print the greeting in UPPERCASE."),
                Option("repeat", int, 1, "How many times to print the greeting."),
            ),
        )
    ]
)


# ----------------------------------------------------------------------
# 3. Let Gesso find (or plan) the configuration file.
# ----------------------------------------------------------------------
def build_store(config_home: Path, fmt: Optional[str]) -> ConfigStore:
    """Locate this application's configuration, in *fmt* if one is forced."""
    context = AppContext(APP, AppPaths.resolve(APP.app_id, config_home=config_home))
    if fmt:
        return ConfigStore.for_format(SCHEMA, context.config_dir, fmt).load()
    return ConfigStore.for_app(SCHEMA, context).load()


def render(store: ConfigStore) -> str:
    """Turn the stored settings into the greeting to print."""
    text = f"Hello, {store.get('greeting.name')}{store.get('greeting.punctuation')}"
    if store.get("greeting.shout"):
        text = text.upper()
    return "\n".join([text] * store.get("greeting.repeat"))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="hello", description="A tiny application built on Gesso."
    )
    parser.add_argument(
        "--config-home",
        type=Path,
        default=Path("hello-config"),
        help="Stands in for $XDG_CONFIG_HOME (default: ./hello-config)",
    )
    parser.add_argument(
        "--format",
        choices=("json", "toml", "yaml"),
        help="Force a configuration format instead of discovering one",
    )
    parser.add_argument(
        "--set",
        nargs=2,
        action="append",
        default=[],
        metavar=("KEY", "VALUE"),
        help="Set a value, e.g. --set greeting.name Ada",
    )
    parser.add_argument("--show", action="store_true", help="Print the configuration and exit")
    parser.add_argument(
        "--convert", metavar="FORMAT", help="Rewrite the configuration in another format"
    )
    args = parser.parse_args(argv)

    try:
        store = build_store(args.config_home, args.format)
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    for key, value in args.set:
        try:
            store.set(key, value)
        except ConfigError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    if args.set:
        store.save()

    for problem in store.validate():
        print(f"warning: {problem}", file=sys.stderr)

    if args.convert:
        try:
            store.convert_to(args.convert)
        except ConfigError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    if args.show:
        print(json.dumps(store.as_dict(), indent=2))
    else:
        print(render(store))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
