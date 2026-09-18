"""The Gallery window — assembled by hand.

Rung four replaces this entire file with a call to ``run_app`` and a few
``add_page`` calls. Everything here is still available there; the shell just
does the assembling.

Two things are worth watching for:

1. **No widget sets its own style.** Every one of them declares an object name
   (``card``, ``rowLabel``, ``segGroup``, …) and the base stylesheet matches on
   it. That is why switching the palette below repaints everything, including
   widgets that were built before the switch.
2. **Icons do not repaint themselves.** A ``QLabel`` holds a *pixmap*, and a
   pixmap does not know the theme moved. ``ThemedIcons.iconsChanged`` says
   *when*; the application decides *what* to rebuild.
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from gesso.config import ConfigError
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

#: The roles an icon can be rendered in. Each maps to a token, not a colour —
#: which is why an icon stays correct across every theme.
ROLES = ("idle", "strong", "active", "disabled", "on-accent")

#: A sample of the icons Gesso ships.
SHOWCASE_ICONS = (
    "check",
    "close",
    "plus",
    "minus",
    "refresh",
    "search",
    "warning",
    "info",
    "chevron-down",
    "chevron-right",
)

#: Icon sizes offered in the rows card.
SIZES = {"Small": 16, "Medium": 20, "Large": 28}


def section_title(text: str) -> QLabel:
    """A heading inside a card.

    ``sectionTitle`` is part of the object-name contract, so this label is
    styled by the same rule the application shell's page headers use.
    """
    label = QLabel(text)
    label.setObjectName("sectionTitle")
    return label


class GalleryWindow(QMainWindow):
    """A window that shows what the design system gives you."""

    def __init__(
        self,
        spec: Any,
        *,
        manager: ThemeManager,
        icons: ThemedIcons,
        store: Optional[Any] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.spec = spec
        self.manager = manager
        self.icons = icons
        self.store = store

        self.icon_size = 20
        if store is not None:
            self.icon_size = store.get("display.icon_size") or 20

        # (button, role) — the role is kept because `iconsChanged` re-renders
        # by role, and the button does not remember which one it was built for.
        self._role_buttons: List[Tuple[IconButton, str]] = []
        self._icon_cells: List[Tuple[str, str, QLabel]] = []

        self.setWindowTitle(spec.display_name)
        self.resize(1020, 800)

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        root.addWidget(self._build_header())
        root.addWidget(self._build_theme_row())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        page = QWidget()
        self.cards = QVBoxLayout(page)
        self.cards.setContentsMargins(0, 0, 0, 0)
        self.cards.setSpacing(16)
        scroll.setWidget(page)
        root.addWidget(scroll, 1)

        self.cards.addWidget(self._buttons_card())
        self.cards.addWidget(self._rows_card())
        self.cards.addWidget(self._empty_card())
        self.cards.addWidget(self._icons_card())
        if store is None or store.get("display.show_tokens"):
            self.cards.addWidget(self._tokens_card())
        self.cards.addStretch(0)

        # Gesso says *when* the icons are stale; the application decides what
        # to do about it.
        self.icons.iconsChanged.connect(self._refresh_icons)

    # ------------------------------------------------------------------
    # Header and palette
    # ------------------------------------------------------------------
    def _build_header(self) -> PageHeader:
        header = PageHeader(
            self.spec.display_name,
            "Every widget below is styled by the base stylesheet alone — no "
            "object names were invented here, and no QSS was written.",
        )
        self.reapply_button = IconButton(
            "refresh",
            icons=self.icons,
            tooltip="Re-apply the current palette",
        )
        self.reapply_button.clicked.connect(self._reapply)
        header.add_action(self.reapply_button)
        return header

    def _build_theme_row(self) -> SettingRow:
        names = self.manager.names()
        self.theme_control = SegmentedControl([(name, name.title()) for name in names])

        if self.manager.current is None:
            # Nothing has been applied yet, so the window would be painting the
            # contract's last-resort defaults rather than a palette. Apply one,
            # so the control below tells the truth about what is on screen.
            self.manager.apply(None)
        if self.manager.current is not None:
            self.theme_control.set_value(self.manager.current.name)

        self.theme_control.changed.connect(self.apply_theme)
        return SettingRow(
            "Palette",
            self.theme_control,
            "Applied live: the stylesheet, the QPalette behind native widgets, "
            "and every icon.",
        )

    def apply_theme(self, name: str) -> bool:
        """Apply *name*, remember it, and repaint what a theme change stales.

        Returns whether *name* is the palette now in force — which is not the
        same question as whether `apply` succeeded. A palette with no file
        installed falls back to the default rather than failing, so an unknown
        name still returns ``True`` from the manager and lands you on a real
        theme. That is the right behaviour (a deleted theme file should not
        leave the window neutral) but only the caller can tell the difference,
        which is why this method answers it.
        """
        self.manager.apply(name)
        self._render_tokens()

        applied = self.manager.current.name if self.manager.current else None
        # Keep the control honest. It may have been a programmatic change, or a
        # fallback; a control that disagrees with the window is worse than none.
        if applied is not None:
            self.theme_control.set_value(applied)

        if self.store is not None and applied is not None:
            try:
                self.store.set("display.theme", applied)
                self.store.save()
            except ConfigError:
                # A settings file we cannot write is not worth crashing over.
                pass
        return applied == name

    def _reapply(self) -> None:
        current = self.manager.current
        self.manager.apply(current.name if current is not None else None)
        self._render_tokens()

    # ------------------------------------------------------------------
    # The widget cards
    # ------------------------------------------------------------------
    def _buttons_card(self) -> Card:
        card = Card(margins=20, spacing=14)
        card.body.addWidget(section_title("Buttons"))

        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(QLabel("one per role:"))
        for role in ROLES:
            button = IconButton("check", icons=self.icons, role=role, tooltip=f"role={role}")
            self._role_buttons.append((button, role))
            row.addWidget(button)
        row.addStretch(1)
        card.body.addLayout(row)

        row = QHBoxLayout()
        row.setSpacing(12)
        row.addWidget(ToggleButton("Toggle me", checked=True))
        row.addWidget(ToggleButton("And me"))
        row.addStretch(1)
        card.body.addLayout(row)

        row = QHBoxLayout()
        row.setSpacing(12)
        segments = SegmentedControl(["All", "Pinned", "Recent"])
        segments.set_value("All")
        row.addWidget(segments)
        row.addStretch(1)
        card.body.addLayout(row)

        return card

    def _rows_card(self) -> Card:
        card = Card(margins=20, spacing=6)
        card.body.addWidget(section_title("Rows"))

        self.compact_toggle = ToggleButton("Compact", checked=False)
        card.body.addWidget(
            SettingRow(
                "Compact spacing",
                self.compact_toggle,
                "A ToggleButton as the control, and a description under the label.",
            )
        )

        self.size_control = SegmentedControl(list(SIZES))
        self.size_control.set_value(
            next((label for label, size in SIZES.items() if size == self.icon_size), "Medium")
        )
        self.size_control.changed.connect(self._on_icon_size)
        card.body.addWidget(
            SettingRow("Icon size", self.size_control, "Changes the showcase below.")
        )

        card.body.addWidget(
            SettingRow(
                "Status",
                QLabel("A plain widget works as a control too."),
                "Any QWidget can be the right-hand side of a row.",
            )
        )
        return card

    def _empty_card(self) -> Card:
        card = Card(margins=20, spacing=12)
        card.body.addWidget(section_title("Empty state"))
        card.body.addWidget(
            EmptyState(
                "Nothing here yet — this is what you show instead of an empty list."
            )
        )
        return card

    def _icons_card(self) -> Card:
        card = Card(margins=20, spacing=14)
        card.body.addWidget(section_title("Icons"))

        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(10)

        grid.addWidget(QLabel("name"), 0, 0)
        for column, role in enumerate(ROLES, start=1):
            head = QLabel(role)
            head.setObjectName("rowDesc")
            head.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(head, 0, column)

        for row, name in enumerate(SHOWCASE_ICONS, start=1):
            label = QLabel(name)
            label.setObjectName("rowLabel")
            grid.addWidget(label, row, 0)
            for column, role in enumerate(ROLES, start=1):
                cell = QLabel()
                cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
                grid.addWidget(cell, row, column)
                self._icon_cells.append((name, role, cell))

        card.body.addLayout(grid)
        self._render_icons()
        return card

    def _tokens_card(self) -> Card:
        card = Card(margins=20, spacing=14)
        card.body.addWidget(section_title("Token contract"))
        card.body.addWidget(
            QLabel(
                "A palette supplies values for these. Anything it leaves out "
                "falls back to the contract's default, which is why a palette "
                "can be partial."
            )
        )
        self._token_grid = QGridLayout()
        self._token_grid.setHorizontalSpacing(16)
        self._token_grid.setVerticalSpacing(4)
        self._token_grid.setColumnStretch(2, 1)
        card.body.addLayout(self._token_grid)
        self._render_tokens()
        return card

    # ------------------------------------------------------------------
    # Re-rendering
    # ------------------------------------------------------------------
    def _render_icons(self) -> None:
        for name, role, cell in self._icon_cells:
            cell.setPixmap(self.icons.render_pixmap(name, role=role, size=self.icon_size))

    def _refresh_icons(self) -> None:
        """Repaint everything holding an icon, after the theme moved."""
        self._render_icons()
        for button, role in self._role_buttons:
            button.set_role(role)
        self.reapply_button.set_role("idle")

    def _render_tokens(self) -> None:
        """Rebuild the token inspector from whichever theme is current."""
        grid = getattr(self, "_token_grid", None)
        if grid is None:
            return

        while grid.count():
            item = grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        theme = self.manager.current
        row = 0
        for group, tokens in self.manager.contract.groups().items():
            head = QLabel(group)
            head.setObjectName("sectionTitle")
            grid.addWidget(head, row, 0, 1, 3)
            row += 1

            for token in tokens:
                value = theme.get(token.key) if theme is not None else None

                swatch = QLabel()
                swatch.setFixedSize(30, 16)
                # The one place an inline stylesheet is right: this colour is
                # *data* read out of the palette, not a style rule. There is no
                # object name that could express "whatever this token is".
                swatch.setStyleSheet(
                    f"background-color: {value or token.default}; border-radius: 3px;"
                )
                grid.addWidget(swatch, row, 0)

                name = QLabel(token.key)
                grid.addWidget(name, row, 1)

                resolved = QLabel(value or f"{token.default}  (contract default)")
                resolved.setObjectName("rowDesc")
                grid.addWidget(resolved, row, 2)
                row += 1

    # ------------------------------------------------------------------
    # Rows
    # ------------------------------------------------------------------
    def _on_icon_size(self, label: str) -> None:
        self.icon_size = SIZES.get(label, 20)
        self._render_icons()
