"""Employer ATS feeds: the employer's own channel, with exact first-publication dates.

Documented public job-board APIs (Greenhouse, Lever, SmartRecruiters, Ashby, Recruitee) are
called without a robots.txt lookup; the Personio feed and the unofficial Workday endpoints sit on
tenant web hosts and keep it.

Endpoints and fields as verified on 2026-10-24 (research notes, data sources §3):
Personio XML (createdAt), Greenhouse Job Board API (first_published,
requisition_id), Lever postings API (createdAt), SmartRecruiters Posting API
(releasedDate, refNumber), Ashby posting API (publishedAt), Recruitee careers
API (published_at, close_at; token required from 10 Feb 2027) and Workday CXS
(unofficial; its startDate is the posting date). A 401/404 on a whole feed means
"no public feed", never "all jobs closed".
"""
from __future__ import annotations

import asyncio
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import parse_qs, urlsplit

from ..http import Blocked, FetchError, PoliteClient
from ..models import Posting
from ..util import html_to_text, parse_datetime, parse_relative_posted, slug_candidates, utcnow

MAX_JOBS = 600
FEED_TTL = 3 * 3600


@dataclass
class FeedRef:
    ats: str
    slug: str
    host: str | None = None  # Lever EU host, Workday tenant host
    site: str | None = None  # Workday site

    @property
    def key(self) -> str:
        return f"{self.ats}:{self.host or ''}:{self.slug}:{self.site or ''}"

    @property
    def public_url(self) -> str:
        return {
            "personio": f"https://{self.slug}.jobs.personio.de/",
            "greenhouse": f"https://boards.greenhouse.io/{self.slug}",
            "lever": f"https://jobs.{'eu.' if self.host and 'eu' in self.host else ''}lever.co/{self.slug}",
            "smartrecruiters": f"https://careers.smartrecruiters.com/{self.slug}",
            "ashby": f"https://jobs.ashbyhq.com/{self.slug}",
            "recruitee": f"https://{self.slug}.recruitee.com/",
            "workday": f"https://{self.host}/{self.site}" if self.host else "",
        }.get(self.ats, "")


@dataclass
class FeedResult:
    ref: FeedRef
    postings: list[Posting] = field(default_factory=list)
    complete: bool = False
    error: str | None = None
    company_name: str | None = None
    fetched_at: datetime = field(default_factory=utcnow)

    @property
    def ok(self) -> bool:
        return self.error is None


# --------------------------------------------------------------------------- URL detection

_WORKDAY = re.compile(r"^(?P<tenant>[\w-]+)\.(?P<wd>wd\d+)\.myworkdayjobs\.com$", re.I)


def detect_from_url(url: str) -> tuple[FeedRef | None, str | None]:
    """Recognise an ATS job URL. Returns (feed, job id in that feed)."""
    parts = urlsplit(url.strip())
    host = (parts.hostname or "").lower()
    segs = [s for s in parts.path.split("/") if s]
    query = parse_qs(parts.query)

    if host.endswith("greenhouse.io"):
        if "for" in query:
            return FeedRef("greenhouse", query["for"][0]), (query.get("token") or [None])[0]
        if segs:
            job = segs[2] if len(segs) >= 3 and segs[1] == "jobs" else None
            return FeedRef("greenhouse", segs[0]), job
    if host in {"jobs.lever.co", "jobs.eu.lever.co"} and segs:
        api = "api.eu.lever.co" if ".eu." in host else "api.lever.co"
        return FeedRef("lever", segs[0], host=api), segs[1] if len(segs) > 1 else None
    if host.endswith(".jobs.personio.de") or host.endswith(".jobs.personio.com"):
        slug = host.split(".")[0]
        job = segs[1] if len(segs) >= 2 and segs[0] == "job" else None
        return FeedRef("personio", slug), job
    if host in {"jobs.smartrecruiters.com", "careers.smartrecruiters.com"} and segs:
        job = None
        if len(segs) > 1:
            match = re.match(r"(\d+)", segs[1])
            job = match.group(1) if match else None
        return FeedRef("smartrecruiters", segs[0]), job
    if host == "jobs.ashbyhq.com" and segs:
        return FeedRef("ashby", segs[0]), segs[1] if len(segs) > 1 else None
    if host.endswith(".recruitee.com"):
        slug = host.split(".")[0]
        job = segs[1] if len(segs) >= 2 and segs[0] == "o" else None
        return FeedRef("recruitee", slug), job
    match = _WORKDAY.match(host)
    if match and segs:
        if re.match(r"^[a-z]{2}-[A-Z]{2}$", segs[0]):
            segs = segs[1:]
        if segs:
            site = segs[0]
            external = "/" + "/".join(segs[1:]) if len(segs) > 1 else None
            return FeedRef("workday", match["tenant"], host=host, site=site), external
    if "gh_jid" in query:
        return None, query["gh_jid"][0]
    return None, None


_LINK_PATTERNS = [
    (re.compile(r"(?:boards|job-boards)(?:\.eu)?\.greenhouse\.io/(?:embed/job_board\?for=)?([\w-]+)", re.I), "greenhouse"),
    (re.compile(r"greenhouse\.io/embed/job_board/js\?for=([\w-]+)", re.I), "greenhouse"),
    (re.compile(r"jobs\.(eu\.)?lever\.co/([\w.-]+)", re.I), "lever"),
    (re.compile(r"([\w-]+)\.jobs\.personio\.(?:de|com)", re.I), "personio"),
    (re.compile(r"(?:careers|jobs)\.smartrecruiters\.com/([\w-]+)", re.I), "smartrecruiters"),
    (re.compile(r"jobs\.ashbyhq\.com/([\w.-]+)", re.I), "ashby"),
    (re.compile(r"([\w-]+)\.recruitee\.com", re.I), "recruitee"),
    (re.compile(r"([\w-]+)\.(wd\d+)\.myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?([\w-]+)", re.I), "workday"),
]
_IGNORE_SLUGS = {"embed", "www", "api", "jobs", "careers", "static", "assets", "boards", "cdn"}


def find_feed_links(html: str) -> list[FeedRef]:
    """ATS boards linked from a careers page."""
    refs: dict[str, FeedRef] = {}
    for pattern, ats in _LINK_PATTERNS:
        for match in pattern.finditer(html):
            if ats == "lever":
                ref = FeedRef("lever", match[2], host="api.eu.lever.co" if match[1] else "api.lever.co")
            elif ats == "workday":
                ref = FeedRef("workday", match[1], host=f"{match[1]}.{match[2]}.myworkdayjobs.com", site=match[3])
            else:
                ref = FeedRef(ats, match[1])
            if ref.slug.lower() in _IGNORE_SLUGS:
                continue
            refs.setdefault(ref.key, ref)
    return list(refs.values())[:6]


# --------------------------------------------------------------------------- fetchers


async def fetch_feed(client: PoliteClient, ref: FeedRef, company: str | None = None) -> FeedResult:
    fetcher = {
        "personio": _personio,
        "greenhouse": _greenhouse,
        "lever": _lever,
        "smartrecruiters": _smartrecruiters,
        "ashby": _ashby,
        "recruitee": _recruitee,
        "workday": _workday,
    }.get(ref.ats)
    if fetcher is None:
        return FeedResult(ref, error=f"Unsupported ATS {ref.ats}")
    try:
        result = await fetcher(client, ref)
    except Blocked as exc:
        return FeedResult(ref, error=exc.reason)
    except FetchError as exc:
        return FeedResult(ref, error=str(exc))
    except (ValueError, KeyError, ET.ParseError) as exc:
        return FeedResult(ref, error=f"Unexpected feed format ({exc.__class__.__name__})")
    for p in result.postings:
        if not p.company:
            p.company = result.company_name or company
    return result


def _no_feed(ref: FeedRef, status: int) -> FeedResult:
    return FeedResult(ref, error=f"No public feed (HTTP {status})")


def _city(location: str | None) -> str | None:
    if not location:
        return None
    first = re.split(r"[,;/|(]| - ", location)[0].strip()
    return first or None


async def _personio(client: PoliteClient, ref: FeedRef) -> FeedResult:
    resp = await client.get(f"https://{ref.slug}.jobs.personio.de/xml", params={"language": "de"}, ttl=FEED_TTL)
    if not resp.ok or b"<workzag-jobs" not in resp.body[:500]:
        return _no_feed(ref, resp.status)
    root = ET.fromstring(resp.body)
    result = FeedResult(ref, complete=True)
    for pos in root.findall("position"):
        def txt(tag: str) -> str | None:
            el = pos.find(tag)
            return el.text.strip() if el is not None and el.text else None

        parts = []
        for desc in pos.findall("jobDescriptions/jobDescription"):
            name, value = desc.findtext("name") or "", desc.findtext("value") or ""
            parts.append(f"{name}\n{html_to_text(value)}")
        office = txt("office")
        result.company_name = result.company_name or txt("subcompany")
        result.postings.append(
            Posting(
                source="personio",
                source_id=f"{ref.slug}:{txt('id')}",
                url=f"https://{ref.slug}.jobs.personio.de/job/{txt('id')}?language=de",
                company=txt("subcompany"),
                title=txt("name") or "",
                location=office,
                city=_city(office),
                department=txt("department"),
                description="\n\n".join(parts),
                posted_at=parse_datetime(txt("createdAt")),
                employment_type=" ".join(x for x in (txt("employmentType"), txt("schedule")) if x) or None,
                channel="employer",
                extra={"seniority": txt("seniority"), "recruitingCategory": txt("recruitingCategory")},
            )
        )
    return result


async def _greenhouse(client: PoliteClient, ref: FeedRef) -> FeedResult:
    resp = await client.get(
        f"https://boards-api.greenhouse.io/v1/boards/{ref.slug}/jobs", params={"content": "true"}, ttl=FEED_TTL,
        check_robots=False,
    )
    if not resp.ok:
        return _no_feed(ref, resp.status)
    data = resp.json()
    result = FeedResult(ref, complete=True)
    meta = await client.get(f"https://boards-api.greenhouse.io/v1/boards/{ref.slug}", ttl=24 * 3600, check_robots=False)
    if meta.ok:
        result.company_name = meta.json().get("name")
    for job in data.get("jobs", []):
        loc = (job.get("location") or {}).get("name")
        depts = [d.get("name") for d in job.get("departments") or [] if d.get("name")]
        result.postings.append(
            Posting(
                source="greenhouse",
                source_id=f"{ref.slug}:{job['id']}",
                url=job.get("absolute_url"),
                company=job.get("company_name"),
                title=job.get("title") or "",
                location=loc,
                city=_city(loc),
                department=depts[0] if depts else None,
                description=html_to_text(job.get("content")),
                posted_at=parse_datetime(job.get("first_published")),
                updated_at=parse_datetime(job.get("updated_at")),
                valid_through=parse_datetime(job.get("application_deadline")),
                requisition_id=job.get("requisition_id"),
                channel="employer",
                extra={"internal_job_id": job.get("internal_job_id")},
            )
        )
    return result


async def _lever(client: PoliteClient, ref: FeedRef) -> FeedResult:
    hosts = [ref.host] if ref.host else ["api.lever.co", "api.eu.lever.co"]
    for host in hosts:
        resp = await client.get(f"https://{host}/v0/postings/{ref.slug}", params={"mode": "json"}, ttl=FEED_TTL,
                                check_robots=False)
        if resp.ok:
            ref.host = host
            break
    else:
        return _no_feed(ref, resp.status)
    result = FeedResult(ref, complete=True)
    for job in resp.json():
        cats = job.get("categories") or {}
        salary = job.get("salaryRange") or {}
        lists = "\n".join(f"{item.get('text', '')}\n{html_to_text(item.get('content'))}" for item in job.get("lists") or [])
        result.postings.append(
            Posting(
                source="lever",
                source_id=f"{ref.slug}:{job['id']}",
                url=job.get("hostedUrl"),
                title=job.get("text") or "",
                location=cats.get("location"),
                city=_city(cats.get("location")),
                department=cats.get("department") or cats.get("team"),
                description="\n".join(x for x in (job.get("descriptionPlain"), lists, job.get("additionalPlain")) if x),
                posted_at=parse_datetime(job.get("createdAt")),
                employment_type=cats.get("commitment"),
                salary_min=salary.get("min"),
                salary_max=salary.get("max"),
                salary_currency=salary.get("currency"),
                salary_period=salary.get("interval"),
                channel="employer",
                extra={"team": cats.get("team"), "workplaceType": job.get("workplaceType")},
            )
        )
    return result


async def _smartrecruiters(client: PoliteClient, ref: FeedRef) -> FeedResult:
    result = FeedResult(ref)
    offset, total = 0, None
    while total is None or offset < total:
        resp = await client.get(
            f"https://api.smartrecruiters.com/v1/companies/{ref.slug}/postings",
            params={"limit": 100, "offset": offset},
            ttl=FEED_TTL,
            check_robots=False,
        )
        if not resp.ok:
            return _no_feed(ref, resp.status) if offset == 0 else result
        data = resp.json()
        total = int(data.get("totalFound") or 0)
        if total == 0:
            return FeedResult(ref, error="No public feed (no postings)")
        for job in data.get("content", []):
            loc = job.get("location") or {}
            company = job.get("company") or {}
            result.company_name = result.company_name or company.get("name")
            result.postings.append(
                Posting(
                    source="smartrecruiters",
                    source_id=f"{ref.slug}:{job['id']}",
                    url=f"https://jobs.smartrecruiters.com/{company.get('identifier') or ref.slug}/{job['id']}",
                    company=company.get("name"),
                    title=job.get("name") or "",
                    location=loc.get("fullLocation") or ", ".join(x for x in (loc.get("city"), loc.get("country")) if x),
                    city=loc.get("city"),
                    region=loc.get("region"),
                    department=(job.get("department") or {}).get("label"),
                    posted_at=parse_datetime(job.get("releasedDate")),
                    employment_type=(job.get("typeOfEmployment") or {}).get("label"),
                    requisition_id=job.get("refNumber"),
                    remote=loc.get("remote"),
                    channel="employer",
                    extra={"experienceLevel": (job.get("experienceLevel") or {}).get("label")},
                )
            )
        offset += 100
        if offset >= MAX_JOBS:
            break
    result.complete = total is not None and offset >= total
    return result


async def smartrecruiters_detail(client: PoliteClient, slug: str, job_id: str) -> str:
    resp = await client.get(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings/{job_id}", ttl=FEED_TTL,
                            check_robots=False)
    if not resp.ok:
        return ""
    sections = ((resp.json().get("jobAd") or {}).get("sections")) or {}
    return "\n\n".join(
        f"{s.get('title', '')}\n{html_to_text(s.get('text'))}" for s in sections.values() if isinstance(s, dict)
    )


async def _ashby(client: PoliteClient, ref: FeedRef) -> FeedResult:
    resp = await client.get(
        f"https://api.ashbyhq.com/posting-api/job-board/{ref.slug}", params={"includeCompensation": "true"}, ttl=FEED_TTL,
        check_robots=False,
    )
    if not resp.ok:
        return _no_feed(ref, resp.status)
    result = FeedResult(ref, complete=True)
    for job in resp.json().get("jobs", []):
        if job.get("isListed") is False:
            continue
        address = ((job.get("address") or {}).get("postalAddress")) or {}
        comp = job.get("compensation") or {}
        salary = next(
            (c for c in comp.get("summaryComponents") or [] if c.get("compensationType") == "Salary"), {}
        )
        result.postings.append(
            Posting(
                source="ashby",
                source_id=f"{ref.slug}:{job['id']}",
                url=job.get("jobUrl"),
                title=job.get("title") or "",
                location=job.get("location"),
                city=address.get("addressLocality") or _city(job.get("location")),
                region=address.get("addressRegion"),
                department=job.get("department") or job.get("team"),
                description=job.get("descriptionPlain") or html_to_text(job.get("descriptionHtml")),
                posted_at=parse_datetime(job.get("publishedAt")),
                employment_type=job.get("employmentType"),
                salary_min=salary.get("minValue"),
                salary_max=salary.get("maxValue"),
                salary_currency=salary.get("currencyCode"),
                salary_period=salary.get("interval"),
                remote=job.get("isRemote"),
                channel="employer",
                extra={"team": job.get("team")},
            )
        )
    return result


async def _recruitee(client: PoliteClient, ref: FeedRef) -> FeedResult:
    resp = await client.get(f"https://{ref.slug}.recruitee.com/api/offers/", ttl=FEED_TTL, check_robots=False)
    if not resp.ok:
        return _no_feed(ref, resp.status)
    result = FeedResult(ref, complete=True)
    for job in resp.json().get("offers", []):
        salary = job.get("salary") or {}
        result.postings.append(
            Posting(
                source="recruitee",
                source_id=f"{ref.slug}:{job['id']}",
                url=job.get("careers_url"),
                company=job.get("company_name"),
                title=job.get("title") or "",
                location=job.get("location"),
                city=job.get("city") or _city(job.get("location")),
                region=job.get("state_name"),
                department=job.get("department"),
                description="\n\n".join(x for x in (html_to_text(job.get("description")), html_to_text(job.get("requirements"))) if x),
                posted_at=parse_datetime(job.get("published_at") or job.get("created_at")),
                updated_at=parse_datetime(job.get("updated_at")),
                valid_through=parse_datetime(job.get("close_at")),
                employment_type=job.get("employment_type_code"),
                salary_min=_num(salary.get("min")),
                salary_max=_num(salary.get("max")),
                salary_currency=salary.get("currency"),
                salary_period=salary.get("period"),
                remote=job.get("remote"),
                channel="employer",
            )
        )
    return result


def _num(value) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


async def _workday(client: PoliteClient, ref: FeedRef) -> FeedResult:
    base = f"https://{ref.host}/wday/cxs/{ref.slug}/{ref.site}"
    result = FeedResult(ref)
    offset, total = 0, None
    now = utcnow()
    while total is None or offset < total:
        resp = await client.post_json(
            f"{base}/jobs", {"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": ""}, ttl=FEED_TTL
        )
        if not resp.ok:
            return _no_feed(ref, resp.status) if offset == 0 else result
        data = resp.json()
        if total is None:
            total = int(data.get("total") or 0)
        for job in data.get("jobPostings", []):
            posted, lower = parse_relative_posted(job.get("postedOn"), now)
            path = job.get("externalPath") or ""
            req = (job.get("bulletFields") or [None])[0]
            result.postings.append(
                Posting(
                    source="workday",
                    source_id=f"{ref.slug}:{ref.site}:{path}",
                    url=f"https://{ref.host}/{ref.site}{path}",
                    title=job.get("title") or "",
                    location=job.get("locationsText"),
                    city=_city(job.get("locationsText")),
                    posted_at=posted,
                    posted_at_is_lower_bound=lower,
                    requisition_id=req,
                    channel="employer",
                    extra={"externalPath": path},
                )
            )
        offset += 20
        if offset >= min(MAX_JOBS, 300) or not data.get("jobPostings"):
            break
    result.complete = total is not None and offset >= total
    return result


async def workday_detail(client: PoliteClient, ref: FeedRef, external_path: str) -> Posting | None:
    resp = await client.get(f"https://{ref.host}/wday/cxs/{ref.slug}/{ref.site}{external_path}", ttl=FEED_TTL)
    if not resp.ok:
        return None
    data = resp.json()
    info = data.get("jobPostingInfo") or {}
    org = (data.get("hiringOrganization") or {}).get("name") or (info.get("hiringOrganization") or {}).get("name")
    return Posting(
        source="workday",
        source_id=f"{ref.slug}:{ref.site}:{external_path}",
        url=info.get("externalUrl") or f"https://{ref.host}/{ref.site}{external_path}",
        company=org,
        title=info.get("title") or "",
        location=info.get("location"),
        city=_city(info.get("location")),
        description=html_to_text(info.get("jobDescription")),
        posted_at=parse_datetime(info.get("startDate")),  # Workday's startDate is the posting date
        requisition_id=info.get("jobReqId"),
        employment_type=info.get("timeType"),
        channel="employer",
        extra={"externalPath": external_path, "endDate": info.get("endDate")},
    )


# --------------------------------------------------------------------------- discovery

_PROBE_ORDER = ["personio", "greenhouse", "lever", "smartrecruiters", "ashby", "recruitee"]


async def discover(client: PoliteClient, company: str, careers_html: str | None = None) -> list[FeedResult]:
    """Find a company's public ATS feeds: links on its careers page first, then slug guesses."""
    found: list[FeedResult] = []
    if careers_html:
        for ref in find_feed_links(careers_html):
            res = await fetch_feed(client, ref, company)
            if res.ok and res.postings:
                found.append(res)
        if found:
            return found

    async def probe_ats(ats: str) -> FeedResult | None:
        for slug in slug_candidates(company, limit=3):
            res = await fetch_feed(client, FeedRef(ats, slug), company)
            if res.ok and res.postings:
                return res
        return None

    results = await asyncio.gather(*(probe_ats(ats) for ats in _PROBE_ORDER))
    return [r for r in results if r is not None]
