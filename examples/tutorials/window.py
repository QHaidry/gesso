"""Tutorial: a windowed application, in one call.

This is the whole shell. Two pages, a header button, a status line, and a theme
— and none of the sidebar, navigation, page-stack or styling code that would
usually go with them.

Run it::

    PYTHONPATH=src python examples/tutorials/window.py
    PYTHONPATH=src python examples/tutorials/window.py --theme light
    QT_QPA_PLATFORM=offscreen PYTHONPATH=src python examples/tutorials/window.py
"""

from __future__ import annotations

import sys
from typing import Any, List, Optional, Sequence

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from gesso.core import AppSpec
from gesso.ui.app import run_app
from gesso.ui.widgets import Card, EmptyState, IconButton, SettingRow, ToggleButton

APP = AppSpec(
    name="Notes",
    app_id="notes-tutorial",
    org="Tutorial",
    version="0.1.0",
    description="Two pages and a window, in one call.",
)

#: ``--check`` builds everything and closes immediately instead of entering the
#: event loop. Useful in CI, and it is how the tutorial is tested.
CHECK = "--check" in sys.argv[1:]


class HomePage(QWidget):
    """A page is an ordinary widget.

    It does not know it is a page: no base class, no registration. The shell
    wraps it in a header and gives it a navigation entry.
    """

    def __init__(
        self,
        icons: Any,
        *,
        on_change: Optional[Any] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.notes: List[str] = []
        # Kept because an IconButton given a *name* needs the icon set to
        # resolve it — `icons=...` — and the error message says exactly that.
        self.icons = icons
        # The page reports that something happened; the application decides what
        # that means. It never reaches for the shell itself.
        self.on_change = on_change

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.card = Card(margins=20, spacing=8)
        layout.addWidget(self.card)
        layout.addStretch(1)
        self.render()

    def header_actions(self) -> List[QWidget]:
        """Buttons this page wants in its header.

        Not a Gesso type and not a shell feature — just the convention this
        application uses. The shell is told `actions=page.header_actions()` and
        the page never learns where they ended up.
        """
        button = IconButton("plus", icons=self.icons, tooltip="Add a note")
        button.clicked.connect(self.add_note)
        return [button]

    def add_note(self) -> None:
        self.notes.append(f"Note {len(self.notes) + 1}")
        self.render()
        if self.on_change is not None:
            self.on_change()

    def count(self) -> int:
        return len(self.notes)

    def render(self) -> None:
        while self.card.body.count():
            item = self.card.body.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

        if not self.notes:
            self.card.body.addWidget(
                EmptyState("No notes yet. Use the + button in the header.")
            )
            return
        for note in self.notes:
            self.card.body.addWidget(SettingRow(note, QLabel("saved")))


class AboutPage(QWidget):
    """A second page, to prove the navigation is not hard-coded."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        card = Card(margins=24, spacing=8)

        title = QLabel(APP.display_name)
        title.setObjectName("displayTitle")
        card.body.addWidget(title)

        blurb = QLabel(APP.description)
        blurb.setObjectName("pageSubtitle")
        blurb.setWordWrap(True)
        card.body.addWidget(blurb)

        self.notify = ToggleButton("Notify me", checked=False)
        card.body.addWidget(SettingRow("Notifications", self.notify))

        layout.addWidget(card)
        layout.addStretch(1)


def build(shell: Any) -> None:
    """Populate the shell. Called once, after the window exists.

    ``shell`` is an ``AppShell``: it already has a sidebar, a drawer button, a
    content stack, a status bar and a theme applied. This function only says
    what goes in them.
    """

    def refresh_status() -> None:
        shell.set_info(f"{home.count()} notes")

    home = HomePage(shell.icons, on_change=refresh_status)

    shell.set_brand(APP.display_name, "two pages, one call to run_app")

    shell.add_page(
        "home",
        "Home",
        home,
        comment="Your notes live here.",
        icon="check",
        actions=home.header_actions(),
    )
    shell.add_page(
        "about",
        "About",
        AboutPage(),
        comment="What this is.",
        icon="info",
    )

    # The status bar: a short-lived message on the left, standing information on
    # the right.
    shell.set_message("Ready.")
    refresh_status()

    if CHECK:
        from PySide6.QtCore import QTimer

        QTimer.singleShot(0, shell.close)


def main(argv: Optional[Sequence[str]] = None) -> int:
    return run_app(
        APP,
        build,
        argv=argv,
        theme=None,
    )


if __name__ == "__main__":
    raise SystemExit(main())
