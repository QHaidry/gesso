"""Starting and structuring an application.

:func:`run_app` is the whole of an application's graphical entry point;
:class:`AppShell` is the window it is handed.

```python
from gesso.ui.app import run_app


def build(shell):
    shell.add_page("home", "Home", HomePage(), icon="folder")
    shell.set_brand("My App", "does one thing well")


if __name__ == "__main__":
    raise SystemExit(run_app(APP, build))
```

Requires PySide6.
"""

from .bootstrap import create_app, install_exception_hook, run_app
from .shell import SIDEBAR_WIDTH_COLLAPSED, SIDEBAR_WIDTH_EXPANDED, AppShell, Page

__all__ = [
    "run_app",
    "create_app",
    "install_exception_hook",
    "AppShell",
    "Page",
    "SIDEBAR_WIDTH_EXPANDED",
    "SIDEBAR_WIDTH_COLLAPSED",
]
