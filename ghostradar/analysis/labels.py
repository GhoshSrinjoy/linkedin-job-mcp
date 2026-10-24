"""Parse what job platforms show next to a posting (German and English UI labels).

Used for data the job seeker captures from their own browser (extension or manual
entry): applicant counts, "posted … ago", "Reposted", recruiter-activity badges.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta

_NUM = r"(\d{1,3}(?:[.,]\d{3})*|\d+)"


def _int(value: str) -> int:
    return int(re.sub(r"[.,]", "", value))


@dataclass
class Applicants:
    count: int | None = None
    lower_bound: bool = False  # "Over 100 applicants"
    upper_bound: bool = False  # "Be among the first 25 applicants"
    text: str | None = None
    clicks: bool = False  # "200 people clicked apply": clicks on an external application link, not applications


_CLICKS = [
    (re.compile(r"(?:over|more than)\s+" + _NUM + r"\s+(?:people|persons?) clicked apply", re.I), "lower"),
    (re.compile(_NUM + r"\s+(?:people|persons?) clicked apply", re.I), "exact"),
    (re.compile(r"(?:über|mehr als)\s+" + _NUM + r"\s+personen haben (?:auf )?\W?bewerben\W? geklickt", re.I), "lower"),
    (re.compile(_NUM + r"\s+personen haben (?:auf )?\W?bewerben\W? geklickt", re.I), "exact"),
]

_APPLICANTS = [
    (re.compile(r"(?:over|more than)\s+" + _NUM + r"\s+applicants?", re.I), "lower"),
    (re.compile(r"(?:über|mehr als)\s+" + _NUM + r"\s+(?:bewerber(?:\*|:|_)?(?:innen)?|bewerbungen|personen)", re.I), "lower"),
    (re.compile(r"(?:be among the first|be one of the first)\s+" + _NUM + r"\s+applicants?", re.I), "upper"),
    (re.compile(r"(?:sei|gehöre|gehören sie) (?:unter|zu) den ersten\s+" + _NUM, re.I), "upper"),
    (re.compile(_NUM + r"\s+applicants?\b", re.I), "exact"),
    (re.compile(_NUM + r"\s+(?:bewerber(?:\*|:|_)?(?:innen)?|bewerbungen)\b", re.I), "exact"),
]


def parse_applicants(text: str | None) -> Applicants:
    if not text:
        return Applicants()
    for pattern, kind in _CLICKS:
        match = pattern.search(text)
        if match:
            return Applicants(count=_int(match.group(1)), lower_bound=kind == "lower", text=match.group(0).strip(),
                              clicks=True)
    for pattern, kind in _APPLICANTS:
        match = pattern.search(text)
        if match:
            return Applicants(
                count=_int(match.group(1)),
                lower_bound=kind == "lower",
                upper_bound=kind == "upper",
                text=match.group(0).strip(),
            )
    if re.search(r"early applicant|frühe[rn]? bewerb", text, re.I):
        return Applicants(count=10, upper_bound=True, text="early applicant")
    return Applicants()


@dataclass
class Posted:
    date: datetime | None = None
    lower_bound: bool = False  # "30+ days ago"
    reposted: bool = False
    text: str | None = None


_UNITS = {
    "minute": 0, "minuten": 0, "min": 0, "hour": 0, "hours": 0, "stunde": 0, "stunden": 0,
    "day": 1, "days": 1, "tag": 1, "tagen": 1, "tage": 1,
    "week": 7, "weeks": 7, "woche": 7, "wochen": 7,
    "month": 30, "months": 30, "monat": 30, "monaten": 30, "monate": 30,
    "year": 365, "years": 365, "jahr": 365, "jahren": 365, "jahre": 365,
}
_UNIT_RX = "|".join(sorted(_UNITS, key=len, reverse=True))
_REPOSTED = re.compile(r"\breposted\b|erneut (?:gepostet|veröffentlicht|eingestellt|geschaltet)|neu eingestellt", re.I)
_EN_AGO = re.compile(r"(\d+)\s*(\+)?\s*(" + _UNIT_RX + r")s?\s+ago", re.I)
_DE_AGO = re.compile(r"vor\s+(?:(?:über|mehr als)\s+)?(\d+)\s*(\+)?\s*(" + _UNIT_RX + r")", re.I)
_DE_OVER = re.compile(r"vor\s+(?:über|mehr als)\s+(\d+)", re.I)
_TODAY = re.compile(r"\b(?:just posted|today|heute|gerade (?:veröffentlicht|geschaltet)|soeben|neu)\b", re.I)
_YESTERDAY = re.compile(r"\b(?:yesterday|gestern)\b", re.I)
_ABSOLUTE = re.compile(
    r"(?:veröffentlicht|erschienen|online seit|eingestellt|posted)(?:\s+(?:am|on|seit))?\s*:?\s*(\d{1,2})\.\s?(\d{1,2})\.\s?(\d{4})",
    re.I,
)


def parse_posted(text: str | None, now: datetime) -> Posted:
    if not text:
        return Posted()
    reposted = bool(_REPOSTED.search(text))
    match = _ABSOLUTE.search(text)
    if match:
        try:
            when = datetime(int(match[3]), int(match[2]), int(match[1]), tzinfo=now.tzinfo)
            return Posted(when, False, reposted, match.group(0).strip())
        except ValueError:
            pass
    for pattern in (_EN_AGO, _DE_AGO):
        match = pattern.search(text)
        if match:
            amount = int(match.group(1))
            days = amount * _UNITS[match.group(3).lower()]
            lower = bool(match.group(2)) or bool(_DE_OVER.search(match.group(0)))
            return Posted(now - timedelta(days=days), lower, reposted, match.group(0).strip())
    if _YESTERDAY.search(text):
        return Posted(now - timedelta(days=1), False, reposted, "yesterday")
    if _TODAY.search(text):
        return Posted(now, False, reposted, "today")
    return Posted(None, False, reposted, None)


_ACTIVE = re.compile(
    r"actively (?:reviewing|recruiting)|bewerber(?::innen|innen)? werden aktiv geprüft|aktiv(?:er)? arbeitgeber|"
    r"responsive employer|reagiert (?:in der regel|meist)|antwortet (?:in der regel|meist)|"
    r"typically responds|usually responds",
    re.I,
)
_NO_INSIGHT = re.compile(r"no response insights|noch keine antwort verfügbar|keine antwortdaten", re.I)


def parse_responsiveness(texts: list[str] | str | None) -> str | None:
    if not texts:
        return None
    joined = " | ".join(texts) if isinstance(texts, list) else texts
    if _ACTIVE.search(joined):
        return "active"
    if _NO_INSIGHT.search(joined):
        return "none"
    return None
