# Examples

Working code, not illustrations. Every example is runnable, and each one is
exercised by the test suite so it cannot quietly rot.

## The ladder

The four examples are a ladder. Each rung adds a tier and keeps the one below
it, so reading them in order is reading Gesso's feature set in order:

| # | Example | Adds | Tiers |
| - | ------- | ---- | ----- |
| 1 | [Hello, Gesso](hello-cli.md) | Identity, a schema, all three config formats | `core`, `config` |
| 2 | [Basket](basket.md) | Constraints, validation, translations, plurals, and data kept apart from settings | `+ i18n` |
| 3 | [Gallery](gallery.md) | A window: palettes, runtime theme switching, the widget set, icons | `+ ui.theme`, `ui.icons`, `ui.widgets` |
| 4 | [Tracker](tracker.md) | The application shell, pages, a user palette, live language switching | `+ ui.app` |

Rungs three and four are worth reading as a pair. Gallery builds its own
window and lays out its own sidebar by hand. Tracker hands the whole window to
`AppShell` — and Tracker is **shorter**, despite having four pages, two
languages, its own palette, its own icons and a settings file. That difference
is the entire argument for the application shell, and it is easier to see in
two files than in a paragraph of prose.

## Running an example

The examples import `gesso`, which lives under `src/`. From a checkout:

```console
$ PYTHONPATH=src python examples/hello.py
```

The later rungs are packages, so they need `examples` on the path too:

```console
$ PYTHONPATH=src:examples python -m basket list
$ PYTHONPATH=src:examples python -m gallery
$ PYTHONPATH=src:examples python -m tracker
```

Or, with the package installed (`pip install -e .`):

```console
$ python -m tracker
```

None of them touch your real `~/.config` or `~/.local/share`: each takes
`--config-home` and `--data-home` flags that stand in for `$XDG_CONFIG_HOME`
and `$XDG_DATA_HOME`.

## The shape every example follows

Each is deliberately small enough to read in one sitting, and structured the
same way:

1. **Who is this application?** — an `AppSpec`.
2. **What does it store?** — a `Schema`.
3. **Let Gesso find the files** — `ConfigStore.for_app(...)`.
4. **Do the actual work** — the part that is yours.

If you can find those four parts, you can read any of them — and you can see
exactly where Gesso stops and the application starts.
