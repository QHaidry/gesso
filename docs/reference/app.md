# `gesso.ui.app`

Starting an application, and the window it is handed. **Requires PySide6.**

```python
from gesso.ui.app import AppShell, create_app, install_exception_hook, run_app
```

## `run_app`

```python
def run_app(
    spec: AppSpec,
    build: Callable[[AppShell], QMainWindow | None],
    *,
    argv: Sequence[str] | None = None,
    theme: str | None = None,
    builtin_theme_dirs: Sequence[Path] | None = None,
    user_theme_dir: Path | None = None,
    icons_dir: Path | None = None,
    icon_dirs: Sequence[Path] | None = None,
    window_icon: QIcon | None = None,
    language: str | None = None,
    theme_manager: ThemeManager | None = None,
    icons: ThemedIcons | None = None,
    on_error: Callable[[str], None] | None = None,
) -> int
```

Builds the application, shows the window, and runs the event loop. Returns the
event loop's exit code, ready for `sys.exit`.

| Parameter | Meaning |
| --- | --- |
| `spec` | The application's identity. Supplies the `QApplication` metadata and the window title |
| `build` | Called with the `AppShell` to populate. Return a `QMainWindow` to use that instead of the shell |
| `theme` | The theme to apply. `None` uses the manager's default |
| `builtin_theme_dirs` | The application's palettes. Defaults to Gesso's |
| `user_theme_dir` | The user's overrides, which win over every built-in |
| `icons_dir` | Where the stylesheet's icon references point |
| `icon_dirs` | Extra icon directories, **appended** so they layer over Gesso's |
| `window_icon` | The window and task-switcher icon |
| `language` | Overrides the detected language; used for the layout direction |
| `theme_manager`, `icons` | Pass pre-built ones, for example in a test |
| `on_error` | Called with a formatted traceback when a slot raises |

An **RTL** language sets the application's layout direction to right-to-left,
which mirrors the whole interface without any widget knowing.

## `create_app`

```python
def create_app(spec: AppSpec, argv: Sequence[str] | None = None) -> QApplication
```

Builds — or returns the existing — `QApplication`, with the application name,
display name, version and organisation taken from the spec. Useful on its own
when an application wants to build its own loop.

## `install_exception_hook`

```python
def install_exception_hook(on_error: Callable[[str], None] | None = None) -> None
```

Logs an unhandled exception and passes the formatted traceback to `on_error`.
`KeyboardInterrupt` is delegated to the previous hook, so `Ctrl-C` behaves.

## `AppShell`

```python
class AppShell(QMainWindow):
    pageChanged = Signal(str)

    def __init__(self, spec, *, theme_manager=None, icons=None, parent=None) -> None
```

A collapsible sidebar, a content stack and a status bar. Object names:
`centralWidget`, `sidebar`, `brand`, `brandSubtitle`, `navButton`,
`contentStack`, `statusInfo` — all styled by the base stylesheet.

### Pages

| Method | Description |
| --- | --- |
| `add_page(key, title, widget, *, comment="", icon="", actions=())` | Add a destination, its navigation entry and its page; returns the `Page` |
| `show_page(key)` | Show a page and check its entry; `False` if the key is unknown |
| `pages()` | Page keys, in the order they were added |
| `page(key)` | The `Page`, or `None` |
| `current_page()` | The visible page's key |
| `header(key)` | The page's `PageHeader`, for changing it later |

Adding a page creates **both** its navigation entry and its body, so the two
cannot drift apart. The first page added is shown automatically. A duplicate
key raises `ValueError`. `pageChanged` carries the new key.

### Sidebar

| Method | Description |
| --- | --- |
| `set_sidebar_collapsed(collapsed)` | Collapse to icons, or expand again |
| `toggle_sidebar()` | Flip the state |
| `sidebar_collapsed` | Whether it is collapsed |
| `set_brand(title, subtitle="")` | Set the name above the navigation entries |

A collapsed entry keeps its label as a **tooltip**.

### Status

| Method | Description |
| --- | --- |
| `set_message(text, timeout=0)` | A transient message on the left |
| `set_info(text)` | Permanent information on the right |

Two widgets, so a transient message does not wipe the live information.

### Theme

| Method | Description |
| --- | --- |
| `apply_theme(name)` | Apply through the manager, repainting navigation icons |
| `theme_manager` | The manager, if one was given |

The shell connects to `themeChanged`, so a theme switch repaints the navigation
— the checked entry taking the accent — without the application asking.

## `Page`

```python
@dataclass
class Page:
    key: str
    title: str
    widget: QWidget
    comment: str = ""
    icon: str = ""
    actions: tuple[QWidget, ...] = ()
    container: QWidget | None = None
```

## Constants

| Name | Value |
| --- | --- |
| `SIDEBAR_WIDTH_EXPANDED` | `220` |
| `SIDEBAR_WIDTH_COLLAPSED` | `56` |
