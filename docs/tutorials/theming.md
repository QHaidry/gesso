# Make a palette

**You will end up with** a palette that states only what it wants to change,
and a rendered stylesheet — checked without opening a window.

No Qt at all. About ten minutes.

!!! tip "This runs without a toolkit"

    The token contract and the stylesheet renderer are **Qt-free**. That is
    deliberate, and this tutorial proves it: at the end the script prints which
    PySide6 modules it loaded, and the answer is none.

    You can therefore check a palette on a build server, in a pre-commit hook,
    or while your GUI dependencies are still installing.

## 1. See what you can set

```python
from gesso.ui.theme import BASE_CONTRACT, TOKEN_GROUPS

print(len(BASE_CONTRACT), "tokens in", len(TOKEN_GROUPS), "groups")
for group, tokens in BASE_CONTRACT.groups().items():
    print(f"  {group:<9} {', '.join(t.key for t in tokens)}")
```

```console
the contract declares 30 tokens in 9 groups:
  surfaces  window, panel, card, card_hover, preview_bg, menu_bg, nav_active_bg, tooltip_bg
  text      text_strong, text, text_muted, text_disabled, tooltip_text
  accent    accent, accent_hover, accent_text, selection
  buttons   btn_bg, btn_hover, btn_active
  borders   border, border_strong
  inputs    input_bg, input_border, focus_border
  scroll    scroll_handle, scroll_handle_hover
  menu      menu_hover
  status    status_bg, status_text
```

Thirty is a deliberately small number. A token earns its place by appearing in
the stylesheet, and the stylesheet only covers the widgets Gesso actually
ships — so there are no tokens for things that do not exist yet.

## 2. A palette is a JSON file, and it may be short

```json
{
  "name": "Midnight",
  "description": "Tracker's own palette.",
  "colors": {
    "window": "#15161e",
    "panel": "#1b1d27",
    "card": "#22242f",
    "text_strong": "#eef1ff",
    "accent": "#7aa2f7",
    "accent_text": "#101223"
  }
}
```

Six of thirty. The other twenty-four are **not missing** — the contract has a
last-resort default for every token:

```python
resolved = BASE_CONTRACT.resolve(PARTIAL)
print(len(resolved))                       # 30
print(resolved["window"])                  # #15161e  (given)
print(resolved["scroll_handle"])           # #4a4a4a  (from the contract)
```

That is what makes a palette this short possible. You state what you want to
change; everything else keeps working.

## 3. Know the difference between a typo and a gap

They are different problems with different fixes, so they are reported
separately:

```console
unknown tokens: ['acccent']
missing tokens: 24
```

- **unknown** — a key the contract does not define. A misspelt token would
  otherwise be silently dropped, and you would spend an afternoon wondering why
  one colour never changes. This is *always* a bug.
- **missing** — a token the palette does not state. Usually fine; sometimes you
  meant to set it. Use `problems(name)` when you want to know whether a palette
  is complete, and `--verbose` style reporting when you want to know what it
  leaves to the contract.

## 4. Render the stylesheet

```python
from gesso.ui.theme import QssError, render

colors = BASE_CONTRACT.resolve(PARTIAL)
try:
    render(colors)
except QssError as exc:
    print(f"render refused: {exc}")
```

```console
render refused: the stylesheet needs tokens that were not provided: icon_dir
```

Exactly one placeholder in the stylesheet is **not** a token: `icon_dir`, a
filesystem path, because QSS wants a path and not a colour. Pass it alongside:

```python
sheet = render(colors, {"icon_dir": "/usr/share/gesso/icons"})
print(len(sheet))          # 9460
print("#7aa2f7" in sheet)  # True
```

!!! warning "Render fails loudly, and that is the point"

    `string.Template.substitute` raises on the *first* gap it meets. That is a
    feature: a stylesheet that silently lost its focus ring, or a palette that
    quietly failed to apply, is the kind of bug that is found by a user rather
    than by you.

    It is also why the checks in steps 2 and 3 exist — so you meet the problem
    here, in a script, rather than there, in a window.

## 5. Hand the palette to a manager

`ThemeManager` is the Qt half. It renders the stylesheet *and* builds a
`QPalette`, so natively-drawn furniture — tooltips, text selection, menu
shadows — matches the theme instead of falling back to the platform default:

```python
from gesso.ui.theme import ThemeManager

manager = ThemeManager(app, user_dir=paths.config_dir / "themes", seed=True)
manager.apply("midnight")
```

`seed=True` copies each built-in palette into the user's directory once, so the
theme is **discoverable and therefore editable**. Copies are only written where
nothing exists, so a later release cannot silently undo someone's customisation.

Search order, in ascending priority: the built-ins, then the user's directory.
Exactly the same shape as translation catalogs.

## The whole tutorial

```python
--8<-- "examples/tutorials/palette.py"
```

## Check it works

```console
$ PYTHONPATH=src python examples/tutorials/palette.py
```

The last line is the interesting one:

```console
PySide6 modules loaded: none
```

## Watch the real thing

[Gallery](../examples/gallery.md) puts the whole contract on screen with a live
palette switcher and a colour chip per token — the fastest way to answer "why
is this the wrong grey?".

## Where to go next

- [The design system](../concepts/design-system.md) — the contract, the object
  names, and why the two halves are split the way they are.
- [Ship your own icons](icons.md) — the other half of a theme.
- [Reference: gesso.ui.theme](../reference/theme.md)
