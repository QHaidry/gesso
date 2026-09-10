# Validating and migrating

## Validation

`validate()` returns a list of human-readable problems. An empty list means
valid.

```python
for problem in store.validate():
    print("warning:", problem)
```

```
warning: unknown section [generl]
warning: unknown option editor.font_sizee
warning: editor.tab_width: cannot read 'wide' as an integer
```

Each message names the exact key, so a user can fix the file without reading
your source.

### What counts as a problem

| Situation | Problem? | Why |
| --- | --- | --- |
| Unknown section or key | :material-check: Yes | Almost always a typo, and silently ignoring it hides the user's intent |
| Value that will not coerce | :material-check: Yes | The application would otherwise get the wrong type or crash later |
| A section that is not a table | :material-check: Yes | Structurally wrong, not merely surprising |
| A **missing** key | :material-close: No | Filled from the schema default — see below |
| A value of the right type | :material-close: No | — |

!!! note "Validation is advisory, not fatal"

    `validate()` never raises and never mutates. It is up to you whether a
    problem is a warning in a log, a banner in the UI, or a refusal to start.
    Gesso's own example prints warnings and carries on, which is the right
    default: a malformed preference should not stop a user opening their
    application.

## Loading never destroys data

This is a guarantee, not a side effect. When Gesso loads a file it **preserves**
keys it does not recognise, and values it cannot coerce, rather than pruning
them.

```python
>>> store.get("editor.mystery")     # not in the schema
7
>>> store.validate()
['unknown option editor.mystery']
```

Why this matters: if loading silently dropped unknown keys, then one run of a
newer version followed by an older version would quietly delete the user's
settings. A configuration file belongs to the user. Gesso reads it, reports on
it, and writes back only what it was given or told to change.

## Migrating

### Adding a setting

**You almost certainly do not need to do anything.** Add the `Option` to your
schema and ship:

```python
Option("show_line_numbers", bool, True, "Display line numbers.")
```

Existing files gain the default on next load. This covers the large majority of
real-world configuration changes, and it is why the schema exists.

### Renaming or restructuring

When a key moves or changes meaning, a default cannot express the intent —
you need to *carry the old value forward*. Do that explicitly, right after
loading:

```python
store = ConfigStore.for_app(SCHEMA, context).load()

# Migration: `tab_size` was renamed to `tab_width` in 2.0.
legacy = store.get("editor.tab_size")
if legacy is not None:
    store.set("editor.tab_width", legacy)
    store.save()
```

Guiding principles:

- **Migrate forward only.** Do not write downgrade paths; they are rarely
  correct and never tested.
- **Be idempotent.** The check above is a no-op once the old key is gone, so it
  is safe to run on every startup.
- **Never fail to start over a migration.** If you cannot carry a value across,
  fall back to the default and warn — losing one preference is better than
  losing the application.

!!! warning "Schema-version migrations are not built yet"

    A declarative migration framework — a schema version plus an ordered list of
    upgrade steps, applied automatically on load — is on the
    [roadmap](../roadmap.md). Today, migrations are explicit code like the
    example above, which is honest and adequate for a young application. If you
    need version tracking now, store it yourself as a normal option:

    ```python
    Option("config_version", int, 1, "Schema version, for migrations.")
    ```

## Next

- [Examples](../examples/index.md)
- [API reference: gesso.config](../reference/config.md)
