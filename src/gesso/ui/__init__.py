"""The Qt user-interface tier.

Importing this package is safe on a machine with no toolkit installed: nothing
here is imported eagerly, so ``import gesso`` never pulls in PySide6. The
modules that need Qt are reached by name, and fail only when you actually ask
for them.
"""

from __future__ import annotations

__all__: list = []
