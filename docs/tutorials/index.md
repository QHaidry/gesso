# Tutorials

Short, hands-on walkthroughs. Each one covers **one** tier, is self-contained,
and ends with something you can run.

They are not a course: you do not have to read them in order, and none of them
assumes you have read the others. If you are starting from nothing, read
[Configuration](config.md) first, then pick whichever tier you need.

## The tutorials

| Tutorial | You end up with | Needs Qt |
| -------- | --------------- | -------- |
| [Store a setting](config.md) | A schema that types and refuses values | no |
| [Translate an application](i18n.md) | Two catalogs, plurals, and a user override | no |
| [Make a palette](theming.md) | A partial palette and a rendered stylesheet | **no** |
| [Ship your own icons](icons.md) | Your artwork, tinted by the theme | yes |
| [Build a settings pane](widgets.md) | A pane with no stylesheet of its own | yes |
| [Build a windowed application](shell.md) | Two pages, a status line, one call | yes |

## Every tutorial is a real file

The code in these pages is not written for the page. Each tutorial is an actual
script under [`examples/tutorials/`](https://github.com/QHaidry/gesso/tree/main/examples/tutorials),
and the pages embed it with `--8<--` so the two cannot drift. The suite runs
each one **as a subprocess**, using the same command line the page gives you.

So if a tutorial is wrong, a test is red.

## Running them

From a checkout:

```console
$ PYTHONPATH=src python examples/tutorials/settings.py
```

The Qt ones need a display, or a way to pretend:

```console
$ PYTHONPATH=src python examples/tutorials/pane.py
$ QT_QPA_PLATFORM=offscreen PYTHONPATH=src python examples/tutorials/pane.py --check
```

`--check` builds everything and closes immediately instead of entering the
event loop. That is what CI uses, and it is a good habit for your own
applications.

!!! note "Where you are told to look, and why"

    Each tutorial explains not only *what* to write but *why* the API is shaped
    the way it is — because in every case there was a plausible alternative
    that turned out worse. Those notes are the most useful part of a tutorial
    and the easiest thing to leave out.

## After the tutorials

- [The examples](../examples/index.md) — the same tiers, in applications rather
  than in isolation, building from a CLI up to a full GUI.
- [Concepts](../concepts/architecture.md) — the reasoning behind the layering.
- [Guides](../guides/config-formats.md) — how to decide, rather than how to do.
