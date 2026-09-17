# Widgets

The other half of the design system. The theme tier defines what a `card` or a
`segGroup` *looks like*; this tier provides widgets that already call themselves
those things.

> **Every widget sets its own object name.** Styling a standard widget never
> means writing stylesheet — and the object names (`card`, `segGroup`,
> `rowLabel`, …) are public API, not an implementation detail.

```python
from gesso.ui.widgets import SegmentedControl, SettingRow

control = SegmentedControl([("nasa", "NASA"), ("bing", "Bing")], columns=2)
control.changed.connect(self._provider_chosen)
pane.addWidget(SettingRow(tr("Provider"), control, tr("Which service supplies your wallpaper.")))
```

## The set is deliberately small

These are the primitives a settings pane is built from — and each one had a
rule **already waiting for it** in `base.qss`, which is the honest test of
whether something belongs in a library rather than an application:

| Widget | Object name | For |
| --- | --- | --- |
| `Card` | `card` | A raised surface. Content goes in `.body` |
| `PageHeader` | `pageHeader`, `pageComment` | Title, comment, right-aligned actions |
| `EmptyState` | `emptyState` | "Nothing here yet" |
| `SettingRow` | `rowLabel`, `rowDesc` | Label and description left, control right |
| `IconButton` | `iconButton` | A flat, icon-only button |
| `ToggleButton` | `toggleButton` | An on/off switch |
| `SegmentedControl` | `segGroup` | Mutually exclusive buttons carrying values |

Larger composites — a settings explorer, a navigation sidebar, a thumbnail grid
— stay in the application until **two** applications need the same one. Guessing
at those here would mean designing an API for a shape nobody has built yet.

## Two things that are easy to get wrong

### Size for the appearance a control will have

A checked `ToggleButton` and a selected `SegmentedControl` member are rendered
**bold** by the stylesheet. A button sized from its regular text is truncated the
moment it is selected — and a segmented group whose buttons each resize on
selection visibly jitters as you use it.

Both widgets therefore measure the **bold** label up front:

```python
control = SegmentedControl([("a", "Short"), ("b", "A much longer label")])
# every member is the same width, sized to the longest bold label
```

`bold_width()` is public, because an application building its own control needs
the same guarantee.

### Loading settings is not a user action

```python
control.set_value("nasa")   # does NOT emit changed
control.buttons[1].click()  # emits changed("bing")
```

`set_value` blocks its own signal. Without that, populating a form from stored
settings fires the same handler a user's click does — so the application writes
back what it just read, re-runs whatever the setting triggers, and in the worst
case loops. Qt does not protect you from this, and it is the kind of bug that
looks like "the app is slow" rather than "the app is wrong".

## Icons

`IconButton` takes either a `QIcon` or an icon **name** plus a
`~gesso.ui.icons.ThemedIcons`, so its icon is tinted for the current theme and
re-tinted when the theme changes:

```python
from gesso.ui.icons import ThemedIcons

icons = ThemedIcons(theme_manager=themes)
button = IconButton("refresh", icons=icons, role="active", tooltip="Refresh")
```

Passing a name without an icon set raises rather than silently rendering a blank
button.

## Next

[:octicons-arrow-right-24: API reference: gesso.ui.widgets](../reference/widgets.md)
