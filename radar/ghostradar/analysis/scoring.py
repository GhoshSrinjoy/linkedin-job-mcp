"""Ghost-risk scoring with transparent, hand-set weights.

Weights follow the working signal set in reports/Ghost job signals in Germany.md.
Design rules taken from that report:
- unknown data counts as neutral;
- young listings are capped (no signal has had time to show);
- no single signal can produce the highest grade on its own;
- the output is an evaluation of observable facts per ghost *type*, never a
  claim about intent; scams are a separate filter outside the score.
Until audited labels exist these are judgements, not calibrated probabilities.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from .company import event_label
from ..models import (
    Communication,
    Competition,
    CoverageItem,
    Features,
    Posting,
    Reason,
    ScamCheck,
    Score,
    TypeIndicator,
)

BASE_POINTS = 10
YOUNG_DAYS = 21
YOUNG_CAP = 25
SINGLE_SIGNAL_CAP = 64

TYPE_LABELS = {
    "stale": "Possibly filled or abandoned",
    "pool": "Candidate pool",
    "pre_decided": "Internal favourite",
    "frozen": "Hiring frozen",
    "fictitious": "CV collection",
}

GRADE_LABELS = {
    "low": "Low ghost-risk",
    "moderate": "Moderate ghost-risk",
    "elevated": "Elevated ghost-risk",
    "high": "High ghost-risk",
    "unknown": "Not enough data",
    "closed": "No longer online",
}

EV_LIFETIME = "German BA/IAB baselines and phantom-vacancy research; not validated against hiring outcomes"
EV_REPOST = "Cited by 24 of 31 sources; theory says some reposting is genuine"
EV_ORIGIN = "Mechanism documented by the US Congressional Research Service and the BA; not validated"
EV_EXPIRY = "Follows from Google's job-posting rules and the BA vacancy clock"
EV_EMPLOYER = "Ghost-like listings concentrate in few employers (descriptive data)"
EV_DISTRESS = "Practitioners agree; untested"
EV_POOL = "The BA says agency registrations partly serve 'Portfoliobildung'"
EV_PREDECIDED = "Works-council and public-sector advertising duties (mechanism); prevalence unknown"
EV_SALARY = "Weak in Germany: only 12–24% of ads state pay"
EV_TEXT = "No evidence links wording to hiring outcomes"
EV_APPLICANTS = "Suggestive (IAB: 16 applications per hire in 2025)"
EV_BADGES = "Weak: automatic rejections count as responses"
EV_USER = "Your own observation"
EV_NOTE = ("Your own knowledge, not observed by the radar. Mechanism: works councils can require internal "
           "advertisement first (§ 93 BetrVG)")
EV_OUTCOMES = ("Your reported application outcomes. Silence alone is a weak label: 63.5% of German applicants "
               "got no reply at least once")
EV_CAPACITY = ("Report: postings versus expected hires, medium weight when far above, especially with flat "
               "headcount; replacement rate and time to fill are assumptions")
EV_GROWTH = "Headcount growth predicts fast genuine filling (validated link); shrinking while hiring is suggestive"
EV_FUNDING = "Funding explains drift between posting volume and headcount (report); suggestive"
EV_CONTINGENT = ("Bid and grant hiring: roles advertised before the contract or funding is secured (mechanism); "
                 "prevalence unknown")
EV_APPROVAL = ("An unapproved position can be postponed or cancelled (uncertainty research); only explicit wording "
               "counts, undisclosed approval stays unknown")
EV_DEMAND = ("Demand that could justify the hire: awarded contracts, funded projects, confirmed new starters "
             "(recruiting-intensity research); a funded project says more than a growth announcement")
EV_TURNOVER = "IAB: shrinking establishments still recruit to replace leavers, so shrinking alone is not a signal"

SOURCE_LABELS = {
    "personio": "Personio", "greenhouse": "Greenhouse", "lever": "Lever", "smartrecruiters": "SmartRecruiters",
    "ashby": "Ashby", "recruitee": "Recruitee", "workday": "Workday", "jsonld": "careers-page",
    "page": "web-page", "arbeitnow": "Arbeitnow", "adzuna": "Adzuna", "manual": "pasted",
    "ba": "the Bundesagentur board", "linkedin": "LinkedIn", "jsearch": "Google for Jobs",
}


def _src(name: str | None) -> str:
    return SOURCE_LABELS.get(name or "", name or "careers")


# segments where pay disclosure is common, so a missing salary says a little more
PAY_COMMON_GROUPS = {"541", "513", "521", "525", "633", "632", "293", "621", "623", "531", "832"}
# IAB 2025 applications per hire: IT and science services 40, personal services 8, overall 16
# (KldB groups: 41–43 science and IT; 81–83 health, care, social and education, 29 food, 54 cleaning,
# 63 hospitality count as personal services)
APPS_PER_HIRE = {"43": 40, "41": 40, "42": 40, "81": 8, "82": 8, "83": 8, "54": 8, "63": 8, "29": 8}


@dataclass
class _Acc:
    reasons: list[Reason] = field(default_factory=list)
    types: dict[str, float] = field(default_factory=lambda: {k: 0.0 for k in TYPE_LABELS})
    type_notes: dict[str, list[str]] = field(default_factory=lambda: {k: [] for k in TYPE_LABELS})
    points: float = 0.0
    employer_points: float = 0.0  # employer-wide evidence; not capped for young postings
    strong_raises: int = 0

    def add(
        self,
        signal: str,
        label: str,
        fact: str,
        points: float = 0.0,
        strength: str = "low",
        evidence: str = "",
        types: dict[str, float] | None = None,
        direction: str | None = None,
        employer: bool = False,
    ) -> None:
        if direction is None:
            direction = "raises" if points > 0 else "lowers" if points < 0 else ("routes" if types else "info")
        self.points += points
        if employer:
            self.employer_points += points
        if points >= 8:
            self.strong_raises += 1
        for key, value in (types or {}).items():
            self.types[key] += value
            if value > 0:
                self.type_notes[key].append(label)
        self.reasons.append(
            Reason(
                signal=signal,
                label=label,
                fact=fact,
                direction=direction,  # type: ignore[arg-type]
                points=round(points, 1),
                strength=strength,  # type: ignore[arg-type]
                evidence=evidence,
                types=[k for k, v in (types or {}).items() if v > 0],
            )
        )


def _d(value) -> str:
    return value.strftime("%d.%m.%Y") if value else "?"


def score(p: Posting, f: Features) -> Score:
    acc = _Acc()
    t = f.text
    caveats: list[str] = []
    now = f.now
    user = f.user
    company = f.company

    if not f.is_live:
        return _closed(f)
    if f.outside_germany:
        caveats.append("This job is located outside Germany, so the German vacancy-duration baselines are only indicative.")

    # ------------------------------------------------------------ lifecycle
    ratio = f.excess_ratio
    base = f.baseline
    occupation = base.kldb_label or "this occupation"
    if f.live_days is None:
        caveats.append("Publication date unknown, so posting age could not be assessed.")
    elif t.apprenticeship and not f.start_overrun_days:
        acc.add(
            "apprenticeship",
            "Apprenticeship cycle",
            "Apprenticeships are advertised many months before the start date, so age is not scored.",
            evidence=EV_LIFETIME,
        )
    elif t.evergreen:
        acc.add(
            "standing_entry",
            "Standing talent-pool entry",
            f"Online for {f.live_days} days. Standing talent-pool or speculative-application entries are "
            "meant to stay up, so their age is not scored.",
            evidence=EV_LIFETIME,
        )
    elif ratio is not None and base.expected_days:
        plus = "+" if f.first_published_is_lower_bound else ""
        tail = f.empirical_tail
        copies = f.repost.instances
        fact = (
            f"Online for {f.live_days}{plus} days (since {_d(f.first_published)}"
            f"{f', counted across all {copies} copies of this job' if copies > 1 else ''}). "
            f"About {base.expected_days} days is usual for {occupation}, so this is {ratio:.1f}× that."
        )
        if tail is not None:
            fact += f" Only {tail:.0%} of comparable jobs stayed online this long."
        if (tail is not None and tail <= 0.05) or ratio >= 3:
            pts, strength, share = 26.0, "high", 0.5
        elif (tail is not None and tail <= 0.10) or ratio >= 2:
            pts, strength, share = 18.0, "medium", 0.35
        elif ratio >= 1.5:
            pts, strength, share = 12.0, "medium", 0.25
        elif ratio >= f.age_start:
            pts, strength, share = 6.0, "low", 0.1
        else:
            pts, strength, share = 0.0, "none", 0.0
        if pts:
            if f.is_agency or t.evergreen:
                acc.add("excess_lifetime", "Long-running pool posting", fact, pts * 0.5, strength, EV_LIFETIME,
                        {"pool": share})
            else:
                acc.add("excess_lifetime", "Online much longer than typical", fact, pts, strength, EV_LIFETIME,
                        {"stale": share, "fictitious": share * 0.3})
        else:
            acc.add("excess_lifetime", "Age within the normal range", fact, 0.0, "none", EV_LIFETIME)
        if base.note:
            caveats.append(base.note)

    rep = f.repost
    refreshes = rep.cosmetic + rep.date_refreshes
    if refreshes:
        pts = 10.0 if refreshes == 1 else 16.0 if refreshes == 2 else 22.0
        if rep.regular_cadence:
            pts += 5
        acc.add(
            "cosmetic_repost",
            "Reposted with unchanged text",
            f"Reappeared {refreshes}× with near-identical text under a new ID or a refreshed date"
            f"{' on a regular cadence' if rep.regular_cadence else ''} (tracked since {_d(rep.first_start)}).",
            pts,
            "high" if pts >= 16 else "medium",
            EV_REPOST,
            {"stale": 0.2, "pool": 0.3, "fictitious": 0.1},
        )
    elif user and user.reposted_label:
        acc.add("reposted_label", "Platform shows 'Reposted'",
                "You saw a 'Reposted' label on the job platform.", 8.0, "medium", EV_USER,
                {"pool": 0.2, "stale": 0.1})
    if rep.republished_days and not refreshes:
        refreshes = 1
        acc.add("republished", "Re-published elsewhere",
                f"A copy on {_src(rep.republished_on)} appeared {rep.republished_days} days after the same job was first "
                f"published on {_src(rep.first_seen_on)}; the older copy started the clock.",
                10.0, "medium", EV_REPOST, {"stale": 0.2, "pool": 0.3})
    if rep.parallel_copies >= 2:
        acc.add("parallel_copies", "Duplicate ads at the same time",
                f"{rep.parallel_copies} copies of this job are live on {_src(rep.parallel_source)} at the same time.",
                4.0, "low", "Multiposting is common for pools and agencies; not validated", {"pool": 0.2})
    if rep.refreshed_days and ratio is not None and ratio >= 1.5:
        acc.add("refreshed", "Kept looking fresh",
                f"The source shows a recent update to an ad first published {rep.refreshed_days} days ago.",
                4.0, "low", EV_REPOST, {"stale": 0.1, "pool": 0.1})
    if rep.new_requisition:
        acc.add("new_requisition", "Re-scoped after a gap",
                f"Content changed substantially after a gap ({rep.new_requisition}×): consistent with a "
                "genuinely re-opened search.", -4.0, "low", EV_REPOST)
    if rep.uncertain:
        acc.add("repost_uncertain", "Unclassified reappearance",
                f"{rep.uncertain} reappearance(s) could not be classified as cosmetic or new.", 0.0, "none", EV_REPOST)

    origin = f.origin
    if origin.status == "removed":
        days = origin.removed_days or 0
        pts = 26.0 if days >= 14 else 16.0 if days >= 3 else 8.0
        acc.add("origin_removed", "Gone from the employer's own site",
                f"The employer's {_src(origin.feed)} feed dropped this job about {days} days ago "
                "(confirmed by two checks), but this copy is still online.",
                pts, "high" if pts >= 16 else "medium", EV_ORIGIN, {"stale": 0.6})
    elif origin.status == "not_found":
        acc.add("origin_not_found", "Not on the employer's own site",
                f"No matching job in the employer's {_src(origin.feed)} feed ({origin.feed_jobs} open jobs, "
                f"checked {_d(origin.checked_at)}).",
                10.0, "medium", EV_ORIGIN, {"stale": 0.2, "fictitious": 0.2})
    elif origin.status == "present":
        acc.add("origin_present", "Also on the employer's own site",
                f"Listed in the employer's {_src(origin.feed)} feed (checked {_d(origin.checked_at)}).",
                -6.0, "medium", EV_ORIGIN)
    elif origin.status == "is_origin":
        acc.add("origin_self", "Employer's own listing",
                f"This is the employer's own {_src(origin.feed)} listing.", -3.0, "low", EV_ORIGIN)
    elif origin.note:
        caveats.append(origin.note)

    if f.valid_through_overrun_days and not f.valid_through_placeholder:
        d = f.valid_through_overrun_days
        acc.add("valid_through_overrun", "Past its own expiry date",
                f"The posting's own expiry date passed {d} days ago (validThrough {_d(p.valid_through)}), "
                "but it is still online. Google requires expired jobs to be taken down.",
                14.0 if d >= 14 else 8.0, "medium", EV_EXPIRY, {"stale": 0.4})
    if f.start_overrun_days and f.start_overrun_days >= 30:
        d = f.start_overrun_days
        start = p.start_date or t.start_date
        acc.add("start_overrun", "Start date long past",
                f"The ad names a start date of {_d(start)}; that was {d} days ago and the ad is still online.",
                16.0 if d >= 90 else 9.0, "medium", EV_EXPIRY, {"stale": 0.35})
    if t.application_deadline and t.application_deadline < now.date() - timedelta(days=7):
        d = (now.date() - t.application_deadline).days
        acc.add("deadline_passed", "Application deadline passed",
                f"The application deadline ({_d(t.application_deadline)}) passed {d} days ago; the ad is still online.",
                8.0, "medium", EV_EXPIRY, {"stale": 0.3})

    # ------------------------------------------------------------ employer context
    if company:
        if company.slow_close_rate is not None and company.slow_close_n >= 5:
            rate = company.slow_close_rate
            if rate >= 0.3:
                acc.add("employer_slow_close", "Employer often leaves ads up",
                        f"{company.slow_close_k} of {company.slow_close_n} closed postings from this employer stayed "
                        f"online far beyond comparable postings (size-adjusted rate {rate:.0%}).",
                        14.0 if rate >= 0.5 else 8.0, "medium", EV_EMPLOYER, {"stale": 0.2, "pool": 0.1}, employer=True)
        if company.board_unchanged_days and company.board_unchanged_days >= 90:
            acc.add("board_unchanged", "Careers board frozen",
                    f"The employer's job board has not changed for {company.board_unchanged_days} days "
                    "(no new and no removed jobs).", 6.0, "low", EV_EMPLOYER, {"frozen": 0.2, "pool": 0.2}, employer=True)
        recent = [e for e in company.events if e.published_at and (now - e.published_at).days <= 180]
        distress = [e for e in recent if e.kind == "distress"]
        funding = [e for e in recent if e.kind == "funding"]
        _employer_evidence(acc, company, bool(distress))
        if distress and company.posting_trend != "falling":
            ev = distress[0]
            if ev.source == "your note":
                acc.add("distress", f"{event_label(ev.subtype) or 'Distress'} while still hiring (your note)",
                        f"You noted on {_d(ev.published_at)}: {ev.title}. The employer is still advertising.",
                        12.0, "medium", EV_NOTE, {"frozen": 0.5}, employer=True)
            else:
                acc.add("distress", "Distress news while still hiring",
                        f"Recent news: “{ev.title}” ({_d(ev.published_at)}). The employer is still advertising.",
                        12.0, "medium", EV_DISTRESS, {"frozen": 0.5}, employer=True)
        starters = [e for e in recent if e.subtype == "new_starters"]
        expansion = [e for e in recent if e.kind == "growth" and e.subtype != "new_starters"]
        if starters:
            acc.add("new_starters", "Confirmed new starters (your note)",
                    f"You noted on {_d(starters[0].published_at)}: {starters[0].title}. Recruitment is producing hires.",
                    -6.0, "medium", EV_DEMAND, employer=True)
        elif expansion and not distress:
            ev = expansion[0]
            acc.add("expansion", "Expansion" + (" (your note)" if ev.source == "your note" else " news"),
                    f"“{ev.title}” ({_d(ev.published_at)}): growth that could need staff.", -3.0, "low", EV_DEMAND,
                    employer=True)
        if company.funding_months is not None and company.funding_months <= 12 and not distress and not (
                funding and (company.coherent_departments or company.posting_trend == "rising")):
            acc.add("funding_recent", "Recent funding",
                    f"Last funding round about {company.funding_months} months ago ({_funding_text(company)}): "
                    "money for hiring is likely there.", -4.0, "low", EV_FUNDING, employer=True)
        if funding:
            ev = funding[0]
            if company.coherent_departments:
                acc.add("funding_coherent", "Funding with a coherent team build",
                        f"Funding news (“{ev.title}”, {_d(ev.published_at)}) and several distinct new roles in "
                        f"{', '.join(company.coherent_departments[:3])}.", -6.0, "low",
                        "Wenske; growth predicts fast filling", employer=True)
            elif company.posting_trend == "rising":
                acc.add("funding_surge", "Posting surge after funding",
                        f"Postings rose after funding news (“{ev.title}”) without coherent team clusters.",
                        6.0, "low", "Signalling motive listed by the CRS", {"fictitious": 0.3}, employer=True)
        if p.department and p.department in company.coherent_departments:
            acc.add("department_cluster", "Part of a team build",
                    f"Several distinct roles opened recently in {p.department}.", -5.0, "low",
                    "Single source (Wenske); low weight until validated")
        elif (p.department and company.departments.get(p.department) == 1 and ratio and ratio >= 1.5
              and rep.instances == 1):
            acc.add("isolated_posting", "Isolated, ageing posting",
                    f"The only open role in {p.department}, and older than typical.", 4.0, "low",
                    "Single source (Wenske); low weight until validated", {"frozen": 0.2})

    # ------------------------------------------------------------ type routing (text)
    if f.is_agency:
        hit = t.agency[0] if t.agency else "staffing agency"
        acc.add("agency", "Staffing agency or client posting",
                f"Posted by a staffing agency or for a client ({hit}). Agencies also advertise for client "
                "orders they only expect.", 8.0, "medium", EV_POOL, {"pool": 0.6})
    if t.evergreen:
        acc.add("evergreen", "Talent-pool wording",
                f"Wording points to a talent pool or speculative application rather than a specific vacancy: "
                f"“{t.evergreen[0]}”.", 20.0, "high", "Google's rules allow résumé collection only for open "
                "positions", {"pool": 0.8})

    if t.pending_approval:
        acc.add("pending_approval", "Position not approved yet",
                f"The ad says the position still needs approval: “{t.pending_approval[0]}”.", 12.0, "medium",
                EV_APPROVAL, {"frozen": 0.4, "fictitious": 0.2})
    if t.contingent:
        acc.add("contingent", "Depends on a project or funding award",
                f"The ad makes the job depend on an award that has not happened yet: “{t.contingent[0]}”.",
                12.0, "medium", EV_CONTINGENT, {"pool": 0.5, "fictitious": 0.2})
    elif t.prospective:
        acc.add("prospective", "Hiring for a project that has not started",
                f"The ad hires for a future project: “{t.prospective[0]}”.", 5.0, "low", EV_CONTINGENT, {"pool": 0.3})

    pre = 0.0
    if t.internal:
        acc.add("internal", "Internal-posting language",
                f"Internal-posting wording: “{t.internal[0]}”.", 8.0, "medium", EV_PREDECIDED, {"pre_decided": 0.5})
    if f.is_public:
        pre += 0.25
        acc.add("public_employer", "Public employer",
                f"Public-sector cues ({t.public_sector[0] if t.public_sector else 'employer type'}). Public posts must be "
                "advertised even when an internal candidate is preferred; fully fictitious posts are rare here.",
                0.0, "none", EV_PREDECIDED, {"pre_decided": 0.25, "fictitious": -0.2})
    formal = bool(t.works_council or t.disability_boilerplate or (t.reference_code and t.application_deadline))
    if formal:
        pre += 0.15
        acc.add("formal_process", "Formal, documented process",
                "Works-council, disability or reference-number/deadline wording marks a documented "
                "selection process.", 0.0, "none", EV_PREDECIDED, {"pre_decided": 0.15, "fictitious": -0.2})
    if t.requirement_specificity >= 0.6:
        pre += 0.25
        acc.add("narrow_profile", "Unusually narrow requirement profile",
                "Many specific certificates, tools or site-specific requirements, which can be tailored to "
                "an internal candidate.", 4.0, "low", "Raised only by German-speaking sources",
                {"pre_decided": 0.25})
    if t.internal or pre >= 0.4:
        acc.add("pre_decided_route", "May be pre-decided",
                "Real vacancy likely, but the outcome may already be decided internally.", 4.0, "low",
                EV_PREDECIDED, direction="routes")

    has_pay = (t.salary_present or ((p.salary_min or p.salary_max) and not p.salary_predicted)
               or p.extra.get("pay_stated"))
    if has_pay:
        detail = t.pay_grade or t.salary_text or (_pay(p) if (p.salary_min or p.salary_max) else "stated on the job board")
        acc.add("salary", "Pay stated", f"Pay information: {detail}.", -2.0, "low", EV_SALARY)
    elif t.tariff_reference:
        acc.add("salary", "Collective agreement referenced",
                "Pay follows a collective agreement (no figure given).", 0.0, "none", EV_SALARY)
    elif f.is_agency or f.is_public or base.kldb in PAY_COMMON_GROUPS:
        acc.add("missing_salary", "No pay where it is usual",
                "No pay stated, although pay is usually given for this kind of job.", 4.0, "low", EV_SALARY)
    else:
        acc.add("missing_salary", "No pay stated (normal in Germany)",
                "No pay stated. Most German ads omit pay, so this is not scored.", 0.0, "none", EV_SALARY)

    publishers = p.extra.get("publishers") or []
    if len(publishers) >= 3:
        acc.add("cross_posted", "Posted on many sites",
                f"Google for Jobs lists this job on {len(publishers)} sites ({', '.join(publishers[:5])}). Wide "
                "multiposting is common for agencies and pools; not scored.", 0.0, "none",
                "Context only; not validated")
    if p.extra.get("ba_flag"):
        acc.add("ba_flag", "Bundesagentur flag",
                f"The Bundesagentur lists this posting under: {p.extra['ba_flag']}.", 0.0, "none", EV_POOL)
    if t.vague_per_100 >= 1.5 and len(t.vague) >= 3:
        acc.add("vague", "Generic wording",
                f"Generic phrases: {', '.join(t.vague[:4])}.", 4.0, "low", EV_TEXT, {"fictitious": 0.1})
    specifics = []
    if t.start_date and not t.start_immediate:
        specifics.append(f"start date {_d(t.start_date)}")
    if len(t.process) >= 2:
        specifics.append("interview steps")
    if t.team_context:
        specifics.append("team details")
    if specifics:
        acc.add("specific", "Concrete details", f"Concrete details: {', '.join(specifics)}.", -4.0, "low", EV_TEXT)

    # ------------------------------------------------------------ user observations and crowd reports
    if user:
        if user.applicant_count is not None and ratio is not None and not user.clicks:
            ac = user.applicant_count
            few = user.applicant_bound == "first" or ac < 10
            shortage = (base.shortage or "").lower().startswith("engpass")
            what = f"fewer than {ac}" if user.applicant_bound == "first" else f"{'over ' if user.applicant_bound == 'over' else ''}{ac}"
            if ac >= 200 and ratio >= 1.5:
                acc.add("applicants_old", "Many applicants, still open",
                        f"{what} applicants and older than typical: many applications without a hire.",
                        10.0, "medium", EV_APPLICANTS, {"pool": 0.2, "fictitious": 0.2})
            elif ac >= 100 and ratio >= 2 and user.applicant_bound != "first":
                acc.add("applicants_old", "Many applicants, still open",
                        f"{what} applicants on a posting {ratio:.1f}× older than typical.", 6.0, "low", EV_APPLICANTS,
                        {"pool": 0.1, "fictitious": 0.1})
            elif few and ratio >= 1.5 and shortage:
                acc.add("applicants_few", "Few applicants in a shortage occupation",
                        f"Only {what} applicants on an old posting, in an occupation the Bundesagentur rates as a shortage: "
                        "more likely genuinely hard to fill.", -3.0, "low", EV_APPLICANTS)
            elif few and ratio >= 1.5:
                acc.add("applicants_few_old", "Old posting, almost no applicants",
                        f"Only {what} applicants after {f.live_days} days in an occupation without a shortage: few people "
                        "see or answer this ad any more.", 6.0, "low", EV_APPLICANTS, {"stale": 0.2, "fictitious": 0.1})
        if user.responsiveness == "none" and (f.live_days or 0) >= 14:
            acc.add("no_activity_badge", "No recruiter-activity indicator",
                    "The platform shows no response insights after 14+ days.", 3.0, "low", EV_BADGES)
        elif user.responsiveness == "active":
            acc.add("activity_badge", "Recruiter-activity indicator",
                    "The platform shows recent recruiter activity (weak: automatic rejections count).",
                    -2.0, "low", EV_BADGES)
        if user.applied_on and user.response:
            waited = (now.date() - user.applied_on).days
            if user.response == "none" and waited >= 30:
                acc.add("own_no_reply", "No reply to your application",
                        f"No reply {waited} days after you applied (weak: 63.5% of German applicants got no "
                        "response at least once).", 3.0, "low", EV_USER)
            elif user.response == "internal":
                acc.add("own_internal", "An internal candidate got this job",
                        "You were told that an internal candidate was chosen for this job.", 20.0, "high", EV_USER,
                        {"pre_decided": 0.8})
            elif user.response == "interview":
                acc.add("own_interview", "Interview invitation",
                        "You were invited to an interview: the process is active.", -8.0, "medium", EV_USER)
            elif user.response == "offer":
                acc.add("own_offer", "Offer received", "You received an offer.", -15.0, "high", EV_USER)
    crowd = f.crowd or {}
    if crowd.get("reports", 0) >= 3:
        silent = crowd.get("no_response_30d", 0)
        if silent / crowd["reports"] >= 0.8:
            acc.add("crowd_silence", "Applicants report silence",
                    f"{silent} of {crowd['reports']} local reports got no reply within 30 days.", 5.0, "low",
                    "Weak: non-response is common in Germany")
        if crowd.get("interviews"):
            acc.add("crowd_interviews", "Applicants report interviews",
                    f"{crowd['interviews']} local report(s) mention interviews.", -4.0, "low", EV_USER)

    # ------------------------------------------------------------ aggregate
    own = BASE_POINTS + acc.points - acc.employer_points
    young = (
        f.live_days is not None
        and f.live_days < YOUNG_DAYS
        and not refreshes
        and origin.status != "removed"
        and not t.evergreen
    )
    if young:
        own = min(own, YOUNG_CAP)
        caveats.append(f"Recently published (under {YOUNG_DAYS} days): most lifecycle signals need time to show.")
    risk = own + acc.employer_points
    if acc.strong_raises < 2:
        risk = min(risk, SINGLE_SIGNAL_CAP)
    risk = int(max(0, min(100, round(risk))))
    grade = "low" if risk < 25 else "moderate" if risk < 45 else "elevated" if risk < 65 else "high"

    dims = [
        f.live_days is not None,
        f.repost.history_days >= 7,
        origin.status in {"present", "removed", "not_found", "is_origin"},
        base.kldb is not None,
        bool(company and company.news_status == "ok"),
    ]
    confidence = "high" if sum(dims) >= 4 else "medium" if sum(dims) >= 2 else "low"
    if f.repost.history_days < 7:
        caveats.append("No tracking history yet: add the employer to the watchlist to detect reposts and removals.")

    types = [
        TypeIndicator(
            key=key,  # type: ignore[arg-type]
            label=label,
            score=round(max(0.0, min(1.0, acc.types[key])), 2),
            explanation="; ".join(dict.fromkeys(acc.type_notes[key])) or "No indicators.",
        )
        for key, label in TYPE_LABELS.items()
    ]
    scam = ScamCheck(flag=bool(t.scam), reasons=t.scam)
    coverage = _coverage(f, base)
    used = sum(1 for c in coverage if c.state == "used")
    if used <= 2:
        caveats.append(f"Only {used} of {len(coverage)} kinds of evidence were available, so posting age weighs heavily.")
    competition = _competition(f, grade)
    comm = company.communication if company and company.communication else Communication(
        text="No applications to this employer recorded yet.")
    advice, tier = _advice(grade, types, scam, f, competition, comm)
    if company and company.hiring_practice:
        caveats.append("Includes your own note about this employer.")
    return Score(
        risk=risk,
        grade=grade,  # type: ignore[arg-type]
        grade_label=GRADE_LABELS[grade],
        confidence=confidence,  # type: ignore[arg-type]
        coverage=coverage,
        types=types,
        scam=scam,
        competition=competition,
        communication=comm,
        reasons=sorted(acc.reasons, key=lambda r: -abs(r.points)),
        advice=advice,
        effort_tier=tier,  # type: ignore[arg-type]
        verify_tips=_tips(types, f),
        caveats=list(dict.fromkeys(caveats)),
    )


def _coverage(f: Features, base) -> list[CoverageItem]:
    """Which evidence the score could use. Age is one item of seven, not the verdict."""
    rep, origin, company, user = f.repost, f.origin, f.company, f.user
    copies_seen = rep.instances > 1 or rep.republished_days is not None or rep.parallel_copies >= 2
    items = [
        CoverageItem(key="age", label="Age vs. occupation norm",
                     state="used" if f.excess_ratio is not None else "missing",
                     note="BA median vacancy duration" if f.excess_ratio is not None else "no publication date"),
        CoverageItem(key="reposts", label="Reposts and copies",
                     state="used" if rep.history_days >= 7 else "partial" if copies_seen else "missing",
                     note="tracked over time" if rep.history_days >= 7 else
                     "compared across platforms today" if copies_seen else "needs repeated checks (watchlist)"),
        CoverageItem(key="origin", label="Employer's own site",
                     state="used" if origin.status in {"present", "removed", "not_found", "is_origin"} else "missing",
                     note={"present": "job is listed there", "removed": "job was removed there",
                           "not_found": "job not listed there", "is_origin": "this is the employer's listing"}.get(
                         origin.status, "no public job feed found")),
        CoverageItem(key="news", label="Company news",
                     state={"ok": "used", "pending": "pending"}.get(company.news_status, "missing") if company else "missing",
                     note={"ok": "layoffs, insolvency, funding checked", "pending": "loading in the background"}.get(
                         company.news_status if company else "", "not checked")),
        CoverageItem(key="applicants", label="Applicants and platform labels",
                     state="used" if user and (user.applicant_count is not None or user.reposted_label) else "missing",
                     note="captured from the platform" if user and user.applicant_count is not None
                     else "capture with the browser extension"),
        CoverageItem(key="wording", label="Wording and employer type", state="used",
                     note="pool, agency, internal-posting and public-sector cues"),
        _track_record_item(company),
    ]
    return items


def _track_record_item(company) -> CoverageItem:
    if not company:
        return CoverageItem(key="track_record", label="Employer track record", state="missing",
                            note="builds up as the radar watches the employer")
    out = company.reports or {}
    parts = []
    if company.slow_close_n >= 5:
        parts.append("past closures")
    if out.get("reports"):
        parts.append(f"{out['reports']} application outcome{'s' if out['reports'] != 1 else ''}")
    if company.hiring_practice:
        parts.append("your note")
    if company.headcount:
        parts.append("size and growth")
    return CoverageItem(key="track_record", label="Employer track record", state="used" if parts else "partial",
                        note=", ".join(parts) if parts else "builds up as the radar watches the employer")


def _pay(p: Posting) -> str:
    if p.salary_min and p.salary_max:
        return f"{p.salary_min:,.0f}–{p.salary_max:,.0f} {p.salary_currency or ''}".strip()
    return f"{(p.salary_min or p.salary_max):,.0f} {p.salary_currency or ''}".strip()


def _dominant(types: list[TypeIndicator]) -> TypeIndicator | None:
    best = max(types, key=lambda t: t.score)
    return best if best.score >= 0.3 else None


TIERS = ["full", "standard", "light", "verify", "skip"]


def _advice(grade: str, types: list[TypeIndicator], scam: ScamCheck, f: Features,
            competition: Competition | None = None, comm: Communication | None = None) -> tuple[str, str]:
    if scam.flag:
        return ("Scam markers found (" + "; ".join(scam.reasons) + "). Do not send ID documents, bank data or "
                "money; verify the employer independently.", "skip")
    text, tier = _ghost_advice(grade, types)
    comp = competition or Competition()
    if comp.chance == "very_low" and tier in {"full", "standard"}:
        text = text.replace(" Worth a tailored application.", "")
        text += f" Your chance is very low ({'; '.join(comp.why)}): apply early, and only with a close match."
        tier = TIERS[TIERS.index(tier) + 1]
    elif comp.chance == "low" and tier in {"full", "standard"}:
        text += f" Your chance is low ({'; '.join(comp.why)}): an early, tailored application matters."
    if comm and comm.level == "high" and tier in {"full", "standard"}:
        text += (f" This employer did not answer {comm.silent} of {comm.n} of your applications within 30 days: "
                 "note a follow-up date and keep the effort proportionate.")
        tier = TIERS[TIERS.index(tier) + 1]
    return text, tier


def _ghost_advice(grade: str, types: list[TypeIndicator]) -> tuple[str, str]:
    dom = _dominant(types)
    if grade == "low":
        return "No ghost-risk indicators of note. Worth a tailored application.", "full"
    if grade == "moderate":
        if dom and dom.key == "pre_decided":
            return ("An internal candidate may be favoured. Keep the application short and ask whether internal "
                    "candidates are already in the process.", "light")
        text = "Some indicators (see below). A solid standard application is reasonable."
        if dom and dom.key == "pool":
            text += " Likely a candidate pool: ask whether a concrete vacancy exists."
        return text, "standard"
    by_type = {
        "stale": "Signs that the role may already be filled or abandoned. Verify before investing time.",
        "pool": "Looks like a candidate pool rather than a specific vacancy. Apply only if being in a pool suits "
                "you, and ask whether a concrete vacancy exists.",
        "pre_decided": "A real vacancy is likely, but the outcome may already be decided internally. Apply if "
                       "your profile matches closely and keep the effort proportionate.",
        "frozen": "Hiring at this employer may be frozen. Ask whether the position is approved before investing time.",
        "fictitious": "The posting pattern fits signalling or CV collection. Verify that a real role exists first.",
    }
    text = by_type.get(dom.key, "Several ghost-risk indicators.") if dom else "Several ghost-risk indicators."
    if grade == "elevated":
        return "Send a short, fast application or verify first. " + text, "light"
    return text, "verify"


def _tips(types: list[TypeIndicator], f: Features) -> list[str]:
    scores = {t.key: t.score for t in types}
    tips = ["Check the employer's own careers page for this exact job and its date."]
    if scores["stale"] >= 0.3 or scores["frozen"] >= 0.3 or scores["fictitious"] >= 0.3:
        tips.append("Ask the contact in writing whether the position is approved and when it should be filled "
                    "(„Ist die Stelle aktuell freigegeben, und zu wann soll sie besetzt werden?“).")
    if scores["pool"] >= 0.3:
        tips.append("Ask the agency or employer whether there is a concrete client order or vacancy "
                    "(„Gibt es einen konkreten Auftrag für diese Stelle?“).")
    if scores["pre_decided"] >= 0.3:
        tips.append("Ask whether internal candidates are in the process and how many positions are open.")
    if f.text.pending_approval:
        tips.append("Ask whether the budget for the position is approved now, who the hiring manager is and what the "
                    "target start date is.")
    if f.repost.history_days < 7:
        tips.append("Track the employer in the watchlist to see reposts and removals over the coming weeks.")
    return tips


CHANCE_STEPS = ["good", "fair", "low", "very_low"]


def _competition(f: Features, grade: str = "low") -> Competition:
    """Your chance if the job is real. Applicants against the applications per hire typical for the field
    (IAB 2025), with your own floors (default 100 and 200 applicants), the application rate, and what you know
    about the employer (internal hiring, your interview record). A likely ghost caps the chance at "low"."""
    user = f.user
    company = f.company
    why: list[str] = []
    comp = Competition()
    kldb = f.baseline.kldb or ""
    base = APPS_PER_HIRE.get(kldb[:2], 16)
    if user and user.applicant_count is not None:
        ac = user.applicant_count
        comp.applicants, comp.per_hire, comp.bound, comp.clicks = ac, base, user.applicant_bound, bool(user.clicks)
        comp.ratio = round(ac / base, 2)
        noun = "people clicked apply" if user.clicks else "applicants"
        if user.applicant_bound == "first":
            comp.level = "normal"
            what = f"fewer than {ac} {noun}"
        else:
            r = ac / base
            comp.level = ("very_high" if r >= 3 or ac >= f.chance_very_high else
                          "high" if r >= 1.5 or ac >= f.chance_high else "normal")
            what = f"{'over ' if user.applicant_bound == 'over' else ''}{ac} {noun}"
        if f.live_days is not None and user.applicant_bound != "first":
            comp.rate_per_day = round(ac / max(1, f.live_days), 1)
        rate = f", about {comp.rate_per_day:g} a day" if comp.rate_per_day else ""
        comp.text = (f"{what[:1].upper()}{what[1:]}{rate}. About {base} applications per hire are usual for this field."
                     + (" These are clicks on an external link, so real applications are fewer." if user.clicks else ""))
        step = {"normal": 0, "high": 2, "very_high": 3}[comp.level]
        if comp.level != "normal":
            why.append(what)
        if comp.rate_per_day and comp.rate_per_day >= 20 and step < 2:
            step = 2
            why.append(f"{comp.rate_per_day:g} applicants a day")
        comp.confidence = "medium" if (user.applicant_bound or user.clicks) else "high"
    else:
        comp.text = "Enter the applicant count you see on the platform, or read it with linkedin-jobs-mcp, to judge your chances."
        step = None
    # what you know about the employer
    adjust = 0
    if company and (company.hiring_practice == "internal_first" or (company.reports or {}).get("internal")):
        adjust += 1
        why.append("internal candidates usually get these jobs")
    out = (company.reports or {}) if company else {}
    decided = sum(out.get(k, 0) for k in ("auto_reject", "reject", "internal")) + out.get("interviews", 0)
    if decided >= 4 and out.get("interviews", 0) == 0:
        adjust += 1
        why.append(f"no interviews from your {decided} answered applications here")
    elif decided >= 3 and out.get("interviews", 0) / decided >= 0.3:
        adjust -= 1
        why.append(f"{out['interviews']} interviews from your {decided} answered applications here")
    if step is None and adjust <= 0:
        comp.chance = "unknown"
    else:
        level = min(3, max(0, (step if step is not None else 1) + adjust))
        if grade in {"elevated", "high"}:
            level = max(level, 2)
            why.append("the job may not be open")
        comp.chance = CHANCE_STEPS[level]
        if step is None:
            comp.confidence = "low"
    comp.why = why
    return comp


def _funding_text(company) -> str:
    when = company.funding_date.strftime("%m/%Y") if company.funding_date else "date unknown"
    amount = f", {company.funding_amount}" if company.funding_amount else ""
    return f"{when}{amount}, from {company.funding_source}"


def _employer_evidence(acc: _Acc, company, distress: bool = False) -> None:
    """Employer-wide evidence: your notes, your outcome record, size, growth and hiring capacity."""
    name = company.name or "this employer"
    note = f" You wrote: “{company.practice_note}”." if company.practice_note else ""
    if company.hiring_practice == "internal_first":
        acc.add("practice_internal", "Internal candidates usually get these jobs (your note)",
                f"You marked {name} as filling roles with internal candidates first.{note}",
                16.0, "medium", EV_NOTE, {"pre_decided": 0.7}, employer=True)
    elif company.hiring_practice == "external":
        acc.add("practice_external", "Usually hires externally (your note)",
                f"You marked {name} as hiring from outside.{note}", -6.0, "low", EV_NOTE,
                {"pre_decided": -0.3}, employer=True)

    out = company.reports or {}
    internal = out.get("internal", 0)
    progress = out.get("interviews", 0)
    decided = out.get("auto_reject", 0) + out.get("reject", 0) + internal + progress
    if internal:
        acc.add("outcome_internal", "Internal candidates got these jobs before",
                f"{internal} of {out.get('reports', internal)} reported applications to {name} ended with an internal "
                "candidate being chosen.", 20.0 if internal >= 2 else 10.0, "high" if internal >= 2 else "medium", EV_OUTCOMES,
                {"pre_decided": 0.6 if internal >= 2 else 0.4}, employer=True)
    if decided >= 4 and progress == 0:
        acc.add("outcome_no_interviews", "No interviews from applications",
                f"None of {decided} answered applications to {name} led to an interview "
                f"({out.get('auto_reject', 0)} automatic and {out.get('reject', 0)} other rejections, "
                f"{internal} internal).", 10.0, "medium", EV_OUTCOMES,
                {"pool": 0.2, "pre_decided": 0.2, "fictitious": 0.2}, employer=True)
    elif decided >= 4 and progress / decided <= 0.1:
        acc.add("outcome_few_interviews", "Few interviews from applications",
                f"Only {progress} of {decided} answered applications to {name} led to an interview.", 5.0, "low",
                EV_OUTCOMES, {"pool": 0.1, "pre_decided": 0.1}, employer=True)
    elif decided >= 3 and progress / decided >= 0.3:
        acc.add("outcome_interviews", "Applications lead to interviews here",
                f"{progress} of {decided} answered applications to {name} led to an interview or offer.",
                -6.0, "medium", EV_OUTCOMES, employer=True)
    silent = out.get("no_response_30d", 0)
    if out.get("reports", 0) >= 4 and silent / out["reports"] >= 0.75:
        acc.add("outcome_silence", "Most applications get no reply",
                f"{silent} of {out['reports']} reported applications to {name} got no reply within 30 days.",
                5.0, "low", EV_OUTCOMES, employer=True)

    if company.capacity_ratio is not None and company.open_jobs >= 4 and company.capacity_ratio >= 2.5:
        cr = company.capacity_ratio
        growth = ("an assumed 20% growth (enter last year's headcount for the real figure)" if company.growth_assumed
                  else f"{company.growth:+.0%} headcount growth")
        acc.add("capacity", "More openings than it can plausibly fill",
                f"{company.open_jobs} open jobs, but about {company.plausible_openings:.0f} openings at a time are "
                f"plausible for {company.headcount} employees ({growth}, 15% of staff replaced a year, about 86 days "
                f"to fill). That is {cr:.1f}× as many.", 14.0 if cr >= 4 else 8.0, "medium", EV_CAPACITY,
                {"fictitious": 0.5 if cr >= 4 else 0.3, "pool": 0.1}, employer=True)
    if company.contracts_12m:
        acc.add("contracts", "Contracts won recently",
                f"{company.contracts_12m} public contract{'s' if company.contracts_12m != 1 else ''} won: "
                "work that may need staff.", -4.0, "low", EV_DEMAND,
                employer=True)
    if company.growth is not None and company.open_jobs >= 3:
        if company.growth <= -0.05 and distress:
            acc.add("shrinking", "Shrinking with distress news while hiring",
                    f"Headcount fell {abs(company.growth):.0%} in a year ({company.headcount_prev} → {company.headcount}), "
                    f"there is distress news, and {company.open_jobs} jobs are advertised.", 10.0, "medium", EV_GROWTH,
                    {"frozen": 0.4, "fictitious": 0.2}, employer=True)
        elif company.growth <= -0.05:
            acc.add("shrinking", "Shrinking headcount",
                    f"Headcount fell {abs(company.growth):.0%} in a year ({company.headcount_prev} → {company.headcount}). "
                    "Shrinking firms still hire to replace leavers, so this is not scored without distress news.",
                    0.0, "none", EV_TURNOVER, employer=True)
        elif company.growth >= 0.15:
            acc.add("growing", "Growing headcount",
                    f"Headcount grew {company.growth:.0%} in a year ({company.headcount_prev} → {company.headcount}): "
                    "genuine hiring is likely.", -4.0, "low", EV_GROWTH, employer=True)
    if (company.funding_source == "your note" and company.funding_months is not None and company.funding_months >= 12
            and (company.capacity_ratio or 0) >= 1.5):
        acc.add("funding_stale", "No funding round in the last year",
                f"Last funding round about {company.funding_months} months ago ({_funding_text(company)}), while "
                f"openings are {company.capacity_ratio:.1f}× what the company can plausibly fill.", 6.0, "low",
                EV_FUNDING, {"frozen": 0.2, "fictitious": 0.2}, employer=True)


def _closed(f: Features) -> Score:
    return Score(
        risk=0,
        grade="closed",
        grade_label=GRADE_LABELS["closed"],
        confidence="high",
        types=[TypeIndicator(key=k, label=v, score=0.0, explanation="Posting is closed.")  # type: ignore[arg-type]
               for k, v in TYPE_LABELS.items()],
        scam=ScamCheck(),
        competition=Competition(),
        reasons=[Reason(signal="closed", label="Posting removed", fact=f.closed_reason or "The posting is no longer online.",
                        direction="info", strength="high", evidence="Direct observation")],
        advice="This posting is no longer online, so there is nothing to apply to. Look for a newer version on the "
               "employer's careers page.",
        effort_tier="skip",
        verify_tips=[],
        caveats=[],
    )
