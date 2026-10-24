"""Company news from the GDELT DOC API (free, attribution required, max one request per 5 s).

News only provides context: distress (layoffs, insolvency, hiring freeze) and
funding events. Matching is by company name, so results can include other
organisations with similar names; the dashboard links every headline.
"""
from __future__ import annotations

import re

from ..http import FetchError, PoliteClient
from ..util import parse_datetime

API = "https://api.gdeltproject.org/api/v2/doc/doc"

DISTRESS = re.compile(
    r"stellenabbau|entlass|kündigungswelle|insolvenz|kurzarbeit|einstellungsstopp|restrukturierung|sparprogramm|"
    r"stellen streich|streicht \d|abbau von \d|werksschließung|standortschließung|layoff|lay off|job cuts|cuts? \d+ jobs|"
    r"hiring freeze|restructuring|insolvency|bankrupt|redundanc|plant closure",
    re.I,
)
FUNDING = re.compile(
    r"finanzierungsrunde|series [a-e]\b|seed-?runde|seed round|raises? \$|raises? €|sammelt \d|millionen.{0,20}investor|"
    r"funding round|investment round|börsengang|\bipo\b|venture capital",
    re.I,
)
GROWTH = re.compile(
    r"neue arbeitsplätze|stellen schaffen|schafft \d+|einstellungsoffensive|expansion|neues werk|neuer standort|"
    r"hiring spree|new jobs|expands|eröffnet",
    re.I,
)

QUERY_TERMS = (
    "(Stellenabbau OR Entlassungen OR Insolvenz OR Kurzarbeit OR Einstellungsstopp OR layoffs "
    'OR "hiring freeze" OR Finanzierungsrunde OR funding OR Expansion)'
)


def classify(title: str) -> str | None:
    if DISTRESS.search(title):
        return "distress"
    if FUNDING.search(title):
        return "funding"
    if GROWTH.search(title):
        return "growth"
    return None


async def company_events(client: PoliteClient, company: str, months: int = 6) -> tuple[list[dict], str]:
    """Return (events, status). Status is 'ok', 'rate_limited' or 'error: ...'."""
    name = re.sub(r'["()]', " ", company).strip()
    if len(name) < 3:
        return [], "error: company name too short for a news search"
    params = {
        "query": f'"{name}" {QUERY_TERMS}',
        "mode": "artlist",
        "maxrecords": 50,
        "format": "json",
        "timespan": f"{months}months",
        "sort": "datedesc",
    }
    try:
        resp = await client.get(
            API, params=params, ttl=24 * 3600, check_robots=False,  # documented public API
            cache_check=lambda r: r.body.lstrip()[:1] in (b"{", b"["),
        )
    except FetchError as exc:
        return [], f"error: {exc}"
    if resp.status == 429:
        return [], "rate_limited"
    if not resp.ok:
        return [], f"error: HTTP {resp.status}"
    if "json" not in resp.content_type and resp.text.lstrip().startswith("Please limit"):
        return [], "rate_limited"
    try:
        data = resp.json()
    except ValueError:
        return [], "rate_limited" if "limit requests" in resp.text else "error: unexpected response"
    events: list[dict] = []
    seen: set[str] = set()
    for art in data.get("articles", []) or []:
        title = (art.get("title") or "").strip()
        kind = classify(title)
        if not kind or title.lower() in seen:
            continue
        seen.add(title.lower())
        events.append(
            {
                "kind": kind,
                "title": title,
                "url": art.get("url"),
                "published_at": parse_datetime(art.get("seendate")),
                "source": art.get("domain"),
            }
        )
    return events[:20], "ok"


_AMOUNT = re.compile(
    r"(?:(?:€|eur|euro|\$|usd)\s?)?(\d+(?:[.,]\d+)?)\s?(mrd\.?|milliarden|billion|bn|mio\.?|millionen|million|m)\b"
    r"\s?(?:€|euro|eur|\$|dollar|usd)?", re.I)
_ROUND = re.compile(r"\b(pre-?seed|seed|series [a-f]|serie [a-f]|börsengang|ipo|growth round)\b", re.I)


def funding_details(title: str) -> str | None:
    """'€12M, Series A' from a funding headline, when it states them."""
    parts = []
    amount = _AMOUNT.search(title or "")
    if amount:
        unit = amount.group(2).lower()
        scale = "B" if unit.startswith(("mrd", "milliard", "billion", "bn")) else "M"
        currency = "$" if re.search(r"\$|usd|dollar", amount.group(0), re.I) else "€"
        parts.append(f"{currency}{amount.group(1).replace(',', '.')}{scale}")
    found = _ROUND.search(title or "")
    if found:
        parts.append(found.group(1).title().replace("Serie ", "Series "))
    return ", ".join(parts) or None
