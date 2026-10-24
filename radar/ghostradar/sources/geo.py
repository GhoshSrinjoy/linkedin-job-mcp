"""City coordinates and Bundesland lookup (approximate city centres) with an optional Nominatim fallback."""
from __future__ import annotations

import re
import unicodedata

from .. import db
from ..config import settings
from ..http import FetchError, PoliteClient

# name: (lat, lon, Bundesland). City centres, rounded; good enough for map markers.
CITIES: dict[str, tuple[float, float, str]] = {
    "berlin": (52.520, 13.405, "Berlin"),
    "hamburg": (53.551, 9.994, "Hamburg"),
    "münchen": (48.137, 11.575, "Bayern"),
    "köln": (50.938, 6.960, "Nordrhein-Westfalen"),
    "frankfurt am main": (50.110, 8.682, "Hessen"),
    "stuttgart": (48.776, 9.183, "Baden-Württemberg"),
    "düsseldorf": (51.227, 6.774, "Nordrhein-Westfalen"),
    "leipzig": (51.340, 12.375, "Sachsen"),
    "dortmund": (51.514, 7.468, "Nordrhein-Westfalen"),
    "essen": (51.456, 7.012, "Nordrhein-Westfalen"),
    "bremen": (53.079, 8.802, "Bremen"),
    "dresden": (51.050, 13.738, "Sachsen"),
    "hannover": (52.376, 9.732, "Niedersachsen"),
    "nürnberg": (49.452, 11.077, "Bayern"),
    "duisburg": (51.435, 6.763, "Nordrhein-Westfalen"),
    "bochum": (51.482, 7.216, "Nordrhein-Westfalen"),
    "wuppertal": (51.256, 7.150, "Nordrhein-Westfalen"),
    "bielefeld": (52.030, 8.532, "Nordrhein-Westfalen"),
    "bonn": (50.737, 7.098, "Nordrhein-Westfalen"),
    "münster": (51.961, 7.626, "Nordrhein-Westfalen"),
    "mannheim": (49.487, 8.466, "Baden-Württemberg"),
    "karlsruhe": (49.007, 8.404, "Baden-Württemberg"),
    "augsburg": (48.371, 10.898, "Bayern"),
    "wiesbaden": (50.078, 8.240, "Hessen"),
    "mönchengladbach": (51.180, 6.443, "Nordrhein-Westfalen"),
    "gelsenkirchen": (51.517, 7.086, "Nordrhein-Westfalen"),
    "aachen": (50.776, 6.084, "Nordrhein-Westfalen"),
    "braunschweig": (52.269, 10.521, "Niedersachsen"),
    "kiel": (54.323, 10.123, "Schleswig-Holstein"),
    "chemnitz": (50.828, 12.921, "Sachsen"),
    "halle": (51.483, 11.970, "Sachsen-Anhalt"),
    "magdeburg": (52.120, 11.628, "Sachsen-Anhalt"),
    "freiburg": (47.999, 7.842, "Baden-Württemberg"),
    "krefeld": (51.339, 6.586, "Nordrhein-Westfalen"),
    "mainz": (49.993, 8.247, "Rheinland-Pfalz"),
    "lübeck": (53.866, 10.687, "Schleswig-Holstein"),
    "erfurt": (50.978, 11.029, "Thüringen"),
    "oberhausen": (51.497, 6.863, "Nordrhein-Westfalen"),
    "rostock": (54.092, 12.099, "Mecklenburg-Vorpommern"),
    "kassel": (51.312, 9.479, "Hessen"),
    "hagen": (51.367, 7.463, "Nordrhein-Westfalen"),
    "potsdam": (52.391, 13.064, "Brandenburg"),
    "saarbrücken": (49.240, 6.997, "Saarland"),
    "hamm": (51.681, 7.817, "Nordrhein-Westfalen"),
    "ludwigshafen": (49.477, 8.445, "Rheinland-Pfalz"),
    "oldenburg": (53.144, 8.214, "Niedersachsen"),
    "mülheim an der ruhr": (51.427, 6.883, "Nordrhein-Westfalen"),
    "osnabrück": (52.279, 8.047, "Niedersachsen"),
    "leverkusen": (51.046, 6.984, "Nordrhein-Westfalen"),
    "darmstadt": (49.873, 8.651, "Hessen"),
    "heidelberg": (49.398, 8.672, "Baden-Württemberg"),
    "solingen": (51.171, 7.083, "Nordrhein-Westfalen"),
    "regensburg": (49.013, 12.101, "Bayern"),
    "herne": (51.538, 7.219, "Nordrhein-Westfalen"),
    "paderborn": (51.718, 8.757, "Nordrhein-Westfalen"),
    "neuss": (51.204, 6.687, "Nordrhein-Westfalen"),
    "ingolstadt": (48.766, 11.426, "Bayern"),
    "offenbach am main": (50.096, 8.766, "Hessen"),
    "fürth": (49.477, 10.989, "Bayern"),
    "würzburg": (49.792, 9.953, "Bayern"),
    "ulm": (48.401, 9.988, "Baden-Württemberg"),
    "heilbronn": (49.142, 9.219, "Baden-Württemberg"),
    "pforzheim": (48.892, 8.694, "Baden-Württemberg"),
    "wolfsburg": (52.423, 10.787, "Niedersachsen"),
    "göttingen": (51.541, 9.916, "Niedersachsen"),
    "bottrop": (51.524, 6.929, "Nordrhein-Westfalen"),
    "reutlingen": (48.491, 9.211, "Baden-Württemberg"),
    "koblenz": (50.356, 7.594, "Rheinland-Pfalz"),
    "bremerhaven": (53.540, 8.581, "Bremen"),
    "erlangen": (49.590, 11.004, "Bayern"),
    "bergisch gladbach": (50.992, 7.136, "Nordrhein-Westfalen"),
    "trier": (49.750, 6.637, "Rheinland-Pfalz"),
    "jena": (50.927, 11.589, "Thüringen"),
    "remscheid": (51.179, 7.189, "Nordrhein-Westfalen"),
    "siegen": (50.875, 8.024, "Nordrhein-Westfalen"),
    "hildesheim": (52.154, 9.957, "Niedersachsen"),
    "gütersloh": (51.906, 8.378, "Nordrhein-Westfalen"),
    "cottbus": (51.756, 14.333, "Brandenburg"),
    "kaiserslautern": (49.444, 7.769, "Rheinland-Pfalz"),
    "schwerin": (53.636, 11.401, "Mecklenburg-Vorpommern"),
    "walldorf": (49.306, 8.642, "Baden-Württemberg"),
    "garching": (48.249, 11.651, "Bayern"),
    "eschborn": (50.143, 8.570, "Hessen"),
    "unterföhring": (48.192, 11.643, "Bayern"),
    "böblingen": (48.686, 9.015, "Baden-Württemberg"),
    "sindelfingen": (48.713, 9.003, "Baden-Württemberg"),
    "konstanz": (47.660, 9.175, "Baden-Württemberg"),
    "flensburg": (54.784, 9.437, "Schleswig-Holstein"),
    "lüneburg": (53.248, 10.407, "Niedersachsen"),
    "bamberg": (49.898, 10.902, "Bayern"),
    "bayreuth": (49.946, 11.578, "Bayern"),
    "passau": (48.574, 13.461, "Bayern"),
    "landshut": (48.537, 12.152, "Bayern"),
    "rosenheim": (47.856, 12.128, "Bayern"),
    "gießen": (50.584, 8.678, "Hessen"),
    "marburg": (50.810, 8.771, "Hessen"),
    "fulda": (50.555, 9.680, "Hessen"),
    "zwickau": (50.719, 12.496, "Sachsen"),
    "weimar": (50.980, 11.329, "Thüringen"),
    "greifswald": (54.093, 13.388, "Mecklenburg-Vorpommern"),
    "frankfurt (oder)": (52.347, 14.550, "Brandenburg"),
    "wilhelmshaven": (53.530, 8.110, "Niedersachsen"),
    "salzgitter": (52.150, 10.333, "Niedersachsen"),
    "moers": (51.451, 6.627, "Nordrhein-Westfalen"),
    "witten": (51.444, 7.335, "Nordrhein-Westfalen"),
    "iserlohn": (51.376, 7.700, "Nordrhein-Westfalen"),
    "tübingen": (48.521, 9.057, "Baden-Württemberg"),
    "esslingen am neckar": (48.742, 9.307, "Baden-Württemberg"),
    "ludwigsburg": (48.897, 9.192, "Baden-Württemberg"),
    "friedrichshafen": (47.655, 9.475, "Baden-Württemberg"),
    "neu-ulm": (48.392, 10.011, "Bayern"),
}

ALIASES = {
    "munich": "münchen", "muenchen": "münchen", "munchen": "münchen",
    "cologne": "köln", "koeln": "köln", "koln": "köln",
    "frankfurt": "frankfurt am main", "frankfurt a.m.": "frankfurt am main", "frankfurt/main": "frankfurt am main",
    "frankfurt a. m.": "frankfurt am main", "frankfurt main": "frankfurt am main",
    "nuremberg": "nürnberg", "nuernberg": "nürnberg", "nurnberg": "nürnberg",
    "dusseldorf": "düsseldorf", "duesseldorf": "düsseldorf",
    "hanover": "hannover", "brunswick": "braunschweig",
    "halle (saale)": "halle", "halle/saale": "halle", "freiburg im breisgau": "freiburg",
    "saarbruecken": "saarbrücken", "muenster": "münster", "munster": "münster",
    "luebeck": "lübeck", "wuerzburg": "würzburg", "goettingen": "göttingen", "guetersloh": "gütersloh",
    "osnabrueck": "osnabrück", "fuerth": "fürth", "moenchengladbach": "mönchengladbach",
    "offenbach": "offenbach am main", "mülheim": "mülheim an der ruhr", "muelheim": "mülheim an der ruhr",
    "esslingen": "esslingen am neckar", "ludwigshafen am rhein": "ludwigshafen",
}

STATES = {
    "baden-württemberg", "bayern", "berlin", "brandenburg", "bremen", "hamburg", "hessen", "mecklenburg-vorpommern",
    "niedersachsen", "nordrhein-westfalen", "rheinland-pfalz", "saarland", "sachsen", "sachsen-anhalt",
    "schleswig-holstein", "thüringen",
}


FOREIGN = re.compile(
    r"\b(?:barcelona|madrid|lisbon|lisboa|porto|paris|lyon|london|manchester|dublin|amsterdam|rotterdam|brussels|"
    r"bruxelles|vienna|wien|graz|linz|salzburg|zurich|zürich|zuerich|geneva|genf|basel|bern|lausanne|milan|milano|"
    r"rome|roma|warsaw|warszawa|krakow|kraków|wroclaw|prague|praha|brno|budapest|bucharest|sofia|athens|stockholm|"
    r"copenhagen|københavn|oslo|helsinki|tallinn|riga|vilnius|luxembourg|new york|san francisco|boston|toronto|"
    r"montreal|bangalore|bengaluru|mumbai|singapore|dubai|tel aviv|sydney|"
    r"spain|españa|france|united kingdom|\buk\b|ireland|netherlands|belgium|austria|österreich|switzerland|schweiz|"
    r"italy|poland|polen|czech|portugal|sweden|denmark|norway|finland|estonia|usa|united states|canada|india)\b",
    re.I,
)


# LinkedIn writes US and Canadian places as "City, ST" (DE is left out: "Berlin, DE" means Germany)
STATE_CODE = re.compile(
    r",\s*(?:AL|AK|AZ|AR|CA|CO|CT|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|"
    r"OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC|ON|QC|BC|AB|MB|NS)\s*$"
)


def outside_germany(location: str | None) -> bool:
    """True when a location clearly names a place outside Germany (and no German city)."""
    if not location:
        return False
    if STATE_CODE.search(location):
        return True  # "Hamburg, NY" is not Hamburg
    if lookup(location):
        return False
    if re.search(r"\b(?:germany|deutschland)\b", location, re.I):
        return False
    return bool(FOREIGN.search(location))


def _key(name: str) -> str:
    text = unicodedata.normalize("NFKC", name).lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r",?\s*(?:germany|deutschland|de)$", "", text).strip(" ,")
    return ALIASES.get(text, text)


def lookup(name: str | None) -> tuple[float, float, str] | None:
    if not name:
        return None
    key = _key(name)
    if key in CITIES:
        return CITIES[key]
    first = _key(re.split(r"[,/;(]| - ", name)[0])
    return CITIES.get(first)


_SMALL_WORDS = {"am", "an", "der", "im", "(oder)", "(saale)"}


def _display(key: str) -> str:
    words = []
    for word in key.split(" "):
        if word in _SMALL_WORDS:
            words.append(word)
        else:
            words.append("-".join(part[:1].upper() + part[1:] for part in word.split("-")))
    return " ".join(words)


def city_name(name: str | None) -> str | None:
    """Canonical city name if known (e.g. 'Munich' -> 'München')."""
    if not name:
        return None
    for candidate in (_key(name), _key(re.split(r"[,/;(]| - ", name)[0])):
        if candidate in CITIES:
            return _display(candidate)
    return None


def matches_city(location: str | None, city: str) -> bool:
    if not location:
        return False
    target = _key(city)
    loc = location.lower()
    names = {target} | {alias for alias, canon in ALIASES.items() if canon == target}
    return any(re.search(r"(?<![a-zäöüß])" + re.escape(n) + r"(?![a-zäöüß])", loc) for n in names)


async def geocode(client: PoliteClient, name: str) -> tuple[float, float, str | None] | None:
    """OSM Nominatim lookup with a permanent local cache (its policy requires caching, 1 req/s)."""
    known = lookup(name)
    if known:
        return known
    cached = db.geocode_get(name)
    if cached:
        return (cached["lat"], cached["lon"], cached["region"]) if cached["lat"] is not None else None
    if not settings.nominatim_enabled:
        return None
    try:
        resp = await client.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": name, "countrycodes": "de", "format": "json", "limit": 1, "addressdetails": 1},
            ttl=30 * 24 * 3600,
            check_robots=False,  # API use under the Nominatim usage policy (1 req/s, cached, identified)
        )
    except FetchError:
        return None
    if not resp.ok:
        return None
    hits = resp.json()
    if not hits:
        db.geocode_put(name, None, None, None)
        return None
    hit = hits[0]
    region = (hit.get("address") or {}).get("state")
    lat, lon = float(hit["lat"]), float(hit["lon"])
    db.geocode_put(name, lat, lon, region)
    return lat, lon, region
