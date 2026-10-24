"""Workflows behind the API: check one posting, analyse a company, map a city, run the watchlist."""
from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import datetime, timedelta

from . import db
from .config import settings
from .analysis import baselines, dedup, labels, scoring
from .analysis import company as company_analysis
from .analysis import text as text_analysis
from .http import Blocked, FetchError, PoliteClient, blocked_reason
from . import tasks
from .ml import audit as ml_audit
from .ml import features as ml_features
from .ml import labels as ml_labels
from .ml import model as ml_model
from .ml import survival
from . import prefs as user_prefs
from .models import EVENT_KINDS
from .sources import ted
from .tasks import Progress
from .models import (
    CaptureIn,
    CheckRequest,
    CheckResponse,
    CityResponse,
    CompanyResponse,
    CompanySignals,
    CopyInfo,
    FeedSummary,
    Features,
    OriginInfo,
    Posting,
    RepostInfo,
    ScoredPosting,
    SearchFilters,
    UserObservations,
)
from .sources import adzuna, arbeitnow, ats, ba, geo, jsearch, jsonld, linkedin, news
from .util import company_key, normalize_title, parse_datetime, stable_jitter, strip_contact_data, utcnow

FEED_FRESH = timedelta(days=3)


# --------------------------------------------------------------------------- ingestion


def _enrich_location(p: Posting) -> None:
    known = geo.lookup(p.city) or geo.lookup(p.location)
    if known:
        if p.lat is None or p.lon is None:
            p.lat, p.lon = known[0], known[1]
        p.region = p.region if p.region in baselines.BUNDESLAND_TO_BA_REGION else known[2]
        p.city = geo.city_name(p.city) or geo.city_name(p.location) or p.city
    elif p.region and p.region not in baselines.BUNDESLAND_TO_BA_REGION:
        p.region = None


def ingest(postings: list[Posting], company_hint: str | None = None, now: datetime | None = None) -> list[int]:
    """Store postings (keeping every instance), link them into job clusters, return their ids."""
    now = now or utcnow()
    ids: list[int] = []
    company_ids: dict[str, int] = {}
    candidates: dict[int, list[dict]] = {}
    for p in postings:
        if not p.company and company_hint:
            p.company = company_hint
        p.description = strip_contact_data(p.description)
        _enrich_location(p)
        cid = None
        if p.company:
            key = company_key(p.company) or p.company
            cid = company_ids.get(key) or db.get_or_create_company(p.company)
            company_ids[key] = cid
        kldb, level, _ = baselines.classify(p.title, p.description, p.extra.get("occupation"))
        sig = dedup.signature(p.description) if p.description else None
        pid, _ = db.upsert_posting(p, cid, now, sig, kldb, level)
        row = db.get_posting_row(pid, light=True)
        if row and not row.get("cluster_id"):
            pool: list[dict] = []
            if cid is not None:
                if cid not in candidates:
                    candidates[cid] = [r for r in db.company_posting_rows(cid, light=True) if r.get("cluster_id")]
                pool = candidates[cid]
            cluster = dedup.find_cluster(row, pool) or pid
            db.set_cluster(pid, cluster)
            row["cluster_id"] = cluster
            if cid is not None:
                pool.append(row)
        ids.append(pid)
    return ids


def _store_feed(company_id: int, feed: ats.FeedResult, now: datetime) -> list[int]:
    # a feed belongs to the employer it was fetched for; legal-entity names (e.g. Personio's
    # "subcompany") are kept as detail instead of splitting the employer in two
    canonical = db.get_company(company_id)["name"]
    for p in feed.postings:
        if p.company and company_key(p.company) != company_key(canonical):
            p.extra["legal_entity"] = p.company
        p.company = canonical
    ids = ingest(feed.postings, canonical, now)
    seen = {p.source_id for p in feed.postings}
    db.sync_feed(company_id, feed.ref.ats, seen, feed.complete, now)
    db.record_feed_run(company_id, feed.ref.ats, feed.ref.slug, feed.ok, len(feed.postings), feed.complete, feed.error or "")
    return ids


# --------------------------------------------------------------------------- features


def _repost_info(row: dict, now: datetime) -> RepostInfo:
    rows = db.cluster_rows(row["cluster_id"]) if row.get("cluster_id") else [row]
    same_channel = [r for r in rows if r["channel"] == row["channel"]] or [row]
    summary = dedup.summarise_cluster([dedup.instance_from_row(r) for r in same_channel], now)
    refreshes = 0
    earliest = summary.first_start
    for r in same_channel:
        dates = sorted({s["posted_at"][:10] for s in db.sightings(r["id"]) if s.get("posted_at")})
        parsed = [d for d in (parse_datetime(x) for x in dates) if d]
        if parsed and (earliest is None or parsed[0] < earliest):
            earliest = parsed[0]  # the oldest publication date any sighting reported
        refreshes += sum(1 for a, b in zip(parsed, parsed[1:]) if (b - a).days >= 7)
    first_seen = min(parse_datetime(r["first_seen"]) for r in rows)
    total = summary.total_live_days
    if earliest and summary.first_start and earliest < summary.first_start:
        total += (summary.first_start - earliest).days

    # evidence visible on the very first check, across every copy of the job
    republished_days = republished_on = first_seen_on = None
    starts = []
    for r in rows:
        start = parse_datetime(r.get("posted_at")) or parse_datetime(r["first_seen"])
        if start:
            starts.append((start, r))
    if len(starts) >= 2:
        oldest = min(starts, key=lambda x: x[0])
        newest = max(((s, r) for s, r in starts if r["status"] == "active" and r.get("posted_at")),
                     key=lambda x: x[0], default=None)
        if newest and newest[1]["id"] != oldest[1]["id"] and (newest[0] - oldest[0]).days >= 21:
            republished_days = (newest[0] - oldest[0]).days
            republished_on, first_seen_on = newest[1]["source"], oldest[1]["source"]
    live_by_source: dict[str, int] = {}
    for r in rows:
        if r["status"] == "active":
            live_by_source[r["source"]] = live_by_source.get(r["source"], 0) + 1
    parallel_source = max(live_by_source, key=live_by_source.get) if live_by_source else None
    parallel = live_by_source.get(parallel_source, 0) if parallel_source else 0
    refreshed = None
    updated, posted = parse_datetime(row.get("updated_at")), parse_datetime(row.get("posted_at"))
    if updated and posted and (now - updated).days <= 14 and (updated - posted).days >= 60:
        refreshed = (updated - posted).days

    return RepostInfo(
        republished_days=republished_days,
        republished_on=republished_on,
        first_seen_on=first_seen_on,
        parallel_copies=parallel if parallel >= 2 else 0,
        parallel_source=parallel_source if parallel >= 2 else None,
        refreshed_days=refreshed,
        instances=summary.instances,
        cosmetic=summary.cosmetic,
        new_requisition=summary.new_requisition,
        uncertain=summary.uncertain,
        date_refreshes=refreshes,
        regular_cadence=summary.regular_cadence,
        total_live_days=total,
        first_start=earliest,
        history_days=(now - first_seen).days if first_seen else 0,
    )


def _origin(row: dict, now: datetime) -> OriginInfo:
    if row["channel"] == "employer":
        return OriginInfo(status="is_origin", feed=row["source"], checked_at=parse_datetime(row["last_seen"]))
    if not row.get("company_id"):
        return OriginInfo(note="Employer unknown, so the employer's own site could not be checked.")
    runs = [r for r in db.feed_runs(row["company_id"]) if r["ok"] and r["complete"]]
    if not runs:
        extra = json.loads(row["extra"]) if row.get("extra") else {}
        if extra.get("employer_apply_link"):
            return OriginInfo(status="present", feed="employer site (via Google for Jobs)",
                              checked_at=parse_datetime(row["last_seen"]))
        return OriginInfo(note="No public job feed found for this employer, so its own site could not be checked.")
    last = runs[-1]
    run_at = parse_datetime(last["run_at"])
    employer_rows = [r for r in db.company_posting_rows(row["company_id"], light=True) if r["channel"] == "employer"]
    active = [r for r in employer_rows if r["status"] == "active"]
    for cand in employer_rows:
        same = cand.get("cluster_id") and cand.get("cluster_id") == row.get("cluster_id")
        if not same:
            same, _ = dedup.same_job(row, cand)
        if not same:
            continue
        if cand["status"] == "active":
            return OriginInfo(status="present", feed=cand["source"], feed_jobs=len(active), checked_at=run_at)
        removed = parse_datetime(cand.get("removed_at"))
        return OriginInfo(
            status="removed", feed=cand["source"], feed_jobs=len(active), checked_at=run_at,
            removed_days=(now - removed).days if removed else None,
        )
    if run_at and now - run_at > FEED_FRESH:
        return OriginInfo(note="The employer's feed has not been checked recently.")
    return OriginInfo(status="not_found", feed=last["source"], feed_jobs=len(active), checked_at=run_at)


def build_features(
    p: Posting,
    row: dict | None,
    now: datetime,
    company_sig: CompanySignals | None,
    user: UserObservations | None = None,
    origin: OriginInfo | None = None,
) -> Features:
    t = text_analysis.analyse(p.title, p.description, p.company)
    base = baselines.baseline_for(p.title, p.description, p.region, p.extra.get("occupation"))
    if row:
        user = _with_observations(user, row["id"])
    pref = user_prefs.get()
    f = Features(now=now, text=t, baseline=base, company=company_sig, user=user, age_start=pref["age_start"],
                 chance_high=pref["chance_high"], chance_very_high=pref["chance_very_high"])
    if row:
        f.repost = _repost_info(row, now)
        f.origin = origin or _origin(row, now)
        f.is_live = row["status"] == "active"
        if not f.is_live:
            f.closed_reason = "The posting is no longer in the source it came from."
    elif origin:
        f.origin = origin

    candidates = [d for d in (p.posted_at, f.repost.first_start) if d]
    if user and user.posted_date_shown:
        candidates.append(parse_datetime(user.posted_date_shown))
    if row and row.get("first_seen"):
        candidates.append(parse_datetime(row["first_seen"]))
    candidates = [c for c in candidates if c and c <= now + timedelta(days=1)]
    if candidates:
        f.first_published = min(candidates)
        f.first_published_is_lower_bound = bool(p.posted_at_is_lower_bound and f.first_published == p.posted_at)
        f.live_days = max(0, (now - f.first_published).days)
    total = max(f.live_days or 0, f.repost.total_live_days or 0) if f.live_days is not None else None
    if total is not None and base.expected_days:
        f.live_days = total
        f.excess_ratio = round(total / base.expected_days, 2)
        if base.kldb:
            info = survival.model(now).tail(total, base.kldb, base.level_code, p.channel, bool(p.agency_flag))
            if info:
                f.empirical_tail, f.tail_group, f.tail_spells = info["tail"], info["group"], info["spells"]

    if p.valid_through and p.valid_through < now:
        f.valid_through_overrun_days = (now - p.valid_through).days
    if p.valid_through and p.posted_at and (p.valid_through - p.posted_at).days > 300:
        f.valid_through_placeholder = True
    start = p.start_date or t.start_date
    if start and not (p.start_immediate or t.start_immediate) and start < now.date():
        f.start_overrun_days = (now.date() - start).days

    f.outside_germany = geo.outside_germany(p.location or p.city)
    employer_type = company_sig.employer_type if company_sig else None
    f.is_agency = bool(p.agency_flag) or bool(t.agency) or employer_type == "agency"
    f.is_public = bool(t.public_sector) or employer_type == "public"
    f.crowd = company_analysis.crowd_for_posting(row["id"] if row else None, now)
    return f


def _with_observations(user: UserObservations | None, posting_id: int) -> UserObservations | None:
    """Fill gaps in what the user entered with the latest platform observation captured for this posting."""
    obs = db.observation_rows(posting_id)
    if not obs:
        return user
    latest = obs[-1]
    merged = user.model_copy() if user else UserObservations()
    counted = [o for o in obs if o.get("applicants") is not None]
    if merged.applicant_count is None and counted:
        last = counted[-1]
        merged.applicant_count = last["applicants"]
        merged.applicant_bound = last.get("applicants_bound") if last.get("applicants_bound") in {"over", "first"} else None
        merged.clicks = bool(last.get("clicks")) or None
    if merged.reposted_label is None and any(o.get("reposted") for o in obs):
        merged.reposted_label = True
    if merged.responsiveness is None and latest.get("responsiveness"):
        merged.responsiveness = latest["responsiveness"]
    return merged


def copies_of(row: dict) -> list[CopyInfo]:
    """Every place the same job was seen (employer feed, LinkedIn, Bundesagentur, ...), oldest first."""
    rows = db.cluster_rows(row["cluster_id"]) if row.get("cluster_id") else [row]
    out = [
        CopyInfo(
            posting_id=r["id"], source=r["source"], channel=r["channel"], status=r["status"], url=r.get("url"),
            posted_at=parse_datetime(r.get("posted_at")), first_seen=parse_datetime(r.get("first_seen")),
            last_seen=parse_datetime(r.get("last_seen")), removed_at=parse_datetime(r.get("removed_at")),
        )
        for r in rows
    ]
    return sorted(out, key=lambda c: c.posted_at or c.first_seen or utcnow())


def one_per_job(items: list[ScoredPosting], rows: list[dict]) -> list[ScoredPosting]:
    """Collapse copies of the same job (same employer and job cluster) into one entry.

    The employer's own listing represents the job when it exists; otherwise the copy carrying the most
    evidence (highest score, then fullest description) does. Every copy stays visible through `copies`.
    """
    cluster_of = {r["id"]: (r.get("company_id"), r.get("cluster_id") or r["id"]) for r in rows if r}

    def rank(sp: ScoredPosting) -> tuple:
        return (sp.posting.channel == "employer", sp.score.risk, len(sp.posting.description or ""))

    best: dict[tuple, ScoredPosting] = {}
    for item in items:
        key = cluster_of.get(item.posting_id, (None, item.posting_id))
        if key not in best or rank(item) > rank(best[key]):
            best[key] = item
    return list(best.values())


def score_row(row: dict, now: datetime, company_sig: CompanySignals | None, user: UserObservations | None = None) -> ScoredPosting:
    p = db.row_to_posting(row)
    f = build_features(p, row, now, company_sig, user)
    sp = ScoredPosting(posting_id=row["id"], posting=p, features=f, score=scoring.score(p, f), copies=copies_of(row))
    sp.estimate = ml_model.estimate(sp)
    return sp


# --------------------------------------------------------------------------- company context


NEWS_TIMEOUT = 45.0  # budget for one background news lookup
NEWS_WAIT = 0.4  # answer at once unless the news is already cached
NEWS_FRESH = timedelta(hours=24)
_BACKGROUND: set[asyncio.Task] = set()
_NEWS: dict[int, dict] = {}  # company_id -> {"task", "started"}


async def _fetch_news(client: PoliteClient, company_id: int, name: str) -> str:
    """Fetch and store company news; returns the status. GDELT is slow, so this runs in the background."""
    events: list[dict] = []
    status = "error: no attempt"
    for attempt in range(2):
        try:
            events, status = await asyncio.wait_for(news.company_events(client, name), timeout=NEWS_TIMEOUT)
        except asyncio.TimeoutError:
            return "timeout"
        if status == "rate_limited" and attempt == 0:
            await asyncio.sleep(7)
            continue
        break
    if events:
        db.add_events(company_id, events)
    if status == "ok":
        db.update_company(company_id, news_checked_at=utcnow().isoformat())
    return status


def known_news_status(company_id: int | None) -> str:
    """News status for scoring views that did not start a lookup themselves."""
    if not company_id:
        return "not_checked"
    state = _NEWS.get(company_id)
    if state:
        return _task_status(state["task"])
    company = db.get_company(company_id) or {}
    checked = parse_datetime(company.get("news_checked_at"))
    return "ok" if checked and utcnow() - checked < NEWS_FRESH else "not_checked"


def _start_news(client: PoliteClient, company_id: int, name: str, enabled: bool = True) -> asyncio.Task | None:
    """Start (or reuse) the background news lookup for one employer."""
    if not enabled:
        return None
    state = _NEWS.get(company_id)
    if state:
        task = state["task"]
        if not task.done():
            return task  # a lookup is already running
        if utcnow() - state["started"] < NEWS_FRESH and not task.cancelled() and task.exception() is None \
                and task.result() == "ok":
            return task  # fresh result from today
    task = asyncio.create_task(_fetch_news(client, company_id, name))
    _NEWS[company_id] = {"task": task, "started": utcnow()}
    _BACKGROUND.add(task)  # keep a reference so the task can finish after the response is sent
    task.add_done_callback(_BACKGROUND.discard)
    return task


def _task_status(task: asyncio.Task | None) -> str:
    if task is None:
        return "not_checked"
    if not task.done():
        return "pending"
    if task.cancelled():
        return "error: cancelled"
    exc = task.exception()
    return f"error: {exc.__class__.__name__}" if exc else task.result()


def news_state(client: PoliteClient, company_id: int) -> dict | None:
    """News status and events for one employer; starts a lookup when none has run yet."""
    company = db.get_company(company_id)
    if not company:
        return None
    state = _NEWS.get(company_id)
    task = state["task"] if state else _start_news(client, company_id, company["name"])
    status = _task_status(task)
    now = utcnow()
    events = db.company_events(company_id)
    recent = [e for e in events if e.get("published_at") and (now - parse_datetime(e["published_at"])).days <= 180]
    return {
        "company_id": company_id,
        "status": status,
        "events": events[:20],
        "affects_score": any(e["kind"] in {"distress", "funding"} for e in recent),
    }


def prefetch_news(client: PoliteClient, names: list[str], limit: int = 4) -> None:
    """Warm the news cache for employers the user is likely to open next."""
    for name in names[:limit]:
        company = db.find_company(name)
        if company:
            _start_news(client, company["id"], company["name"])


async def _company_context(
    company_id: int, now: datetime, news_task: asyncio.Task | None, notes: list[str]
) -> CompanySignals:
    if news_task and not news_task.done():
        await asyncio.wait({news_task}, timeout=NEWS_WAIT)  # cached news arrives instantly
    status = _task_status(news_task)
    if status == "rate_limited":
        notes.append("News check skipped: the news service is busy. It retries automatically.")
    elif status == "timeout":
        notes.append("News check timed out. It retries automatically.")
    elif status.startswith("error"):
        notes.append(f"News check failed ({status[7:]}).")
    sig = company_analysis.signals(company_id, now)
    sig.news_status = status
    return sig


async def _ensure_feeds(
    client: PoliteClient,
    company_id: int,
    name: str,
    now: datetime,
    careers_url: str | None = None,
) -> tuple[list[ats.FeedResult], str, list[str]]:
    """Fetch the employer's ATS feeds (stored, from a careers URL, or discovered by name)."""
    notes: list[str] = []
    company = db.get_company(company_id) or {}
    refs: list[ats.FeedRef] = []
    matched_by = "stored"
    if company.get("ats") and company.get("ats_slug") and not careers_url:
        refs.append(ats.FeedRef(company["ats"], company["ats_slug"], host=company.get("ats_url") or None,
                                site=(company.get("careers_url") or None) if company["ats"] == "workday" else None))
    results: list[ats.FeedResult] = []
    if careers_url and not refs:
        matched_by = "careers URL"
        ref, _ = ats.detect_from_url(careers_url)
        if ref:
            refs.append(ref)
        else:
            try:
                page = await client.get(careers_url, ttl=6 * 3600)
                if page.ok:
                    refs.extend(ats.find_feed_links(page.text))
                    if not refs:
                        notes.append("No supported ATS feed linked from that careers page.")
            except Blocked as exc:
                notes.append(f"Careers page not fetched: {exc.reason}")
            except FetchError as exc:
                notes.append(f"Careers page not reachable: {exc}")
    for ref in refs:
        results.append(await ats.fetch_feed(client, ref, name))
    if not refs:
        matched_by = "name guess"
        results = await ats.discover(client, name)
        if results:
            notes.append(
                "The job feed was found by guessing the board name from the company name. Check that the jobs "
                "below really belong to this employer; if not, enter its careers-page URL."
            )
    good = [r for r in results if r.ok]
    for res in good:
        _store_feed(company_id, res, now)
    if good:
        first = good[0].ref
        db.update_company(company_id, ats=first.ats, ats_slug=first.slug, ats_url=first.host or "",
                          careers_url=first.site if first.ats == "workday" else (careers_url or company.get("careers_url")))
    for res in results:
        if res.error and refs:
            notes.append(f"{res.ref.ats} feed '{res.ref.slug}': {res.error}")
    return results, matched_by, notes


# --------------------------------------------------------------------------- check one posting


async def check_posting(client: PoliteClient, req: CheckRequest, progress: Progress | None = None) -> CheckResponse:
    now = utcnow()
    progress = progress or Progress("check")
    progress.add("read", "Reading the posting")
    progress.add("origin", "Employer's own channel and copies")
    progress.add("score", "Scoring against the occupation norm")
    progress.set("read", "running")
    notes: list[str] = []
    sources: list[str] = []
    posting: Posting | None = None
    mode = "fetched"
    html: str | None = None
    capture: tuple | None = None

    if req.url:
        url = req.url.strip()
        reason = blocked_reason(url)
        refnr = ba.refnr_from_url(url) if "arbeitsagentur.de" in url else None
        li_id = linkedin.job_id(url) if "linkedin.com" in url else None
        if li_id and settings.linkedin_enabled:
            posting, observed, err = await linkedin.detail(client, li_id)
            if err == "closed":
                return _closed_response(url, req, now, notes, sources)
            if err:
                notes.append(f"{err} Paste the ad text instead, or capture the job with the browser extension.")
                mode = "manual"
            else:
                sources.append("LinkedIn via linkedin-jobs-mcp")
                capture = observed
                if observed and observed[1] is not None:
                    notes.append(f"Read from the LinkedIn job page: {'over ' if observed[2] == 'over' else ''}"
                                 f"{observed[1]} applicants" + (f"; {observed[3]}" if observed[3] else "") + ".")
        elif refnr and settings.ba_jobsuche:
            posting, err = await ba.detail(client, refnr)
            if err == "closed":
                return _closed_response(url, req, now, notes, sources)
            if err:
                notes.append(err)
            else:
                sources.append("Bundesagentur Jobsuche API")
        elif reason:
            mode = "manual"
            hint = (" Or use the browser extension (extension/ folder) to capture it in one click, including "
                    "applicant counts and 'Reposted' labels.")
            notes.append(f"Not fetched automatically: {reason} Paste the ad text and what you see on the page.{hint}")
        else:
            ref, job_id = ats.detect_from_url(url)
            if ref:
                posting, closed, more = await _from_ats(client, ref, job_id, url, req.company, now)
                notes.extend(more)
                sources.append(f"{ref.ats} feed")
                if closed:
                    return _closed_response(url, req, now, notes, sources)
            if posting is None:
                try:
                    page = await client.get(url, ttl=3600)
                except Blocked as exc:
                    mode = "manual"
                    notes.append(f"Not fetched: {exc.reason} Paste the ad text instead.")
                    page = None
                except FetchError as exc:
                    mode = "error"
                    notes.append(f"Could not load the page: {exc}")
                    page = None
                if page is not None:
                    if page.status in (404, 410):
                        return _closed_response(url, req, now, notes, sources)
                    html = page.text
                    if jsonld.looks_closed(html):
                        return _closed_response(url, req, now, notes, sources)
                    found = [p for p in jsonld.extract(html, page.url) if p.title]
                    if found:
                        posting = found[0]
                        sources.append("schema.org JobPosting markup")
                        org_url = posting.extra.get("org_url")
                        posting.channel = "employer" if org_url and jsonld.same_site(org_url, page.url) else "aggregator"
                    else:
                        title, body = jsonld.page_text(html)
                        if len(body) > 200:
                            posting = Posting(source="page", source_id=page.url.split("#")[0], url=page.url,
                                              title=req.title or title, description=body, company=req.company,
                                              location=req.location, channel="aggregator")
                            sources.append("page text (no job markup)")
                            notes.append("The page has no structured job data; analysis uses its visible text.")

    if posting is None and req.text and req.text.strip():
        text = req.text.strip()
        first_line = text.splitlines()[0][:120]
        posting = Posting(
            source="manual",
            source_id=hashlib.sha1(text.encode("utf-8")).hexdigest()[:20],
            url=req.url,
            title=req.title or first_line,
            description=text,
            company=req.company,
            location=req.location,
            city=req.location,
            channel="manual",
        )
        sources.append("pasted text")
        if mode != "error":
            mode = "manual"
    if posting is None:
        if not notes:
            notes.append("Enter a job URL or paste the ad text.")
        return CheckResponse(result=None, mode="error" if mode != "manual" else "manual", notes=notes, sources_used=sources)

    if req.company and not posting.company:
        posting.company = req.company
    if req.title and not posting.title:
        posting.title = req.title
    if req.location and not (posting.city or posting.location):
        posting.location = posting.city = req.location
    if req.observations and req.observations.posted_date_shown and not posting.posted_at:
        posting.posted_at = parse_datetime(req.observations.posted_date_shown)
    progress.set("read", "done", detail=", ".join(sources) or None)
    return await _analyse(client, posting, now, _with_capture(req.observations, capture), req.with_news, notes,
                          sources, mode, html=html, company_hint=req.company, capture=capture, progress=progress)


def _with_capture(obs: UserObservations | None, capture: tuple | None) -> UserObservations | None:
    """Applicant count and repost label read from the job page, unless the user entered their own."""
    if not capture:
        return obs
    out = obs.model_copy() if obs else UserObservations()
    if out.applicant_count is None and capture[1] is not None:
        out.applicant_count = capture[1]
    if out.reposted_label is None and capture[4]:
        out.reposted_label = True
    return out


async def _analyse(
    client: PoliteClient,
    posting: Posting,
    now: datetime,
    observations: UserObservations | None,
    with_news: bool,
    notes: list[str],
    sources: list[str],
    mode: str,
    html: str | None = None,
    company_hint: str | None = None,
    capture: tuple | None = None,
    progress: Progress | None = None,
) -> CheckResponse:
    """Store one posting, check the employer's own channel and news, then score it."""
    progress = progress or Progress("check")
    progress.add("origin", "Employer's own channel and copies")
    progress.add("score", "Scoring against the occupation norm")
    progress.set("origin", "running")
    (posting_id,) = ingest([posting], company_hint, now)
    if capture:
        db.add_observation(posting_id, *capture)
    row = db.get_posting_row(posting_id)
    company_sig = None
    if row and row.get("company_id"):
        name = db.get_company(row["company_id"])["name"]
        news_task = _start_news(client, row["company_id"], name, with_news)
        if posting.channel != "employer":
            careers = None
            if html:
                links = ats.find_feed_links(html)
                if links:
                    careers = links[0].public_url
            _, _, more = await _ensure_feeds(client, row["company_id"], name, now, careers_url=careers)
            notes.extend(more)
            row = db.get_posting_row(posting_id)
        company_sig = await _company_context(row["company_id"], now, news_task, notes)
        if company_sig.news_status == "ok":
            sources.append("GDELT news")
        progress.set("origin", "done", detail=f"{len(copies_of(row))} cop{'y' if len(copies_of(row)) == 1 else 'ies'} of this job")
    else:
        notes.append("Employer name unknown: enter it to check the employer's own site, history and news.")
        progress.set("origin", "skipped", detail="employer unknown")
    progress.set("score", "running")
    f = build_features(posting, row, now, company_sig, observations)
    scored = ScoredPosting(posting_id=posting_id, posting=posting, features=f, score=scoring.score(posting, f),
                           copies=copies_of(row) if row else [])
    scored.estimate = ml_model.estimate(scored)
    progress.set("score", "done", detail=scored.score.grade_label)
    return CheckResponse(result=scored, mode=mode, notes=list(dict.fromkeys(notes)), sources_used=sources)


PLATFORMS = {"linkedin", "indeed", "stepstone", "xing", "ba", "glassdoor", "kununu", "monster", "web"}


async def capture_posting(client: PoliteClient, cap: CaptureIn, progress: Progress | None = None) -> CheckResponse:
    """Analyse a job page the user opened in their own browser (sent by the extension)."""
    now = utcnow()
    platform = cap.platform.lower() if cap.platform.lower() in PLATFORMS else "web"
    notes: list[str] = []
    sources = [f"browser capture ({platform})"]
    found = [p for p in jsonld.from_nodes(cap.jsonld, cap.url) if p.title]
    posting = found[0] if found else Posting(source=platform, source_id=cap.url, title=cap.title or "")
    job_ref = cap.job_id or (linkedin.job_id(cap.url) if platform == "linkedin" else None) or cap.url.split("#")[0]
    posting.source = platform
    posting.source_id = job_ref
    posting.url = linkedin.canonical_url(cap.url) if platform == "linkedin" else cap.url
    posting.title = posting.title or cap.title or ""
    posting.company = posting.company or cap.company
    posting.location = posting.location or cap.location
    posting.city = posting.city or (cap.location.split(",")[0].strip() if cap.location else None)
    if cap.description and len(cap.description) > len(posting.description or ""):
        posting.description = cap.description
    org_url = posting.extra.get("org_url")
    posting.channel = "employer" if platform == "web" and org_url and jsonld.same_site(org_url, cap.url) else "aggregator"
    if not posting.title:
        return CheckResponse(result=None, mode="error", notes=["No job title found on that page."], sources_used=sources)

    applicants = labels.parse_applicants(cap.applicant_text or cap.top_text)
    posted = labels.parse_posted(cap.posted_text or cap.top_text, now)
    responsiveness = labels.parse_responsiveness(cap.badges + [cap.top_text or ""])
    if posted.reposted and posted.date:
        posting.updated_at = posted.date  # a repost date says when it was refreshed, not first published
    elif not posting.posted_at and posted.date:
        posting.posted_at, posting.posted_at_is_lower_bound = posted.date, posted.lower_bound
    obs = cap.observations.model_copy() if cap.observations else UserObservations()
    if obs.applicant_count is None and applicants.count is not None:
        obs.applicant_count = applicants.count
    if obs.reposted_label is None and posted.reposted:
        obs.reposted_label = True
    if obs.responsiveness is None and responsiveness:
        obs.responsiveness = responsiveness
    bound = "over" if applicants.lower_bound else "first" if applicants.upper_bound else None
    capture = (platform, applicants.count, bound, posted.text, posted.reposted, responsiveness)
    if applicants.text:
        notes.append(f"Captured from the page: {applicants.text}" + (f"; {posted.text}" if posted.text else "") + ".")
    return await _analyse(client, posting, now, obs, cap.with_news, notes, sources, "fetched", capture=capture,
                          progress=progress)


def scored_posting(posting_id: int) -> ScoredPosting | None:
    row = db.get_posting_row(posting_id)
    if not row:
        return None
    now = utcnow()
    sig = None
    if row.get("company_id"):
        sig = company_analysis.signals(row["company_id"], now)
        sig.news_status = known_news_status(row["company_id"])
    return score_row(row, now, sig)


async def _from_ats(
    client: PoliteClient, ref: ats.FeedRef, job_id: str | None, url: str, company: str | None, now: datetime
) -> tuple[Posting | None, bool, list[str]]:
    """Resolve a job URL on an ATS through the employer's feed. Returns (posting, closed, notes)."""
    notes: list[str] = []
    feed = await ats.fetch_feed(client, ref, company)
    if not feed.ok:
        notes.append(f"{ref.ats} feed unavailable: {feed.error}")
        return None, False, notes
    # attach to the employer already tracked for this feed; otherwise prefer the name the user gave,
    # then the board's display name (Personio only offers legal-entity names), then the slug
    known = db.find_company_by_feed(ref.ats, ref.slug)
    display = feed.company_name if ref.ats in {"greenhouse", "smartrecruiters", "recruitee"} else None
    name = (known or {}).get("name") or company or display or ref.slug
    company_id = known["id"] if known else db.get_or_create_company(name)
    fields = {"ats": ref.ats, "ats_slug": ref.slug, "ats_url": ref.host or ""}
    if ref.ats == "workday":
        fields["careers_url"] = ref.site
    db.update_company(company_id, **fields)
    _store_feed(company_id, feed, now)
    match = None
    if job_id:
        for p in feed.postings:
            if p.source_id.endswith(f":{job_id}") or (p.url and job_id in p.url):
                match = p
                break
    if match and ref.ats == "workday" and match.extra.get("externalPath"):
        detail = await ats.workday_detail(client, ref, match.extra["externalPath"])
        if detail:
            detail.posted_at = detail.posted_at or match.posted_at
            match = detail
    elif ref.ats == "workday" and job_id and not match:
        match = await ats.workday_detail(client, ref, job_id)
    if match and ref.ats == "smartrecruiters" and not match.description:
        match.description = await ats.smartrecruiters_detail(client, ref.slug, job_id or "")
    if match:
        match.company = match.company or name
        return match, False, notes
    if job_id and feed.complete:
        notes.append(f"This job is not in {name}'s public {ref.ats} job list.")
        return None, True, notes
    return None, False, notes


def _closed_response(url: str, req: CheckRequest, now: datetime, notes: list[str], sources: list[str]) -> CheckResponse:
    existing = db.find_posting_row("page", url.split("#")[0]) or db.find_posting_row("jsonld", url.split("#")[0])
    if existing:
        db.mark_closed(existing["id"], now)
    p = Posting(source="page", source_id=url, url=url, title=req.title or "Job posting", company=req.company)
    f = Features(now=now, is_live=False, closed_reason="The job page says the job is removed, expired or filled.")
    notes.append("The posting is no longer online.")
    return CheckResponse(
        result=ScoredPosting(posting_id=existing["id"] if existing else None, posting=p, features=f, score=scoring.score(p, f)),
        mode="closed",
        notes=notes,
        sources_used=sources,
    )


# --------------------------------------------------------------------------- company report


async def company_report(
    client: PoliteClient, name: str, careers_url: str | None = None, with_news: bool = True,
    progress: Progress | None = None,
) -> CompanyResponse:
    now = utcnow()
    progress = progress or Progress("company")
    progress.add("feed", "Employer's own job feed")
    progress.add("platforms", "Copies on LinkedIn, Bundesagentur and Google for Jobs")
    progress.add("contracts", "Public contracts won")
    progress.add("score", "Scoring every job")
    company_id = db.get_or_create_company(name)
    news_task = _start_news(client, company_id, name, with_news)
    async with progress.step("feed", "Employer's own job feed"):
        results, matched_by, notes = await _ensure_feeds(client, company_id, name, now, careers_url)
        good = [r for r in results if r.ok]
        progress.set("feed", "done" if good else "skipped",
                     detail=", ".join(f"{r.ref.ats}: {len(r.postings)} jobs" for r in good) or "no public feed found")
    async with progress.step("platforms", "Copies on LinkedIn, Bundesagentur and Google for Jobs"):
        platform_sources = await _company_platform_copies(client, company_id, now, notes)
        progress.set("platforms", "done", detail=", ".join(platform_sources) or "none found")
    if settings.ted_contracts:
        async with progress.step("contracts", "Public contracts won"):
            found, status = await ted.contracts(client, name, now, days=user_prefs.get()["window_days"])
            if found:
                db.add_events(company_id, found)
            progress.set("contracts", "done" if status == "ok" else "failed",
                         detail=f"{len(found)} found" if status == "ok" else status)
    else:
        progress.set("contracts", "skipped", detail="switched off")
    progress.set("score", "running")
    feeds = [
        FeedSummary(ats=r.ref.ats, slug=r.ref.slug, url=r.ref.public_url, jobs=len(r.postings),
                    complete=r.complete, matched_by=matched_by, error=r.error)
        for r in results
    ]
    sig = await _company_context(company_id, now, news_task, notes)
    rows = [r for r in db.company_posting_rows(company_id) if r["status"] == "active"]
    scored = one_per_job([score_row(r, now, sig) for r in rows], rows)
    scored.sort(key=lambda s: -s.score.risk)
    flags = company_analysis.weighted_flags(s.score.grade for s in scored)
    share = company_analysis.shrunk_rate(flags, len(scored)) if scored else 0.0
    grade, grade_note = company_analysis.grade_from_share(share, len(scored))
    progress.set("score", "done", detail=f"{len(scored)} jobs")
    # search results carry no ad text: read the Bundesagentur texts in the background so wording checks can run
    text_task = start_text_task(client, rows, notes)
    return CompanyResponse(name=db.get_company(company_id)["name"], company_id=company_id, feeds=feeds, signals=sig,
                           grade=grade, grade_note=grade_note, postings=scored, notes=list(dict.fromkeys(notes)),
                           text_task=text_task)


AD_TEXT_LIMIT = 20  # detail requests per company or city view (Bundesagentur about 1/s, LinkedIn 1 per 1.5 s)
_AD_TEXT_TRIED: set[int] = set()
TEXT_SOURCES = {"ba": "Bundesagentur", "linkedin": "LinkedIn"}


def start_text_task(client: PoliteClient, rows: list[dict], notes: list[str], limit: int = AD_TEXT_LIMIT) -> str | None:
    """Read the ad texts of copies that came from search results without text, in the background."""
    enabled = {"ba": settings.ba_jobsuche, "linkedin": settings.linkedin_enabled}
    textless = [r for r in rows if r["source"] in TEXT_SOURCES and not (r.get("description") or "").strip()]
    todo = [r["id"] for r in textless if enabled[r["source"]] and r["id"] not in _AD_TEXT_TRIED][:limit]
    off = sorted({TEXT_SOURCES[r["source"]] for r in textless if not enabled[r["source"]]})
    if off:
        notes.append(f"Copies from {', '.join(off)} have no ad text and that connector is off, so wording checks "
                     "cannot run on them.")
    if not todo:
        return None
    _AD_TEXT_TRIED.update(todo)  # each posting is tried once per run, so a failed text never loops
    notes.append(f"{len(todo)} copies came from search results without ad text. The radar is reading their texts "
                 "(and LinkedIn applicant counts) in the background and will update the scores.")
    return tasks.start("Reading the ad texts", lambda p: fetch_ad_texts(client, todo, p))


async def fetch_ad_texts(client: PoliteClient, posting_ids: list[int], progress: Progress) -> dict:
    """Fill in the ad texts of Bundesagentur and LinkedIn copies that came from search results without text.
    LinkedIn pages also give the applicant count, stored as an observation; jobs LinkedIn no longer has are closed."""
    rows = [r for r in (db.get_posting_row(i) for i in posting_ids) if r]
    for r in rows:
        progress.add(f"ad:{r['id']}", (r.get("title") or "Posting")[:60])
    filled = closed = 0
    for r in rows:
        key = f"ad:{r['id']}"
        progress.set(key, "running")
        observed = None
        if r["source"] == "linkedin":
            posting, observed, err = await linkedin.detail(client, r["source_id"])
        else:
            posting, err = await ba.detail(client, r["source_id"])
        if err == "closed":
            db.mark_closed(r["id"])
            closed += 1
            progress.set(key, "done", detail=f"no longer on {TEXT_SOURCES.get(r['source'], r['source'])}")
        elif posting and (posting.description or "").strip():
            posting.company = r.get("company") or posting.company  # keep the employer the posting is filed under
            ingest([posting])
            if observed:
                db.add_observation(r["id"], *observed)
            filled += 1
            progress.set(key, "done")
        else:
            progress.set(key, "skipped" if err is None else "failed", detail=err or "no text")
    return {"filled": filled, "closed": closed, "checked": len(rows)}


async def enrich_employers(client: PoliteClient, names: list[str], progress: Progress) -> dict:
    """Look for the employers' own ATS feeds. A guessed feed is kept only if it contains at least one
    job we already know from that employer, so a namesake's board can never be attached by mistake."""
    now = utcnow()
    for name in names:
        progress.add(f"emp:{name}", name)
    found: list[str] = []
    for name in names:
        key = f"emp:{name}"
        company = db.find_company(name)
        if not company:
            progress.set(key, "skipped")
            continue
        progress.set(key, "running")
        known = {r["title_key"] for r in db.company_posting_rows(company["id"], light=True) if r.get("title_key")}
        accepted = None
        for res in await ats.discover(client, company["name"]):
            titles = {normalize_title(p.title) for p in res.postings}
            if any(dedup._key_similarity(t, k) >= 0.75 for t in titles for k in known):
                accepted = res
                break
        if accepted:
            _store_feed(company["id"], accepted, now)
            db.update_company(company["id"], ats=accepted.ref.ats, ats_slug=accepted.ref.slug,
                              ats_url=accepted.ref.host or "")
            found.append(company["name"])
            progress.set(key, "done", detail=f"{accepted.ref.ats}: {len(accepted.postings)} jobs")
        else:
            progress.set(key, "done", detail="no public job feed")
    return {"found": found}


def _same_company(candidate: str | None, target_key: str) -> bool:
    key = company_key(candidate)
    return bool(key) and (key == target_key or key.startswith(target_key + " ") or target_key.startswith(key + " "))


async def _company_platform_copies(client: PoliteClient, company_id: int, now: datetime, notes: list[str]) -> list[str]:
    """Collect the employer's postings on job platforms (LinkedIn, Google for Jobs, BA) as aggregator copies,
    so the origin check can see which copies outlive the employer's own listing."""
    name = db.get_company(company_id)["name"]
    target = company_key(name)
    searches = {
        "LinkedIn": linkedin.search(client, keyword=name, location="Germany", limit=60),
        "Google for Jobs (JSearch)": jsearch.search(client, keyword=name, city=None),
        "Bundesagentur": ba.search(client, city="", keyword=None, employer=name, pages=1),
    }
    results = await asyncio.gather(*searches.values())
    used: list[str] = []
    for label, (found, err) in zip(searches, results):
        if err and err != ba.OFF_NOTE:
            notes.append(err)
        matches = [p for p in found if _same_company(p.company, target) and not geo.outside_germany(p.location or p.city)]
        if not matches:
            continue
        for p in matches:
            p.company = name
        ingest(matches, name, now)
        used.append(f"{label} ({len(matches)})")
    return used


# --------------------------------------------------------------------------- city map


REMOTE_WORDS = ("remote", "home office", "homeoffice", "home-office", "mobiles arbeiten", "mobile work", "work from home")


def _remote(p: Posting) -> bool:
    if p.remote:
        return True
    text = f"{p.title} {p.location or ''} {p.description[:3000]}".lower()
    return any(w in text for w in REMOTE_WORDS)


async def city_report(
    client: PoliteClient,
    city: str,
    keyword: str | None = None,
    radius_km: int = 20,
    include_arbeitnow: bool = True,
    filters: SearchFilters | None = None,
    progress: Progress | None = None,
    read_texts: bool = True,
) -> CityResponse:
    now = utcnow()
    progress = progress or Progress("city")
    filters = filters or SearchFilters()
    if not include_arbeitnow and "arbeitnow" in filters.sources:
        filters.sources = [s for s in filters.sources if s != "arbeitnow"]
    wanted = set(filters.sources)
    notes: list[str] = []
    sources: list[str] = []
    center_info = geo.lookup(city) or await geo.geocode(client, city)
    center = (center_info[0], center_info[1]) if center_info else None

    collected: list[Posting] = []
    ba_facets: dict = {}
    searches = {}
    if "adzuna" in wanted:
        searches["Adzuna"] = adzuna.search(client, city, keyword, radius_km, filters=filters)
    if "linkedin" in wanted:
        searches["LinkedIn"] = linkedin.search(client, keyword=keyword or "", location=city, limit=75, filters=filters)
    if "ba" in wanted:
        searches["Bundesagentur"] = ba.search(client, city, keyword, radius_km, filters=filters, facets_out=ba_facets)
    if "jsearch" in wanted:
        searches["Google for Jobs"] = jsearch.search(client, keyword, city, filters=filters)
    if "arbeitnow" in wanted:
        searches["Arbeitnow"] = arbeitnow.search(client, city, keyword, filters=filters)
    for label in searches:
        progress.add(f"src:{label}", label)
    progress.add("merge", "Merging copies of the same job")
    progress.add("score", "Scoring every job")

    async def tracked_search(label: str, coro):
        progress.set(f"src:{label}", "running")
        found, err = await coro
        if err and err != ba.OFF_NOTE:
            progress.set(f"src:{label}", "failed", detail=err[:120])
        else:
            progress.set(f"src:{label}", "done", detail=f"{len(found)} postings")
        return found, err

    results = await asyncio.gather(*(tracked_search(label, coro) for label, coro in searches.items()))
    source_counts: dict[str, int] = {}
    for label, (found, err) in zip(searches, results):
        if err and err != ba.OFF_NOTE:
            notes.append(err if label != "Arbeitnow" else f"Arbeitnow: {err}")
        if found:
            source_counts[label] = len(found)
            sources.append(f"{label}: {len(found)}")
            collected.extend(found)
            if label == "Arbeitnow":
                notes.append("Arbeitnow's dates can be the day Arbeitnow imported a job, so ages from that source are minimums.")
    abroad = [p for p in collected if geo.outside_germany(p.location or p.city)]
    if abroad:
        collected = [p for p in collected if not geo.outside_germany(p.location or p.city)]
        notes.append(f"{len(abroad)} results outside Germany were left out.")
    if filters.remote:
        before = len(collected)
        collected = [p for p in collected if _remote(p)]
        if before - len(collected):
            notes.append(f"Remote filter: {before - len(collected)} postings without a remote or home-office mention were "
                         "left out (the Bundesagentur has no remote filter of its own).")
    progress.set("merge", "running")
    ids = ingest(collected, now=now)
    progress.set("merge", "done", detail=f"{len(collected)} postings stored")

    # employer-feed postings already tracked for this city (from company views and the watchlist)
    tracked = []
    if "tracked" in wanted:
        tracked = [
            r for r in db.city_posting_rows(geo.city_name(city) or city)
            if r["channel"] == "employer" and r["id"] not in set(ids)
            and (not keyword or keyword.lower() in (r.get("title") or "").lower())
        ]
    if tracked:
        source_counts["Employer feeds"] = len(tracked)
        sources.append(f"tracked employer feeds: {len(tracked)}")
    tracked_ids = {r["id"] for r in tracked}
    rows = [db.get_posting_row(i) for i in dict.fromkeys(ids)] + tracked
    rows = [r for r in rows if r and r["status"] == "active"]

    sig_cache: dict[int, CompanySignals | None] = {}
    scored: list[ScoredPosting] = []
    progress.set("score", "running", detail=f"0 of {len(rows)}")
    for n, row in enumerate(rows, 1):
        if n % 10 == 0:
            progress.set("score", "running", detail=f"{n} of {len(rows)}")
            await asyncio.sleep(0)  # let progress polls through
        cid = row.get("company_id")
        if cid not in sig_cache:
            sig_cache[cid] = company_analysis.signals(cid, now) if cid else None
            if sig_cache[cid] is not None:
                sig_cache[cid].news_status = known_news_status(cid)
        item = score_row(row, now, sig_cache[cid])
        if filters.exclude_agencies and item.features.is_agency:
            continue
        if filters.posted_within and row["id"] in tracked_ids and (item.features.live_days or 0) > filters.posted_within:
            continue
        p = item.posting
        if p.lat is None or p.lon is None:
            loc = geo.lookup(p.city) or geo.lookup(p.location)
            if loc:
                p.lat, p.lon = loc[0], loc[1]
            elif center:
                p.lat, p.lon = center
            p.extra["approximate_position"] = True
        if p.lat is not None and p.lon is not None:
            spread = 0.012 if p.extra.get("approximate_position") else 0.002
            dx, dy = stable_jitter(f"{p.source}:{p.source_id}", spread)
            p.lat, p.lon = p.lat + dy, p.lon + dx
        scored.append(item)
    scored = one_per_job(scored, rows)
    scored.sort(key=lambda s: -s.score.risk)

    grades: dict[str, int] = {}
    types: dict[str, int] = {}
    employers: dict[str, dict] = {}
    for s in scored:
        grades[s.score.grade] = grades.get(s.score.grade, 0) + 1
        top = max(s.score.types, key=lambda t: t.score)
        if top.score >= 0.3:
            types[top.key] = types.get(top.key, 0) + 1
        name = s.posting.company or "Unknown employer"
        entry = employers.setdefault(name, {"company": name, "count": 0, "grades": {}, "agency": False})
        entry["count"] += 1
        entry["grades"][s.score.grade] = entry["grades"].get(s.score.grade, 0) + 1
        entry["agency"] = entry["agency"] or s.features.is_agency
    ages = sorted(s.features.live_days for s in scored if s.features.live_days is not None)
    summary = {
        "total": len(scored),
        "grades": grades,
        "types": types,
        "median_age_days": ages[len(ages) // 2] if ages else None,
        "agencies": sum(1 for s in scored if s.features.is_agency),
        "sources": source_counts,
        "top_employers": sorted(employers.values(), key=lambda e: -e["count"])[:10],
        "ba_facets": ba_facets or None,
        "filters": filters.model_dump(),
    }
    progress.set("score", "done", detail=f"{len(scored)} jobs")
    by_id = {r["id"]: r for r in rows}
    shown = [by_id[s.posting_id] for s in scored if s.posting_id in by_id]  # highest ghost-risk first
    summary["text_task"] = start_text_task(client, shown, notes, limit=15) if read_texts else None
    candidates = [e["company"] for e in summary["top_employers"] if not e.get("agency")]
    prefetch_news(client, candidates)
    unknown = [n for n in candidates if (db.find_company(n) or {}).get("ats") is None][:3]
    if unknown:
        summary["enrich_task"] = tasks.start(
            "Checking the top employers' own job sites",
            lambda p: enrich_employers(client, unknown, p),
        )
    if not scored:
        notes.append("No postings found for this city with the selected sources and filters.")
    missing = [name for name, on in (("Adzuna", settings.adzuna_enabled), ("LinkedIn", settings.linkedin_enabled),
                                     ("Google for Jobs", settings.jsearch_enabled), ("Bundesagentur", settings.ba_jobsuche))
               if not on]
    if missing:
        notes.append(f"Not connected: {', '.join(missing)}.")
    return CityResponse(city=geo.city_name(city) or city, center=center, postings=scored, summary=summary,
                        notes=list(dict.fromkeys(notes)), sources_used=sources)


# --------------------------------------------------------------------------- watchlist


async def run_watch_item(client: PoliteClient, item: dict) -> dict:
    params = item.get("params") or {}
    if item["kind"] == "company":
        report = await company_report(client, item["query"], params.get("careers_url"),
                                      with_news=params.get("news", True))
        if report.company_id:
            await refresh_linkedin_observations(client, report.company_id)
        result = {
            "postings": len(report.postings),
            "grade": report.grade,
            "flagged": sum(1 for s in report.postings if s.score.grade in {"elevated", "high"}),
            "feeds": [f.model_dump() for f in report.feeds],
        }
    else:
        report = await city_report(client, item["query"], params.get("keyword"), int(params.get("radius", 20)))
        result = {"postings": report.summary["total"], "grades": report.summary["grades"]}
    db.watch_mark_run(item["id"], result)
    return result


def posting_history(posting_id: int) -> dict:
    row = db.get_posting_row(posting_id)
    if not row:
        return {}
    cluster = db.cluster_rows(row["cluster_id"]) if row.get("cluster_id") else [row]
    return {
        "sightings": db.sightings(posting_id)[-200:],
        "instances": [
            {k: r.get(k) for k in ("id", "source", "source_id", "url", "channel", "title", "first_seen",
                                   "last_seen", "status", "removed_at", "posted_at")}
            for r in cluster
        ],
    }


def posting_timeline(posting_id: int) -> dict | None:
    """Everything needed to draw a posting's life: every copy, platform observations and key dates."""
    scored = scored_posting(posting_id)
    if scored is None:
        return None
    row = db.get_posting_row(posting_id)
    cluster = db.cluster_rows(row["cluster_id"]) if row.get("cluster_id") else [row]
    now = scored.features.now
    instances = []
    for r in cluster:
        start = parse_datetime(r.get("posted_at")) or parse_datetime(r["first_seen"])
        first_seen = parse_datetime(r["first_seen"])
        if first_seen and start and first_seen < start:
            start = first_seen
        instances.append({
            "posting_id": r["id"], "source": r["source"], "channel": r["channel"], "status": r["status"],
            "url": r.get("url"), "start": start, "first_seen": first_seen, "last_seen": parse_datetime(r["last_seen"]),
            "end": parse_datetime(r.get("removed_at")) if r["status"] == "removed" else None,
            "sightings": len(db.sightings(r["id"])),
        })
    observations = []
    for r in cluster:
        for o in db.observation_rows(r["id"]):
            observations.append({"at": parse_datetime(o["seen_at"]), "applicants": o.get("applicants"),
                                 "bound": o.get("applicants_bound"), "reposted": bool(o.get("reposted")),
                                 "platform": o.get("platform")})
    f = scored.features
    p = scored.posting
    expected_end = None
    if f.first_published and f.baseline.expected_days:
        expected_end = f.first_published + timedelta(days=f.baseline.expected_days)
    return {
        "now": now,
        "first_published": f.first_published,
        "expected_days": f.baseline.expected_days,
        "expected_end": expected_end,
        "start_date": p.start_date or f.text.start_date,
        "valid_through": None if f.valid_through_placeholder else p.valid_through,
        "deadline": f.text.application_deadline,
        "instances": sorted(instances, key=lambda i: i["start"] or now),
        "observations": sorted(observations, key=lambda o: o["at"]),
        "grade": scored.score.grade,
    }


# --------------------------------------------------------------------------- overview


OVERVIEW_LIMIT = 1500  # most recently seen active postings that the overview scores
OVERVIEW_JOBS = 600  # jobs sent to the dashboard (highest ghost-risk first)
OVERVIEW_TTL = timedelta(minutes=10)
_OVERVIEW: dict = {"key": None, "at": None, "data": None}
SOURCE_GROUPS = {"linkedin": "LinkedIn", "ba": "Bundesagentur"}


def source_group(p: Posting) -> str:
    """The radar sector a job belongs to: the employer's own site, LinkedIn, the Bundesagentur or other boards."""
    if p.channel == "employer" and p.source not in {"manual", "page"}:
        return "Employer sites"
    return SOURCE_GROUPS.get(p.source, "Other boards")


def overview(now: datetime | None = None) -> dict:
    """Everything the radar has stored, scored: grades, ages against the norm, employers, cities, sources.

    Results are cached until the database changes (or for at most ten minutes).
    """
    now = now or utcnow()
    key = db.data_fingerprint()
    cached = _OVERVIEW
    if cached["key"] == key and cached["at"] and now - cached["at"] < OVERVIEW_TTL:
        return cached["data"]
    rows = db.recent_active_rows(OVERVIEW_LIMIT)
    sig_cache: dict[int, CompanySignals | None] = {}
    scored: list[ScoredPosting] = []
    for row in rows:
        cid = row.get("company_id")
        if cid not in sig_cache:
            sig_cache[cid] = company_analysis.signals(cid, now) if cid else None
            if sig_cache[cid] is not None:
                sig_cache[cid].news_status = known_news_status(cid)
        scored.append(score_row(row, now, sig_cache[cid]))
    jobs = [s for s in one_per_job(scored, rows) if not s.features.outside_germany]
    jobs.sort(key=lambda s: -s.score.risk)
    _OVERVIEW["jobs_all"] = jobs

    grades: dict[str, int] = {}
    types: dict[str, int] = {}
    groups: dict[str, int] = {}
    employers: dict[str, dict] = {}
    cities: dict[str, dict] = {}
    months: dict[str, int] = {}
    evidence: list[int] = []
    for s in jobs:
        grade = s.score.grade
        grades[grade] = grades.get(grade, 0) + 1
        top = max(s.score.types, key=lambda t: t.score)
        if top.score >= 0.3:
            types[top.key] = types.get(top.key, 0) + 1
        group = source_group(s.posting)
        groups[group] = groups.get(group, 0) + 1
        name = s.posting.company or "Unknown employer"
        entry = employers.setdefault(name, {"company": name, "count": 0, "grades": {}, "agency": False})
        entry["count"] += 1
        entry["grades"][grade] = entry["grades"].get(grade, 0) + 1
        entry["agency"] = entry["agency"] or s.features.is_agency
        city = geo.city_name(s.posting.city) or s.posting.city or "Unknown"
        centry = cities.setdefault(city, {"company": city, "count": 0, "grades": {}})
        centry["count"] += 1
        centry["grades"][grade] = centry["grades"].get(grade, 0) + 1
        if s.features.first_published:
            month = s.features.first_published.strftime("%Y-%m")
            months[month] = months.get(month, 0) + 1
        evidence.append(sum(1 for c in s.score.coverage if c.state == "used"))
    ratios = sorted(s.features.excess_ratio for s in jobs if s.features.excess_ratio is not None)
    ages = sorted(s.features.live_days for s in jobs if s.features.live_days is not None)
    copies: dict[str, int] = {}
    for row in rows:
        copies[row["source"]] = copies.get(row["source"], 0) + 1
    counts = db.stats()
    light = []
    for s in jobs[:OVERVIEW_JOBS]:
        item = s.model_copy(deep=True)
        item.posting.description = None
        light.append(item)
    data = {
        "generated_at": now,
        "totals": {
            "jobs": len(jobs),
            "postings": len(rows),
            "employers": len({s.posting.company for s in jobs if s.posting.company}),
            "cities": len([c for c in cities if c != "Unknown"]),
            "checks": counts["checks"],
            "removed": counts["removed"],
            "own_feeds": counts["own_feeds"],
            "observations": counts["observations"],
            "watch": counts["watch"],
            "first_seen": counts["first_seen"],
            "last_seen": counts["last_seen"],
            "limited": len(rows) >= OVERVIEW_LIMIT,
        },
        "grades": grades,
        "types": types,
        "groups": groups,
        "copies": copies,
        "median_ratio": ratios[len(ratios) // 2] if ratios else None,
        "median_days": ages[len(ages) // 2] if ages else None,
        "evidence_avg": round(sum(evidence) / len(evidence), 2) if evidence else None,
        "evidence_total": len(jobs[0].score.coverage) if jobs else 7,
        "months": dict(sorted(months.items())),
        "top_employers": sorted(employers.values(), key=lambda e: -e["count"])[:10],
        "top_cities": sorted(cities.values(), key=lambda e: -e["count"])[:8],
        "jobs": light,
    }
    _OVERVIEW.update(key=key, at=now, data=data)
    return data


# --------------------------------------------------------------------------- data science: labels, audits, model


def all_jobs() -> list[ScoredPosting]:
    """Every stored job, scored once per job (shares the overview's cache)."""
    overview()
    return _OVERVIEW.get("jobs_all") or []


def snapshot(posting_id: int) -> tuple[int | None, dict | None]:
    """The posting's score and feature vector right now, stored with a label so training never sees hindsight."""
    sp = scored_posting(posting_id)
    if sp is None or sp.score.grade == "closed":
        return None, None
    return sp.score.risk, ml_features.vector(sp)


_QUEUE: dict = {"items": []}


def audit_queue(n: int = 12, redraw: bool = False) -> dict:
    """The current audit sample (drawn per grade, probability proportional to age), minus postings already audited."""
    audited = {a["posting_id"] for a in db.audit_rows()}
    jobs = {sp.posting_id: sp for sp in all_jobs()}
    if _QUEUE.get("db") != str(settings.db_path):  # a queue belongs to one database
        _QUEUE.update(items=[], db=str(settings.db_path))
    items = [q for q in _QUEUE["items"] if q["posting_id"] not in audited and q["posting_id"] in jobs]
    if redraw or not items:
        items = [{k: v for k, v in q.items() if k != "item"} for q in ml_audit.draw(list(jobs.values()), n, audited)]
        _QUEUE["items"] = items
    return {
        "script_de": ml_audit.SCRIPT_DE,
        "script_en": ml_audit.SCRIPT_EN,
        "labels": {k: v[0] for k, v in ml_labels.AUDIT_LABELS.items()},
        "items": [{**q, "posting": jobs[q["posting_id"]]} for q in items],
    }


def record_audit(posting_id: int, label: str, method: str | None, note: str | None, inclusion_prob: float | None,
                 approval: str | None = None, manager_named: bool | None = None,
                 start_date_given: bool | None = None) -> int:
    risk, vec = snapshot(posting_id)
    return db.add_audit(posting_id, label, method, note, inclusion_prob, risk, vec, approval, manager_named,
                        start_date_given)


def model_status() -> dict:
    """Everything the model page shows: ground truth, labelling functions, survival baselines, model, prevalence."""
    jobs = all_jobs()
    gold = ml_labels.gold_labels()
    weak = [ml_labels.label_model(ml_labels.votes(sp)) for sp in jobs]
    covered = [w for w in weak if w is not None]
    lifetimes = survival.model()
    trained = ml_model.load()
    return {
        "jobs": len(jobs),
        "gold": {
            "total": len(gold),
            "ghost": sum(1 for g in gold if g["y"] == 1),
            "genuine": sum(1 for g in gold if g["y"] == 0),
            "audits": sum(1 for g in gold if g["source"] == "audit"),
            "outcomes": sum(1 for g in gold if g["source"] == "outcome"),
            "with_snapshot": sum(1 for g in gold if g.get("snapshot")),
        },
        "weak": {"covered": len(covered), "share": round(len(covered) / len(jobs), 3) if jobs else 0.0,
                 "likely_ghost": sum(1 for w in covered if w >= 0.5)},
        "labelling_functions": ml_labels.lf_report(jobs, gold),
        "survival": {**lifetimes.totals(), "groups": lifetimes.summary()},
        "model": ({k: v for k, v in trained.items() if not k.startswith("_") and k != "cov"} if trained
                  else {"trained": False, "min_labels": ml_model.MIN_LABELS, "min_per_class": ml_model.MIN_PER_CLASS}),
        "prevalence": ml_audit.prevalence(gold),
        "features": [{"name": n, "label": label} for n, label, _ in ml_features.FEATURES],
    }


# --------------------------------------------------------------------------- your employer knowledge, evidence log


def add_employer_event(company_id: int, kind: str, when, note: str | None) -> None:
    """A dated fact you learned about the employer (hiring freeze, manager left, contract won, new starters, …)."""
    category, label = EVENT_KINDS[kind]
    stamp = datetime.combine(when, datetime.min.time()).replace(tzinfo=utcnow().tzinfo)
    db.add_events(company_id, [{
        "kind": category, "subtype": kind, "title": f"{label}" + (f": {note}" if note else ""),
        "url": f"note:{kind}:{stamp.date().isoformat()}:{hashlib.sha1((note or '').encode()).hexdigest()[:8]}",
        "published_at": stamp, "source": "your note",
    }])


def import_notes(csv_text: str) -> dict:
    """Lines of company;practice;note (comma or tab also work). Practice: internal_first, external or empty."""
    added = 0
    skipped: list[str] = []
    for line in csv_text.splitlines():
        if not line.strip() or line.lower().startswith(("company", "firma", "#")):
            continue
        sep = ";" if ";" in line else "\t" if "\t" in line else ","
        parts = [p.strip() for p in line.split(sep)]
        name = parts[0]
        practice = (parts[1] if len(parts) > 1 else "").lower().replace("-", "_").replace(" ", "_")
        practice = {"internal": "internal_first", "intern": "internal_first", "extern": "external"}.get(practice, practice)
        if len(name) < 2 or practice not in {"internal_first", "external", ""}:
            skipped.append(line[:80])
            continue
        company_id = db.get_or_create_company(name)
        fields = {"practice_note": sep.join(parts[2:]).strip() or None}
        if practice:
            fields["hiring_practice"] = practice
        db.update_company(company_id, **fields)
        added += 1
    return {"added": added, "skipped": skipped}


def evidence_log(posting_id: int) -> list[dict]:
    """Every dated observation behind a posting's assessment, newest first."""
    row = db.get_posting_row(posting_id)
    if not row:
        return []
    out: list[dict] = []

    def add(when, kind: str, text: str, source: str | None = None, url: str | None = None) -> None:
        when = parse_datetime(when) if not isinstance(when, datetime) else when
        out.append({"at": when, "kind": kind, "text": text, "source": source, "url": safe_url(url)})

    cluster = db.cluster_rows(row["cluster_id"]) if row.get("cluster_id") else [row]
    for r in cluster:
        where = r["source"]
        if r.get("posted_at"):
            add(r["posted_at"], "posting", "Published", where, r.get("url"))
        add(r["first_seen"], "posting", "First seen by the radar", where, r.get("url"))
        checks = len(db.sightings(r["id"]))
        add(r["last_seen"], "posting", f"Last seen ({checks} check{'s' if checks != 1 else ''})", where)
        if r.get("removed_at"):
            add(r["removed_at"], "posting", "Removed", where)
        for o in db.observation_rows(r["id"]):
            if o.get("applicants") is not None:
                bound = {"over": "over ", "first": "fewer than "}.get(o.get("applicants_bound") or "", "")
                noun = "people clicked apply" if o.get("clicks") else "applicants"
                add(o["seen_at"], "applicants", f"{bound}{o['applicants']} {noun}" + (f" ({o['posted_text']})" if o.get("posted_text") else ""),
                    o.get("platform"))
    for rep in db.report_rows(posting_id=posting_id):
        what = {"none": "no reply yet", "auto_reject": "automatic rejection", "reject": "rejection",
                "internal": "internal candidate chosen", "interview": "interview invitation", "offer": "offer"}.get(rep.get("response") or "", "recorded")
        add(rep.get("applied_on") or rep["created_at"], "outcome", f"Your application: {what}" + (f" (stage: {rep['stage']})" if rep.get("stage") else ""), "you")
    for a in db.audit_rows():
        if a["posting_id"] == posting_id:
            add(a["created_at"], "audit", f"Audit: {a['label']}" + (f", approval {a['approval']}" if a.get("approval") else "") + (f" ({a['method']})" if a.get("method") else ""), "you")
    if row.get("company_id"):
        since = user_prefs.since(utcnow())
        events = [ev for ev in db.company_events(row["company_id"])
                  if (parse_datetime(ev.get("published_at")) or since) > since]
        contracts = [ev for ev in events if ev["kind"] == "contract" and ev.get("source") != "your note"]
        for ev in [e for e in events if e not in contracts] + contracts[:5]:  # newest contracts only
            add(ev.get("published_at"), ev["kind"], ev.get("title") or "", ev.get("source"), ev.get("url"))
        if len(contracts) > 5:
            add(contracts[5].get("published_at"), "contract",
                f"… and {len(contracts) - 5} earlier contracts", "TED")
    out = [o for o in out if o["at"]]
    out.sort(key=lambda o: o["at"], reverse=True)
    return out[:200]


def safe_url(url: str | None) -> str | None:
    return url if isinstance(url, str) and url.startswith(("http://", "https://")) else None


async def refresh_linkedin_observations(client: PoliteClient, company_id: int, max_age_days: int = 7,
                                        limit: int = 20) -> int:
    """Re-read the LinkedIn pages of an employer's open jobs once a week, so applicant counts become a curve."""
    if not settings.linkedin_enabled:
        return 0
    now = utcnow()
    done = 0
    for r in db.company_posting_rows(company_id, status="active"):
        if done >= limit:
            break
        if r["source"] != "linkedin":
            continue
        obs = db.observation_rows(r["id"])
        last = parse_datetime(obs[-1]["seen_at"]) if obs else None
        if last and (now - last).days < max_age_days:
            continue
        posting, observed, err = await linkedin.detail(client, r["source_id"])
        done += 1
        if err == "closed":
            db.mark_closed(r["id"])
        elif posting:
            if not (r.get("description") or "").strip() and posting.description:
                posting.company = r.get("company") or posting.company
                ingest([posting])
            if observed:
                db.add_observation(r["id"], *observed)
    return done
