"""Feature vector for the model, built from a scored posting.

The expert score enters as one feature, so with no labels the model is a calibrated version of the hand-set
weights; the other features let it learn where those weights were wrong once labels exist.
"""
from __future__ import annotations

import math

from ..models import ScoredPosting


def _company(sp: ScoredPosting):
    return sp.features.company


def _outcomes(sp: ScoredPosting) -> dict:
    c = _company(sp)
    return (c.reports or {}) if c else {}


FEATURES: list[tuple[str, str, callable]] = [
    ("expert_score", "Expert score ÷ 10", lambda sp: sp.score.risk / 10),
    ("log_excess", "log(1 + time online ÷ typical)", lambda sp: math.log1p(sp.features.excess_ratio or 0.0)),
    ("age_unknown", "Publication date unknown", lambda sp: float(sp.features.live_days is None)),
    ("tail_low", "At most 5% of comparable postings lasted this long",
     lambda sp: float(sp.features.empirical_tail is not None and sp.features.empirical_tail <= 0.05)),
    ("reposts", "Cosmetic reposts and refreshes (max 4)",
     lambda sp: float(min(4, sp.features.repost.cosmetic + sp.features.repost.date_refreshes))),
    ("republished", "Re-published on another site", lambda sp: float(sp.features.repost.republished_days is not None)),
    ("origin_removed", "Gone from the employer's own site", lambda sp: float(sp.features.origin.status == "removed")),
    ("origin_missing", "Not on the employer's own site", lambda sp: float(sp.features.origin.status == "not_found")),
    ("origin_present", "On the employer's own site", lambda sp: float(sp.features.origin.status in {"present", "is_origin"})),
    ("expired", "Past its expiry, start date or deadline",
     lambda sp: float(bool(sp.features.valid_through_overrun_days or (sp.features.start_overrun_days or 0) >= 30))),
    ("pool_wording", "Talent-pool wording", lambda sp: float(bool(sp.features.text.evergreen))),
    ("agency", "Staffing agency", lambda sp: float(sp.features.is_agency)),
    ("internal_wording", "Internal-posting wording", lambda sp: float(bool(sp.features.text.internal))),
    ("contingent", "Depends on a project or funding award", lambda sp: float(bool(sp.features.text.contingent))),
    ("public", "Public employer", lambda sp: float(sp.features.is_public)),
    ("no_text", "No ad text available", lambda sp: float(sp.features.text.word_count < 25)),
    ("note_internal", "Your note: internal candidates usually get the jobs",
     lambda sp: float(bool(_company(sp) and _company(sp).hiring_practice == "internal_first"))),
    ("outcomes_internal", "Reported internal hires at the employer (max 3)",
     lambda sp: float(min(3, _outcomes(sp).get("internal", 0)))),
    ("outcomes_no_interview", "Employer: no interviews from 4+ answered applications",
     lambda sp: float(_outcomes(sp).get("interviews", 0) == 0 and sum(_outcomes(sp).get(k, 0) for k in
                                                                    ("auto_reject", "reject", "internal")) >= 4)),
    ("capacity", "log(1 + openings ÷ plausible openings)",
     lambda sp: math.log1p(_company(sp).capacity_ratio) if _company(sp) and _company(sp).capacity_ratio else 0.0),
    ("shrinking", "Employer headcount shrinking",
     lambda sp: float(bool(_company(sp) and _company(sp).growth is not None and _company(sp).growth <= -0.05))),
    ("applicants", "log(1 + applicants)",
     lambda sp: math.log1p(sp.features.user.applicant_count) if sp.features.user and sp.features.user.applicant_count else 0.0),
]
NAMES = [name for name, _, _ in FEATURES]
LABELS = {name: label for name, label, _ in FEATURES}


def vector(sp: ScoredPosting) -> dict[str, float]:
    """Named feature values for one scored posting (stored as a snapshot when a label arrives)."""
    out = {}
    for name, _, fn in FEATURES:
        try:
            out[name] = round(float(fn(sp)), 4)
        except (TypeError, ValueError, AttributeError):
            out[name] = 0.0
    return out
