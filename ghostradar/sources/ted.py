"""Public contracts won, from TED (Tenders Electronic Daily), the EU's procurement journal.

Free, documented search API (no key): https://api.ted.europa.eu/v3/notices/search. A contract award shows work
that could need staff, which is independent evidence that hiring is real. Matching is by winner name, so
group companies (for example "Siemens Healthineers AG" and "Siemens Healthineers Nederland B.V.") all count; every
entry links to its notice so it can be checked.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from ..http import FetchError, PoliteClient
from ..util import parse_datetime

API = "https://api.ted.europa.eu/v3/notices/search"
FIELDS = ["publication-number", "publication-date", "notice-title", "winner-name", "buyer-name", "notice-type"]


def _text(value) -> str:
    """TED fields come as language maps or lists; take English, then German, then anything."""
    if isinstance(value, dict):
        value = value.get("eng") or value.get("deu") or next(iter(value.values()), "")
    if isinstance(value, list):
        value = value[0] if value else ""
    return str(value or "").strip()


async def contracts(client: PoliteClient, company: str, now: datetime, days: int = 365,
                    limit: int = 100, country: str | None = "Germany") -> tuple[list[dict], str]:
    """Contract awards won from buyers in `country` in the last `days` (one year at most); returns (events, status)."""
    name = company.replace('"', " ").strip()
    if len(name) < 3:
        return [], "error: company name too short"
    since = (now - timedelta(days=min(days, 365))).strftime("%Y%m%d")
    body = {"query": f'winner-name ~ "{name}" AND publication-date >= {since}', "fields": FIELDS,
            "limit": limit, "page": 1, "scope": "ALL"}
    try:
        resp = await client.post_json(API, body, ttl=24 * 3600, check_robots=False,  # documented public API
                                      cache_check=lambda r: r.status == 200)
    except FetchError as exc:
        return [], f"error: {exc}"
    if resp.status == 429:
        return [], "rate_limited"
    if not resp.ok:
        return [], f"error: HTTP {resp.status}"
    events = []
    for notice in resp.json().get("notices", []):
        title = _text(notice.get("notice-title"))
        if country and not title.lower().startswith(country.lower()):
            continue  # notice titles start with the buyer's country; work abroad says little about jobs here
        number = notice.get("publication-number")
        published = parse_datetime(str(notice.get("publication-date") or "")[:10])
        if not number or not published:
            continue
        winner = _text(notice.get("winner-name"))
        buyer = _text(notice.get("buyer-name"))
        events.append({
            "kind": "contract",
            "subtype": str(notice.get("notice-type") or "contract award"),
            "title": f"{winner or name} won: {title[:160]}" + (f" (buyer: {buyer})" if buyer else ""),
            "url": f"https://ted.europa.eu/en/notice/-/detail/{number}",
            "published_at": published,
            "source": "TED",
        })
    return events, "ok"
