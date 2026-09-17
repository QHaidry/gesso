# Icons

Icons follow the same rule as the rest of the design system: **one asset, every
theme**. An SVG is rendered into a pixmap and tinted at request time, so adding
a theme never means adding a second copy of the artwork — which is exactly what
a set of fixed-colour icons forces you to do.

## Tinting

Tinting is a composition, not an edit to the SVG source. The artwork is drawn,
then `CompositionMode_SourceIn` replaces its colour while preserving its alpha:

```python
registry = IconRegistry()
pixmap = registry.render_pixmap("check", size=24, tint="#ff0000")
```

That is why the `stroke` colour inside the shipped SVGs does not matter, and
why one file renders correctly at every size.

Pass `tint=None` to keep the artwork's own colours — the right choice for a
multi-colour logo, where flattening to one colour would lose the design.

## Roles, not colours

An icon is requested by **role**, and the role decides which token it draws its
colour from:

| Role | Token | For |
| --- | --- | --- |
| `idle` | `text_muted` | A resting toolbar or navigation icon |
| `strong` | `text` | Emphasised icon |
| `active` | `accent` | The selected or primary action |
| `disabled` | `text_disabled` | An unavailable action |
| `on-accent` | `accent_text` | An icon sitting on an accent fill |

Naming roles by *purpose* rather than by colour is what lets a theme decide
what "active" looks like without anything else changing.

## Icons that follow the theme

```python
from gesso.ui.icons import ThemedIcons
from gesso.ui.theme import ThemeManager

themes = ThemeManager(app)
icons = ThemedIcons(theme_manager=themes)

button.setIcon(icons.make_icon("refresh", role="active"))
```

`ThemedIcons` connects to the manager's `themeChanged` signal and re-emits
`iconsChanged`, so a widget holding an icon can rebuild it without knowing why.

!!! note "Why this signal matters"

    When tinting is done by hand at each call site, switching theme leaves every
    icon at its **old** colour until something else happens to redraw it — an
    interface that is subtly wrong, and hard to attribute to anything. The
    signal removes the class of bug rather than the instance.

Before any theme has been applied, a role still resolves — to the token
contract's default, which is the same value the stylesheet will use. An icon
built during start-up, before the first `apply()`, is therefore not visibly
different from one built after it.

## Adding your own icons

`IconRegistry` searches directories in order, later ones winning, so an
application layers its own icons over Gesso's without forking the set:

```python
registry = IconRegistry()
registry.add_directory(Path("myapp/icons"))
```

A missing icon names the alternatives rather than rendering nothing:

```
IconError: no icon named 'refrsh'; available icons: check, chevron-down, ...
```

That message is the point. A reference to an icon that is not shipped renders
as *nothing at all* — no error, no placeholder, just a control that is quietly
missing its picture.

## The shipped set

Gesso ships a deliberately small starter set: chevrons in four directions,
`check`, `close`, `plus`, `minus`, `refresh`, `search`, `warning` and `info`.
The machinery is the deliverable; adding an SVG to the directory is the whole
of "adding an icon".

The base stylesheet already references `chevron-up` and `chevron-down` for the
spin-box arrows, and a test asserts that **every icon the stylesheet references
exists** — the same drift check the token contract gets.

## Next

[:octicons-arrow-right-24: API reference: gesso.ui.icons](../reference/icons.md)
