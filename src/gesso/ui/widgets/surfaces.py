"""Surface and layout widgets: the shapes a page is built from.

Each sets its own object name, so the stylesheet styles it. A ``Card`` is
deliberately just a ``QFrame`` with the ``card`` name — that is the whole of
what "a raised surface" means, and it lets a theme restyle every card in an
application by changing one token.
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple, Union

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

__all__ = ["Card", "PageHeader", "EmptyState"]

Margins = Union[int, Tuple[int, int, int, int]]


class Card(QFrame):
    """A raised surface. Object name: ``card``.

    Add content to :attr:`body`.
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        margins: Margins = 16,
        spacing: int = 8,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.body = QVBoxLayout(self)
        if isinstance(margins, int):
            self.body.setContentsMargins(margins, margins, margins, margins)
        else:
            self.body.setContentsMargins(*margins)
        self.body.setSpacing(spacing)


class PageHeader(QWidget):
    """A page title, an optional comment, and right-aligned actions.

    Object names: ``pageHeader`` and ``pageComment``.

    The comment sits *beside* the title rather than under it, which keeps a
    page's chrome to one line however long the description runs.
    """

    def __init__(
        self,
        title: str = "",
        comment: str = "",
        actions: Sequence[QWidget] = (),
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("pageHeader")
        row.addWidget(self.title_label)

        self.comment_label = QLabel(comment)
        self.comment_label.setObjectName("pageComment")
        self.comment_label.setVisible(bool(comment))
        row.addWidget(self.comment_label)

        row.addStretch()

        self._actions: List[QWidget] = []
        for action in actions:
            self.add_action(action)

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)

    def set_comment(self, comment: str) -> None:
        self.comment_label.setText(comment)
        self.comment_label.setVisible(bool(comment))

    def add_action(self, widget: QWidget) -> None:
        """Add a widget to the right-hand end of the header row."""
        layout = self.layout()
        layout.addWidget(widget)
        self._actions.append(widget)

    @property
    def actions(self) -> List[QWidget]:
        return list(self._actions)


class EmptyState(QLabel):
    """A muted, centred placeholder. Object name: ``emptyState``.

    For "there is nothing here yet", which is a different message from an
    error and should not be dressed as one.
    """

    def __init__(self, text: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("emptyState")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
