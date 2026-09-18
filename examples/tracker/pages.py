"""Tracker's pages.

Each is an ordinary ``QWidget``. The shell wraps it in a header, gives it a
navigation entry, and styles it — none of which the page needs to know about.
A page that wants buttons in its header says so with ``header_actions()``; the
shell puts them in the header row and the page never learns where they landed.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Callable, List, Optional

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from gesso.ui.icons import ThemedIcons
from gesso.ui.widgets import (
    Card,
    EmptyState,
    IconButton,
    SegmentedControl,
    SettingRow,
    ToggleButton,
)

from .session import Session


def clear(layout: Any) -> None:
    """Remove everything from a layout, disposing of the widgets.

    The widgets are *detached* before ``deleteLater``, not just queued for
    deletion. ``deleteLater`` hands the widget to the event loop, so until the
    loop catches up it is still a child of the page — which means
    ``findChildren`` finds ghosts of the previous render alongside the new one.
    ``setParent(None)`` makes the removal immediate and leaves ``deleteLater``
    to do nothing but free the memory.
    """
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.hide()
            widget.setParent(None)
            widget.deleteLater()


def subtitle(text: str = "") -> QLabel:
    """A muted line under a heading. ``pageSubtitle`` is Gesso's object name."""
    label = QLabel(text)
    label.setObjectName("pageSubtitle")
    label.setWordWrap(True)
    return label


def heading(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("sectionTitle")
    return label


def plural_key(prefix: str, count: int) -> str:
    """The ``.one`` or ``.other`` form of a key, as Basket's example does.

    Gesso does not guess plural rules: they are not one-versus-many in most
    languages and getting them right needs real CLDR data. The catalogs carry
    the forms and the application chooses.
    """
    return f"{prefix}.{'one' if count == 1 else 'other'}"


# ----------------------------------------------------------------------
# The page base
# ----------------------------------------------------------------------
class Page(QWidget):
    """A shell page: a widget with two optional hooks.

    ``header_actions()`` lets a page offer buttons for its header without
    knowing where the header puts them — the shell decides that, and the page
    never learns. ``retranslate()`` lets it re-say anything that came from a
    catalog, which is what makes changing language possible without a restart.

    Neither is required. They exist so that adding a page means writing a
    widget, not negotiating a protocol.
    """

    def header_actions(self) -> List[QWidget]:
        """Buttons for the header row. Default: none."""
        return []

    def retranslate(self) -> None:
        """Say everything again, in whatever language is now active."""


# ----------------------------------------------------------------------
# Today
# ----------------------------------------------------------------------
class TodayPage(Page):
    """The habits, one toggle each."""

    def __init__(
        self,
        session: Session,
        icons: ThemedIcons,
        *,
        on_change: Optional[Callable[[], None]] = None,
        today: Optional[Callable[[], date]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.session = session
        self.icons = icons
        self.on_change = on_change
        # Injected so tests can settle on a fixed day rather than depending on
        # what day the suite happens to run.
        self._today = today or date.today

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.card = Card(margins=20, spacing=8)
        layout.addWidget(self.card)
        layout.addStretch(1)

        self._rows: List[Any] = []
        self.progress = subtitle()
        self.reload()

    def header_actions(self) -> List[QWidget]:
        button = IconButton(
            "refresh", icons=self.icons, tooltip=self.session.t("tracker.today.reload")
        )
        button.clicked.connect(self.reload)
        return [button]

    def reload(self) -> None:
        """Rebuild the list from the log. Safe to call at any time."""
        clear(self.card.body)
        self._rows = []

        today = self._today()
        habits = self.session.tracker.habits

        self.progress = subtitle()
        self.card.body.addWidget(self.progress)

        if not habits:
            self.card.body.addWidget(EmptyState(self.session.t("tracker.today.empty")))
            self._refresh_progress()
            return

        for name in habits:
            toggle = ToggleButton(
                self.session.t("tracker.today.done"),
                checked=self.session.tracker.is_done(name, today),
            )
            # `clicked` carries the button's new checked state, and PySide
            # cannot introspect a `partial` to find out whether the slot wants
            # it — so the argument is named explicitly, as Gesso's own shell
            # does for its navigation buttons.
            toggle.clicked.connect(lambda checked=False, n=name: self._on_toggle(n, checked))
            row = SettingRow(name, toggle, "")
            self._rows.append((name, row))
            self.card.body.addWidget(row)

        self._refresh_progress()

    def _on_toggle(self, name: str, checked: bool) -> None:
        self.session.tracker.set_done(name, self._today(), bool(checked))
        self.session.save()
        # Deliberately *not* a full reload: rebuilding the card would delete the
        # button that is in the middle of emitting this signal.
        self._refresh_progress()
        if self.on_change is not None:
            self.on_change()

    def _refresh_progress(self) -> None:
        t = self.session.t
        today = self._today()
        tracker = self.session.tracker
        total = len(tracker.habits)

        if total == 0:
            self.progress.setText(t("tracker.today.no_habits"))
            return

        done = sum(1 for name in tracker.habits if tracker.is_done(name, today))
        target = self.session.store.get("today.target") or 1
        self.progress.setText(
            t("tracker.today.progress", done=done, total=total, target=target)
        )

        show = bool(self.session.store.get("display.show_streaks"))
        for name, row in self._rows:
            if not show:
                row.set_description("")
                continue
            days = tracker.streak(name, today=today)
            row.set_description(t(plural_key("tracker.today.streak", days), days=days))

    def retranslate(self) -> None:
        self.reload()


# ----------------------------------------------------------------------
# History
# ----------------------------------------------------------------------
class HistoryPage(Page):
    """The last few days, and what was done on them."""

    def __init__(
        self,
        session: Session,
        icons: ThemedIcons,
        *,
        today: Optional[Callable[[], date]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.session = session
        self.icons = icons
        self._today = today or date.today

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.body = QVBoxLayout()
        self.body.setSpacing(12)
        layout.addLayout(self.body)

        self.reload()

    def header_actions(self) -> List[QWidget]:
        button = IconButton(
            "refresh", icons=self.icons, tooltip=self.session.t("tracker.history.reload")
        )
        button.clicked.connect(self.reload)
        return [button]

    def reload(self) -> None:
        clear(self.body)
        t = self.session.t
        tracker = self.session.tracker

        if not tracker.habits:
            card = Card(margins=20, spacing=8)
            card.body.addWidget(EmptyState(t("tracker.history.empty")))
            self.body.addWidget(card)
            self.body.addStretch(1)
            return

        count = self.session.store.get("today.history_days") or 7
        for day in tracker.recent_days(today=self._today(), count=count):
            card = Card(margins=18, spacing=6)

            card.body.addWidget(heading(day.isoformat()))

            names = tracker.done_on(day)
            card.body.addWidget(
                subtitle(t(plural_key("tracker.history.count", len(names)), count=len(names)))
            )
            if names:
                listed = QLabel("  ·  ".join(names))
                listed.setWordWrap(True)
                card.body.addWidget(listed)

            self.body.addWidget(card)

        self.body.addStretch(1)

    def retranslate(self) -> None:
        self.reload()


# ----------------------------------------------------------------------
# Settings
# ----------------------------------------------------------------------
class SettingsPage(Page):
    """Every setting, plus the file they live in."""

    def __init__(
        self,
        session: Session,
        icons: ThemedIcons,
        *,
        theme_names: List[str],
        current_theme: Optional[str],
        on_theme_change: Callable[[str], None],
        on_language_change: Callable[[str], None],
        on_settings_change: Optional[Callable[[], None]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.session = session
        self.icons = icons
        self.theme_names = list(theme_names)
        self.on_theme_change = on_theme_change
        self.on_language_change = on_language_change
        self.on_settings_change = on_settings_change

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.card = Card(margins=20, spacing=6)
        layout.addWidget(self.card)
        layout.addStretch(1)

        self._current_theme = current_theme
        self._build()

    def _build(self) -> None:
        """(Re)build every row. Called again when the language changes."""
        clear(self.card.body)
        t = self.session.t
        store = self.session.store

        language = SegmentedControl(
            [
                ("auto", t("tracker.settings.language_auto")),
                ("en", "English"),
                ("fr", "Fran\u00e7ais"),
            ]
        )
        language.set_value(store.get("display.language") or "auto")
        language.changed.connect(self._on_language)
        self.card.body.addWidget(
            SettingRow(
                t("tracker.settings.language"),
                language,
                t("tracker.settings.language_help"),
            )
        )

        theme = SegmentedControl([(name, name.title()) for name in self.theme_names])
        if self._current_theme:
            theme.set_value(self._current_theme)
        theme.changed.connect(self._on_theme)
        self.card.body.addWidget(
            SettingRow(t("tracker.settings.theme"), theme, t("tracker.settings.theme_help"))
        )

        streaks = ToggleButton(
            t("tracker.settings.enabled"), checked=bool(store.get("display.show_streaks"))
        )
        streaks.clicked.connect(self._on_streaks)
        self.card.body.addWidget(
            SettingRow(
                t("tracker.settings.streaks"), streaks, t("tracker.settings.streaks_help")
            )
        )

        target = SegmentedControl([(str(size), str(size)) for size in (1, 3, 5, 10)])
        target.set_value(str(store.get("today.target") or 3))
        target.changed.connect(self._on_target)
        self.card.body.addWidget(
            SettingRow(t("tracker.settings.target"), target, t("tracker.settings.target_help"))
        )
        # A read-only row: where the settings actually are. Driving it from
        # `store.path` rather than a string means it cannot go stale.
        self.card.body.addWidget(
            SettingRow(t("tracker.settings.file"), QLabel(store.format), str(store.path))
        )

    def _on_language(self, code: str) -> None:
        self.on_language_change(code)

    def _on_theme(self, name: str) -> None:
        self._current_theme = name
        self.on_theme_change(name)

    def _on_streaks(self, checked: bool) -> None:
        self.session.remember("display.show_streaks", bool(checked))
        self._notify()

    def _on_target(self, value: str) -> None:
        self.session.remember("today.target", value)
        self._notify()

    def _notify(self) -> None:
        if self.on_settings_change is not None:
            self.on_settings_change()

    def retranslate(self) -> None:
        self._build()


# ----------------------------------------------------------------------
# About
# ----------------------------------------------------------------------
class AboutPage(Page):
    """What it is, and what it was built from."""

    def __init__(self, session: Session, icons: ThemedIcons, *, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.session = session
        self.icons = icons

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.card = Card(margins=24, spacing=8)
        layout.addWidget(self.card)
        layout.addStretch(1)

        self.reload()

    def reload(self) -> None:
        clear(self.card.body)
        t = self.session.t
        from gesso import __version__ as gesso_version

        from .spec import APP

        title = QLabel(APP.display_name)
        title.setObjectName("displayTitle")
        self.card.body.addWidget(title)

        self.card.body.addWidget(subtitle(t("tracker.about.blurb")))
        self.card.body.addWidget(heading(t("tracker.about.version", version=APP.version)))
        self.card.body.addWidget(subtitle(t("tracker.about.built_with", version=gesso_version)))
        self.card.body.addWidget(
            subtitle(t("tracker.about.settings", path=self.session.store.path))
        )
        self.card.body.addWidget(subtitle(t("tracker.about.data", path=self.session.data_path)))

    def retranslate(self) -> None:
        self.reload()
