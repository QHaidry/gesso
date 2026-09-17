"""The application window: a sidebar, a content stack and a status bar.

Almost every desktop application is the same window. A list of destinations
down one side, a page for each, and a strip of live information along the
bottom — and almost every application implements it slightly differently, and
gets the collapsible-sidebar details slightly wrong.

The shell sets only object names the base stylesheet already styles, so it
looks right with no QSS of its own, and it composes
:class:`~gesso.ui.widgets.PageHeader` for each page rather than reimplementing
a header row.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from gesso.core.app import AppSpec
from gesso.ui.widgets import IconButton, PageHeader

__all__ = ["AppShell", "Page", "SIDEBAR_WIDTH_EXPANDED", "SIDEBAR_WIDTH_COLLAPSED"]

#: Sidebar widths when expanded and collapsed.
SIDEBAR_WIDTH_EXPANDED = 220
SIDEBAR_WIDTH_COLLAPSED = 56

#: The icon size used for navigation entries.
_NAV_ICON_SIZE = 18


@dataclass
class Page:
    """One destination in the shell."""

    key: str
    title: str
    widget: QWidget
    comment: str = ""
    icon: str = ""
    actions: Tuple[QWidget, ...] = field(default_factory=tuple)
    container: Optional[QWidget] = None


class AppShell(QMainWindow):
    """A sidebar, a content stack and a status bar.

    Object names: ``centralWidget``, ``sidebar``, ``brand``, ``brandSubtitle``,
    ``navButton``, ``contentStack`` and ``statusInfo`` — all styled by the base
    stylesheet.

    Emits :attr:`pageChanged` with the new page's key.
    """

    pageChanged = Signal(str)

    def __init__(
        self,
        spec: AppSpec,
        *,
        theme_manager: Any = None,
        icons: Any = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.spec = spec
        self.theme_manager = theme_manager
        self.icons = icons

        self.setWindowTitle(spec.display_name)

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._pages: "OrderedDict[str, Page]" = OrderedDict()
        self._nav_buttons: Dict[str, QPushButton] = {}
        self._collapsed = False

        self._build_sidebar(root)

        self.stack = QStackedWidget()
        self.stack.setObjectName("contentStack")
        root.addWidget(self.stack, 1)

        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)

        self._build_status_bar()

        if theme_manager is not None and hasattr(theme_manager, "themeChanged"):
            theme_manager.themeChanged.connect(self._on_theme_changed)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def _build_sidebar(self, root: QHBoxLayout) -> None:
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(SIDEBAR_WIDTH_EXPANDED)

        side = QVBoxLayout(self.sidebar)
        side.setContentsMargins(12, 14, 12, 12)
        side.setSpacing(4)

        top = QHBoxLayout()
        top.setSpacing(8)

        self.drawer_button = IconButton(
            "chevron-left" if self.icons is not None else None,
            icons=self.icons,
            tooltip="Toggle navigation",
            size=20,
        )
        self.drawer_button.clicked.connect(self.toggle_sidebar)
        top.addWidget(self.drawer_button)

        self.brand_label = QLabel(self.spec.display_name)
        self.brand_label.setObjectName("brand")
        top.addWidget(self.brand_label)
        top.addStretch()

        side.addLayout(top)

        self.brand_subtitle = QLabel("")
        self.brand_subtitle.setObjectName("brandSubtitle")
        self.brand_subtitle.setWordWrap(True)
        self.brand_subtitle.setVisible(False)
        side.addWidget(self.brand_subtitle)

        side.addSpacing(12)

        # Navigation entries live in their own container so the stretch below
        # stays last however many pages are added.
        self.nav_container = QWidget()
        self._nav_layout = QVBoxLayout(self.nav_container)
        self._nav_layout.setContentsMargins(0, 0, 0, 0)
        self._nav_layout.setSpacing(4)
        side.addWidget(self.nav_container)
        side.addStretch()

        root.addWidget(self.sidebar)

    def _build_status_bar(self) -> None:
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # A permanent widget rather than a transient message, so live
        # information is not wiped by the next showMessage().
        self.status_info = QLabel("")
        self.status_info.setObjectName("statusInfo")
        self.status_bar.addPermanentWidget(self.status_info)

    # ------------------------------------------------------------------
    # Pages
    # ------------------------------------------------------------------
    def add_page(
        self,
        key: str,
        title: str,
        widget: QWidget,
        *,
        comment: str = "",
        icon: str = "",
        actions: Sequence[QWidget] = (),
    ) -> Page:
        """Add a destination, its navigation entry and its page.

        Returns the :class:`Page`, so a caller can keep a reference to the
        widget it passed in.
        """
        if key in self._pages:
            raise ValueError(f"a page named {key!r} already exists")

        page = Page(
            key=key,
            title=title,
            widget=widget,
            comment=comment,
            icon=icon,
            actions=tuple(actions),
        )
        page.container = self._wrap(page)
        self._pages[key] = page
        self.stack.addWidget(page.container)

        button = self._make_nav_button(page)
        self._nav_layout.addWidget(button)
        self._nav_buttons[key] = button
        self._nav_group.addButton(button)

        if len(self._pages) == 1:
            self.show_page(key)
        return page

    def _wrap(self, page: Page) -> QWidget:
        """A page body: a header row above the content."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        self._headers = getattr(self, "_headers", {})
        header = PageHeader(page.title, page.comment, page.actions)
        self._headers[page.key] = header
        layout.addWidget(header)
        layout.addWidget(page.widget, 1)
        return container

    def _make_nav_button(self, page: Page) -> QPushButton:
        button = QPushButton(page.title)
        button.setObjectName("navButton")
        button.setCheckable(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        if page.icon and self.icons is not None:
            button.setIcon(self.icons.make_icon(page.icon, role="idle", size=_NAV_ICON_SIZE))
        button.toggled.connect(self._refresh_nav_icons)
        button.clicked.connect(lambda _checked=False, k=page.key: self.show_page(k))
        return button

    def pages(self) -> List[str]:
        """Page keys, in the order they were added."""
        return list(self._pages)

    def page(self, key: str) -> Optional[Page]:
        return self._pages.get(key)

    def current_page(self) -> Optional[str]:
        """The visible page's key."""
        current = self.stack.currentWidget()
        for key, page in self._pages.items():
            if page.container is current:
                return key
        return None

    def show_page(self, key: str) -> bool:
        """Show a page and check its navigation entry."""
        page = self._pages.get(key)
        if page is None:
            return False
        self.stack.setCurrentWidget(page.container)
        button = self._nav_buttons[key]
        if not button.isChecked():
            button.setChecked(True)
        self.pageChanged.emit(key)
        return True

    def header(self, key: str) -> Optional[PageHeader]:
        """The header of a page, for changing its title or actions later."""
        header = getattr(self, "_headers", {}).get(key)
        return header

    # ------------------------------------------------------------------
    # Sidebar
    # ------------------------------------------------------------------
    def toggle_sidebar(self) -> None:
        self.set_sidebar_collapsed(not self._collapsed)

    def set_sidebar_collapsed(self, collapsed: bool) -> None:
        """Collapse the sidebar to icons, or expand it again.

        Collapsed entries keep their label as a tooltip: icon-only navigation
        with no labels and no tooltips is a memory test, not an interface.
        """
        self._collapsed = collapsed
        self.sidebar.setFixedWidth(
            SIDEBAR_WIDTH_COLLAPSED if collapsed else SIDEBAR_WIDTH_EXPANDED
        )

        for key, button in self._nav_buttons.items():
            label = self._pages[key].title
            button.setText("" if collapsed else label)
            button.setToolTip(label if collapsed else "")
            # The stylesheet keys the collapsed layout off this property, so
            # the button has to be repolished for the change to take effect.
            button.setProperty("collapsed", collapsed)
            button.style().unpolish(button)
            button.style().polish(button)

        self.brand_label.setVisible(not collapsed)
        self.brand_subtitle.setVisible(not collapsed and bool(self.brand_subtitle.text()))

    @property
    def sidebar_collapsed(self) -> bool:
        return self._collapsed

    def set_brand(self, title: str, subtitle: str = "") -> None:
        """Set the name shown above the navigation entries."""
        self.brand_label.setText(title)
        self.brand_subtitle.setText(subtitle)
        self.brand_subtitle.setVisible(bool(subtitle) and not self._collapsed)

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------
    def set_message(self, text: str, timeout: int = 0) -> None:
        """Show a transient message on the left of the status bar."""
        self.status_bar.showMessage(text, timeout)

    def set_info(self, text: str) -> None:
        """Set the permanent information on the right of the status bar."""
        self.status_info.setText(text)

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------
    def apply_theme(self, name: str) -> bool:
        """Apply a theme through the manager, if there is one."""
        if self.theme_manager is None:
            return False
        applied = self.theme_manager.apply(name)
        if applied:
            self._refresh_nav_icons()
        return applied

    def _on_theme_changed(self, _name: str) -> None:
        self._refresh_nav_icons()

    def _refresh_nav_icons(self) -> None:
        """Re-tint navigation icons; the checked entry takes the accent.

        Driven by the theme manager's signal, so a theme switch repaints the
        navigation without the application remembering to ask.
        """
        if self.icons is None:
            return
        for key, button in self._nav_buttons.items():
            name = self._pages[key].icon
            if not name:
                continue
            role = "active" if button.isChecked() else "idle"
            button.setIcon(self.icons.make_icon(name, role=role, size=_NAV_ICON_SIZE))

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"AppShell(pages={self.pages()}, collapsed={self._collapsed})"
