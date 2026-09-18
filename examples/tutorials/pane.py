"""Tutorial: build a settings pane from the widget library.

Every widget used here sets its **own object name**, and the base stylesheet
matches on that name. This file contains no QSS at all — which is the point.

Run it::

    PYTHONPATH=src python examples/tutorials/pane.py
    QT_QPA_PLATFORM=offscreen PYTHONPATH=src python examples/tutorials/pane.py
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

from gesso.core import AppSpec
from gesso.ui.app import create_app
from gesso.ui.icons import ThemedIcons
from gesso.ui.theme import ThemeManager
from gesso.ui.widgets import (
    Card,
    EmptyState,
    IconButton,
    PageHeader,
    SegmentedControl,
    SettingRow,
    ToggleButton,
)

APP = AppSpec(
    name="Pane",
    app_id="pane-tutorial",
    org="Tutorial",
    version="0.1.0",
    description="A settings pane built from the widget library.",
)

#: ``--check`` builds everything and closes immediately instead of entering the
#: event loop. Useful in CI, and it is how the tutorial is tested.
CHECK = "--check" in sys.argv[1:]


def heading(text: str) -> QLabel:
    """A heading inside a card. ``sectionTitle`` is a *shared* name.

    Gesso's own application shell uses it for page headers, which is why this
    label needs no styling of its own: the rule already exists.
    """
    label = QLabel(text)
    label.setObjectName("sectionTitle")
    return label


class SettingsPane(QWidget):
    """A settings pane, from primitives."""

    def __init__(self, icons: ThemedIcons, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # A header, with a button the pane itself never positions.
        header = PageHeader(
            "Preferences",
            "Built from Gesso's widgets, with no stylesheet of its own.",
        )
        self.refresh = IconButton("refresh", icons=icons, tooltip="Reset to defaults")
        header.add_action(self.refresh)
        layout.addWidget(header)

        # ------------------------------------------------------------------
        # A card of rows
        # ------------------------------------------------------------------
        general = Card(margins=20, spacing=6)
        general.body.addWidget(heading("General"))

        self.theme = SegmentedControl(["Dark", "Light"])
        self.theme.set_value("Dark")
        general.body.addWidget(
            SettingRow("Theme", self.theme, "A SegmentedControl as the row's control.")
        )

        self.notify = ToggleButton("On", checked=True)
        general.body.addWidget(
            SettingRow("Notifications", self.notify, "A ToggleButton, and a description.")
        )

        # Any widget can be the control. There is no `SettingRow.with_text()`.
        general.body.addWidget(
            SettingRow("Download folder", QLabel("~/Pictures"), "A plain QLabel is fine.")
        )
        layout.addWidget(general)

        # ------------------------------------------------------------------
        # And an empty state, which is not an error state
        # ------------------------------------------------------------------
        advanced = Card(margins=20, spacing=6)
        advanced.body.addWidget(heading("Advanced"))
        advanced.body.addWidget(
            EmptyState("Nothing advanced yet — this is what goes here when there is.")
        )
        layout.addWidget(advanced)

        layout.addStretch(1)


def main() -> int:
    app = create_app(APP, [])

    themes = ThemeManager(app, parent=app)
    themes.apply("dark")
    icons = ThemedIcons(theme_manager=themes)

    pane = SettingsPane(icons)
    window = QMainWindow()
    window.setWindowTitle(APP.display_name)
    window.setCentralWidget(pane)
    window.resize(760, 620)
    window.show()

    # ------------------------------------------------------------------
    # What the pane actually declared
    # ------------------------------------------------------------------
    # These names are the public contract between the widget library and the
    # stylesheet. Printing them is the quickest way to notice that a widget you
    # added is unstyled: it will not appear here.
    names = sorted(
        {child.objectName() for child in pane.findChildren(QWidget) if child.objectName()}
    )
    print("object names declared by this pane:")
    for name in names:
        print(f"  #{name}")

    sheet = themes.stylesheet()
    unstyled = [name for name in names if f"#{name}" not in sheet]
    print(f"\nunstyled: {unstyled or 'none - every name has a rule'}")

    if CHECK:
        from PySide6.QtCore import QTimer

        QTimer.singleShot(0, window.close)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
