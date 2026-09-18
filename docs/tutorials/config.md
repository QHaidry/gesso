# Store a setting

**You will end up with** a settings file that types itself, refuses values it
should not hold, and can be rewritten in another format.

No Qt. About ten minutes.

## 1. Say who the application is

```python
from gesso.core import AppContext, AppSpec, AppPaths

APP = AppSpec(
    name="Pomodoro",
    app_id="pomodoro",
    version="0.1.0",
    default_config_format="json",
)
```

`app_id` is the directory name, so you never type a path. `AppSpec` is covered
in [Application identity](../concepts/application-identity.md).

## 2. Say what it remembers

```python
SCHEMA = Schema(
    [
        Section(
            "timer",
            title="Timer",
            options=(
                Option("minutes", int, 25, "Length of a session.", minimum=1, maximum=180),
                Option("label", str, "Focus", "What the session is called."),
                Option("chime", bool, True, "Play a sound at the end."),
                Option("mode", str, "work", "Which mode to start in.",
                       choices=("work", "break")),
            ),
        )
    ]
)
```

That is the **entire** specification of what persists: two strings, an integer
and a boolean. Each has a default, and three of the four carry a constraint.

## 3. Open the store

```python
paths = AppPaths.resolve(APP.app_id, config_home=Path("pomodoro-home"))
store = ConfigStore.for_app(SCHEMA, AppContext(APP, paths)).load()

print(store.path)        # pomodoro-home/pomodoro/config.json
print(store.exists())    # False — nothing is written until there is something to write
```

Two things to notice already:

- **`--config-home` in the tutorial stands in for `$XDG_CONFIG_HOME`.** Nothing
  writes to your real `~/.config`, which is also what lets the test suite run
  without side effects.
- **Reading does not create a file.** Starting an application should not litter.

## 4. Read a value: it is already the right type

```python
minutes = store.get("timer.minutes")
print(repr(minutes))     # 25
print(type(minutes).__name__)   # int
```

There is no `getint`. There is no `int(store.get(...))`, no `getboolean`, and
no `"true"` anywhere in your code. The schema is the only place the type is
written down, and the store is where it is applied.

## 5. Write a value: coercion is the schema's job

```python
store.set("timer.minutes", "50")     # a string, on purpose
store.set("timer.chime", "no")       # also not a boolean
store.save()
```

Both of those are accepted. Coercion turns `"50"` into an integer and `"no"`
into `False`, so a command-line tool, a web form and a config file all work
without the caller helping.

```console
$ python examples/tutorials/settings.py
settings live in pomodoro-home/pomodoro/config.json
file exists yet? False
minutes: 25 (int)
after saving: 50, False
problems: none
```

## 6. Watch a bad value get refused

Constraints are enforced in **two** places, and it matters which is which:

| | When | What it does |
| - | ---- | ------------ |
| `Schema.validate()` | when you ask | **reports** everything wrong with the data on disk |
| `ConfigStore.set()` | at the call site | **rejects**, and does not store |

```console
$ python examples/tutorials/settings.py --break
refused: timer.minutes: 999 exceeds the maximum of 180
refused: timer.mode: 'siesta' is not one of: work, break
after saving: 50, False
```

`999` is a perfectly good integer. The *schema* is what refuses it, and the
message names the bound rather than saying "invalid". The refused values never
reached the file — the saved `minutes` is still `50`.

!!! tip "Why both?"

    A value can be unacceptable for two different reasons. `999` **cannot be
    coerced** — it is a valid integer, just out of range. `"lots"` **cannot be
    read** as an integer at all. Gesso reports them the same way because from
    the outside they are the same problem: *this setting is not usable, and you
    would rather know now than at three in the morning.*

    The split matters because `validate()` has to cope with a file a human
    edited, while `set()` is the last moment you have the caller's attention.

## 7. Change the format without changing the code

```python
reloaded.convert_to("toml")
```

```console
$ python examples/tutorials/settings.py --toml
rewritten as toml: pomodoro-home/pomodoro/config.toml
```

The old file is kept as a `.bak`. And if the format you asked for has no
writer installed:

```console
$ python examples/tutorials/settings.py --toml
cannot convert: writing TOML requires the 'tomli-w' package (pip install 'gesso-sdk[toml]')
```

That is the design, not a shortcoming: a codec that cannot write **says so**
rather than quietly writing a second config file in a format it *can* manage.
Two config files is a bug you find months later.

## The whole tutorial

```python
--8<-- "examples/tutorials/settings.py"
```

## Check it works

```console
$ PYTHONPATH=src python examples/tutorials/settings.py
$ PYTHONPATH=src python examples/tutorials/settings.py --break
$ PYTHONPATH=src python examples/tutorials/settings.py --toml
$ cat pomodoro-home/pomodoro/config.json
```

## Where to go next

- [Defining a schema](../guides/defining-a-schema.md) — the same thing, with
  the decisions explained rather than the mechanics.
- [Validating and migrating](../guides/validating-and-migrating.md) — what to
  do when the file on disk is wrong, or older than the code.
- [Translate an application](i18n.md) — the next tier up.
