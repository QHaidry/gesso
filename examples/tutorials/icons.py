"""Tutorial: ship your own icons, tinted by the theme.

Run it::

    PYTHONPATH=src python examples/tutorials/icons.py
    QT_QPA_PLATFORM=offscreen PYTHONPATH=src python examples/tutorials/icons.py

(``offscreen`` is only needed on a machine with no display; the script prints a
report and never opens a window.)
"""

from __future__ import annotations

from pathlib import Path

from gesso.ui.icons import ROLE_TOKENS, IconError, IconRegistry, ThemedIcons
from gesso.ui.theme import ThemeManager

HERE = Path(__file__).parent
#: This application's own icons.
MY_ICONS = HERE / "icons"
#: Gesso's, which this application wants to keep.
import gesso.ui.icons  # noqa: E402  (after the constants, for readability)

GESSO_ICONS = gesso.ui.icons.ICONS_DIR


def main() -> int:
    from gesso.ui.app import create_app

    app = create_app(_spec(), [])

    # ------------------------------------------------------------------
    # 1. A registry is a search path, and later directories win
    # ------------------------------------------------------------------
    mine_only = IconRegistry([MY_ICONS])
    print(f"my directory alone provides: {mine_only.names()}")

    # ...which means Gesso's icons are now *gone*. This is the mistake to know
    # about: the stylesheet addresses some icons by name (the spin-box arrows),
    # so a registry that replaced Gesso's would leave them unresolved.
    print(f"  knows 'check'?  {mine_only.has('check')}")
    print(f"  knows 'star'?   {mine_only.has('star')}")

    layered = IconRegistry([GESSO_ICONS])
    layered.add_directory(MY_ICONS)
    print(f"\nlayered: {len(layered.names())} icons")
    print(f"  knows 'check'?  {layered.has('check')}   (Gesso's, still there)")
    print(f"  knows 'star'?   {layered.has('star')}    (mine, added)")

    # A name that does not exist says so, and lists what does — because
    # "no icon called 'str'" is a typo you want to see immediately.
    try:
        layered.source("str")
    except IconError as exc:
        print(f"\ntypos are loud: {exc}")

    # ------------------------------------------------------------------
    # 2. Roles are tokens, not colours
    # ------------------------------------------------------------------
    print("\nroles map to tokens, so one piece of artwork suits every theme:")
    for role, token in sorted(ROLE_TOKENS.items()):
        print(f"  {role:<10} -> {token}")

    # ------------------------------------------------------------------
    # 3. ThemedIcons resolves those at render time
    # ------------------------------------------------------------------
    themes = ThemeManager(app, parent=app)
    icons = ThemedIcons(layered, themes)

    for name in ("dark", "light"):
        themes.apply(name)
        tinted = {role: icons.color(role) for role in icons.roles()}
        print(f"\n{name:<6} idle={tinted['idle']}  active={tinted['active']}")

    pixmap = icons.render_pixmap("star", role="active", size=24)
    print(f"\nrendered 'star' at 24px: {pixmap.width()}x{pixmap.height()}, null? {pixmap.isNull()}")

    # `iconsChanged` fires after every theme change. It says *when* the icons
    # are stale; whatever is displaying them decides what to rebuild — a QLabel
    # holds a pixmap, and a pixmap does not know the theme moved.
    fired = []
    icons.iconsChanged.connect(lambda: fired.append(True))
    themes.apply("dark")
    themes.apply("light")
    print(f"iconsChanged fired {len(fired)} times across two theme changes")
    return 0


def _spec():
    from gesso.core import AppSpec

    return AppSpec(name="Icons", app_id="icons-tutorial", version="0.1.0")


if __name__ == "__main__":
    raise SystemExit(main())
