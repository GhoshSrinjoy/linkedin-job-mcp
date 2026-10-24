"""Calibrated ghost-job model: Bayesian logistic regression whose prior is the expert score.

    logit P(not genuinely open) = a + b · (expert score ÷ 10) + Σ w_k · x_k

The prior a ~ N(-4.5, 2²), b ~ N(1, 0.5²) puts 50% at an expert score of 45 (the "elevated" threshold) and every
other weight starts at w_k ~ N(0, 0.5²). With few labels the model is the expert score, calibrated; it learns
corrections only where the labels support them. Fitted by Newton's method (maximum a posteriori); the Laplace
approximation gives a 90% interval for every estimate.

Evaluation: train on earlier labels and test on later ones, using only what was known when each label was
recorded (feature snapshots). Brier score, log loss, ROC AUC, precision at a fixed review budget and a calibration
table, each next to the expert score alone and the base rate, never plain accuracy. With too few later labels of
both kinds, stratified cross-validation is used instead and the result says so.
"""
from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path

import numpy as np

from ..config import settings
from ..models import ScoredPosting
from ..util import utcnow
from . import features as feats
from . import labels as lab

MIN_LABELS = 12
MIN_PER_CLASS = 4
REVIEW_BUDGET = 0.2  # share of postings a reviewer can check: precision is measured on the top 20%
TEST_SHARE = 0.3  # the latest 30% of labels are held out for the temporal test
PRIOR_MEAN = {"intercept": -4.5, "expert_score": 1.0}
PRIOR_SD = {"intercept": 2.0, "expert_score": 0.5}
DEFAULT_SD = 0.5
NAMES = ["intercept", *feats.NAMES]


def model_path() -> Path:
    return Path(settings.db_path).parent / "model.json"


def _prior() -> tuple[np.ndarray, np.ndarray]:
    mean = np.array([PRIOR_MEAN.get(n, 0.0) for n in NAMES])
    sd = np.array([PRIOR_SD.get(n, DEFAULT_SD) for n in NAMES])
    return mean, 1.0 / sd**2


def design(snapshots: list[dict]) -> np.ndarray:
    return np.array([[1.0, *[float(s.get(n, 0.0)) for n in feats.NAMES]] for s in snapshots])


def _sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -35, 35)))


def fit(X: np.ndarray, y: np.ndarray, weights: np.ndarray | None = None, iters: int = 60):
    """MAP estimate and Laplace covariance for logistic regression with a Gaussian prior."""
    mean, precision = _prior()
    w = np.ones(len(y)) if weights is None else weights
    beta = mean.copy()
    hessian = np.diag(precision)
    for _ in range(iters):
        p = _sigmoid(X @ beta)
        grad = X.T @ (w * (p - y)) + precision * (beta - mean)
        hessian = X.T @ (X * (w * p * (1 - p))[:, None]) + np.diag(precision)
        step = np.linalg.solve(hessian, grad)
        beta = beta - step
        if np.max(np.abs(step)) < 1e-8:
            break
    return beta, np.linalg.inv(hessian)


def predict(X: np.ndarray, beta: np.ndarray, cov: np.ndarray | None = None):
    """Probability with the Laplace (probit) correction, plus a 90% interval."""
    mu = X @ beta
    if cov is None:
        p = _sigmoid(mu)
        return p, p, p
    var = np.einsum("ij,jk,ik->i", X, cov, X)
    p = _sigmoid(mu / np.sqrt(1 + math.pi * var / 8))
    sd = np.sqrt(var)
    return p, _sigmoid(mu - 1.645 * sd), _sigmoid(mu + 1.645 * sd)


# ---------------------------------------------------------------- metrics


def brier(p, y) -> float:
    return float(np.mean((p - y) ** 2))


def log_loss(p, y) -> float:
    q = np.clip(p, 1e-6, 1 - 1e-6)
    return float(-np.mean(y * np.log(q) + (1 - y) * np.log(1 - q)))


def roc_auc(p, y) -> float | None:
    pos, neg = int(np.sum(y == 1)), int(np.sum(y == 0))
    if not pos or not neg:
        return None
    order = np.argsort(p, kind="mergesort")
    ranks = np.empty(len(p))
    sorted_p = p[order]
    i = 0
    while i < len(p):  # average ranks for ties
        j = i
        while j + 1 < len(p) and sorted_p[j + 1] == sorted_p[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2 + 1
        i = j + 1
    return float((np.sum(ranks[y == 1]) - pos * (pos + 1) / 2) / (pos * neg))


def precision_at(p, y, budget: float = REVIEW_BUDGET) -> float:
    k = max(1, int(round(budget * len(p))))
    top = np.argsort(-p, kind="mergesort")[:k]
    return float(np.mean(y[top]))


def calibration(p, y, bins: int = 5) -> list[dict]:
    order = np.argsort(p, kind="mergesort")
    out = []
    for chunk in np.array_split(order, min(bins, len(p))):
        if len(chunk):
            out.append({"predicted": round(float(np.mean(p[chunk])), 3), "observed": round(float(np.mean(y[chunk])), 3),
                        "n": int(len(chunk))})
    return out


def _metrics(p, y) -> dict:
    return {"brier": round(brier(p, y), 4), "log_loss": round(log_loss(p, y), 4),
            "auc": None if roc_auc(p, y) is None else round(roc_auc(p, y), 3),
            "precision_at_budget": round(precision_at(p, y), 3)}


def _folds(y: np.ndarray, k: int, seed: int = 7) -> list[np.ndarray]:
    """Stratified folds: each class is shuffled and dealt round-robin."""
    rng = np.random.default_rng(seed)
    folds = [[] for _ in range(k)]
    for cls in (0, 1):
        idx = np.flatnonzero(y == cls)
        rng.shuffle(idx)
        for n, i in enumerate(idx):
            folds[n % k].append(i)
    return [np.array(sorted(f)) for f in folds]


# ---------------------------------------------------------------- training and status


def train(now: datetime | None = None) -> dict:
    """Fit on every gold label that has a feature snapshot; evaluate out of fold; save the model."""
    now = now or utcnow()
    gold = [g for g in lab.gold_labels() if g.get("snapshot")]
    y = np.array([g["y"] for g in gold], dtype=float)
    n_ghost, n_genuine = int(np.sum(y == 1)), int(np.sum(y == 0))
    status = {"labels": len(gold), "ghost": n_ghost, "genuine": n_genuine, "min_labels": MIN_LABELS,
              "min_per_class": MIN_PER_CLASS}
    if len(gold) < MIN_LABELS or min(n_ghost, n_genuine) < MIN_PER_CLASS:
        status["trained"] = False
        status["reason"] = (f"Needs at least {MIN_LABELS} labelled postings with {MIN_PER_CLASS} of each class "
                            f"(now {n_ghost} not genuine, {n_genuine} genuine).")
        return status
    gold.sort(key=lambda g: g.get("at") or "")  # oldest first
    y = np.array([g["y"] for g in gold], dtype=float)
    X = design([g["snapshot"] for g in gold])
    mean, _ = _prior()
    cut = int(round(len(y) * (1 - TEST_SHARE)))
    train_y, test_y = y[:cut], y[cut:]
    temporal = len(set(train_y)) == 2 and len(set(test_y)) == 2 and len(test_y) >= 4
    if temporal:
        beta, cov = fit(X[:cut], train_y)
        eval_idx = np.arange(cut, len(y))
        pred_model = predict(X[cut:], beta, cov)[0]
        pred_base = np.full(len(test_y), np.mean(train_y))
        validation = f"trained on the {cut} earlier labels, tested on the {len(test_y)} later ones"
        k = 0
    else:
        k = max(2, min(5, n_ghost, n_genuine))
        eval_idx = np.arange(len(y))
        pred_model = np.zeros(len(y))
        pred_base = np.zeros(len(y))
        for fold in _folds(y, k):
            train_idx = np.setdiff1d(np.arange(len(y)), fold)
            beta, cov = fit(X[train_idx], y[train_idx])
            pred_model[fold] = predict(X[fold], beta, cov)[0]
            pred_base[fold] = np.mean(y[train_idx])
        validation = f"{k}-fold cross-validation (too few later labels of both kinds for a test on later cases)"
    y_eval = y[eval_idx]
    expert = predict(X[eval_idx], mean)[0]  # the prior alone: the expert score through the starting calibration
    beta, cov = fit(X, y)
    result = {
        "trained": True,
        "trained_at": now.isoformat(),
        **status,
        "folds": k,
        "validation": validation,
        "temporal": temporal,
        "tested_on": int(len(eval_idx)),
        "review_budget": REVIEW_BUDGET,
        "names": NAMES,
        "labels_text": {"intercept": "Intercept", **feats.LABELS},
        "beta": [round(float(b), 5) for b in beta],
        "cov": [[round(float(c), 7) for c in row] for row in cov],
        "prior_mean": [float(m) for m in mean],
        "prior_sd": [PRIOR_SD.get(n, DEFAULT_SD) for n in NAMES],
        "metrics": {"model": _metrics(pred_model, y_eval), "expert": _metrics(expert, y_eval),
                    "base_rate": _metrics(pred_base, y_eval)},
        "calibration": calibration(pred_model, y_eval),
        "calibration_expert": calibration(expert, y_eval),
    }
    model_path().write_text(json.dumps(result), encoding="utf-8")
    _LOADED.update(mtime=None)
    return result


_LOADED: dict = {"mtime": None, "model": None}


def load() -> dict | None:
    path = model_path()
    if not path.exists():
        return None
    mtime = path.stat().st_mtime
    if _LOADED["mtime"] != mtime:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("names") != NAMES:  # features changed since training: retrain first
            return None
        data["_beta"] = np.array(data["beta"])
        data["_cov"] = np.array(data["cov"])
        _LOADED.update(mtime=mtime, model=data)
    return _LOADED["model"]


def estimate(sp: ScoredPosting) -> dict | None:
    """The trained model's estimate for one posting, with its interval and strongest learned corrections."""
    m = load()
    if not m:
        return None
    vec = feats.vector(sp)
    x = np.array([[1.0, *[vec[n] for n in feats.NAMES]]])
    p, low, high = (float(v[0]) for v in predict(x, m["_beta"], m["_cov"]))
    contrib = []
    for i, name in enumerate(NAMES):
        if name in {"intercept", "expert_score"}:
            continue
        delta = (m["_beta"][i]) * x[0, i]
        if abs(delta) >= 0.05:
            contrib.append({"feature": name, "label": feats.LABELS[name], "logit": round(float(delta), 3)})
    contrib.sort(key=lambda c: -abs(c["logit"]))
    return {"p": round(p, 3), "low": round(low, 3), "high": round(high, 3), "labels": m["labels"],
            "trained_at": m["trained_at"], "corrections": contrib[:3]}
