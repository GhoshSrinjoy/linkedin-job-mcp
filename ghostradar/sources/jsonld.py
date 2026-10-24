"""schema.org JobPosting markup on careers pages and job boards.

Google defines datePosted as the original posting date, forbids expired postings
and requires filled jobs to be taken down (validThrough in the past, 404/410 or
markup removed). On boards, validThrough can be a placeholder far in the future.
"""
from __future__ import annotations

import json
import re
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from ..models import Posting
from ..util import html_to_text, normalize_space, parse_date, parse_datetime

CLOSED_MARKERS = re.compile(
    r"(?:stelle|stellenanzeige|anzeige|position|job|vacancy|posting)[^.]{0,40}"
    r"(?:nicht mehr verfügbar|ist bereits besetzt|wurde besetzt|ist abgelaufen|nicht mehr aktiv|"
    r"no longer available|has been filled|has expired|is closed|no longer accepting)",
    re.I,
)


def _iter_nodes(data):
    if isinstance(data, list):
        for item in data:
            yield from _iter_nodes(item)
    elif isinstance(data, dict):
        yield data
        if "@graph" in data:
            yield from _iter_nodes(data["@graph"])


def _is_jobposting(node: dict) -> bool:
    kind = node.get("@type")
    kinds = kind if isinstance(kind, list) else [kind]
    return any(isinstance(k, str) and k.lower() == "jobposting" for k in kinds)


def _text(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return _text(value.get("name") or value.get("value") or value.get("@value"))
    if isinstance(value, list):
        return ", ".join(t for t in (_text(v) for v in value) if t) or None
    return normalize_space(str(value)) or None


def _location(node: dict) -> tuple[str | None, str | None, str | None]:
    locs = node.get("jobLocation")
    locs = locs if isinstance(locs, list) else [locs] if locs else []
    for loc in locs:
        if not isinstance(loc, dict):
            continue
        addr = loc.get("address") or {}
        if isinstance(addr, str):
            return addr, addr, None
        city = _text(addr.get("addressLocality"))
        region = _text(addr.get("addressRegion"))
        country = _text(addr.get("addressCountry"))
        label = ", ".join(x for x in (city, region, country) if x) or None
        return label, city, region
    return None, None, None


def _salary(node: dict) -> tuple[float | None, float | None, str | None, str | None]:
    base = node.get("baseSalary")
    if not isinstance(base, dict):
        return None, None, None, None
    currency = base.get("currency")
    value = base.get("value")
    if isinstance(value, dict):
        lo = value.get("minValue", value.get("value"))
        hi = value.get("maxValue", value.get("value"))
        unit = value.get("unitText")
    else:
        lo = hi = value
        unit = None

    def num(v):
        try:
            return float(v) if v not in (None, "") else None
        except (TypeError, ValueError):
            return None

    return num(lo), num(hi), currency, unit


def extract(html: str, url: str) -> list[Posting]:
    """All JobPosting objects embedded as JSON-LD in a page."""
    soup = BeautifulSoup(html, "html.parser")
    blocks = []
    for script in soup.find_all("script", attrs={"type": re.compile("ld\\+json", re.I)}):
        raw = script.string or script.get_text() or ""
        try:
            blocks.append(json.loads(raw.strip()))
        except (json.JSONDecodeError, ValueError):
            continue
    return from_nodes(blocks, url)


def from_nodes(blocks: list, url: str) -> list[Posting]:
    """JobPosting objects from already-parsed JSON-LD blocks (e.g. sent by the browser extension)."""
    postings: list[Posting] = []
    for data in blocks:
        for node in _iter_nodes(data):
            if not _is_jobposting(node):
                continue
            org = node.get("hiringOrganization")
            company = _text(org.get("name")) if isinstance(org, dict) else _text(org)
            org_url = org.get("sameAs") or org.get("url") if isinstance(org, dict) else None
            label, city, region = _location(node)
            lo, hi, cur, unit = _salary(node)
            ident = node.get("identifier")
            ident_value = _text(ident.get("value")) if isinstance(ident, dict) else _text(ident)
            start = node.get("jobStartDate")
            postings.append(
                Posting(
                    source="jsonld",
                    source_id=url.split("#")[0],
                    url=url,
                    company=company,
                    title=_text(node.get("title")) or "",
                    location=label,
                    city=city,
                    region=region,
                    description=html_to_text(node.get("description") or ""),
                    posted_at=parse_datetime(node.get("datePosted")),
                    valid_through=parse_datetime(node.get("validThrough")),
                    start_date=parse_date(start) if isinstance(start, str) and re.match(r"\d{4}-\d{2}-\d{2}", start) else None,
                    start_immediate=bool(node.get("jobImmediateStart")) if "jobImmediateStart" in node else None,
                    employment_type=_text(node.get("employmentType")),
                    requisition_id=ident_value,
                    salary_min=lo,
                    salary_max=hi,
                    salary_currency=cur,
                    salary_period=unit,
                    channel="employer",
                    extra={"org_url": org_url, "directApply": node.get("directApply")},
                )
            )
    return postings


def page_text(html: str) -> tuple[str, str]:
    """(title, main visible text) of a page without JobPosting markup."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "footer", "header", "form"]):
        tag.decompose()
    title = ""
    h1 = soup.find("h1")
    if h1:
        title = normalize_space(h1.get_text(" "))
    elif soup.title:
        title = normalize_space(soup.title.get_text(" "))
    main = soup.find("main") or soup.find("article") or soup.body or soup
    return title, html_to_text(str(main))


def looks_closed(html: str) -> bool:
    return bool(CLOSED_MARKERS.search(html_to_text(html)[:20000]))


def same_site(url_a: str | None, url_b: str | None) -> bool:
    """True when two URLs share a registrable-looking domain (last two labels)."""
    if not url_a or not url_b:
        return False

    def base(u: str) -> str:
        host = (urlsplit(u).hostname or "").lower()
        return ".".join(host.split(".")[-2:])

    return base(url_a) == base(url_b)
