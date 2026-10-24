"""Ground truth: gold labels from audits and outcomes, weak labels from labelling functions.

Rules from the report's validation design:
- an audit asks the employer (the Eurostat definition: is the post being filled from outside, now or soon?);
- outcomes that say something about the job itself count (interview or offer: genuine; internal candidate
  chosen: not externally fillable). Silence after applying is not a label: 63.5% of German applicants got no
  reply at least once;
- labelling functions are combined in a label model, and postings without votes stay unlabelled instead of
  being treated as genuine;
- weak labels never train the model, because they are built from the same signals as its features
  (the circular-model trap the report describes).
"""
from __future__ import annotations

import json
import math

from datetime import timedelta

from .. import db
from ..models import ScoredPosting
from ..util import parse_datetime, utcnow

MAX_AGE_DAYS = 365  # labels older than a year are not used

GHOST, GENUINE = 1, 0

AUDIT_LABELS = {
    "open": ("Open and filled from outside", GENUINE),
    "filled": ("Already filled but still advertised", GHOST),
    "internal": ("Reserved for an internal candidate", GHOST),
    "pool": ("Candidate pool, no concrete vacancy", GHOST),
    "on_hold": ("On hold or not approved", GHOST),
    "unsure": ("Could not find out", None),
}
OUTCOME_LABELS = {"interview": GENUINE, "offer": GENUINE, "internal": GHOST}


def gold_labels() -> list[dict]:
    """One label per posting: the latest audit wins over outcome reports. Each carries the feature snapshot taken
    when the label was recorded, so the model never sees what happened afterwards."""
    labels: dict[int, dict] = {}
    cutoff = utcnow() - timedelta(days=MAX_AGE_DAYS)
    recent = lambda row: (parse_datetime(row.get("created_at")) or utcnow()) >= cutoff  # noqa: E731
    for r in reversed([r for r in db.labelled_reports() if recent(r)]):  # oldest first, later reports overwrite
        y = OUTCOME_LABELS.get(r.get("response"))
        if y is None:
            continue
        labels[r["posting_id"]] = {"posting_id": r["posting_id"], "y": y, "source": "outcome", "detail": r["response"],
                                   "snapshot": json.loads(r["snapshot"]) if r.get("snapshot") else None,
                                   "risk": r.get("risk"), "weight": 1.0, "at": r.get("created_at")}
    for a in reversed([a for a in db.audit_rows() if recent(a)]):
        y = AUDIT_LABELS.get(a["label"], (None, None))[1]
        if y is None:
            continue
        labels[a["posting_id"]] = {"posting_id": a["posting_id"], "y": y, "source": "audit", "detail": a["label"],
                                   "snapshot": json.loads(a["snapshot"]) if a.get("snapshot") else None,
                                   "risk": a.get("risk"), "inclusion_prob": a.get("inclusion_prob"), "weight": 1.0,
                                   "at": a.get("created_at")}
    return list(labels.values())


# labelling functions: (key, description, assumed accuracy, vote)
LABELLING_FUNCTIONS = [
    ("repost_after_close", "Reposted with unchanged text after a close", 0.75,
     lambda sp: GHOST if sp.features.repost.cosmetic >= 1 else None),
    ("extreme_age", "Far beyond comparable lifetimes (tail ≤ 2% or 4× typical)", 0.70,
     lambda sp: GHOST if ((sp.features.empirical_tail is not None and sp.features.empirical_tail <= 0.02)
                          or (sp.features.excess_ratio or 0) >= 4) else None),
    ("origin_lag", "Copy online 14+ days after the employer removed it", 0.80,
     lambda sp: GHOST if sp.features.origin.status == "removed" and (sp.features.origin.removed_days or 0) >= 14 else None),
    ("pool_wording", "Talent-pool wording", 0.80, lambda sp: GHOST if sp.features.text.evergreen else None),
    ("fresh_on_origin", "Young and listed on the employer's own site", 0.70,
     lambda sp: GENUINE if sp.features.origin.status in {"present", "is_origin"} and (sp.features.excess_ratio or 9) < 1
     and sp.features.repost.cosmetic == 0 else None),
    ("team_build", "Part of a coherent team build", 0.65,
     lambda sp: GENUINE if sp.features.company and sp.posting.department
     and sp.posting.department in sp.features.company.coherent_departments else None),
]


def votes(sp: ScoredPosting) -> dict[str, int]:
    out = {}
    for key, _, _, fn in LABELLING_FUNCTIONS:
        try:
            v = fn(sp)
        except (TypeError, AttributeError):
            v = None
        if v is not None:
            out[key] = v
    return out


def label_model(vote_map: dict[str, int], accuracies: dict[str, float] | None = None) -> float | None:
    """Probability of 'ghost' from the votes (weighted majority vote in log-odds; class prior 50:50).
    None when no labelling function voted: the posting stays unlabelled."""
    if not vote_map:
        return None
    acc = {key: a for key, _, a, _ in LABELLING_FUNCTIONS}
    acc.update(accuracies or {})
    logit = 0.0
    for key, v in vote_map.items():
        a = min(0.99, max(0.51, acc.get(key, 0.6)))
        weight = math.log(a / (1 - a))
        logit += weight if v == GHOST else -weight
    return 1 / (1 + math.exp(-logit))


def lf_report(scored: list[ScoredPosting], gold: list[dict]) -> list[dict]:
    """Coverage, votes and accuracy against gold labels for each labelling function."""
    gold_by_id = {g["posting_id"]: g["y"] for g in gold}
    rows = []
    for key, desc, prior, fn in LABELLING_FUNCTIONS:
        ghost = genuine = hits = checked = 0
        for sp in scored:
            try:
                v = fn(sp)
            except (TypeError, AttributeError):
                v = None
            if v is None:
                continue
            ghost += v == GHOST
            genuine += v == GENUINE
            if sp.posting_id in gold_by_id:
                checked += 1
                hits += gold_by_id[sp.posting_id] == v
        rows.append({"key": key, "label": desc, "prior_accuracy": prior, "ghost_votes": ghost, "genuine_votes": genuine,
                     "coverage": round((ghost + genuine) / len(scored), 3) if scored else 0.0,
                     "checked": checked, "accuracy": round((hits + 1) / (checked + 2), 3) if checked else None})
    return rows
