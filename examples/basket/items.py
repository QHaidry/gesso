"""The list itself — Basket's own data, not its settings.

Gesso governs configuration. It deliberately does not govern application data:
a schema is small, typed and hand-editable, whereas what an application stores
is whatever shape that application needs. Keeping the two apart is why the list
lives in the *data* directory and the preferences live in the *config*
directory, and why this module is plain Python.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


@dataclass
class Item:
    """One line of the list."""

    name: str
    price: Optional[float] = None


class ItemStore:
    """The list, as a JSON file."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> List[Item]:
        """Read the list, tolerating a missing or damaged file.

        Returning empty on damage is a choice, and not the only reasonable one
        — but crashing on startup because a data file was hand-edited badly is
        worse than starting empty and letting the user see that.
        """
        if not self.path.is_file():
            return []
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            rows = payload["items"]
        except (OSError, ValueError, KeyError, TypeError):
            return []

        items: List[Item] = []
        for row in rows:
            if isinstance(row, dict) and row.get("name"):
                price = row.get("price")
                items.append(
                    Item(name=str(row["name"]), price=float(price) if price is not None else None)
                )
        return items

    def save(self, items: Sequence[Item]) -> None:
        """Write the list, creating the data directory if it is not there yet."""
        payload: Dict[str, Any] = {
            "items": [{"name": item.name, "price": item.price} for item in items]
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    # -- operations ----------------------------------------------------
    @staticmethod
    def find(items: Sequence[Item], name: str) -> Optional[Item]:
        """Find an item by name, case-insensitively."""
        wanted = name.casefold()
        for item in items:
            if item.name.casefold() == wanted:
                return item
        return None

    @staticmethod
    def sorted_by_name(items: Sequence[Item]) -> List[Item]:
        return sorted(items, key=lambda item: item.name.casefold())
