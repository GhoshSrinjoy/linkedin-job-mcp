"""Shared helpers: time handling, text normalisation and company-name handling."""
from __future__ import annotations

import hashlib
import html
import re
import unicodedata
from datetime import date, datetime, timedelta, timezone

from bs4 import BeautifulSoup


# --------------------------------------------------------------------------- time

def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def parse_datetime(value) -> datetime | None:
    """Parse ISO strings, dates or epoch seconds/milliseconds into an aware UTC datetime."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
    if isinstance(value, (int, float)) or (isinstance(value, str) and value.strip().isdigit()):
        num = float(value)
        if num > 1e12:  # epoch milliseconds
            num /= 1000.0
        try:
            return datetime.fromtimestamp(num, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        match = re.match(r"(\d{4})-(\d{2})-(\d{2})", text)
        if not match:
            match = re.match(r"(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})", text)  # GDELT style
            if not match:
                return None
            return datetime(*(int(g) for g in match.groups()), tzinfo=timezone.utc)
        parsed = datetime(int(match[1]), int(match[2]), int(match[3]))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def parse_date(value) -> date | None:
    parsed = parse_datetime(value)
    return parsed.date() if parsed else None


def iso(value: datetime | date | None) -> str | None:
    return value.isoformat() if value else None


def days_between(start: datetime | None, end: datetime | None) -> int | None:
    if start is None or end is None:
        return None
    return max(0, (end - start).days)


_RELATIVE_POSTED = [
    (re.compile(r"\b(?:today|heute)\b", re.I), 0, False),
    (re.compile(r"\b(?:yesterday|gestern)\b", re.I), 1, False),
]


def parse_relative_posted(text: str | None, now: datetime | None = None) -> tuple[datetime | None, bool]:
    """Parse Workday-style labels ("Posted 30+ Days Ago", "Vor 3 Tagen ausgeschrieben").

    Returns (date, is_lower_bound). A "30+" label only tells us the posting is at
    least 30 days old, so the age is a lower bound.
    """
    if not text:
        return None, False
    now = now or utcnow()
    for pattern, days, bound in _RELATIVE_POSTED:
        if pattern.search(text):
            return now - timedelta(days=days), bound
    match = re.search(r"(\d+)\s*(\+)?\s*(?:days?|tage?n?)", text, re.I)
    if match:
        return now - timedelta(days=int(match[1])), bool(match[2])
    if re.search(r"(?:mehr als|more than)\s*30", text, re.I):
        return now - timedelta(days=30), True
    return None, False


# --------------------------------------------------------------------------- text

_GENDER_TAGS = [
    re.compile(r"\(\s*(?:[mwfdxi]|divers|all)\s*(?:[/|,\-]\s*(?:[mwfdxi]|divers))+\s*\)", re.I),
    re.compile(r"\(\s*(?:all genders?|alle geschlechter|gn|genderneutral|w/m/d|m/w/d)\s*\)", re.I),
    re.compile(r"(?<![a-z])[mwfd]\s*/\s*[mwfd]\s*/\s*[mwfdx](?:ivers)?(?![a-z])", re.I),
]
_GENDER_SUFFIX = re.compile(r"(?<=[a-zäöüß])(?:\*|:|_|/-?|\()in(?:nen)?\)?(?![a-zäöüß])", re.I)


def strip_gender_tags(text: str) -> str:
    for pattern in _GENDER_TAGS:
        text = pattern.sub(" ", text)
    return _GENDER_SUFFIX.sub("", text)


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def normalize_title(title: str | None) -> str:
    """Lower-case job title without gender tags, punctuation or extra whitespace."""
    if not title:
        return ""
    text = unicodedata.normalize("NFKC", title)
    text = strip_gender_tags(text).lower()
    text = re.sub(r"[^\w+#. ]+", " ", text)
    text = re.sub(r"(?<!\w)\.|\.(?!\w)", " ", text)
    return normalize_space(text)


def html_to_text(markup: str | None) -> str:
    """Visible text of an HTML fragment (entities decoded, scripts and styles removed)."""
    if not markup:
        return ""
    if "<" not in markup and "&" in markup:
        markup = html.unescape(markup)
    if "&lt;" in markup:  # Greenhouse returns escaped HTML
        markup = html.unescape(markup)
    soup = BeautifulSoup(markup, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text("\n")
    lines = [normalize_space(line) for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# phone numbers start with +, 00 or a leading 0 and never contain dots (so dates and amounts survive)
_PHONE = re.compile(r"(?<![\w.])(?:\+\d{2}|00\d{2}|\(?0)\d{1,5}\)?[ /-]?\d[\d /-]{3,}\d(?![\w.])")


def strip_contact_data(text: str) -> str:
    """Remove e-mail addresses and phone numbers (recruiter personal data) before storing ad text."""
    if not text:
        return text
    text = _EMAIL.sub("[e-mail removed]", text)
    return _PHONE.sub(lambda m: "[phone removed]" if sum(c.isdigit() for c in m.group(0)) >= 8 else m.group(0), text)


def text_hash(text: str) -> str:
    norm = normalize_space(strip_gender_tags(text or "").lower())
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- companies

_LEGAL_FORMS = re.compile(
    r"\b(?:gmbh\s*&\s*co\.?\s*(?:kgaa|kg|ohg)|ggmbh|gmbh|mbh|ag|se|kgaa|kg|ohg|"
    r"ug(?:\s*\(haftungsbeschränkt\))?|e\.\s?k\.|e\.\s?v\.|ev|ltd\.?|limited|inc\.?|llc|plc|"
    r"b\.\s?v\.|bv|s\.\s?a\.|sa|sarl|s\.à\s?r\.l\.|co\.|corp\.?|corporation)(?=\s|$|[.,])",
    re.I,
)
_FILLER = {"group", "gruppe", "holding", "deutschland", "germany", "international", "the", "und", "and"}


def company_key(name: str | None) -> str:
    """Stable comparison key for a company name (legal forms and punctuation removed)."""
    if not name:
        return ""
    text = unicodedata.normalize("NFKC", name).lower()
    text = _LEGAL_FORMS.sub(" ", text)
    text = text.replace("&", " und ")
    text = re.sub(r"[^\w ]+", " ", text)
    return normalize_space(text)


def _ascii_fold(text: str) -> str:
    text = text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def slug_candidates(name: str, limit: int = 4) -> list[str]:
    """Likely ATS board slugs for a company name, most likely first."""
    key = _ascii_fold(company_key(name))
    tokens = key.split()
    core = [t for t in tokens if t not in _FILLER] or tokens
    candidates = [
        "".join(core),
        "-".join(core),
        "".join(tokens),
        "-".join(tokens),
    ]
    if len(core) > 1 and len(core[0]) >= 4:
        candidates.append(core[0])
    seen: list[str] = []
    for cand in candidates:
        cand = re.sub(r"[^a-z0-9-]", "", cand)
        if cand and cand not in seen:
            seen.append(cand)
    return seen[:limit]


def stable_jitter(seed: str, scale: float = 0.01) -> tuple[float, float]:
    """Deterministic small offset so markers in the same city do not overlap exactly."""
    digest = hashlib.md5(seed.encode("utf-8")).digest()
    dx = (digest[0] / 255.0 - 0.5) * 2 * scale
    dy = (digest[1] / 255.0 - 0.5) * 2 * scale
    return dx, dy
