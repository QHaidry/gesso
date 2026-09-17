# `gesso.ui.widgets`

The standard widget library. **Requires PySide6.**

```python
from gesso.ui.widgets import (
    Card, EmptyState, IconButton, PageHeader, SegmentedControl, SettingRow,
    ToggleButton, bold_width,
)
```

Every widget sets its own object name, so Gesso's stylesheet styles it without
the application writing QSS.

## `bold_width`

```python
bold_width(text: str, font: QFont) -> int
```

The pixel width of *text* rendered bold, plus comfortable padding. Public
because an application building its own control needs the same guarantee: a
control that renders bold when selected must be sized for its bold form, or it
truncates the moment it is selected.

## Buttons

### `SegmentedControl`

```python
class SegmentedControl(QWidget):
    changed = Signal(str)

    def __init__(
        self,
        options: Iterable[str | tuple[str, str]],
        parent: QWidget | None = None,
        *,
        columns: int = 0,
        tooltips: Sequence[str] | None = None,
    ) -> None
```

A grid of mutually exclusive buttons. An option is either a bare `value` (which
is also its label) or a `(value, label)` pair — which is what lets a control
show a translated name while the configuration keeps a stable key.

`columns=0` lays every member on one row. Every member is given the same width,
measured from the widest **bold** label.

| Member | Description |
| --- | --- |
| `changed` | Emitted with the chosen value when a member is **clicked** |
| `buttons` | The member buttons, in order |
| `values()` | Every value, in order |
| `value()` | The checked value, or `None` |
| `set_value(value)` | Check a value, **without** emitting `changed`; returns whether it exists |
| `set_enabled_values(values)` | Enable only these values; disable the rest |

### `ToggleButton`

```python
class ToggleButton(QPushButton):
    def __init__(self, text: str = "", checked: bool = False, parent=None) -> None
```

A checkable button styled as an on/off switch, sized for its bold label.

| Member | Description |
| --- | --- |
| `refit()` | Re-measure after the font changes |
| `setText(text)` | Set the text, and re-measure |

### `IconButton`

```python
class IconButton(QPushButton):
    def __init__(
        self,
        icon: QIcon | str | None = None,
        parent=None,
        *,
        icons: ThemedIcons | None = None,
        role: str = "idle",
        tooltip: str = "",
        size: int = 18,
    ) -> None
```

A flat, icon-only button. An icon given **by name** needs `icons`, and raises
`ValueError` without it rather than rendering a blank button.

| Member | Description |
| --- | --- |
| `set_icon(icon)` | A `QIcon`, or a name resolved through `icons` |
| `set_role(role)` | Change the theme role the icon is tinted for |

## Surfaces

### `Card`

```python
class Card(QFrame):
    def __init__(self, parent=None, *, margins: int | tuple = 16, spacing: int = 8) -> None
```

A raised surface. Add content to `body` (a `QVBoxLayout`).

### `PageHeader`

```python
class PageHeader(QWidget):
    def __init__(self, title="", comment="", actions=(), parent=None) -> None
```

A title, an optional comment beside it, and right-aligned actions. The comment
is hidden while empty.

| Member | Description |
| --- | --- |
| `title_label`, `comment_label` | The underlying labels |
| `set_title(text)`, `set_comment(text)` | Update, hiding an empty comment |
| `add_action(widget)` | Append to the header row |
| `actions` | The action widgets, in order |

### `EmptyState`

```python
class EmptyState(QLabel):
    def __init__(self, text: str = "", parent=None) -> None
```

A muted, centred, word-wrapped placeholder.

## Rows

### `SettingRow`

```python
class SettingRow(QWidget):
    def __init__(self, label: str, control: QWidget, description: str = "", parent=None) -> None
```

Label and description on the left, control on the right, both columns
top-aligned so the description hugs the label even when the control is taller.
The description is hidden while empty.

| Member | Description |
| --- | --- |
| `label`, `description`, `control` | The three parts |
| `set_label(text)`, `set_description(text)` | Update, hiding an empty description |

## Not here

Larger composites — settings explorers, navigation sidebars, thumbnail grids,
dialogs — are deliberately absent. They belong in an application until two
applications need the same one, and guessing at their API before then means
designing for a shape nobody has built.
