import asyncio
from datetime import datetime, timezone

import httpx
import respx

from ghostradar.analysis import labels
from ghostradar.config import settings
from ghostradar.http import PoliteClient
from ghostradar.sources import ba, jsearch, linkedin
from ghostradar.util import strip_contact_data

NOW = datetime(2026, 10, 24, 12, tzinfo=timezone.utc)


def test_applicant_labels_in_german_and_english():
    assert labels.parse_applicants("Berlin · 2 weeks ago · Over 100 applicants").count == 100
    assert labels.parse_applicants("Über 200 Bewerber:innen").lower_bound
    assert labels.parse_applicants("57 applicants").count == 57
    first = labels.parse_applicants("Be among the first 25 applicants")
    assert first.count == 25 and first.upper_bound
    assert labels.parse_applicants("Sei unter den ersten 25 Bewerber:innen").upper_bound
    assert labels.parse_applicants("Keine Angabe").count is None


def test_posted_labels_and_reposts():
    p = labels.parse_posted("Reposted 3 weeks ago", NOW)
    assert p.reposted and (NOW - p.date).days == 21
    d = labels.parse_posted("vor 2 Wochen erneut gepostet", NOW)
    assert d.reposted and (NOW - d.date).days == 14
    assert labels.parse_posted("Vor 30+ Tagen geschaltet", NOW).lower_bound
    assert labels.parse_posted("Veröffentlicht am 01.10.2026", NOW).date.day == 1
    assert (NOW - labels.parse_posted("Gestern", NOW).date).days == 1


def test_responsiveness_badges():
    assert labels.parse_responsiveness(["Bewerber:innen werden aktiv geprüft"]) == "active"
    assert labels.parse_responsiveness("No response insights available yet") == "none"
    assert labels.parse_responsiveness("Easy Apply") is None


def test_contact_data_is_stripped_but_dates_and_pay_survive():
    text = "Bewerbung an lisa.niklas@pilze-niklas.de oder Tel. 0171 / 123 45 67. Start 01.03.2027, 55.000 EUR."
    clean = strip_contact_data(text)
    assert "@" not in clean and "0171" not in clean
    assert "01.03.2027" in clean and "55.000" in clean


def test_linkedin_api_job_mapping():
    job = {"position": "Backend Engineer", "company": "Acme", "location": "Berlin, Berlin, Germany",
           "date": "2026-10-01", "agoTime": "3 weeks ago", "salary": "€60,000.00 - €75,000.00",
           "jobUrl": "https://de.linkedin.com/jobs/view/backend-engineer-at-acme-4012345678?refId=x"}
    p = linkedin.from_api_job(job, NOW)
    assert p.source_id == "4012345678" and p.url == "https://www.linkedin.com/jobs/view/4012345678/"
    assert p.city == "Berlin" and p.posted_at.day == 1
    assert (p.salary_min, p.salary_max, p.salary_currency) == (60000.0, 75000.0, "EUR")
    messy = linkedin.from_api_job({**job, "company": "Actaport\n          \n      "}, NOW)
    assert messy.company == "Actaport"


@respx.mock
def test_linkedin_search_through_local_api(monkeypatch):
    monkeypatch.setattr(settings, "linkedin_jobs_api", "http://localhost:3999")
    respx.post("http://localhost:3999/search").mock(return_value=httpx.Response(200, json={"cached": False, "total": 1, "jobs": [
        {"position": "Data Analyst", "company": "Acme", "location": "Leipzig, Saxony, Germany", "date": "2026-09-01",
         "agoTime": "1 month ago", "salary": "Not specified", "jobUrl": "https://www.linkedin.com/jobs/view/4099999999"}]}))

    async def go():
        client = PoliteClient()
        try:
            return await linkedin.search(client, "analyst", "Leipzig")
        finally:
            await client.aclose()

    postings, err = asyncio.run(go())
    assert err is None and postings[0].title == "Data Analyst" and postings[0].salary_min is None


def test_ba_item_mapping():
    item = {
        "stellenangebotsTitel": "Mitarbeiter/in im Qualitätsmanagement (m/w/d)", "referenznummer": "10001-1003907718-S",
        "firma": "Beispiel GmbH", "datumErsteVeroeffentlichung": "2026-10-24", "aenderungsdatum": "2026-10-24T10:03:08.380",
        "eintrittszeitraum": {"von": "2026-10-24"}, "verguetungsangabe": "KEINE_ANGABEN", "arbeitszeitVollzeit": True,
        "stellenlokationen": [{"adresse": {"ort": "Roding, Regen", "region": "BAYERN"}, "breite": 49.2, "laenge": 12.4}],
        "stellenangebotsBeschreibung": "Bewerbung an lisa@example.de", "arbeitgeberKundennummerHash": "abc",
    }
    p = ba.to_posting(item)
    assert p.source_id == "10001-1003907718-S" and p.city == "Roding" and p.region == "Bayern"
    assert p.start_date is None and p.start_immediate  # start = publication date means "ab sofort"
    assert "@" not in p.description and p.extra["employer_hash"] == "abc"
    assert ba.refnr_from_url("https://www.arbeitsagentur.de/jobsuche/jobdetail/10001-1003907718-S") == "10001-1003907718-S"


def test_ba_is_off_by_default():
    async def go():
        client = PoliteClient()
        try:
            return await ba.search(client, "Berlin")
        finally:
            await client.aclose()

    postings, note = asyncio.run(go())
    assert postings == [] and note == ba.OFF_NOTE


def test_jsearch_mapping_reads_apply_options():
    job = {"job_id": "abc==", "job_title": "Pflegefachkraft (m/w/d)", "employer_name": "Klinikum X",
           "job_publisher": "StepStone", "job_city": "Hamburg", "job_country": "DE",
           "job_posted_at_datetime_utc": "2026-08-01T00:00:00.000Z",
           "apply_options": [{"publisher": "StepStone", "apply_link": "https://www.stepstone.de/x", "is_direct": False},
                             {"publisher": "Klinikum X", "apply_link": "https://karriere.klinikum-x.de/1", "is_direct": True}]}
    p = jsearch.to_posting(job)
    assert p.extra["employer_apply_link"] == "https://karriere.klinikum-x.de/1"
    assert p.extra["publishers"] == ["Klinikum X", "StepStone"] and p.posted_at.month == 8


LINKEDIN_JOB = {"id": "4011111111", "position": "Senior Backend Engineer", "company": "Acme GmbH",
                "location": "Berlin, Berlin, Germany", "postedAgo": "Reposted 2 weeks ago",
                "applicants": "Over 200 applicants", "employmentType": "Full-time", "seniority": "Mid-Senior level",
                "acceptingApplications": True,
                "description": "Wir suchen Verstärkung für unser Backend-Team. Kontakt: jobs@example.com"}


@respx.mock
def test_linkedin_job_details_through_local_api(monkeypatch):
    monkeypatch.setattr(settings, "linkedin_jobs_api", "http://localhost:3999")
    respx.get("http://localhost:3999/job/4011111111").mock(return_value=httpx.Response(200, json=LINKEDIN_JOB))
    respx.get("http://localhost:3999/job/4022222222").mock(return_value=httpx.Response(404, json={"id": "4022222222", "removed": True}))
    respx.get("http://localhost:3999/job/4033333333").mock(
        return_value=httpx.Response(404, text="Cannot GET /job/4033333333", headers={"content-type": "text/html"}))
    respx.get("http://localhost:3999/job/4044444444").mock(
        return_value=httpx.Response(200, json={**LINKEDIN_JOB, "id": "4044444444", "acceptingApplications": False}))

    async def go():
        client = PoliteClient()
        try:
            return [await linkedin.detail(client, ref) for ref in (
                "https://www.linkedin.com/jobs/view/senior-backend-engineer-4011111111/", "4022222222", "4033333333",
                "4044444444")]
        finally:
            await client.aclose()

    (posting, observed, err), (_, _, removed), (_, _, old_api), (_, _, not_accepting) = asyncio.run(go())
    assert err is None and posting.source_id == "4011111111" and posting.city == "Berlin"
    assert "@" not in posting.description  # contact data is stripped on the way in
    assert posting.posted_at is None and posting.updated_at  # "Reposted 2 weeks ago" is a refresh, not a first date
    assert observed[:3] == ("linkedin", 200, "over") and observed[4] is True
    assert removed == "closed" and not_accepting == "closed"
    assert "no job-details endpoint" in old_api  # an older linkedin-jobs-mcp is not mistaken for a removed job


@respx.mock
def test_linkedin_search_names_the_country(monkeypatch):
    import json as _json

    monkeypatch.setattr(settings, "linkedin_jobs_api", "http://localhost:3999")
    route = respx.post("http://localhost:3999/search").mock(return_value=httpx.Response(200, json={"jobs": []}))

    async def go():
        client = PoliteClient()
        try:
            await linkedin.search(client, "analyst", "Hamburg")
        finally:
            await client.aclose()

    asyncio.run(go())
    assert _json.loads(route.calls[0].request.content)["location"] == "Hamburg, Germany"


@respx.mock
def test_ted_contract_awards():
    from ghostradar.sources import ted

    respx.post("https://api.ted.europa.eu/v3/notices/search").mock(return_value=httpx.Response(200, json={
        "totalNoticeCount": 1, "notices": [{
            "publication-number": "12345-2026", "publication-date": "2026-09-01+02:00", "notice-type": "can-standard",
            "notice-title": {"eng": "Germany – MRI scanner"}, "winner-name": {"deu": ["Acme Medical GmbH"]},
            "buyer-name": {"deu": ["Klinikum Nord"]}},
            {"publication-number": "12346-2026", "publication-date": "2026-09-02+02:00", "notice-type": "can-standard",
             "notice-title": {"eng": "Greece – Laboratory reagents"}, "winner-name": {"eng": ["Acme Medical Hellas"]}}]}))

    async def go():
        client = PoliteClient()
        try:
            return await ted.contracts(client, "Acme Medical", NOW)
        finally:
            await client.aclose()

    events, status = asyncio.run(go())
    assert status == "ok" and len(events) == 1 and events[0]["kind"] == "contract"  # buyers abroad are left out
    assert "Acme Medical GmbH won" in events[0]["title"] and "Klinikum Nord" in events[0]["title"]
    assert events[0]["url"].endswith("12345-2026")
