# Ship your own icons

**You will end up with** your own artwork, tinted by whichever theme is active,
in the same set as Gesso's.

Qt required. About ten minutes.

## 1. Draw one, and put it in a directory

Any SVG will do. `examples/tutorials/icons/star.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
     fill="none" stroke="#9a9a9a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M12 3l2.6 5.6 6 .8-4.4 4.2 1.1 6-5.3-3-5.3 3 1.1-6L3.4 9.4l6-.8z" />
</svg>
```

!!! note "The stroke colour does not matter"

    Gesso tints by **composition**, not by editing SVG source: it draws the
    artwork, then `CompositionMode_SourceIn` replaces the colour while keeping
    the alpha. So `stroke="#9a9a9a"` above is never seen, and one asset serves
    every theme.

    That is the whole reason a theme switch does not need a second copy of
    your icons — which is exactly what a set of fixed-colour icons makes you do.

## 2. Register the directory

```python
from gesso.ui.icons import IconRegistry

mine = IconRegistry([MY_ICONS])
print(mine.names())        # ['star']
print(mine.has("check"))   # False
```

Careful. That registry knows about your icons **and nothing else**:

```console
my directory alone provides: ['star']
  knows 'check'?  False
```

This is the mistake to know about before you make it. The base stylesheet
addresses some icons **by name** — the spin-box arrows are `chevron-up` and
`chevron-down` — so a registry that *replaced* Gesso's would leave them
unresolved in your application, at runtime, silently.

Layer instead:

```python
layered = IconRegistry([GESSO_ICONS])
layered.add_directory(MY_ICONS)      # appended, so later wins
```

```console
layered: 13 icons
  knows 'check'?  True   (Gesso's, still there)
  knows 'star'?   True    (mine, added)
```

Directories are searched in **reverse** order, so yours wins for any name the
two share. That is how you override Gesso's artwork without forking it.

## 3. Make typos loud

```python
layered.source("str")
```

```console
no icon named 'str'; available icons: check, chevron-down, chevron-left,
chevron-right, chevron-up, close, info, minus, plus, refresh, search, star, warning
```

A missing icon names the alternatives rather than returning a blank pixmap or
raising a bare `KeyError`. `"no icon called 'str'"` is a typo you want to see
immediately, and a list of what *does* exist usually contains the answer.

## 4. Ask for a role, not a colour

```python
from gesso.ui.icons import ROLE_TOKENS
```

| Role | Token | For |
| ---- | ----- | --- |
| `idle` | `text_muted` | a resting icon |
| `strong` | `text` | one that should stand out |
| `active` | `accent` | selected |
| `disabled` | `text_disabled` | unavailable |
| `on-accent` | `accent_text` | sitting on an accent-coloured surface |

Because each role names a **token** rather than a colour, one asset is correct
in every theme:

```console
dark   idle=#9a9a9a  active=#7c6cf6
light  idle=#6a6a72  active=#5b4bd6
```

Those values come out of whichever palette is applied. Add a theme and your
icons follow it; you do not touch the icons.

## 5. Attach them to a theme

```python
from gesso.ui.icons import ThemedIcons
from gesso.ui.theme import ThemeManager

themes = ThemeManager(app)
icons = ThemedIcons(layered, themes)

icons.render_pixmap("star", role="active", size=24)
icons.make_icon("star", role="idle", size=18)     # a QIcon
```

## 6. And repaint them when the theme moves

This is the part people miss.

An icon is rendered into a `QPixmap`. A `QLabel` holds that pixmap. **A pixmap
does not know the theme moved**, so changing palette leaves every icon at its
old colour unless something rebuilds it:

```python
icons.iconsChanged.connect(repaint_everything)
```

`ThemedIcons` emits `iconsChanged` after a theme change. It says **when**; your
application decides **what**. Anything holding an icon has to do something:

- a widget built from a name — `IconButton.set_role(role)` re-renders it;
- a label holding a pixmap — call `render_pixmap` again.

[Gallery](../examples/gallery.md) demonstrates both, in one window you can
switch palettes under.

!!! tip "The alternative, and why it is worse"

    Gesso could have had icons register themselves and repaint automatically.
    It does not, because that would mean every icon widget holds a reference to
    the theme manager, and your widgets would have to be Gesso's widgets. The
    signal keeps the dependency one-way: Gesso says when, you say what.

## The whole tutorial

```python
--8<-- "examples/tutorials/icons.py"
```

## Check it works

```console
$ PYTHONPATH=src python examples/tutorials/icons.py
$ QT_QPA_PLATFORM=offscreen PYTHONPATH=src python examples/tutorials/icons.py
```

The script prints a report and never opens a window, so `offscreen` is only
needed on a machine with no display.

## Where to go next

- [Icons](../concepts/icons.md) — the registry, the roles, and the tinting.
- [Make a palette](theming.md) — the other half of a theme.
- [Reference: gesso.ui.icons](../reference/icons.md)
