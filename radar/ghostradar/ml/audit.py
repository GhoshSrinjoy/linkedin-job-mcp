"""Audit sample and prevalence estimate, following the report's validation design.

Postings are drawn per grade with probability proportional to their age, without replacement (Efraimidis–Spirakis
keys). Each draw keeps its inclusion probability, so the audited labels give a design-weighted (Hájek) estimate of
the share of postings that are not genuinely open, with a Wilson interval on the effective sample size.
"""
from __future__ import annotations

import math
import random

from ..models import ScoredPosting

GRADES = ("low", "moderate", "elevated", "high")

# the audit question (MoreThanCareer's practical test, Eurostat's vacancy definition)
SCRIPT_DE = ("Ist die Stelle aktuell freigegeben, wird sie extern besetzt, und zu welchem Termin soll sie besetzt "
             "werden?")
SCRIPT_EN = "Is the position approved, is it being filled from outside, and what is the target start date?"


def draw(jobs: list[ScoredPosting], n: int = 12, exclude: set[int] | None = None, seed: int | None = None) -> list[dict]:
    """A stratified sample: equal shares per grade, probability proportional to age within each grade."""
    rng = random.Random(seed)
    exclude = exclude or set()
    strata: dict[str, list[ScoredPosting]] = {}
    for sp in jobs:
        if sp.posting_id and sp.posting_id not in exclude and sp.score.grade in GRADES:
            strata.setdefault(sp.score.grade, []).append(sp)
    if not strata:
        return []
    per = max(1, n // len(strata))
    picked = []
    for grade in GRADES:
        items = strata.get(grade, [])
        if not items:
            continue
        k = min(len(items), per)
        weights = [max(7.0, float(sp.features.live_days or 7)) for sp in items]
        total = sum(weights)
        keys = sorted(((rng.random() ** (1.0 / w), i) for i, w in enumerate(weights)), reverse=True)[:k]
        for _, i in keys:
            picked.append({"posting_id": items[i].posting_id, "grade": grade,
                           "inclusion_prob": round(min(1.0, k * weights[i] / total), 5), "item": items[i]})
    return picked


def prevalence(gold: list[dict], z: float = 1.96) -> dict:
    """Design-weighted share of audited postings that are not genuinely open (Hájek estimator)."""
    audited = [g for g in gold if g.get("source") == "audit" and g.get("inclusion_prob")]
    if len(audited) < 5:
        return {"audited": len(audited), "estimate": None,
                "note": "Needs at least 5 audited postings from the audit sample."}
    w = [1.0 / g["inclusion_prob"] for g in audited]
    p = sum(wi * g["y"] for wi, g in zip(w, audited)) / sum(w)
    n_eff = sum(w) ** 2 / sum(wi * wi for wi in w)
    denom = 1 + z * z / n_eff
    centre = (p + z * z / (2 * n_eff)) / denom
    half = z * math.sqrt(p * (1 - p) / n_eff + z * z / (4 * n_eff * n_eff)) / denom
    return {"audited": len(audited), "estimate": round(p, 3), "low": round(max(0.0, centre - half), 3),
            "high": round(min(1.0, centre + half), 3), "effective_n": round(n_eff, 1)}
