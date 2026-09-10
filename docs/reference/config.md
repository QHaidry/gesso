# `gesso.config`

Schema-typed, format-agnostic configuration. JSON always available; TOML and
YAML via optional extras.

```python
from gesso.config import ConfigStore, Option, Schema, Section
```

## `ConfigStore`

An application's configuration file, bound to a schema.

### Construction

| Classmethod | Use when |
| --- | --- |
| `for_app(schema, context, *, preferred=None)` | Normal use — discover inside an `AppContext`'s config directory |
| `discover(schema, directory, *, stem="config", preferred="json")` | You have a directory but no `AppContext` |
| `for_format(schema, directory, fmt, *, stem="config")` | The user explicitly chose a format |
| `for_path(schema, path)` | You have an exact file in mind; the suffix picks the codec |

All four raise `ConfigError` if the required format backend is not installed, or
if a path's suffix is not recognised.

```python
store = ConfigStore.for_app(SCHEMA, context).load()
```

!!! note "`discover` reports ambiguity"

    `discover` populates `store.others` with any further config files it found,
    rather than choosing silently. If a file exists in a format whose backend
    is missing, `discover` raises rather than creating a second config beside
    it.

### Properties

| Name | Returns |
| --- | --- |
| `schema` | The bound `Schema` |
| `path` | The `Path` of the configuration file |
| `codec` | The active `Codec` |
| `format` | The codec's name, e.g. `"json"` |
| `others` | `tuple[Path, ...]` of other config files found (empty by default) |

### Methods

| Signature | Description |
| --- | --- |
| `load()` | Read the file (if present), overlay onto schema defaults, coerce; returns `self` |
| `reload()` | Alias for `load()`, for picking up external edits |
| `save()` | Encode and write **atomically** (temp file + `os.replace`) |
| `get(dotted, default=None)` | Read `"section.key"`; with no dot, returns the whole section |
| `set(dotted, value)` | Write `"section.key"`, coercing to the declared type; raises `ConfigError` on failure |
| `as_dict()` | A deep copy of the whole configuration |
| `validate()` | `list[str]` of problems; empty means valid |
| `reset()` | Restore all values to schema defaults (does not write) |
| `exists()` | Whether the file is on disk |
| `convert_to(fmt, *, keep_backup=True)` | Rewrite in another format; returns the new `Path` |

```python
>>> store.get("editor.font_size")
13
>>> store.set("editor.font_size", "15")
>>> store.get("editor.font_size")
15
```

Behaviour worth knowing:

- `load()` **preserves** unknown keys and uncoercible values instead of dropping
  them; `validate()` reports them.
- `convert_to` **refuses to overwrite** an existing target file, and keeps the
  previous file as `<name>.bak` unless `keep_backup=False`.

## `Schema`

### `Option`

```python
@dataclass(frozen=True)
class Option:
    key: str
    type: type
    default: Any
    description: str = ""
    choices: Sequence[Any] | None = None
    minimum: float | None = None
    maximum: float | None = None
    pattern: str | None = None
```

| Method | Description |
| --- | --- |
| `coerce(value)` | Convert to the declared type; raises `ValueError` on failure |
| `check(value)` | Constraint problems with an *already-coerced* value; empty means acceptable |
| `coerce_and_check(value)` | Both, returning `(value, problems)` |

Supported `type` values: `bool`, `int`, `float`, `str`, `list`, `dict`. Anything
else raises `SchemaError` when `coerce` is called.

**Type and constraint are separate concerns.** A type says what shape a value
is; a constraint says whether that value is acceptable. `"nonsense"` fails the
type; `99999` passes the type but fails the constraint.

| Constraint | Applies to | Meaning |
| --- | --- | --- |
| `choices` | any | The value must be one of these |
| `minimum` / `maximum` | `int`, `float` | Inclusive bounds. Ignored for other types, so a stray bound on a string option cannot produce nonsense comparisons |
| `pattern` | `str` | A regular expression the **whole** value must match |

```python
Option("resolution", str, "1920x1080", pattern=r"^\d{3,4}x\d{3,4}$")
Option("quality", int, 90, minimum=1, maximum=100)
Option("effect", str, "none", choices=["none", "blur", "vignette"])
```

Constraints are enforced in two places: `Schema.validate()` reports a violation
alongside type errors, and `ConfigStore.set()` **rejects** it with a
`ConfigError` rather than storing it. Writing an unacceptable value is a
mistake at the call site, and it should surface there.

### `Section`

```python
@dataclass(frozen=True)
class Section:
    name: str
    options: tuple[Option, ...] = ()
    title: str = ""
    description: str = ""
```

| Method | Returns |
| --- | --- |
| `option(key)` | The `Option`, or `None` |
| `defaults()` | `{key: default}` for every option |

Raises `SchemaError` if two options share a `key`.

### `Schema`

```python
class Schema:
    def __init__(self, sections: Sequence[Section]) -> None
```

| Member | Returns |
| --- | --- |
| `sections` | `tuple[Section, ...]` |
| `section(name)` | The `Section`, or `None` |
| `option(section, key)` | The `Option`, or `None` |
| `defaults()` | A **fresh** `{section: {key: default}}` on every call |
| `coerce(section, key, value)` | Coerced value; unknown keys pass through unchanged |
| `validate(data)` | `list[str]` of problems with a plain dict |

Raises `SchemaError` if two sections share a name.

## Codecs

### `Codec`

Base class. Subclasses define `name`, `extensions`, and the `loads`/`dumps`
pair.

| Member | Description |
| --- | --- |
| `name` | Format name, e.g. `"json"` |
| `extensions` | `tuple[str, ...]`, e.g. `(".yaml", ".yml")` |
| `available()` | Whether it can both read **and** write right now |
| `unavailable_reason()` | Actionable explanation when `available()` is `False` |
| `loads(text)` | Decode into a `dict`; an empty document is `{}`; raises `CodecError` |
| `dumps(data)` | Encode to text, with a trailing newline |

| Codec | `name` | `extensions` | Backend |
| --- | --- | --- | --- |
| `JsonCodec` | `json` | `.json` | `json` (stdlib) — always available |
| `TomlCodec` | `toml` | `.toml` | `tomllib`/`tomli` to read, `tomli-w` to write |
| `YamlCodec` | `yaml` | `.yaml`, `.yml` | `PyYAML` (`safe_load` only) |

!!! warning "`available()` means read *and* write"

    A codec that can read but not write reports itself unavailable, because a
    configuration store must be able to save. That is why `config.toml` without
    `tomli-w` is an error rather than a read-only success.

### Registry functions

| Function | Returns |
| --- | --- |
| `builtin_codecs()` | `tuple[Codec, ...]` — the shipped codecs |
| `codec_for_name(name)` | A codec by format name; accepts `"json"`, `".json"`, `"JSON"`. Raises `LookupError` |
| `codec_for_extension(ext)` | A codec by extension, or `None` |
| `codec_for_path(path)` | A codec from a path's suffix, or `None` |
| `DISCOVERY_PRECEDENCE` | `("json", "toml", "yaml")` — order used when several configs exist |

## Exceptions

| Exception | Raised when |
| --- | --- |
| `CodecError` | A document cannot be decoded or encoded |
| `ConfigError` | A configuration cannot be located, read, written, or a value will not coerce |
| `SchemaError` | The schema *definition* is malformed (a programming error) |

The split matters: `SchemaError` means you made a mistake writing the schema and
should see it immediately during development. `ConfigError` means the user's
environment or input needs attention and should be shown to them.
