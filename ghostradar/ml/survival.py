"""Posting lifetimes with survival methods, the report's recommended baseline.

Each posting is a spell from its first publication to its removal. Three complications are handled:
- right-censoring: a posting still online ends at its last confirmed sighting, without an event;
- left-truncation: a posting first seen when it was already online only counts from that age on;
- interval-censoring: a removal falls between the last sighting and the confirmed removal (two misses), so the
  midpoint is used.
The tail probability S(age | group) is the share of comparable postings still online at that age. Groups go from
fine (occupation, level, employer or platform, agency) to coarse (everything) and the finest group with enough
observed removals is used.
"""
from __future__ import annotations

import bisect
from dataclasses import dataclass
from datetime import datetime, timedelta

from .. import db
from ..util import parse_datetime, utcnow

MIN_EVENTS = 20  # observed removals a group needs before its curve is used
MIN_SPELLS = 40
WINDOW_DAYS = 365  # only jobs the radar saw in the last year


@dataclass
class Spell:
    entry: float  # age in days when the radar first saw the posting
    exit: float  # age at removal, or at the last confirmed sighting
    event: bool  # True if removal was observed


def spell_from_row(row: dict, now: datetime) -> Spell | None:
    start = parse_datetime(row.get("posted_at")) or parse_datetime(row.get("first_seen"))
    first_seen = parse_datetime(row.get("first_seen"))
    if not start or not first_seen:
        return None
    if first_seen < start:
        start = first_seen
    if row.get("status") == "removed" and row.get("removed_at"):
        removed = parse_datetime(row["removed_at"])
        last = parse_datetime(row.get("last_seen")) or removed
        end = last + (removed - last) / 2 if removed and last and removed > last else (removed or last)
        event = True
    else:
        end = parse_datetime(row.get("last_seen")) or now
        event = False
    entry = max(0.0, (first_seen - start).total_seconds() / 86400)
    exit_ = max(entry + 0.5, (end - start).total_seconds() / 86400)
    return Spell(entry=entry, exit=exit_, event=event)


def kaplan_meier(spells: list[Spell]) -> list[tuple[float, float]]:
    """Product-limit estimate with left-truncation: the risk set at t is every spell with entry < t <= exit."""
    times = sorted({s.exit for s in spells if s.event})
    entries = sorted(s.entry for s in spells)
    exits = sorted(s.exit for s in spells)
    events: dict[float, int] = {}
    for s in spells:
        if s.event:
            events[s.exit] = events.get(s.exit, 0) + 1
    surv = 1.0
    curve = [(0.0, 1.0)]
    for t in times:
        entered = bisect.bisect_left(entries, t)  # entry < t
        left = bisect.bisect_left(exits, t)  # exit < t
        at_risk = entered - left
        if at_risk > 0:
            surv *= 1 - events[t] / at_risk
        curve.append((t, surv))
    return curve


def survival_at(curve: list[tuple[float, float]], age: float) -> float:
    idx = bisect.bisect_right([t for t, _ in curve], age) - 1
    return curve[max(0, idx)][1]


def median_lifetime(curve: list[tuple[float, float]]) -> float | None:
    for t, s in curve:
        if s <= 0.5:
            return t
    return None


@dataclass
class Group:
    key: tuple
    label: str
    spells: list[Spell]
    curve: list[tuple[float, float]] | None = None

    @property
    def events(self) -> int:
        return sum(1 for s in self.spells if s.event)

    def usable(self) -> bool:
        return self.events >= MIN_EVENTS and len(self.spells) >= MIN_SPELLS

    def fitted(self) -> list[tuple[float, float]]:
        if self.curve is None:
            self.curve = kaplan_meier(self.spells)
        return self.curve


def _keys(row: dict) -> list[tuple[tuple, str]]:
    kldb = row.get("kldb") or "?"
    level = row.get("level_code") or "?"
    channel = row.get("channel") or "?"
    agency = "agency" if row.get("agency_flag") == 1 else "direct"
    return [
        (("occ+lvl+chan", kldb, level, channel, agency), f"KldB {kldb}, level {level}, {channel}, {agency}"),
        (("occ+lvl", kldb, level), f"KldB {kldb}, level {level}"),
        (("occ", kldb[:3]), f"KldB {kldb[:3]}"),
        (("area", kldb[:2]), f"KldB area {kldb[:2]}"),
        (("agency", agency), "staffing agencies" if agency == "agency" else "direct employers"),
        (("all",), "all postings"),
    ]


def job_rows(rows: list[dict]) -> list[dict]:
    """One row per job: copies of a job (same cluster) form one lifetime, from the first publication anywhere to
    the last removal; the job is closed only when every copy is gone."""
    clusters: dict = {}
    for r in rows:
        clusters.setdefault(r.get("cluster_id") or ("id", r.get("id")), []).append(r)
    jobs = []
    for copies in clusters.values():
        main = next((c for c in copies if c.get("channel") == "employer"), copies[0])
        starts = [c.get("posted_at") or c.get("first_seen") for c in copies]
        closed = all(c.get("status") == "removed" and c.get("removed_at") for c in copies)
        jobs.append({
            **main,
            "posted_at": min((s for s in starts if s), default=None),
            "first_seen": min((c["first_seen"] for c in copies if c.get("first_seen")), default=None),
            "last_seen": max((c["last_seen"] for c in copies if c.get("last_seen")), default=None),
            "status": "removed" if closed else "active",
            "removed_at": max((c["removed_at"] for c in copies if c.get("removed_at")), default=None) if closed else None,
        })
    return jobs


class LifetimeModel:
    """Survival curves for every group of comparable postings in the archive."""

    def __init__(self, rows: list[dict], now: datetime):
        self.now = now
        self.groups: dict[tuple, Group] = {}
        for row in job_rows(rows):
            spell = spell_from_row(row, now)
            if spell is None:
                continue
            for key, label in _keys(row):
                group = self.groups.get(key)
                if group is None:
                    group = self.groups[key] = Group(key=key, label=label, spells=[])
                group.spells.append(spell)

    def best_group(self, kldb: str | None, level: str | None, channel: str | None, agency: bool) -> Group | None:
        row = {"kldb": kldb, "level_code": level, "channel": channel, "agency_flag": 1 if agency else 0}
        for key, _ in _keys(row):
            group = self.groups.get(key)
            if group and group.usable():
                return group
        return None

    def tail(self, age: float, kldb: str | None, level: str | None, channel: str | None, agency: bool) -> dict | None:
        group = self.best_group(kldb, level, channel, agency)
        if group is None:
            return None
        curve = group.fitted()
        return {"tail": round(survival_at(curve, age), 3), "group": group.label, "spells": len(group.spells),
                "events": group.events, "median_days": median_lifetime(curve)}

    def summary(self, limit: int = 8) -> list[dict]:
        """The largest usable groups, finest first, with their curves (for the model page)."""
        usable = [g for g in self.groups.values() if g.usable()]
        usable.sort(key=lambda g: (-len(g.key), -g.events))
        out = []
        for g in usable[:limit]:
            curve = g.fitted()
            out.append({"group": g.label, "spells": len(g.spells), "events": g.events,
                        "median_days": median_lifetime(curve),
                        "curve": [(round(t, 1), round(s, 4)) for t, s in curve[:: max(1, len(curve) // 120)]]})
        return out

    def totals(self) -> dict:
        everything = self.groups.get(("all",))
        spells = everything.spells if everything else []
        return {"spells": len(spells), "events": sum(1 for s in spells if s.event),
                "left_truncated": sum(1 for s in spells if s.entry >= 1), "min_events": MIN_EVENTS}


_CACHE: dict = {"key": None, "model": None}


def model(now: datetime | None = None) -> LifetimeModel:
    """The lifetime model for the current archive, rebuilt when postings change."""
    key = db.data_fingerprint()
    if _CACHE["key"] != key or _CACHE["model"] is None:
        now = now or utcnow()
        cutoff = now - timedelta(days=WINDOW_DAYS)
        rows = [r for r in db.lifetime_rows() if (parse_datetime(r.get("last_seen")) or now) >= cutoff]
        _CACHE.update(key=key, model=LifetimeModel(rows, now))
    return _CACHE["model"]
