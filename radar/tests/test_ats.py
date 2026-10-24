import asyncio

import httpx
import respx

from ghostradar.http import Blocked, PoliteClient, blocked_reason
from ghostradar.sources import ats

PERSONIO_XML = """<?xml version="1.0" encoding="UTF-8"?>
<workzag-jobs>
  <position>
    <id>123</id>
    <subcompany>Beispiel GmbH</subcompany>
    <office>München</office>
    <department>Engineering</department>
    <name>Backend Engineer (m/w/d)</name>
    <jobDescriptions><jobDescription><name>Deine Aufgaben</name><value><![CDATA[<p>Python &amp; Go</p>]]></value></jobDescription></jobDescriptions>
    <employmentType>permanent</employmentType>
    <schedule>full-time</schedule>
    <createdAt>2026-03-23T15:24:29+00:00</createdAt>
  </position>
</workzag-jobs>"""


def run(coro):
    return asyncio.run(coro)


def test_detect_from_url():
    assert ats.detect_from_url("https://boards.greenhouse.io/n26/jobs/12345")[0].slug == "n26"
    ref, job = ats.detect_from_url("https://jobs.eu.lever.co/acme/5b7c-uuid")
    assert ref.ats == "lever" and ref.host == "api.eu.lever.co" and job == "5b7c-uuid"
    ref, job = ats.detect_from_url("https://ottonova.jobs.personio.de/job/987?language=de")
    assert (ref.ats, ref.slug, job) == ("personio", "ottonova", "987")
    ref, job = ats.detect_from_url("https://jobs.smartrecruiters.com/BoschGroup/744000157589077-engineer")
    assert (ref.ats, job) == ("smartrecruiters", "744000157589077")
    ref, job = ats.detect_from_url("https://ag.wd3.myworkdayjobs.com/en-US/Airbus/job/Hamburg/Engineer_JR1")
    assert (ref.ats, ref.slug, ref.site, job) == ("workday", "ag", "Airbus", "/job/Hamburg/Engineer_JR1")
    assert ats.detect_from_url("https://example.com/jobs/1")[0] is None


def test_find_feed_links_in_careers_html():
    html = '<a href="https://boards.greenhouse.io/acme">Jobs</a> <script src="https://foo.jobs.personio.de/widget"></script>'
    found = {(r.ats, r.slug) for r in ats.find_feed_links(html)}
    assert ("greenhouse", "acme") in found and ("personio", "foo") in found


def test_blocked_domains():
    assert blocked_reason("https://www.linkedin.com/jobs/view/1")
    assert blocked_reason("https://de.indeed.com/viewjob?jk=1")
    assert blocked_reason("https://www.arbeitsagentur.de/jobsuche/jobdetail/1")
    assert blocked_reason("https://boards.greenhouse.io/n26") is None


@respx.mock
def test_personio_feed_is_parsed():
    respx.get("https://beispiel.jobs.personio.de/robots.txt").mock(return_value=httpx.Response(404))
    respx.get("https://beispiel.jobs.personio.de/xml").mock(return_value=httpx.Response(200, text=PERSONIO_XML))

    async def go():
        client = PoliteClient()
        try:
            return await ats.fetch_feed(client, ats.FeedRef("personio", "beispiel"))
        finally:
            await client.aclose()

    res = run(go())
    assert res.ok and res.complete and res.company_name == "Beispiel GmbH"
    p = res.postings[0]
    assert p.source_id == "beispiel:123" and p.department == "Engineering" and p.city == "München"
    assert p.posted_at.year == 2026 and "Python & Go" in p.description


@respx.mock
def test_greenhouse_feed_and_missing_board():
    respx.get("https://boards-api.greenhouse.io/robots.txt").mock(return_value=httpx.Response(404))
    respx.get("https://boards-api.greenhouse.io/v1/boards/acme/jobs").mock(return_value=httpx.Response(200, json={
        "jobs": [{"id": 7, "title": "Data Engineer", "absolute_url": "https://acme.com/jobs?gh_jid=7",
                  "location": {"name": "Berlin, Germany"}, "first_published": "2026-01-02T10:00:00Z",
                  "updated_at": "2026-10-01T10:00:00Z", "requisition_id": "R9", "content": "&lt;p&gt;Spark&lt;/p&gt;",
                  "departments": [{"name": "Data"}]}]}))
    respx.get("https://boards-api.greenhouse.io/v1/boards/acme").mock(return_value=httpx.Response(200, json={"name": "Acme"}))
    respx.get("https://boards-api.greenhouse.io/v1/boards/nobody/jobs").mock(return_value=httpx.Response(404))

    async def go():
        client = PoliteClient()
        try:
            return (await ats.fetch_feed(client, ats.FeedRef("greenhouse", "acme")),
                    await ats.fetch_feed(client, ats.FeedRef("greenhouse", "nobody")))
        finally:
            await client.aclose()

    good, missing = run(go())
    assert good.ok and good.company_name == "Acme"
    p = good.postings[0]
    assert p.requisition_id == "R9" and p.city == "Berlin" and p.description == "Spark"
    assert not missing.ok and "No public feed" in missing.error


@respx.mock
def test_robots_txt_is_respected():
    respx.get("https://careers.example.com/robots.txt").mock(
        return_value=httpx.Response(200, text="User-agent: *\nDisallow: /jobs/"))

    async def go():
        client = PoliteClient()
        try:
            await client.get("https://careers.example.com/jobs/1", ttl=0)
        finally:
            await client.aclose()

    try:
        run(go())
        raise AssertionError("expected Blocked")
    except Blocked as exc:
        assert "robots.txt" in exc.reason
