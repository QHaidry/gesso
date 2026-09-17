"""The standard widget library.

Every widget here sets its **own object name**, so Gesso's stylesheet styles it
without the application writing a line of QSS. Those object names
(``card``, ``segGroup``, ``rowLabel``, …) are the public contract, and the
stylesheet half of it lives in :mod:`gesso.ui.theme`.

The set is deliberately small: the primitives a settings pane is built from,
each of which already had a rule waiting for it in the base stylesheet. Larger
composites belong in an application until two applications need the same one.

Requires PySide6.
"""

from .buttons import IconButton, SegmentedControl, ToggleButton, bold_width
from .rows import SettingRow
from .surfaces import Card, EmptyState, PageHeader

__all__ = [
    "IconButton",
    "ToggleButton",
    "SegmentedControl",
    "bold_width",
    "Card",
    "PageHeader",
    "EmptyState",
    "SettingRow",
]
