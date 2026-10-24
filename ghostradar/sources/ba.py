"""Bundesagentur für Arbeit Jobsuche API (the Jobbörse backend, documented by github.com/bundesAPI).

Switched off by default. The BA's terms of use (§2a(3), version of 8 July 2026) ban
robots and reading out interfaces "zum Zweck der Datensammlung und -auswertung", so
only switch it on (BA_JOBSUCHE=1) with the BA's permission or for small, personal
lookups at your own risk. See docs/ba-permission-request.md.

Schema as observed on 2026-10-24: v6 search returns `ergebnisliste` items with
referenznummer, stellenangebotsTitel, firma, datumErsteVeroeffentlichung, aenderungsdatum,
eintrittszeitraum.von, stellenlokationen[].adresse/breite/laenge, verguetungsangabe,
arbeitgeberKundennummerHash; v4 jobdetails adds stellenangebotsBeschreibung and allianzpartnerName.
"""
from __future__ import annotations

import base64
import re
from datetime import timedelta

from ..config import settings
from ..http import FetchError, PoliteClient
from ..models import Posting, SearchFilters
from ..util import parse_date, parse_datetime, strip_contact_data

BASE = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service"
HEADERS = {"X-API-Key": "jobboerse-jobsuche"}
OFF_NOTE = ("Bundesagentur job board not queried: switched off (BA_JOBSUCHE=1 enables it; the BA's terms require "
            "permission for automated use).")
_REGIONS = {
    "BADEN_WUERTTEMBERG": "Baden-Württemberg", "BAYERN": "Bayern", "BERLIN": "Berlin", "BRANDENBURG": "Brandenburg",
    "BREMEN": "Bremen", "HAMBURG": "Hamburg", "HESSEN": "Hessen", "MECKLENBURG_VORPOMMERN": "Mecklenburg-Vorpommern",
    "NIEDERSACHSEN": "Niedersachsen", "NORDRHEIN_WESTFALEN": "Nordrhein-Westfalen", "RHEINLAND_PFALZ": "Rheinland-Pfalz",
    "SAARLAND": "Saarland", "SACHSEN": "Sachsen", "SACHSEN_ANHALT": "Sachsen-Anhalt",
    "SCHLESWIG_HOLSTEIN": "Schleswig-Holstein", "THUERINGEN": "Thüringen",
}
_REFNR = re.compile(r"jobdetail/([\w-]+)")


def refnr_from_url(url: str) -> str | None:
    match = _REFNR.search(url or "")
    return match.group(1) if match else None


def to_posting(item: dict) -> Posting | None:
    refnr = item.get("referenznummer") or item.get("refnr")
    title = item.get("stellenangebotsTitel") or item.get("titel")
    if not refnr or not title:
        return None
    loc = (item.get("stellenlokationen") or [{}])[0]
    addr = loc.get("adresse") or {}
    city = (addr.get("ort") or "").split(",")[0].strip() or None
    posted = parse_datetime(item.get("datumErsteVeroeffentlichung") or (item.get("veroeffentlichungszeitraum") or {}).get("von"))
    start = parse_date((item.get("eintrittszeitraum") or {}).get("von"))
    # the BA stores "ab sofort" as the publication date: only a start clearly after publication is explicit
    explicit_start = start if start and posted and start > (posted + timedelta(days=14)).date() else None
    pay = item.get("verguetungsangabe")
    employment = []
    if item.get("arbeitszeitVollzeit"):
        employment.append("Vollzeit")
    if any(item.get(k) for k in ("arbeitszeitTeilzeitVormittag", "arbeitszeitTeilzeitNachmittag",
                                 "arbeitszeitTeilzeitAbend", "arbeitszeitTeilzeitFlexibel")):
        employment.append("Teilzeit")
    if item.get("vertragsdauer") and item["vertragsdauer"] not in ("KEINE_ANGABE",):
        employment.append(str(item["vertragsdauer"]).lower())
    return Posting(
        source="ba",
        source_id=refnr,
        url=f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{refnr}",
        company=item.get("firma"),
        title=title,
        location=addr.get("ort"),
        city=city,
        region=_REGIONS.get(str(addr.get("region") or "").upper()),
        lat=loc.get("breite"),
        lon=loc.get("laenge"),
        description=strip_contact_data(item.get("stellenangebotsBeschreibung") or ""),
        posted_at=posted,
        updated_at=parse_datetime(item.get("aenderungsdatum")),
        start_date=explicit_start,
        start_immediate=bool(start and not explicit_start) or None,
        employment_type=", ".join(employment) or None,
        channel="aggregator",
        extra={
            "employer_hash": item.get("arbeitgeberKundennummerHash"),
            "occupation": item.get("hauptberuf"),
            "pay_stated": bool(pay and pay != "KEINE_ANGABEN"),
            "partner_board": item.get("allianzpartnerName"),
        },
    )


PAGE_SIZE = 50  # the API caps pages at 50 results


def _filter_params(filters: SearchFilters | None) -> dict:
    """Map shared filters to the Jobsuche parameters verified on 2026-10-24
    (veroeffentlichtseit, arbeitszeit=vz|tz, befristung=1, zeitarbeit, pav). It has no remote filter."""
    if not filters:
        return {}
    params: dict = {}
    if filters.posted_within:
        params["veroeffentlichtseit"] = filters.posted_within
    if filters.job_type == "full_time":
        params["arbeitszeit"] = "vz"
    elif filters.job_type == "part_time":
        params["arbeitszeit"] = "tz"
    elif filters.job_type == "contract":
        params["befristung"] = 1
    if filters.exclude_agencies:
        params["zeitarbeit"] = "false"
        params["pav"] = "false"
    return params


async def _page(client: PoliteClient, params: dict) -> tuple[dict | None, str | None]:
    try:
        resp = await client.get(f"{BASE}/pc/v6/jobs", params=params, headers=HEADERS, ttl=3 * 3600,
                                check_robots=False, allow_blocked=True)
    except FetchError as exc:
        return None, f"Bundesagentur API not reachable: {exc}"
    if not resp.ok:
        return None, f"Bundesagentur API returned HTTP {resp.status}."
    return resp.json(), None


def summarise_facets(facets: dict, total: int | None) -> dict:
    """Top employers, partner-board share and recency buckets for the searched area."""
    employers = (facets.get("arbeitgeber") or {}).get("counts") or {}
    partner = (facets.get("externestellenboersen") or {}).get("counts") or {}
    recency = (facets.get("veroeffentlichtseit") or {}).get("counts") or {}
    agency = (facets.get("pav") or {}).get("counts") or {}
    top = sorted(employers.items(), key=lambda kv: -kv[1])[:10]
    return {
        "total": total,
        "top_employers": [{"company": name, "count": count} for name, count in top],
        "partner_board_share": round(partner.get("true", 0) / max(1, partner.get("true", 0) + partner.get("false", 0)), 3),
        "private_recruiter_share": round(agency.get("true", 0) / max(1, agency.get("true", 0) + agency.get("false", 0)), 3),
        "published_last_7_days": recency.get("7"),
        "published_last_28_days": recency.get("28"),
    }


async def search(
    client: PoliteClient, city: str, keyword: str | None = None, radius_km: int = 20, pages: int = 2,
    employer: str | None = None, filters: SearchFilters | None = None, facets_out: dict | None = None,
) -> tuple[list[Posting], str | None]:
    if not settings.ba_jobsuche:
        return [], OFF_NOTE
    base = {"wo": city or None, "umkreis": radius_km if city else None, "was": keyword or employer or None,
            "angebotsart": 1, "size": PAGE_SIZE, **_filter_params(filters)}
    postings: list[Posting] = []
    for page in range(1, pages + 1):
        data, err = await _page(client, {**base, "page": page})
        if err:
            return postings, err
        if page == 1 and facets_out is not None:
            facets_out.update(summarise_facets(data.get("facetten") or {}, data.get("maxErgebnisse")))
        items = data.get("ergebnisliste") or []
        postings.extend(p for p in (to_posting(i) for i in items) if p)
        if len(items) < PAGE_SIZE:
            break
    # the result list has no per-posting agency flag, so ask once more for temp agencies and private recruiters
    if postings and not (filters and filters.exclude_agencies):
        by_ref = {p.source_id: p for p in postings}
        for flag in ("zeitarbeit", "pav"):
            data, err = await _page(client, {**base, flag: "true", "page": 1})
            for item in (data or {}).get("ergebnisliste") or []:
                hit = by_ref.get(item.get("referenznummer"))
                if hit:
                    hit.agency_flag = True
                    hit.extra["ba_flag"] = "Zeitarbeit" if flag == "zeitarbeit" else "private Arbeitsvermittlung"
    return postings, None


async def detail(client: PoliteClient, refnr: str) -> tuple[Posting | None, str | None]:
    if not settings.ba_jobsuche:
        return None, OFF_NOTE
    encoded = base64.b64encode(refnr.encode()).decode()
    try:
        resp = await client.get(f"{BASE}/pc/v4/jobdetails/{encoded}", headers=HEADERS, ttl=6 * 3600,
                                check_robots=False, allow_blocked=True)
    except FetchError as exc:
        return None, f"Bundesagentur API not reachable: {exc}"
    if resp.status in (404, 410):
        return None, "closed"
    if not resp.ok:
        return None, f"Bundesagentur API returned HTTP {resp.status}."
    return to_posting(resp.json()), None
