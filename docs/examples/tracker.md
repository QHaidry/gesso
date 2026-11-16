# Tracker (GUI)

The top of the ladder: every tier in one small application. Typed settings, a
habit log kept apart from them, two languages with plural forms, a palette of
its own, its own icons, and four pages assembled by the application shell.

It is also the **shortest** of the three GUI examples to read — and that is the
point.

## Run it

```console
$ PYTHONPATH=src:examples python -m tracker
$ PYTHONPATH=src:examples python -m tracker --language fr
$ PYTHONPATH=src:examples python -m tracker --theme light
$ PYTHONPATH=src:examples python -m tracker --config-home ./tracker-home
```

It opens on **Today** — a toggle per habit, a progress line, and a streak under
each habit. **History** lists the last seven days. **Settings** is every
setting. **About** says where the two files live.

## Compare it with Gallery

This is the most useful thing to do with this example.

[Gallery](gallery.md) builds its own window. It creates a `QMainWindow`, a
central widget, a root layout, a sidebar frame, a brand label, a navigation
column, a button group, a scroll area and a page stack — roughly 130 lines of
chrome before it does anything of its own.

Tracker does this instead:

```python
for key, label, comment, icon in PAGES:
    page = pages[key]
    shell.add_page(
        key,
        session.t(label),
        page,
        comment=session.t(comment) if comment else "",
        icon=icon,
        actions=page.header_actions(),
    )
```

Ten lines. Tracker has *four* pages, two languages, its own palette, its own
icons and a settings file — and it is shorter than Gallery, which has one page
and none of those.

`add_page` is doing the work: it wraps the page in a header, builds a
navigation entry for it, keeps the two in step, and adds it to the stack. The
page never learns where its buttons ended up.

## A page is just a widget

Tracker's pages share a tiny base class:

```python
class Page(QWidget):
    def header_actions(self) -> List[QWidget]:
        """Buttons for the header row. Default: none."""
        return []

    def retranslate(self) -> None:
        """Say everything again, in whatever language is now active."""
```

Both hooks are optional, and neither is a Gesso type. A page is a `QWidget`;
these are just the two questions the application asks of one. Adding a fifth
page means writing a widget.

## The shell speaks your language

Gesso's shell has strings of its own. It does not ship them in English and
leave you to live with it — it looks them up through **your** translator, under
a reserved `gesso.` domain:

```python
return run_app(
    APP,
    lambda shell: build(shell, session),
    ...
    translate=session.t,
)
```

So when Tracker switches to French, the drawer button's tooltip changes too:

```console
>>> shell.drawer_button.toolTip()
'Show or hide the navigation'
>>> # ...switch to French...
>>> shell.drawer_button.toolTip()
'Afficher ou masquer la navigation'
```

That is the reserved domain earning its keep. The framework owns `gesso.*`, the
application owns everything else, and the two cannot collide. A missing
translation shows the raw key rather than an empty string, so you can see it on
screen and grep for it in the source.

## Changing language without restarting

A page's title lives in **three** places — the `Page` record, the navigation
button, and the header. Retitling two of them is worse than retitling none, so
the shell does all three at once:

```python
shell.set_page_title(key, session.t(label), session.t(comment))
```

...and re-says its own strings:

```python
shell.retranslate()
```

Both of these exist because Tracker needed them. That is worth noticing: a
framework grows its API from the applications that use it, not from design
sessions.

## A palette of its own

Tracker ships `examples/tracker/themes/midnight.json`, and it is deliberately
**partial** — sixteen tokens out of thirty:

```json
{
  "name": "Midnight",
  "description": "Tracker's own palette. Deliberately partial: the contract supplies anything a palette leaves out...",
  "colors": {
    "window": "#15161e",
    "panel": "#1b1d27",
    "card": "#22242f",
    "text_strong": "#eef1ff",
    "accent": "#7aa2f7"
  }
}
```

The fourteen it omits are not missing. The token contract has a last-resort
default for every token, so a palette only has to state what it wants to
change. `ThemeManager.problems("midnight")` returns nothing, and the scrollbars
still work.

!!! warning "`builtin_theme_dirs` replaces; `icon_dirs` appends"

    These two arguments look like a pair and behave differently:

    ```python
    builtin_theme_dirs=[THEMES_DIR, BUILTIN_PALETTES_DIR],
    icon_dirs=[ICONS_DIR],
    ```

    Passing only `[THEMES_DIR]` gives you Midnight and **loses** `dark` and
    `light`. This is deliberate — Gesso's stylesheet references Gesso's icon
    *names*, so those directories must stay resolvable, whereas nothing breaks
    if a palette is absent — but it surprises people. An application that wants
    its own palette *and* Gesso's names both.

## Icons from two places, one registry

Tracker ships two icons — a chart and a set of sliders — and uses two of
Gesso's:

```python
PAGES = (
    ("today", "tracker.nav.today", "tracker.page.today", "check"),
    ("history", "tracker.nav.history", "tracker.page.history", "streak"),
    ("settings", "tracker.nav.settings", "tracker.page.settings", "settings"),
    ("about", "tracker.nav.about", "", "info"),
)
```

All four resolve, because Tracker's directory is **appended** to Gesso's rather
than substituted for it. That is what makes `icon_dirs` an append: the
stylesheet's spin-box arrows are addressed by name from Gesso's directory, so
replacing the search path would leave them unresolved.

## Settings, and the data next to them

The schema is ordinary — choices, bounds, defaults:

```python
Section(
    "display",
    title="Display",
    description="How the window looks and reads.",
    options=(
        Option("language", str, "auto", "Interface language. 'auto' follows your system locale.",
               choices=("auto", "en", "fr")),
        Option("theme", str, "midnight", "Palette to use."),
        Option("show_streaks", bool, True, "Show how many days in a row each habit runs."),
        ...
    ),
)
```

Two things about it are worth noting.

**No `choices` for the theme.** The valid palettes are whichever ones Gesso can
find — Midnight, plus Gesso's, plus whatever the user dropped into
`~/.config/tracker/themes/`. A schema listing them would be wrong the moment a
user added one, so it constrains what it can and stays out of the rest.

**The habits are not in here.** They live in `tracker.json` in the *data*
directory, as plain Python. A schema is for settings: small, typed, and meant
to be hand-edited. A list the user grows is none of those things.

Moving to `auto` also does not freeze today's answer:

```python
def set_language(self, language: str, *, persist: bool = True) -> str:
    chosen = language or "auto"
    resolved = chosen if chosen != "auto" else (detect_language() or DEFAULT_LANGUAGE)
    ...
    if persist:
        self.store.set("display.language", chosen)
```

Picking "System" stores `auto`, so the preference keeps meaning "whatever my
machine says" rather than becoming a snapshot of this afternoon's locale.

## What it demonstrates

- `run_app` and `AppShell`: pages, navigation, headers with actions, a live
  status line, and one call each to build all of it
- Gesso's own strings translated through the application's translator
- Retitling and retranslating without a restart
- A partial palette, completed by the token contract
- An application's icons layered over Gesso's in one registry
- Settings in the config directory, data in the data directory, and why
- `auto` as a stored value that still means automatic

## Read the source

- [`examples/tracker/__init__.py`](https://github.com/QHaidry/gesso/blob/main/examples/tracker/__init__.py) — the ladder's top: `build`, `run`, and how the pages are wired
- [`examples/tracker/pages.py`](https://github.com/QHaidry/gesso/blob/main/examples/tracker/pages.py) — the four pages, and the two hooks
- [`examples/tracker/session.py`](https://github.com/QHaidry/gesso/blob/main/examples/tracker/session.py) — settings, data and a translator, in one object
- [`examples/tracker/store.py`](https://github.com/QHaidry/gesso/blob/main/examples/tracker/store.py) — the log, and why it is not a schema

## Next

- [The application shell](../concepts/application-shell.md)
- [Tutorial: build a windowed application](../tutorials/shell.md)
- [Reference: gesso.ui.app](../reference/app.md)
