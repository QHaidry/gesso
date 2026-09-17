# `gesso.ui.icons`

SVG icons rendered and tinted at runtime. **Requires PySide6.**

```python
from gesso.ui.icons import IconRegistry, ThemedIcons, IconError
```

## `IconRegistry`

A search path of directories containing `<name>.svg` files. Later directories
win, so an application layers its own icons over Gesso's.

```python
registry = IconRegistry()                      # just Gesso's icons
registry = IconRegistry([mine, gesso_icons])   # later wins
registry.add_directory(Path("myapp/icons"))    # highest priority
```

| Member | Returns |
| --- | --- |
| `directories` | The directories in priority order |
| `names()` | Every icon available, sorted |
| `path(name)` | The file an icon resolves to, or `None` |
| `has(name)` | Whether an icon resolves |
| `source(name)` | The SVG text; raises `IconError` if unknown |
| `render_pixmap(name, size=18, tint="#9a9a9a")` | A tinted `QPixmap` |
| `make_icon(name, tint="#9a9a9a", size=18, sizes=None)` | A `QIcon`, optionally at several sizes |

`render_pixmap` and `source` raise `IconError` naming the available icons when
a name does not resolve. `tint=None` preserves the artwork's own colours, for
multi-colour logos that should not be flattened.

## `ThemedIcons`

Icons tinted from a theme, re-tinted when that theme changes.

```python
class ThemedIcons(QObject):
    iconsChanged = Signal()

    def __init__(
        self,
        registry: IconRegistry | None = None,
        theme_manager: ThemeManager | None = None,
        role_tokens: dict[str, str] | None = None,
        parent: QObject | None = None,
    ) -> None
```

`theme_manager` is duck-typed: anything exposing `themeChanged`, `current` and
`contract` works, and it is optional — an application with no theming still
renders icons.

| Member | Description |
| --- | --- |
| `registry` | The underlying `IconRegistry` |
| `themes` | The theme manager, if any |
| `roles()` | The known role names, sorted |
| `color(role="idle")` | The colour a role resolves to **right now** |
| `make_icon(name, role="idle", size=18, sizes=None)` | A `QIcon` tinted for the role |
| `render_pixmap(name, role="idle", size=18)` | A tinted `QPixmap` |

`color` raises `IconError` for an unknown role, naming the known ones. It falls
back to the token contract's default when no theme has been applied yet, so an
icon built during start-up matches the stylesheet.

`iconsChanged` is emitted after `themeChanged`, so a widget holding an icon can
rebuild it without knowing why.

`role_tokens` overrides the role-to-token mapping for an application that wants
different colours for the same purposes.

## Constants

| Name | Value |
| --- | --- |
| `ICONS_DIR` | The icons shipped with the package |
| `DEFAULT_SIZE` | `18` |
| `DEFAULT_TINT` | `"#9a9a9a"` — the contract's `text_muted` |
| `ROLE_TOKENS` | The role-to-token map (see [Icons](../concepts/icons.md#roles-not-colours)) |

## Exceptions

| Exception | Raised when |
| --- | --- |
| `IconError` | An icon cannot be found, read or rendered; or a role is unknown |
