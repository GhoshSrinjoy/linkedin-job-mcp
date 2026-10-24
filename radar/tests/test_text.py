from datetime import date

from ghostradar.analysis import labels, text
from ghostradar.util import company_key, normalize_title, slug_candidates


def test_gender_tags_are_removed_from_titles():
    assert normalize_title("Softwareentwickler (m/w/d) Java") == "softwareentwickler java"
    assert normalize_title("Pflegefachkraft (w/m/d)") == "pflegefachkraft"
    assert normalize_title("Entwickler*in Backend") == "entwickler backend"
    assert normalize_title("Projektleiter:in Bau (all genders)") == "projektleiter bau"


def test_agency_markers_and_names():
    t = text.analyse("Lagerhelfer (m/w/d)", "Für unseren Kunden suchen wir im Rahmen der Arbeitnehmerüberlassung …",
                     "Randstad Deutschland GmbH & Co. KG")
    assert t.agency and t.agency[0].startswith("employer name")
    assert any("arbeitnehmerüberlassung" in h for h in t.agency)


def test_agency_false_positives_seen_in_live_data():
    # ordinary company language and skill requirements must not count as agency placement
    for desc in (
        "Reisebereitschaft: etwa 3 Tage im Monat für Kundentermine und Workshops.",
        "Technische Einweisungen für Kunden und Partner.",
        "Erfahrung in der Personaldienstleistung, Arbeitnehmerüberlassung oder im Recruiting ist ein Plus.",
        "Praktikum als Founder's Associate mit Option auf Übernahme.",
        "Wir beraten unsere Kunden in ganz Europa.",
    ):
        assert not text.analyse("Job", desc).agency, desc
    for desc in (
        "Im Auftrag unseres Partnerunternehmens in Berlin suchen wir Sie.",
        "Unser Kunde ist eine AI-first Agentur aus Berlin.",
        "Für unseren Kunden suchen wir eine Buchhalterin.",
    ):
        assert text.analyse("Job", desc).agency, desc


def test_pool_wording_ignores_consent_boilerplate_and_duties():
    consent = "Legal basis: with your consent, we will consider you for future opportunities."
    assert not text.analyse("Senior Engineer", consent).evergreen
    duty = "Your tasks: build and maintain a structured candidate pipeline."
    assert not text.analyse("Recruiter Intern", duty).evergreen


def test_evergreen_and_internal_markers():
    pool = text.analyse("Initiativbewerbung (m/w/d)", "Werde Teil unseres Talentpools für zukünftige Positionen.")
    assert pool.evergreen
    internal = text.analyse("Sachbearbeitung", "Interne Stellenausschreibung. Versetzungsbewerbungen sind willkommen.")
    assert internal.internal


def test_pay_grades_count_as_salary_information():
    t = text.analyse("Referent (m/w/d)", "Die Vergütung erfolgt nach TVöD Bund Entgeltgruppe E 13.")
    assert t.pay_grade and t.salary_present
    t2 = text.analyse("Developer", "Gehalt: 60.000 – 70.000 € brutto im Jahr, 30 Tage Urlaub.")
    assert t2.salary_present and "60.000" in t2.salary_text
    t3 = text.analyse("Developer", "Wir sind ein Startup mit 50 Mitarbeitenden in Berlin.")
    assert not t3.salary_present


def test_public_sector_requires_strong_cues():
    private = text.analyse("Data Scientist", "Abgeschlossenes Studium an einer Universität oder Hochschule.")
    assert not private.public_sector
    public = text.analyse("Sachbearbeiter", "Eine Verbeamtung ist möglich. Bezahlung nach TV-L E 9a im öffentlichen Dienst.")
    assert public.public_sector


def test_dates_are_parsed():
    t = text.analyse("Ingenieur", "Eintrittstermin: 01.03.2027. Bewerbungsfrist: 15.11.2026.")
    assert t.start_date == date(2027, 3, 1)
    assert t.application_deadline == date(2026, 11, 15)
    t2 = text.analyse("Engineer", "Start date: 1 April 2027")
    assert t2.start_date == date(2027, 4, 1)
    t3 = text.analyse("Koch", "Wir suchen ab sofort Verstärkung.")
    assert t3.start_immediate and t3.start_date is None


def test_scam_markers():
    t = text.analyse("Paketagent (m/w/d)", "Arbeiten von zu Hause: Pakete annehmen und weiterleiten. Kontakt nur per WhatsApp bewerben.")
    assert len(t.scam) >= 2


def test_company_keys_and_slugs():
    assert company_key("N26 GmbH") == "n26"
    assert company_key("Siemens AG") == "siemens"
    assert slug_candidates("Deutsche Bahn AG")[:2] == ["deutschebahn", "deutsche-bahn"]
    assert slug_candidates("Müller Gruppe GmbH")[0] == "mueller"


def test_project_and_funding_contingent_wording():
    assert text.analyse("Projektleiter", "Die Stelle ist vorbehaltlich der Projektvergabe zu besetzen.").contingent
    assert text.analyse("Engineer", "This position is subject to contract award by our client.").contingent
    assert text.analyse("Researcher", "The post is subject to funding.").contingent
    assert text.analyse("Consultant", "Wir suchen dich für ein geplantes Projekt in Hamburg.").prospective
    duty = "Du unterstützt bei der Vergabe von Aufträgen und begleitest projektabhängige Reisen."
    assert not text.analyse("Einkäufer", duty).contingent


def test_more_internal_preference_phrasings():
    assert text.analyse("Analyst", "Internal candidates will be given priority for this role.").internal
    assert text.analyse("Analyst", "This vacancy is open only to current employees.").internal


def test_application_instructions_are_not_talent_pool_wording():
    footer_de = ("Wir nehmen die DSGVO ernst. Deshalb bitten wir Sie, uns Ihren Lebenslauf nicht per E-Mail zu schicken. "
                 "Bitte legen Sie ein Profil in unserer Talent Community an, um Ihren Lebenslauf hochzuladen.")
    footer_en = ("We ask instead that you create a profile in our talent community where you can upload your CV. "
                 "Setting up a profile lets us know you are interested in career opportunities with us.")
    for footer in (footer_de, footer_en):
        assert not text.analyse("Softwareentwickler*in (w/m/d)", "Entwicklung von System-Software. " + footer).evergreen
    assert text.analyse("Talent Community (m/w/d)", "Werde Teil unserer Talent Community.").evergreen


def test_pending_approval_is_its_own_flag():
    t = text.analyse("Controller", "Die Position ist vorbehaltlich der Budgetfreigabe ab Januar zu besetzen.")
    assert t.pending_approval and not t.contingent
    assert text.analyse("Engineer", "This role is subject to final budget approval.").pending_approval


def test_clicks_are_not_applications():
    a = labels.parse_applicants("Over 200 people clicked apply")
    assert a.count == 200 and a.lower_bound and a.clicks
    assert not labels.parse_applicants("74 applicants").clicks


def test_funding_amount_from_headlines():
    from ghostradar.sources import news

    assert news.funding_details("Berliner Startup sammelt 12 Millionen Euro in Series A ein") == "€12M, Series A"
    assert news.funding_details("Acme raises $40M Series B") == "$40M, Series B"
    assert news.funding_details("Acme opens new office") is None
