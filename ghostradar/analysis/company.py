"""Employer-level signals from the local archive: track record, clusters, trends, events."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta

import math

from .. import db
from .. import prefs as user_prefs
from ..models import EVENT_KINDS, Communication, CompanyEvent, CompanySignals
from ..sources import news
from ..util import normalize_title, parse_date, parse_datetime
from .baselines import baseline_for

# Beta prior for size-adjusted rates: pulls employers with few postings towards
# the archive-wide rate (the report's empirical-Bayes recommendation).
PRIOR_STRENGTH = 10.0
DEFAULT_PRIOR = 0.15

# How much each grade counts towards an employer's ghost-risk share: elevated and high fully,
# moderate partly, so employer-wide evidence that lifts every posting to moderate still shows.
GRADE_WEIGHTS = {"moderate": 0.4, "elevated": 1.0, "high": 1.0}

# Hiring capacity: how many openings an employer can plausibly have at once.
# Openings at a time ≈ headcount × (replacement rate + growth) × time to fill / 365.
REPLACEMENT_RATE = 0.15  # assumed share of staff replaced each year (judgement; sector rates differ)
FILL_DAYS = 86  # IAB 2025: days from the start of a search to the start of work
ASSUMED_GROWTH = 0.20  # generous default when no earlier headcount is known


def shrunk_rate(k: int, n: int, prior: float = DEFAULT_PRIOR, strength: float = PRIOR_STRENGTH) -> float:
    alpha, beta = prior * strength, (1 - prior) * strength
    return (alpha + k) / (alpha + beta + n)


def weighted_flags(grades) -> float:
    """Flag count for the employer grade: elevated and high postings count fully, moderate ones partly."""
    return sum(GRADE_WEIGHTS.get(g, 0.0) for g in grades)


def grade_from_share(share: float, n: int) -> tuple[str, str]:
    """Coarse A–D grade for an employer's size-adjusted ghost-risk share."""
    if n == 0:
        return "–", "No postings analysed yet."
    grade = "A" if share < 0.10 else "B" if share < 0.25 else "C" if share < 0.45 else "D"
    note = f"Ghost-risk share {share:.0%} across {n} job{'s' if n != 1 else ''}."
    if n < 10:
        note += " Few jobs, so the grade is uncertain."
    return grade, note


def plausible_openings(headcount: int, growth: float | None) -> float:
    """Openings an employer of this size can plausibly have at once."""
    g = ASSUMED_GROWTH if growth is None else max(growth, 0.0)
    return headcount * (REPLACEMENT_RATE + g) * FILL_DAYS / 365


def _employer_type(company: dict | None, rows: list[dict]) -> str | None:
    if company and company.get("employer_type"):
        return company["employer_type"]
    agency = sum(1 for r in rows if r.get("agency_flag") == 1)
    if rows and agency / len(rows) >= 0.5:
        return "agency"
    return None


def signals(company_id: int, now: datetime, events: list[dict] | None = None) -> CompanySignals:
    company = db.get_company(company_id)
    rows = db.company_posting_rows(company_id, light=True)
    employer_rows = [r for r in rows if r["channel"] == "employer"]
    active = [r for r in employer_rows if r["status"] == "active"] or [r for r in rows if r["status"] == "active"]
    sig = CompanySignals(company_id=company_id, name=company["name"] if company else None)
    sig.employer_type = _employer_type(company, rows)
    sig.active_postings = len(active)
    # one job can have copies on several platforms: count distinct jobs for capacity
    sig.open_jobs = len({r.get("cluster_id") or r["id"] for r in active})
    sig.headcount = company.get("headcount") if company else None
    if sig.headcount:
        sig.postings_per_100 = round(100.0 * len(active) / max(1, sig.headcount), 1)
    if company:
        sig.hiring_practice = company.get("hiring_practice") or None
        sig.practice_note = company.get("practice_note") or None
        sig.headcount_prev = company.get("headcount_prev") or None
        sig.funding_amount = company.get("funding_amount") or None
    if sig.headcount:
        if sig.headcount_prev:
            sig.growth = round((sig.headcount - sig.headcount_prev) / sig.headcount_prev, 3)
        sig.growth_assumed = sig.growth is None
        sig.plausible_openings = round(plausible_openings(sig.headcount, sig.growth), 1)
        sig.capacity_ratio = round(sig.open_jobs / max(sig.plausible_openings, 0.5), 2)

    first_seen = [parse_datetime(r["first_seen"]) for r in rows if r.get("first_seen")]
    if first_seen:
        sig.tracked_days = (now - min(first_seen)).days

    # departments and coherent clusters: ≥3 distinct roles opened in the last 90 days
    dept_counts: Counter[str] = Counter()
    recent_titles: dict[str, set[str]] = defaultdict(set)
    for r in active:
        dept = (r.get("department") or "").strip()
        if not dept:
            continue
        dept_counts[dept] += 1
        start = parse_datetime(r.get("posted_at")) or parse_datetime(r["first_seen"])
        if start and (now - start).days <= 90:
            recent_titles[dept].add(normalize_title(r.get("title")))
    sig.departments = dict(dept_counts.most_common())
    sig.coherent_departments = sorted(d for d, titles in recent_titles.items() if len(titles) >= 3)

    # slow-close rate: closed employer postings that ran far beyond their occupation's norm
    closed = [r for r in employer_rows if r["status"] == "removed" and r.get("removed_at")]
    slow = 0
    for r in closed:
        start = parse_datetime(r.get("posted_at")) or parse_datetime(r["first_seen"])
        end = parse_datetime(r["removed_at"])
        if not start or not end:
            continue
        expected = baseline_for(r.get("title") or "", "", r.get("region")).expected_days or 100
        if (end - start).days > 2.5 * expected:
            slow += 1
    if closed:
        sig.slow_close_n = len(closed)
        sig.slow_close_k = slow
        sig.slow_close_rate = round(shrunk_rate(slow, len(closed)), 3)

    # likely filled: closures (any channel, one per job, inside the history window) within the typical window.
    # A removal does not prove a hire, so this is a proxy and is shown with its count.
    since = user_prefs.since(now)
    fills: dict = {}
    for r in rows:
        end = parse_datetime(r.get("removed_at"))
        if r["status"] != "removed" or not end or end < since:
            continue
        start = parse_datetime(r.get("posted_at")) or parse_datetime(r["first_seen"])
        if not start:
            continue
        expected = baseline_for(r.get("title") or "", "", r.get("region")).expected_days or 100
        key = r.get("cluster_id") or r["id"]
        fills[key] = fills.get(key, False) or (end - start).days <= expected
    if fills:
        sig.fill_n = len(fills)
        sig.fill_k = sum(1 for v in fills.values() if v)
        sig.fill_rate = round(sig.fill_k / sig.fill_n, 3)

    # board unchanged: tracked for 90+ days with no new and no removed employer postings
    runs = db.feed_runs(company_id)
    if runs and employer_rows:
        tracked_since = parse_datetime(runs[0]["run_at"])
        last_change = max(
            [parse_datetime(r["first_seen"]) for r in employer_rows]
            + [parse_datetime(r["removed_at"]) for r in employer_rows if r.get("removed_at")]
        )
        if tracked_since and last_change and (now - tracked_since).days >= 90:
            sig.board_unchanged_days = (now - max(last_change, tracked_since)).days

    # trend: active postings now vs. 60 days ago (needs at least 60 days of tracking)
    if sig.tracked_days >= 60 and employer_rows:
        cutoff = now - timedelta(days=60)
        then = sum(
            1
            for r in employer_rows
            if parse_datetime(r["first_seen"]) <= cutoff
            and (not r.get("removed_at") or parse_datetime(r["removed_at"]) > cutoff)
        )
        nowc = len(active)
        if then == 0:
            sig.posting_trend = "rising" if nowc else "flat"
        else:
            change = (nowc - then) / then
            sig.posting_trend = "rising" if change > 0.25 else "falling" if change < -0.25 else "flat"

    for ev in events if events is not None else db.company_events(company_id):
        published = parse_datetime(ev.get("published_at"))
        if published and published < since:  # history window: one year at most
            continue
        sig.events.append(
            CompanyEvent(
                kind=ev["kind"] if ev["kind"] in {"distress", "funding", "growth", "contract", "other"} else "other",
                title=ev.get("title") or "",
                url=ev.get("url"),
                published_at=published,
                source=ev.get("source"),
                subtype=ev.get("subtype"),
                id=ev.get("id"),
            )
        )
    sig.contracts_12m = sum(1 for e in sig.events if e.kind == "contract")

    # last funding round: the user's entry, or the latest funding headline
    funding: list[tuple] = []
    noted = parse_date(company.get("funding_date")) if company else None
    if noted:
        funding.append((noted, "your note"))
    funding += [(e.published_at.date(), "news") for e in sig.events if e.kind == "funding" and e.published_at]
    if funding:
        sig.funding_date, sig.funding_source = max(funding, key=lambda x: x[0])
        sig.funding_months = max(0, (now.date() - sig.funding_date).days // 30)
        if sig.funding_source == "news" and not sig.funding_amount:
            latest = max((e for e in sig.events if e.kind == "funding" and e.published_at), key=lambda e: e.published_at)
            sig.funding_amount = news.funding_details(latest.title)

    # application outcomes reported for this employer (inside the history window)
    reports = [r for r in (db.report_rows(company=company["name"]) if company else [])
               if (parse_datetime(r.get("applied_on")) or parse_datetime(r.get("created_at")) or now) >= since]
    sig.communication = communication(reports, now) if reports else None
    if reports:
        counts = Counter(r.get("response") or "unknown" for r in reports)
        silent = 0
        for r in reports:
            applied = parse_datetime(r.get("applied_on"))
            if r.get("response") == "none" and applied and (now - applied).days >= 30:
                silent += 1
        sig.reports = {
            "reports": len(reports),
            "replied": len(reports) - counts["none"] - counts["unknown"],
            "no_response": counts["none"],
            "no_response_30d": silent,
            "auto_reject": counts["auto_reject"],
            "reject": counts["reject"],
            "internal": counts["internal"],
            "interviews": counts["interview"] + counts["offer"],
            "offers": counts["offer"],
        }
    return sig


def crowd_for_posting(posting_id: int | None, now: datetime) -> dict:
    """Outcome reports for this exact posting (employer-wide outcomes live in CompanySignals.reports)."""
    rows = db.report_rows(posting_id=posting_id) if posting_id else []
    if not rows:
        return {}
    silent = 0
    for r in rows:
        applied = parse_datetime(r.get("applied_on"))
        if r.get("response") == "none" and applied and (now - applied).days >= 30:
            silent += 1
    return {
        "reports": len(rows),
        "no_response_30d": silent,
        "interviews": sum(1 for r in rows if r.get("response") in {"interview", "offer"}),
    }


REPLY_DAYS = 30  # outcome definition: a substantive reply within 30 days (a rejection counts as a reply)


def _wilson(k: int, n: int, z: float = 1.645) -> tuple[float, float]:
    """90% Wilson interval for a share k/n."""
    if not n:
        return 0.0, 1.0
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def communication(reports: list[dict], now: datetime) -> Communication:
    """Candidate-ghosting risk from your own applications to one employer.

    Each application counts once at the stage it reached. Replied: any substantive answer, including rejections.
    Silent: no answer 30 days after applying, after the promised date, or after the interview. Unresolved: still
    inside those 30 days. Withdrawn applications are left out.
    """
    c = Communication()
    for r in reports:
        stage = r.get("stage") or ("interview" if r.get("response") in {"interview", "offer"} else "application")
        counts = c.by_stage.setdefault(stage, {"replied": 0, "silent": 0, "unresolved": 0})
        if r.get("withdrawn"):
            c.withdrawn += 1
            continue
        c.unanswered_followups += int(r.get("followups") or 0)
        response = r.get("response")
        applied = parse_datetime(r.get("applied_on")) or parse_datetime(r.get("created_at")) or now
        promised = parse_datetime(r.get("promised_by"))
        if response in {"auto_reject", "reject", "internal", "offer"}:
            outcome = "replied"  # a decision, including a rejection, is a substantive reply
        elif response == "interview" and stage != "interview":
            outcome = "replied"  # invited to interview: the application was answered
        else:
            # waiting at this stage: after an interview the clock starts at the invitation, otherwise at applying
            started = applied
            if stage == "interview" and r.get("days_to_response") is not None:
                started = applied + timedelta(days=int(r["days_to_response"]))
            overdue_promise = bool(promised and now > promised)
            if overdue_promise:
                c.missed_promises += 1
            outcome = "silent" if overdue_promise or (now - started).days >= REPLY_DAYS else "unresolved"
        counts[outcome] += 1
        if outcome == "replied":
            c.replied += 1
        elif outcome == "silent":
            c.silent += 1
        else:
            c.unresolved += 1
    c.n = c.replied + c.silent
    if c.n:
        c.share_silent = round(c.silent / c.n, 3)
        c.low, c.high = (round(v, 3) for v in _wilson(c.silent, c.n))
    c.confidence = "high" if c.n >= 15 else "medium" if c.n >= 5 else "low"
    if c.n < 2:
        c.level = "unknown"
    elif c.share_silent >= 0.6 and c.n >= 3:
        c.level = "high"
    elif c.share_silent >= 0.3:
        c.level = "medium"
    else:
        c.level = "low"
    extra = []
    if c.missed_promises:
        extra.append(f"{c.missed_promises} promised date{'s' if c.missed_promises != 1 else ''} missed")
    if c.unanswered_followups:
        extra.append(f"{c.unanswered_followups} follow-up{'s' if c.unanswered_followups != 1 else ''} unanswered")
    if c.unresolved:
        extra.append(f"{c.unresolved} still within 30 days")
    if c.n:
        c.text = (f"{c.silent} of {c.n} of your applications got no reply within 30 days"
                  + (f"; {', '.join(extra)}" if extra else "") + ".")
    else:
        c.text = ("No resolved applications yet" + (f" ({', '.join(extra)})" if extra else "") + ".")
    return c


def event_label(subtype: str | None) -> str | None:
    return EVENT_KINDS.get(subtype or "", (None, None))[1]
