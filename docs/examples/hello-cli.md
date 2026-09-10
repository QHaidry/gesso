# Hello, Gesso (CLI)

A complete command-line application in one file. It stores a greeting the way
you tell it to, in any of the three supported formats, and it is short enough to
read in a few minutes.

## Run it

```console
$ PYTHONPATH=src python examples/hello.py
Hello, World!

$ PYTHONPATH=src python examples/hello.py --set greeting.name Ada
Hello, Ada!

$ PYTHONPATH=src python examples/hello.py --show
{
  "greeting": {
    "name": "Ada",
    "punctuation": "!",
    "shout": false,
    "repeat": 1
  }
}
```

## The whole program

```python
--8<-- "examples/hello.py"
```

## Reading it

The file is in four parts, and the first three are the ones Gesso cares about.

### 1. Who is this application?

```python
APP = AppSpec(
    name="Gesso Hello",
    app_id="gesso-hello",
    version="0.1.0",
    description="A tiny example application built on Gesso.",
    default_config_format="json",
)
```

Three of these fields do real work:

- `app_id` becomes the directory name — `gesso-hello/config.json`.
- `default_config_format` decides what is created on first run.
- `version` and `description` are what a future About box, QSettings
  organisation, or systemd unit will read, so that none of them has to be
  maintained separately.

### 2. What does it store?

```python
SCHEMA = Schema(
    [
        Section(
            "greeting",
            ...
            options=(
                Option("name", str, "World", "Who to greet."),
                Option("punctuation", str, "!", "Appended to the greeting."),
                Option("shout", bool, False, "Print the greeting in UPPERCASE."),
                Option("repeat", int, 1, "How many times to print the greeting."),
            ),
        )
    ]
)
```

This is the entire specification of what persists: two strings, a boolean and an
integer, each with a default. No `getboolean`, no `int(...)`, no `"true"`.

### 3. Let Gesso find the file

```python
def build_store(config_home: Path, fmt: Optional[str]) -> ConfigStore:
    """Locate this application's configuration, in *fmt* if one is forced."""
    context = AppContext(APP, AppPaths.resolve(APP.app_id, config_home=config_home))
    if fmt:
        return ConfigStore.for_format(SCHEMA, context.config_dir, fmt).load()
    return ConfigStore.for_app(SCHEMA, context).load()
```

The one line worth pausing on is `AppPaths.resolve(APP.app_id, config_home=...)`.
`--config-home` stands in for `$XDG_CONFIG_HOME`, which is what keeps the
example from writing into your real `~/.config` — and, more importantly, it is
the same mechanism that lets the test suite run without side effects.

Note what is *not* here: no `Path.home()`, no `"gesso-hello"` string in a path,
no format table. Those all come from the `AppSpec` and the schema.

### 4. Do the actual work

```python
def render(store: ConfigStore) -> str:
    """Turn the stored settings into the greeting to print."""
    text = f"Hello, {store.get('greeting.name')}{store.get('greeting.punctuation')}"
    if store.get("greeting.shout"):
        text = text.upper()
    return "\n".join([text] * store.get("greeting.repeat"))
```

Everything above this is plumbing Gesso provides. This function is the
application.

### `main`: wiring it up

`main` is ordinary `argparse`, with a few calls into the store:

| Flag | What it does |
| --- | --- |
| `--config-home PATH` | Where `$XDG_CONFIG_HOME` would be |
| `--format {json,toml,yaml}` | Force a format instead of discovering one |
| `--set KEY VALUE` | Set a value, coerced by the schema |
| `--show` | Print the whole configuration as JSON |
| `--convert FORMAT` | Rewrite the configuration in another format |

Two behaviours are worth copying:

```python
for problem in store.validate():
    print(f"warning: {problem}", file=sys.stderr)
```

Problems are **reported, not fatal** — the application still starts. And:

```python
except ConfigError as exc:
    print(f"error: {exc}", file=sys.stderr)
    return 2
```

Every failure path prints a message that names the actual problem and exits
non-zero, rather than raising a traceback at the user.

## Play with the formats

=== "JSON (default)"

    ```console
    $ python examples/hello.py --set greeting.name Ada
    $ cat hello-config/gesso-hello/config.json
    ```

    ```json
    {
      "greeting": {
        "name": "Ada",
        "punctuation": "!",
        "shout": false,
        "repeat": 1
      }
    }
    ```

=== "YAML"

    ```console
    $ python examples/hello.py --format yaml --set greeting.name Ada
    $ cat hello-config/gesso-hello/config.yaml
    ```

    ```yaml
    greeting:
      name: Ada
      punctuation: '!'
      shout: false
      repeat: 1
    ```

=== "TOML"

    ```console
    $ python examples/hello.py --format toml --set greeting.name Ada
    ```

    Requires `gesso-sdk[toml]`. Without it you get a message naming the package
    to install, not an obscure failure.

## Convert between formats

```console
$ python examples/hello.py --convert yaml
$ ls hello-config/gesso-hello/
config.json.bak  config.yaml
```

The old file is kept as a `.bak`, and the values come across intact — including
their types.

## Try to break it

```console
$ python examples/hello.py --set greeting.repeat lots
error: greeting.repeat: cannot read 'lots' as an integer
```

The value is rejected at the call site. It never reaches the file, and the
user gets a sentence instead of a stack trace.

## What it demonstrates

- Application identity without a single hard-coded path
- A typed schema replacing `getboolean`/`int()` at every call site
- All three formats, chosen at runtime, with conversion between them
- Validation that advises rather than crashes
- Errors that name the problem

## Next

- [Defining a schema](../guides/defining-a-schema.md)
- [API reference: gesso.config](../reference/config.md)
