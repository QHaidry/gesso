# `gesso.ui.theme`

The design system: a token contract, a stylesheet, and a theme manager.

```python
from gesso.ui.theme import BASE_CONTRACT, render          # no Qt
from gesso.ui.theme import ThemeManager                   # needs Qt
```

## Token contract

### `Token`

```python
@dataclass(frozen=True)
class Token:
    key: str
    default: str
    group: str = "misc"
    description: str = ""
```

The default is a **last-resort** value: it is what an unset token resolves to,
so a partial theme still renders.

### `TokenContract`

```python
class TokenContract:
    def __init__(self, tokens: Sequence[Token]) -> None
```

Raises `ValueError` if two tokens share a `key`.

| Member | Returns |
| --- | --- |
| `tokens` | `tuple[Token, ...]` |
| `token(key)` | The `Token`, or `None` |
| `keys()` | Every token key |
| `defaults()` | `{key: default}` — the neutral palette |
| `groups()` | Tokens by group, in `TOKEN_GROUPS` order |
| `unknown(colors)` | Keys the contract does not know — almost always a typo |
| `missing(colors)` | Contract tokens absent from `colors` |
| `resolve(*layers)` | Layers merged over the defaults, later winning, values stringified |

Also supports `len()`, iteration and `in`.

### `BASE_CONTRACT`

The 30-token contract every Gesso application shares. `TOKEN_GROUPS` is the
presentation order used by `groups()`.

## Stylesheet rendering

| Function | Description |
| --- | --- |
| `template()` | The base stylesheet as a `string.Template`, read once and cached |
| `placeholders(text=None)` | Every token name the stylesheet references, sorted |
| `missing_tokens(colors)` | Tokens the stylesheet needs but `colors` does not supply |
| `render(colors, extra=None)` | The full stylesheet, ready for `setStyleSheet` |

`placeholders()` derives the required-token list **from the stylesheet**, so the
two cannot disagree. `render` raises `QssError` naming **every** missing token
rather than failing one at a time.

`extra` carries values that are not design tokens. `EXTRA_KEYS` names them —
currently just `icon_dir`, a filesystem path rather than a colour.

`BASE_QSS_PATH` is where the base stylesheet lives.

## `Theme`

```python
@dataclass(frozen=True)
class Theme:
    name: str
    colors: Dict[str, str]
    description: str = ""
    explicit: Tuple[str, ...] = ()
```

A *resolved* palette: every contract token has a value. `explicit` records the
tokens the theme's own files set, as opposed to those inherited — which is what
lets `coverage()` tell the difference.

| Member | Description |
| --- | --- |
| `get(key, default=None)` | A token's value |
| `theme[key]` / `key in theme` | Direct access |
| `as_dict()` | A copy of the resolved palette |
| `is_explicit(key)` | Whether the theme sets it, rather than inheriting it |

## `ThemeManager`

```python
class ThemeManager(QObject):
    themeChanged = Signal(str)

    def __init__(
        self,
        app=None,
        *,
        builtin_dirs: Sequence[Path] | None = None,
        user_dir: Path | None = None,
        contract: TokenContract | None = None,
        default: str | None = None,
        icons_dir: Path | None = None,
        seed: bool = False,
        parent: QObject | None = None,
    ) -> None
```

| Parameter | Meaning |
| --- | --- |
| `app` | The `QApplication` to style. Without one, themes still load and validate — they just cannot be applied |
| `builtin_dirs` | Directories of `<name>.json` palettes, later winning. Defaults to Gesso's own; pass your application's to layer over them |
| `user_dir` | The user's overrides, which win over every built-in |
| `contract` | The token contract to resolve against |
| `default` | The theme used when a caller names none |
| `icons_dir` | Where the stylesheet's icon references point |
| `seed` | Copy the built-in palettes into `user_dir` on construction, so they can be edited |

| Property | Returns |
| --- | --- |
| `contract` | The token contract |
| `app` | The application, if any |
| `builtin_dirs` | The built-in directories, in priority order |
| `user_dir` | The override directory, if any |
| `current` | The theme most recently applied |

| Method | Description |
| --- | --- |
| `search_dirs()` | Every directory consulted, lowest priority first |
| `names()` | Available theme names, sorted |
| `exists(name)` | Whether a theme is available |
| `load(name=None)` | Resolve a theme: defaults, then each directory in order |
| `problems(name=None)` | Tokens a theme sets that the contract does not know |
| `coverage(name=None)` | `{"explicit": [...], "inherited": [...], "unknown": [...]}` |
| `stylesheet(name=None)` | The full stylesheet, with `icon_dir` filled in |
| `palette(theme)` | A matching `QPalette` |
| `seed_user_dir(overwrite=False)` | Copy the built-in palettes into `user_dir`; returns the paths written |
| `apply(name=None)` | Apply, returning whether it worked |

### `seed_user_dir`

A user cannot edit a theme they cannot see, so seeding makes the shipped
palettes discoverable. Copies are only written where nothing exists unless
`overwrite` is set, which means an edit is never clobbered — and a later release
of an application cannot silently undo a user's customisation. Failures are
ignored: a read-only config directory costs the user their copies, not the
application.

### `apply`

Sets the stylesheet **and** the palette, and emits `themeChanged` when the
theme actually changes. A name with no palette installed falls back to the
default theme, so a user whose theme file was deleted gets the application's own
look rather than a neutral one.

Returns `False` — rather than raising — when there is no application to style
or the stylesheet cannot be rendered: a theme is a preference, and a broken one
should not stop an application opening.

Re-applying the same theme does not re-emit. Widgets re-tint on a change, and a
redundant signal would make every application redraw for nothing.

### `palette`

Qt draws tooltips, menu frames and other native furniture from the
`QPalette`, **not** from the stylesheet. Setting only the stylesheet leaves
those at the platform default, which is how a themed application ends up with a
yellow tooltip.

## Constants

| Name | Value |
| --- | --- |
| `DEFAULT_THEME` | `"dark"` |
| `BUILTIN_PALETTES_DIR` | The palettes shipped with the package |
| `ICONS_DIR` | The icons the stylesheet references |

## Exceptions

| Exception | Raised when |
| --- | --- |
| `QssError` | A stylesheet cannot be read or rendered |
| `ValueError` | A token contract declares a duplicate key |
