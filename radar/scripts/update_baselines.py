"""Download the BA Engpassanalyse data and write the vacancy-duration baseline table.

Source: Statistik der Bundesagentur für Arbeit, Engpassanalyse (the same JSON the
interactive page at statistik.arbeitsagentur.de uses for its "Gesamtdownload").
Reuse is allowed with attribution ("© Statistik der Bundesagentur für Arbeit");
own calculations must be labelled as such.

Usage:  python scripts/update_baselines.py
Writes: data/ba_engpass.csv
"""
from __future__ import annotations

import csv
import json
import sys
import urllib.request
from pathlib import Path

SOURCE_URL = (
    "https://statistik.arbeitsagentur.de/DE/Statischer-Content/Statistiken/"
    "Interaktive-Statistiken/Generische-Publikationen/epaliste.asc?__blob=publicationFile"
)
OUT = Path(__file__).resolve().parent.parent / "data" / "ba_engpass.csv"
USER_AGENT = "GhostJobRadar/0.1 (baseline download; local research tool)"

COLUMNS = [
    "year",
    "region_code",
    "region",
    "kldb",
    "kldb_label",
    "level_code",
    "level",
    "vakanzzeit_median_days",
    "einstufung",
    "gesamtbewertung",
    "arbeitsuchende_je_stelle",
]


def fetch(url: str) -> list[dict]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8-sig")
    return json.loads(raw)


def to_float(value: str) -> str:
    """BA files use German decimal commas; store dot decimals."""
    value = (value or "").strip()
    return value.replace(".", "").replace(",", ".") if value else ""


def main() -> int:
    rows = fetch(SOURCE_URL)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        for r in rows:
            vakanz = (r.get("Vakanzzeit") or "").strip()
            if not vakanz.isdigit():
                continue
            writer.writerow(
                {
                    "year": r.get("Jahr.DESC", ""),
                    "region_code": r.get("Bundesland RZ.BA_SCHL", ""),
                    "region": r.get("Bundesland RZ.DESC", ""),
                    "kldb": r.get("Beruf.BA_SCHL", ""),
                    "kldb_label": r.get("Beruf.DESC", ""),
                    "level_code": r.get("Anforderungsniveau.BA_SCHL", ""),
                    "level": r.get("Anforderungsniveau.DESC", ""),
                    "vakanzzeit_median_days": vakanz,
                    "einstufung": r.get("Einstufung", ""),
                    "gesamtbewertung": to_float(r.get("Gesamtbewertung", "")),
                    "arbeitsuchende_je_stelle": to_float(r.get("Arbeitsuchenden-Stellen-Relation", "")),
                }
            )
            written += 1
    print(f"wrote {written} rows to {OUT}")
    return 0 if written else 1


if __name__ == "__main__":
    sys.exit(main())
