"""Adzuna job search API (Germany: country code 'de'; free key at developer.adzuna.com).

Terms: personal and academic research use is permitted; commercial analysis
requires Adzuna's written agreement; results must credit "The Adzuna API".
Descriptions are truncated to 500 characters and predicted salaries are flagged.
"""
from __future__ import annotations

from ..config import settings
from ..http import FetchError, PoliteClient
from ..models import Posting, SearchFilters
from ..util import parse_datetime

API = "https://api.adzuna.com/v1/api/jobs/de/search/{page}"


async def search(
    client: PoliteClient,
    city: str,
    keyword: str | None = None,
    distance_km: int = 20,
    pages: int = 2,
    filters: SearchFilters | None = None,
) -> tuple[list[Posting], str | None]:
    if not settings.adzuna_enabled:
        return [], "Adzuna is not configured (set ADZUNA_APP_ID and ADZUNA_APP_KEY in .env)."
    postings: list[Posting] = []
    for page in range(1, pages + 1):
        params = {
            "app_id": settings.adzuna_app_id,
            "app_key": settings.adzuna_app_key,
            "results_per_page": 50,
            "where": city,
            "distance": distance_km,
            "what": keyword or None,
            "max_days_old": filters.posted_within if filters else None,
            "content-type": "application/json",
        }
        if filters and filters.job_type in {"full_time", "part_time", "contract"}:
            params[filters.job_type] = 1  # Adzuna's full_time / part_time / contract switches
        try:
            resp = await client.get(API.format(page=page), params=params, ttl=3 * 3600, check_robots=False)
        except FetchError as exc:
            return postings, str(exc)
        if not resp.ok:
            return postings, f"Adzuna returned HTTP {resp.status}"
        results = resp.json().get("results", [])
        for job in results:
            loc = job.get("location") or {}
            area = loc.get("area") or []
            postings.append(
                Posting(
                    source="adzuna",
                    source_id=str(job.get("id")),
                    url=job.get("redirect_url"),
                    company=(job.get("company") or {}).get("display_name"),
                    title=job.get("title") or "",
                    location=loc.get("display_name"),
                    city=area[-1] if len(area) >= 3 else (area[-1] if area else None),
                    region=area[1] if len(area) >= 2 else None,
                    lat=job.get("latitude"),
                    lon=job.get("longitude"),
                    description=job.get("description") or "",
                    posted_at=parse_datetime(job.get("created")),
                    employment_type=" ".join(x for x in (job.get("contract_time"), job.get("contract_type")) if x) or None,
                    salary_min=job.get("salary_min"),
                    salary_max=job.get("salary_max"),
                    salary_currency="EUR" if job.get("salary_min") or job.get("salary_max") else None,
                    salary_predicted=str(job.get("salary_is_predicted")) == "1",
                    channel="aggregator",
                    extra={"adref": job.get("adref"), "category": (job.get("category") or {}).get("label"),
                           "description_truncated": True},
                )
            )
        if len(results) < 50:
            break
    return postings, None
