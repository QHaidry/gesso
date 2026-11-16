# Basket (CLI)

A grocery list, with settings that are *typed and constrained* and strings that
are *not English-only*. It is the first rung that could be mistaken for a real
program.

[Hello, Gesso](hello-cli.md) shows one setting and prints a greeting. Basket
adds the two things that make settings hard:

- some values have to be **refused**, not merely stored; and
- a string that reaches the user has to be translatable.

## Run it

```console
$ PYTHONPATH=src:examples python -m basket add milk --price 1.20
Added milk. There is 1 item on the list.

$ PYTHONPATH=src:examples python -m basket add bread
Added bread. There are 2 items on the list.

$ PYTHONPATH=src:examples python -m basket list
Shopping list
2 items, sorted by name.

   1. bread
   2. milk                    €1.20

Total: €1.20

$ PYTHONPATH=src:examples python -m basket --language fr list
Liste de courses
2 articles, triés par nom.

   1. bread
   2. milk                    €1.20

Total : €1.20
```

## A schema that refuses

The whole specification of what persists:

```python
SCHEMA = Schema(
    [
        Section(
            "display",
            title="Display",
            description="How the list is presented.",
            options=(
                Option(
                    "language", str, "auto", "Interface language.",
                    choices=("auto", "en", "fr"),
                ),
                Option("currency", str, "€", "Symbol printed before a price."),
                Option("show_prices", bool, True, "Print a column of prices."),
                Option(
                    "width", int, 24, "Width of the item column, in characters.",
                    minimum=8, maximum=60,
                ),
            ),
        ),
        Section(
            "list",
            title="List",
            description="Rules the list obeys.",
            options=(
                Option(
                    "max_items", int, 50, "Refuse to hold more than this many items.",
                    minimum=1, maximum=500,
                ),
                Option("name_pattern", str, r"^[\w][\w \-']*$", "What an item name may look like."),
            ),
        ),
    ]
)
```

`choices`, `minimum`, `maximum` and `pattern` are all **constraints**, and they
are enforced in two places that are easy to confuse:

| | Where | What it does |
| - | ----- | ------------ |
| `Schema.validate()` | When you ask | **Reports** everything wrong with the data on disk |
| `ConfigStore.set()` | At the call site | **Rejects** a value, and does not store it |

So this does not reach the file:

```console
$ python -m basket config --set list.max_items 9999
error: list.max_items: 9999 exceeds the maximum of 500
$ echo $?
2
```

9999 is a perfectly good integer. The *schema* is what refuses it, and the
message names the bounds rather than saying "invalid".

## Coercion is not validation

Those are two different jobs, and the example shows both:

```console
$ python -m basket config --set display.show_prices false
Set display.show_prices to False.
```

The string `"false"` was passed on the command line. The schema turned it into
a real `bool` — that is *coercion*, and it is why `getboolean` never appears in
this codebase. Whether `False` is a sensible thing for the setting to be is a
separate question, and for a boolean it always is.

Both halves live in `gesso.config`:

- `Option.coerce` — make it the declared shape
- `Option.check` — say whether that shape is acceptable

## Settings are not data

Basket keeps two files, and *which* file is the interesting part:

```console
$ find basket-home -type f | sort
basket-home/basket/config.json
basket-home/basket/items.json
```

- The **preferences** are `gesso.config`'s business: small, typed, and meant to
  be hand-editable.
- The **shopping list** is not. It is a list the user grows, of no fixed shape,
  so it is plain JSON in the *data* directory and Gesso stays out of it.

Putting the list in the config file would have been shorter and wrong. That is
the distinction `AppPaths` exists to make: `config_dir` for what you configure,
`data_dir` for what you accumulate.

There is a third behaviour worth copying:

```console
$ python -m basket list          # reading settings writes nothing
$ ls basket-home/basket/
items.json
```

A config file appears only once there is something to write into it. Starting
an application should not litter.

## Translations

The catalogs live beside the code, in `examples/basket/locales/`, and
`Translator.for_app` finds them:

```python
translator = Translator.for_app(
    context,
    language=language or resolve_language(store),
    locale_dir=LOCALES_DIR,
)
```

Three things are worth knowing about that line.

**A stored preference outranks a detected locale — but only when it is set.**
Basket's `language` option defaults to `"auto"`, and `resolve_language` is what
that means:

```python
def resolve_language(store: ConfigStore) -> str:
    chosen = store.get("display.language")
    if chosen and chosen != "auto":
        return chosen
    return detect_language() or DEFAULT_LANGUAGE
```

Gesso will not guess this for you. A stored preference outranking the system
locale is one possible policy; so is the opposite. Only the application knows
whether its setting means "unset" or means a literal value.

**The search order goes from the framework out to the user.** In ascending
priority: Gesso's own catalogs, then the application's, then a directory beside
the user's settings. So a user can override any string without touching the
application:

```console
$ cat basket-home/basket/i18n/fr.json
{ "basket": { "list": { "heading": "Ma liste" } } }
```

**Plural forms are the application's job**, and Basket does them by hand:

```python
def plural(t, key, count, **kwargs) -> str:
    form = "one" if count == 1 else "other"
    return t(f"{key}.{form}", count=count, **kwargs)
```

That is not laziness. Plural rules are not one-versus-many in most languages —
Russian has three forms, Arabic six — and getting them right needs real CLDR
data, which Gesso's roadmap lists as an *optional* backend rather than
pretending to have. For English and French the rule really is this simple, so
the catalogs carry both forms and the application chooses.

!!! warning "A missing translation does not fail"

    It prints English. Nothing raises, no test turns red, and the bug ships.
    Basket's suite catches it by comparing the two catalogs key-for-key:

    ```python
    def test_the_catalogs_cover_the_same_keys():
        assert keys_of(load_catalog("en")) == keys_of(load_catalog("fr"))
    ```

    If you take one test from this example, take that one.

## One flag is not the other

```console
$ python -m basket --language fr list     # this run only
$ python -m basket config --set display.language fr   # remembered
```

`--language` is a top-level flag meaning "for this run". To change the setting
you go through `config --set` like every other setting — which means it is
coerced, checked and reported by the same machinery as everything else.

This was not the first design. `basket config --language fr` looks natural and
cannot work: `argparse` will not route a top-level flag into a subcommand. The
flag was given a meaning that matches what it can actually do.

## What it demonstrates

- Constraints that **reject** at `set()` and **report** at `validate()`
- Coercion separated from validation
- Configuration and application data, in the right directories
- Reading settings without creating a file
- A translator that searches framework → application → user
- Plural forms chosen by the application, and why Gesso does not guess them
- A catalog-completeness test, which is the only cheap way to catch a missing string

## Read the source

- [`examples/basket/__init__.py`](https://github.com/QHaidry/gesso/blob/main/examples/basket/__init__.py) — identity, schema, and the profile that ties settings to a translator
- [`examples/basket/cli.py`](https://github.com/QHaidry/gesso/blob/main/examples/basket/cli.py) — the commands
- [`examples/basket/items.py`](https://github.com/QHaidry/gesso/blob/main/examples/basket/items.py) — the data, deliberately not a schema

## Next

- [Gallery](gallery.md) — the same tiers, with a window on top
- [Configuration](../concepts/configuration.md)
- [Internationalisation](../concepts/internationalisation.md)
