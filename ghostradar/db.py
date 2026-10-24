"""SQLite storage: postings with their lifecycle, companies, events, reports, watchlist, caches."""
from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from .config import settings
from .models import Posting
from .util import company_key, iso, normalize_title, parse_date, parse_datetime, text_hash, utcnow

SCHEMA = """
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    name_key TEXT NOT NULL UNIQUE,
    ats TEXT,
    ats_slug TEXT,
    ats_url TEXT,
    careers_url TEXT,
    employer_type TEXT,
    headcount INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS postings (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL,
    source_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    company_id INTEGER REFERENCES companies(id),
    company TEXT,
    url TEXT,
    title TEXT,
    title_key TEXT,
    location TEXT,
    city TEXT,
    region TEXT,
    lat REAL,
    lon REAL,
    department TEXT,
    description TEXT,
    text_hash TEXT,
    signature TEXT,
    kldb TEXT,
    level_code TEXT,
    posted_at TEXT,
    posted_lower_bound INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT,
    valid_through TEXT,
    start_date TEXT,
    start_immediate INTEGER,
    employment_type TEXT,
    requisition_id TEXT,
    salary_min REAL,
    salary_max REAL,
    salary_currency TEXT,
    salary_period TEXT,
    salary_predicted INTEGER NOT NULL DEFAULT 0,
    agency_flag INTEGER,
    remote INTEGER,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    missed_checks INTEGER NOT NULL DEFAULT 0,
    removed_at TEXT,
    reopened INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    cluster_id INTEGER,
    extra TEXT,
    UNIQUE(source, source_id)
);
CREATE INDEX IF NOT EXISTS idx_postings_company ON postings(company_id);
CREATE INDEX IF NOT EXISTS idx_postings_city ON postings(city);
CREATE INDEX IF NOT EXISTS idx_postings_cluster ON postings(cluster_id);
CREATE INDEX IF NOT EXISTS idx_postings_kldb ON postings(kldb, level_code);
CREATE TABLE IF NOT EXISTS sightings (
    id INTEGER PRIMARY KEY,
    posting_id INTEGER NOT NULL REFERENCES postings(id),
    seen_at TEXT NOT NULL,
    text_hash TEXT,
    posted_at TEXT,
    valid_through TEXT
);
CREATE INDEX IF NOT EXISTS idx_sightings_posting ON sightings(posting_id);
CREATE TABLE IF NOT EXISTS feed_runs (
    id INTEGER PRIMARY KEY,
    company_id INTEGER,
    source TEXT NOT NULL,
    slug TEXT NOT NULL,
    run_at TEXT NOT NULL,
    ok INTEGER NOT NULL,
    jobs INTEGER NOT NULL DEFAULT 0,
    complete INTEGER NOT NULL DEFAULT 0,
    note TEXT
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    kind TEXT NOT NULL,
    title TEXT,
    url TEXT,
    published_at TEXT,
    source TEXT,
    fetched_at TEXT NOT NULL,
    UNIQUE(company_id, url)
);
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY,
    posting_id INTEGER,
    posting_url TEXT,
    company TEXT,
    company_key TEXT,
    created_at TEXT NOT NULL,
    applied_on TEXT,
    response TEXT,
    days_to_response INTEGER,
    applicant_count INTEGER,
    reposted_label INTEGER,
    note TEXT
);
CREATE TABLE IF NOT EXISTS watchlist (
    id INTEGER PRIMARY KEY,
    kind TEXT NOT NULL,
    query TEXT NOT NULL,
    params TEXT,
    created_at TEXT NOT NULL,
    last_run TEXT,
    last_result TEXT,
    UNIQUE(kind, query)
);
CREATE TABLE IF NOT EXISTS audits (
    id INTEGER PRIMARY KEY,
    posting_id INTEGER NOT NULL REFERENCES postings(id),
    label TEXT NOT NULL,
    method TEXT,
    note TEXT,
    inclusion_prob REAL,
    risk INTEGER,
    snapshot TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audits_posting ON audits(posting_id);
CREATE TABLE IF NOT EXISTS prefs (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS http_cache (
    key TEXT PRIMARY KEY,
    fetched_at REAL NOT NULL,
    status INTEGER NOT NULL,
    content_type TEXT,
    final_url TEXT,
    body BLOB
);
CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY,
    posting_id INTEGER NOT NULL REFERENCES postings(id),
    seen_at TEXT NOT NULL,
    platform TEXT,
    applicants INTEGER,
    applicants_bound TEXT,
    posted_text TEXT,
    reposted INTEGER,
    responsiveness TEXT
);
CREATE INDEX IF NOT EXISTS idx_observations_posting ON observations(posting_id);
CREATE TABLE IF NOT EXISTS geocode_cache (
    query TEXT PRIMARY KEY,
    lat REAL,
    lon REAL,
    region TEXT,
    fetched_at TEXT NOT NULL
);
"""

# what the user records about an employer: hiring practice, size a year ago, last funding round
PROFILE_COLUMNS = {
    "hiring_practice": "TEXT",
    "practice_note": "TEXT",
    "headcount_prev": "INTEGER",
    "funding_date": "TEXT",
    "funding_amount": "TEXT",
}

_lock = threading.RLock()
_conn: sqlite3.Connection | None = None
_conn_path: Path | None = None


def _connection() -> sqlite3.Connection:
    global _conn, _conn_path
    path = Path(settings.db_path)
    if _conn is None or _conn_path != path:
        if _conn is not None:
            _conn.close()
        path.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(str(path), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA foreign_keys=ON")
        _conn.executescript(SCHEMA)
        _ensure_column(_conn, "companies", "news_checked_at", "TEXT")
        for column, decl in PROFILE_COLUMNS.items():
            _ensure_column(_conn, "companies", column, decl)
        # the feature vector at the moment an outcome was reported (training data without hindsight)
        _ensure_column(_conn, "reports", "risk", "INTEGER")
        _ensure_column(_conn, "reports", "snapshot", "TEXT")
        # communication history: how far the application got, promised dates, withdrawals, unanswered follow-ups
        for column, decl in {"stage": "TEXT", "promised_by": "TEXT", "withdrawn": "INTEGER", "followups": "INTEGER"}.items():
            _ensure_column(_conn, "reports", column, decl)
        for column, decl in {"approval": "TEXT", "manager_named": "INTEGER", "start_date_given": "INTEGER"}.items():
            _ensure_column(_conn, "audits", column, decl)
        _ensure_column(_conn, "events", "subtype", "TEXT")
        _ensure_column(_conn, "observations", "clicks", "INTEGER")
        _conn_path = path
    return _conn


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, decl: str) -> None:
    """Add a column to an existing database created by an older version."""
    names = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in names:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")
        conn.commit()


@contextmanager
def tx() -> Iterator[sqlite3.Connection]:
    """Serialised access to the shared connection, committed on success."""
    with _lock:
        conn = _connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def init_db() -> None:
    with tx():
        pass


def close_db() -> None:
    global _conn, _conn_path
    with _lock:
        if _conn is not None:
            _conn.close()
        _conn = None
        _conn_path = None


def _now() -> str:
    return utcnow().isoformat()


# --------------------------------------------------------------------------- companies


def get_or_create_company(name: str) -> int:
    key = company_key(name) or name.strip().lower()
    with tx() as conn:
        row = conn.execute("SELECT id FROM companies WHERE name_key = ?", (key,)).fetchone()
        if row:
            return int(row["id"])
        cur = conn.execute(
            "INSERT INTO companies (name, name_key, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (name.strip(), key, _now(), _now()),
        )
        return int(cur.lastrowid)


def find_company(name: str) -> dict | None:
    key = company_key(name)
    if not key:
        return None
    with tx() as conn:
        row = conn.execute("SELECT * FROM companies WHERE name_key = ?", (key,)).fetchone()
        return dict(row) if row else None


def find_company_by_feed(ats: str, slug: str) -> dict | None:
    with tx() as conn:
        row = conn.execute(
            "SELECT * FROM companies WHERE ats = ? AND lower(ats_slug) = lower(?) ORDER BY id LIMIT 1", (ats, slug)
        ).fetchone()
        return dict(row) if row else None


def get_company(company_id: int) -> dict | None:
    with tx() as conn:
        row = conn.execute("SELECT * FROM companies WHERE id = ?", (company_id,)).fetchone()
        return dict(row) if row else None


def update_company(company_id: int, **fields: Any) -> None:
    allowed = {"name", "ats", "ats_slug", "ats_url", "careers_url", "employer_type", "headcount", "news_checked_at",
               *PROFILE_COLUMNS}
    items = {k: v for k, v in fields.items() if k in allowed}
    if not items:
        return
    sets = ", ".join(f"{k} = ?" for k in items)
    with tx() as conn:
        conn.execute(
            f"UPDATE companies SET {sets}, updated_at = ? WHERE id = ?",
            (*items.values(), _now(), company_id),
        )


# --------------------------------------------------------------------------- postings


def _posting_columns(p: Posting) -> dict[str, Any]:
    return {
        "channel": p.channel,
        "company": p.company,
        "url": p.url,
        "title": p.title,
        "title_key": normalize_title(p.title),
        "location": p.location,
        "city": p.city,
        "region": p.region,
        "lat": p.lat,
        "lon": p.lon,
        "department": p.department,
        "description": p.description,
        "text_hash": text_hash(p.description) if p.description else None,
        "posted_at": iso(p.posted_at),
        "posted_lower_bound": int(p.posted_at_is_lower_bound),
        "updated_at": iso(p.updated_at),
        "valid_through": iso(p.valid_through),
        "start_date": iso(p.start_date),
        "start_immediate": None if p.start_immediate is None else int(p.start_immediate),
        "employment_type": p.employment_type,
        "requisition_id": p.requisition_id,
        "salary_min": p.salary_min,
        "salary_max": p.salary_max,
        "salary_currency": p.salary_currency,
        "salary_period": p.salary_period,
        "salary_predicted": int(p.salary_predicted),
        "agency_flag": None if p.agency_flag is None else int(p.agency_flag),
        "remote": None if p.remote is None else int(p.remote),
        "extra": json.dumps(p.extra, default=str) if p.extra else None,
    }


def upsert_posting(
    p: Posting,
    company_id: int | None,
    seen_at: datetime | None = None,
    signature: list[int] | None = None,
    kldb: str | None = None,
    level_code: str | None = None,
) -> tuple[int, bool]:
    """Insert or refresh a posting and record a sighting. Returns (posting_id, is_new)."""
    seen = iso(seen_at or utcnow())
    cols = _posting_columns(p)
    cols["company_id"] = company_id
    cols["signature"] = json.dumps(signature) if signature else None
    cols["kldb"] = kldb
    cols["level_code"] = level_code
    with tx() as conn:
        row = conn.execute(
            "SELECT id, description, posted_at, status FROM postings WHERE source = ? AND source_id = ?",
            (p.source, p.source_id),
        ).fetchone()
        if row is None:
            names = ["source", "source_id", *cols.keys(), "first_seen", "last_seen", "status"]
            values = [p.source, p.source_id, *cols.values(), seen, seen, "active"]
            cur = conn.execute(
                f"INSERT INTO postings ({', '.join(names)}) VALUES ({', '.join('?' for _ in names)})",
                values,
            )
            posting_id, is_new = int(cur.lastrowid), True
        else:
            posting_id, is_new = int(row["id"]), False
            # a sighting with less information must not erase what earlier sightings recorded
            # (e.g. a capture without a date would otherwise wipe the original posting date)
            cols = {k: v for k, v in cols.items() if v is not None}
            if not p.description and row["description"]:
                for key in ("description", "text_hash", "signature"):
                    cols.pop(key, None)
            sets = ", ".join(f"{k} = ?" for k in cols)
            # a posting that comes back under the same ID after a confirmed removal is a reopening
            reopened = 1 if row["status"] == "removed" else 0
            conn.execute(
                f"UPDATE postings SET {sets}, last_seen = ?, missed_checks = 0, status = 'active', "
                "removed_at = NULL, reopened = reopened + ? WHERE id = ?",
                (*cols.values(), seen, reopened, posting_id),
            )
        conn.execute(
            "INSERT INTO sightings (posting_id, seen_at, text_hash, posted_at, valid_through) VALUES (?, ?, ?, ?, ?)",
            (posting_id, seen, cols.get("text_hash"), cols.get("posted_at"), cols.get("valid_through")),
        )
    return posting_id, is_new


def sync_feed(
    company_id: int,
    source: str,
    seen_ids: set[str],
    complete: bool,
    seen_at: datetime | None = None,
) -> dict[str, int]:
    """Count misses for postings absent from a complete feed run; two misses mark removal.

    Incomplete runs (pagination caps, errors) never count as misses: a parser or
    paging problem must not look like mass closures.
    """
    seen = iso(seen_at or utcnow())
    removed = 0
    missed = 0
    if not complete:
        return {"missed": 0, "removed": 0}
    with tx() as conn:
        rows = conn.execute(
            "SELECT id, source_id, missed_checks FROM postings "
            "WHERE company_id = ? AND source = ? AND status = 'active'",
            (company_id, source),
        ).fetchall()
        for row in rows:
            if row["source_id"] in seen_ids:
                continue
            misses = int(row["missed_checks"]) + 1
            if misses >= 2:
                conn.execute(
                    "UPDATE postings SET missed_checks = ?, status = 'removed', removed_at = ? WHERE id = ?",
                    (misses, seen, row["id"]),
                )
                removed += 1
            else:
                conn.execute("UPDATE postings SET missed_checks = ? WHERE id = ?", (misses, row["id"]))
                missed += 1
    return {"missed": missed, "removed": removed}


def mark_closed(posting_id: int, when: datetime | None = None) -> None:
    with tx() as conn:
        conn.execute(
            "UPDATE postings SET status = 'removed', removed_at = COALESCE(removed_at, ?) WHERE id = ?",
            (iso(when or utcnow()), posting_id),
        )


def set_cluster(posting_id: int, cluster_id: int) -> None:
    with tx() as conn:
        conn.execute("UPDATE postings SET cluster_id = ? WHERE id = ?", (cluster_id, posting_id))


def row_to_posting(row: sqlite3.Row | dict) -> Posting:
    r = dict(row)
    return Posting(
        source=r["source"],
        source_id=r["source_id"],
        url=r.get("url"),
        company=r.get("company"),
        title=r.get("title") or "",
        location=r.get("location"),
        city=r.get("city"),
        region=r.get("region"),
        lat=r.get("lat"),
        lon=r.get("lon"),
        department=r.get("department"),
        description=r.get("description") or "",
        posted_at=parse_datetime(r.get("posted_at")),
        posted_at_is_lower_bound=bool(r.get("posted_lower_bound")),
        updated_at=parse_datetime(r.get("updated_at")),
        valid_through=parse_datetime(r.get("valid_through")),
        start_date=parse_date(r.get("start_date")),
        start_immediate=None if r.get("start_immediate") is None else bool(r["start_immediate"]),
        employment_type=r.get("employment_type"),
        requisition_id=r.get("requisition_id"),
        salary_min=r.get("salary_min"),
        salary_max=r.get("salary_max"),
        salary_currency=r.get("salary_currency"),
        salary_period=r.get("salary_period"),
        salary_predicted=bool(r.get("salary_predicted")),
        agency_flag=None if r.get("agency_flag") is None else bool(r["agency_flag"]),
        remote=None if r.get("remote") is None else bool(r["remote"]),
        channel=r.get("channel") or "employer",
        extra=json.loads(r["extra"]) if r.get("extra") else {},
    )


def get_posting_row(posting_id: int, light: bool = False) -> dict | None:
    with tx() as conn:
        row = conn.execute(
            f"SELECT {LIGHT_COLUMNS if light else '*'} FROM postings WHERE id = ?", (posting_id,)
        ).fetchone()
        return dict(row) if row else None


def find_posting_row(source: str, source_id: str) -> dict | None:
    with tx() as conn:
        row = conn.execute(
            "SELECT * FROM postings WHERE source = ? AND source_id = ?", (source, source_id)
        ).fetchone()
        return dict(row) if row else None


LIGHT_COLUMNS = (
    "id, source, source_id, channel, company_id, company, url, title, title_key, city, region, department, "
    "text_hash, signature, requisition_id, posted_at, first_seen, last_seen, status, removed_at, reopened, "
    "cluster_id, agency_flag"
)


def company_posting_rows(company_id: int, status: str | None = None, light: bool = False) -> list[dict]:
    """All postings of one employer; light=True skips descriptions for bulk work."""
    query = f"SELECT {LIGHT_COLUMNS if light else '*'} FROM postings WHERE company_id = ?"
    params: list[Any] = [company_id]
    if status:
        query += " AND status = ?"
        params.append(status)
    with tx() as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]


def cluster_rows(cluster_id: int) -> list[dict]:
    with tx() as conn:
        return [
            dict(r)
            for r in conn.execute("SELECT * FROM postings WHERE cluster_id = ?", (cluster_id,)).fetchall()
        ]


def city_posting_rows(city: str, limit: int = 1000) -> list[dict]:
    with tx() as conn:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM postings WHERE lower(city) = lower(?) AND status = 'active' "
                "ORDER BY last_seen DESC LIMIT ?",
                (city, limit),
            ).fetchall()
        ]


def recent_active_rows(limit: int = 1500) -> list[dict]:
    """The most recently seen active postings, for the overview."""
    with tx() as conn:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM postings WHERE status = 'active' ORDER BY last_seen DESC LIMIT ?", (limit,)
            ).fetchall()
        ]


def stats() -> dict[str, Any]:
    """Counts for the overview: postings by status, checks, employers with their own feed, watchlist."""
    with tx() as conn:
        one = lambda q: conn.execute(q).fetchone()[0]  # noqa: E731
        return {
            "active": one("SELECT COUNT(*) FROM postings WHERE status = 'active'"),
            "removed": one("SELECT COUNT(*) FROM postings WHERE status != 'active'"),
            "checks": one("SELECT COUNT(*) FROM sightings"),
            "own_feeds": one("SELECT COUNT(*) FROM companies WHERE ats IS NOT NULL"),
            "observations": one("SELECT COUNT(*) FROM observations"),
            "watch": one("SELECT COUNT(*) FROM watchlist"),
            "first_seen": one("SELECT MIN(first_seen) FROM postings"),
            "last_seen": one("SELECT MAX(last_seen) FROM postings"),
        }


def lifetime_rows(limit: int = 50000) -> list[dict]:
    """Lifetime fields of every posting, for the survival baselines."""
    with tx() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT id, cluster_id, kldb, level_code, channel, agency_flag, posted_at, first_seen, last_seen, "
            "removed_at, status FROM postings ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]


def data_fingerprint() -> tuple:
    """Changes whenever postings, sightings, events or observations change (cheap cache key)."""
    with tx() as conn:
        return tuple(conn.execute(
            "SELECT (SELECT COUNT(*) FROM postings), (SELECT MAX(last_seen) FROM postings), "
            "(SELECT COUNT(*) FROM sightings), (SELECT COUNT(*) FROM events), (SELECT COUNT(*) FROM observations), "
            "(SELECT COUNT(*) FROM companies WHERE ats IS NOT NULL), (SELECT COUNT(*) FROM postings WHERE status != 'active')"
        ).fetchone())


def sightings(posting_id: int) -> list[dict]:
    with tx() as conn:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM sightings WHERE posting_id = ? ORDER BY seen_at", (posting_id,)
            ).fetchall()
        ]


def comparable_lifetimes(kldb: str, level_code: str | None, limit: int = 2000) -> list[tuple[str, str, str]]:
    """(first_published_or_seen, end_or_null, status) for postings in the same occupation group."""
    query = (
        "SELECT COALESCE(posted_at, first_seen) AS start, removed_at, status FROM postings "
        "WHERE kldb = ? AND channel = 'employer' AND agency_flag IS NOT 1"
    )
    params: list[Any] = [kldb]
    if level_code:
        query += " AND level_code = ?"
        params.append(level_code)
    query += " LIMIT ?"
    params.append(limit)
    with tx() as conn:
        return [(r["start"], r["removed_at"], r["status"]) for r in conn.execute(query, params).fetchall()]


def record_feed_run(company_id: int | None, source: str, slug: str, ok: bool, jobs: int, complete: bool, note: str = "") -> None:
    with tx() as conn:
        conn.execute(
            "INSERT INTO feed_runs (company_id, source, slug, run_at, ok, jobs, complete, note) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (company_id, source, slug, _now(), int(ok), jobs, int(complete), note),
        )


def feed_runs(company_id: int) -> list[dict]:
    with tx() as conn:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM feed_runs WHERE company_id = ? ORDER BY run_at", (company_id,)
            ).fetchall()
        ]


# --------------------------------------------------------------------------- platform observations


def add_observation(
    posting_id: int,
    platform: str | None,
    applicants: int | None,
    applicants_bound: str | None,
    posted_text: str | None,
    reposted: bool | None,
    responsiveness: str | None,
    clicks: bool | None = None,
) -> None:
    with tx() as conn:
        conn.execute(
            "INSERT INTO observations (posting_id, seen_at, platform, applicants, applicants_bound, posted_text, "
            "reposted, responsiveness, clicks) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (posting_id, _now(), platform, applicants, applicants_bound, posted_text,
             None if reposted is None else int(reposted), responsiveness, None if clicks is None else int(clicks)),
        )


def observation_rows(posting_id: int) -> list[dict]:
    with tx() as conn:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM observations WHERE posting_id = ? ORDER BY seen_at", (posting_id,)
            ).fetchall()
        ]


# --------------------------------------------------------------------------- events


def add_events(company_id: int, events: list[dict]) -> None:
    with tx() as conn:
        for ev in events:
            conn.execute(
                "INSERT OR IGNORE INTO events (company_id, kind, title, url, published_at, source, fetched_at, subtype) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (company_id, ev["kind"], ev.get("title"), ev.get("url"), iso(ev.get("published_at")), ev.get("source"),
                 _now(), ev.get("subtype")),
            )


def delete_note_event(company_id: int, event_id: int) -> bool:
    """Remove one of your own dated employer events (news and TED entries stay)."""
    with tx() as conn:
        cur = conn.execute("DELETE FROM events WHERE id = ? AND company_id = ? AND source = 'your note'",
                           (event_id, company_id))
        return cur.rowcount > 0


def get_prefs() -> dict[str, str]:
    with tx() as conn:
        return {r["key"]: r["value"] for r in conn.execute("SELECT key, value FROM prefs").fetchall()}


def set_prefs(values: dict[str, Any]) -> None:
    with tx() as conn:
        for key, value in values.items():
            if value is None:
                conn.execute("DELETE FROM prefs WHERE key = ?", (key,))
            else:
                conn.execute("INSERT INTO prefs (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                             (key, str(value)))


def noted_companies() -> list[dict]:
    """Employers you wrote something about: notes, figures or dated events."""
    with tx() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT c.id, c.name, c.hiring_practice, c.practice_note, c.headcount, c.headcount_prev, c.funding_date, "
            "c.funding_amount, (SELECT COUNT(*) FROM events e WHERE e.company_id = c.id AND e.source = 'your note') AS events, "
            "(SELECT COUNT(*) FROM reports r WHERE r.company_key = c.name_key) AS outcomes "
            "FROM companies c WHERE c.hiring_practice IS NOT NULL OR c.practice_note IS NOT NULL OR c.headcount IS NOT NULL "
            "OR c.funding_date IS NOT NULL OR EXISTS (SELECT 1 FROM events e WHERE e.company_id = c.id AND e.source = 'your note') "
            "ORDER BY c.name").fetchall()]


def company_events(company_id: int) -> list[dict]:
    with tx() as conn:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM events WHERE company_id = ? ORDER BY published_at DESC", (company_id,)
            ).fetchall()
        ]


# --------------------------------------------------------------------------- reports


def add_report(data: dict) -> int:
    with tx() as conn:
        cur = conn.execute(
            "INSERT INTO reports (posting_id, posting_url, company, company_key, created_at, applied_on, response, "
            "days_to_response, applicant_count, reposted_label, note, risk, snapshot, stage, promised_by, withdrawn, "
            "followups) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                data.get("posting_id"),
                data.get("posting_url"),
                data.get("company"),
                company_key(data.get("company")),
                _now(),
                iso(data.get("applied_on")),
                data.get("response"),
                data.get("days_to_response"),
                data.get("applicant_count"),
                None if data.get("reposted_label") is None else int(bool(data.get("reposted_label"))),
                data.get("note"),
                data.get("risk"),
                json.dumps(data["snapshot"]) if data.get("snapshot") else None,
                data.get("stage"),
                iso(data.get("promised_by")),
                None if data.get("withdrawn") is None else int(bool(data.get("withdrawn"))),
                data.get("followups"),
            ),
        )
        return int(cur.lastrowid)


def add_audit(posting_id: int, label: str, method: str | None, note: str | None, inclusion_prob: float | None,
              risk: int | None, snapshot: dict | None, approval: str | None = None, manager_named: bool | None = None,
              start_date_given: bool | None = None) -> int:
    """A checked label for one posting: what the audit found out (open, filled, internal, pool, on hold)."""
    flag = lambda v: None if v is None else int(bool(v))  # noqa: E731
    with tx() as conn:
        cur = conn.execute(
            "INSERT INTO audits (posting_id, label, method, note, inclusion_prob, risk, snapshot, created_at, approval, "
            "manager_named, start_date_given) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (posting_id, label, method, note, inclusion_prob, risk, json.dumps(snapshot) if snapshot else None, _now(),
             approval, flag(manager_named), flag(start_date_given)),
        )
        return int(cur.lastrowid)


def audit_rows() -> list[dict]:
    with tx() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT a.*, p.title, p.company, p.source FROM audits a LEFT JOIN postings p ON p.id = a.posting_id "
            "ORDER BY a.created_at DESC").fetchall()]


def labelled_reports() -> list[dict]:
    """Outcome reports tied to one posting that say something about the job itself."""
    with tx() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM reports WHERE posting_id IS NOT NULL AND response IN ('interview', 'offer', 'internal') "
            "ORDER BY created_at DESC").fetchall()]


def report_rows(company: str | None = None, posting_id: int | None = None) -> list[dict]:
    query = "SELECT * FROM reports WHERE 1 = 1"
    params: list[Any] = []
    if company:
        query += " AND company_key = ?"
        params.append(company_key(company))
    if posting_id is not None:
        query += " AND posting_id = ?"
        params.append(posting_id)
    query += " ORDER BY created_at DESC"
    with tx() as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]


# --------------------------------------------------------------------------- watchlist


def watch_add(kind: str, query: str, params: dict) -> int:
    with tx() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO watchlist (kind, query, params, created_at) VALUES (?, ?, ?, ?)",
            (kind, query.strip(), json.dumps(params), _now()),
        )
        row = conn.execute(
            "SELECT id FROM watchlist WHERE kind = ? AND query = ?", (kind, query.strip())
        ).fetchone()
        return int(row["id"])


def watch_list() -> list[dict]:
    with tx() as conn:
        rows = [dict(r) for r in conn.execute("SELECT * FROM watchlist ORDER BY created_at").fetchall()]
    for r in rows:
        r["params"] = json.loads(r["params"]) if r.get("params") else {}
        r["last_result"] = json.loads(r["last_result"]) if r.get("last_result") else None
    return rows


def watch_get(item_id: int) -> dict | None:
    for item in watch_list():
        if item["id"] == item_id:
            return item
    return None


def watch_delete(item_id: int) -> None:
    with tx() as conn:
        conn.execute("DELETE FROM watchlist WHERE id = ?", (item_id,))


def watch_mark_run(item_id: int, result: dict) -> None:
    with tx() as conn:
        conn.execute(
            "UPDATE watchlist SET last_run = ?, last_result = ? WHERE id = ?",
            (_now(), json.dumps(result, default=str), item_id),
        )


# --------------------------------------------------------------------------- caches


def cache_get(key: str) -> dict | None:
    with tx() as conn:
        row = conn.execute("SELECT * FROM http_cache WHERE key = ?", (key,)).fetchone()
        return dict(row) if row else None


def cache_put(key: str, status: int, content_type: str | None, final_url: str, body: bytes, fetched_at: float) -> None:
    with tx() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO http_cache (key, fetched_at, status, content_type, final_url, body) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (key, fetched_at, status, content_type, final_url, body),
        )


def geocode_get(query: str) -> dict | None:
    with tx() as conn:
        row = conn.execute("SELECT * FROM geocode_cache WHERE query = ?", (query.lower(),)).fetchone()
        return dict(row) if row else None


def geocode_put(query: str, lat: float | None, lon: float | None, region: str | None) -> None:
    with tx() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO geocode_cache (query, lat, lon, region, fetched_at) VALUES (?, ?, ?, ?, ?)",
            (query.lower(), lat, lon, region, _now()),
        )
