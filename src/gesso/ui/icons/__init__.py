"""SVG icons, rendered and tinted at runtime.

One asset serves every theme. An icon is rendered into a pixmap and tinted to
whatever colour the caller asks for, so adding a theme never means adding a
second copy of the artwork — which is exactly what a set of fixed-colour icons
makes you do.

Tinting works by composition rather than by editing SVG source: the artwork is
drawn, then ``CompositionMode_SourceIn`` replaces its colour while keeping its
alpha. The stroke colour in the shipped SVGs is therefore irrelevant, and an
icon renders correctly at any size without a second asset.

:class:`IconRegistry` exists so an application can add its own icons without
forking Gesso's: directories are searched in order, and later ones win.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from PySide6.QtCore import QObject, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

__all__ = [
    "ICONS_DIR",
    "DEFAULT_SIZE",
    "DEFAULT_TINT",
    "ROLE_TOKENS",
    "IconError",
    "IconRegistry",
    "ThemedIcons",
]

#: The icons shipped with the package.
ICONS_DIR = Path(__file__).parent

#: A sensible default for toolbar- and menu-sized icons.
DEFAULT_SIZE = 18

#: Used when nothing better can be determined. Matches the contract's
#: ``text_muted``, so an untinted icon does not look out of place.
DEFAULT_TINT = "#9a9a9a"

#: Icon roles, mapped to the design token each takes its colour from.
#:
#: Named by *purpose* rather than by colour, so a theme decides what "active"
#: looks like and nothing else has to change.
ROLE_TOKENS: Dict[str, str] = {
    "idle": "text_muted",
    "strong": "text",
    "active": "accent",
    "disabled": "text_disabled",
    "on-accent": "accent_text",
}


class IconError(Exception):
    """Raised when an icon cannot be found or rendered."""


class IconRegistry:
    """A search path of directories containing ``<name>.svg`` files.

    Later directories win, so an application layers its own icons over
    Gesso's simply by adding a directory.
    """

    def __init__(self, directories: Optional[Sequence[Path]] = None) -> None:
        if directories is None:
            directories = [ICONS_DIR]
        self._directories: Tuple[Path, ...] = tuple(Path(d) for d in directories)

    @property
    def directories(self) -> Tuple[Path, ...]:
        return self._directories

    def add_directory(self, directory: Path) -> None:
        """Append a directory, giving it the highest priority."""
        self._directories = self._directories + (Path(directory),)

    def names(self) -> List[str]:
        """Every icon available, sorted."""
        found = set()
        for directory in self._directories:
            if directory.is_dir():
                found.update(path.stem for path in directory.glob("*.svg"))
        return sorted(found)

    def path(self, name: str) -> Optional[Path]:
        """The file an icon resolves to, or ``None``."""
        for directory in reversed(self._directories):
            candidate = directory / f"{name}.svg"
            if candidate.is_file():
                return candidate
        return None

    def has(self, name: str) -> bool:
        return self.path(name) is not None

    def source(self, name: str) -> str:
        """The SVG source for an icon.

        Raises :class:`IconError` naming the alternatives, because "no icon
        called 'refrsh'" is a typo you want to see immediately.
        """
        found = self.path(name)
        if found is None:
            known = ", ".join(self.names()) or "none"
            raise IconError(f"no icon named {name!r}; available icons: {known}")
        try:
            return found.read_text(encoding="utf-8")
        except OSError as exc:
            raise IconError(f"cannot read icon {name!r}: {exc}") from exc

    def render_pixmap(
        self, name: str, size: int = DEFAULT_SIZE, tint: Optional[str] = None
    ) -> QPixmap:
        """Render an icon at *size*, tinted with *tint* (or its own colours)."""
        found = self.path(name)
        if found is None:
            known = ", ".join(self.names()) or "none"
            raise IconError(f"no icon named {name!r}; available icons: {known}")

        renderer = QSvgRenderer(str(found))
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        try:
            renderer.render(painter, QRectF(0, 0, size, size))
            if tint is not None:
                # Keep the artwork's alpha, replace its colour: one asset then
                # serves every theme.
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
                painter.fillRect(pixmap.rect(), QColor(tint))
        finally:
            painter.end()
        return pixmap

    def make_icon(
        self,
        name: str,
        tint: Optional[str] = DEFAULT_TINT,
        size: int = DEFAULT_SIZE,
        sizes: Optional[Sequence[int]] = None,
    ) -> QIcon:
        """Build a :class:`QIcon`, optionally at several sizes."""
        icon = QIcon()
        for pixel_size in sizes or (size,):
            icon.addPixmap(self.render_pixmap(name, pixel_size, tint))
        return icon


class ThemedIcons(QObject):
    """Icons tinted from a theme, and re-tinted when that theme changes.

    Connecting to ``themeChanged`` is the entire point. When tinting is done by
    hand at each call site, switching theme leaves every icon at its old colour
    until something else happens to redraw it — an icon that is subtly wrong
    and hard to attribute.

    Emits :attr:`iconsChanged` after a theme change, so widgets holding icons
    can rebuild them without knowing why.
    """

    iconsChanged = Signal()

    def __init__(
        self,
        registry: Optional[IconRegistry] = None,
        theme_manager: Any = None,
        role_tokens: Optional[Dict[str, str]] = None,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._registry = registry or IconRegistry()
        self._themes = theme_manager
        self._role_tokens = dict(ROLE_TOKENS)
        if role_tokens:
            self._role_tokens.update(role_tokens)
        if theme_manager is not None and hasattr(theme_manager, "themeChanged"):
            theme_manager.themeChanged.connect(self._on_theme_changed)

    @property
    def registry(self) -> IconRegistry:
        return self._registry

    @property
    def themes(self) -> Any:
        return self._themes

    def roles(self) -> Tuple[str, ...]:
        return tuple(sorted(self._role_tokens))

    def color(self, role: str = "idle") -> str:
        """The colour an icon role resolves to right now.

        Falls back to the token contract's default when no theme has been
        applied yet, so an icon built before the first ``apply()`` still comes
        out the colour the stylesheet will use.
        """
        token = self._role_tokens.get(role)
        if token is None:
            known = ", ".join(self.roles())
            raise IconError(f"unknown icon role {role!r}; known roles: {known}")

        theme = getattr(self._themes, "current", None)
        if theme is not None:
            value = theme.get(token)
            if value:
                return value

        contract = getattr(self._themes, "contract", None)
        if contract is not None:
            spec = contract.token(token)
            if spec is not None:
                return spec.default

        return DEFAULT_TINT

    def make_icon(
        self,
        name: str,
        role: str = "idle",
        size: int = DEFAULT_SIZE,
        sizes: Optional[Sequence[int]] = None,
    ) -> QIcon:
        return self._registry.make_icon(name, self.color(role), size, sizes)

    def render_pixmap(self, name: str, role: str = "idle", size: int = DEFAULT_SIZE) -> QPixmap:
        return self._registry.render_pixmap(name, size, self.color(role))

    def _on_theme_changed(self, _name: str) -> None:
        self.iconsChanged.emit()

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"ThemedIcons(icons={len(self._registry.names())})"
