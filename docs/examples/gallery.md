# Gallery (GUI)

The first example with a window, and the last one that builds its own layout.
It puts the design system on screen — every palette, every widget, every icon
role and every design token — and lets you switch themes underneath them.

It is also a tool you can leave open. When a widget looks wrong, Gallery is
where you find out whether the fault is the palette, the stylesheet or your
own code.

## Run it

```console
$ PYTHONPATH=src:examples python -m gallery
$ PYTHONPATH=src:examples python -m gallery --theme light
$ PYTHONPATH=src:examples python -m gallery --list-themes
dark
light
```

The window has a palette switcher at the top and five cards below it: buttons,
rows, an empty state, an icon matrix, and the token inspector.

## Nothing styles itself

This is the point of the example. Every widget Gesso ships sets its **own
object name**, and the base stylesheet matches on it. The application writes no
QSS at all:

```python
card = Card(margins=20, spacing=14)
card.body.addWidget(section_title("Buttons"))
```

`Card` sets `objectName("card")`. A heading set up like this:

```python
def section_title(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("sectionTitle")
    return label
```

...is styled by the same rule the application shell's page headers use, because
they agree on the same name.

Those object names — `card`, `rowLabel`, `segGroup`, `emptyState` — are the
**public contract** between the widget library and the stylesheet. They are
also deliberately unqualified: the stylesheet says `#card`, not `QFrame#card`,
so a `QLabel` can be a card if you want one to be.

!!! tip "The one place an inline stylesheet is right"

    The token inspector draws a colour swatch per token, and it sets a
    stylesheet string to do it:

    ```python
    swatch.setStyleSheet(f"background-color: {value}; border-radius: 3px;")
    ```

    That looks like exactly the thing the design system tells you not to do. It
    is not: this colour is **data** read out of the palette at runtime. There is
    no object name that could express "whatever this token currently is", and
    hard-coding a name would defeat the point of inspecting it.

    The rule is "no *style rules* in the application" — not "no stylesheets".

## Switching palettes

`ThemeManager` does three things on `apply(name)`, and the third is the one
people forget:

```python
def apply_theme(self, name: str) -> bool:
    self.manager.apply(name)
    self._render_tokens()
    applied = self.manager.current.name if self.manager.current else None
    if applied is not None:
        self.theme_control.set_value(applied)
    ...
```

1. the **stylesheet** is re-rendered from the new palette's tokens;
2. the **`QPalette`** is rebuilt, so natively-drawn furniture — tooltips, menu
   shadows, text selection — matches instead of falling back to the platform
   default;
3. and the application repaints whatever a theme change **staled**.

That last one is the application's job, because Gesso cannot know what your
widgets are holding. Which brings us to icons.

## Icons do not repaint themselves

An icon is rendered into a `QPixmap` and tinted. A `QLabel` holds that pixmap.
A pixmap does not know the theme moved, so nothing happens unless something
rebuilds it:

```python
self.icons.iconsChanged.connect(self._refresh_icons)
```

`ThemedIcons` emits `iconsChanged` after a theme change. It says **when**; you
decide **what**. Gallery keeps the role each button was built for and re-renders
the matrix:

```python
def _refresh_icons(self) -> None:
    self._render_icons()
    for button, role in self._role_buttons:
        button.set_role(role)
```

The roles are worth knowing, because they are tokens rather than colours:

| Role | Token | For |
| ---- | ----- | --- |
| `idle` | `text_muted` | a resting icon |
| `strong` | `text` | one that should stand out |
| `active` | `accent` | selected |
| `disabled` | `text_disabled` | unavailable |
| `on-accent` | `accent_text` | sitting on an accent-coloured surface |

Because each role names a token, one piece of artwork is correct in every
theme. Adding a theme never means adding a second copy of the icons.

## The token inspector

The bottom card lists all thirty tokens, their group, and what each resolves to
in the current palette. It is the fastest way to answer "why is this the wrong
grey?".

It also shows something worth understanding about how palettes work: a palette
may be **partial**. Anything it leaves out falls back to the contract's
last-resort default, which is why a palette only has to state what it wants to
change. [Tracker](tracker.md) ships one that does exactly that.

## A fallback that is not a failure

Gallery's `apply_theme` returns whether *the palette you asked for* is the one
in force — which is not the same question as whether `apply` succeeded:

```console
$ # a palette with no file installed
>>> window.apply_theme("chartreuse")
False
>>> window.manager.current.name
'dark'
```

`ThemeManager.apply` **falls back** rather than failing. A user who deletes a
theme file should get the application's own look, not a neutral window nobody
chose. So `apply` returns `True` — something *was* applied — and only the caller
can tell the difference between "worked" and "worked, but not as asked".

That is a deliberate design, and it is the kind of thing that is much easier to
copy from a working example than to infer from an API listing.

## What it demonstrates

- `create_app` — the `QApplication`, carrying the application's identity
- `ThemeManager`: loading, applying and switching palettes at runtime
- The `QPalette` side of theming, not just the stylesheet
- `ThemedIcons`, and why `iconsChanged` exists
- The whole widget set, styled by object name alone
- The token contract, including partial palettes
- Where an inline stylesheet *is* the right answer

## Read the source

- [`examples/gallery/__init__.py`](https://github.com/QHaidry/gesso/blob/main/examples/gallery/__init__.py) — the application, the schema, and the startup
- [`examples/gallery/window.py`](https://github.com/QHaidry/gesso/blob/main/examples/gallery/window.py) — the whole window, by hand

## Next

- [Tracker](tracker.md) — the same features, with the shell doing the layout
- [The design system](../concepts/design-system.md)
- [Icons](../concepts/icons.md)
