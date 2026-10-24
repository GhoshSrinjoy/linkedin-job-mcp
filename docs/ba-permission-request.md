# Anfrage: Nutzung der Jobsuche-Schnittstelle der Bundesagentur für Arbeit für ein Forschungs- und Verbraucherschutzprojekt

**An:** Bundesagentur für Arbeit, Produktverantwortung Jobbörse / Datenschutz
**Kopie:** Institut für Arbeitsmarkt- und Berufsforschung (IAB), Forschungsdatenzentrum
**Von:** [Name, Organisation, Anschrift, E-Mail]
**Datum:** [Datum]

Sehr geehrte Damen und Herren,

wir entwickeln ein nicht-kommerzielles Analysewerkzeug („Ghost Job Radar“), das Stellenanzeigen ohne tatsächlich
besetzbare Stelle erkennbar machen soll. Gemeint sind Anzeigen, die nach der Besetzung weiterlaufen, reine
Bewerberpools oder Stellen, deren Besetzung bereits intern feststeht. Bewerberinnen und Bewerber sollen so ihren
Aufwand besser einschätzen können.

Ihre Nutzungsbedingungen (§2a Abs. 3, Stand 8. Juli 2026) untersagen den Einsatz von Robots und das automatisierte
Auslesen von Schnittstellen zur Datensammlung und -auswertung. Wir bitten deshalb um Ihre schriftliche Erlaubnis, die
Jobsuche-Schnittstelle in dem unten beschriebenen Umfang zu nutzen, oder um einen alternativen Datenzugang.

## Zweck

- Erkennen von Anzeigen, die deutlich länger online sind als die von Ihnen veröffentlichte Median-Vakanzzeit des
  jeweiligen Berufs (Engpassanalyse), sowie von Anzeigen, die nach dem Wegfall beim Arbeitgeber weiterlaufen.
- Ihre eigene Methodenbeschreibung zu den Medianvakanzzeiten (August 2026) weist auf Arbeitgeber hin, die Stellen
  „durchgehend laufen lassen“. Unser Projekt soll dieses Phänomen messbar machen und die Ergebnisse dem IAB zur
  Verfügung stellen.

## Gewünschter Umfang

| Punkt | Vorschlag |
| --- | --- |
| Endpunkte | Stellensuche (`/pc/v6/jobs`) und Stellendetails (`/pc/v4/jobdetails/{refnr}`) |
| Abfragen | höchstens [5.000] Anfragen pro Tag, höchstens 1 Anfrage pro Sekunde, Zwischenspeicherung jeder Antwort für mindestens 3 Stunden |
| Kennung | eindeutiger User-Agent mit Kontaktadresse |
| Gespeicherte Daten | Referenznummer, Titel, Arbeitgebername, Ort, Veröffentlichungs- und Änderungsdatum, Eintrittsdatum, Angaben zu Arbeitszeit und Vergütung, Beschreibungstext |
| Nicht gespeichert | Namen, E-Mail-Adressen und Telefonnummern von Ansprechpersonen (werden beim Eingang automatisch entfernt) |
| Veröffentlichung | keine Wiedergabe von Anzeigentexten; nur aggregierte Kennzahlen nach Beruf, Region und Zeitraum sowie die Einzelbewertung für die Person, die eine Anzeige selbst prüft |
| Löschung | Rohdaten nach Abschluss der Auswertung, spätestens nach [12] Monaten |

## Unsere Zusagen

- Wir umgehen keine technischen Schutzmaßnahmen und halten von Ihnen vorgegebene Abruflimits ein.
- Wir weisen die Bundesagentur bei jeder Veröffentlichung als Quelle aus („© Statistik der Bundesagentur für Arbeit“
  für statistische Daten).
- Wir stellen dem IAB unsere Methode und unsere aggregierten Ergebnisse zur Verfügung, auf Wunsch vor der
  Veröffentlichung.

## Alternativen, falls eine Freigabe nicht möglich ist

1. Zugang zu Daten über gemeldete Arbeitsstellen über das Forschungsdatenzentrum des IAB, zum Beispiel
   Abmeldegründe und Laufzeiten nach Beruf und Region.
2. Eine Kooperation mit dem IAB, in der die Stellenerhebung als Prüfmaßstab dient (Frage an Betriebe, ob eine
   ausgeschriebene Stelle aktiv besetzt werden soll).

Für Rückfragen und ein Gespräch stehen wir gern zur Verfügung.

Mit freundlichen Grüßen

[Name]
[Funktion, Organisation]
[Telefon, E-Mail]
