"""German vacancy-duration baselines from the BA Engpassanalyse.

Raw posting age misleads in Germany (86 days from search start to start of work
in 2025; BA vacancies take 156 days on average to be deregistered). Age only
means something relative to the occupation's normal duration, so every posting
is mapped to a KldB-2010 occupation group (3 digits) and a requirement level,
and compared with the BA's median completed vacancy duration (Vakanzzeit).

Data: © Statistik der Bundesagentur für Arbeit, Engpassanalyse 2025.
The mapping and the "expected days" rule are our own calculations.
"""
from __future__ import annotations

import csv
import re
import statistics
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from ..config import settings
from ..models import Baseline
from ..util import normalize_title, parse_datetime

# The BA clock runs from the employer's desired start date; ads usually go up
# about a month earlier, so the expected live time adds a lead time.
LEAD_DAYS = 30
MIN_EXPECTED_DAYS = 45

LEVELS = {"1": "Helfer", "2": "Fachkräfte", "3": "Spezialisten", "4": "Experten"}

# (pattern on the normalised title, KldB-2010 group, default requirement level)
# Ordered: specific patterns first. Group labels come from the BA file.
TITLE_RULES: list[tuple[str, str, str]] = [
    # health and care
    (r"pflegehelfer|pflegeassist|altenpflegehelfer|betreuungskraft|alltagsbegleit", "813x+821", "1"),
    (r"pflegefach|krankenpfleg|krankenschwester|altenpfleg|kinderkrankenpfleg|gesundheits und krankenpfleg|"
     r"intensivpfleg|anästhesiepfleg|op pflege|pflegedienstleit|stationsleit|wohnbereichsleit|notfallsanitäter|"
     r"rettungssanitäter|hebamme|\bnurse\b|\bpflege", "813x+821", "2"),
    (r"zahnmedizinische fachangestellte|medizinische fachangestellte|\bmfa\b|\bzfa\b|arzthelfer|praxisassist", "811", "2"),
    (r"\bmta\b|\bmtla\b|\bmtr\b|medizinisch technische|biomedizinische analytik", "812", "2"),
    (r"tierarzt|tierärzt|tiermedizinische|\btfa\b|veterinär", "815", "4"),
    (r"zahnarzt|zahnärzt|assistenzarzt|assistenzärzt|facharzt|fachärzt|oberarzt|oberärzt|chefarzt|chefärzt|"
     r"\barzt\b|\bärztin\b|physician|medical doctor", "814", "4"),
    (r"psycholog|psychotherap", "816", "4"),
    (r"physiotherap|ergotherap|logopäd|heilpraktik|masseur|osteopath", "817", "2"),
    (r"apotheker|pharmazeut|\bpta\b", "818", "4"),
    (r"orthopädietechn|zahntechn|hörakust|augenoptik|medizintechnik techniker", "825", "2"),
    (r"friseur|kosmetik", "823", "2"),
    (r"erzieher|kinderpfleger|kita|sozialpädagog|sozialarbeit|heilerziehungspfleg|pädagogische fachkraft|"
     r"jugendhilfe|schulbegleit", "831", "2"),
    (r"lehrkraft|lehrer|grundschul|gymnasial|oberschul", "841", "4"),
    (r"wissenschaftliche r mitarbeiter|wissenschaftlicher mitarbeiter|wissenschaftliche mitarbeiterin|postdoc|"
     r"doktorand|\bphd\b|professor|professur|research associate|lecturer|research scientist", "843", "4"),
    (r"ausbilder|berufsschullehr", "842", "3"),
    (r"dozent|kursleit|nachhilfe|trainer in der erwachsenenbildung", "844", "3"),
    # IT
    (r"data scien|machine learning|\bml\b|\bai engineer|\bki\b|künstliche intelligenz|data engineer|"
     r"data analyst|informatiker", "431", "4"),
    (r"fachinformatiker systemintegration|systemadministr|sysadmin|it administr|netzwerk|network engineer|"
     r"it support|helpdesk|service desk|it techniker|cloud|site reliability|\bsre\b|it security|"
     r"informationssicherheit|cyber ?security|security engineer|system engineer|systems engineer|"
     r"it infrastruktur|it infrastructure|devops|platform engineer|kubernetes", "433", "3"),
    (r"sap berater|sap consultant|it berater|it consultant|it projekt|it project|product owner|scrum master|"
     r"architect|architekt it|it architekt|systemanalyt|business analyst|anwendungsbetreu|presales|pre sales|"
     r"solution engineer|it vertrieb|it sales", "432", "4"),
    (r"hardware ?entwickl|elektronikentwickl|fpga|leiterplatt|hardware engineer", "263", "4"),
    # testing of machines, devices and materials is technical R&D, not software testing
    (r"(?:mechanical|mechanik|mechanische?r?|hardware|electrical|elektrische?r?|vehicle|fahrzeug|material|werkstoff)"
     r" ?(?:test|prüf)\w*|prüfingenieur|prüftechnik|prüfstand|test ?bench", "271", "4"),
    (r"software|anwendungsentwickl|web ?entwickl|app ?entwickl|datenbankentwickl|spieleentwickl|"
     r"developer|programmier|frontend|front end|backend|back end|full ?stack|\bios\b|android|"
     r"web dev|java|python|\.net|php|golang|typescript|react|angular|\bvue\b|node|c\+\+|c#|"
     r"qa engineer|test engineer|testautomat|abap|fachinformatiker anwendungsentwicklung|"
     r"game developer|embedded", "434", "4"),
    # engineering and production
    (r"kfz|kraftfahrzeug|fahrzeugtechn|karosserie|automotive mechan|luftfahrt|aerospace|flugzeug|schiffbau|"
     r"zweiradmechan", "252", "2"),
    (r"mechatronik|mechatroniker|automatisierung|automation engineer|\bsps\b|\bplc\b|robotik|robotics", "261", "2"),
    (r"elektroniker für energie|energietechnik|energieanlagen|photovoltaik|solar|wind ?energie|netzmonteur|"
     r"energieelektron", "262", "2"),
    (r"elektrotechn|elektroniker|elektriker|electrical engineer|elektroingenieur|elektromonteur|"
     r"elektroinstallat|elektronik", "263", "2"),
    (r"forschung und entwicklung|\bf und e\b|r d engineer|research engineer|entwicklungsingenieur|"
     r"versuchsingenieur", "271", "4"),
    (r"konstrukteur|konstruktion|technischer zeichner|technische zeichnerin|\bcad\b|design engineer", "272", "3"),
    (r"arbeitsvorbereit|produktionsplan|fertigungsplan|production planner|qualitätsmanag|qualitätssicher|"
     r"quality engineer|quality manager|\bqm\b|produktionsleit|fertigungsleit|prozessingenieur|"
     r"process engineer|industrial engineer", "273", "3"),
    (r"schweißer|schweisser|metallbauer|welder|schlosser", "244", "2"),
    (r"zerspanungsmechan|\bcnc\b|dreher|fräser|machinist|werkzeugmechan", "242", "2"),
    (r"maschinenbau|mechanical engineer|industriemechan|instandhalt|servicetechniker|anlagenmechaniker industrie|"
     r"maintenance|field service|service engineer", "251", "2"),
    (r"verfahrensmechaniker kunststoff|kunststoff", "221", "2"),
    (r"chemik|chemielaborant|chemist|laborant|labor", "413", "2"),
    (r"biolog|biotechnolog", "412", "4"),
    (r"physiker|physicist", "414", "4"),
    (r"mathematik|statistik|aktuar|actuary", "411", "4"),
    (r"nachhaltigkeit|sustainability|umweltmanag|umweltberat|\besg\b|klimaschutz", "423", "4"),
    (r"umwelttechn|umweltschutz", "422", "3"),
    (r"bäcker|konditor|fleischer|metzger|lebensmitteltechn", "292", "2"),
    (r"produktionsmitarbeiter|produktionshelfer|maschinenbediener|anlagenbediener|montagehelfer|monteur", "251", "1"),
    # construction and buildings
    (r"architekt|bauingenieur|bauleit|civil engineer|tragwerksplan|projektleiter bau|bauplan|bauüberwach", "311", "4"),
    (r"vermess|geomatik", "312", "3"),
    (r"maurer|betonbauer|hochbau|polier|dachdeck|gerüstbau", "321", "2"),
    (r"tiefbau|straßenbau|strassenbau|kanalbau|gleisbau|rohrleitungsbau", "322", "2"),
    (r"bodenleger|fliesenleger|parkettleger", "331", "2"),
    (r"maler|lackierer|stuckateur", "332", "2"),
    (r"trockenbau|zimmerer|zimmermann|tischler|schreiner|fensterbau|glaser|isolier", "333", "2"),
    (r"anlagenmechaniker|sanitär|heizung|klima|installateur|klempner|\bshk\b|kältetechn", "342", "2"),
    (r"haustechn|gebäudetechn|hausmeister|facility techn", "341", "2"),
    (r"entsorgung|abwasser|wasserversorg|recycling", "343", "2"),
    (r"gärtner|garten und landschaftsbau|galabau|landschaftsgärtner|florist", "121", "2"),
    (r"landwirt|agrar", "111", "2"),
    (r"tierpfleger|tierpflege", "115", "2"),
    # transport and logistics
    (r"staplerfahrer|gabelstapler|kranführer|baggerfahrer|radlader", "525", "1"),
    (r"berufskraftfahrer|lkw|kraftfahrer|busfahrer|fahrer|kurierfahrer|truck driver|driver", "521", "2"),
    (r"lokführer|triebfahrzeugführer|zugführer", "522", "2"),
    (r"flugbegleit|zugbegleit|flight attendant|cabin crew", "514", "2"),
    (r"speditionskaufm|disponent|logistikkaufm|kaufmann für spedition|kauffrau für spedition|supply chain|"
     r"logistics coordinator|logistics manager|logistikmanag", "516", "3"),
    (r"fachkraft für lagerlogistik|fachlagerist", "513", "2"),
    (r"lager|logistik|kommissionier|versand|zusteller|paketzustell|warehouse|picker|packer|postbote", "513", "1"),
    # sales, retail, hospitality
    (r"verkäufer|verkaufsberat|kassierer|einzelhandel|sales associate|retail|filialleit|store manager|"
     r"verkaufsmitarbeiter|kaufmann im einzelhandel|kauffrau im einzelhandel", "621", "2"),
    (r"bäckereifachverkäuf|fleischereifachverkäuf|lebensmittel verkauf", "623", "2"),
    (r"key account|account manag|account executive|vertrieb|sales|business development|außendienst|"
     r"aussendienst|einkäufer|einkauf|procurement|buyer|kundenberater", "611", "3"),
    (r"e commerce|ecommerce|category manag|handelsfachwirt|groß und außenhandel", "612", "3"),
    (r"immobilien|makler|property manag|facility manag|hausverwalt|objektbetreu", "613", "3"),
    (r"reiseverkehr|reisebüro|tourism|tourismus|sportlehrer|fitnesstrainer", "631", "2"),
    (r"rezeption|hotelfach|front office|housekeeping|zimmermädchen|hotel", "632", "2"),
    (r"veranstaltungskaufm|eventmanag|event manag", "634", "3"),
    (r"küchenhilfe|spülkraft|beikoch", "293", "1"),
    (r"\bkoch\b|\bköchin\b|chef de partie|sous chef|küchenchef|\bcook\b", "293", "2"),
    (r"servicekraft|kellner|restaurantfach|barkeeper|systemgastronom|gastronom|waiter|barista", "633", "1"),
    # business, finance, law, administration
    (r"geschäftsführ|managing director|\bceo\b|vorstand", "711", "4"),
    (r"steuerberater|steuerfachangest|tax manager|tax consultant|tax advisor|steuerfach", "723", "3"),
    (r"buchhalt|bilanzbuchhalt|finanzbuchhalt|accountant|accounting|controller|controlling|revision|"
     r"internal audit|financial analyst|finanzanalyst|kreditor|debitor|lohnbuchhalt", "722", "3"),
    (r"bankkaufm|bankberat|finanzberat|versicherungskaufm|versicherungsfach|underwriter|kreditanalyst|"
     r"risk manag|risikomanag|investment|anlageberat|vermögensberat|treasury", "721", "3"),
    (r"personalreferent|personalsachbearbeit|personalleit|personalberat|recruiter|recruiting|talent acquisition|"
     r"\bhr\b|human resources|people partner|people operations|entgeltabrechn|gehaltsabrechn|payroll|"
     r"personalentwickl", "715", "3"),
    (r"rechtsanwalt|rechtsanwält|jurist|syndikus|legal counsel|paralegal|rechtsanwaltsfachangest|"
     r"notarfachangest|compliance", "731", "4"),
    (r"verwaltungsfachangest|verwaltungswirt|sachbearbeiter verwaltung|verwaltung|public administration|"
     r"kommunal|bürgerbüro|standesamt", "732", "2"),
    (r"bibliothek|archivar|dokumentar", "733", "3"),
    (r"büro|sekretär|assistenz|assistant|office manag|kaufmann für büromanagement|kauffrau für büromanagement|"
     r"empfang|sachbearbeit|bürokauf|teamassist", "714", "2"),
    (r"industriekaufm|industriekauff|kaufmännische r? mitarbeiter|kaufmännischer angestellter", "713", "2"),
    (r"projektmanag|project manag|projektleit|unternehmensberat|management consultant|strategy|strategie|"
     r"referent der geschäftsführung|operations manag|program manag|programmmanag|consultant|berater", "713", "4"),
    # media and communication
    (r"marketing|\bseo\b|\bsea\b|social media|content manag|brand manag|kampagnen|campaign|growth manag", "921", "3"),
    (r"public relations|\bpr\b|pressesprech|kommunikationsmanag|unternehmenskommunikation|communications manag", "922", "4"),
    (r"redakteur|journalist|editor|volontär", "924", "4"),
    (r"mediengestalt|grafikdesign|graphic design|\bux\b|\bui\b|designer|motion design", "232", "3"),
    (r"übersetzer|dolmetscher|translator|interpreter", "911", "4"),
    (r"volkswirt|ökonom|economist", "914", "4"),
    # security and cleaning
    (r"sicherheitsmitarbeit|sicherheitsdienst|security guard|wachmann|objektschutz|werkschutz|"
     r"fachkraft für arbeitssicherheit|brandschutz|arbeitssicherheit", "531", "2"),
    (r"reinigungskraft|gebäudereinig|reinigung|cleaner|raumpfleg", "541", "1"),
    (r"hauswirtschaft", "832", "2"),
]
_COMPILED_RULES = [(re.compile(p), code, level) for p, code, level in TITLE_RULES]

_DEGREE = re.compile(
    r"abgeschlossene[sn]? (?:\w+ )?(?:hochschul|fachhochschul|universitäts)?studium|\bmaster\b|\bdiplom\b|"
    r"promotion|\bphd\b|university degree|bachelor'?s degree|master'?s degree",
    re.I,
)
_LEVEL_TEXT = [
    ("4", re.compile(_DEGREE.pattern + r"|\bstudium\b", re.I)),
    ("3", re.compile(r"\bmeister\b|\btechniker\b|\bfachwirt\b|staatlich geprüfte", re.I)),
    ("2", re.compile(r"abgeschlossene (?:\w+ )?(?:berufs)?ausbildung|\bausbildung als\b|kaufmännische ausbildung", re.I)),
    ("1", re.compile(r"\bhelfer|hilfskraft|aushilfe|ungelernt|angelernt|quereinsteiger ohne|keine ausbildung erforderlich", re.I)),
]
_HELPER_TITLE = re.compile(r"helfer|hilfskraft|aushilfe|minijob|ungelernt|angelernt")
_SENIOR_TITLE = re.compile(r"\b(?:senior|lead|head of|leiter|leiterin|leitung|principal)\b")

# German Bundesland -> BA region label in the Engpassanalyse
BUNDESLAND_TO_BA_REGION = {
    "Baden-Württemberg": "Baden-Württemberg",
    "Bayern": "Bayern",
    "Berlin": "Brandenburg / Berlin",
    "Brandenburg": "Brandenburg / Berlin",
    "Bremen": "Niedersachsen / Bremen",
    "Niedersachsen": "Niedersachsen / Bremen",
    "Hamburg": "Schleswig-Holstein / Hamburg",
    "Schleswig-Holstein": "Schleswig-Holstein / Hamburg",
    "Hessen": "Hessen",
    "Mecklenburg-Vorpommern": "Mecklenburg-Vorpommern",
    "Nordrhein-Westfalen": "Nordrhein-Westfalen",
    "Rheinland-Pfalz": "Rheinland-Pfalz / Saarland",
    "Saarland": "Rheinland-Pfalz / Saarland",
    "Sachsen": "Sachsen",
    "Sachsen-Anhalt": "Sachsen-Anhalt",
    "Thüringen": "Thüringen",
}


@dataclass(frozen=True)
class BaRow:
    region: str
    kldb: str
    kldb_label: str
    level_code: str
    level: str
    days: int
    einstufung: str


@dataclass
class BaTable:
    national: dict[tuple[str, str], BaRow]
    national_any: dict[str, int]
    regional: dict[tuple[str, str, str], BaRow]
    labels: dict[str, str]
    overall_median: int
    year: str


@lru_cache(maxsize=1)
def load_table(path: str | None = None) -> BaTable:
    csv_path = Path(path or settings.baseline_csv)
    national: dict[tuple[str, str], BaRow] = {}
    regional: dict[tuple[str, str, str], BaRow] = {}
    by_group: dict[str, list[int]] = {}
    labels: dict[str, str] = {}
    year = ""
    if not csv_path.exists():
        return BaTable({}, {}, {}, {}, 71, "")
    with csv_path.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            year = r["year"] or year
            row = BaRow(r["region"], r["kldb"], r["kldb_label"], r["level_code"], r["level"],
                        int(r["vakanzzeit_median_days"]), r["einstufung"])
            if r["region"] == "Deutschland - Berufsgruppen":
                national[(row.kldb, row.level_code)] = row
                by_group.setdefault(row.kldb, []).append(row.days)
                labels[row.kldb] = row.kldb_label
            elif not r["region"].startswith("Deutschland"):
                regional[(row.region, row.kldb, row.level_code)] = row
    national_any = {k: int(statistics.median(v)) for k, v in by_group.items()}
    overall = int(statistics.median([r.days for r in national.values()])) if national else 71
    return BaTable(national, national_any, regional, labels, overall, year)


def classify(title: str, description: str = "", hint: str | None = None) -> tuple[str | None, str | None, str | None]:
    """Return (kldb group, requirement level code, matched pattern) for a job title.

    `hint` is an occupation name from the source (e.g. the BA's "hauptberuf"), tried when the title alone
    does not match any rule.
    """
    norm = normalize_title(title)
    kldb = level = matched = None
    for candidate in (norm, normalize_title(hint) if hint else ""):
        if not candidate:
            continue
        for pattern, code, default_level in _COMPILED_RULES:
            found = pattern.search(candidate)
            if found:
                kldb, level, matched = code, default_level, found.group(0)
                break
        if kldb:
            break
    text = f"{title}\n{description[:4000]}"
    if _HELPER_TITLE.search(norm):
        level = "1"
    elif kldb is None:
        level = next((code for code, pattern in _LEVEL_TEXT if pattern.search(text)), None)
    elif level == "3" and _DEGREE.search(text):
        level = "4"
    if _SENIOR_TITLE.search(norm) and level in {"2", "3"}:
        level = "3" if kldb in {"813x+821", "251", "263", "342", "293", "621"} else "4"
    return kldb, level, matched


def baseline_for(title: str, description: str = "", region: str | None = None, hint: str | None = None) -> Baseline:
    table = load_table()
    kldb, level, matched = classify(title, description, hint)
    base = Baseline(kldb=kldb, level_code=level, level=LEVELS.get(level or ""), matched_by=matched)
    if not table.national:
        base.note = "BA baseline table missing; run scripts/update_baselines.py."
        base.vakanzzeit_days = 71
        base.expected_days = max(MIN_EXPECTED_DAYS, 71 + LEAD_DAYS)
        return base
    row: BaRow | None = None
    ba_region = BUNDESLAND_TO_BA_REGION.get(region or "")
    if kldb and ba_region and level:
        row = table.regional.get((ba_region, kldb, level))
    if kldb and level and row is None:
        row = table.national.get((kldb, level))
    if row is not None:
        base.vakanzzeit_days = row.days
        base.kldb_label = row.kldb_label
        base.region = row.region
        base.shortage = row.einstufung
    elif kldb and kldb in table.national_any:
        base.vakanzzeit_days = table.national_any[kldb]
        base.kldb_label = table.labels.get(kldb)
        base.region = "Deutschland"
        base.note = "No BA value for this requirement level; median across levels used."
    else:
        base.vakanzzeit_days = table.overall_median
        base.region = "Deutschland"
        base.note = "Occupation not recognised; national median across occupations used."
    base.expected_days = max(MIN_EXPECTED_DAYS, base.vakanzzeit_days + LEAD_DAYS)
    return base


def empirical_tail(age_days: int, lifetimes: list[tuple[str, str | None, str]], now: datetime) -> float | None:
    """Share of comparable postings that stayed live at least as long (S(age)); None if too few.

    Live postings count as censored at their current age, which makes the
    estimate conservative (it can only overstate survival).
    """
    durations: list[int] = []
    for start, end, status in lifetimes:
        began = parse_datetime(start)
        finished = parse_datetime(end) if end else now
        if began is None or finished is None:
            continue
        durations.append(max(0, (finished - began).days))
    if len(durations) < 40:
        return None
    longer = sum(1 for d in durations if d >= age_days)
    return round(longer / len(durations), 3)
