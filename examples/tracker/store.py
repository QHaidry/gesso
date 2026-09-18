"""Tracker's data: the habits, and the days they were done.

No schema describes this, and that is deliberate. Configuration is small, typed
and hand-editable, which is what makes a schema worth having. A habit log is a
list the user grows and a mapping of days — neither fixed nor small — so Gesso
stays out of it and this module is plain Python.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Sequence

#: What a new profile starts with, so the first run is not a blank window.
SEED_HABITS = ("read", "walk", "water the plants")


@dataclass
class Tracker:
    """Every habit, and which of them were done on which day."""

    habits: List[str] = field(default_factory=list)
    #: ISO date -> the habit names done that day.
    done: Dict[str, List[str]] = field(default_factory=dict)

    # -- persistence ---------------------------------------------------
    @classmethod
    def load(cls, path) -> "Tracker":
        """Read the log, tolerating a missing or damaged file.

        Starting empty is a choice. Crashing on startup because a user
        hand-edited a data file badly is the worse one.
        """
        if not path.is_file():
            return cls(habits=list(SEED_HABITS))
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            habits = [str(name) for name in payload["habits"]]
            done = {
                str(day): [str(name) for name in names]
                for day, names in payload.get("done", {}).items()
            }
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            return cls()
        return cls(habits=habits, done=done)

    def save(self, path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"habits": self.habits, "done": self.done}
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    # -- queries -------------------------------------------------------
    def done_on(self, day: date) -> List[str]:
        return list(self.done.get(day.isoformat(), ()))

    def is_done(self, name: str, day: date) -> bool:
        return name in self.done.get(day.isoformat(), ())

    def count_on(self, day: date) -> int:
        return len(self.done.get(day.isoformat(), ()))

    def set_done(self, name: str, day: date, done: bool) -> None:
        """Record a habit as done (or not) on *day*."""
        key = day.isoformat()
        names = self.done.setdefault(key, [])
        if done and name not in names:
            names.append(name)
        elif not done and name in names:
            names.remove(name)
        # A day with nothing done leaves no trace; a log of empty days is noise.
        if not names:
            self.done.pop(key, None)

    def streak(self, name: str, *, today: date) -> int:
        """Days in a row, counting back from *today*."""
        count = 0
        day = today
        while self.is_done(name, day):
            count += 1
            day = date.fromordinal(day.toordinal() - 1)
        return count

    def recent_days(self, *, today: date, count: int) -> Sequence[date]:
        """The last *count* days, most recent first."""
        return [date.fromordinal(today.toordinal() - offset) for offset in range(count)]
