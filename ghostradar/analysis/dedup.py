"""Near-duplicate detection that keeps reposts as a signal instead of deleting them.

Follows the research report: compare only within one employer, use 4-character
shingles (robust to German compounds), keep an explicit "uncertain" class, and
measure a job's total live time across all of its instances.
"""
from __future__ import annotations

import json
import re
import zlib
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..util import normalize_space, normalize_title, parse_datetime, strip_gender_tags

NUM_PERM = 64
_PRIME = (1 << 61) - 1
_A = [(i * 0x9E3779B97F4A7C15 + 0x632BE59BD9B4E019) % _PRIME or 1 for i in range(1, NUM_PERM + 1)]
_B = [(i * 0xBF58476D1CE4E5B9 + 0x94D049BB133111EB) % _PRIME for i in range(1, NUM_PERM + 1)]

COSMETIC = 0.85  # near-identical text: a cosmetic repost
DIFFERENT = 0.60  # below this the content changed: a new requisition


def _clean(text: str) -> str:
    text = strip_gender_tags(text or "").lower()
    text = re.sub(r"\d+", "0", text)
    return normalize_space(re.sub(r"[^\w ]+", " ", text))


def shingles(text: str, k: int = 4, max_chars: int = 6000) -> set[int]:
    clean = _clean(text)[:max_chars]
    if len(clean) < k:
        return {zlib.crc32(clean.encode())} if clean else set()
    return {zlib.crc32(clean[i:i + k].encode()) for i in range(len(clean) - k + 1)}


def signature(text: str) -> list[int] | None:
    sh = shingles(text)
    if not sh:
        return None
    return [min((a * x + b) % _PRIME for x in sh) for a, b in zip(_A, _B)]


def similarity(sig_a: list[int] | None, sig_b: list[int] | None) -> float | None:
    if not sig_a or not sig_b or len(sig_a) != len(sig_b):
        return None
    return sum(1 for x, y in zip(sig_a, sig_b) if x == y) / len(sig_a)


def title_similarity(a: str | None, b: str | None) -> float:
    ta, tb = set(normalize_title(a).split()), set(normalize_title(b).split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


@dataclass
class Instance:
    posting_id: int
    source_id: str
    start: datetime
    end: datetime | None  # None while live
    signature: list[int] | None
    text_hash: str | None
    requisition_id: str | None
    reopened: int = 0


def instance_from_row(row: dict) -> Instance:
    start =parse_datetime(row.get("posted_at")) or parse_datetime(row["first_seen"])
    first_seen = parse_datetime(row["first_seen"])
    if first_seen and start and first_seen < start:
        start = first_seen
    sig = _sig(row)
    end = parse_datetime(row.get("removed_at")) if row.get("status") == "removed" else None
    return Instance(
        posting_id=row["id"],
        source_id=row["source_id"],
        start=start,
        end=end,
        signature=sig,
        text_hash=row.get("text_hash"),
        requisition_id=row.get("requisition_id"),
        reopened=int(row.get("reopened") or 0),
    )


def _title_key(row: dict) -> str:
    return row.get("title_key") or normalize_title(row.get("title"))


def _key_similarity(a: str, b: str) -> float:
    ta, tb = set(a.split()), set(b.split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _sig(row: dict) -> list[int] | None:
    value = row.get("signature")
    if isinstance(value, str):
        return json.loads(value)
    return value


def same_job(a: dict, b: dict) -> tuple[bool, float | None]:
    """Decide whether two postings of one employer are instances of the same job."""
    if a.get("requisition_id") and a.get("requisition_id") == b.get("requisition_id"):
        return True, None
    key_a, key_b = _title_key(a), _title_key(b)
    if key_a != key_b and _key_similarity(key_a, key_b) < 0.75:
        return False, None
    if a.get("city") and b.get("city") and a["city"].lower() != b["city"].lower():
        return False, None
    if a.get("text_hash") and a.get("text_hash") == b.get("text_hash"):
        return True, 1.0
    sim = similarity(_sig(a), _sig(b))
    if sim is None:
        # no text on one side: same normalised title and city is the best we have
        return key_a == key_b, None
    return sim >= DIFFERENT, sim


def find_cluster(row: dict, candidates: list[dict]) -> int | None:
    """Cluster id of the first candidate that is the same job, checking cheap matches first."""
    req = row.get("requisition_id")
    if req:
        for cand in candidates:
            if cand.get("requisition_id") == req and cand.get("cluster_id"):
                return cand["cluster_id"]
    key = _title_key(row)
    ordered = [c for c in candidates if _title_key(c) == key] + [
        c for c in candidates if _title_key(c) != key and _key_similarity(_title_key(c), key) >= 0.75
    ]
    for cand in ordered:
        if cand.get("cluster_id") and cand["id"] != row["id"] and same_job(row, cand)[0]:
            return cand["cluster_id"]
    return None


@dataclass
class RepostSummary:
    instances: int
    cosmetic: int
    new_requisition: int
    uncertain: int
    regular_cadence: bool
    total_live_days: int
    first_start: datetime | None


def summarise_cluster(instances: list[Instance], now: datetime) -> RepostSummary:
    """Classify the sequence of instances of one job and measure its total live time."""
    if not instances:
        return RepostSummary(0, 0, 0, 0, False, 0, None)
    ordered = sorted(instances, key=lambda i: i.start)
    cosmetic = new_req = uncertain = 0
    starts: list[datetime] = [ordered[0].start]
    for prev, cur in zip(ordered, ordered[1:]):
        # a repost replaces an instance that has ended (allowing the common "post new, then
        # remove old" overlap); instances live side by side are parallel copies, not reposts
        if prev.end is None or cur.start < prev.end - timedelta(days=14):
            continue
        prev_end = prev.end
        starts.append(cur.start)
        sim = 1.0 if prev.text_hash and prev.text_hash == cur.text_hash else similarity(prev.signature, cur.signature)
        gap = (cur.start - prev_end).days
        same_req = prev.requisition_id and prev.requisition_id == cur.requisition_id
        if sim is None:
            uncertain += 1
        elif sim >= COSMETIC or (same_req and sim >= DIFFERENT):
            cosmetic += 1
        elif sim < DIFFERENT and gap >= 30:
            new_req += 1
        else:
            uncertain += 1
    cosmetic += sum(i.reopened for i in ordered)

    # union of live intervals; short gaps (≤14 days) count as continuous presence
    intervals = sorted((i.start, i.end or now) for i in ordered)
    total = timedelta()
    cur_start, cur_end = intervals[0]
    for start, end in intervals[1:]:
        if start <= cur_end + timedelta(days=14):
            cur_end = max(cur_end, end)
        else:
            total += cur_end - cur_start
            cur_start, cur_end = start, end
    total += cur_end - cur_start

    regular = False
    if len(starts) >= 4:
        gaps = [(b - a).days for a, b in zip(starts, starts[1:])]
        mean = sum(gaps) / len(gaps)
        if mean > 0:
            var = sum((g - mean) ** 2 for g in gaps) / len(gaps)
            regular = (var ** 0.5) / mean < 0.35
    return RepostSummary(
        instances=len(ordered),
        cosmetic=cosmetic,
        new_requisition=new_req,
        uncertain=uncertain,
        regular_cadence=regular,
        total_live_days=max(0, total.days),
        first_start=ordered[0].start,
    )
