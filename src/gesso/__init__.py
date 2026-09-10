"""Gesso — a framework for building Qt (PySide6) desktop applications.

Gesso is the primer layer an application is painted onto: it provides the
design system, theming, internationalisation, configuration management and a
standard widget library, so application authors write only their own logic.

The package is deliberately layered by dependency weight:

``gesso.core``
    Application identity and XDG path resolution. No third-party imports.
``gesso.config``
    Schema-typed, format-agnostic configuration (JSON / TOML / YAML).
``gesso.i18n``
    Translation loading and lookup. (planned)

Qt-facing layers (``gesso.ui``) are imported lazily so that headless consumers
never load PySide6.
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
