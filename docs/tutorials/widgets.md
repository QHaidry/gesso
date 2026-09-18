# Build a settings pane

**You will end up with** a pane built from Gesso's widgets and styled by the
base stylesheet — with no stylesheet of your own.

Qt required. About fifteen minutes.

## 1. The one rule

Every widget in the library sets its **own object name**, and the stylesheet
matches on that name. The application writes no QSS. That is the whole idea; the
rest of this tutorial is what it buys you.

The names are also deliberately **unqualified**. The stylesheet says `#card`,
not `QFrame#card`, so a `QLabel` can be a card if you want one to be.

## 2. Put widgets in a card

```python
from gesso.ui.widgets import Card, PageHeader, SegmentedControl, SettingRow, ToggleButton

header = PageHeader("Preferences", "Built from Gesso's widgets.")
self.refresh = IconButton("refresh", icons=icons, tooltip="Reset to defaults")
header.add_action(self.refresh)

general = Card(margins=20, spacing=6)
general.body.addWidget(heading("General"))
```

`PageHeader` takes a title, a comment and a list of actions — and
`add_action` puts a widget at the right-hand end of the row. The caller never
positions anything, which is why it works on a narrow window.

`Card` gives you a styled surface and a `body` layout. That is all it is.

## 3. Rows are the unit of a settings pane

```python
self.theme = SegmentedControl(["Dark", "Light"])
self.theme.set_value("Dark")
general.body.addWidget(
    SettingRow("Theme", self.theme, "A SegmentedControl as the row's control.")
)

self.notify = ToggleButton("On", checked=True)
general.body.addWidget(
    SettingRow("Notifications", self.notify, "A ToggleButton, and a description.")
)

general.body.addWidget(
    SettingRow("Download folder", QLabel("~/Pictures"), "A plain QLabel is fine.")
)
```

The third one is the important one. **Any `QWidget` can be the right-hand side
of a row** — there is no `SettingRow.with_text()`, no
`SettingRow.with_segmented_control()`. A label, a combo box, a spin box, or a
widget you wrote yourself all work, because a row is a label, an optional
description, and a control.

`SegmentedControl` takes either `"value"` or `("value", "Label")` per option,
and emits `changed` with the value:

```python
self.theme.changed.connect(self.on_theme)
```

It also has `set_value`, `values()`, `value()`, and
`set_enabled_values([...])` — for greying out the choices that do not apply
right now without rebuilding the control.

## 4. Empty is not an error

```python
advanced.body.addWidget(
    EmptyState("Nothing advanced yet — this is what goes here when there is.")
)
```

`EmptyState` is a distinct widget because "there is nothing here yet" is a
different message from "something went wrong", and it should not be dressed as
one. It is muted and centred; an error should be neither.

## 5. Check you did not invent a name

The widget library and the stylesheet agree on the object names, and you can
check that agreement from your own code:

```python
names = sorted(
    {child.objectName() for child in pane.findChildren(QWidget) if child.objectName()}
)
sheet = themes.stylesheet()
unstyled = [name for name in names if f"#{name}" not in sheet]
print(f"unstyled: {unstyled or 'none — every name has a rule'}")
```

```console
object names declared by this pane:
  #card
  #emptyState
  #iconButton
  #pageComment
  #pageHeader
  #rowDesc
  #rowLabel
  #sectionTitle
  #segGroup
  #toggleButton

unstyled: none - every name has a rule
```

Run it after every change. If you add a widget and a name appears in the first
list but not in the stylesheet, you have found a hole — either in your code or
in Gesso's — before a user finds it as "one panel looks wrong".

!!! tip "What the check is really for"

    Adding a widget that is unstyled does not raise, log or warn. It simply
    looks slightly wrong, in one theme, on one screen. This is the cheapest
    possible way to notice.

## 6. Show it

```python
app = create_app(APP, [])
themes = ThemeManager(app, parent=app)
themes.apply("dark")                      # light or dark, both are fine
icons = ThemedIcons(theme_manager=themes)

window = QMainWindow()
window.setCentralWidget(SettingsPane(icons))
window.show()
return app.exec()
```

Note the order: **apply the theme before you build the widgets.** Widgets
created first would paint with the default palette and then be repainted, which
is a visible flash on a slow machine.

## The whole tutorial

```python
--8<-- "examples/tutorials/pane.py"
```

## Check it works

```console
$ PYTHONPATH=src python examples/tutorials/pane.py
$ PYTHONPATH=src python examples/tutorials/pane.py --check    # build, print, exit
```

## Where to go next

- [Widgets](../concepts/widgets.md) — the set, and why it is deliberately small.
- [Build a windowed application](shell.md) — the same widgets, with a shell
  around them.
- [Reference: gesso.ui.widgets](../reference/widgets.md)
