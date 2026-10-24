"""LinkedIn job listings via the linkedin-jobs-mcp REST API (github.com/GhoshSrinjoy/linkedin-job-mcp).

Start that server separately (`npm run api`, default http://localhost:3000) and set
LINKEDIN_JOBS_API in .env. It reads LinkedIn's public guest job search; LinkedIn's
terms and robots.txt prohibit automated access without permission, so keep volumes
low and use the results for your own analysis.

Response contract (api.js):
- POST /search → {"cached": bool, "total": int, "jobs": [{"position", "company", "location", "date",
  "agoTime", "salary", "jobUrl", "companyLogo"}]}
- GET /job/{id} → {"id", "position", "company", "location", "postedAgo", "applicants", "salary", "seniority",
  "employmentType", "jobFunction", "industries", "acceptingApplications", "description", "jobUrl"};
  404 with {"removed": true} when LinkedIn no longer has the job. The service fetches one job page at a time,
  at least 1.5 s apart, and caches each for 6 hours.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from ..config import settings
from ..http import FetchError, PoliteClient
from ..models import Posting, SearchFilters
from ..util import parse_datetime, strip_contact_data, utcnow
from ..analysis.labels import parse_applicants, parse_posted

OFF_NOTE = "LinkedIn not queried: connect linkedin-jobs-mcp (LINKEDIN_JOBS_API in .env)."

_ID = re.compile(r"/jobs/view/(?:[^/?#]*-)?(\d{6,})")
_MONEY = re.compile(r"[€$£]?\s?(\d{1,3}(?:[.,]\d{3})+|\d+)(?:[.,]\d{2})?\s?(k)?", re.I)


def job_id(url: str | None) -> str | None:
    if not url:
        return None
    match = _ID.search(url) or re.search(r"currentJobId=(\d{6,})", url)
    return match.group(1) if match else None


def canonical_url(url: str | None) -> str | None:
    jid = job_id(url)
    return f"https://www.linkedin.com/jobs/view/{jid}/" if jid else url


def _salary(text: str | None) -> tuple[float | None, float | None, str | None]:
    if not text or text.lower().startswith("not specified"):
        return None, None, None
    values = []
    for amount, k in _MONEY.findall(text):
        value = float(re.sub(r"[.,]", "", amount))
        values.append(value * 1000 if k else value)
    if not values:
        return None, None, None
    currency = "EUR" if "€" in text else "USD" if "$" in text else "GBP" if "£" in text else None
    return min(values), max(values), currency


def _first_line(value: str | None) -> str | None:
    """Card texts arrive with layout whitespace ("Acme\\n   \\n   "); keep the first non-empty line."""
    for line in (value or "").splitlines():
        line = " ".join(line.split())
        if line:
            return line
    return None


def from_api_job(job: dict, now: datetime) -> Posting | None:
    url = job.get("jobUrl") or ""
    jid = job_id(url)
    job = {**job, "position": _first_line(job.get("position")), "company": _first_line(job.get("company")),
           "location": _first_line(job.get("location"))}
    if not jid or not job.get("position"):
        return None
    posted = parse_datetime(job.get("date"))
    lower = False
    if posted is None and job.get("agoTime"):
        rel = parse_posted(job.get("agoTime"), now)
        posted, lower = rel.date, rel.lower_bound
    lo, hi, cur = _salary(job.get("salary"))
    location = (job.get("location") or "").strip() or None
    return Posting(
        source="linkedin",
        source_id=jid,
        url=canonical_url(url),
        company=(job.get("company") or "").strip() or None,
        title=job["position"].strip(),
        location=location,
        city=location.split(",")[0].strip() if location else None,
        posted_at=posted,
        posted_at_is_lower_bound=lower,
        salary_min=lo,
        salary_max=hi,
        salary_currency=cur,
        channel="aggregator",
        extra={"agoTime": job.get("agoTime"), "via": "linkedin-jobs-mcp"},
    )


DATE_FILTER = {1: "past 24 hours", 7: "past week", 30: "past month"}
JOB_TYPE = {"full_time": "full time", "part_time": "part time", "contract": "contract", "internship": "internship"}


async def search(
    client: PoliteClient, keyword: str = "", location: str = "Germany", limit: int = 50,
    filters: SearchFilters | None = None,
) -> tuple[list[Posting], str | None]:
    if not settings.linkedin_enabled:
        return [], None
    # name the country, or LinkedIn may resolve a city name elsewhere (Hamburg, NY) or return worldwide jobs
    place = (location or "Germany").strip()
    if not re.search(r"germany|deutschland", place, re.I):
        place = f"{place}, Germany"
    body = {"keyword": keyword or "", "location": place, "limit": limit, "sortBy": "recent"}
    if filters:
        # the linkedin-jobs-mcp API maps these to LinkedIn's f_TPR, f_JT and f_WT search parameters
        if filters.posted_within:
            body["dateSincePosted"] = DATE_FILTER.get(min(DATE_FILTER, key=lambda d: abs(d - filters.posted_within)))
        if filters.job_type:
            body["jobType"] = JOB_TYPE[filters.job_type]
        if filters.remote:
            body["remoteFilter"] = "remote"
    try:
        resp = await client.post_json(f"{settings.linkedin_jobs_api}/search", body, ttl=2 * 3600, check_robots=False)
    except FetchError as exc:
        return [], f"LinkedIn (linkedin-jobs-mcp at {settings.linkedin_jobs_api}) not reachable: start it with `npm run api`. ({exc})"
    if resp.status == 429:
        return [], "LinkedIn connector is rate-limited; try again in a minute."
    if not resp.ok:
        return [], f"LinkedIn connector returned HTTP {resp.status}."
    now = utcnow()
    postings = [p for p in (from_api_job(j, now) for j in resp.json().get("jobs", [])) if p]
    return postings, None


async def detail(client: PoliteClient, ref: str | None) -> tuple[Posting | None, tuple | None, str | None]:
    """One job's full ad text, criteria and the applicant count shown on its public page (GET /job/{id}).

    Returns (posting, observation, error). The observation is the argument tuple for db.add_observation
    (platform, applicants, bound, posted_text, reposted, responsiveness). The error is "closed" when LinkedIn no
    longer has the job or stopped accepting applications.
    """
    if not settings.linkedin_enabled:
        return None, None, OFF_NOTE
    jid = job_id(ref) or (ref if ref and ref.isdigit() else None)
    if not jid:
        return None, None, "Not a LinkedIn job link."
    try:
        resp = await client.get(f"{settings.linkedin_jobs_api}/job/{jid}", ttl=6 * 3600, check_robots=False,
                                cache_check=lambda r: "json" in (r.content_type or ""))
    except FetchError as exc:
        return None, None, (f"LinkedIn (linkedin-jobs-mcp at {settings.linkedin_jobs_api}) not reachable: start it "
                            f"with `npm run api`. ({exc})")
    data: dict = {}
    if "json" in (resp.content_type or ""):
        try:
            data = resp.json() or {}
        except ValueError:
            data = {}
    if resp.status == 404 and data.get("removed"):
        return None, None, "closed"
    if resp.status == 404:
        return None, None, ("Your linkedin-jobs-mcp has no job-details endpoint yet (GET /job/{id}); update it to "
                            "read LinkedIn ad texts.")
    if resp.status == 429:
        return None, None, "LinkedIn connector is rate-limited; try again in a minute."
    if not resp.ok:
        return None, None, f"linkedin-jobs-mcp could not read the job (HTTP {resp.status}: {data.get('error', 'no detail')})."
    if data.get("acceptingApplications") is False:
        return None, None, "closed"
    now = utcnow()
    posted = parse_posted(data.get("postedAgo"), now)
    applicants = parse_applicants(data.get("applicants"))
    location = _first_line(data.get("location"))
    lo, hi, cur = _salary(data.get("salary"))
    posting = Posting(
        source="linkedin",
        source_id=jid,
        url=f"https://www.linkedin.com/jobs/view/{jid}/",
        company=_first_line(data.get("company")),
        title=_first_line(data.get("position")) or "",
        location=location,
        city=location.split(",")[0].strip() if location else None,
        description=strip_contact_data(data.get("description") or ""),
        # a "Reposted 2 weeks ago" date says when the ad was refreshed, not when it was first published
        posted_at=None if posted.reposted else posted.date,
        posted_at_is_lower_bound=posted.lower_bound,
        updated_at=posted.date if posted.reposted else None,
        salary_min=lo,
        salary_max=hi,
        salary_currency=cur,
        employment_type=data.get("employmentType"),
        channel="aggregator",
        extra={k: v for k, v in {"seniority": data.get("seniority"), "industries": data.get("industries"),
                                 "job_function": data.get("jobFunction"), "via": "linkedin-jobs-mcp"}.items() if v},
    )
    observation = None
    if applicants.count is not None or posted.text:
        bound = "over" if applicants.lower_bound else "first" if applicants.upper_bound else None
        observation = ("linkedin", applicants.count, bound, posted.text, posted.reposted, None, applicants.clicks)
    return posting, observation, None
