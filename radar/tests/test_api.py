from fastapi.testclient import TestClient

from ghostradar.main import app

AD = """Initiativbewerbung (m/w/d)
Du findest keine passende Stelle? Bewirb dich initiativ für unseren Talentpool.
Wir melden uns, sobald eine passende Position frei wird."""


def test_meta_and_static_index():
    with TestClient(app) as client:
        meta = client.get("/api/meta").json()
        assert meta["baseline_occupations"] > 100
        assert client.get("/").status_code == 200


def test_check_pasted_text_without_network():
    with TestClient(app) as client:
        res = client.post("/api/check", json={"text": AD, "with_news": False}).json()
        assert res["mode"] == "manual"
        score = res["result"]["score"]
        assert any(t["key"] == "pool" and t["score"] >= 0.8 for t in score["types"])
        assert res["result"]["posting_id"]


def test_blocked_url_switches_to_manual_mode():
    with TestClient(app) as client:
        res = client.post("/api/check", json={"url": "https://www.linkedin.com/jobs/view/123", "with_news": False}).json()
        assert res["mode"] == "manual" and res["result"] is None
        assert any("LinkedIn" in n for n in res["notes"])


def test_capture_from_browser_extension():
    payload = {
        "platform": "linkedin",
        "url": "https://www.linkedin.com/jobs/search/?currentJobId=4011111111",
        "title": "Senior Backend Engineer",
        "location": "Berlin, Germany",
        "description": "Wir suchen Verstärkung für unser Backend-Team. Kontakt: jobs@example.com",
        "top_text": "Berlin, Germany · Reposted 3 weeks ago · Over 200 applicants",
        "badges": ["Responses managed off LinkedIn"],
        "with_news": False,
    }
    with TestClient(app) as client:
        res = client.post("/api/capture", json=payload).json()
        sp = res["result"]
        assert sp["posting"]["url"] == "https://www.linkedin.com/jobs/view/4011111111/"
        assert sp["features"]["user"]["applicant_count"] == 200
        assert sp["features"]["user"]["reposted_label"] is True
        assert "@" not in sp["posting"]["description"]
        assert any(r["signal"] == "reposted_label" for r in sp["score"]["reasons"])
        again = client.get(f"/api/postings/{sp['posting_id']}").json()
        assert again["features"]["user"]["applicant_count"] == 200  # remembered from the observation


def test_later_sightings_never_erase_the_original_posting_date():
    from datetime import datetime, timezone

    from ghostradar import db, services
    from ghostradar.models import Posting

    original = Posting(source="linkedin", source_id="4000000001", title="Data Engineer", company="Acme",
                       posted_at=datetime(2026, 4, 8, tzinfo=timezone.utc), channel="aggregator")
    (pid,) = services.ingest([original])
    later = Posting(source="linkedin", source_id="4000000001", title="Data Engineer", company="Acme",
                    updated_at=datetime(2026, 10, 10, tzinfo=timezone.utc), channel="aggregator")
    services.ingest([later])
    row = db.get_posting_row(pid)
    assert row["posted_at"].startswith("2026-04-08")
    scored = services.scored_posting(pid)
    assert scored.features.first_published.month == 4


def test_copies_of_one_job_are_merged_and_timeline_lists_them():
    from datetime import datetime, timezone

    from ghostradar import db, services
    from ghostradar.models import Posting

    now = datetime(2026, 10, 24, tzinfo=timezone.utc)
    text = "Wir suchen eine Data Engineerin (m/w/d) mit Spark, Python und Airflow für unser Plattform-Team."
    employer = Posting(source="greenhouse", source_id="acme:1", title="Data Engineer (m/w/d)", company="Acme",
                       city="Berlin", description=text, posted_at=datetime(2026, 6, 1, tzinfo=timezone.utc))
    copy = Posting(source="linkedin", source_id="4111111111", title="Data Engineer (m/w/d)", company="Acme",
                   city="Berlin", description=text, channel="aggregator", posted_at=datetime(2026, 6, 3, tzinfo=timezone.utc))
    ids = services.ingest([employer, copy], now=now)
    rows = [db.get_posting_row(i) for i in ids]
    assert rows[0]["cluster_id"] == rows[1]["cluster_id"]
    scored = [services.score_row(r, now, None) for r in rows]
    merged = services.one_per_job(scored, rows)
    assert len(merged) == 1 and merged[0].posting.channel == "employer"
    assert {c.source for c in merged[0].copies} == {"greenhouse", "linkedin"}
    with TestClient(app) as client:
        data = client.get(f"/api/postings/{ids[0]}/timeline").json()
        assert len(data["instances"]) == 2 and data["expected_days"]


def test_city_filters_are_accepted():
    with TestClient(app) as client:
        res = client.get("/api/city", params={"city": "Leipzig", "posted_within": 7, "job_type": "full_time",
                                              "exclude_agencies": "true", "sources": "tracked"})
        assert res.status_code == 200
        body = res.json()
        assert body["summary"]["filters"]["job_type"] == "full_time"
        assert body["summary"]["filters"]["sources"] == ["tracked"]


def test_tasks_report_progress_and_result():
    import time

    with TestClient(app) as client:
        task_id = client.post("/api/tasks/check", json={"text": AD, "with_news": False}).json()["task_id"]
        for _ in range(50):
            data = client.get(f"/api/tasks/{task_id}").json()
            if data["state"] != "running":
                break
            time.sleep(0.05)
        assert data["state"] == "done"
        assert data["progress"]["fraction"] == 1.0
        assert {s["key"] for s in data["progress"]["steps"]} >= {"read", "score"}
        coverage = {c["key"]: c["state"] for c in data["result"]["result"]["score"]["coverage"]}
        assert coverage["wording"] == "used" and coverage["applicants"] == "missing"


def test_republication_across_platforms_is_visible_on_first_check():
    from datetime import datetime, timezone

    from ghostradar import services
    from ghostradar.models import Posting

    now = datetime(2026, 10, 24, tzinfo=timezone.utc)
    text = "Wir suchen eine Projektleitung Bau (m/w/d) für Großprojekte im Hochbau in Leipzig und Umgebung."
    old = Posting(source="ba", source_id="10001-1", title="Projektleiter Bau (m/w/d)", company="Bau AG", city="Leipzig",
                  description=text, channel="aggregator", posted_at=datetime(2025, 12, 1, tzinfo=timezone.utc))
    new = Posting(source="linkedin", source_id="4200000000", title="Projektleiter Bau (m/w/d)", company="Bau AG",
                  city="Leipzig", description=text, channel="aggregator", posted_at=datetime(2026, 10, 10, tzinfo=timezone.utc))
    ids = services.ingest([old, new], now=now)
    scored = services.scored_posting(ids[1])
    assert scored.features.repost.republished_days >= 300
    assert any(r.signal == "republished" for r in scored.score.reasons)


def test_watchlist_and_reports_roundtrip():
    with TestClient(app) as client:
        item = client.post("/api/watchlist", json={"kind": "city", "query": "Leipzig", "params": {"keyword": "python"}}).json()
        assert any(w["id"] == item["id"] for w in client.get("/api/watchlist").json())
        client.delete(f"/api/watchlist/{item['id']}")
        assert client.get("/api/watchlist").json() == []
        rep = client.post("/api/reports", json={"company": "Acme GmbH", "response": "none", "applied_on": "2026-09-01"}).json()
        assert rep["id"]
        assert client.get("/api/reports", params={"company": "Acme"}).json()[0]["response"] == "none"


def test_overview_scores_everything_stored():
    from datetime import datetime, timezone

    from ghostradar import services
    from ghostradar.models import Posting

    now = datetime(2026, 10, 24, tzinfo=timezone.utc)
    text = "Wir suchen eine Data Engineerin (m/w/d) mit Spark, Python und Airflow für unser Plattform-Team."
    services.ingest([
        Posting(source="greenhouse", source_id="acme:1", title="Data Engineer (m/w/d)", company="Acme", city="Berlin",
                description=text, posted_at=datetime(2026, 6, 1, tzinfo=timezone.utc)),
        Posting(source="linkedin", source_id="4111111111", title="Data Engineer (m/w/d)", company="Acme", city="Berlin",
                description=text, channel="aggregator", posted_at=datetime(2026, 6, 3, tzinfo=timezone.utc)),
        Posting(source="ba", source_id="10001-2", title="Pflegefachkraft (m/w/d)", company="Klinik Nord", city="Hamburg",
                description="Pflegefachkraft für die Intensivstation gesucht.", channel="aggregator",
                posted_at=datetime(2026, 9, 1, tzinfo=timezone.utc)),
    ], now=now)
    with TestClient(app) as client:
        data = client.get("/api/overview").json()
    assert data["totals"]["jobs"] == 2 and data["totals"]["postings"] == 3
    assert sum(data["grades"].values()) == 2
    assert data["groups"] == {"Employer sites": 1, "Bundesagentur": 1}
    assert {c["company"] for c in data["top_cities"]} == {"Berlin", "Hamburg"}
    assert all(j["posting"]["description"] is None for j in data["jobs"])
    assert data["months"]


def test_employer_notes_and_outcomes_change_the_scores():
    from datetime import timedelta

    from ghostradar import db, services
    from ghostradar.models import Posting
    from ghostradar.util import utcnow

    ids = services.ingest([Posting(source="ba", source_id="20001-1", title="Softwareentwickler (m/w/d)",
                                   company="Example AG", city="Erlangen", description="", channel="aggregator",
                                   posted_at=utcnow() - timedelta(days=5))])
    cid = db.find_company("Example AG")["id"]
    with TestClient(app) as client:
        assert client.get(f"/api/postings/{ids[0]}").json()["score"]["grade"] == "low"
        profile = {"hiring_practice": "internal_first", "practice_note": "own applications", "headcount": 120,
                   "headcount_prev": 100, "funding_date": "2026-01-15", "funding_amount": "€10M Series A"}
        assert client.put(f"/api/company/{cid}", json=profile).json()["ok"]
        for _ in range(2):
            client.post("/api/reports", json={"company": "Example AG", "posting_id": ids[0], "response": "internal",
                                              "applied_on": "2026-09-01"})
        after = client.get(f"/api/postings/{ids[0]}").json()
        assert {"practice_internal", "outcome_internal"} <= {r["signal"] for r in after["score"]["reasons"]}
        assert after["score"]["grade"] in {"moderate", "elevated"}
        sig = after["features"]["company"]
        assert sig["growth"] == 0.2 and sig["funding_source"] == "your note" and sig["reports"]["internal"] == 2
        client.put(f"/api/company/{cid}", json={"hiring_practice": ""})
        cleared = client.get(f"/api/postings/{ids[0]}").json()
        assert "practice_internal" not in {r["signal"] for r in cleared["score"]["reasons"]}
        assert db.get_company(cid)["headcount"] == 120  # fields left out are kept


def test_linkedin_link_is_checked_through_linkedin_jobs_mcp(monkeypatch):
    import httpx
    import respx

    from ghostradar.config import settings

    monkeypatch.setattr(settings, "linkedin_jobs_api", "http://localhost:3999")
    job = {"id": "4055555555", "position": "Senior Backend Engineer", "company": "Acme GmbH", "location": "Berlin, Germany",
           "postedAgo": "3 weeks ago", "applicants": "Over 200 applicants", "employmentType": "Full-time",
           "acceptingApplications": True,
           "description": "Wir suchen eine Backend-Entwicklerin (m/w/d) für unser Plattform-Team in Berlin. Python und Go."}
    with respx.mock(assert_all_called=False) as router:
        router.get("http://localhost:3999/job/4055555555").mock(return_value=httpx.Response(200, json=job))
        router.route().mock(return_value=httpx.Response(404))  # employer feed guesses and robots.txt: nothing found
        with TestClient(app) as client:
            res = client.post("/api/check", json={"url": "https://www.linkedin.com/jobs/view/backend-4055555555/",
                                                  "with_news": False}).json()
    assert res["mode"] == "fetched" and "LinkedIn via linkedin-jobs-mcp" in res["sources_used"]
    sp = res["result"]
    assert "Plattform-Team" in sp["posting"]["description"]
    assert sp["score"]["competition"]["level"] == "very_high"  # 200+ applicants read from the job page
    assert sp["features"]["user"]["applicant_count"] == 200


def test_prefs_events_notes_and_evidence_log():
    from datetime import timedelta

    from ghostradar import db, services
    from ghostradar.models import Posting
    from ghostradar.util import utcnow

    ids = services.ingest([Posting(source="ba", source_id="30001-1", title="Softwareentwickler (m/w/d)", company="Beispiel GmbH",
                                   city="Leipzig", description="Wir suchen Verstärkung.", channel="aggregator",
                                   posted_at=utcnow() - timedelta(days=40))])
    cid = db.find_company("Beispiel GmbH")["id"]
    with TestClient(app) as client:
        assert client.get("/api/prefs").json()["window_days"] == 365
        assert client.put("/api/prefs", json={"chance_high": 300, "chance_very_high": 200}).status_code == 422
        saved = client.put("/api/prefs", json={"chance_high": 20, "chance_very_high": 100, "window_days": 90}).json()
        assert saved["chance_high"] == 20 and saved["window_days"] == 90
        assert client.post(f"/api/company/{cid}/events", json={"kind": "hiring_freeze", "date": str((utcnow() - timedelta(days=5)).date()),
                                                             "note": "announced in the all-hands"}).json()["ok"]
        sp = client.get(f"/api/postings/{ids[0]}").json()
        assert any(r["signal"] == "distress" and "your note" in r["label"] for r in sp["score"]["reasons"])
        event = next(e for e in sp["features"]["company"]["events"] if e["source"] == "your note")
        news_like = db.add_events(cid, [{"kind": "distress", "title": "Stellenabbau", "url": "https://example.org/a",
                                         "published_at": utcnow(), "source": "example.org"}])
        other = next(e for e in db.company_events(cid) if e["source"] == "example.org")
        assert client.delete(f"/api/company/{cid}/events/{other['id']}").status_code == 404  # news stays
        assert client.delete(f"/api/company/{cid}/events/{event['id']}").json()["ok"]
        imported = client.post("/api/notes/import", json={"csv": "company;practice;note\nmeinGPT;internal_first;own applications\nBad;maybe;x"}).json()
        assert imported["added"] == 1 and len(imported["skipped"]) == 1
        assert any(n["name"] == "meinGPT" and n["hiring_practice"] == "internal_first" for n in client.get("/api/notes").json())
        log = client.get(f"/api/postings/{ids[0]}/evidence").json()
        assert {"posting"} <= {e["kind"] for e in log} and all(e["at"] for e in log)


def test_overview_leaves_out_jobs_outside_germany():
    from ghostradar import services
    from ghostradar.models import Posting

    services.ingest([
        Posting(source="linkedin", source_id="4100000001", title="Cashier", company="Store Inc", location="Chula Vista, CA",
                city="Chula Vista", channel="aggregator", description="Cashier wanted."),
        Posting(source="linkedin", source_id="4100000002", title="Data Engineer", company="Acme", location="Berlin, Berlin, Germany",
                city="Berlin", channel="aggregator", description="Data Engineer gesucht."),
    ])
    with TestClient(app) as client:
        data = client.get("/api/overview").json()
    assert data["totals"]["jobs"] == 1 and data["jobs"][0]["posting"]["city"] == "Berlin"
