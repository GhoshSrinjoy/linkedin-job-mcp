"""Runtime settings, read from environment variables or a local .env file."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(ROOT / ".env")


def _flag(name: str, default: str) -> bool:
    return os.environ.get(name, default).strip() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    db_path: Path = Path(os.environ.get("GHOSTRADAR_DB", str(DATA_DIR / "ghostradar.db")))
    baseline_csv: Path = DATA_DIR / "ba_engpass.csv"
    adzuna_app_id: str = os.environ.get("ADZUNA_APP_ID", "")
    adzuna_app_key: str = os.environ.get("ADZUNA_APP_KEY", "")
    user_agent: str = os.environ.get(
        "GHOSTRADAR_USER_AGENT",
        "GhostJobRadar/0.2 (research and educational job-market monitoring; low volume; respects robots.txt)",
    )
    robots_agent: str = "GhostJobRadar"
    request_timeout: float = float(os.environ.get("GHOSTRADAR_TIMEOUT", "20"))
    min_host_interval: float = float(os.environ.get("GHOSTRADAR_HOST_INTERVAL", "1.0"))
    cache_ttl_seconds: int = int(os.environ.get("GHOSTRADAR_CACHE_TTL", str(6 * 3600)))
    monitor_enabled: bool = _flag("GHOSTRADAR_MONITOR", "1")
    monitor_interval_hours: float = float(os.environ.get("GHOSTRADAR_MONITOR_HOURS", "12"))
    nominatim_enabled: bool = _flag("GHOSTRADAR_NOMINATIM", "1")
    # LinkedIn via the linkedin-jobs-mcp REST API (github.com/GhoshSrinjoy/linkedin-job-mcp), e.g. http://localhost:3000
    linkedin_jobs_api: str = os.environ.get("LINKEDIN_JOBS_API", "").rstrip("/")
    # Bundesagentur Jobsuche API (unofficial backend; its terms ban robots without BA permission)
    ba_jobsuche: bool = _flag("BA_JOBSUCHE", "0")
    # public contracts won, from the EU procurement journal TED (documented open API, no key)
    ted_contracts: bool = _flag("TED_CONTRACTS", "1")
    # JSearch (Google for Jobs aggregator: LinkedIn, Indeed, Glassdoor, StepStone, …) via RapidAPI or OpenWeb Ninja
    jsearch_api_key: str = os.environ.get("JSEARCH_API_KEY", "")
    jsearch_host: str = os.environ.get("JSEARCH_HOST", "jsearch.p.rapidapi.com")
    # browser extension origins allowed to call the local API
    cors_origin_regex: str = os.environ.get("GHOSTRADAR_CORS", r"^(chrome-extension|moz-extension)://[a-z0-9-]+$")

    @property
    def adzuna_enabled(self) -> bool:
        return bool(self.adzuna_app_id and self.adzuna_app_key)

    @property
    def linkedin_enabled(self) -> bool:
        return bool(self.linkedin_jobs_api)

    @property
    def jsearch_enabled(self) -> bool:
        return bool(self.jsearch_api_key)


settings = Settings()
