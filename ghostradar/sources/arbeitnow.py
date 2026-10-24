"""Arbeitnow free job-board API (no key; "please do not abuse", link back appreciated).

Jobs come mostly from employer ATSs; the feed is ordered newest first and
`created_at` may be Arbeitnow's ingestion time rather than the employer's date.
"""
from __future__ import annotations

from ..http import FetchError, PoliteClient
from ..models import Posting, SearchFilters
from ..util import html_to_text, parse_datetime, utcnow
from .geo import matches_city

API = "https://www.arbeitnow.com/api/job-board-api"


JOB_TYPE_WORDS = {
    "full_time": ("full", "vollzeit", "unbefristet"),
    "part_time": ("part", "teilzeit", "minijob"),
    "contract": ("contract", "befristet", "freelance", "freiberuf"),
    "internship": ("intern", "praktik", "werkstudent", "trainee"),
}


async def search(
    client: PoliteClient, city: str | None = None, keyword: str | None = None, pages: int = 3,
    filters: SearchFilters | None = None,
) -> tuple[list[Posting], str | None]:
    postings: list[Posting] = []
    kw = (keyword or "").lower().strip()
    now = utcnow()
    for page in range(1, pages + 1):
        try:
            resp = await client.get(API, params={"page": page}, ttl=3600, check_robots=False)
        except FetchError as exc:
            return postings, str(exc)
        if not resp.ok:
            return postings, f"Arbeitnow returned HTTP {resp.status}"
        data = resp.json()
        for job in data.get("data", []):
            location = job.get("location") or ""
            if city and not matches_city(location, city):
                continue
            if filters:
                created = parse_datetime(job.get("created_at"))
                if filters.posted_within and created and (now - created).days > filters.posted_within:
                    continue
                if filters.remote and not job.get("remote"):
                    continue
                if filters.job_type:
                    types = " ".join(str(t) for t in job.get("job_types") or []).lower()
                    if not any(w in types for w in JOB_TYPE_WORDS[filters.job_type]):
                        continue
            text = html_to_text(job.get("description"))
            if kw and kw not in (job.get("title") or "").lower() and kw not in text.lower() and not any(
                kw in str(t).lower() for t in job.get("tags") or []
            ):
                continue
            postings.append(
                Posting(
                    source="arbeitnow",
                    source_id=job.get("slug") or job.get("url"),
                    url=job.get("url"),
                    company=job.get("company_name"),
                    title=job.get("title") or "",
                    location=location,
                    city=location.split(",")[0].strip() or None,
                    description=text,
                    posted_at=parse_datetime(job.get("created_at")),
                    employment_type=", ".join(job.get("job_types") or []) or None,
                    remote=bool(job.get("remote")) if job.get("remote") is not None else None,
                    channel="aggregator",
                    extra={"tags": job.get("tags") or [], "created_at_note": "may be ingestion time"},
                )
            )
        if not (data.get("links") or {}).get("next"):
            break
    return postings, None
