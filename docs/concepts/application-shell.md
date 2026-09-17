# The application shell

Almost every desktop application is the same window: a list of destinations
down one side, a page for each, and a strip of live information along the
bottom. Almost every application implements it slightly differently, and gets
the collapsible-sidebar details slightly wrong.

Gesso ships that window, and the few lines of start-up that go around it.

## Starting up

```python
from gesso.ui.app import run_app


def build(shell):
    shell.add_page("home", "Home", HomePage(), icon="folder")
    shell.set_brand("My App", "does one thing well")


if __name__ == "__main__":
    raise SystemExit(run_app(APP, build))
```

`run_app` does five things, each of which every Qt application does slightly
differently:

| Step | Why it is not trivial |
| --- | --- |
| Build the `QApplication` | The name and organisation are what Qt uses to locate settings, and what the window manager shows in the task switcher |
| Set the layout direction | An RTL language mirrors the entire interface, and Qt does it without a single widget knowing |
| Apply the theme | Stylesheet *and* palette — see [the design system](design-system.md) |
| Build the window | `build` populates the shell, or returns a window of its own |
| Install an exception hook | **This is the one everybody forgets** |

!!! warning "The forgotten step"

    A Qt application whose slot raises prints a traceback to stderr and carries
    on. When the application was launched from a menu, that stderr goes nowhere
    — the user sees a button that did nothing, and there is no record of why.

    `run_app` installs a hook that logs the traceback and hands it to your
    `on_error` so you can show it. `KeyboardInterrupt` is left to Python, which
    is what `Ctrl-C` in a terminal expects.

!!! note "No high-DPI setup, deliberately"

    Qt 6 scales high-DPI displays by default. The Qt 5 attributes that used to
    enable it are deprecated no-ops that only produce warnings, so Gesso does
    not set them.

## The shell

```python
shell.add_page("settings", tr("Settings"), SettingsPage(), icon="settings",
               comment=tr("Providers and storage."), actions=(apply_button,))
```

`add_page` creates **both** the navigation entry and the page body, so the two
cannot drift apart. It returns the `Page`, and `shell.header(key)` gives you the
header row afterwards if a title or an action needs to change later.

Pages are addressed by a stable `key`, so a translated title never becomes an
identifier.

### Collapsing

Collapsing the sidebar narrows it to icons. It also **keeps every label as a
tooltip** — icon-only navigation with no labels and no tooltips is a memory
test, not an interface. The collapsed layout is keyed off a `collapsed`
property on the button, so the button is repolished when it changes; without
that the stylesheet never notices.

## The payoff from the theme tier

```python
themes.apply("light")   # navigation icons re-tint themselves
```

The shell connects to `ThemeManager.themeChanged` and repaints its navigation
icons, giving the checked entry the accent. That is the whole reason the signal
exists: without it, every application has to remember to refresh its icons at
every call site, and the failure mode — an icon left at the old colour until
something else happens to redraw it — is subtle enough to ship.

## What the shell deliberately is not

- **Not a framework you subclass into.** It is a window you populate. If you
  need a different window, return one from `build` and the shell goes unused.
- **Not a settings UI.** `SettingsExplorer` and a schema-driven `SettingsPage`
  are on the [roadmap](../roadmap.md), waiting for a second application to need
  the same shape.
- **Not Qt's translation system.** Gesso's i18n reads JSON catalogs directly,
  so there is nothing to install into Qt; `QTranslator` and `.qm` files are a
  different mechanism and would arrive as an optional backend.

## Next

[:octicons-arrow-right-24: API reference: gesso.ui.app](../reference/app.md)
