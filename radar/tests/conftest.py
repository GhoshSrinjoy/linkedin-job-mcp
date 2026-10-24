import pytest

from ghostradar import db
from ghostradar.config import settings


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Every test gets its own SQLite file and no background monitor."""
    db.close_db()
    monkeypatch.setattr(settings, "db_path", tmp_path / "test.db")
    monkeypatch.setattr(settings, "monitor_enabled", False)
    monkeypatch.setattr(settings, "min_host_interval", 0.0)
    monkeypatch.setattr(settings, "nominatim_enabled", False)
    # tests never depend on the local .env: every external connector is off unless a test turns it on
    monkeypatch.setattr(settings, "ba_jobsuche", False)
    monkeypatch.setattr(settings, "ted_contracts", False)
    monkeypatch.setattr(settings, "linkedin_jobs_api", "")
    monkeypatch.setattr(settings, "jsearch_api_key", "")
    monkeypatch.setattr(settings, "adzuna_app_id", "")
    monkeypatch.setattr(settings, "adzuna_app_key", "")
    db.init_db()
    yield
    db.close_db()
