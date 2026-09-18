"""Tutorial: store a setting, and refuse a bad one.

Run it::

    PYTHONPATH=src python examples/tutorials/settings.py
    PYTHONPATH=src python examples/tutorials/settings.py --break
    PYTHONPATH=src python examples/tutorials/settings.py --toml
"""

from __future__ import annotations

import sys
from pathlib import Path

from gesso.config import ConfigError, ConfigStore, Option, Schema, Section
from gesso.core import AppContext, AppSpec, AppPaths

# ----------------------------------------------------------------------
# 1. What is this, and what does it remember?
# ----------------------------------------------------------------------
APP = AppSpec(
    name="Pomodoro",
    app_id="pomodoro",
    version="0.1.0",
    default_config_format="json",
)

SCHEMA = Schema(
    [
        Section(
            "timer",
            title="Timer",
            options=(
                Option("minutes", int, 25, "Length of a session.", minimum=1, maximum=180),
                Option("label", str, "Focus", "What the session is called."),
                Option("chime", bool, True, "Play a sound at the end."),
                Option(
                    "mode",
                    str,
                    "work",
                    "Which mode to start in.",
                    choices=("work", "break"),
                ),
            ),
        )
    ]
)


def open_store(name: str, config_home: Path) -> ConfigStore:
    """Find (or plan) the settings file for an application called *name*."""
    spec = APP if name == APP.app_id else AppSpec(name=name, app_id=name, version="0.1.0")
    paths = AppPaths.resolve(spec.app_id, config_home=config_home)
    return ConfigStore.for_app(SCHEMA, AppContext(spec, paths)).load()


def main(argv: list) -> int:
    config_home = Path("pomodoro-home")
    store = open_store("pomodoro", config_home)
    print(f"settings live in {store.path}")
    print(f"file exists yet? {store.exists()}")

    # Settings come out of the store already typed. There is no getboolean.
    minutes = store.get("timer.minutes")
    print(f"minutes: {minutes!r} ({type(minutes).__name__})")

    if "--break" in argv:
        # A value the schema refuses never reaches the file.
        try:
            store.set("timer.minutes", 999)
        except ConfigError as exc:
            print(f"refused: {exc}")
        try:
            store.set("timer.mode", "siesta")
        except ConfigError as exc:
            print(f"refused: {exc}")

    # A *string* is fine: coercion is the schema's job, not the caller's.
    store.set("timer.minutes", "50")
    store.set("timer.chime", "no")
    store.save()

    reloaded = open_store("pomodoro", config_home)
    print(f"after saving: {reloaded.get('timer.minutes')!r}, {reloaded.get('timer.chime')!r}")

    if "--toml" in argv:
        try:
            reloaded.convert_to("toml")
            print(f"rewritten as {reloaded.format}: {reloaded.path}")
        except ConfigError as exc:
            # A codec that cannot write says which package to install, rather
            # than writing a second config file in a format it can manage.
            print(f"cannot convert: {exc}")

    problems = reloaded.validate()
    print(f"problems: {problems or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
