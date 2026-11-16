# Quickstart

Five minutes, one file, a working application that remembers its settings — in
whichever format you prefer.

## The fast way: `gesso new`

```bash
pip install "gesso-sdk[gui]"
gesso new myapp
cd myapp
pip install -e ".[dev]"
pytest
python -m myapp.main
```

That writes a **working** application — config schema, palette, translations, a
window and a passing test — so you start from something that runs rather than
an empty directory. See [the generator](../reference/generator.md) for what is
in it.

The rest of this page builds the same foundations by hand, which is worth
reading if you want to know what the scaffold is doing.

## 1. Write the application

Save this as `myapp.py`:

```python
from gesso.config import ConfigStore, Option, Schema, Section
from gesso.core import AppContext, AppSpec

# Who is this application?
APP = AppSpec("My App", app_id="myapp")

# What does it store?
SCHEMA = Schema(
    [
        Section(
            "editor",
            options=(
                Option("font_size", int, 13, "Editor font size in points."),
                Option("wrap", bool, True, "Wrap long lines."),
                Option("theme", str, "dark", "Colour scheme."),
            ),
        )
    ]
)


def main() -> None:
    context = AppContext(APP)
    store = ConfigStore.for_app(SCHEMA, context).load()

    print("font size:", store.get("editor.font_size"))
    print("wrap     :", store.get("editor.wrap"))

    # `set` takes whatever you give it and coerces to the declared type.
    store.set("editor.font_size", "15")  # a string in, an int out
    print("after set:", store.get("editor.font_size"), end=" ")
    print(f"({type(store.get('editor.font_size')).__name__})")

    store.save()
    print("saved to :", store.path)


main()
```

## 2. Run it

```console
$ python myapp.py
font size: 13
wrap     : True
after set: 15 (<class 'int'>)
saved to : /home/you/.config/myapp/config.json
```

That last line is the interesting one. You never said *where* to put the
configuration or *what format* to use — Gesso derived both. The directory comes
from `app_id` placed under `$XDG_CONFIG_HOME`, and the format from the
application's `default_config_format`.

## 3. Look at what it wrote

```console
$ cat ~/.config/myapp/config.json
```

```json
{
  "editor": {
    "font_size": 15,
    "wrap": true,
    "theme": "dark"
  }
}
```

Notice `font_size` is the **number** `15` and `wrap` is a real **boolean** —
not `"15"` and `"true"`. That is the schema doing its job. A configuration
whose values are all strings cannot survive contact with TOML, and produces a
steady stream of bugs long before that.

## 4. Change the format

The format is a property of the *file*, not of its contents, so switching is
just a different extension. Copy the same file and change one line:

```python
store = ConfigStore.for_format(SCHEMA, context.config_dir, "yaml").load()
```

```console
$ python myapp.py
$ cat ~/.config/myapp/config.yaml
```

```yaml
editor:
  font_size: 15
  wrap: true
  theme: dark
```

Or convert an existing configuration in place:

```python
store.convert_to("toml")   # writes config.toml, keeps config.yaml.bak
```

!!! warning "TOML needs an extra"

    TOML *writing* requires `tomli-w`. Without it, Gesso raises a clear error
    naming the package to install rather than failing obscurely. See
    [Installation](installation.md#optional-extras).

## 5. See the whole example

`myapp.py` above is the short version. The [`examples/hello.py`](../examples/hello-cli.md)
walkthrough builds the same idea into a complete command-line application with
argument parsing, `--set`, `--show` and `--convert`.

## Where to go next

- **Understand the design** — [Architecture](../concepts/architecture.md)
- **Learn the identity layer** — [Application identity](../concepts/application-identity.md)
- **Go deep on configuration** — [Configuration](../concepts/configuration.md)
