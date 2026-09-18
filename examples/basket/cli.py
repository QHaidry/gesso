"""Basket's command line.

``python -m basket`` reaches :func:`main` here::

    PYTHONPATH=src:examples python -m basket --help

The commands live in this module rather than in ``__main__.py`` so the test
suite can import and drive them directly.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Optional, Sequence

from gesso.config import ConfigError

from . import APP, Profile
from .items import Item, ItemStore

EXIT_OK = 0
EXIT_REFUSED = 1
EXIT_BAD_USAGE = 2


# ----------------------------------------------------------------------
# Pluralisation
# ----------------------------------------------------------------------
def plural(t: Any, key: str, count: int, **kwargs: Any) -> str:
    """Choose the ``.one`` or ``.other`` form of *key* for *count*.

    Gesso deliberately does not guess plural rules. They are not
    one-versus-many in most languages — Russian has three forms, Arabic six —
    and getting them right needs real CLDR data, which is a planned optional
    backend rather than something the core should pretend to have.

    Until then the catalogs carry the forms and the application chooses. For
    English and French, that choice is the whole rule.
    """
    form = "one" if count == 1 else "other"
    return t(f"{key}.{form}", count=count, **kwargs)


# ----------------------------------------------------------------------
# Commands
# ----------------------------------------------------------------------
def cmd_add(profile: Profile, args: argparse.Namespace) -> int:
    t = profile.t
    name = args.name.strip()

    pattern = profile.store.get("list.name_pattern")
    if not re.fullmatch(pattern, name):
        print(t("basket.add.bad_name", name=name), file=sys.stderr)
        return EXIT_REFUSED

    items_file = profile.data_dir / "items.json"
    items = ItemStore(items_file).load()

    if ItemStore.find(items, name) is not None:
        print(t("basket.add.duplicate", name=name))
        return EXIT_REFUSED

    # A constraint the *schema* cannot express: it bounds the setting, and only
    # the application can check the setting against its own data.
    limit = profile.store.get("list.max_items")
    if len(items) >= limit:
        print(t("basket.add.full", limit=limit), file=sys.stderr)
        return EXIT_REFUSED

    items.append(Item(name=name, price=args.price))
    ItemStore(items_file).save(items)
    print(plural(t, "basket.add.done", len(items), name=name))
    return EXIT_OK


def cmd_list(profile: Profile, args: argparse.Namespace) -> int:
    t = profile.t
    items = ItemStore.sorted_by_name(ItemStore(profile.data_dir / "items.json").load())

    if not items:
        print(t("basket.list.empty"))
        return EXIT_OK

    width = profile.store.get("display.width")
    currency = profile.store.get("display.currency")
    show_prices = profile.store.get("display.show_prices")

    print(t("basket.list.heading"))
    print(plural(t, "basket.list.names", len(items)))
    print()

    total = 0.0
    priced = False
    for index, item in enumerate(items, start=1):
        line = f"  {index:>2}. {item.name:<{width}}"
        if show_prices and item.price is not None:
            line += f"{currency}{item.price:.2f}"
            total += item.price
            priced = True
        print(line.rstrip())

    if show_prices and priced:
        print()
        print(t("basket.list.total", total=f"{currency}{total:.2f}"))
    return EXIT_OK


def cmd_remove(profile: Profile, args: argparse.Namespace) -> int:
    t = profile.t
    items_file = profile.data_dir / "items.json"
    items = ItemStore(items_file).load()

    found = ItemStore.find(items, args.name)
    if found is None:
        print(t("basket.remove.missing", name=args.name))
        return EXIT_REFUSED

    items.remove(found)
    ItemStore(items_file).save(items)
    print(t("basket.remove.done", name=found.name))
    return EXIT_OK


def cmd_clear(profile: Profile, args: argparse.Namespace) -> int:
    t = profile.t
    items_file = profile.data_dir / "items.json"
    items = ItemStore(items_file).load()

    if not items:
        print(t("basket.clear.already_empty"))
        return EXIT_OK

    ItemStore(items_file).save([])
    print(plural(t, "basket.clear.done", len(items)))
    return EXIT_OK


def cmd_config(profile: Profile, args: argparse.Namespace) -> int:
    t = profile.t
    store = profile.store
    changed = False

    for key, value in args.set or []:
        try:
            # `set` rejects, rather than stores, a value the schema refuses.
            store.set(key, value)
        except ConfigError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return EXIT_BAD_USAGE
        store.save()
        changed = True
        # Re-read through the schema, so the confirmation shows the *coerced*
        # value rather than the string that was typed.
        print(t("basket.config.changed", key=key, value=store.get(key)))

    if args.convert:
        try:
            store.convert_to(args.convert)
        except ConfigError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return EXIT_BAD_USAGE
        changed = True
        print(t("basket.config.converted", format=args.convert))

    if args.show or not changed:
        show_settings(profile)
    return EXIT_OK


def show_settings(profile: Profile) -> None:
    """Print every setting, with the description from the schema.

    Driving the listing from ``store.schema`` rather than from a hand-written
    list means a new option appears here the moment it is declared.
    """
    t = profile.t
    store = profile.store

    print(t("basket.config.heading"))
    print(t("basket.config.source", path=store.path))
    print()

    for section in store.schema.sections:
        print(f"[{section.name}]" + (f"  {section.title}" if section.title else ""))
        for option in section.options:
            value = store.get(f"{section.name}.{option.key}")
            comment = f"  # {option.description}" if option.description else ""
            print(f"  {option.key} = {value!r}{comment}")
        print()


# ----------------------------------------------------------------------
# Wiring
# ----------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="basket",
        description=f"{APP.display_name} — {APP.description}",
    )
    parser.add_argument(
        "--config-home",
        type=Path,
        default=Path("basket-home"),
        help="Stands in for $XDG_CONFIG_HOME (default: ./basket-home)",
    )
    parser.add_argument(
        "--data-home",
        type=Path,
        default=Path("basket-home"),
        help="Stands in for $XDG_DATA_HOME (default: ./basket-home)",
    )
    parser.add_argument(
        "--language",
        help="Use this language for this run, without changing the setting",
    )

    commands = parser.add_subparsers(dest="command", required=True)

    add = commands.add_parser("add", help="Put something on the list")
    add.add_argument("name")
    add.add_argument("--price", type=float, default=None)
    add.set_defaults(func=cmd_add)

    list_cmd = commands.add_parser("list", help="Print the list")
    list_cmd.set_defaults(func=cmd_list)

    remove = commands.add_parser("remove", help="Take something off the list")
    remove.add_argument("name")
    remove.set_defaults(func=cmd_remove)

    commands.add_parser("clear", help="Empty the list").set_defaults(func=cmd_clear)

    config = commands.add_parser("config", help="Show or change the settings")
    config.add_argument("--show", action="store_true")
    # `--language` is deliberately *not* here: it is a top-level flag meaning
    # "for this run only". To change the setting, use
    # `config --set display.language fr`, which goes through the schema like
    # every other setting.
    config.add_argument("--set", nargs=2, action="append", default=[], metavar=("KEY", "VALUE"))
    config.add_argument("--convert", metavar="FORMAT")
    config.set_defaults(func=cmd_config)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run Basket. Returns the process exit code."""
    args = build_parser().parse_args(argv)
    profile = Profile.open(
        config_home=args.config_home,
        data_home=args.data_home,
        language=args.language,
    )

    # Settings that are wrong are reported, not fatal. A user with a
    # hand-edited config should be told what is wrong with it, and still be
    # able to run `basket config --show` to see it.
    problems = profile.store.validate()
    if problems:
        print(profile.t("basket.problem.heading"), file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)

    return args.func(profile, args)


if __name__ == "__main__":
    raise SystemExit(main())
