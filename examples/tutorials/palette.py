"""Tutorial: the token contract, without a toolkit.

This is the whole theming layer minus Qt. Nothing here imports PySide6, so you
can check a palette on a build server, in a pre-commit hook, or while your GUI
dependencies are still installing.

Run it::

    PYTHONPATH=src python examples/tutorials/palette.py
"""

from __future__ import annotations

from gesso.ui.theme import BASE_CONTRACT, QssError, TOKEN_GROUPS, render

# ----------------------------------------------------------------------
# 1. A palette only has to state what it changes
# ----------------------------------------------------------------------
# Tracker's actual palette, trimmed to the interesting lines. The other
# fourteen tokens are not missing: the contract has a last-resort default for
# every one of them, which is what lets a palette be this short.
PARTIAL = {
    "window": "#15161e",
    "panel": "#1b1d27",
    "card": "#22242f",
    "text_strong": "#eef1ff",
    "accent": "#7aa2f7",
    "accent_text": "#101223",
}


def main() -> int:
    print(f"the contract declares {len(BASE_CONTRACT)} tokens in {len(TOKEN_GROUPS)} groups:")
    for group, tokens in BASE_CONTRACT.groups().items():
        print(f"  {group:<9} {', '.join(token.key for token in tokens)}")

    # ------------------------------------------------------------------
    # 2. Resolving fills the gaps
    # ------------------------------------------------------------------
    resolved = BASE_CONTRACT.resolve(PARTIAL)
    print(f"\n{PARTIAL.__len__()} given + contract defaults = {len(resolved)} tokens")
    print(f"  window        {resolved['window']}   (given)")
    print(f"  scroll_handle {resolved['scroll_handle']}   (from the contract)")

    # ------------------------------------------------------------------
    # 3. Typos and gaps are reported, not ignored
    # ------------------------------------------------------------------
    # A mistyped token is *unknown*: it would be silently dropped otherwise, and
    # you would spend an afternoon wondering why one colour never changes.
    print(f"\nunknown tokens: {BASE_CONTRACT.unknown({'acccent': '#fff'})}")
    # An unstated one is *missing*, which is a different problem with a
    # different fix.
    print(f"missing tokens: {len(BASE_CONTRACT.missing(PARTIAL))}")

    # ------------------------------------------------------------------
    # 4. Rendering the stylesheet
    # ------------------------------------------------------------------
    colors = BASE_CONTRACT.resolve(PARTIAL)
    try:
        render(colors)
    except QssError as exc:
        # Exactly one placeholder is not a token: `icon_dir`, a filesystem path
        # the stylesheet uses for the spin-box arrows.
        print(f"\nrender refused: {exc}")

    sheet = render(colors, {"icon_dir": "/usr/share/gesso/icons"})
    print(f"rendered {len(sheet)} characters of QSS")
    print(f"  accent made it into the sheet: {'#7aa2f7' in sheet}")

    # ------------------------------------------------------------------
    # 5. And no Qt anywhere
    # ------------------------------------------------------------------
    import sys

    loaded = [name for name in sys.modules if name.startswith("PySide6")]
    print(f"\nPySide6 modules loaded: {loaded or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
