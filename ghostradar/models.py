"""Data models shared by sources, analysis and the API."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

# what came of an application: no reply, automatic or other rejection, an internal candidate chosen,
# interview, offer
Outcome = Literal["none", "auto_reject", "reject", "internal", "interview", "offer"]

Channel = Literal["employer", "aggregator", "manual"]
Grade = Literal["low", "moderate", "elevated", "high", "unknown", "closed"]
TypeKey = Literal["stale", "pool", "pre_decided", "frozen", "fictitious"]


class Posting(BaseModel):
    """One job posting as delivered by a single source."""

    source: str
    source_id: str
    url: str | None = None
    company: str | None = None
    title: str = ""
    location: str | None = None
    city: str | None = None
    region: str | None = None  # German Bundesland, if known
    country: str | None = None
    lat: float | None = None
    lon: float | None = None
    department: str | None = None
    description: str = ""
    posted_at: datetime | None = None
    posted_at_is_lower_bound: bool = False
    updated_at: datetime | None = None
    valid_through: datetime | None = None
    start_date: date | None = None
    start_immediate: bool | None = None
    employment_type: str | None = None
    requisition_id: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None
    salary_period: str | None = None
    salary_predicted: bool = False
    agency_flag: bool | None = None
    remote: bool | None = None
    channel: Channel = "employer"
    extra: dict[str, Any] = Field(default_factory=dict)


# --------------------------------------------------------------------------- features


class TextFeatures(BaseModel):
    language: str = "unknown"
    word_count: int = 0
    evergreen: list[str] = Field(default_factory=list)
    agency: list[str] = Field(default_factory=list)
    internal: list[str] = Field(default_factory=list)
    contingent: list[str] = Field(default_factory=list)
    pending_approval: list[str] = Field(default_factory=list)
    prospective: list[str] = Field(default_factory=list)
    works_council: list[str] = Field(default_factory=list)
    disability_boilerplate: bool = False
    public_sector: list[str] = Field(default_factory=list)
    salary_present: bool = False
    salary_text: str | None = None
    pay_grade: str | None = None
    tariff_reference: bool = False
    start_date: date | None = None
    start_immediate: bool = False
    application_deadline: date | None = None
    reference_code: bool = False
    named_contact: bool = False
    process: list[str] = Field(default_factory=list)
    team_context: list[str] = Field(default_factory=list)
    vague: list[str] = Field(default_factory=list)
    vague_per_100: float = 0.0
    scam: list[str] = Field(default_factory=list)
    seniority: str | None = None
    apprenticeship: bool = False
    requirement_specificity: float = 0.0
    years_required: int | None = None
    multi_vacancy: bool = False


class Baseline(BaseModel):
    kldb: str | None = None
    kldb_label: str | None = None
    level_code: str | None = None
    level: str | None = None
    region: str | None = None
    vakanzzeit_days: int | None = None
    expected_days: int | None = None
    shortage: str | None = None
    matched_by: str | None = None
    note: str = ""


class RepostInfo(BaseModel):
    instances: int = 1
    cosmetic: int = 0
    new_requisition: int = 0
    uncertain: int = 0
    date_refreshes: int = 0
    regular_cadence: bool = False
    total_live_days: int | None = None
    first_start: datetime | None = None
    history_days: int = 0
    # visible on the first check, no history needed
    republished_days: int | None = None  # a copy published this many days after the job first appeared
    republished_on: str | None = None
    first_seen_on: str | None = None
    parallel_copies: int = 0  # most live copies of this job on a single source
    parallel_source: str | None = None
    refreshed_days: int | None = None  # source shows a recent update on an ad first published this long ago


class OriginInfo(BaseModel):
    status: Literal["present", "removed", "not_found", "unknown", "is_origin"] = "unknown"
    feed: str | None = None
    feed_jobs: int | None = None
    checked_at: datetime | None = None
    removed_days: int | None = None
    note: str = ""


class CompanyEvent(BaseModel):
    kind: Literal["distress", "funding", "growth", "contract", "other"]
    title: str
    url: str | None = None
    published_at: datetime | None = None
    source: str | None = None
    subtype: str | None = None  # e.g. hiring_freeze, manager_left (your notes) or a TED notice type
    id: int | None = None


class Communication(BaseModel):
    """Candidate-ghosting risk from the applications you recorded: does this employer reply at all?

    Outcome definition: a substantive reply within 30 days of applying or of the last interview; a rejection
    counts as a reply. Withdrawn applications are left out, and applications still inside the 30 days are
    unresolved rather than silent. One person's applications describe that person's experience, not a
    company-wide ghosting rate."""

    level: Literal["unknown", "low", "medium", "high"] = "unknown"
    text: str = ""
    n: int = 0  # resolved applications (replied or silent)
    replied: int = 0
    silent: int = 0
    unresolved: int = 0
    withdrawn: int = 0
    missed_promises: int = 0
    unanswered_followups: int = 0
    share_silent: float | None = None
    low: float | None = None
    high: float | None = None
    by_stage: dict[str, dict[str, int]] = Field(default_factory=dict)
    confidence: Literal["low", "medium", "high"] = "low"


class CompanySignals(BaseModel):
    company_id: int | None = None
    name: str | None = None
    employer_type: str | None = None
    active_postings: int = 0
    tracked_days: int = 0
    departments: dict[str, int] = Field(default_factory=dict)
    coherent_departments: list[str] = Field(default_factory=list)
    slow_close_rate: float | None = None
    slow_close_n: int = 0
    slow_close_k: int = 0
    board_unchanged_days: int | None = None
    posting_trend: str = "unknown"
    headcount: int | None = None
    postings_per_100: float | None = None
    events: list[CompanyEvent] = Field(default_factory=list)
    news_status: str = "not_checked"
    reports: dict[str, Any] = Field(default_factory=dict)
    # what the user knows about the employer (stored locally, always labelled as their note)
    hiring_practice: Literal["internal_first", "external"] | None = None
    practice_note: str | None = None
    # size, growth and funding: openings against the hiring the employer can plausibly do
    open_jobs: int = 0
    headcount_prev: int | None = None
    growth: float | None = None
    growth_assumed: bool = False
    plausible_openings: float | None = None
    capacity_ratio: float | None = None
    funding_date: date | None = None
    funding_amount: str | None = None
    funding_months: int | None = None
    funding_source: str | None = None
    # evidence of actual hiring and of demand
    communication: Communication | None = None
    fill_rate: float | None = None  # share of closed postings that closed within the typical window (likely filled)
    fill_n: int = 0
    fill_k: int = 0
    contracts_12m: int = 0  # public contracts won in the last 12 months (TED)


class UserObservations(BaseModel):
    """Things the job seeker can see on a platform we must not scrape."""

    applicant_count: int | None = None
    applicant_bound: Literal["over", "first"] | None = None  # "over 200" is a floor, "first 25" means fewer
    clicks: bool | None = None  # the count is "people clicked apply", not applications
    reposted_label: bool | None = None
    responsiveness: Literal["active", "none", "unknown"] | None = None
    posted_date_shown: date | None = None
    applied_on: date | None = None
    response: Outcome | None = None


class Features(BaseModel):
    now: datetime
    first_published: datetime | None = None
    first_published_is_lower_bound: bool = False
    live_days: int | None = None
    is_live: bool = True
    closed_reason: str | None = None
    repost: RepostInfo = Field(default_factory=RepostInfo)
    origin: OriginInfo = Field(default_factory=OriginInfo)
    valid_through_overrun_days: int | None = None
    valid_through_placeholder: bool = False
    start_overrun_days: int | None = None
    baseline: Baseline = Field(default_factory=Baseline)
    excess_ratio: float | None = None
    empirical_tail: float | None = None
    tail_group: str | None = None  # the comparable postings behind the survival tail
    tail_spells: int | None = None
    is_agency: bool = False
    is_public: bool = False
    outside_germany: bool = False
    text: TextFeatures = Field(default_factory=TextFeatures)
    company: CompanySignals | None = None
    user: UserObservations | None = None
    crowd: dict[str, Any] = Field(default_factory=dict)
    # your thresholds (Method page): where age starts to count, and applicant counts for low chances
    age_start: float = 1.0
    chance_high: int = 100
    chance_very_high: int = 200


# --------------------------------------------------------------------------- scores


class Reason(BaseModel):
    signal: str
    label: str
    fact: str
    direction: Literal["raises", "lowers", "routes", "info"]
    points: float = 0.0
    strength: Literal["high", "medium", "low", "none"] = "low"
    evidence: str = ""
    types: list[str] = Field(default_factory=list)


class TypeIndicator(BaseModel):
    key: TypeKey
    label: str
    score: float
    explanation: str


class ScamCheck(BaseModel):
    flag: bool = False
    reasons: list[str] = Field(default_factory=list)


class Competition(BaseModel):
    """Your chance if the job is real: applicants against the applications per hire typical for the field."""

    level: Literal["unknown", "normal", "high", "very_high"] = "unknown"
    text: str = ""
    applicants: int | None = None
    per_hire: int | None = None
    ratio: float | None = None
    bound: Literal["over", "first"] | None = None
    clicks: bool = False
    rate_per_day: float | None = None  # applicants per day since the job was (re)posted
    chance: Literal["unknown", "good", "fair", "low", "very_low"] = "unknown"
    confidence: Literal["low", "medium", "high"] = "low"
    why: list[str] = Field(default_factory=list)


class CoverageItem(BaseModel):
    """Which kinds of evidence a score could use, so age alone never looks like the whole story."""

    key: str
    label: str
    state: Literal["used", "partial", "missing", "pending"]
    note: str = ""


class Score(BaseModel):
    risk: int
    grade: Grade
    grade_label: str
    confidence: Literal["low", "medium", "high"]
    coverage: list[CoverageItem] = Field(default_factory=list)
    types: list[TypeIndicator]
    scam: ScamCheck
    competition: Competition
    communication: Communication = Field(default_factory=Communication)
    reasons: list[Reason]
    advice: str
    effort_tier: Literal["full", "standard", "light", "verify", "skip"]
    verify_tips: list[str]
    caveats: list[str]


class CopyInfo(BaseModel):
    """One place where the same job is (or was) published."""

    posting_id: int
    source: str
    channel: str
    status: str
    url: str | None = None
    posted_at: datetime | None = None
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    removed_at: datetime | None = None


class ScoredPosting(BaseModel):
    posting_id: int | None = None
    posting: Posting
    features: Features
    score: Score
    copies: list[CopyInfo] = Field(default_factory=list)
    estimate: dict[str, Any] | None = None  # the trained model's estimate, once audited labels exist


class SearchFilters(BaseModel):
    """Filters passed through to every connector that supports them."""

    posted_within: int | None = None  # days: 1, 7 or 30
    job_type: Literal["full_time", "part_time", "contract", "internship"] | None = None
    remote: bool = False
    exclude_agencies: bool = False
    sources: list[str] = Field(default_factory=lambda: ["linkedin", "ba", "jsearch", "adzuna", "arbeitnow", "tracked"])


# --------------------------------------------------------------------------- API payloads


class CheckRequest(BaseModel):
    url: str | None = None
    text: str | None = None
    title: str | None = None
    company: str | None = None
    location: str | None = None
    observations: UserObservations | None = None
    with_news: bool = True


class CaptureIn(BaseModel):
    """A job page captured in the user's own browser (extension or bookmarklet)."""

    platform: str = Field(max_length=40)
    url: str = Field(max_length=2000)
    job_id: str | None = Field(default=None, max_length=200)
    title: str | None = Field(default=None, max_length=500)
    company: str | None = Field(default=None, max_length=300)
    location: str | None = Field(default=None, max_length=300)
    description: str | None = Field(default=None, max_length=80000)
    top_text: str | None = Field(default=None, max_length=10000)
    applicant_text: str | None = Field(default=None, max_length=300)
    posted_text: str | None = Field(default=None, max_length=300)
    badges: list[str] = Field(default_factory=list, max_length=40)
    jsonld: list[dict[str, Any]] = Field(default_factory=list, max_length=20)
    observations: UserObservations | None = None
    with_news: bool = True


class CheckResponse(BaseModel):
    result: ScoredPosting | None
    mode: Literal["fetched", "manual", "closed", "error"]
    notes: list[str] = Field(default_factory=list)
    sources_used: list[str] = Field(default_factory=list)


class FeedSummary(BaseModel):
    ats: str
    slug: str
    url: str
    jobs: int
    complete: bool
    matched_by: str
    error: str | None = None


class CompanyResponse(BaseModel):
    name: str
    company_id: int | None
    feeds: list[FeedSummary]
    signals: CompanySignals | None
    grade: str
    grade_note: str
    postings: list[ScoredPosting]
    notes: list[str] = Field(default_factory=list)
    text_task: str | None = None  # background task filling in missing ad texts


class CityResponse(BaseModel):
    city: str
    center: tuple[float, float] | None
    postings: list[ScoredPosting]
    summary: dict[str, Any]
    notes: list[str] = Field(default_factory=list)
    sources_used: list[str] = Field(default_factory=list)


class ReportIn(BaseModel):
    posting_id: int | None = None
    posting_url: str | None = None
    company: str | None = None
    applied_on: date | None = None
    response: Outcome | None = None
    days_to_response: int | None = None
    applicant_count: int | None = None
    reposted_label: bool | None = None
    note: str | None = Field(default=None, max_length=500)
    stage: Literal["application", "screening", "interview"] | None = None  # how far the application got
    promised_by: date | None = None  # the date the employer promised an update by
    withdrawn: bool | None = None
    followups: int | None = Field(default=None, ge=0, le=20)  # your follow-ups that got no answer


class AuditIn(BaseModel):
    """The result of checking one posting with the employer (the report's audit design)."""

    posting_id: int
    label: Literal["open", "filled", "internal", "pool", "on_hold", "unsure"]
    method: str | None = Field(default=None, max_length=120)
    note: str | None = Field(default=None, max_length=500)
    inclusion_prob: float | None = Field(default=None, gt=0, le=1)
    # evidence of an approved position (the employer's answer)
    approval: Literal["confirmed", "pending", "unknown"] | None = None
    manager_named: bool | None = None
    start_date_given: bool | None = None


EVENT_KINDS = {
    # what you learned about the employer, with a date: (category, label)
    "hiring_freeze": ("distress", "Hiring freeze"),
    "restructuring": ("distress", "Restructuring or job cuts"),
    "manager_left": ("distress", "Hiring manager left"),
    "recruiter_change": ("distress", "Recruiter reassigned or recruiting team cut"),
    "project_cancelled": ("distress", "Project cancelled or financing delayed"),
    "contract_won": ("contract", "Contract or order won"),
    "expansion": ("growth", "New site, product or team expansion"),
    "funding": ("funding", "Funding round or grant"),
    "new_starters": ("growth", "Confirmed new starters in the team"),
}


class EventIn(BaseModel):
    """A dated fact about the employer that you learned yourself."""

    kind: Literal["hiring_freeze", "restructuring", "manager_left", "recruiter_change", "project_cancelled",
                  "contract_won", "expansion", "funding", "new_starters"]
    date: date
    note: str | None = Field(default=None, max_length=300)


class PrefsIn(BaseModel):
    """Your thresholds."""

    age_start: float | None = Field(default=None, ge=0.5, le=2.0)
    chance_high: int | None = Field(default=None, ge=5, le=5000)
    chance_very_high: int | None = Field(default=None, ge=10, le=10000)
    window_days: Literal[7, 30, 90, 365] | None = None  # history window, one year at most


class NotesImport(BaseModel):
    """CSV lines: company;practice;note (practice: internal_first, external or empty)."""

    csv: str = Field(max_length=200_000)


class WatchIn(BaseModel):
    kind: Literal["company", "city"]
    query: str
    params: dict[str, Any] = Field(default_factory=dict)


class CompanyUpdate(BaseModel):
    """Fields the user can set for an employer; an empty value clears the field."""

    headcount: int | None = Field(default=None, ge=0)
    headcount_prev: int | None = Field(default=None, ge=0)
    employer_type: Literal["agency", "public", "private"] | None = None
    hiring_practice: Literal["internal_first", "external", ""] | None = None
    practice_note: str | None = Field(default=None, max_length=300)
    funding_date: date | None = None
    funding_amount: str | None = Field(default=None, max_length=60)
