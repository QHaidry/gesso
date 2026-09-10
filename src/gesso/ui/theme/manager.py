"""Loading, validating and applying themes.

The Qt-backed half of the design system. Everything here is a thin layer over
the token contract and the renderer: a theme is data, and applying one is
substitution plus a palette.

Keeping the palette in step with the stylesheet matters more than it looks.
Qt draws tooltips, menu shadows and other native furniture from the
:class:`QPalette`, *not* from the stylesheet, so setting only the stylesheet
leaves those pieces at the platform default — which is how a carefully themed
application ends up with a yellow tooltip.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor, QPalette

from . import qss
from .tokens import BASE_CONTRACT, TokenContract

__all__ = [
    "BUILTIN_PALETTES_DIR",
    "ICONS_DIR",
    "DEFAULT_THEME",
    "Theme",
    "ThemeManager",
]

#: Palettes shipped with the package.
BUILTIN_PALETTES_DIR = Path(__file__).parent / "palettes"

#: Icons referenced by the stylesheet (spin-box chevrons).
ICONS_DIR = Path(__file__).parent.parent / "icons"

#: Used when a caller does not name a theme.
DEFAULT_THEME = "dark"


def _read_json(path: Path) -> Dict[str, Any]:
    """Read a palette, tolerating a missing or malformed file.

    A broken theme should cost you that theme, not the application. The
    manager reports the problem through :meth:`ThemeManager.problems`; it does
    not refuse to start.
    """
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


@dataclass(frozen=True)
class Theme:
    """A resolved palette: every token the contract declares, with a value."""

    name: str
    colors: Dict[str, str]
    description: str = ""
    #: Tokens the theme's own files set, as opposed to contract defaults.
    explicit: Tuple[str, ...] = ()

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self.colors.get(key, default)

    def __getitem__(self, key: str) -> str:
        return self.colors[key]

    def __contains__(self, key: object) -> bool:
        return key in self.colors

    def as_dict(self) -> Dict[str, str]:
        return dict(self.colors)

    def is_explicit(self, key: str) -> bool:
        """Whether the theme itself sets *key*, rather than inheriting it."""
        return key in self.explicit

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"Theme({self.name!r}, {len(self.colors)} tokens)"


class ThemeManager(QObject):
    """Loads, validates and applies themes.

    Emits :attr:`themeChanged` when the applied theme changes, so themed
    widgets can re-tint themselves instead of being poked individually — the
    reason icons used to need manual refreshing on every theme switch.

    Args:
        app: The ``QApplication`` to style. Without one the manager still
            loads and validates themes; it just cannot apply them.
        builtin_dirs: Directories of ``<name>.json`` palettes. Later
            directories win, so an application can layer its own over Gesso's.
        user_dir: The user's overrides, which win over every built-in.
        contract: The token contract to resolve against.
        icons_dir: Where the stylesheet's icon references point.
    """

    themeChanged = Signal(str)

    def __init__(
        self,
        app: Any = None,
        *,
        builtin_dirs: Optional[Sequence[Path]] = None,
        user_dir: Optional[Path] = None,
        contract: Optional[TokenContract] = None,
        default: Optional[str] = None,
        icons_dir: Optional[Path] = None,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._app = app
        self._contract = contract or BASE_CONTRACT
        self._builtin_dirs = [Path(d) for d in (builtin_dirs or [BUILTIN_PALETTES_DIR])]
        self._user_dir = Path(user_dir) if user_dir is not None else None
        self._icons_dir = Path(icons_dir) if icons_dir is not None else ICONS_DIR
        self._default = default or DEFAULT_THEME
        self._current: Optional[Theme] = None

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------
    @property
    def contract(self) -> TokenContract:
        return self._contract

    @property
    def app(self) -> Any:
        return self._app

    @property
    def builtin_dirs(self) -> Tuple[Path, ...]:
        return tuple(self._builtin_dirs)

    @property
    def user_dir(self) -> Optional[Path]:
        return self._user_dir

    @property
    def current(self) -> Optional[Theme]:
        """The theme most recently applied, if any."""
        return self._current

    def search_dirs(self) -> Tuple[Path, ...]:
        """Every directory consulted, lowest priority first."""
        directories = list(self._builtin_dirs)
        if self._user_dir is not None:
            directories.append(self._user_dir)
        return tuple(directories)

    def names(self) -> List[str]:
        """Available theme names, sorted."""
        found = set()
        for directory in self.search_dirs():
            if directory.is_dir():
                found.update(path.stem for path in directory.glob("*.json"))
        return sorted(found) or [self._default]

    def exists(self, name: str) -> bool:
        return name in self.names()

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------
    def load(self, name: Optional[str] = None) -> Theme:
        """Resolve a theme: contract defaults, then each directory in order."""
        name = name or self._default
        layers: List[Mapping[str, Any]] = []
        explicit: List[str] = []
        description = ""

        for directory in self.search_dirs():
            data = _read_json(directory / f"{name}.json")
            colors = data.get("colors")
            if isinstance(colors, dict):
                layers.append(colors)
                explicit.extend(str(key) for key in colors)
            if not description and isinstance(data.get("description"), str):
                description = data["description"]

        return Theme(
            name=name,
            colors=self._contract.resolve(*layers),
            description=description,
            explicit=tuple(sorted(set(explicit))),
        )

    def problems(self, name: Optional[str] = None) -> List[str]:
        """Tokens a theme sets that the contract does not know about.

        Worth checking: a typo such as ``acccent`` is otherwise ignored, and
        the accent quietly stays at its default with nothing to explain why.
        """
        theme = self.load(name)
        unknown = self._contract.unknown(dict.fromkeys(theme.explicit, ""))
        return [f"unknown token {key!r}" for key in unknown]

    def coverage(self, name: Optional[str] = None) -> Dict[str, List[str]]:
        """Which contract tokens a theme sets, and which it inherits."""
        theme = self.load(name)
        return {
            "explicit": sorted(theme.explicit),
            "inherited": [
                key for key in self._contract.keys() if not theme.is_explicit(key)
            ],
            "unknown": self._contract.unknown(dict.fromkeys(theme.explicit, "")),
        }

    # ------------------------------------------------------------------
    # Rendering and applying
    # ------------------------------------------------------------------
    def stylesheet(self, name: Optional[str] = None) -> str:
        """The full stylesheet for a theme, ready for ``setStyleSheet``."""
        theme = self.load(name)
        return qss.render(theme.colors, {"icon_dir": str(self._icons_dir.absolute())})

    def palette(self, theme: Theme) -> QPalette:
        """A matching :class:`QPalette`.

        Native popups and platform-drawn furniture read the palette, so a
        stylesheet alone leaves tooltips and menu frames at the platform
        default.
        """
        colors = theme.colors

        def color(key: str, fallback: str) -> QColor:
            return QColor(colors.get(key, fallback))

        palette = QPalette()
        mapping = {
            QPalette.ColorRole.Window: ("window", "#1e1e1e"),
            QPalette.ColorRole.WindowText: ("text", "#d4d4d4"),
            QPalette.ColorRole.Base: ("input_bg", "#2a2a2b"),
            QPalette.ColorRole.AlternateBase: ("panel", "#252526"),
            QPalette.ColorRole.Text: ("text", "#d4d4d4"),
            QPalette.ColorRole.Button: ("btn_bg", "#333333"),
            QPalette.ColorRole.ButtonText: ("text", "#d4d4d4"),
            QPalette.ColorRole.ToolTipBase: ("tooltip_bg", "#3a3a3a"),
            QPalette.ColorRole.ToolTipText: ("tooltip_text", "#f0f0f0"),
            QPalette.ColorRole.Highlight: ("accent", "#7c6cf6"),
            QPalette.ColorRole.HighlightedText: ("accent_text", "#ffffff"),
            QPalette.ColorRole.PlaceholderText: ("text_muted", "#9a9a9a"),
        }
        for role, (key, fallback) in mapping.items():
            palette.setColor(role, color(key, fallback))
        return palette

    def apply(self, name: Optional[str] = None) -> bool:
        """Apply a theme, returning whether it worked.

        Returns ``False`` when there is no application to style or the
        stylesheet cannot be rendered. It does not raise: a theme is a
        preference, and a broken one should not stop the application opening.
        """
        if self._app is None:
            return False

        theme = self.load(name)
        try:
            sheet = self.stylesheet(theme.name)
        except qss.QssError:
            return False

        self._app.setStyleSheet(sheet)
        self._app.setPalette(self.palette(theme))

        changed = self._current is None or self._current.name != theme.name
        self._current = theme
        if changed:
            self.themeChanged.emit(theme.name)
        return True

    def __repr__(self) -> str:  # pragma: no cover - trivial
        current = self._current.name if self._current else None
        return f"ThemeManager(themes={len(self.names())}, current={current!r})"
