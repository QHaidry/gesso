"""Shared fixtures for the Gesso test suite."""

from __future__ import annotations

import os

# Qt must be told to run headless before it is imported anywhere, so the
# design-system tests need no display and behave the same in CI.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402 - must follow the environment setup above

from gesso.config import Option, Schema, Section  # noqa: E402


@pytest.fixture
def schema() -> Schema:
    """A small but representative schema covering every supported type."""
    return Schema(
        [
            Section(
                "general",
                title="General",
                options=(
                    Option("provider", str, "bing", "Default provider"),
                    Option("auto_update", bool, True, "Update on a schedule"),
                    Option("interval", int, 86400, "Seconds between updates"),
                ),
            ),
            Section(
                "image",
                options=(
                    Option("scale", float, 1.5, "Upscale factor"),
                    Option("effects", list, ["none"], "Applied effects"),
                ),
            ),
        ]
    )
