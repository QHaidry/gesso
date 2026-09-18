"""Starting an application.

``run_app`` is the whole of an application's graphical entry point: build the
``QApplication``, decide the layout direction, apply the theme, build the
window, and run the event loop. Every one of those steps is something every Qt
application does slightly differently and gets slightly wrong — and the one
that is always forgotten is the exception hook, without which an error inside a
slot vanishes into a terminal nobody is looking at.
"""

from __future__ import annotations

import logging
import sys
import traceback
from pathlib import Path
from typing import Any, Callable, Optional, Sequence

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget

from gesso.core.app import AppSpec
from gesso.i18n import detect_language, is_rtl
from gesso.ui.icons import IconRegistry, ThemedIcons
from gesso.ui.theme import ThemeManager

from .shell import AppShell

__all__ = ["create_app", "run_app", "install_exception_hook"]

logger = logging.getLogger("gesso.app")


def create_app(spec: AppSpec, argv: Optional[Sequence[str]] = None) -> QApplication:
    """Build (or return) the ``QApplication``, carrying the application's identity.

    The name and organisation are not cosmetic: Qt uses them to locate
    settings, and the window manager uses the display name for the window and
    the task switcher.

    Note there is no high-DPI setup. Qt 6 scales high-DPI displays by default,
    and the Qt 5 attributes that used to enable it are deprecated no-ops that
    only produce warnings.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(list(argv) if argv is not None else sys.argv)

    app.setApplicationName(spec.app_id)
    app.setApplicationDisplayName(spec.display_name)
    app.setApplicationVersion(spec.version)
    if spec.org:
        app.setOrganizationName(spec.org)
    return app


def install_exception_hook(
    on_error: Optional[Callable[[str], None]] = None,
) -> None:
    """Report an unhandled exception instead of losing it.

    A Qt application whose slot raises prints to stderr and carries on, which
    is invisible when the application was launched from a menu. The traceback
    is always logged; *on_error* is given the formatted text so the application
    can show it.

    ``KeyboardInterrupt`` is left to Python, which is what ``Ctrl-C`` in a
    terminal expects.
    """
    previous = sys.excepthook

    def hook(exc_type: Any, exc_value: Any, exc_tb: Any) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            previous(exc_type, exc_value, exc_tb)
            return
        text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        logger.error("unhandled exception:\n%s", text)
        if on_error is not None:
            try:
                on_error(text)
            except Exception:  # pragma: no cover - a broken handler
                logger.exception("the error handler itself failed")

    sys.excepthook = hook


def run_app(
    spec: AppSpec,
    build: Optional[Callable[[AppShell], Optional[QMainWindow]]] = None,
    *,
    argv: Optional[Sequence[str]] = None,
    theme: Optional[str] = None,
    builtin_theme_dirs: Optional[Sequence[Path]] = None,
    user_theme_dir: Optional[Path] = None,
    icons_dir: Optional[Path] = None,
    icon_dirs: Optional[Sequence[Path]] = None,
    window_icon: Optional[QIcon] = None,
    language: Optional[str] = None,
    theme_manager: Optional[ThemeManager] = None,
    icons: Optional[ThemedIcons] = None,
    shell_factory: Callable[..., AppShell] = AppShell,
    translate: Optional[Callable[..., str]] = None,
    on_error: Optional[Callable[[str], None]] = None,
) -> int:
    """Build the application, show the window, and run the event loop.

    *build* receives the :class:`~gesso.ui.app.shell.AppShell` and populates it
    with pages. It may return a window of its own instead, in which case that
    is shown. It may also be omitted, for an application whose shell populates
    itself.

    *shell_factory* is called to make the window, so an application can supply
    its own :class:`~gesso.ui.app.shell.AppShell` subclass rather than having
    one built and thrown away. *translate* is handed to the shell for its own
    strings.

    Returns the event loop's exit code, ready for ``sys.exit``.
    """
    app = create_app(spec, argv)

    # The layout direction follows the language. An RTL language mirrors the
    # whole interface, and Qt does it without a single widget knowing.
    language = language or detect_language()
    app.setLayoutDirection(
        Qt.LayoutDirection.RightToLeft if is_rtl(language) else Qt.LayoutDirection.LeftToRight
    )

    # Extra directories are *appended*, so an application layers its own icons
    # over Gesso's rather than replacing the set the stylesheet depends on.
    registry = IconRegistry()
    for directory in icon_dirs or ():
        registry.add_directory(directory)

    if theme_manager is None:
        theme_manager = ThemeManager(
            app,
            builtin_dirs=list(builtin_theme_dirs) if builtin_theme_dirs else None,
            user_dir=user_theme_dir,
            icons_dir=icons_dir,
        )
    if icons is None:
        icons = ThemedIcons(registry, theme_manager)

    theme_manager.apply(theme)

    if window_icon is not None:
        app.setWindowIcon(window_icon)

    install_exception_hook(on_error)

    shell = shell_factory(
        spec, theme_manager=theme_manager, icons=icons, translate=translate
    )
    window = build(shell) if build is not None else None
    if window is None:
        window = shell
    elif not isinstance(window, QWidget):
        # The documented contract is "return a window to use instead of the
        # shell, or nothing". Anything else is a mistake, and saying so beats
        # the AttributeError that `window.show()` would otherwise raise.
        raise TypeError(
            f"build returned {type(window).__name__}, but run_app expects a "
            f"QWidget to show, or None to use the shell"
        )
    window.show()

    return app.exec()
