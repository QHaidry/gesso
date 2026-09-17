"""Button widgets, styled by the design system.

Each widget sets its own object name, so the stylesheet styles it without the
application writing a line of QSS. That is the contract: object names are
public, and a widget's name is part of its API.

Two of these size themselves for the **bold** form of their label. The
stylesheet renders a checked button bold, and a button sized for its regular
text is truncated the moment it is selected — a bug that only appears once you
click, and only in the language with the longest word.
"""

from __future__ import annotations

from typing import Any, Iterable, List, Optional, Sequence, Tuple

from PySide6.QtCore import QSignalBlocker, QSize, Qt, Signal
from PySide6.QtGui import QFont, QFontMetrics
from PySide6.QtWidgets import (
    QButtonGroup,
    QGridLayout,
    QPushButton,
    QSizePolicy,
    QWidget,
)

__all__ = ["IconButton", "ToggleButton", "SegmentedControl", "bold_width"]

#: Room for the border, the padding and the check indicator, on top of the
#: measured text. Bold metrics drift slightly between platforms and fonts, so
#: this is deliberately generous.
_BOLD_PADDING = 40


def bold_width(text: str, font: QFont) -> int:
    """The pixel width of *text* rendered bold, plus comfortable padding.

    Public because an application building its own control still needs the
    same guarantee.
    """
    bold = QFont(font)
    bold.setBold(True)
    return QFontMetrics(bold).horizontalAdvance(text) + _BOLD_PADDING


class IconButton(QPushButton):
    """A flat, icon-only button.

    Object name: ``iconButton``.

    ``icon`` may be a :class:`QIcon` or the *name* of an icon, in which case
    pass ``icons`` — a :class:`~gesso.ui.icons.ThemedIcons` — so the icon is
    tinted for the current theme.
    """

    def __init__(
        self,
        icon: Optional[Any] = None,
        parent: Optional[QWidget] = None,
        *,
        icons: Optional[Any] = None,
        role: str = "idle",
        tooltip: str = "",
        size: int = 18,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("iconButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setIconSize(QSize(size, size))
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self._icons = icons
        self._icon_name: Optional[str] = None
        self._role = role
        self._size = size

        if tooltip:
            self.setToolTip(tooltip)
        if icon is not None:
            self.set_icon(icon)

    def set_icon(self, icon: Any) -> None:
        """Set the icon from a :class:`QIcon`, or by name through ``icons``."""
        if isinstance(icon, str):
            if self._icons is None:
                raise ValueError(
                    f"icon {icon!r} is a name; pass icons=... so it can be resolved"
                )
            self._icon_name = icon
            self.setIcon(self._icons.make_icon(icon, role=self._role, size=self._size))
        else:
            self._icon_name = None
            self.setIcon(icon)

    def set_role(self, role: str) -> None:
        """Change the theme role the icon is tinted for, and repaint it.

        Meaningful only for an icon set by name.
        """
        self._role = role
        if self._icon_name is not None:
            self.set_icon(self._icon_name)


class ToggleButton(QPushButton):
    """A checkable button styled as an on/off switch.

    Object name: ``toggleButton``.

    Sized for the bold label, so turning it on never truncates its text.
    """

    def __init__(self, text: str = "", checked: bool = False, parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.setObjectName("toggleButton")
        self.setCheckable(True)
        self.setChecked(checked)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.refit()

    def refit(self) -> None:
        """Re-measure after the text or the font changes."""
        self.setFixedWidth(bold_width(self.text(), self.font()))

    def setText(self, text: str) -> None:  # noqa: N802 - Qt naming
        super().setText(text)
        self.refit()


class SegmentedControl(QWidget):
    """A grid of mutually exclusive buttons, each carrying a value.

    Object name: ``segGroup``. Emits :attr:`changed` with the chosen value.

    A label may differ from its value, which is what lets a control show a
    translated name while the configuration keeps a stable key:

        >>> control = SegmentedControl([("nasa", "NASA"), ("bing", "Bing")])

    Every button is given the same width, measured from the widest **bold**
    label — a selected member is rendered bold, and a group of buttons that
    resized on selection would jitter as you used it.
    """

    changed = Signal(str)

    def __init__(
        self,
        options: Iterable[Any],
        parent: Optional[QWidget] = None,
        *,
        columns: int = 0,
        tooltips: Optional[Sequence[str]] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("segGroup")

        pairs = [self._as_pair(option) for option in options]
        columns = columns or len(pairs) or 1

        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(6)

        group = QButtonGroup(self)
        group.setExclusive(True)

        self._buttons: List[QPushButton] = []
        self._by_value = {}
        for index, (value, label) in enumerate(pairs):
            button = QPushButton(label)
            button.setCheckable(True)
            button.setProperty("value", value)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
            if tooltips and index < len(tooltips):
                button.setToolTip(tooltips[index])
            button.clicked.connect(lambda _checked=False, v=value: self._on_clicked(v))
            group.addButton(button)
            self._buttons.append(button)
            self._by_value[value] = button
            grid.addWidget(button, index // columns, index % columns)
            grid.setAlignment(button, Qt.AlignmentFlag.AlignHCenter)

        self._fit_widths()

    # ------------------------------------------------------------------
    @staticmethod
    def _as_pair(option: Any) -> Tuple[str, str]:
        """Accept ``"value"`` or ``("value", "Label")``."""
        if isinstance(option, (tuple, list)) and len(option) == 2:
            return str(option[0]), str(option[1])
        return str(option), str(option)

    def _fit_widths(self) -> None:
        if not self._buttons:
            return
        widest = max(bold_width(button.text(), button.font()) for button in self._buttons)
        for button in self._buttons:
            button.setFixedWidth(widest)

    def _on_clicked(self, value: str) -> None:
        self.changed.emit(value)

    # ------------------------------------------------------------------
    @property
    def buttons(self) -> List[QPushButton]:
        """The member buttons, in order."""
        return list(self._buttons)

    def values(self) -> List[str]:
        return list(self._by_value)

    def value(self) -> Optional[str]:
        """The checked value, or ``None`` when nothing is selected."""
        for value, button in self._by_value.items():
            if button.isChecked():
                return value
        return None

    def set_value(self, value: str) -> bool:
        """Check a value without emitting :attr:`changed`.

        Returns whether the value exists. A caller loading stored settings must
        not have that look like a user choosing something.
        """
        button = self._by_value.get(value)
        if button is None:
            return False
        with QSignalBlocker(button):
            button.setChecked(True)
        return True

    def set_enabled_values(self, enabled: Sequence[str]) -> None:
        """Enable only the listed values; disable the rest."""
        allowed = set(enabled)
        for value, button in self._by_value.items():
            button.setEnabled(value in allowed)
