# Build a windowed application

**You will end up with** two pages, a header button, a live status line and a
theme — without writing the sidebar, the navigation, the page stack or a single
line of styling.

Qt required. About fifteen minutes. This is the tutorial the
[Tracker example](../examples/tracker.md) is built on.

## 1. The entry point is one call

```python
from gesso.ui.app import run_app

if __name__ == "__main__":
    raise SystemExit(run_app(APP, build))
```

`run_app` does everything a Qt application does slightly differently in every
project:

| | What it does |
| - | ------------ |
| `create_app` | makes the `QApplication` and sets its metadata from the `AppSpec` |
| layout direction | mirrors the whole interface if the language is right-to-left |
| theme | makes a `ThemeManager`, applies the stored or given palette |
| palette | sets the `QPalette`, so native furniture matches |
| icons | makes a `ThemedIcons` over Gesso's icons plus any `icon_dirs` |
| exception hook | **shows** an error raised inside a slot, instead of swallowing it |
| window | makes the shell, calls `build`, shows it, runs the loop |

That exception hook is the one people never write and always need. Without it,
an exception in a Qt slot is printed to a terminal nobody is reading, and the
application carries on looking fine.

## 2. A page is an ordinary widget

```python
class HomePage(QWidget):
    def __init__(self, icons, *, on_change=None, parent=None):
        super().__init__(parent)
        ...
```

No base class. No registration. No decorator. A page is a `QWidget`, and the
shell wraps it in a header and gives it a navigation entry.

The two methods below are **conventions**, not Gesso types — but they are worth
adopting, because they are the only two questions the shell needs answered:

```python
def header_actions(self):
    """Buttons this page wants in its header."""
    button = IconButton("plus", icons=self.icons, tooltip="Add a note")
    button.clicked.connect(self.add_note)
    return [button]
```

The page says *which* buttons it wants. The shell decides *where* they go. The
page never learns where that was — which is why it keeps working when the
layout changes.

```python
def retranslate(self):
    """Say everything again, in whatever language is now active."""
```

Optional, and only needed if your strings come from a catalog. See
[step 6](#6-and-a-language-you-can-change-live).

## 3. Tell the shell what to show

```python
def build(shell):
    home = HomePage(shell.icons, on_change=lambda: shell.set_info(f"{home.count()} notes"))

    shell.set_brand(APP.display_name, "two pages, one call to run_app")

    shell.add_page(
        "home", "Home", home,
        comment="Your notes live here.",
        icon="check",
        actions=home.header_actions(),
    )
    shell.add_page("about", "About", AboutPage(), comment="What this is.", icon="info")

    shell.set_message("Ready.")
    shell.set_info("0 notes")
```

`add_page` does more than it looks like:

- wraps your widget in a header carrying the title and comment;
- creates the **navigation entry**, with the icon, in the same call;
- adds the page to the content stack;
- keeps the navigation button's checked state in step with the visible page.

That last point is why the navigation is not hard-coded anywhere: a page and its
destination are created together, so the two cannot drift apart.

`shell.icons` and `shell.theme_manager` are ready by the time `build` is
called, so a page can be handed them without the application building its own.

## 4. The status bar has two halves

```python
shell.set_message("Ready.")       # left: transient, e.g. "Saved."
shell.set_info("0 notes")         # right: standing information
```

`set_message` takes an optional timeout in milliseconds and reverts afterwards,
which is what you want for "Downloaded 12 images." `set_info` is for the state
of the world, and it stays put.

## 5. Do not reach for the shell from inside a page

Notice the shape in step 3:

```python
on_change=lambda: shell.set_info(f"{home.count()} notes")
```

The page reports **that something happened**; the application decides what that
means. The alternative — the page walking up to its window with
`self.window().set_info(...)` — couples every page to the shell, and is exactly
what makes a UI hard to test in isolation. `HomePage` in the tutorial has no
idea it is inside a shell.

## 6. And a language you can change live

If your strings come from a catalog, changing language needs three things, and
the shell provides two of them:

```python
def retranslate():
    shell.set_brand(APP.display_name, session.t("app.tagline"))
    # A page's title lives in the Page record, the navigation button AND the
    # header. Retitling two of three is worse than retitling none.
    shell.set_page_title("home", session.t("app.nav.home"), session.t("app.page.home"))
    # Gesso's own strings, under the reserved `gesso.` domain.
    shell.retranslate()
    for page in pages.values():
        page.retranslate()
```

And when you build the application, hand the shell **your** translator:

```python
run_app(APP, build, translate=t)
```

That is what makes `shell.retranslate()` come out in the right language rather
than English. Gesso's own strings live under `gesso.*` — a reserved domain the
framework owns and your catalogs cannot collide with — and a missing
translation shows the raw key rather than an empty label, so you can see it on
screen and grep for it.

## 7. A window of your own, if you need one

`build` may return a window instead of populating the shell:

```python
def build(shell):
    return MyOwnWindow()
```

`run_app` shows that instead. (Return a `QWidget` or nothing — anything else is
a mistake, and `run_app` says so rather than failing inside Qt's start-up.)
Returning one is rarely right, but it is the escape hatch when the shell's
shape genuinely does not fit.

## The whole tutorial

```python
--8<-- "examples/tutorials/window.py"
```

## Check it works

```console
$ PYTHONPATH=src python examples/tutorials/window.py
$ PYTHONPATH=src python examples/tutorials/window.py --theme light
$ PYTHONPATH=src python examples/tutorials/window.py --check     # build and exit
```

## Watch a bigger one

[Tracker](../examples/tracker.md) is this tutorial grown up: four pages, its
own palette, its own icons, two languages, and a settings file — in **fewer**
lines than [Gallery](../examples/gallery.md), which has one page and builds its
own window. Reading those two side by side is the clearest statement of what
the shell is for.

## Where to go next

- [The application shell](../concepts/application-shell.md)
- [Reference: gesso.ui.app](../reference/app.md)
- [Scaffold a new project](../getting-started/quickstart.md) — `gesso new`
  generates exactly this shape, already wired.
