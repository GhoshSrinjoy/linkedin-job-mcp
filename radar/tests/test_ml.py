from datetime import datetime, timedelta, timezone

import numpy as np
from fastapi.testclient import TestClient

from ghostradar.main import app
from ghostradar.ml import audit, labels, model, survival

NOW = datetime(2026, 10, 24, tzinfo=timezone.utc)


def test_kaplan_meier_matches_a_hand_computed_curve():
    # removals at 10, 20 (two), censored at 15 and 30: S(10)=4/5, S(20)=4/5 * (1 - 2/3)
    spells = [survival.Spell(0, 10, True), survival.Spell(0, 15, False), survival.Spell(0, 20, True),
              survival.Spell(0, 20, True), survival.Spell(0, 30, False)]
    curve = survival.kaplan_meier(spells)
    assert abs(survival.survival_at(curve, 10) - 0.8) < 1e-9
    assert abs(survival.survival_at(curve, 25) - 0.8 / 3) < 1e-9
    assert survival.median_lifetime(curve) == 20


def test_left_truncated_postings_only_count_from_when_they_were_seen():
    # a posting first seen at age 50 cannot be at risk at age 10
    spells = [survival.Spell(0, 10, True), survival.Spell(50, 60, False), survival.Spell(0, 40, False)]
    assert abs(survival.survival_at(survival.kaplan_meier(spells), 10) - 0.5) < 1e-9


def test_copies_of_one_job_form_one_lifetime():
    rows = [
        {"id": 1, "cluster_id": 1, "channel": "employer", "kldb": "434", "posted_at": "2026-01-01T00:00:00+00:00",
         "first_seen": "2026-01-02T00:00:00+00:00", "last_seen": "2026-03-01T00:00:00+00:00", "status": "removed",
         "removed_at": "2026-03-03T00:00:00+00:00"},
        {"id": 2, "cluster_id": 1, "channel": "aggregator", "kldb": "434", "posted_at": "2026-01-05T00:00:00+00:00",
         "first_seen": "2026-01-05T00:00:00+00:00", "last_seen": "2026-06-01T00:00:00+00:00", "status": "active"},
    ]
    jobs = survival.job_rows(rows)
    assert len(jobs) == 1 and jobs[0]["status"] == "active"  # one copy is still online: the job is not closed
    spell = survival.spell_from_row(jobs[0], NOW)
    assert not spell.event and spell.exit > 140


def test_logistic_model_learns_a_planted_effect_and_starts_at_the_prior():
    rng = np.random.default_rng(1)
    n = 400
    X = np.zeros((n, len(model.NAMES)))
    X[:, 0] = 1.0
    X[:, model.NAMES.index("expert_score")] = rng.uniform(1, 8, n)
    planted = model.NAMES.index("origin_removed")
    X[:, planted] = rng.integers(0, 2, n)
    logit = -4.5 + X[:, 1] + 2.0 * X[:, planted]
    y = (rng.uniform(size=n) < 1 / (1 + np.exp(-logit))).astype(float)
    beta, cov = model.fit(X, y)
    assert beta[planted] > 1.0  # learned from the data, against a prior centred on 0
    p, low, high = model.predict(X[:5], beta, cov)
    assert np.all(low <= p) and np.all(p <= high)
    empty_beta, _ = model.fit(X[:0], y[:0])
    assert np.allclose(empty_beta, model._prior()[0])  # no labels: the expert prior


def test_metrics_on_known_inputs():
    p = np.array([0.9, 0.8, 0.3, 0.2])
    y = np.array([1.0, 0.0, 1.0, 0.0])
    assert model.roc_auc(p, y) == 0.75
    assert abs(model.brier(p, y) - (0.01 + 0.64 + 0.49 + 0.04) / 4) < 1e-12
    assert model.precision_at(p, y, budget=0.5) == 0.5
    assert sum(b["n"] for b in model.calibration(p, y, bins=2)) == 4


def test_label_model_leaves_unvoted_postings_unlabelled():
    assert labels.label_model({}) is None
    assert labels.label_model({"origin_lag": labels.GHOST}) > 0.5
    assert labels.label_model({"origin_lag": labels.GHOST, "fresh_on_origin": labels.GENUINE}) is not None


def test_prevalence_estimate_weights_by_inclusion_probability():
    gold = [{"source": "audit", "y": 1, "inclusion_prob": 0.5}] * 3 + [{"source": "audit", "y": 0, "inclusion_prob": 0.1}] * 3
    est = audit.prevalence(gold)
    assert abs(est["estimate"] - (3 * 2) / (3 * 2 + 3 * 10)) < 1e-3  # rarely drawn genuine postings count more
    assert est["low"] <= est["estimate"] <= est["high"]
    assert audit.prevalence(gold[:2])["estimate"] is None


def _store_jobs(n: int):
    from ghostradar import services
    from ghostradar.models import Posting
    from ghostradar.util import utcnow

    now = utcnow()
    postings = [Posting(source="greenhouse", source_id=f"acme:{i}", title=f"Data Engineer {i} (m/w/d)", company="Acme",
                        city="Berlin", description=f"Wir suchen Verstärkung {i} für das Plattform-Team mit Python.",
                        posted_at=now - timedelta(days=10 + 15 * i)) for i in range(n)]
    return services.ingest(postings, now=now)


def test_audit_queue_audits_and_training_through_the_api():
    ids = _store_jobs(16)
    with TestClient(app) as client:
        queue = client.get("/api/audit/queue", params={"n": 8}).json()
        assert queue["items"] and all(0 < q["inclusion_prob"] <= 1 for q in queue["items"])
        assert "freigegeben" in queue["script_de"]
        first = queue["items"][0]
        client.post("/api/audit", json={"posting_id": first["posting_id"], "label": "internal", "method": "asked HR",
                                        "inclusion_prob": first["inclusion_prob"]})
        assert first["posting_id"] not in {q["posting_id"] for q in client.get("/api/audit/queue").json()["items"]}
        status = client.get("/api/model").json()
        assert status["gold"]["audits"] == 1 and status["gold"]["with_snapshot"] == 1
        assert client.post("/api/model/train").json()["trained"] is False  # too few labels: no model yet
        for i, pid in enumerate(ids):
            client.post("/api/audit", json={"posting_id": pid, "label": "filled" if i % 2 else "open"})
        trained = client.post("/api/model/train").json()
        assert trained["trained"] and {"model", "expert", "base_rate"} <= set(trained["metrics"])
        posting = client.get(f"/api/postings/{ids[0]}").json()
        assert 0 <= posting["estimate"]["p"] <= 1
