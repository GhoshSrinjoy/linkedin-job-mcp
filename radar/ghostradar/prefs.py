"""Your thresholds and the history window, stored in the database and set on the Method page.

The history window limits every look back (news, contracts, funding, your notes and outcomes, lifetimes, model
labels) to at most one year, so assessments rest on current data.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta

from . import db
from .config import settings

DEFAULTS: dict[str, float | int] = {
    "age_start": 1.0,  # age starts to count at this multiple of the occupation's typical advertising time
    "chance_high": 100,  # applicants from which chances count as low, whatever the field
    "chance_very_high": 200,
    "window_days": 365,  # history window: 7, 30, 90 or 365 days
}
MAX_WINDOW_DAYS = 365
WINDOWS = (7, 30, 90, 365)
_CACHE: dict = {"at": 0.0, "db": None, "values": None}


def get() -> dict:
    now = time.monotonic()
    path = str(settings.db_path)
    if _CACHE["values"] is None or _CACHE["db"] != path or now - _CACHE["at"] > 5:
        values = dict(DEFAULTS)
        for key, raw in db.get_prefs().items():
            if key in DEFAULTS:
                try:
                    values[key] = type(DEFAULTS[key])(float(raw))
                except ValueError:
                    pass
        values["window_days"] = min(MAX_WINDOW_DAYS, max(7, int(values["window_days"])))
        _CACHE.update(at=now, db=path, values=values)
    return _CACHE["values"]


def save(values: dict) -> dict:
    db.set_prefs({k: v for k, v in values.items() if k in DEFAULTS})
    _CACHE["values"] = None
    return get()


def since(now: datetime) -> datetime:
    """Start of the history window."""
    return now - timedelta(days=get()["window_days"])
