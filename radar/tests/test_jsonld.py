from ghostradar.sources import jsonld

PAGE = """
<html><head><script type="application/ld+json">
{"@context": "https://schema.org", "@graph": [
  {"@type": "Organization", "name": "Acme"},
  {"@type": "JobPosting", "title": "Elektroniker (m/w/d)", "datePosted": "2026-02-01",
   "validThrough": "2026-05-01T00:00:00+02:00", "description": "<p>Wartung von Anlagen</p>",
   "hiringOrganization": {"@type": "Organization", "name": "Acme GmbH", "sameAs": "https://acme.de"},
   "jobLocation": {"@type": "Place", "address": {"addressLocality": "Leipzig", "addressRegion": "Sachsen", "addressCountry": "DE"}},
   "baseSalary": {"@type": "MonetaryAmount", "currency": "EUR", "value": {"minValue": 3200, "maxValue": 3800, "unitText": "MONTH"}},
   "identifier": {"@type": "PropertyValue", "value": "REQ-77"}}
]}
</script></head><body><h1>Elektroniker</h1></body></html>
"""


def test_extract_jobposting_from_graph():
    postings = jsonld.extract(PAGE, "https://acme.de/jobs/77")
    assert len(postings) == 1
    p = postings[0]
    assert p.title == "Elektroniker (m/w/d)" and p.company == "Acme GmbH"
    assert p.city == "Leipzig" and p.region == "Sachsen"
    assert p.salary_min == 3200 and p.salary_period == "MONTH"
    assert p.requisition_id == "REQ-77"
    assert p.valid_through.month == 5
    assert jsonld.same_site(p.extra["org_url"], "https://www.acme.de/jobs/77")


def test_closed_markers():
    assert jsonld.looks_closed("<p>Diese Stellenanzeige ist nicht mehr verfügbar.</p>")
    assert jsonld.looks_closed("<p>This job is no longer available</p>")
    assert not jsonld.looks_closed("<p>Wir freuen uns auf Ihre Bewerbung.</p>")
