# Defining a schema

A schema is the contract between your application and its configuration file:
every setting, its type, its default, and what it means.

## A complete schema

```python
from gesso.config import Option, Schema, Section

SCHEMA = Schema(
    [
        Section(
            "editor",
            title="Editor",
            description="How text is displayed and edited.",
            options=(
                Option("font_size", int, 13, "Font size, in points."),
                Option("font_family", str, "monospace", "The font to use."),
                Option("wrap", bool, True, "Wrap long lines."),
                Option("tab_width", int, 4, "Spaces per tab stop."),
            ),
        ),
        Section(
            "files",
            title="Files",
            description="Where files are opened from and saved to.",
            options=(
                Option("last_dir", str, "~/Documents", "Directory to open on startup."),
                Option("autosave", bool, False, "Save automatically while typing."),
                Option("recent", list, [], "Recently opened files."),
            ),
        ),
    ]
)
```

That is the whole thing. It reads as documentation because it *is* the
documentation — the `description` on each option is what a future settings
window, or a generated reference, will show.

## The three objects

=== "`Option`"

    One setting.

    | Parameter | Meaning |
    | --- | --- |
    | `key` | The name within its section, e.g. `font_size` |
    | `type` | `bool`, `int`, `float`, `str`, `list` or `dict` |
    | `default` | Used when the key is absent from the file |
    | `description` | Human-readable help |

=== "`Section`"

    A named group of options — one table in JSON/TOML/YAML.

    | Parameter | Meaning |
    | --- | --- |
    | `name` | The table name, e.g. `editor` |
    | `options` | A tuple of `Option`s |
    | `title` | Display name, for a settings UI |
    | `description` | What the section covers |

=== "`Schema`"

    The ordered collection of sections. Ordered because presentation order is
    meaningful in a settings window, and dicts would make it arbitrary.

## Naming sections

Reuse your own vocabulary, and prefer a small number of meaningful sections
over one flat namespace. `editor.font_size` reads better at a call site than
`font_size`, and it gives a settings UI something to group by:

```python
store.get("editor.font_size")
store.get("files.last_dir")
```

## Defaults are the migration mechanism

Because a missing key is filled from the schema default, **a configuration file
never has to be complete**. Users can write the two settings they care about and
ignore the rest:

```json
{ "editor": { "font_size": 15 } }
```

and your application still reads a fully-populated configuration. This is also
how you add a setting without breaking anyone:

1. Add the `Option` to your schema.
2. Ship the release.

Every existing file picks up the default on next load. There is no migration to
write, and no version gate to add. See
[Validating and migrating](validating-and-migrating.md) for when that stops
being enough.

## Keep the schema in one place

Give the schema a name and import it, rather than rebuilding it where it is
needed — a schema built twice is a schema that will drift:

```python
# myapp/config.py
SCHEMA = Schema([...])
```

```python
# anywhere else
from myapp.config import SCHEMA
```

## What not to put in the schema

- **Secrets.** API keys and tokens belong in the keyring (see
  [Choosing a config format](config-formats.md#a-word-on-secrets)).
- **Derived state.** Anything you can recompute — a cache directory, a resolved
  absolute path — is not a setting.
- **Per-run values.** A schema describes persistence. If it should not survive a
  restart, it is not configuration.

## Next

[:octicons-arrow-right-24: Validating and migrating](validating-and-migrating.md)
