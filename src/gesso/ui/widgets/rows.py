"""The row shape every settings pane is built from.

A settings page is a list of these: a label and a description on the left, the
control on the right.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

__all__ = ["SettingRow"]


class SettingRow(QWidget):
    """One setting: label and description left, control right.

    Object names: ``rowLabel`` and ``rowDesc``.

    Both columns are **top-aligned**, so the description sits directly under the
    setting's name even when the control is much taller than one line — a grid
    of buttons, say, which would otherwise centre the label against it and make
    the row read as belonging to the wrong thing.
    """

    def __init__(
        self,
        label: str,
        control: QWidget,
        description: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 8, 0, 8)
        row.setSpacing(16)
        row.setAlignment(Qt.AlignmentFlag.AlignTop)

        left = QVBoxLayout()
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(0)
        left.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.label = QLabel(label)
        self.label.setObjectName("rowLabel")
        left.addWidget(self.label)

        self.description = QLabel(description)
        self.description.setObjectName("rowDesc")
        self.description.setWordWrap(True)
        self.description.setVisible(bool(description))
        left.addWidget(self.description)

        row.addLayout(left, 1)

        self.control = control
        row.addWidget(control, 0, Qt.AlignmentFlag.AlignTop)

    def set_label(self, text: str) -> None:
        self.label.setText(text)

    def set_description(self, text: str) -> None:
        self.description.setText(text)
        self.description.setVisible(bool(text))
