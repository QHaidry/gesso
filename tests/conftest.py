"""Shared fixtures for the Gesso test suite."""

from __future__ import annotations

import pytest

from gesso.config import Option, Schema, Section


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
