"""JSearch API (OpenWeb Ninja, sold via RapidAPI): Google for Jobs results across LinkedIn, Indeed,
Glassdoor, StepStone, XING and employer sites. Needs JSEARCH_API_KEY (free tier available).

Its `apply_options` list shows every site carrying the same job, including the employer's own
career site (`is_direct`), which feeds the cross-posting and origin checks. Field names follow the
JSearch documentation; parsing is defensive because they were not verifiable without a key.
"""
from __future__ import annotations

from ..config import settings
from ..http import FetchError, PoliteClient
from ..models import Posting, SearchFilters
from ..util import parse_datetime, strip_contact_data


def to_posting(job: dict) -> Posting | None:
    jid = job.get("job_id")
    title = job.get("job_title")
    if not jid or not title:
        return None
    options = job.get("apply_options") or []
    direct = [o for o in options if isinstance(o, dict) and o.get("is_direct")]
    employer_link = direct[0].get("apply_link") if direct else (job.get("job_apply_link") if job.get("job_apply_is_direct") else None)
    posted = parse_datetime(job.get("job_posted_at_datetime_utc") or job.get("job_posted_at_timestamp"))
    return Posting(
        source="jsearch",
        source_id=str(jid),
        url=job.get("job_apply_link") or job.get("job_google_link"),
        company=job.get("employer_name"),
        title=title,
        location=job.get("job_location") or ", ".join(x for x in (job.get("job_city"), job.get("job_state")) if x) or None,
        city=job.get("job_city"),
        region=job.get("job_state"),
        country=job.get("job_country"),
        lat=job.get("job_latitude"),
        lon=job.get("job_longitude"),
        description=strip_contact_data(job.get("job_description") or ""),
        posted_at=posted,
        valid_through=parse_datetime(job.get("job_offer_expiration_datetime_utc") or job.get("job_offer_expiration_timestamp")),
        employment_type=job.get("job_employment_type"),
        salary_min=job.get("job_min_salary"),
        salary_max=job.get("job_max_salary"),
        salary_currency=job.get("job_salary_currency"),
        salary_period=job.get("job_salary_period"),
        remote=job.get("job_is_remote"),
        channel="aggregator",
        extra={
            "publisher": job.get("job_publisher"),
            "publishers": sorted({o.get("publisher") for o in options if isinstance(o, dict) and o.get("publisher")}),
            "employer_apply_link": employer_link,
            "employer_website": job.get("employer_website"),
        },
    )


DATE_POSTED = {1: "today", 3: "3days", 7: "week", 30: "month"}
EMPLOYMENT = {"full_time": "FULLTIME", "part_time": "PARTTIME", "contract": "CONTRACTOR", "internship": "INTERN"}


async def search(
    client: PoliteClient, keyword: str | None, city: str | None, pages: int = 1, filters: SearchFilters | None = None
) -> tuple[list[Posting], str | None]:
    if not settings.jsearch_enabled:
        return [], None
    query = " ".join(x for x in (keyword, f"in {city}" if city else "in Germany") if x)
    params = {"query": query, "page": 1, "num_pages": pages, "country": "de", "date_posted": "all"}
    if filters:
        if filters.posted_within:
            params["date_posted"] = DATE_POSTED[min(DATE_POSTED, key=lambda d: abs(d - filters.posted_within))]
        if filters.job_type:
            params["employment_types"] = EMPLOYMENT[filters.job_type]
        if filters.remote:
            params["remote_jobs_only"] = "true"
    headers = {"X-RapidAPI-Key": settings.jsearch_api_key, "X-RapidAPI-Host": settings.jsearch_host}
    try:
        resp = await client.get(f"https://{settings.jsearch_host}/search", params=params, headers=headers,
                                ttl=6 * 3600, check_robots=False)
    except FetchError as exc:
        return [], f"JSearch not reachable: {exc}"
    if resp.status in (401, 403):
        return [], "JSearch rejected the API key (check JSEARCH_API_KEY and your subscription)."
    if resp.status == 429:
        return [], "JSearch quota or rate limit reached."
    if not resp.ok:
        return [], f"JSearch returned HTTP {resp.status}."
    data = resp.json().get("data") or []
    return [p for p in (to_posting(j) for j in data if isinstance(j, dict)) if p], None
