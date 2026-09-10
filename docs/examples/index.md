# Examples

Working code, not illustrations. Every example is runnable, and the ones shown
here are exercised by the test suite so they cannot quietly rot.

## Running an example

The examples import `gesso`, which lives under `src/`. From a checkout:

```console
$ PYTHONPATH=src python examples/hello.py
```

Or, with the package installed (`pip install -e .`):

```console
$ python examples/hello.py
```

Neither touches your real `~/.config` — each example takes a `--config-home`
that stands in for `$XDG_CONFIG_HOME`.

## Available examples

| Example | Shows | Layer |
| --- | --- | --- |
| [Hello, Gesso (CLI)](hello-cli.md) | A complete application: identity, schema, all three config formats, `--set`, `--convert` | `gesso.core`, `gesso.config` |

!!! note "More examples as the SDK grows"

    Qt examples — theming, the widget library, internationalisation — arrive
    with their tiers. See the [Roadmap](../roadmap.md).

## The shape every example follows

Each one is deliberately small enough to read in one sitting, and structured
the same way:

1. **Who is this application?** — an `AppSpec`.
2. **What does it store?** — a `Schema`.
3. **Let Gesso find the file** — `ConfigStore.for_app(...)`.
4. **Do the actual work** — the part that is yours.

If you can find those four parts, you can read any of them.
