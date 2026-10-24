"""Text features for German and English job ads.

The research found no text signal linked to hiring outcomes, so text features
mostly route a posting to a ghost *type* (pool, pre-decided) and carry low weight
on their own. Lexicons are deliberately explicit so they can be reviewed.
"""
from __future__ import annotations

import re
from datetime import date

from ..models import TextFeatures
from ..util import normalize_space, strip_gender_tags


def _rx(*patterns: str) -> list[re.Pattern]:
    return [re.compile(p, re.I) for p in patterns]


EVERGREEN = _rx(
    r"\binitiativ\s?bewerb\w*",
    r"\binitiativ bewerben",
    r"\btalent\s?-?pool",
    r"\btalent ?community",
    r"\b(?:bewerber|kandidaten)pool",
    r"\bfür (?:zukünftige|künftige) (?:positionen|stellen|vakanzen|projekte|aufgaben)",
    r"\b(?:future|upcoming) (?:openings|opportunities|roles|positions|vacancies)",
    r"\b(?:general|unsolicited|spontaneous|open) application",
    r"\bwir suchen (?:immer|laufend|ständig|kontinuierlich|jederzeit)",
    r"\b(?:always|continuously|constantly) (?:looking|hiring|searching)",
    r"\bevergreen",
    r"\bkeine konkrete (?:stelle|vakanz|position)",
    r"\bno specific (?:vacancy|position|role|opening)",
    r"\bvorratsstelle",
)

# Placement grammar only: "für unseren Kunden" (accusative singular) is agency phrasing, whereas
# "für unsere Kunden" or "für Kundentermine" is ordinary company language. Mentions of the staffing
# industry as a skill ("Erfahrung in der Arbeitnehmerüberlassung") must not count.
AGENCY = _rx(
    r"\bfür (?:unseren|einen) (?:kunden|mandanten|klienten|auftraggeber)\b",
    r"\b(?:unser|unserem) (?:kunde|kunden|mandant|mandanten|auftraggeber)\b",
    r"\bunsere kundin\b",
    r"\bim (?:auftrag|kundenauftrag) (?:unseres|unserer|eines|einer) (?:kunden|kundin|mandanten|klienten|"
    r"partnerunternehmens|auftraggebers)\b",
    r"\b(?:im rahmen|im wege|auf basis) (?:der|einer|von) (?:arbeitnehmerüberlassung|zeitarbeit)\b",
    r"\b(?:einsatz|anstellung|beschäftigung) (?:bei|in) (?:unserem|einem) (?:kunden|kundenunternehmen)\b",
    r"\bübernahme (?:durch|beim|bei unserem|in den) (?:den )?kunden\b",
    r"\b(?:igz|gvp|bap)[- ]?(?:tarif|dgb|tarifvertrag)",
    r"\bdirektvermittlung\b",
    r"\bon behalf of (?:our|a) client\b",
    r"\bour client\b",
)

AGENCY_NAMES = re.compile(
    r"\b(?:randstad|adecco|manpower|hays|persona service|dis ag|orizon|tempton|piening|arwa|timepartner|"
    r"time partner|ik hofmann|i\.k\. hofmann|hofmann personal|amadeus fire|brunel|gulp|akkodis|modis|"
    r"trenkwalder|start people|jobactive|zag personal|avanti|autovision|page personnel|michael page|"
    r"robert half|robert walters|kelly services|experis|academic work|studitemps|westhouse|etengo|"
    r"actief|unique personal|fellow ?force|people ?force|office people|uniqo|careforce|medwork|"
    r"jobs in time|bindan|expertum|dekra arbeit|tuv rheinland personal)\b"
    r"|\b\w*(?:personaldienst\w*|personalservice|personal-service|personalmanagement|personalleasing|"
    r"zeitarbeit\w*|personalvermittlung|staffing|recruiting gmbh|personal gmbh|personalpartner)\b",
    re.I,
)

INTERNAL = _rx(
    r"\binterne? (?:stellen)?ausschreibung",
    r"\binnerbetriebliche (?:stellen)?ausschreibung",
    r"\bversetzungsbewerb\w*",
    r"\bbeförderungsdienstposten",
    r"\bbeförderungsamt",
    r"\binterne bewerber(?:innen)? werden (?:bevorzugt|vorrangig)",
    r"\bvorrangig (?:intern|interne)",
    r"\b(?:nur|ausschließlich) für (?:interne|beschäftigte|mitarbeitende)",
    r"\binternal candidates? (?:only|preferred|will be prioriti[sz]ed)",
    r"\binternal (?:job )?(?:posting|vacancy|advertisement)",
    r"\bnicht für externe",
    r"\binternal (?:applicants|candidates) (?:are|will be) (?:preferred|given (?:preference|priority)|prioriti[sz]ed)",
    r"\bpreference (?:will be|is) given to internal",
    r"\bopen (?:only )?to (?:internal|current) (?:candidates|applicants|employees|staff)\b",
    r"\binterne (?:bewerbungen|bewerber\w*|kandidat\w*) werden (?:bevorzugt|vorrangig)",
)

# the job exists only if a project, contract or grant is won (bid and grant hiring)
CONTINGENT = _rx(
    r"\bvorbehaltlich (?:der |des |einer |eines )?(?:erfolgreichen |positiven )?"
    r"(?:projekt|auftrags|mittel|budget|finanzierungs|förder)?"
    r"(?:vergabe|zusage|zuschlags?|beauftragung|bewilligung|genehmigung|freigabe|finanzierung|förderung)",
    r"\b(?:bei|nach) (?:erfolgreicher |positiver )?(?:projekt|auftrags)?(?:vergabe|beauftragung)\b",
    r"\b(?:bei|nach) (?:erteiltem |erfolgtem )?zuschlag\b",
    r"\bfür (?:ein|einen|eine) (?:potenzielles?|potentielles?|mögliches?|möglichen) (?:projekt|kundenprojekt|großprojekt|auftrag|vorhaben)",
    r"\bsubject to (?:the )?(?:successful )?(?:contract|project|funding|grant|budget|client) (?:award|approval|confirmation)",
    r"\bsubject to the award of (?:the |a )?(?:contract|project|grant|tender)",
    r"\bsubject to (?:the )?(?:availability of )?funding\b",
    r"\bcontingent (?:up)?on (?:the )?(?:contract|project|funding|grant|award|client approval)",
    r"\bpending (?:the )?(?:contract|project|funding|grant) (?:award|approval)",
    r"\bfor (?:an? )?(?:potential|anticipated|possible) (?:project|bid|tender|contract)\b",
)

# the position itself is not approved yet (budget or headcount approval pending)
PENDING_APPROVAL = _rx(
    r"\bvorbehaltlich (?:der |einer )?(?:budget|stellen|personal|headcount)?(?:freigabe|genehmigung|bewilligung)",
    r"\bvorbehaltlich (?:der )?(?:zustimmung|genehmigung) (?:durch )?(?:die |den )?(?:gremien|geschäftsführung|vorstand|aufsichtsrat)",
    r"\bsubject to (?:final )?(?:budget|headcount|internal|management|board) approval",
    r"\bpending (?:budget|headcount|final|internal) approval",
    r"\b(?:position|role) (?:is )?(?:not yet|still to be) approved",
)

# hiring for a project that has not started yet (weaker)
PROSPECTIVE = _rx(
    r"\bfür (?:ein|einen|eine) (?:zukünftiges?|künftiges?|anstehendes?|geplantes?) (?:projekt|kundenprojekt|großprojekt|auftrag|vorhaben)",
    r"\bfor (?:an? )?(?:upcoming|future|planned) (?:project|bid|tender|contract)\b",
)

WORKS_COUNCIL = _rx(
    r"\bbetriebsrat",
    r"\bpersonalrat",
    r"\bmitarbeitervertretung",
    r"§\s?93\s?betrvg",
    r"\bworks council",
)

DISABILITY = _rx(
    r"schwerbehindert\w*",
    r"\bgleichgestellte\b",
    r"\bseverely disabled",
)

PUBLIC_SECTOR = _rx(
    r"\btvöd\b",
    r"\btv-?l\b",
    r"\btv-?h\b",
    r"\btv-?ärzte\b",
    r"\bbesoldungsgruppe",
    r"\bbeamt(?:e|en|in|innen|enverhältnis)\b",
    r"\böffentlichen? dienst",
    r"\b(?:bundes|landes)(?:amt|behörde|anstalt|ministerium)",
    r"\bministerium\b",
    r"\b(?:stadt|kreis|gemeinde)verwaltung",
    r"\blandkreis\b",
    r"\b(?:körperschaft|anstalt|stiftung) des öffentlichen rechts",
)

PAY_GRADE = re.compile(
    r"\b(?:(?:tvöd|tv-?l|tv-?h|tv-?v|tv-?n|tv-?ärzte|avr|tv-?bund)\b[^.\n]{0,40}?\b(?:e|eg|p|s|kr|ä)\s?\d{1,2}[a-z]?\b"
    r"|(?:entgeltgruppe|eg)\s?(?:e\s?)?\d{1,2}[a-z]?\b"
    r"|besoldungsgruppe\s?[abwr]\s?\d{1,2}\b"
    r"|\b[abw]\s?\d{1,2}\s?(?:bbesg|lbesg|besoldung)"
    r"|\bw\s?[23]\b(?=[^.\n]{0,30}(?:professur|besoldung|w-besoldung)))",
    re.I,
)
TARIFF = re.compile(r"\b(?:tarifvertrag|tarifgebunden|tarifliche[nr]? (?:vergütung|bezahlung)|nach tarif|tarifvergütung|haustarif)\b", re.I)

MONEY = re.compile(
    r"(?:€|eur\b|euro\b)\s?\d{1,3}(?:[.\s]\d{3})*(?:,\d{1,2})?\s?(?:k\b)?"
    r"|\d{1,3}(?:[.\s]\d{3})+(?:,\d{1,2})?\s?(?:€|eur\b|euro\b)"
    r"|\d{2,3}\s?(?:k|tsd\.?|tausend)\s?(?:€|eur\b|euro\b)?"
    r"|\d{1,3}(?:,\d{1,2})?\s?(?:€|eur\b|euro\b)\s?(?:/|pro|per|je)\s?(?:std|stunde|h\b|hour)",
    re.I,
)
SALARY_WORDS = re.compile(
    r"gehalt|vergütung|salary|brutto|jahresgehalt|monatsgehalt|stundenlohn|stundensatz|bezahlung|"
    r"verdienst|einkommen|compensation|\bpay\b|\blohn\b|per annum|p\.\s?a\.|jährlich|monatlich",
    re.I,
)

IMMEDIATE = re.compile(
    r"\bab sofort\b|\bzum nächstmöglichen (?:zeitpunkt|termin)|\bschnellstmöglich\b|\bas soon as possible\b|"
    r"\basap\b|\bimmediate(?:ly)? (?:start|available)|\bstart(?:ing)? immediately",
    re.I,
)
_START_LEAD = (
    r"(?:ab|zum|start(?:termin|datum)?:?(?: am| zum| ab)?|beginn(?: am| zum| ab)?:?|eintritt(?:stermin)?:?(?: zum| am)?|"
    r"ausbildungsbeginn:?|ausbildungsstart:?|starting(?: on| from)?|start date:?|starts? on)"
)
START_NUMERIC = re.compile(_START_LEAD + r"\s*(?:dem\s)?(\d{1,2})\.\s?(\d{1,2})\.\s?(\d{2,4})", re.I)
_MONTHS = {
    "januar": 1, "january": 1, "jan": 1, "februar": 2, "february": 2, "feb": 2, "märz": 3, "maerz": 3,
    "march": 3, "april": 4, "apr": 4, "mai": 5, "may": 5, "juni": 6, "june": 6, "juli": 7, "july": 7,
    "august": 8, "aug": 8, "september": 9, "sept": 9, "sep": 9, "oktober": 10, "october": 10, "okt": 10,
    "oct": 10, "november": 11, "nov": 11, "dezember": 12, "december": 12, "dez": 12, "dec": 12,
}
START_MONTH = re.compile(
    _START_LEAD + r"\s*(?:dem\s|the\s)?(?:(\d{1,2})\.?\s*)?(" + "|".join(sorted(_MONTHS, key=len, reverse=True)) + r")\.?\s+(\d{4})",
    re.I,
)
DEADLINE = re.compile(
    r"(?:bewerbungsfrist|bewerbungsschluss|bewerbung(?:en)? bis(?: zum)?|bewerben sie sich bis(?: zum)?|"
    r"bewirb dich bis(?: zum)?|ende der bewerbungsfrist|einsendeschluss|apply by|application deadline|"
    r"deadline(?: for applications)?)\s*:?\s*(?:ist\s)?(?:der\s|am\s)?(\d{1,2})\.\s?(\d{1,2})\.\s?(\d{2,4})",
    re.I,
)
REFERENCE = re.compile(
    r"\b(?:kennziffer|kennzahl|referenz(?:nummer|code)?|ausschreibungs(?:nummer|kennziffer)|stellen(?:nummer|-?id)|"
    r"job-?id|reference(?: number| no\.?| code)?|req(?:uisition)?\.? ?(?:id|no\.?|#))\s*[:#]?\s*[A-Z0-9][\w\-/]{1,20}",
    re.I,
)
CONTACT = re.compile(
    r"\b(?:ansprechpartner(?:in)?|ihr(?:e)? kontakt|kontaktperson|deine? ansprechperson|"
    r"fragen beantwortet (?:ihnen|dir)|for (?:any )?questions,? (?:please )?contact|your contact)\b"
)
CONTACT_NAME = re.compile(r"\b(?:Frau|Herr|Mrs?\.|Ms\.)\s+(?:Dr\.\s+)?[A-ZÄÖÜ][a-zäöüß]+")
PROCESS = _rx(
    r"\bbewerbungsprozess",
    r"\bauswahlverfahren",
    r"\bvorstellungsgespräch",
    r"\bkennenlerngespräch",
    r"\binterview(?:s|prozess|runde)?\b",
    r"\btelefoninterview",
    r"\bvideo-?(?:call|interview)",
    r"\bprobearbeit",
    r"\bhospitation",
    r"\bassessment",
    r"\bcase study",
    r"\bfachgespräch",
    r"\b(?:rückmeldung|feedback|antwort) (?:innerhalb|binnen) (?:von )?\w+ (?:tagen|wochen)",
    r"\bwithin (?:\d+|one|two|three|four|five) (?:days|weeks)\b",
)
TEAM = _rx(
    r"\bteam (?:von|aus|of) \d+",
    r"\b\d+[- ]?köpfig\w* team",
    r"\bberichte(?:st|n sie)? (?:direkt )?an\b",
    r"\b(?:reporting|reports) to\b",
    r"\bdein (?:zukünftiges )?team (?:besteht|umfasst)",
    r"\byour team (?:consists|includes|of)",
)
VAGUE = [
    "abwechslungsreiche tätigkeit", "abwechslungsreiche aufgaben", "dynamisches team", "spannende aufgaben",
    "vielfältige aufgaben", "attraktive vergütung", "attraktives gehalt", "leistungsgerechte vergütung",
    "flache hierarchien", "kurze entscheidungswege", "familiäre atmosphäre", "angenehmes arbeitsklima",
    "moderne arbeitsumgebung", "zukunftssicherer arbeitsplatz", "spannendes umfeld", "innovatives unternehmen",
    "mehr als nur einen job", "work hard play hard", "hands-on-mentalität", "teamplayer",
    "fast-paced environment", "dynamic team", "competitive salary", "competitive compensation",
    "exciting opportunities", "self-starter", "rockstar", "ninja", "wear many hats",
    "other duties as assigned", "attractive salary", "make an impact", "passionate team", "great team",
]
BOILERPLATE = re.compile(
    r"datenschutz|dsgvo|gdpr|chancengleichheit|unabhängig von (?:geschlecht|alter|herkunft)|"
    r"equal opportunit|diversity|vielfalt|schwerbehindert|agg\b|privacy|consent|einwilligung|legal basis|"
    r"rechtsgrundlage|aufbewahr|retention|retain your|speicher(?:n|ung) (?:ihrer|deiner) (?:daten|bewerbung)|"
    # how to apply ("create a profile in our talent community to upload your CV") is process, not a talent pool
    r"lebenslauf (?:hoch|zu )?(?:zu)?laden|hochzuladen|upload (?:your|a|the) (?:cv|resume|résumé)|"
    r"(?:ein|einen|ihr|dein) profil (?:in|auf|bei) unser|create (?:a|your) (?:candidate )?profile|"
    r"nicht per e-?mail|not (?:to )?send (?:us )?your (?:cv|resume)",
    re.I,
)
SCAM = [
    (re.compile(r"\b(?:whatsapp|telegram)\b.{0,50}\b(?:bewerb|kontakt|apply|contact|melde|schreib)", re.I), "contact only via messenger"),
    (re.compile(r"\b(?:startgebühr|schulungsgebühr|bearbeitungsgebühr|vorkasse|anzahlung|registration fee|training fee|upfront (?:payment|fee))\b", re.I), "asks for a fee or upfront payment"),
    (re.compile(r"\b(?:paketagent|paketannahme|warenagent|pakete? (?:annehmen|weiterleiten|umpacken)|reshipping)\b", re.I), "parcel forwarding ('Paketagent') pattern"),
    (re.compile(r"\b(?:personalausweis|ausweiskopie|bankdaten|kontodaten|iban|kreditkarte|passport copy)\b.{0,60}\b(?:vorab|senden|schicken|übermitteln|mit der bewerbung)", re.I), "early request for ID or bank data"),
    (re.compile(r"(?:\d{3,5}\s?€|€\s?\d{3,5})\s?(?:pro|per|/|die|in der)\s?(?:tag|day|woche|week)\b.{0,80}(?:ohne (?:vor)?erfahrung|no experience)", re.I), "high pay with no experience required"),
    (re.compile(r"\b(?:produkttester|product tester)\b.{0,40}\b(?:von zuhause|from home)", re.I), "product-tester-from-home pattern"),
    (re.compile(r"\b(?:geld|money) (?:verdienen|making) (?:von zu ?hause|from home)", re.I), "easy money from home"),
]
SENIORITY = [
    ("executive", re.compile(r"\b(?:geschäftsführ\w*|ceo|cto|cfo|coo|vorstand|managing director|vice president|vp\b|chief\b|head of|bereichsleit\w*|direktor\w*|director)\b", re.I)),
    ("junior", re.compile(r"\b(?:junior|jr\.|trainee|werkstudent\w*|praktikum|praktikant\w*|intern(?:ship)?\b|azubi|auszubildende\w*|ausbildung (?:zum|zur|als)|duales studium|einsteiger\w*|absolvent\w*|graduate|berufseinsteiger\w*)\b", re.I)),
    ("senior", re.compile(r"\b(?:senior|sr\.|lead|principal|staff engineer|teamleit\w*|team lead|abteilungsleit\w*|leiter(?:in)?\b|manager)\b", re.I)),
]
APPRENTICESHIP = re.compile(
    r"\b(?:ausbildung (?:zum|zur|als)|ausbildungsplatz|azubi|auszubildende|duales studium|ausbildungsbeginn|"
    r"ausbildungsstart|ausbildungsjahr)\b",
    re.I,
)
YEARS = re.compile(r"\b(?:mindestens|mind\.|min\.|at least|über|more than)\s?(\d{1,2})\+?\s?(?:jahre|years)", re.I)
ACRONYM = re.compile(r"\b[A-ZÄÖÜ]{2,6}(?:[-/][A-Z0-9]{1,6})?\b")
CERT = re.compile(r"\b\w*(?:zertifizier|zertifikat|certified|certification|schein\b|lizenz|license)\w*", re.I)
SITE_SPECIFIC = re.compile(
    r"\berfahrung (?:am|im|an unserem) (?:standort|werk)|\bkenntnisse (?:des|unseres) (?:standortes|werkes|standorts)|"
    r"\bortskenntnisse|\bexperience (?:at|in) our (?:site|plant)",
    re.I,
)
MULTI_VACANCY = re.compile(
    r"\bmehrere (?:stellen|positionen|mitarbeiter|fachkräfte|kolleg\w+)|\bmultiple (?:positions|openings|hires)|"
    r"\b\d+\s?(?:stellen|positionen|positions|openings)\b",
    re.I,
)
_ACRONYM_STOP = {
    "GMBH", "AG", "SE", "KG", "UG", "EV", "DE", "EN", "UND", "OR", "AND", "THE", "WIR", "SIE", "DU", "IHR", "CV",
    "PDF", "FAQ", "HR", "MWD", "WMD", "MFD", "BZW", "CA", "INKL", "Z", "B", "USA", "EU", "EUR", "DSGVO", "AGG",
}

_DE_STOP = {"und", "der", "die", "das", "mit", "für", "wir", "sie", "ist", "nicht", "auf", "ein", "eine", "zu", "von", "bei", "ihre", "deine", "du"}
_EN_STOP = {"and", "the", "with", "for", "we", "you", "is", "not", "on", "a", "to", "of", "our", "your", "in"}


def _hits(patterns: list[re.Pattern], text: str, limit: int = 5) -> list[str]:
    found: list[str] = []
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            found.append(normalize_space(match.group(0))[:60])
        if len(found) >= limit:
            break
    return found


def _to_date(day: str | None, month: int, year: str) -> date | None:
    try:
        y = int(year)
        if y < 100:
            y += 2000
        return date(y, month, int(day) if day else 1)
    except (TypeError, ValueError):
        return None


def detect_language(text: str) -> str:
    words = re.findall(r"[a-zäöüß]+", text.lower())[:600]
    de = sum(1 for w in words if w in _DE_STOP)
    en = sum(1 for w in words if w in _EN_STOP)
    if de == en == 0:
        return "unknown"
    if de > en * 1.3:
        return "de"
    if en > de * 1.3:
        return "en"
    return "mixed"


def find_start_date(text: str) -> date | None:
    match = START_NUMERIC.search(text)
    if match:
        found = _to_date(match[1], int(match[2]), match[3]) if 1 <= int(match[2]) <= 12 else None
        if found:
            return found
    match = START_MONTH.search(text)
    if match:
        return _to_date(match[1], _MONTHS[match[2].lower()], match[3])
    return None


def find_salary(text: str) -> str | None:
    """The sentence or line stating pay, if a money amount sits next to a pay word."""
    for match in MONEY.finditer(text):
        window = text[max(0, match.start() - 90): match.end() + 90]
        if not SALARY_WORDS.search(window):
            continue
        start = max(text.rfind("\n", 0, match.start()), text.rfind(". ", 0, match.start() - 1))
        end_candidates = [i for i in (text.find("\n", match.end()), text.find(". ", match.end())) if i != -1]
        end = min(end_candidates) if end_candidates else len(text)
        return normalize_space(text[start + 1: end].lstrip(". "))[:140]
    return None


def analyse(title: str, description: str, company: str | None = None) -> TextFeatures:
    raw = f"{title}\n{description or ''}"
    text = strip_gender_tags(raw)
    lower = text.lower()
    words = re.findall(r"\w+", lower)
    features = TextFeatures(language=detect_language(text), word_count=len(words))

    # legal and process boilerplate (privacy, consent, equal opportunity) is excluded from
    # wording signals: "we keep your data for future opportunities" is not a talent pool
    sentences = re.split(r"(?<=[.!?\n])\s+", lower)
    core = " ".join(s for s in sentences if not BOILERPLATE.search(s))

    features.evergreen = _hits(EVERGREEN, core)
    features.agency = _hits(AGENCY, lower)
    if company and AGENCY_NAMES.search(company):
        features.agency.insert(0, f"employer name: {company}")
    features.internal = _hits(INTERNAL, lower)
    features.pending_approval = _hits(PENDING_APPROVAL, core)
    features.contingent = [c for c in _hits(CONTINGENT, core) if c not in features.pending_approval]
    features.prospective = _hits(PROSPECTIVE, core)
    features.works_council = _hits(WORKS_COUNCIL, lower)
    features.disability_boilerplate = any(p.search(lower) for p in DISABILITY)
    features.public_sector = _hits(PUBLIC_SECTOR, lower)
    if company and re.search(
        r"\b(?:stadt|landkreis|kreis|gemeinde|bundes\w*|landes\w*|ministerium|universität|hochschule|amt|behörde|"
        r"bundeswehr|polizei|landratsamt|senatsverwaltung|bezirksamt)\b",
        company,
        re.I,
    ):
        features.public_sector.insert(0, f"employer name: {company}")

    grade = PAY_GRADE.search(text)
    features.pay_grade = normalize_space(grade.group(0))[:40] if grade else None
    features.tariff_reference = bool(TARIFF.search(lower))
    features.salary_text = find_salary(text)
    features.salary_present = bool(features.salary_text or features.pay_grade)

    features.start_immediate = bool(IMMEDIATE.search(lower))
    features.start_date = find_start_date(text)
    deadline = DEADLINE.search(text)
    if deadline and 1 <= int(deadline[2]) <= 12:
        features.application_deadline = _to_date(deadline[1], int(deadline[2]), deadline[3])
    features.reference_code = bool(REFERENCE.search(text))
    features.named_contact = bool(CONTACT.search(lower) or CONTACT_NAME.search(text))
    features.process = _hits(PROCESS, lower, limit=6)
    features.team_context = _hits(TEAM, lower, limit=3)

    # vagueness is measured on the same boilerplate-free text
    core_words = max(1, len(re.findall(r"\w+", core)))
    features.vague = [phrase for phrase in VAGUE if phrase in core][:8]
    features.vague_per_100 = round(100.0 * len(features.vague) / core_words, 2)

    features.scam = [label for pattern, label in SCAM if pattern.search(text)]
    for level, pattern in SENIORITY:
        if pattern.search(title or ""):
            features.seniority = level
            break
    features.apprenticeship = bool(APPRENTICESHIP.search(raw))

    years = [int(m) for m in YEARS.findall(lower) if 0 < int(m) < 40]
    features.years_required = max(years) if years else None
    # narrow profiles: odd certificate combinations, site-specific experience, very long experience.
    # Tech ads are acronym-heavy by nature, so acronyms only count when extreme.
    acronyms = {a for a in ACRONYM.findall(description or "") if a.upper() not in _ACRONYM_STOP}
    certs = len(set(m.lower() for m in CERT.findall(description or "")))
    specificity = (
        0.15 * min(certs, 3)
        + (0.35 if SITE_SPECIFIC.search(lower) else 0.0)
        + (0.15 if features.years_required and features.years_required >= 8 else 0.0)
        + min(0.25, max(0.0, (len(acronyms) - 15) / 20.0))
    )
    features.requirement_specificity = round(min(1.0, specificity), 2)
    features.multi_vacancy = bool(MULTI_VACANCY.search(lower))
    return features
