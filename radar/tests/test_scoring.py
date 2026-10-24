from datetime import datetime, timedelta, timezone

from ghostradar.analysis import baselines, scoring, text
from ghostradar.models import CompanyEvent, CompanySignals, Features, OriginInfo, Posting, RepostInfo, UserObservations

NOW = datetime(2026, 10, 24, tzinfo=timezone.utc)
DESC = "Wir suchen eine Softwareentwicklerin (m/w/d) für unser Backend-Team in Berlin. Python, Go und AWS."


def make(title="Softwareentwickler (m/w/d)", desc=DESC, days=30, employer=None, **kw):
    p = Posting(source="test", source_id="1", title=title, description=desc, company=employer,
                posted_at=NOW - timedelta(days=days))
    base = baselines.baseline_for(title, desc)
    f = Features(now=NOW, text=text.analyse(title, desc, employer), baseline=base, first_published=p.posted_at,
                 live_days=days, excess_ratio=round(days / base.expected_days, 2), **kw)
    return p, f


def test_fresh_posting_is_low_and_capped():
    p, f = make(days=5)
    s = scoring.score(p, f)
    assert s.grade == "low"
    assert s.risk <= scoring.YOUNG_CAP


def test_raw_age_alone_cannot_reach_high():
    p, f = make(days=900)
    s = scoring.score(p, f)
    assert s.grade != "high"  # one strong signal is capped below the highest grade
    assert any(r.signal == "excess_lifetime" and r.points > 0 for r in s.reasons)


def test_two_strong_signals_reach_high():
    p, f = make(days=500, origin=OriginInfo(status="removed", feed="greenhouse", removed_days=40),
                repost=RepostInfo(instances=4, cosmetic=3, total_live_days=500, history_days=200))
    s = scoring.score(p, f)
    assert s.grade == "high"
    stale = next(t for t in s.types if t.key == "stale")
    assert stale.score >= 0.5


def test_talent_pool_routes_to_pool_type():
    p, f = make(title="Initiativbewerbung (m/w/d)", desc="Bewirb dich initiativ für unseren Talentpool.", days=60)
    s = scoring.score(p, f)
    pool = next(t for t in s.types if t.key == "pool")
    assert pool.score >= 0.8
    assert any(r.signal == "evergreen" for r in s.reasons)


def test_employer_listing_and_interview_lower_risk():
    p, f = make(days=200, origin=OriginInfo(status="present", feed="personio"),
                user=UserObservations(applied_on=(NOW - timedelta(days=10)).date(), response="interview"))
    s = scoring.score(p, f)
    lowers = {r.signal for r in s.reasons if r.direction == "lowers"}
    assert {"origin_present", "own_interview"} <= lowers


def test_distress_news_raises_frozen_type():
    company = CompanySignals(active_postings=5, events=[CompanyEvent(kind="distress", title="Firma streicht 300 Stellen",
                                                                      published_at=NOW - timedelta(days=20))])
    p, f = make(days=100, company=company)
    s = scoring.score(p, f)
    frozen = next(t for t in s.types if t.key == "frozen")
    assert frozen.score >= 0.5


def test_missing_salary_is_not_scored_for_it_roles():
    p, f = make(days=60)
    s = scoring.score(p, f)
    missing = next(r for r in s.reasons if r.signal == "missing_salary")
    assert missing.points == 0


def test_scam_flag_is_separate_from_risk():
    p, f = make(title="Paketagent", desc="Pakete annehmen und weiterleiten. Startgebühr 50 Euro.", days=3)
    s = scoring.score(p, f)
    assert s.scam.flag
    assert s.effort_tier == "skip"


def test_closed_posting():
    p = Posting(source="test", source_id="1", title="Job")
    s = scoring.score(p, Features(now=NOW, is_live=False, closed_reason="gone"))
    assert s.grade == "closed" and s.effort_tier == "skip"


def test_competition_uses_iab_baseline():
    p, f = make(days=40, user=UserObservations(applicant_count=200))
    s = scoring.score(p, f)
    assert s.competition.level == "very_high"  # IT: about 40 applications per hire


def test_your_internal_first_note_counts_even_for_fresh_postings():
    company = CompanySignals(name="Example AG", hiring_practice="internal_first", practice_note="own applications 2025")
    p, f = make(days=5, company=company)
    s = scoring.score(p, f)
    note = next(r for r in s.reasons if r.signal == "practice_internal")
    assert note.points > 0 and "your note" in note.label
    assert s.grade == "moderate"  # employer-wide evidence is not capped for young postings
    assert next(t for t in s.types if t.key == "pre_decided").score >= 0.7
    assert s.effort_tier == "light"  # internal favourite: keep the application short
    assert any("your own note" in c for c in s.caveats)
    plain = scoring.score(*make(days=5))
    assert plain.grade == "low"


def test_one_note_alone_never_reaches_the_highest_grade():
    s = scoring.score(*make(days=5, company=CompanySignals(hiring_practice="internal_first")))
    assert s.grade != "high"


def test_outcome_record_internal_hires_and_no_interviews():
    reports = {"reports": 6, "auto_reject": 3, "reject": 1, "internal": 2, "interviews": 0, "no_response": 0}
    p, f = make(days=10, company=CompanySignals(name="Example AG", reports=reports))
    s = scoring.score(p, f)
    signals = {r.signal for r in s.reasons}
    assert {"outcome_internal", "outcome_no_interviews"} <= signals
    assert s.grade == "moderate" and s.effort_tier == "light"
    noted = CompanySignals(name="Example AG", reports=reports, hiring_practice="internal_first")
    assert scoring.score(*make(days=10, company=noted)).grade == "elevated"  # your note plus your outcomes
    good = {"reports": 4, "reject": 2, "interviews": 2}
    s2 = scoring.score(*make(days=10, company=CompanySignals(reports=good)))
    assert any(r.signal == "outcome_interviews" and r.points < 0 for r in s2.reasons)


def test_openings_beyond_capacity_and_shrinking_headcount():
    from ghostradar.analysis import company as company_analysis

    plausible = company_analysis.plausible_openings(40, -0.1)
    company = CompanySignals(headcount=40, headcount_prev=45, growth=-0.111, open_jobs=12,
                             plausible_openings=round(plausible, 1), capacity_ratio=round(12 / plausible, 2))
    s = scoring.score(*make(days=30, company=company))
    signals = {r.signal for r in s.reasons}
    assert {"capacity", "shrinking"} <= signals
    assert next(t for t in s.types if t.key == "fictitious").score >= 0.5


def test_contingent_project_wording_routes_to_pool():
    desc = "Für ein potenzielles Projekt bei unserem Kunden suchen wir, vorbehaltlich der Auftragsvergabe, eine Projektleitung."
    s = scoring.score(*make(title="Projektleiter (m/w/d)", desc=desc, days=30))
    assert any(r.signal == "contingent" for r in s.reasons)
    assert next(t for t in s.types if t.key == "pool").score >= 0.5


def test_competition_has_absolute_floors_and_lowers_effort():
    p, f = make(days=10, user=UserObservations(applicant_count=100))
    s = scoring.score(p, f)
    assert s.competition.level == "high" and s.competition.per_hire == 40
    p, f = make(days=10, user=UserObservations(applicant_count=260))
    s = scoring.score(p, f)
    assert s.competition.level == "very_high"
    assert s.effort_tier == "standard"  # a low ghost-risk job, but the odds call for less effort
    care = scoring.score(*make(title="Pflegefachkraft (m/w/d)", desc="Pflege auf Station.", days=10,
                               user=UserObservations(applicant_count=20)))
    assert care.competition.level == "high"  # about 8 applications per hire are typical in care


def test_internal_candidate_outcome_for_this_job():
    p, f = make(days=40, user=UserObservations(applied_on=(NOW - timedelta(days=20)).date(), response="internal"))
    s = scoring.score(p, f)
    assert any(r.signal == "own_internal" for r in s.reasons)
    assert next(t for t in s.types if t.key == "pre_decided").score >= 0.8


def test_age_counts_from_the_typical_time_on():
    p, f = make(days=10)
    expected = f.baseline.expected_days
    s = scoring.score(*make(days=int(expected * 1.2)))
    age = next(r for r in s.reasons if r.signal == "excess_lifetime")
    assert age.points == 6
    strict_p, strict_f = make(days=int(expected * 0.8), age_start=0.75)
    assert next(r for r in scoring.score(strict_p, strict_f).reasons if r.signal == "excess_lifetime").points == 6
    assert scoring.score(*make(days=int(expected * 2.1))).grade == "moderate"  # 2× the norm is moderate on its own


def test_applicant_bounds_and_few_applicants_on_old_postings():
    p, f = make(days=300, user=UserObservations(applicant_count=25, applicant_bound="first"))
    s = scoring.score(p, f)
    assert any(r.signal == "applicants_few_old" and r.points > 0 for r in s.reasons)
    assert s.competition.level == "normal" and "fewer than 25" in s.competition.text.lower()
    care = scoring.score(*make(title="Pflegefachkraft (m/w/d)", desc="Pflege auf Station.", days=300,
                               user=UserObservations(applicant_count=4)))
    assert any(r.signal == "applicants_few" and r.points < 0 for r in care.reasons)  # shortage: hard to fill


def test_chance_combines_competition_rate_and_employer_record():
    s = scoring.score(*make(days=2, user=UserObservations(applicant_count=150)))
    assert s.competition.rate_per_day == 75 and s.competition.chance in {"low", "very_low"}
    noted = CompanySignals(hiring_practice="internal_first")
    s2 = scoring.score(*make(days=5, company=noted, user=UserObservations(applicant_count=30)))
    assert s2.competition.chance == "fair" and "internal candidates usually get these jobs" in s2.competition.why
    assert scoring.score(*make(days=5)).competition.chance == "unknown"


def test_pending_approval_and_demand_evidence():
    desc = DESC + " Die Stelle ist vorbehaltlich der Budgetfreigabe zu besetzen."
    s = scoring.score(*make(desc=desc, days=40))
    assert any(r.signal == "pending_approval" and r.points > 0 for r in s.reasons)
    assert any("approved" in t for t in s.verify_tips)
    company = CompanySignals(contracts_12m=3, events=[CompanyEvent(kind="growth", subtype="new_starters", source="your note",
                                                                   title="Confirmed new starters in the team",
                                                                   published_at=NOW - timedelta(days=10))])
    s2 = scoring.score(*make(days=40, company=company))
    assert {"contracts", "new_starters"} <= {r.signal for r in s2.reasons if r.points < 0}


def test_shrinking_alone_is_not_scored():
    company = CompanySignals(headcount=90, headcount_prev=100, growth=-0.1, open_jobs=5)
    shrink = next(r for r in scoring.score(*make(days=30, company=company)).reasons if r.signal == "shrinking")
    assert shrink.points == 0
    company.events = [CompanyEvent(kind="distress", title="Stellenabbau angekündigt", published_at=NOW - timedelta(days=30))]
    shrink = next(r for r in scoring.score(*make(days=30, company=company)).reasons if r.signal == "shrinking")
    assert shrink.points > 0


def test_communication_record_reaches_the_advice():
    from ghostradar.analysis.company import communication

    reports = [{"response": "none", "applied_on": "2026-08-01"}, {"response": "none", "applied_on": "2026-07-01"},
               {"response": "auto_reject", "applied_on": "2026-09-01"},
               {"response": "interview", "stage": "interview", "applied_on": "2026-06-01", "days_to_response": 5},
               {"response": "none", "applied_on": "2026-10-20"}, {"response": "none", "applied_on": "2026-05-01", "withdrawn": 1}]
    c = communication(reports, NOW)
    assert (c.replied, c.silent, c.unresolved, c.withdrawn) == (1, 3, 1, 1)
    assert c.level == "high" and c.low < c.share_silent < c.high
    s = scoring.score(*make(days=5, company=CompanySignals(communication=c)))
    assert s.communication.level == "high" and "did not answer 3 of 4" in s.advice
