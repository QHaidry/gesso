"""Tests for the widget library.

Two things matter here and neither is visual: that each widget declares the
object name its stylesheet rule expects, and that the controls which change
appearance on selection are sized for the appearance they will have.
"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QPushButton, QWidget

from gesso.ui.widgets import (
    Card,
    EmptyState,
    IconButton,
    PageHeader,
    SegmentedControl,
    SettingRow,
    ToggleButton,
    bold_width,
)


@pytest.fixture(scope="module")
def qapp():
    from PySide6.QtWidgets import QApplication

    application = QApplication.instance() or QApplication([])
    yield application
    application.setStyleSheet("")


@pytest.fixture
def themes(qapp):
    from gesso.ui.theme import ThemeManager

    manager = ThemeManager(qapp)
    manager.apply("dark")
    return manager


@pytest.fixture
def icons(themes):
    from gesso.ui.icons import ThemedIcons

    return ThemedIcons(theme_manager=themes)


def _object_names(widget: QWidget) -> set:
    """Every object name in a widget tree, including the root's."""
    names = set()
    if widget.objectName():
        names.add(widget.objectName())
    for child in widget.findChildren(QWidget):
        if child.objectName():
            names.add(child.objectName())
    return names


# ----------------------------------------------------------------------
# The object-name contract
# ----------------------------------------------------------------------


def _one_of_each(icons) -> list:
    return [
        IconButton("check", icons=icons, tooltip="Check"),
        ToggleButton("Enabled"),
        SegmentedControl([("a", "Alpha"), ("b", "Beta")]),
        Card(),
        PageHeader("Title", "Comment"),
        EmptyState("Nothing here"),
        SettingRow("Label", QPushButton("control"), "Description"),
    ]


def test_every_widget_declares_a_styled_object_name(qapp, themes, icons):
    """No widget is silently unstyled.

    A widget's object name is how the stylesheet finds it. A name with no rule
    produces no error at all — the widget simply renders as a bare platform
    control — so the two halves of the design system are checked against each
    other here rather than trusted to stay in step.
    """
    sheet = themes.stylesheet("dark")

    declared = set()
    for widget in _one_of_each(icons):
        declared |= _object_names(widget)

    assert declared, "the widgets should declare object names"
    missing = sorted(name for name in declared if f"#{name}" not in sheet)
    assert missing == [], f"these object names are not styled: {missing}"


# ----------------------------------------------------------------------
# Buttons
# ----------------------------------------------------------------------


def test_icon_button_is_flat_and_named(qapp, icons):
    button = IconButton("check", icons=icons, tooltip="Check")
    assert button.objectName() == "iconButton"
    assert button.toolTip() == "Check"
    assert not button.icon().isNull()


def test_icon_button_by_name_needs_an_icon_set(qapp):
    with pytest.raises(ValueError) as excinfo:
        IconButton("check")
    assert "icons=" in str(excinfo.value)


def test_icon_button_changes_role(qapp, icons):
    button = IconButton("check", icons=icons, role="idle")
    button.set_role("active")
    # The tint changed, so the icon was rebuilt.
    assert not button.icon().isNull()


def test_toggle_button_starts_in_the_given_state(qapp):
    assert ToggleButton("x", checked=True).isChecked() is True
    assert ToggleButton("x").isChecked() is False


def test_toggle_button_is_sized_for_its_bold_label(qapp):
    # A checked toggle renders bold; sized for the regular text it would
    # truncate the moment it was turned on.
    text = "Automatic updates"
    button = ToggleButton(text)
    assert button.width() >= bold_width(text, button.font())


def test_toggle_button_refits_when_its_text_changes(qapp):
    button = ToggleButton("short")
    narrow = button.width()
    button.setText("a considerably longer label")
    assert button.width() > narrow


def test_segmented_control_accepts_bare_values(qapp):
    control = SegmentedControl(["one", "two"])
    assert control.values() == ["one", "two"]
    assert [b.text() for b in control.buttons] == ["one", "two"]


def test_segmented_control_accepts_value_label_pairs(qapp):
    control = SegmentedControl([("nasa", "NASA"), ("bing", "Bing")])
    assert control.values() == ["nasa", "bing"]
    assert [b.text() for b in control.buttons] == ["NASA", "Bing"]


def test_segmented_control_reports_the_checked_value(qapp):
    control = SegmentedControl(["a", "b"])
    assert control.value() is None
    control.set_value("b")
    assert control.value() == "b"


def test_segmented_control_set_value_is_silent(qapp):
    # Loading stored settings must not look like a user choosing something.
    control = SegmentedControl(["a", "b"])
    seen = []
    control.changed.connect(seen.append)

    assert control.set_value("a") is True

    assert seen == []
    assert control.value() == "a"


def test_segmented_control_set_value_rejects_an_unknown_value(qapp):
    assert SegmentedControl(["a"]).set_value("nope") is False


def test_segmented_control_emits_changed_on_a_click(qapp):
    control = SegmentedControl(["a", "b"])
    seen = []
    control.changed.connect(seen.append)

    control.buttons[1].click()

    assert seen == ["b"]


def test_segmented_control_members_share_one_bold_width(qapp):
    control = SegmentedControl([("a", "Short"), ("b", "A much longer label")])
    widths = {button.width() for button in control.buttons}
    assert len(widths) == 1
    widest = max(bold_width(b.text(), b.font()) for b in control.buttons)
    assert widths.pop() >= widest


def test_segmented_control_lays_out_in_columns(qapp):
    control = SegmentedControl(["a", "b", "c", "d"], columns=2)
    grid = control.layout()
    assert grid.itemAtPosition(0, 1) is not None
    assert grid.itemAtPosition(1, 0) is not None


def test_segmented_control_can_disable_values(qapp):
    control = SegmentedControl(["a", "b"])
    control.set_enabled_values(["a"])
    assert control.buttons[0].isEnabled() is True
    assert control.buttons[1].isEnabled() is False


# ----------------------------------------------------------------------
# Surfaces
# ----------------------------------------------------------------------


def test_card_is_named_and_has_a_body(qapp):
    card = Card()
    assert card.objectName() == "card"
    assert card.body is card.layout()


def test_page_header_names_its_labels(qapp):
    header = PageHeader("Title", "Comment")
    assert header.objectName() == ""
    assert header.title_label.objectName() == "pageHeader"
    assert header.comment_label.objectName() == "pageComment"
    assert header.title_label.text() == "Title"


def test_page_header_hides_an_empty_comment(qapp):
    # isHidden, not isVisible: this widget is never shown, and a child of an
    # unshown parent reports isVisible() == False whatever it asked for.
    header = PageHeader("Title")
    assert header.comment_label.isHidden() is True
    header.set_comment("now there is one")
    assert header.comment_label.isHidden() is False


def test_page_header_takes_actions(qapp):
    action = QPushButton("Apply")
    header = PageHeader("Title", actions=[action])
    assert header.actions == [action]

    later = QPushButton("Reset")
    header.add_action(later)
    assert header.actions == [action, later]


def test_empty_state_is_centred(qapp):
    from PySide6.QtCore import Qt

    state = EmptyState("Nothing here")
    assert state.objectName() == "emptyState"
    assert state.alignment() & Qt.AlignmentFlag.AlignCenter
    assert state.wordWrap() is True


# ----------------------------------------------------------------------
# Rows
# ----------------------------------------------------------------------


def test_setting_row_names_its_labels(qapp):
    row = SettingRow("Volume", QPushButton(), "How loud")
    assert row.label.objectName() == "rowLabel"
    assert row.description.objectName() == "rowDesc"
    assert row.control is not None


def test_setting_row_hides_an_empty_description(qapp):
    row = SettingRow("Volume", QPushButton())
    assert row.description.isHidden() is True
    row.set_description("now there is one")
    assert row.description.isHidden() is False


def test_setting_row_top_aligns_so_the_description_hugs_the_label(qapp):
    from PySide6.QtCore import Qt

    row = SettingRow("Volume", QPushButton(), "How loud")
    assert row.layout().alignment() & Qt.AlignmentFlag.AlignTop
