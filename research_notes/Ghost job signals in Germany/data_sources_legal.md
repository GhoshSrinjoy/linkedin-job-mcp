# Data sources, access methods and legal constraints for a German ghost-job monitoring pipeline and public dashboard (research notes, status 2026-10-24)

Conventions used throughout these notes:
- Feature codes: **F1** posting age and reposts; **F2** posting on the company's own careers site vs only on aggregators; **F3** gap between posting date and start date; **F4** salary stated; **F5** staffing-agency flag; **F6** employer posting volume vs headcount; **F7** funding, layoffs and insolvency; **F8** reviews of the application experience.
- "Accessed" dates are 2026-10-24 unless stated otherwise. Legal points are research, not legal advice; items marked "lawyer review" need a German IT/media lawyer.
- Method note: the shared web-search budget for this research session ran out partway through.
  - Sections 3 (ATS feeds), 6 (company data) and 7 (law on collecting) incorporate the reports of parallel research agents that fetched primary portals, statutes, court databases, vendor docs and live public feeds on 2026-10-24.
  - The agent assigned to job boards and schema.org had not returned at handback. Sections 4–5 therefore rest only on primary pages fetched directly (official docs, live public feeds, robots.txt).
  - **Sections 1, 2, 3, 6, 7 and 8 are substantially complete; Sections 4–5 are partial.** Unverified recollections appear only in Gaps and are labelled as such.

## 1. Bundesagentur für Arbeit (BA) Jobsuche API: endpoints, authentication, parameters, fields, jobdetails, volumes, limits and legal status

### Takeaway
The BA offers **no official public API**. The "Jobsuche API" is the undocumented backend of the BA Jobbörse web site and app, documented by the community project bundesAPI. On 2026-10-24 it still answered with a static key: v6 search returned HTTP 200, v4 jobdetails returned HTTP 200, and v4 search returned 403. It holds about **1.02 million postings**, with first-publication date, modification timestamp, start date, salary-type, temp-agency (`zeitarbeit`), private-placement (`pav`) and partner-board flags, so it is technically the richest single source for F1, F3, F4 and F5.

Two cautions apply. First, the **schema changed in 2026**: most of the field names in the community docs (refnr, titel, arbeitgeber, aktuelleVeroeffentlichungsdatum, modifikationsTimestamp, arbeitsort) are now renamed. Second, the BA's own **Nutzungsbedingungen (Stand 08.07.2026) explicitly forbid robots and web spiders and the reading out of interfaces for data collection**. That makes the BA the source with the clearest contractual prohibition. Written permission from the BA, or a research cooperation, should be sought before any systematic collection (lawyer review).

### Cited Findings
**Access and authentication**
- The BA does not offer an official API; the bundesAPI repo documents the Jobbörse backend as unofficial — [bundesAPI/jobsuche-api README](https://github.com/bundesAPI/jobsuche-api)
- Base URL `https://rest.arbeitsagentur.de/jobboerse/jobsuche-service`; logo service at `https://rest.arbeitsagentur.de/vermittlung/ag-darstellung-service`. Authentication is a static client ID sent as header `X-API-Key: jobboerse-jobsuche`; no OAuth (OpenAPI spec version 2.1.0) — [bundesAPI openapi.yaml](https://raw.githubusercontent.com/bundesAPI/jobsuche-api/main/openapi.yaml)
- Documented endpoints: `GET /pc/v6/jobs` (search), `GET /pc/v4/app/jobs` (app search), `GET /pc/v4/jobdetails/{encryptedJobCode}` (recommended) and `GET /pc/v3/jobdetails/{encryptedJobCode}`, and `GET /ct/v1/arbeitgeberlogo/{kundennummerHash}` (returns 404 when no logo exists) — [openapi.yaml](https://raw.githubusercontent.com/bundesAPI/jobsuche-api/main/openapi.yaml)
- `encryptedJobCode` is the Base64-encoded reference number, e.g. `10001-1002716922-S` → `MTAwMDEtMTAwMjcxNjkyMi1T` — [README](https://github.com/bundesAPI/jobsuche-api)

**Query parameters**
- `was` (free-text job title), `wo` (location), `berufsfeld`, `page` (from 1), `size`, `arbeitgeber` (employer name), `veroeffentlichtseit` (days since publication, 0–100), `zeitarbeit` (boolean, **default true**, i.e. temp-agency jobs included unless excluded), `pav` (boolean, include private placement agencies), `angebotsart` (1 ARBEIT, 2 SELBSTAENDIGKEIT, 4 AUSBILDUNG/Duales Studium, 34 Praktikum/Trainee), `befristung` (1 befristet, 2 unbefristet; multiple values `;`-separated), `arbeitszeit` (vz, tz, snw, ho, mj; `;`-separated), `behinderung`, `corona`, `umkreis` (km) — [README](https://github.com/bundesAPI/jobsuche-api); [openapi.yaml](https://raw.githubusercontent.com/bundesAPI/jobsuche-api/main/openapi.yaml)
- The Rust client `jobsuche` 0.4.0 (published 2026-09-20) reports that employer search is case-sensitive and exact-match only, and that **results are sorted oldest to newest and the sort cannot be changed** — [docs.rs/jobsuche](https://docs.rs/jobsuche)

**Response fields as documented (pre-2026 naming)**
- Search items: `hashId`, `beruf`, `refnr`, `arbeitgeber`, `aktuelleVeroeffentlichungsdatum`, `eintrittsdatum`, `arbeitsort` (plz, ort, strasse, region, land, koordinaten), `kundennummerHash` (nullable), `externeUrl` (nullable), `modifikationsTimestamp`; envelope `maxErgebnisse`, `page`, `size`, `facetten` — [openapi.yaml](https://raw.githubusercontent.com/bundesAPI/jobsuche-api/main/openapi.yaml)
- Jobdetails: `aktuelleVeroeffentlichungsdatum`, `ersteVeroeffentlichungsdatum`, `eintrittsdatum`, `modifikationsTimestamp`, `angebotsart`, `branche`, `beruf`, `befristung`, `arbeitszeitmodelle`, `betriebsgroesse`, `titel`, `stellenbeschreibung`, `refnr`, `arbeitgeber`, `arbeitgeberAdresse`, `arbeitgeberdarstellung(Url)`, `allianzpartner(Url)`, `verguetung`, `fertigkeiten`, `uebernahme`, `istBetreut`, `istGoogleJobsRelevant`, `anzeigeAnonym`, `anzahlOffeneStellen` — [openapi.yaml](https://raw.githubusercontent.com/bundesAPI/jobsuche-api/main/openapi.yaml)

**2026 schema change (verified)**
- GitHub issue #69 (opened 2026-08-08, no maintainer reply): v6 search returns `ergebnisliste` instead of `stellenangebote`. Renamed fields: `refnr`→`referenznummer`, `titel`→`stellenangebotsTitel`, `arbeitgeber`→`firma`, `aktuelleVeroeffentlichungsdatum`→`datumErsteVeroeffentlichung`, `arbeitsort`→`stellenlokationen`, `modifikationsTimestamp`→`aenderungsdatum`. v4 jobdetails has the same renames, plus `stellenbeschreibung`→`stellenangebotsBeschreibung` — [issue #69](https://github.com/bundesAPI/jobsuche-api/issues/69)
- Own verification on 2026-10-24 at 08:04 UTC, one request per endpoint, header `X-API-Key: jobboerse-jobsuche`:
  - `/pc/v4/jobs` returned **HTTP 403**.
  - `/pc/v6/jobs?size=1&page=1` returned HTTP 200 with item fields `stellenangebotsart`, `stellenangebotsTitel`, six `arbeitszeit*` booleans, `eintrittszeitraum{von}`, `verguetungsangabe` (e.g. `KEINE_ANGABEN`), `vertragsdauer`, `stellenlokationen[{adresse{strasse,hausnummer,plz,ort,ortsteil,region,land}, breite, laenge}]`, `veroeffentlichungszeitraum{von}`, `datumErsteVeroeffentlichung` (date), `aenderungsdatum` (timestamp, e.g. `2026-10-24T10:03:08.380`), `hauptberuf`, `alleBerufe`, `firma`, `arbeitgeberKundennummerHash`, `referenznummer`.
  - Source: [BA Jobsuche v6 search response, queried 2026-10-24](https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs?size=1&page=1)
- Same check: `/pc/v4/jobdetails/{base64(referenznummer)}` returned HTTP 200 with the same field names plus `stellenangebotsBeschreibung`, `istBetreut`, `allianzpartnerName` and `allianzpartnerUrl`. The sampled BA-native ad showed `allianzpartnerName = arbeitsagentur.de`. No employer contact fields were returned — [BA jobdetails v4 response, queried 2026-10-24](https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobdetails/MTAwMDEtMTAwMzkwNzcxOC1T)

**Volumes: snapshot of the facet counts, 2026-10-24, whole Jobbörse, no filters**
- `maxErgebnisse` = **1,024,646** postings — [v6 response](https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs?size=1&page=1)
- `zeitarbeit=true` 214,947 (≈21%); `pav=true` 85,802 (≈8.4%); `externestellenboersen=true` 201,336 (≈19.6%, ads that came from external partner job boards) — [v6 response](https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs?size=1&page=1)
- Salary facet `verguetung`: `jahr` 66,098 + `stunde` 154,664 (≈21.6% of postings carry a structured annual or hourly pay figure); `ausbildungsverguetung` `monat` 22,464 — [v6 response](https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs?size=1&page=1)
- `veroeffentlichtseit` facet (cumulative): 0 days 2,459; ≤1 day 19,845; ≤7 days 97,164; ≤14 days 186,281; ≤28 days 362,492. So only ≈35% of the stock was published in the last 4 weeks — [v6 response](https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs?size=1&page=1)
- `eintrittsdatum` facet: 801,720 postings (≈78%) fall in the bucket "2010-01-01 to now" (start date today or in the past); 569,571 in October 2026; 91,533 in Aug–Sep 2027 (mostly apprenticeships) — [v6 response](https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs?size=1&page=1)
- `angebotsart`: 1 (work) 821,269; 4 (apprenticeship/dual study) 184,651; 34 (internship) 14,430; 2 (self-employment) 4,296. `befristung`: 1 = 33,045; 2 = 543,440; 3 = 448,161 (bucket 3 is undocumented, probably "no information") — [v6 response](https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs?size=1&page=1)
- Top employers by posting count: Netto Marken-Discount 25,482; Lidl 14,530; TimePartner Personalmanagement (staffing) 13,388; Randstad 9,621; Sanovetis 9,434; PerZukunft Arbeitsvermittlung 7,703; TEDi 6,321; ALDI SÜD 5,978; Deutsche Bahn 4,115 — [v6 response](https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs?size=1&page=1)

**Limits and reliability**
- Community reports conflict on paging:
  - maximum `size` 100 per page (issue #23, March 2022) and a cap of 100 pages (issue #14, December 2021)
  - October 2025: a related client committed "fix: correct pagination limit from 1000 to 100 pages"
  - March 2026: a user reported null/empty results "around page 1000" while `maxErgebnisse` still showed more
  - Sources: [issue #14](https://github.com/bundesAPI/jobsuche-api/issues/14); [issues list](https://github.com/bundesAPI/jobsuche-api/issues)
- The client library handles HTTP 429 using `Retry-After` and reports sporadic 403 blocks. Jobdetails can return 404 for jobs still in search results "since listings expire quickly" — [docs.rs/jobsuche](https://docs.rs/jobsuche)
- Recurring breakages reported as GitHub issues:
  - jobdetails 404 or not working: #46 (Nov 2023), #57 (Oct 2024), #59 (Feb 2025: search returned no hashes), #61 (Jun 2025)
  - "403 Forbidden": #60 (Mar 2025)
  - Source: [issues list](https://github.com/bundesAPI/jobsuche-api/issues)
- Contact details for "a significant number of offers" are protected by captcha on the BA platform and are not available through the API (issue #68, opened 2026-06-02) — [issue #68](https://github.com/bundesAPI/jobsuche-api/issues/68)
- ATS vendors such as JOIN push postings into the BA Jobbörse through a sanctioned integration, so BA postings are partly syndicated from ATSs — [JOIN blog](https://join.com/de/recruitment-hr-blog/ats-integration-bundesagentur-fuer-arbeit)

**Legal status: BA terms of use**
- Nutzungsbedingungen arbeitsagentur.de, "Stand 08.07.2026" (earlier change-log entries 13.04.2026, 29.04.2025, 19.07.2024):
  - §2a applies to all users and visitors, not only registered accounts.
  - §2a(3) prohibits activities not serving the portal's intended use that can burden the infrastructure, the use of "Robots, Webspider oder ähnliche Technologien", the use of interfaces contrary to their purpose, e.g. reading out content "zum Zweck der Datensammlung und -auswertung", and attempts to circumvent security measures.
  - Source: [BA Nutzungsbedingungen](https://www.arbeitsagentur.de/nutzungsbedingungen)
- Further clauses in the same terms:
  - §3(1): copyright in the portal, its structure and content "liegt in seiner Gesamtheit bei der BA".
  - §4: the BA may block access temporarily or permanently and reserves damages claims.
  - §6d(4): companies that downloaded or stored offers must delete them after the recruitment procedure ends.
  - §6d(5): private placement agencies and temp-work firms may not use the portal to build their own job or applicant pools.
  - Source: [BA Nutzungsbedingungen](https://www.arbeitsagentur.de/nutzungsbedingungen)

### Inferences
- **Field mapping for features (current v6 names).**
  - F1: `datumErsteVeroeffentlichung` + `veroeffentlichungszeitraum.von` + `aenderungsdatum`. Reposts under a new `referenznummer` must be matched fuzzily on `firma` + `stellenangebotsTitel` + `stellenlokationen` + `arbeitgeberKundennummerHash`.
  - F3: `eintrittszeitraum.von` minus first publication.
  - F4: `verguetungsangabe` / `verguetung` facet.
  - F5: `zeitarbeit` and `pav` filters; run queries with `zeitarbeit=false` vs default to label postings.
  - F2: partial, via `externestellenboersen` facet and `allianzpartnerName/Url`. This shows only whether the BA copy came from a partner board; it says nothing about the employer's own careers site.
  - F6: `arbeitgeberKundennummerHash` as a stable employer key for posting-volume counts.
- **F3 caution.** About 78% of postings have a start date of "today or earlier", and the sampled new ad had `eintrittszeitraum.von` equal to its publication date. "Ab sofort" vacancies are therefore probably encoded as the publication date or a rolling date. F3 should only use postings with an explicit future start date, and the semantics should be validated on longitudinal snapshots.
- **Posting age at scale.** About 65% of the stock is older than 28 days. Posting age therefore needs occupation-specific baselines (see Section 2) to be meaningful, and very high-volume multi-branch employers (retail chains, staffing firms) dominate raw counts. F6 must normalise for multi-location postings.
- **Feasibility.** Results are sorted oldest-first with a page cap, so a complete daily census of about 1M postings would require partitioned queries (e.g. by `veroeffentlichtseit`, PLZ/`umkreis`, `berufsfeld`, `arbeitgeber`) plus about 1M detail calls. That is exactly the "Datensammlung und -auswertung" that §2a(3) of the terms forbids, and the 403s show the BA can and does block clients.
- **Legal position (lawyer review).** The prohibition is explicit and covers visitors, which weakens any "no contract was formed" argument. How the BA terms classify (public-law Benutzungsordnung vs private AGB) and whether they can be enforced against API users is unclear. Separately, database-right and TDM questions arise (see Section 7).
  - The lowest-risk routes are (a) written permission from the BA or a research cooperation (e.g. via the IAB), (b) using BA aggregate statistics (Section 2), or (c) restricting collection to small, rate-limited samples for methodology validation, without storing personal or contact data.
- **Schema dependency.** Building on the bundesAPI documentation alone would currently break: the field names in the request brief are the pre-2026 names. The pipeline needs schema-drift monitoring.

### Gaps
- No official BA statement was found on whether it tolerates third-party use of the Jobbörse backend, or on any official data-access programme for third parties (search budget exhausted before this could be pursued).
- Not confirmed:
  - whether `veroeffentlichungszeitraum` also carries a `bis` (valid-through) value (absent in the sampled record)
  - whether `datumErsteVeroeffentlichung` is truly the first publication date or the current one (issue #69 maps it from `aktuelleVeroeffentlichungsdatum`)
  - what `befristung` bucket 3 means
- Unresolved: whether the effective paging cap is 100 or about 1,000 pages, and the current maximum `size`.
- Not settled: whether the Jobbörse database is protected by the sui generis right (§87a UrhG). OLG Köln (27.02.2026, 6 U 75/25) held that public funding does not exclude §87a protection (Section 7). Whether §5 UrhG (amtliche Werke) could apply to a public body's database was not verified.

## 2. BA statistics data as baselines (Statistik API, Engpassanalyse, Vakanzzeit, BA-X, IAB-Stellenerhebung)

### Takeaway
BA statistics are free to reuse with attribution and contain no company names, so the legal risk is low. Since December 2025 there is a **pilot Statistik API**, which so far covers only key figures ("Eckwerte") such as the stock and inflow of registered vacancies by region. The most useful ghost-job baseline is the **Engpassanalyse 2025**: six indicators per KldB-2010 occupation, including the **median completed vacancy duration (Vakanzzeit)**, with a CSV bulk download. The monthly **BA-X** index and the quarterly **IAB-Stellenerhebung** (all vacancies, including those not reported to the BA) give macro baselines for "posting inflation".

### Cited Findings
- Since December 2025 BA Statistik offers automated data transfer by API. The pilot covers the interactive "Aktuelle Eckwerte"; dashboards, databases and interactive tables are planned to follow — [BA Statistik API overview](https://statistik.arbeitsagentur.de/DE/Navigation/Service/API/API-Start-Nav.html)
- Registered-vacancy endpoint (table `EckwerteTabelleSTEA`), e.g. `https://statistik-dr.arbeitsagentur.de/bifrontend/bids-api/ct/v1/tableFetch/csv/EckwerteTabelleSTEA?Bundesland=Bayern`:
  - Formats: xlsx variant, and a JSON variant under `/pc/v1/tableFetch/dia/`.
  - Filters: Bundesland, Kreis, Agentur für Arbeit or Arbeitsmarktregion, using official names; one region per call "aus Performancegründen".
  - Indicators: stock (Bestand) and inflow (Zugang) of vacancies, with changes vs the previous month and the previous year. Periods: current reporting month and the two before.
  - The page states no authentication, rate limits or licence.
  - Source: [API-STEA](https://statistik.arbeitsagentur.de/DE/Statischer-Content/Service/API/API-STEA.html)
- Parallel API pages exist for unemployment (ALO), employment (BST), funding (FST) and Grundsicherung (GRUSI) — [API-ALO](https://statistik.arbeitsagentur.de/DE/Statischer-Content/Service/API/API-ALO.html); [API-BST](https://statistik.arbeitsagentur.de/DE/Statischer-Content/Service/API/API-BST.html)
- Reuse terms: BA statistics are in principle freely accessible. Tables published under the statutory statistics mandate may be used without restriction, and content may be stored, reproduced and distributed with source attribution. Content must not be altered; own calculations must be labelled. Attribution "© Statistik der Bundesagentur für Arbeit", with a link when used online — [BA Statistik Impressum](https://statistik.arbeitsagentur.de/DE/Home/Service/Impressum/impressum_node.html)
- Engpassanalyse 2025: six indicators scored per KldB-2010 Berufsgattung (national) or Berufsgruppe (Länder). There is a "Gesamtdownload Engpassanalyse als csv".
  - Vakanzzeit (median 2025)
  - Arbeitsuchenden-Stellen-Relation (2025 annual average)
  - berufsspezifische Arbeitslosenquote
  - change in the foreign-national employment share (June 2022 to June 2025)
  - Abgangsrate aus Arbeitslosigkeit
  - development of median pay
  - Source: [BA Engpassanalyse](https://statistik.arbeitsagentur.de/DE/Navigation/Statistiken/Interaktive-Statistiken/Fachkraeftebedarf/Engpassanalyse-Nav.html)
- **Vakanzzeit definition:** completed vacancy duration in days, from the employer's desired start date ("gewünschter Besetzungstermin") to deregistration of the vacancy with the Arbeitgeberservice. Only filled vacancies count; cancelled offers do not. Deregistration is a proxy for the filling date — [BA Engpassanalyse](https://statistik.arbeitsagentur.de/DE/Navigation/Statistiken/Interaktive-Statistiken/Fachkraeftebedarf/Engpassanalyse-Nav.html)
- **BA methodology note "Medianvakanzzeiten in der Statistik der gemeldeten Arbeitsstellen" (August 2026)**, read in full. Source for all points below: [BA Hintergrundinfo Medianvakanzzeiten, Aug 2026](https://statistik.arbeitsagentur.de/DE/Statischer-Content/Grundlagen/Methodik-Qualitaet/Methodenberichte/gemeldete-Arbeitsstellen/Generische-Publikationen/Hintergrundinfo-Medianvakanzzeiten-in-der-Statistik-der-gemeldeten-Arbeitsstellen.pdf)
  - Employers always state a desired start date when registering a vacancy. Vakanzzeit runs from that date to the statistical count date (stock) or to deregistration (outflow), and is zero while the desired date has not passed.
  - **The share of deregistered vacancies with more than 1,000 days of completed vacancy duration "seit 2017 kontinuierlich gestiegen":** 0.1% (2016), 0.2% (2017–18), 0.3% (2019), 0.4% (2020–21), 0.5% (2022), 0.6% (2023), 0.9% (2024), 1.5% (2025).
  - The BA's explanation: it seems implausible in many cases that an employer searches for almost three years, but "es gibt Arbeitgeber die immer Personal suchen und aus diesem Grund ihre Stellen nicht abmelden bzw. durchgehend laufen lassen", alongside employers who genuinely search long without success.
  - Outliers distort means. In Hamburg the mean completed Vakanzzeit jumped from 115 days (Oct 2023) to 229 days (Nov 2023), driven by occupation group 252 (vehicle/aerospace/shipbuilding engineering, mean 2,260 days in Nov 2023), while the median moved only from 73 to 85 days.
  - The Engpass indicator has used the median since 2020. The median now becomes the leading measure in standard reporting, with most standard products and data spaces expected to switch by the end of October 2026. Regional statistics services can still supply means on request.
  - Example of a published mean: building construction (Hochbau) vacancies stayed unfilled for 277 days on average in 2025.
  - Usage terms printed in the note: "Daten und Tabellen dürfen uneingeschränkt verwendet werden", with attribution, no alteration, own calculations labelled, and a link when published online.
- 157 bottleneck occupations were identified in 2025 (2024: 163; 2023: 183) — [zm-online](https://www.zm-online.de/news/detail/pflege-und-gesundheitsberufe-weiterhin-am-staerksten-betroffen) (secondary source)
- BA-X: a seasonally adjusted monthly index of labour demand in the primary labour market, based on registered vacancies; April 2026 = 102 — [BA-X Deutschland, April 2026](https://statistik.arbeitsagentur.de/Statistikdaten/Detail/202604/arbeitsmarktberichte/bax-ba-x/ba-x-d-0-202604-pdf.pdf); June 2026 = 103 per secondary reporting — [iww.de](https://www.iww.de/aa/arbeitsvertragsrecht/statistik-arbeitsmarkt-im-juni-2026-verhaltener-ausklang-der-fruehjahrsbelebung-f174800)
- IAB-Stellenerhebung: a quarterly representative establishment survey that counts all vacancies, including those not reported to the BA. It found 1.15 million open positions in Q1 2026 (Q2 2025: 1.06m; Q3 2025: 1.03m) — [dpa via onvista, 2026-06-08](https://www.onvista.de/news/2026/06-08-1-15-millionen-offene-stellen-in-deutschland-im-ersten-quartal-0-10-26519667); FDZ data report on the survey — [IAB-FDZ Datenreport 09/2025](https://doku.iab.de/fdz/reporte/2025/DR_09-25.pdf)

### Inferences
- The BA's own data supply an official, citable precedent for the "evergreen / never deregistered" phenomenon: the share of vacancies closed after more than 1,000 days rose from 0.1% to 1.5% between 2016 and 2025, and the BA attributes this partly to employers who "durchgehend laufen lassen". The dashboard can cite this as context without naming companies.
- Use the occupation-specific (and, where available, regional) median Vakanzzeit as the "expected time-to-fill" yardstick for F1 and F3. A posting alive several multiples beyond its occupation's median is anomalous.
  - Definitions differ: BA durations run from the desired start date to deregistration of registered vacancies, not from the online publication date. The comparison is therefore indicative only.
- Macro "posting inflation" baseline for F6: compare the Jobbörse stock (about 1.02M on 2026-10-24, which includes apprenticeships and partner-board ads) and online-posting counts by occupation with IAB total vacancies (about 1.15M, Q1 2026) and the BA registered-vacancy stock. Rising postings without rising survey vacancies would suggest more non-genuine or duplicate postings. This is an analytic hypothesis, not established.
- BA statistics carry no company identifiers, so there are no publication risks and only an attribution duty applies.

### Gaps
- The current BA "Meldequote" (share of vacancies registered with the BA) for 2025/26 was not found in a primary source.
- The new Statistik API does not yet expose vacancy durations or occupation detail. Its licence terms and rate limits are not stated.
- Not checked: whether Vakanzzeit by occupation and Kreis is downloadable outside the Engpassanalyse (e.g. in "Gemeldete Arbeitsstellen" monthly tables).

## 3. Public job feeds from ATS systems common in Germany (Personio, Greenhouse, Lever, SmartRecruiters, Workday, Recruitee, Ashby, JOIN, softgarden, d.vinci, rexx, SuccessFactors, Umantis, onlyfy)

### Takeaway
**Unauthenticated public sources working on 2026-10-24**

| ATS | Public source | Date fields |
|---|---|---|
| Personio | XML feed, `{company}.jobs.personio.de/xml` | `createdAt` |
| Greenhouse | Job Board API | `first_published`, `updated_at`, `application_deadline` |
| Lever | Postings API, global and EU hosts | `createdAt`, undocumented, epoch ms |
| SmartRecruiters | Posting API | `releasedDate` |
| Workday | unofficial CXS JSON | `startDate` (the posting date, not the job start), `jobReqId` |
| Ashby | Posting API | `publishedAt` |
| JOIN | schema.org JSON-LD on job pages | `datePosted` |
| d.vinci easy | JSON embedded in job pages | `startDate`/`endDate`, probably the publication window |

**Credentials needed**
- softgarden's Frontend API needs the employer's client token.
- Recruitee's careers API will require an employer-generated token from **10 Feb 2027**.
- SmartRecruiters' docs (Aug 2026) say a token is required, even though anonymous calls still work. Treat this access as at risk.
- SAP SuccessFactors, rexx, Umantis and onlyfy were largely unverified; onlyfy pages show no dates.

**What these feeds are good for**
- F1: exact first-publication dates and stable requisition IDs.
- F2: they are the employer-controlled baseline against which aggregator copies are compared.
- F4: salary appears only where the employer enabled it (Greenhouse `pay_input_ranges`, Lever `salaryRange`, Ashby `compensation`, Recruitee and softgarden `salary`).
- F3: **no ATS feed gives an employment start date**, so F3 needs text parsing.
- F5: no feed flags staffing agencies.

**Pitfalls**
- Greenhouse `updated_at` changes on bulk edits, so it is not a freshness signal.
- Feeds contain evergreen "Initiativbewerbung" (speculative application) postings that must be excluded.
- JOIN multiposts every active job to job boards by default.

Vendors publish no terms or rate limits for automated reading of these feeds.

### Cited Findings
**Personio**
- Documented as a website integration: `https://{company}.jobs.personio.de/xml?language={de|en}` (dev docs updatedAt 2025-09-18). Accounts created before 25.11.2020 had to move to the `{company}.jobs.personio.de` domain by 31.05.2021. No rate limits or terms are stated — [Personio dev docs, Integration of open positions](https://developer.personio.de/docs/integration-of-open-positions)
- `.de` and `.com` hosts serve byte-identical XML. Live fields (ottonova, 10 positions) — [ottonova Personio XML, accessed 2026-10-24](https://ottonova.jobs.personio.de/xml?language=en); [Personio's own feed](https://personio.jobs.personio.de/xml)
  - Root `<workzag-jobs>`; each `<position>` contains `id`, `subcompany` (legal entity), `office`, `additionalOffices/office`, `department`, `recruitingCategory`, `name`, `jobDescriptions`, `employmentType`, `seniority`, `schedule`, `keywords`, `occupation`, `occupationCategory`.
  - `createdAt` in ISO 8601, e.g. `2026-03-23T15:24:29+00:00`.
  - No salary, update, expiry or start-date element.
  - The feed includes an evergreen "Initiativ bewerben (m/w/d)" position.
- An undocumented `/search.json` returns JSON without dates — [ottonova search.json](https://ottonova.jobs.personio.de/search.json)
- Tenants without a public feed return 404 on `/xml` (e.g. 10xfounders, 2026-10-24).
- Personio's Recruiting API v2 needs OAuth and covers only the customer's own data — [Personio llms.txt](https://developer.personio.de/llms.txt)
- TheirStack claims data on 4,533 companies using Personio, 1,344 of them in Germany. The figure is undated and the method undisclosed — [TheirStack](https://theirstack.com/en/technology/personio)

**Greenhouse**
- Endpoints `GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs` (`content=true`) and `/jobs/{id}` (`pay_transparency=true` adds `pay_input_ranges` with `min_cents`, `max_cents`, `currency_type`). "Job Board data is publicly available, so authentication is not required for any GET endpoints." No rate limits or terms are stated — [Greenhouse Job Board API docs](https://docs.greenhouse.io/job-board.html)
- Live check (N26, 39 jobs). Source: [N26 Greenhouse board, accessed 2026-10-24](https://boards-api.greenhouse.io/v1/boards/n26/jobs)
  - The list response included `first_published` and `application_deadline` for every job, although the docs list them only for single jobs.
  - `requisition_id` was set on 39/39 (e.g. "R6948"); `application_deadline` was null on 39/39.
  - `first_published` was unique per job (2026-04-02 to 2026-10-23).
  - **`updated_at` had only 25 distinct values; 9 jobs shared one timestamp, i.e. bulk edits.**
  - All `absolute_url`s pointed to n26.com with `?gh_jid=`.

**Lever**
- `GET https://api.lever.co/v0/postings/{SITE}?mode=json` and the EU host `https://api.eu.lever.co/v0/postings/`. No auth for GET. The only stated rate limit is 2 req/s for application POSTs. The README has no terms or licence; last commit 2026-04-23 — [lever/postings-api](https://github.com/lever/postings-api)
- `createdAt` (epoch ms) is **present live but undocumented**, on both the global and EU hosts. There is no requisition ID, update date, expiry or start date — [Lever demo postings, accessed 2026-10-24](https://api.lever.co/v0/postings/leverdemo?mode=json&limit=2); [EU host example](https://api.eu.lever.co/v0/postings/aavelabs?mode=json&limit=1)

**SmartRecruiters**
- Anonymous `GET https://api.smartrecruiters.com/v1/companies/{id}/postings` worked on 2026-10-24 (BoschGroup `totalFound` 5,088). Source: [Bosch postings](https://api.smartrecruiters.com/v1/companies/BoschGroup/postings?limit=1); [Bosch detail](https://api.smartrecruiters.com/v1/companies/BoschGroup/postings/744000157589077)
  - List fields: `id`, `uuid`, `jobAdId`, `refNumber`, `company`, `releasedDate`, `location{…remote,hybrid,…}`, `typeOfEmployment`, `customField[]`.
  - Detail adds `jobId`, `active`, `visibility`, `creator{name}` (recruiter name, personal data), `postingUrl`, `applyUrl`, `jobAd.sections`.
  - There is no salary field.
- The docs (updatedAt 2026-08-24) say the Public Posting API supports API key and OAuth, and the reference requires an `X-SmartToken` header. Anonymous access may be withdrawn — [SmartRecruiters Posting API docs](https://developers.smartrecruiters.com/docs/posting-api); [reference](https://developers.smartrecruiters.com/reference/postingsjsonstream-1)
- Job ads go to the Posting API and "optionally to all free job aggregators" — [SmartRecruiters llms.txt](https://developers.smartrecruiters.com/llms.txt)

**Workday (unofficial)**
- `POST https://{tenant}.wd{N}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs` (JSON body with `limit`, `offset`, `searchText`) and `GET …/job/{externalPath}` worked unauthenticated for Airbus. Source: [Airbus CXS list](https://ag.wd3.myworkdayjobs.com/wday/cxs/ag/airbus/jobs); [Airbus CXS detail](https://ag.wd3.myworkdayjobs.com/wday/cxs/ag/airbus/job/hamburg-area/duales-studium-bachelor-of-science-software-engineering--angewandte-informatik---d-m-w-_jr10420411)
  - The list gives `total` and `jobPostings[]{title, externalPath, locationsText, postedOn}`; `postedOn` is text such as "Posted 30+ Days Ago".
  - The detail's `jobPostingInfo` includes `startDate`, `endDate`, `jobReqId`, `jobPostingId`, `timeType`, `remoteType`, `externalUrl`, and `hiringOrganization{name}` (legal entity).
- In two samples `startDate` matched the posting date: "Posted Yesterday" gave 2026-10-23. Source: [Airbus detail example](https://ag.wd3.myworkdayjobs.com/wday/cxs/ag/airbus/job/Montreal-Area/Leader-Processus-Outillage---Tool-Process-Leader_JR10450490)
- The tenant's robots.txt has no rule for `/wday/cxs/`, and the sitemap has no `<lastmod>`. No Workday terms for these endpoints were found — [Airbus Workday robots.txt](https://ag.wd3.myworkdayjobs.com/robots.txt)

**Recruitee (Tellent)**
- Careers Site API `https://{company}.recruitee.com/api/offers`. Offer fields: `id`, `guid`, `slug`, `created_at`, `published_at`, `updated_at`, `close_at`, `employment_type_code`, `salary{min,max,…}` — [Recruitee offers reference](https://docs.recruitee.com/reference/offers)
- "Deadline for introducing the token to calls is 10 February 2027". After that, "Calls without the authorization header will return the 401 Unauthorized error". The token (`X-Careers-Sites-Token`) is generated in the employer's settings, and "The XML offer feed and jobs widget are not covered by the Careers API token" — [Recruitee authentication, updatedAt 2026-08-12](https://docs.recruitee.com/reference/authentication-1)
- XML job-board feed tags include `<reference>`, `<min_salary>`, `<max_salary>`, `<posted>`, `<updated>` — [Recruitee feed docs](https://docs.recruitee.com/docs/feed)

**Ashby**
- `GET https://api.ashbyhq.com/posting-api/job-board/{name}?includeCompensation=true` (docs updatedAt 2026-10-23); no auth, rate limit or terms stated — [Ashby docs](https://developers.ashbyhq.com/docs/public-job-posting-api)
- Live fields: `id`, `title`, `department`, `team`, `employmentType`, `workplaceType`, `isListed`, `isRemote`, `address.postalAddress`, `jobUrl`, `applyUrl`, `publishedAt`, `compensation{compensationTierSummary, scrapeableCompensationSalarySummary, …}`. No update date or requisition ID — [Ashby API response (n8n, Berlin)](https://api.ashbyhq.com/posting-api/job-board/n8n?includeCompensation=true); [Ashby's own board](https://api.ashbyhq.com/posting-api/job-board/ashby?includeCompensation=true)

**JOIN**
- Job pages `join.com/companies/{company}/{jobId}-{slug}` embed schema.org JSON-LD with `datePosted`, `hiringOrganization`, `directApply`. A 2022-dated posting still rendered in 2026 — [JOIN job page sample](https://join.com/companies/02100/15023229-no-code-developer-webflow-m-f-d)
- API v2 needs an employer API key — [JOIN API reference](https://docs.join.com/reference/getjobs-1)
- "When a job is created, it will be automatically set as active (meaning that the job will be multiposted on job boards)" — [JOIN llms.txt](https://docs.join.com/llms.txt)
- JOIN pushes jobs to the BA Jobbörse — [JOIN blog](https://join.com/de/recruitment-hr-blog/ats-integration-bundesagentur-fuer-arbeit). Vendor claim: 20,000+ companies — [join.com](https://join.com/)

**softgarden**
- The Frontend API v3 `GET https://api.softgarden.io/api/rest/v3/frontend/jobslist/{channelId}` requires a "Client Token or Basic Authorization" — [softgarden Frontend API v3](https://dev.softgarden.de/frontend-v3/jobs-eines-kanals/)
  - Documented fields: `jobDbId`, `jobStartDate`, `jobEndDate`, `postingLastUpdatedDate`, `salary{min_value,max_value,currency,period}`, `project_number`, `internal_reference_id`, `job_owner_*` (personal data).
  - Vendor claim: more than 2,000 companies — [softgarden.com](https://softgarden.com/de/)

**d.vinci easy, rexx, SuccessFactors, Umantis, onlyfy**
- d.vinci easy: pages `{tenant}.dvinci-easy.com/de/jobs/{id}/{slug}` embed JSON with `id`, `startDate`, `endDate`, `reference`, `jobPublicationURL`. One apprenticeship posting showed `startDate` 2026-08-28 and `endDate` 2026-10-31. No public API docs — [d.vinci easy job page](https://aekno-karriere.dvinci-easy.com/de/jobs/269/auszubildende-kaufleute-fur-buromanagement-mwd)
- rexx: vendor claim of "Über 3.000 Kunden in über 30 Ländern"; feeds not verified — [rexx-systems.com](https://www.rexx-systems.com/)
- SAP SuccessFactors
  - jobs.sap.com robots.txt allows all and lists per-language sitemaps — [jobs.sap.com robots.txt](https://jobs.sap.com/robots.txt)
  - The RSS job path returned 403 behind a Cloudflare challenge.
  - The legacy host career5.successfactors.eu disallows all crawling except `/login` — [career5 robots.txt](https://career5.successfactors.eu/robots.txt)
- onlyfy: job pages `{tenant}.onlyfy.jobs/{lang}/job/{id}` have no JSON-LD and no date keys — [onlyfy job page](https://aithyra.onlyfy.jobs/en/job/16jg1teu9fdy5d88oo7pe4t9ko1jy3t)

**Discovery**
- The Common Crawl URL index (latest CC-MAIN-2026-43) lists tenant URLs for smaller ATS domains (e.g. `jobs.eu.lever.co`, `dvinci-easy.com`, `onlyfy.jobs`, `wd3.myworkdayjobs.com`). Queries on large domains such as `jobs.personio.de` timed out (502/504) — [CC index collinfo](https://index.commoncrawl.org/collinfo.json); [example query](https://index.commoncrawl.org/CC-MAIN-2026-43-index?url=jobs.eu.lever.co&matchType=domain&output=json&limit=10&fl=url)
- Personio, d.vinci and onlyfy use wildcard TLS certificates, so certificate-transparency logs (crt.sh) cannot enumerate tenants. Greenhouse, SmartRecruiters and Lever use path-based tokens. This is the ATS subagent's live TLS check and inference.

### Inferences
- **F1 (age and reposts).** Use the first-publication fields: Greenhouse `first_published`, SmartRecruiters `releasedDate`, Ashby `publishedAt`, Personio `createdAt`, Lever `createdAt`, Workday `startDate`/`postedOn`, Recruitee `published_at`. Use requisition-level IDs to link reposts: Greenhouse `requisition_id`/`internal_job_id`, Workday `jobReqId`, SmartRecruiters `jobId`/`refNumber`, softgarden `project_number`, d.vinci `reference`.
  - Ignore Greenhouse `updated_at` as a freshness signal (bulk edits).
  - Check whether Personio `createdAt` and Ashby `publishedAt` reset on republication, which is undocumented.
- **F2 (own channel).** ATS feeds represent the employer's own channel. Greenhouse `absolute_url` on the employer's domain and Workday `externalUrl` confirm a careers-site presence. JOIN's default multiposting means that "on aggregators" is the norm for JOIN customers, so F2 should flag the reverse case: an aggregator posting with no counterpart in the employer's feed.
- **F3.** No ATS exposes the employment start date. Workday's `startDate` is a posting date, and d.vinci/softgarden dates are probably publication windows (unverified). Parse "ab sofort" / "zum 01.01." from description text.
- **Expiry signals.** d.vinci `endDate`, Recruitee `close_at` and Greenhouse `application_deadline` give planned expiry dates. Repeated extension of these dates is a measurable staleness signal.
- **Durability risk.** SmartRecruiters' and Recruitee's moves towards mandatory tokens show that "public" ATS endpoints can close. The pipeline should prefer documented endpoints, monitor HTTP status, and treat 404/401 as "no public feed" rather than "job closed".
- **Personal data.** Strip recruiter names and contact fields at ingestion (SmartRecruiters `creator.name`, softgarden `job_owner_*`).

### Gaps
- **Unverified:** SAP's acquisition of SmartRecruiters and its effect on the API; the Greenhouse EU API host; a live Recruitee check and its XML feed URL; the inner structure of Personio `jobDescriptions`.
- **Undocumented meanings:** Workday `endDate`, and whether Workday's list `total` is capped at 2,000.
- **Not verified:** the date semantics of softgarden and d.vinci; rexx, Umantis and SuccessFactors Career Site Builder feeds (RSS, sitemaps, JSON-LD); onlyfy APIs and ownership.
- **No vendor terms** for automated reading of public feeds were found. Independent German ATS market shares exist only as vendor claims and TheirStack's undated counts (BuiltWith and Wappalyzer not checked).

## 4. schema.org JobPosting structured data, Google's guidelines on expired postings, and Common Crawl

### Takeaway
schema.org JobPosting provides standard fields for most ghost-job features: `datePosted`, `validThrough`, `jobStartDate`/`jobImmediateStart`, `identifier`, `baseSalary` vs `estimatedSalary`, `directApply`, `totalJobOpenings`, `hiringOrganization`.

Google's job-posting documentation (last updated 2026-09-08) gives two ghost-relevant rules:
- `datePosted` is the **original** posting date.
- Expired or filled jobs must be removed: set `validThrough` in the past, return 404/410, or remove the markup.

Google states "We don't allow expired job postings", prohibits fake or non-existent jobs, and enforces this with manual actions. Live markup on a long-filled role is therefore a policy breach, and the markup is a defensible, documented F1 signal.

Common Crawl can in principle supply historical HTML for mining JobPosting markup. Its terms state that crawled content remains subject to third parties' rights, and sites can block CCBot via robots.txt, so coverage is biased. Adoption figures for Germany (Web Data Commons, Web Almanac) were not verified.

### Cited Findings
- schema.org (V30.1, 2026-09-16) definitions:
  - `datePosted` "Publication date of an online listing"
  - `validThrough` "The date after when the item is not valid"
  - `jobStartDate` "The date on which a successful applicant for this job would be expected to start work"
  - `jobImmediateStart` (available for immediate start)
  - `baseSalary`; `estimatedSalary` (often computed by outside organisations, not the hiring organisation)
  - `directApply` (whether the URL enables direct application)
  - `hiringOrganization` ("Organization or Person offering the job position")
  - `totalJobOpenings` (positive integer; omit if unknown)
  - `employmentUnit`, `identifier`, `employmentType`, `jobLocation`
  - Source: [schema.org/JobPosting](https://schema.org/JobPosting)
- Google Search Central, Job posting structured data ("Last updated 2026-09-08 UTC"):
  - **Required:** `datePosted` ("the original date" the employer posted the job), `description`, `hiringOrganization`, `jobLocation`, `title`.
  - **Recommended:** `applicantLocationRequirements`, `baseSalary` (the employer's actual base pay, not an estimate), `directApply`, `employmentType`, `identifier` (the hiring organisation's unique job ID), `jobLocationType`, and `validThrough` (required when the posting has an expiration date).
  - Source: [Google job posting docs](https://developers.google.com/search/docs/appearance/structured-data/job-posting)
- Google on expired or filled jobs: do one of the following, then notify Google via the Indexing API (preferred) and keep a sitemap. If a job is filled early, "remove the job posting" — [Google job posting docs](https://developers.google.com/search/docs/appearance/structured-data/job-posting)
  - set `validThrough` to a past date;
  - remove the page so it returns 404/410;
  - remove the JobPosting markup.
- Google policies: "We don't allow expired job postings". Markup is only for single-job pages, not listing pages. Prohibited content includes fake or non-existent jobs, false location data, keyword stuffing, and requiring payment from applicants. Sanctions: manual actions, after which the markup is ignored and postings are removed from job search — [Google job posting docs](https://developers.google.com/search/docs/appearance/structured-data/job-posting)
- Google's `directApply` definition: a "short and simple application process"; it is not direct if the user must click apply, fill in a form, or sign in or log in more than once — [Google job posting docs](https://developers.google.com/search/docs/appearance/structured-data/job-posting)
- Common Crawl terms of use (last updated 2024-03-07):
  - The licence is limited and non-exclusive.
  - No warranty for the "lawfulness or accuracy of the Crawled Content".
  - The content may be subject to separate terms from its owners, and users must "respect the copyrights and other applicable rights of third parties".
  - Users are advised to obtain legal advice before use, including commercial use; users indemnify CC; California law; arbitration.
  - Source: [Common Crawl Terms of Use](https://commoncrawl.org/terms-of-use)
- CCBot: user agent `CCBot/2.0`, dedicated IP ranges (published JSON), blockable with `User-agent: CCBot` / `Disallow: /`; Common Crawl runs an opt-out registry — [Common Crawl CCBot page](https://commoncrawl.org/ccbot)
- Indeed's robots.txt lists CCBot among AI-training bots that get specific path disallows. StepStone's robots.txt names no AI or CC bots — [de.indeed.com/robots.txt](https://de.indeed.com/robots.txt); [stepstone.de/robots.txt](https://www.stepstone.de/robots.txt)

### Inferences
- **F1.** Compare `datePosted` against the first date the URL or `identifier` was observed (in Common Crawl or own crawls). If `datePosted` moves forward on an unchanged `identifier` or text, the posting is being refreshed or reposted; Google defines `datePosted` as the original date. If `validThrough` lies in the past while the page is still live, or `validThrough` keeps being extended, the posting is stale.
- **F2.** `hiringOrganization` plus the page's domain (employer domain vs board domain) indicates own-site vs aggregator presence. `directApply=false`, or apply links that redirect to an aggregator, are supporting hints.
- **F3.** Use `jobStartDate`/`jobImmediateStart` vs `datePosted`.
- **F4.** Use `baseSalary` (employer-provided), ignoring `estimatedSalary`, which third parties compute.
- **Coverage bias.** Historical mining via Common Crawl misses sites that block CCBot, and job-detail pages are a moving target. Sampling bias must be documented if Common Crawl rates are published.
- **Law.** Mining markup at scale raises the TDM and database-right questions in Section 7. CJEU C-762/19 (CV-Online) concerned a search engine that used exactly this kind of job-ad meta-tag markup; its holding should be read in full before publishing derived data.

### Gaps
- Not retrieved (search budget exhausted):
  - Web Data Commons JobPosting statistics (hosts and pages, .de share) and HTTP Archive Web Almanac structured-data figures, so the extent of JobPosting use in Germany is **unknown** from this research;
  - the Common Crawl crawl cadence and index-query mechanics;
  - research papers that mined Common Crawl or WDC for job postings.
- Google's page does not say whether `datePosted` may be refreshed on edits, so how sites actually behave is unknown.



## 5. Job boards and aggregators (StepStone, Indeed, LinkedIn, XING, Glassdoor, Stellenanzeigen.de, Monster.de, Arbeitnow, Adzuna, Jooble, Careerjet, Google for Jobs via SerpApi-style services)

### Takeaway
The large boards signal hostility to automated access in their robots.txt files:
- **LinkedIn** prohibits robots or other automated access without express permission.
- **StepStone** prohibits "any other use of robots", and disallows search-result and most query-string URLs.
- **Indeed** disallows job-view pages (`/viewjob`, `/m/viewjob`, `/rc/`) for generic crawlers.

Scraping these for F1 or F2 is therefore high-risk (contract or ToS, database right; see Section 7) and should be replaced by open or licensed APIs. **Arbeitnow** offers a free, keyless JSON feed with `created_at`. **Adzuna** has a registered API with search, histogram, historical-salary, regional and top-companies endpoints; its Germany coverage and terms were not verified here.

Not verified in this session:
- XING, Glassdoor, Stellenanzeigen.de, Monster.de, Jooble, Careerjet and SerpApi
- the boards' terms-of-service texts
- whether LinkedIn's "reposted" labels and applicant counts are exposed

### Cited Findings
- **StepStone robots.txt.**
  - The header states that "Any other use of robots or failure to obey the robots exclusion standards" is prohibited.
  - Disallowed: `/search-results`, the `/5/` search and job-apply paths, company-profile paths, `/jobs/vollzeit/`, `/jobs/teilzeit/`, `/jobs/home-office/`, and all query-string URLs (`/?*`, `/*?*`) apart from listed exceptions.
  - No crawl-delay, no sitemap, no AI-bot or TDM-specific lines.
  - Source: [stepstone.de/robots.txt, accessed 2026-10-24](https://www.stepstone.de/robots.txt)
- **Indeed (de.indeed.com) robots.txt.**
  - For `*`: `/viewjob`, `/m/viewjob` and `/rc/` are disallowed, as are country and title paths under `/jobs`.
  - Search/retrieval bots (Googlebot, Google-Extended, ChatGPT-User, PerplexityBot, Claude-User, Claude-SearchBot, OAI-SearchBot) get `Allow: /` with path disallows.
  - AI-training bots (GPTBot, CCBot, anthropic-ai, ClaudeBot, Bytespider, Applebot-Extended, Meta-ExternalAgent) get specific path disallows.
  - Fully blocked: JobdiggerSpider, Scrapy, GoogleOther and others.
  - Source: [de.indeed.com/robots.txt, accessed 2026-10-24](https://de.indeed.com/robots.txt)
- **LinkedIn robots.txt.** The header says the use of robots or other automated means to access LinkedIn without LinkedIn's express permission is strictly prohibited, and invites organisations to apply for crawling permission. Named search bots get long disallow lists including `/jobs/view/externalApply/`, `/jobs?runSearch*` and `/jobs-guest/` — [linkedin.com/robots.txt, accessed 2026-10-24](https://www.linkedin.com/robots.txt)
- **Arbeitnow job board API** (`https://www.arbeitnow.com/api/job-board-api`). JSON with top-level `data`; job objects have `slug`, `company_name`, `title`, `description` (HTML), `remote`, `url`, `tags`, `job_types`, `location`, `created_at` (Unix seconds). No key needed. The page was about 4.1 MB, so pagination metadata and terms could not be confirmed — [Arbeitnow API, accessed 2026-10-24](https://www.arbeitnow.com/api/job-board-api)
- **Adzuna API.** Endpoints: search ads, salary data, historical data, histogram, regional data, top companies, categories, "jobsworth" (salary estimate) and API version. Every request needs `app_id` and `app_key` (registration). The overview page does not list countries, rate limits or ad fields, and its terms are linked but were not read — [Adzuna developer overview](https://developer.adzuna.com/overview)

### Inferences
- **Role of boards.** Boards are mainly needed for F2 (is the ad also, or only, on aggregators?) and for repost frequency. Board dates are often ingestion or refresh dates, not employer posting dates (this needs verifying per board). Use licensed APIs, partner feeds, or Google-for-Jobs-style APIs rather than scraping pages the robots.txt files exclude.
- **Adzuna** could supply an independent cross-check of German posting counts and pay. Adzuna marks predicted salaries (e.g. a `salary_is_predicted` flag, unverified here); predicted salaries must not count as "salary stated" for F4.
- **Arbeitnow** skews to English-language and tech jobs (inferred from its descriptions' footer "English Speaking Jobs in Germany"), so it is not representative.

### Gaps
- Not verified:
  - the ToS texts and scraping clauses of StepStone, Indeed, LinkedIn, XING, Glassdoor, Stellenanzeigen.de and Monster.de
  - official API options in 2026 (Indeed Publisher/Job Sync, LinkedIn partner APIs, XING API status, Glassdoor API)
  - the Jooble and Careerjet APIs
  - SerpApi Google Jobs fields and any Google v. SerpApi litigation
  - LinkedIn's "Reposted"/applicant-count labels
  - Adzuna's Germany coverage, rate limits and terms
- LinkedIn's `*` group was truncated in the fetch, so whether `/jobs/view/` is disallowed for generic crawlers was not confirmed.



## 6. Company context data: Handelsregister, Unternehmensregister, Bundesanzeiger, insolvency notices, OffeneRegister, OpenCorporates, North Data, funding, layoffs, LinkedIn headcount, employer reviews

### Takeaway
No German register offers an official bulk API for this purpose, and the official portals restrict systematic retrieval.

**Registers and notices**
- **Handelsregister** limits use to **60 searches or entity views per hour**. It expressly bans systematic retrieval that builds or updates parallel registers, so it suits on-demand lookups of employers seen in postings, not mirroring.
- **Annual accounts**, the source of the average employee count for F6, are filed with the **Unternehmensregister** for fiscal years starting after 31.12.2021, and with the **Bundesanzeiger** for older years. Bundesanzeiger pages are captcha-gated.
- **Small companies must still state the employee count.** Micro companies can avoid it by depositing only their balance sheet. Counts lag one to two years.
- **insolvenzbekanntmachungen.de** is the core F7 source. Notices are deleted about six months after proceedings end, so snapshots are essential. Its two-week search restriction applies only to consumer (non-self-employed) insolvencies.

**Commercial and open data**
- OpenCorporates is ODbL share-alike and bans scraping.
- North Data AGB ban scraping and resale and require attribution.
- Crunchbase's data terms forbid public display unless the order form allows it.
- startupdetector (Handelsregister-derived German funding data) and GDELT/layoffs.fyi (free with attribution) are the most usable F7 add-ons.

**Not public or restricted**
- German mass-layoff notices (§17 KSchG) are **not public**.
- **LinkedIn** headcount is off-limits: its User Agreement bans scraping, and the Proxycurl settlement (2025) shows enforcement.
- **F8 (kununu applicant reviews, Glassdoor interview reviews)** has no API. Terms and criteria could not be fetched, and Glassdoor was legally merged into Indeed on 1 July 2026.

### Cited Findings
**Handelsregister (handelsregister.de)**
- A joint Länder portal for Handels-, Genossenschafts-, Partnerschafts-, Gesellschafts- and Vereinsregister (version 2.12.12, Stand 2026-09-22) — [Registerportal welcome page](https://www.handelsregister.de/rp_web/welcome.xhtml)
- Document types: AD (current printout), CD (chronological), HD (historical), SI (structured register content as XML; "unverbindlicher Service"), register-folder documents (e.g. Gesellschafterliste, Gesellschaftsvertrag), Unternehmensträgerdaten. No API and no bulk offer is mentioned — [Registerportal information](https://www.handelsregister.de/rp_web/information/welcome.xhtml)
- Nutzungsordnung:
  - **Ziffer 5:** "Es ist unzulässig, mehr als 60 Suchen oder Aufrufe von Rechtsträgern pro Stunde im Registerportal vorzunehmen."
  - **Ziffer 3:** "Systematische Abrufe, um parallele Voll- oder Teilregister aufzubauen, auszubauen oder zu aktualisieren, sind unzulässig."
  - **Ziffer 6:** IP blocking and user exclusion.
  - **Ziffer 7:** users with a demonstrable need can apply to the Servicestelle at AG Hagen for a "Whitelist-IP".
  - FAQ: TOR is blocked, as are high-volume IPs.
  - Source: [Registerportal information](https://www.handelsregister.de/rp_web/information/welcome.xhtml)
- §52 HRV allows automated retrieval only "einzeln für jedes Registerblatt" and with "keine gezielte Suche nach natürlichen Personen"; §53 HRV requires retrieval logging — [§52 HRV](https://lxgesetze.de/hrv/52); [§53 HRV](https://www.gesetze-im-internet.de/hdlregvfg/__53.html)
- The community CLI bundesAPI/handelsregister (search only, "work in progress") warns that the portal is regularly targeted by automated mass queries and that §§303a/303b StGB may apply — [bundesAPI/handelsregister](https://github.com/bundesAPI/handelsregister)
- After fees were dropped in 2022, the Bundesrat noted a sharp rise in retrievals and asked the ministry to examine "Data-Mining" misuse — [BR-Drs. 208/23](https://dserver.bundestag.de/brd/2023/0208-23.pdf)
- Documents not yet online can be digitised on request: "derzeit 2,00 EUR pro Seite, mindestens 25,00 EUR" — [Registerportal FAQ](https://www.handelsregister.de/rp_web/information/welcome.xhtml)
- Status notices report repeated overloads from heavy retrieval volumes and a planned outage of Coesfeld retrievals from 29.10.2026 to 02.11.2026 — [Registerportal welcome page](https://www.handelsregister.de/rp_web/welcome.xhtml)

**Unternehmensregister**
- §8b(2) HGB gives access to the following — [§8b HGB](https://www.gesetze-im-internet.de/hgb/__8b.html)
  - register entries and filed documents
  - accounting documents (except permanently deposited balance sheets)
  - company-law notices
  - capital-market publications
  - insolvency-court notices under §9 InsO, excluding consumer proceedings (Nr. 11)
- Under its terms (ANB), accounts "für Geschäftsjahre beginnend nach dem 31.12.2021 sind mit Inkrafttreten des DiRUG … zum 01.08.2022 an das Unternehmensregister zu übermitteln". Other ANB clauses — [Unternehmensregister ANB (PDF)](https://www.unternehmensregister.de/i18n-doc/D061_UReg_nutz_0118_de.pdf)
  - Deposited micro-company balance sheets (§326(2) HGB) are excluded from search and available only for a fee after registration.
  - Viewing needs no registration.
  - "alle Abrufe dürfen dokumentiert" (§6(2)).
  - A keyword scan found no clause on robots or mass retrieval.

**Bundesanzeiger**
- Holds accounts for fiscal years before 2022 — [Unternehmensregister ANB](https://www.unternehmensregister.de/i18n-doc/D061_UReg_nutz_0118_de.pdf)
- The bundesAPI `deutschland` package (Apache-2.0) has a Bundesanzeiger module. It detects captcha pages and solves them with an ONNX model by default, which confirms that report pages are captcha-gated. It returns date, name, company, report text and HTML — [bundesAPI/deutschland bundesanzeiger.py](https://github.com/bundesAPI/deutschland/blob/main/src/deutschland/bundesanzeiger/bundesanzeiger.py)
- §288 HGB relieves small companies only of "eine Trennung nach Gruppen bei der Angabe nach § 285 Nummer 7", so they must still state the average employee number. Medium companies get no relief — [§288 HGB](https://www.gesetze-im-internet.de/hgb/__288.html)
- The filing deadline is at most 12 months after the balance-sheet date — [IHK Frankfurt on DiRUG](https://www.frankfurt-main.ihk.de/recht/recht-und-steuern-aktuell/neue-offenlegungspflichten-nach-dirug-5559734)

**insolvenzbekanntmachungen.de** (operated by the NRW Justice Ministry; www redirects to neu.insolvenzbekanntmachungen.de)
- Search fields: Bundesland, court, name or Firma, seat or residence, Aktenzeichen, register number (only for proceedings opened up to 25.06.2018), publication type. Results are capped at 1,000 hits, except when only one day's hits are shown, and result sets are valid for 60 minutes. No API or RSS — [search info](https://neu.insolvenzbekanntmachungen.de/ap/info_suche.jsf)
- The §2(1) Nr. 3 InsoBekV two-week search restriction applies only where the debtor is a natural person without self-employed economic activity — [§2 InsoBekV](https://www.gesetze-im-internet.de/insobekv/__2.html)
- Deletion "spätestens sechs Monate nach der Aufhebung" (or after a discontinuation becomes final); other publications after one month — [§3 InsoBekV](https://www.gesetze-im-internet.de/insobekv/__3.html)
- The legal notice has no clause on automated access and states that official notices are not copyright-protected under §5 UrhG — [Rechtliche Hinweise](https://neu.insolvenzbekanntmachungen.de/ap/rechtlicheHinweise.jsf)

**OffeneRegister, OpenCorporates, North Data**
- OffeneRegister: built with OpenCorporates mainly from Handelsregister announcements; CC BY 4.0; JSONL (about 250 MB as bz2) and SQLite dumps plus a SQL API. The snapshot date is not shown (likely stale) — [offeneregister.de](https://offeneregister.de/)
- OpenCorporates API plans, with "free at-scale access" for journalists, NGOs and universities — [OpenCorporates pricing](https://opencorporates.com/pricing/)
  - Essentials £2,250 a year (500 calls a month)
  - Starter £6,600 a year (2,500)
  - Basic £12,000 a year (5,000)
  - Enterprise bulk on request
- OpenCorporates terms — [OpenCorporates terms](https://opencorporates.com/terms-of-use-2/)
  - Data under ODbL 1.0, with improvements to be shared under ODbL (share-alike).
  - Attribution "from OpenCorporates" is required.
  - Scraping is banned "for any purpose other than search engine indexation".
- North Data API — [North Data data page](https://www.northdata.de/_data)
  - M €500 a month (base data, history, insolvencies), L €750, XL €1,000 (financials), XXL €1,500 (shareholders), excl. VAT.
  - 5,000 calls a month included, then €0.10–0.05 per call.
  - Minimum 12 months; "kein Weiterverkauf"; quarterly country bulk export €2,250–7,950.
- North Data AGB (10.10.2024) — [North Data AGB](https://www.northdata.de/_agb)
  - Scraping is banned ("nicht mittels automatisierter Skripte/Abfragen auszulesen").
  - Data may be passed to third parties only "auszugsweise und in verarbeiteter Form".
  - "In jedem Fall muss jedoch die Quelle angegeben werden."

**Funding**
- Crunchbase
  - "Crunchbase no longer offers new Basic API keys" — [Crunchbase Basic APIs](https://data.crunchbase.com/docs/basic-apis.md)
  - Rate limit: 200 requests per minute per key — [API essentials](https://data.crunchbase.com/docs/api-essentials.md)
  - Insights and Predictions packages include Layoff endpoints — [Crunchbase llms.txt](https://data.crunchbase.com/llms.txt)
  - Data Access Terms (effective 26 Nov 2024): no "display, publish, distribute" except as the Order Form authorises; no model training; data must be destroyed on termination — [Crunchbase Data Access Terms](https://data.crunchbase.com/docs/data-access-terms.md)
  - Pricing is sales-only; third parties cite about $20k a year (unverified) — [Vendr](https://www.vendr.com/marketplace/crunchbase)
- Dealroom: Premium €250 and Premium Plus €325 per seat per month (annual, 3–20 seats). The API is an add-on "Priced on call volume, on top of any plan" — [Dealroom pricing](https://dealroom.co/pricing)
- startupdetector
  - Monitors the Handelsregister "jede Woche" for new startups, funding rounds and investors.
  - Germany only, data from 2014.
  - 23,000+ startups, 8,000+ funding rounds.
  - Fields include industry, location, investors, insolvencies, amounts and dilution.
  - Access via API or spreadsheet.
  - Sources: [startupdetector](https://startupdetector.de/)
  - Pricing: €385–695 a month on annual contracts; the page shows two price versions; research ("Wissenschaft") on request — [startupdetector pricing](https://startupdetector.de/pricing)

**Layoffs and restructuring**
- layoffs.fyi is a "Tech and Startup Layoff Tracker": "Data is free to use with attribution to layoffs.fyi" — [layoffs.fyi](https://layoffs.fyi/)
- GDELT
  - Terms: "unlimited and unrestricted use … without fee", with a citation and link required — [GDELT about](https://www.gdeltproject.org/about.html)
  - DOC 2.0 API: rolling three months of coverage, 65 machine-translated languages, filters `sourcelang`/`sourcecountry`/`theme`/`tone`, up to 250 records per query as JSON/CSV/RSS — [GDELT DOC 2.0 announcement](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/)
  - A test query `Stellenabbau sourcelang:german` returned `{}` and a follow-up call returned HTTP 429. This comes from the subagent's own test on 2026-10-24; the cause and the rate limit are unverified.
- EQS News shows ad-hoc-filterable news (newest item 24 Oct 2026). No RSS or API was visible, and the terms were not read — [EQS News](https://www.eqs-news.com/)
- Mass-layoff notices under §17 KSchG go only to the Agentur für Arbeit (with a copy to the works council). The law provides for no publication — [§17 KSchG](https://www.gesetze-im-internet.de/kschg/__17.html); [BA page on Anzeigepflicht](https://www.arbeitsagentur.de/unternehmen/personalfragen/pflichten-arbeitgeber/anzeigepflicht-bei-entlassungen)

**LinkedIn headcount**
- There is no public API. Talent Insights is sold through sales only, with no API or export mentioned — [LinkedIn Talent Insights](https://business.linkedin.com/talent-solutions/talent-insights)
- User Agreement (effective 3 Nov 2025) §8.2 bans "software, devices, scripts, robots or any other means" to scrape, the copying or distribution of information "obtained from the Services", and "bots or other unauthorized automated methods" — [LinkedIn User Agreement](https://www.linkedin.com/legal/user-agreement)
- Proxycurl shut down "to comply with the legal settlement with LinkedIn" after being sued in January 2025 (blog post of 4 July 2025) — [Proxycurl blog](https://nubela.co/blog/goodbye-proxycurl/)

**Employer reviews (F8)**
- kununu: owned by Xing since 2013; part of New Work SE (Xing, onlyfy, kununu, InterNations). New Work was delisted in August 2024, and "Im Juni 2025 übernahm Burda 100 % der Aktienanteile" — [de.wikipedia New Work SE](https://de.wikipedia.org/wiki/New_Work_SE) (secondary source)
- Applicants can rate application processes anonymously on kununu — [de.wikipedia Kununu](https://de.wikipedia.org/wiki/Kununu); [123recht](https://www.123recht.de/ratgeber/internetrecht-computerrecht/Hilfe-bei-negativen-Bewertungen-auf-Kununu-__a159574.html)
- Glassdoor
  - Recruit announced in July 2025 that Glassdoor's operations would fold into Indeed (1,300 layoffs) — [HR Dive](https://www.hrdive.com/news/layoffs-glassdoor-indeed-ai-integration/752876/)
  - Glassdoor legally merged into Indeed, Inc. on 1 July 2026 — [Reworked, 24 Jul 2026](https://www.reworked.co/employee-experience/glassdoor-folds-into-indeed/)
  - Contradiction: Indeed's terms (last updated 29 Sep 2026) say "Indeed and Glassdoor continue to be separate online platforms" — [Indeed legal](https://www.indeed.com/legal)

### Inferences
- **F6 (posting volume vs headcount).**
  - Numerator: BA employer facets or hashes plus ATS feed counts (Sections 1 and 3).
  - Denominator: average employee numbers from accounts in the Unternehmensregister (FY2022+) or Bundesanzeiger (older), or North Data XL+ financials if licensed.
  - Constraints: Handelsregister lookups are capped at 60 an hour with mirroring banned, Bundesanzeiger captchas must not be bypassed automatically (circumventing a technical measure is a legal risk), and micro companies and the 1–2-year lag leave holes. Use headcount bands and treat missing values explicitly.
- **F7 (funding, layoffs, insolvency).**
  - Insolvency: query insolvenzbekanntmachungen.de one day at a time (avoiding the 1,000-hit cap) and keep own snapshots, because notices are deleted. Sole traders' notices are personal data, so align retention with §3 InsoBekV.
  - Funding: startupdetector (licensed, German, Handelsregister-based) is the closest fit. Crunchbase needs explicit display rights for a public dashboard.
  - Layoffs: there is no public German register (§17 KSchG notices are confidential). Use news (GDELT, with attribution) and ad-hoc disclosures for listed firms. layoffs.fyi is tech-only.
- **Entity resolution.** Match BA `firma` and ATS company names to register numbers, using on-demand Handelsregister lookups within the hourly limit, or licensed North Data/OpenCorporates. OpenCorporates' ODbL share-alike would force publication of the derived database under ODbL, and North Data forbids resale and requires attribution.
- **F8.** No lawful bulk source for applicant-experience reviews was identified. kununu and Glassdoor offer no API, and their content carries the review-authenticity issues discussed in Section 8. F8 should be dropped, or limited to licensed or partnered data.

### Gaps
- **Bundesanzeiger:** reader terms, costs, and whether FY2022+ accounts are shown.
- **Unternehmensregister:** rules on automated access beyond the ANB, the scope of the "Großkundenschnittstelle", and retrieval fees (a third-party calculator cites €4.50 per automated retrieval under JVKostG; unverified).
- **Handelsregister:** compliance with the EU High-Value Datasets Regulation (EU) 2023/138 "companies" category (EUR-Lex could not be retrieved), any plans for an official API, and transposition of Directive (EU) 2025/25.
- **OpenCorporates and North Data:** OpenCorporates' German coverage and freshness; whether North Data returns employee counts as API fields.
- **Funding and layoff sources:** the EY Startup-Barometer was not checked; Dealroom's API scope and display terms; layoffs.fyi fields and German coverage; GDELT's rate limit and how German-language queries behave.
- **Capital-market notices:** EQS RSS and terms, and whether Art. 17 MAR ad-hoc notices reach the Unternehmensregister.
- **LinkedIn-data vendors:** terms and legal exposure of Revelio, Coresignal, Live Data and PDL.
- **Review platforms:** kununu applicant-review criteria, terms and API (kununu.com returned empty pages); Glassdoor's terms (HTTP 403), interview-review fields and API status.

## 7. Legal constraints on collecting (GDPR, database right §87a ff. UrhG and CJEU case law, TDM exception §44b UrhG, BGH screen-scraping case law, enforceability of terms, EU AI Act)

### Takeaway
**Highest risk: bulk scraping or mirroring of commercial job boards.** This is exactly the CJEU *CV-Online v Melons* scenario: a job-ad search engine that copies and indexes a job site, including the metadata embedded for search engines. It is extraction and re-utilisation, which the maker may prohibit where it endangers the return on its investment. OLG Köln applied this in February 2026 against an aggregator and held that **public funding does not exclude database protection**, which is relevant to the BA Jobbörse.

**TDM exceptions cover copying, not publishing.**
- §44b UrhG (and, for databases, §87c(1) Nr. 4) cover *copying* for analysis, not publishing copies.
- The exception is lost if the rightholder reserved it in machine-readable form. OLG Hamburg (LAION appeal, 10.12.2025) held that a reservation must be machine-*interpretable* by the technology at the time of download. Natural-language terms may therefore count for crawls today, and a BGH appeal is reportedly pending.
- Commercial TDM of databases (Nr. 4) can be excluded by contract; research TDM under §60d cannot.

**Scraping case law and its limits.**
- BGH *Flugvermittlung im Internet* (2014): scraping public data in breach of click-accepted terms is not unfair competition by itself, but circumventing technical protection may be.
- Criminal and circumvention limits apply to logins, captchas and access controls: §202a and §§303a/b StGB, §§95a/108b UrhG.

**Platform terms.** The BA (Stand 08.07.2026), LinkedIn and StepStone expressly ban robots. Greenhouse and Lever publish feeds for public consumption.

**GDPR.** Legitimate interest (Art. 6(1)(f)) is a workable basis (CJEU KNLTB 2024; EDPB Opinion 28/2024; CNIL 2025; OLG Köln 2025), with the Dutch DPA as a strict outlier. Recruiter contact data should be dropped at ingestion, and sole-trader employers are natural persons.

**AI Act.** A ghost-job scorer most likely falls outside Annex III(4). The Digital Omnibus, Regulation (EU) 2026/1744, moved Annex III obligations to **2 Dec 2027**, and the Art. 50 transparency duties have applied since 2 Aug 2026.

### Cited Findings
**Database maker's right: statute**
- §87a: protection for a systematically arranged, individually accessible collection whose obtaining, verification or presentation required an investment "nach Art oder Umfang wesentlich". A substantially changed database with a substantial new investment counts as a new database — [§87a UrhG](https://www.gesetze-im-internet.de/urhg/__87a.html)
- §87b(1): the maker has exclusive rights over the whole database or "einen nach Art oder Umfang wesentlichen Teil". Repeated and systematic use of insubstantial parts is treated the same where it "einer normalen Auswertung der Datenbank zuwiderlaufen" or "die berechtigten Interessen des Datenbankherstellers unzumutbar beeinträchtigen" — [§87b UrhG](https://www.gesetze-im-internet.de/urhg/__87b.html)
- §87c(1) permits reproducing a substantial part for private use (Nr. 1, not for electronically accessible databases), research (§60c, Nr. 2), teaching (Nr. 3), **TDM under §44b (Nr. 4)**, **research TDM under §60d (Nr. 5)** and preservation (Nr. 6) — [§87c UrhG](https://www.gesetze-im-internet.de/urhg/__87c.html)
  - Per the legal subagent's reading of §87c(6) with §60g(1), Nr. 2, 3, 5 and 6 are protected against contractual override, but **Nr. 4 (commercial TDM) is not**.
  - The exceptions cover reproduction, not public communication.
- §87d: protection lasts 15 years from publication — [§87d UrhG](https://www.gesetze-im-internet.de/urhg/__87d.html)
- §87e: contract clauses barring a lawful user from normal, non-prejudicial use of insubstantial parts are void — [§87e UrhG](https://www.gesetze-im-internet.de/urhg/__87e.html)

**CJEU case law**
- **CJEU C-762/19, CV-Online Latvia v Melons (3 June 2021).**
  - Facts: CV-Online ran a job-ad database. Melons' KurDarbs.lv was a job search engine that aggregated sites and linked to the original ads, and argued it only reused metadata CV-Online had embedded for search-engine indexing.
  - Holding: a specialised search engine that copies and indexes the whole or a substantial part of a freely accessible database and lets users search it "is 'extracting' and 're-utilising'". The maker can prohibit this only "where those acts adversely affect its investment", i.e. "constitute a risk to the possibility of redeeming that investment", which is for the national court to establish.
  - Source: [Lewis Silkin, 10 Jun 2021](https://www.lewissilkin.com/insights/2021/06/10/database-battle-between-job-ad-websites-eu-court-of-justice-decision-102h08y); background on the AG opinion (Szpunar, 14 Jan 2021) — [Kluwer Copyright Blog](https://legalblogs.wolterskluwer.com/copyright-blog/search-engines-and-databases-in-the-search-for-a-balance-the-ags-opinion-in-the-cv-online-latvia-case/)
  - Paragraphs quoted by German courts — [dejure citing list](https://dejure.org/dienste/vernetzung/rechtsprechung?Gericht=EuGH&Datum=03.06.2021&Aktenzeichen=C-762/19); [OLG Köln 6 U 75/25](https://nrwe.justiz.nrw.de/olgs/koeln/j2026/6_U_75_25_Urteil_20260227.html)
    - Para 31: extraction and re-utilisation cover any appropriation of the results of the investment without consent that deprives the maker of revenue.
    - Para 41: the court must strike a "fair balance" between recouping the investment and users' and competitors' interests in access to information and innovation.
- **CJEU C-202/12, Innoweb v Wegener (19 Dec 2013).** A dedicated meta search engine for car ads re-utilises the searched database when it does all of the following — [Kluwer Copyright Blog](https://legalblogs.wolterskluwer.com/copyright-blog/search-engines-and-databases-in-the-search-for-a-balance-the-ags-opinion-in-the-cv-online-latvia-case/)
  - offers a search form with essentially the same functionality as the database's own;
  - translates queries in real time;
  - presents results in a comparable order.
- **CJEU C-30/14, Ryanair v PR Aviation (15 Jan 2015).** German headnotes: "Screen Scraping; Vertragliche Beschränkung der Nutzung einer Datenbank" and "Fluglinie kann Screen Scraping per AGB verbieten". Where a database is protected by neither copyright nor the sui generis right, the directive does not prevent contractual restrictions on its use — [dejure](https://dejure.org/dienste/vernetzung/rechtsprechung?Gericht=EuGH&Datum=15.01.2015&Aktenzeichen=C-30/14)

**German follow-on case law**
- **OLG Köln 27.02.2026, 6 U 75/25** (preliminary injunction; appeal from LG Köln 15.04.2025, 14 O 82/25). The ARD broadcasters sued a streaming platform that integrated the ARD Mediathek. Source: [OLG Köln 6 U 75/25 (NRWE)](https://nrwe.justiz.nrw.de/olgs/koeln/j2026/6_U_75_25_Urteil_20260227.html)
  - The Mediathek is a §87a database (search, categories and curation; substantial investment), and **public, licence-fee funding does not exclude protection**.
  - Near-complete replication is not mere linking.
  - In the CV-Online balancing, one-sided commercial use and the diversion of users weighed against the aggregator.
  - A bulk takeover of metadata over several days was repeated and systematic extraction under §87b(1) S.2.
- **Older scraper-friendly line.**
  - BGH 22.06.2011, I ZR 159/10 ("Automobil-Onlinebörse"): no claim under §87b(1) S.2 for repeated copying of insubstantial parts not aimed at rebuilding the database.
  - OLG Frankfurt 05.03.2009, 6 U 221/08 and OLG Hamburg 24.10.2012, 5 U 38/10: flight-data scraping stayed within normal exploitation.
  - Source: [Otto Schmidt IT-Recht blog](https://www.otto-schmidt.de/blog/it-recht-blog/sind-datenbanken-gegen-screen-scraping-geschutzt-ITBLOG0001400.html)

**TDM exceptions and LAION**
- **§44b UrhG.**
  - TDM is "die automatisierte Analyse von einzelnen oder mehreren digitalen oder digitalisierten Werken … um daraus Informationen insbesondere über Muster, Trends und Korrelationen zu gewinnen" (Abs. 1).
  - Copies of lawfully accessible works are permitted and must be deleted when no longer needed (Abs. 2).
  - "Ein Nutzungsvorbehalt bei online zugänglichen Werken ist nur dann wirksam, wenn er in maschinenlesbarer Form erfolgt" (Abs. 3).
  - Source: [§44b UrhG](https://www.gesetze-im-internet.de/urhg/__44b.html)
- **§60d UrhG.**
  - Research TDM may be done by research organisations (non-commercial, reinvesting profits, or with a public-interest mandate), cultural-heritage institutions, and individual researchers "sofern sie nicht kommerzielle Zwecke verfolgen".
  - Organisations under a private company's decisive influence with preferential access to results are excluded.
  - Copies may be shared only within a closed research group or for verification.
  - Source: [§60d UrhG](https://www.gesetze-im-internet.de/urhg/__60d.html)
- **LG Hamburg 27.09.2024, 310 O 227/23 (LAION)** dismissed a photographer's claim over copies made for an AI-training dataset (§60d) — [dejure](https://dejure.org/dienste/vernetzung/rechtsprechung?Gericht=LG%20Hamburg&Datum=27.09.2024&Aktenzeichen=310%20O%20227/23)
- **OLG Hamburg 10.12.2025, 5 U 104/24** dismissed the appeal — [CMS, 12 Jan 2026](https://cms.law/de/deu/legal-updates/vervielfaeltigung-eines-fotos-fuer-erstellung-eines-ki-trainingsdatensatzes-zulaessig); [Kanzlei Plutte, 11 Dec 2025](https://www.ra-plutte.de/olg-hamburg-erlaubt-fotonutzung-fuer-ki-training/)
  - A natural-language ToS clause banning automated access and scraping was not machine-readable. Being "maschinell erfasst" is not enough; it must be capable of being "maschinell interpretiert", judged by the technology available at the time of download (2021).
  - The user relying on the exception bears the burden of proof; the rightholder has a secondary burden to show the reservation.
  - §44b covers building the dataset.
  - The case "könnte bereits anders zu entscheiden sein" with permanent storage or purely commercial use.
  - The Revision was admitted and is reportedly pending at the BGH as I ZR 281/25 — [dejure](https://dejure.org/dienste/vernetzung/rechtsprechung?Gericht=LG%20Hamburg&Datum=27.09.2024&Aktenzeichen=310%20O%20227/23)

**Screen scraping, circumvention and criminal law**
- **BGH 30.04.2014, I ZR 224/12, "Flugvermittlung im Internet".** Source: [LTO, 30 Apr 2014](https://www.lto.de/recht/hintergruende/h/bgh-urteil-izr22412-screen-scraping-flugdaten-automatisiert-auslesen-ryanair-reiseportal)
  - A flight portal's automated retrieval of Ryanair's freely accessible flight data was not unfair obstruction (§4 Nr. 10 UWG old, today §4 Nr. 4), even though terms prohibiting it were accepted by tick-box.
  - Ryanair could still market its services. Price transparency is in the public interest. A click-accepted contractual ban is not a technical barrier.
  - Overcoming technical protection "könnte zwar unlauter sein".
- Later BGH decisions cite it for the principle that circumventing protective measures is generally unfair: World of Warcraft II, I ZR 253/14 (12.01.2017) and AdBlock Plus, I ZR 154/16 (19.04.2018) — [dejure citing list](https://dejure.org/dienste/vernetzung/rechtsprechung?Gericht=BGH&Datum=30.04.2014&Aktenzeichen=I%20ZR%20224/12)
- **§202a StGB** requires data "gegen unberechtigten Zugang besonders gesichert", obtained "unter Überwindung der Zugangssicherung" — [§202a StGB](https://www.gesetze-im-internet.de/stgb/__202a.html). §§303a/303b StGB (data alteration, computer sabotage) can apply to load at denial-of-service level — [§303b StGB](https://www.gesetze-im-internet.de/stgb/__303b.html)
- **§95a UrhG** bans circumventing effective technical measures protecting protected subject matter, including §87a databases. §108b adds criminal liability — [§95a UrhG](https://www.gesetze-im-internet.de/urhg/__95a.html); [§108b UrhG](https://www.gesetze-im-internet.de/urhg/__108b.html)

**Terms of use and robots.txt**
- **AGB inclusion.** For consumers, inclusion requires an express reference, an opportunity to read the terms, and agreement — [§305(2) BGB](https://www.gesetze-im-internet.de/bgb/__305.html)
- **Platform restrictions verified on 2026-10-24:**
  - BA Nutzungsbedingungen §2a(3) bans robots, web spiders and the reading out of interfaces for data collection — [BA Nutzungsbedingungen](https://www.arbeitsagentur.de/nutzungsbedingungen)
  - LinkedIn: automated access "without the express permission of LinkedIn" is prohibited — [linkedin.com/robots.txt](https://www.linkedin.com/robots.txt). The User Agreement §8.2 bans scraping — [LinkedIn User Agreement](https://www.linkedin.com/legal/user-agreement)
  - StepStone: "Any other use of robots or failure to obey the robots exclusion standards" is prohibited — [stepstone.de/robots.txt](https://www.stepstone.de/robots.txt)
  - North Data and OpenCorporates ban scraping (Section 6).
- **Feeds meant for public use:**
  - Greenhouse: "Job Board data is publicly available, so authentication is not required for any GET endpoints" — [Greenhouse docs](https://docs.greenhouse.io/job-board.html)
  - Lever: published jobs "may be scraped by third parties" — [Lever README](https://github.com/lever/postings-api)
  - Common Crawl: crawled content can be subject to its owners' separate terms, and users must respect third-party rights — [Common Crawl Terms of Use](https://commoncrawl.org/terms-of-use)
- **robots.txt in data-protection guidance:**
  - The EDPB lists respecting robots.txt or ai.txt as a mitigating measure for scraping — [EDPB Opinion 28/2024, para 105](https://www.edpb.europa.eu/system/files/documents/2024-12/edpb_opinion_202428_ai-models_en.pdf)
  - The EDPB's draft Guidelines 03/2026 on web scraping for generative AI (adopted 7 Jul 2026; consultation to about 30 Oct 2026) treat robots.txt, ai.txt, captchas and logins as signals that negate a reasonable expectation of being scraped. They prefer targeted over untargeted scraping and require publication of the source domains — [Reed Smith, 14 Jul 2026](https://www.reedsmith.com/our-insights/blogs/technology-law-dispatch/102nbqu/edpb-web-scraping-guidelines-for-ai-making-the-impossible-possible/)

**GDPR**
- **CJEU C-621/22, KNLTB (4 Oct 2024).** A commercial interest can be a legitimate interest if not unlawful, subject to strict necessity and reasonable expectations. Sources: as cited in [EDPB Opinion 28/2024](https://www.edpb.europa.eu/system/files/documents/2024-12/edpb_opinion_202428_ai-models_en.pdf), and applied by **OLG Köln 23.05.2025, 15 UKl 2/25** (Meta AI training), which accepted Art. 6(1)(f) for public data given de-identification and an opt-out — [OLG Köln 15 UKl 2/25 (NRWE)](https://nrwe.justiz.nrw.de/olgs/koeln/j2025/15_UKl_2_25_Urteil_20250523.html)
- **EDPB Opinion 28/2024 (18 Dec 2024).** Source: [EDPB Opinion 28/2024](https://www.edpb.europa.eu/system/files/documents/2024-12/edpb_opinion_202428_ai-models_en.pdf)
  - Reliance on Art. 14(5)(b) is "strictly limited", especially for scraping (para 63).
  - Scraping can have a significant impact because of volume and indiscriminate collection (para 86).
  - Recommended measures: exclude data categories and sources, respect robots.txt and ai.txt, time limits, opt-out lists before collection (paras 104–106).
- **CNIL (June 2025).** Legitimate interest is workable with precise collection criteria, immediate deletion of irrelevant data, a published list of scraped sites, and objection before collection — [CNIL recommendations](https://www.cnil.fr/fr/recommandations-developpement-ia-interet-legitime); [Clifford Chance summary](https://www.cliffordchance.com/insights/resources/blogs/talking-tech/en/articles/2025/06/web-scraping-for-ai-development--the-cnil-builds-on-edpb-guidanc.html)
- **Dutch AP (May 2024), strict outlier.** Private-sector scraping often lacks a legal basis, and purely commercial interests are unlikely to qualify; that view is now undercut by KNLTB — [Morgan Lewis, 23 May 2024](https://www.morganlewis.com/pubs/2024/05/eu-regulator-adopts-restrictive-gdpr-position-on-data-scraping-impacting-ai-technologies)
- **LfDI Baden-Württemberg (v2.0, 17 Oct 2024).** Art. 6(1)(f) is the most suitable basis; necessity means trying anonymised or synthetic data first; reasonable expectations depend on the context of publication — [LfDI BW, Rechtsgrundlagen KI](https://www.baden-wuerttemberg.datenschutz.de/rechtsgrundlagen-datenschutz-ki/)
- **Sole traders and the media privilege.**
  - The GDPR excludes only legal persons' data, "including the name and the form of the legal person" (Recital 14), so an e.K. or "Praxis Dr. X" employer name identifies a natural person — [GDPR](https://eur-lex.europa.eu/eli/reg/2016/679/oj)
  - Handelsregister inspection is "zu Informationszwecken" — [§9 HGB](https://www.gesetze-im-internet.de/hgb/__9.html)
  - The §23 MStV media privilege covers broadcasters and "Unternehmen und Hilfsunternehmen der Presse als Anbieter von Telemedien" — [§23 MStV](https://www.gesetze-bayern.de/Content/Document/MStV-23)

**EU AI Act**
- **Annex III(4).**
  - (a) covers AI systems "intended to be used for the recruitment or selection of natural persons, in particular to place targeted job advertisements, to analyse and filter job applications, and to evaluate candidates".
  - (b) covers AI systems "intended to be used to make decisions affecting terms of work-related relationships", promotion or termination, task allocation based on individual behaviour or personal traits, and monitoring or evaluating workers' performance and behaviour.
  - Source: [AI Act Annex III](https://artificialintelligenceact.eu/annex/3/)
- **Art. 6(3).** An Annex III system escapes the high-risk class if it poses no significant risk and performs a narrow procedural or preparatory task. It is nonetheless "always … high-risk where the AI system performs profiling of natural persons" — [AI Act Art. 6](https://artificialintelligenceact.eu/article/6/)
- **Art. 50(4).** Deployers must disclose AI-generated text "published with the purpose of informing the public on matters of public interest" unless it "has undergone a process of human review or editorial control" — [AI Act Art. 50](https://artificialintelligenceact.eu/article/50/)
- **Digital Omnibus on AI: Regulation (EU) 2026/1744 of 8 Jul 2026.**
  - Published in the OJ on 24 Jul 2026; in force 27 Jul 2026.
  - New dates: **Annex III high-risk obligations 2 Dec 2027** (was 2 Aug 2026); Annex I obligations 2 Aug 2028; Art. 50 applies from 2 Aug 2026.
  - Sources: [NI Assembly EU law tracker](https://www.niassembly.gov.uk/assembly-business/brexit-and-beyond/eu-law-scrutiny-tracker/regulation-2026-1744/); [FPF AI Act timeline, Jul 2026](https://fpf.org/wp-content/uploads/2026/07/FPF-EU-AI-Act-Timeline-2026-R2.pdf); political agreement of May 2026 per [Gibson Dunn, 27 May 2026](https://www.gibsondunn.com/eu-ai-act-omnibus-agreement-postponed-high-risk-deadlines-and-other-key-changes/)

### Inferences
**Per source (lawyer review)**

| Source | Database right / TDM | Contract / ToS | Circumvention / criminal | GDPR | Overall |
|---|---|---|---|---|---|
| BA Jobsuche backend | Likely a §87a database (OLG Köln: public funding doesn't exclude protection); daily full harvests copy a substantial part, so §87c(1) Nr. 4/5 is needed for the copying; re-publishing ads not covered | **Explicit ban** in Nutzungsbedingungen §2a(3), applying to all visitors | Static public client ID; do not work around any future authentication or 403 blocks | Strip contact persons from descriptions | **High** without BA permission |
| ATS public feeds | Employer-created data; low database-right risk when used as intended | Vendor terms not reviewed; could exclude commercial TDM (§87c(6)) | None if public endpoints only | Drop recruiter fields | **Low** |
| Employer career pages (schema.org) | §44b after checking robots.txt, TDMRep and explicit TDM reservations | Browsewrap terms weak (no assent) | None | Sole-trader employers = natural persons | **Low–medium** |
| Common Crawl extracts | New reproduction by you; source sites' reservations persist; job-board pages inside Common Crawl carry board risk | CC terms: respect third-party rights | None | As above | **Medium** |
| Job boards (StepStone, Indeed, LinkedIn) | Core CV-Online / OLG Köln scenario; bulk metadata harvests can be §87b(1) S.2 extraction | Robot bans; clickwrap if logged in | Captcha solving, IP rotation and login use are high-risk (§95a/108b UrhG, §202a StGB, UWG per BGH WoW II) | Respect robots.txt and logins (EDPB) | **High** |
| Registers (Handelsregister, Unternehmensregister, insolvency notices) | Mostly facts; §5 UrhG for official notices | Handelsregister: 60/h, no mirroring; North Data and OpenCorporates ban scraping | Bundesanzeiger captcha: do not bypass | Director names not needed; insolvency of sole traders = personal data | **Medium** (limits, not copyright) |

**Design rules that follow**
- **Publish derived data, not copies.** Publish derived indicators and aggregates with links out, never mirrors or searchable copies of ads. The TDM exceptions cover reproduction only, and a substitute search interface is what CV-Online and OLG Köln weighed against the aggregator.
- **Check reservations and delete raw copies.** Before each crawl, check for and log machine-readable reservations (robots.txt, TDMRep, `tdm-reservation`). Treat explicit natural-language TDM reservations as binding for current crawls (OLG Hamburg's "machine-interpretable by today's technology" test). Delete raw copies after feature extraction, as §44b(2) requires and GDPR storage limitation supports.
- **Never circumvent.** Never solve captchas, rotate IPs to evade blocks, use logins, or reuse other tenants' API keys.
- **GDPR setup.** Document a legitimate-interest assessment, strip personal data at ingestion, publish a source list and transparency page with an objection channel, and decide how sole-trader employers are handled. Scoring them is profiling of natural persons (see Section 8).
- **AI Act.** A scorer of postings or employers for job seekers is probably not Annex III(4): it does not recruit, select, target or filter natural persons, nor decide on work relationships.
  - This changes if a job board uses the score to target ads to job seekers or to make decisions about individuals.
  - If the dashboard publishes LLM-written summaries on matters of public interest, Art. 50(4) disclosure applies unless there is editorial review.
- **§60d** only helps a non-commercial research operator. A sponsor such as an HR-tech firm or job board with decisive influence and preferential access would destroy eligibility.

### Gaps
- **CJEU primary texts** could not be fetched (EUR-Lex bot challenge; InfoCuria is JavaScript-only). Not verified against primary text:
  - CV-Online paragraph numbers beyond 31 and 41, and whether Melons' metadata was specifically schema.org microdata;
  - the operative wording of Innoweb, Ryanair and KNLTB.
- **LAION (LG Hamburg):** the obiter on natural-language reservations is not verified. **BGH I ZR 224/12** and **I ZR 159/10** are known from summaries, not full texts.
- **Not found or not verified:**
  - any German ruling on browsewrap terms binding scrapers, or on the legal effect of robots.txt outside §44b;
  - any DSK or other German DPA statement specific to scraping;
  - whether the Dutch AP updated its position after KNLTB.
- **Not verified (from the legal subagent's background knowledge):**
  - the SCHUFA ruling (C-634/21, 7 Dec 2023) on Art. 22 and scores relied on by third parties;
  - CJEU C-92/09 Schecke on legal persons' names;
  - the Bisnode (Poland 2019) Art. 14 decision.
- **OLG Köln 6 U 75/25** is a preliminary-injunction ruling (no Revision to the BGH); the status of the main proceedings is unknown. Whether the BA Jobbörse is a §87a database, and whether §5 UrhG or open-data law (DNG, §12a EGovG) affect it, is untested.
- **EDPB Guidelines 03/2026** are a draft; the final text is expected after the consultation closes (about 30 Oct 2026). Omnibus details (Art. 4 AI literacy, Art. 6(4)/49 registration) are not checked against the OJ.
- **Terms not reviewed:** ATS vendor terms (Personio, Greenhouse and others) that could contractually exclude commercial TDM.

## 8. Legal constraints on publishing: labelling named companies or postings as likely ghost jobs (Unternehmenspersönlichkeitsrecht, §824 BGB, §§823/1004 BGB, UWG §4 Nr. 1–2, rating-portal case law) and how to frame scores

### Takeaway
Naming companies is defensible in Germany when the label is presented as a **transparent, methodologically sound evaluation (Werturteil) resting on true, documented facts**. It becomes risky when it reads as a **factual allegation that cannot be proven**, such as "fake job", "no intention to hire" or "collects applicant data". Such allegations can trigger:
- injunctions and retraction (§§823(1), 1004 BGB analogous)
- damages for credit endangerment (§824 BGB), which protects only against untrue facts
- §823(2) BGB with §186 StGB
- where the operator competes with the named party, UWG §4 Nr. 2, which puts the **burden of proving truth on the speaker**

BGH case law on credit ratings, Yelp's algorithmic review filter, rating portals (spickmich, Jameda, hotel portals, kununu) and comparative product tests ("Warentest") supplies a practical template:
- neutrality, expertise and genuine effort at objectivity
- a "vertretbar" (defensible) and consistently applied methodology
- an accurate factual basis
- transparency about the method
- a complaint, verification and reply procedure

No court decision on algorithmic "ghost job" labels was found, so this framing is an analogy and needs lawyer review.

### Cited Findings
**Statutory bases**
- §824(1) BGB (Kreditgefährdung): whoever asserts or disseminates an untrue fact ("der Wahrheit zuwider eine Tatsache behauptet oder verbreitet") that can endanger another's credit or harm their earnings or advancement must compensate the damage, even without knowing of the untruth if they should have known. §824(2): no damages for a communication whose untruth was unknown to the communicator if the communicator or the recipient has a legitimate interest in it — [§824 BGB](https://www.gesetze-im-internet.de/bgb/__824.html)
- UWG §4 Nr. 1: it is unfair to disparage or denigrate ("herabsetzt oder verunglimpft") the marks, goods, services, activities or personal or business circumstances of a **competitor**. §4 Nr. 2: it is unfair to assert or disseminate facts about a competitor's goods, services or business, or its management, that can damage the business or credit, "sofern die Tatsachen nicht erweislich wahr sind" (unless the facts are provably true) — [§4 UWG](https://www.gesetze-im-internet.de/uwg_2004/__4.html)
- UWG scope:
  - A "geschäftliche Handlung" is conduct in favour of one's own or another's business that is "unmittelbar und objektiv" connected with promoting sales or purchases of goods or services.
  - A "Mitbewerber" is any business in a "konkreten Wettbewerbsverhältnis" (concrete competitive relationship) with another as supplier or buyer of goods or services.
  - Source: [§2 UWG](https://www.gesetze-im-internet.de/uwg_2004/__2.html)
- Unternehmenspersönlichkeitsrecht:
  - Not codified; derived from Art. 2(1) with Art. 19(3) GG. It protects the company's social standing ("sozialen Geltungs- und Achtungsbereich") and is weaker than individuals' personality rights.
  - Companies, especially large ones, must tolerate more criticism. Untrue factual claims and Schmähkritik fall outside the protection of free speech; true factual claims must generally be tolerated; potentially harmful opinions need case-by-case balancing in which "das schwache Unternehmenspersönlichkeitsrecht der stark geschützten Meinungsfreiheit gegenübersteht".
  - Remedies: injunction, retraction or correction, damages. Cited decisions: BGH VI ZR 102/85 (03.06.1986), BVerfG 1 BvR 737/94 (03.05.1994).
  - Source: [WBS legal, Unternehmenspersönlichkeitsrecht](https://www.wbs.legal/medienrecht/persoenlichkeitsrecht/unternehmenspersoenlichkeitsrecht)

**Ratings and scores as opinions: BGH, 22.02.2011, VI ZR 120/10 (credit rating index)**
- A credit-rating number is generally an evaluation based on facts. The facts feed into the value judgment according to set criteria but do not thereby become factual claims. It becomes a factual claim only when, from the recipient's perspective, the evaluative elements recede behind the underlying facts (paras. 10–11).
- §824 BGB requires untrue facts, not mere value judgments (para. 9).
- Claims under §823(1) BGB (interference with the business) "scheiden grundsätzlich aus" if the rating is an opinion "auf einer zutreffenden Tatsachengrundlage". If the opinion rests on incorrect underlying facts, a claim may arise (paras. 13, 22).
- The rated index combined 15 differently weighted features with insolvency and sector analysis, and contained a prognosis (para. 16).
- Source: [BGH VI ZR 120/10 via rewis](https://rewis.io/urteile/urteil/ixg-22-02-2011-vi-zr-12010/)

**Algorithmic selection: BGH, 14.01.2020, VI ZR 496/18 (Yelp)**
- Yelp's software automatically classifies reviews as "recommended" or "not recommended", and the star average uses only recommended reviews. The BGH found no untrue factual claim under §824 BGB, because readers understand that the average is based only on recommended reviews.
- No unlawful interference with the business: the display and sorting are protected "durch die Berufs- sowie Meinungsfreiheit". A business "muss Kritik an seinen Leistungen und die öffentliche Erörterung geäußerter Kritik grundsätzlich hinnehmen".
- Yelp had explained its use of automated software on the platform.
- Source: [Kanzlei Plutte on BGH VI ZR 496/18](https://www.ra-plutte.de/bgh-plattform-yelp-bewertungen-selektieren-aussortieren/)

**Comparative tests ("Warentest" doctrine): LG München I, 19.01.2023, 26 O 15365/21 (AfP 2023, 80)**, applying BGH 09.12.1975 VI ZR 157/73 and BGH 17.06.1997 ("Druckertest")
- A comparative test that negatively evaluates a company's products touches the right to the established business (Gewerbebetrieb). It is "regelmäßig zulässig" as an exercise of Art. 5(1) GG if the underlying investigations were designed and carried out "neutral, sachkundig und im Bemühen um objektive Richtigkeit", and both the test procedure and the conclusions drawn appear "vertretbar, dh diskutabel" (Leitsatz 2, para. 32).
- The tester has "ein erheblicher Entscheidungsfreiraum" in choosing methods, test objects and presentation (para. 32).
- "Objectivity" means an effort towards objective correctness, not correct results. Methods must be defensible, results must not be presented in a distorting or misleading way, and the selection must permit a meaningful comparison and respect equal treatment (para. 36).
- Test reports are generally value judgments. Individual factual statements with independent significance are judged as factual claims under §824 BGB (para. 24).
- The court noted that the manufacturer had received the test programme in advance, participated in an advisory-board meeting and received pre-notification of its results. Objections it failed to raise then were held against it (paras. 7–8, 16, 46).
- The standard is formulated for situations "außerhalb von … Wettbewerbsverhältnissen" (outside competitive relationships) (para. 32).
- Source: [LG München I, 26 O 15365/21 (gesetze-bayern.de)](https://www.gesetze-bayern.de/Content/Pdf/Y-300-Z-BECKRS-B-2023-N-1236?all=False)

**Rating portals**
- **spickmich, BGH 23.06.2009, VI ZR 196/08.** Teacher ratings are permissible: they are personal data, but the right to free exchange of opinions outweighed the teacher's informational self-determination because the criteria concerned professional conduct. The limit is Schmähkritik and formal insult. The BGH stressed that the ruling was case-specific and not transferable to all portals. The BVerfG did not accept the constitutional complaint (1 BvR 1750/09, 16.08.2010) — [WBS legal on spickmich](https://www.wbs.legal/urheberrecht/bundesgerichtshof-entscheidet-ueber-die-zulaessigkeit-einer-lehrerbewertung-im-internet-wwwspickmichde-967/); [LTO on BVerfG](https://www.lto.de/recht/nachrichten/n/bverfg-causa-spickmichde-geschlossen)
- **Jameda, BGH 20.02.2018, VI ZR 30/17.** Jameda lost its position as a "neutral information intermediary" by favouring paying premium doctors (competitor ads shown on non-paying doctors' profiles but not on premium profiles), so a non-paying doctor could demand deletion of her profile. **BGH 01.03.2016, VI ZR 34/15** ("Jameda II") had set out the operator's verification duties after complaints — [Otto Schmidt on VI ZR 30/17](https://www.otto-schmidt.de/news/wirtschaftsrecht/arztebewertungsportal-jameda-bgh-bewilligt-loschungsanspruch-mangels-neutraler-informationsvermittlung-2018-02-20.html); [Rose & Partner](https://www.rosepartner.de/blog/jameda-kein-neutraler-informationsvermittler.html)
- **Hotel portal, BGH 09.08.2022, VI ZR 1244/20.** A rated business's simple objection that a review lacks any guest contact generally suffices to trigger the portal's duty to verify, with a secondary burden of presentation on the portal. If the portal does not verify, the lack of contact is treated as true and the review is unlawful. The basis is §1004(1) sentence 2 analogous with §823(1) BGB and Art. 2(1), 19(3) GG — [LTO](https://www.lto.de/recht/nachrichten/n/bgh-vi-zr1244-20-online-bewertung-hotel-darlegungslast-kontakt-kunden-gaeste); [Otto Schmidt](https://www.otto-schmidt.de/news/zivil-und-zivilverfahrensrecht/bewertung-ohne-gastekontakt-entsprechende-ruge-des-bewerteten-hat-prufpflicht-des-hotelbewertungsportals-zur-folge-2022-09-06.html)
- **kununu (employer reviews).**
  - OLG Hamburg 08.02.2024, 7 W 11/24 (summary proceedings): an employer can demand deletion when the portal does not identify the reviewer sufficiently for the employer to check whether an employment relationship existed. Anonymised proof checked only by kununu was not enough — [WBS legal](https://www.wbs.legal/it-und-internet-recht/datenschutzrecht/olg-hamburg-kununu-muss-identitaeten-offenlegen-oder-bewertungen-loeschen-72512/); [Heuking](https://www.heuking.de/de/news-events/newsletter-fachbeitraege/artikel/offenlegung-der-identitaet-des-bewerters-bei-kununu.html)
  - Main proceedings (LG Hamburg 324 O 315/24; OLG Hamburg 7 U 8/25, indicative order reported 2026-07-29): no duty to reveal real names, but kununu must make the reviewer identifiable enough for the employer to verify the business contact, otherwise delete the review and prevent republication; kununu is liable as indirect interferer. kununu withdrew its appeal, so the LG judgment is final, and **there is still no BGH ruling on this point** — [beck-aktuell, 2026-07-29](https://www.beck-aktuell.de/heute-im-recht/rechtsprechung/olg-hamburg-7u825-arbeitgeber-bewertungsportale-klarnamen-2026-07-29)
- **Employer review as opinion, BGH 11.03.2025, VI ZB 79/23.** A negative employer review of a law firm was classified as a value judgment ("Im Zweifel" an opinion, in the interest of effective protection of fundamental rights). Disclosure of user data under §21(2) TDDDG requires one of the listed offences, and §§186/187 StGB are ruled out for value judgments. The statement was permissible criticism because its factual elements were true (former employees had needed court action to obtain pay and a reference) — [zm-online on BGH VI ZB 79/23](https://www.zm-online.de/artikel/2025/zm-2025-10/im-zweifel-ist-es-eine-meinungsaeusserung)

**Suspicion statements ("Verdachtsberichterstattung")**
- BGH case law (e.g. VI ZR 262/21 of 20.06.2023, VI ZR 1241/20) sets cumulative requirements for publicly voicing a suspicion about an identifiable party: a minimum stock of supporting facts ("Mindestbestand an Beweistatsachen"), no prejudgment, normally obtaining the affected party's comment before publication, and a matter of sufficient weight to justify public interest. Media are held to stricter research duties than private persons — [WBS legal on VI ZR 262/21](https://www.wbs.legal/medienrecht/botschafter-geht-gegen-spiegel-und-mdr-vor-bgh-schaerft-voraussetzungen-zulaessiger-verdachtsberichterstattung-68672/); [Taylor Wessing](https://www.taylorwessing.com/de/insights-and-events/insights/2023/10/bgh-identifizierende-verdachtsberichterstattung)
- Recent application: OLG München 31.03.2026, 18 U 3853/25 Pre, citing BGH VI ZR 367/15 (16.02.2016), BGH VI ZR 1175/20 (22.02.2022), BVerfG 1 BvR 573/25 (03.11.2025) and 1 BvR 584/25 (09.12.2025). The court noted that the affected person had been asked to comment before publication — [Otto Schmidt, 2026-04-07](https://www.otto-schmidt.de/news/wirtschaftsrecht/verdachtsberichterstattung-voraussetzungen-fur-den-mindestbestand-an-beweistatsachen-2026-04-07.html)

### Inferences
**Risk analysis**
- **Main risk vector.** The words "ghost job", "Geisterstelle", "Fake-Stelle" or "Scheinausschreibung" can be read by the average reader as the factual claim that the employer publishes vacancies it does not intend to fill, i.e. deception. Intent is hard to prove. If the label is read that way, §824 BGB, §823(2) BGB with §186 StGB, and injunction claims are realistic, and the operator would have to substantiate the claim. Labels describing observable behaviour avoid this ("stale", "repeatedly reposted", "no salary stated", "open longer than 95% of comparable postings").
- **Probabilistic wording helps but does not immunise.** Under VI ZR 120/10 a score is an opinion only while the evaluative element dominates. A label such as "80% probability that this job is fake" could be read as a factual or suspicion statement. The Verdachtsberichterstattung requirements are a prudent benchmark for any company-level "likely ghost job" label, even though they were developed for the press: minimum factual basis, no prejudgment, opportunity to comment, sufficient public interest.
- **UWG exposure depends on the business model.** A non-commercial research dashboard is unlikely to be a "geschäftliche Handlung" towards rated employers. If the operator runs a job board, recruiting service, ATS or HR-analytics business, statements about competing job boards, ATS vendors or recruiters are likely to fall under §4 Nr. 1–2 UWG. Under Nr. 2 the operator must prove the truth of the facts, with competitor standing to sue. Rating other job boards' "ghost share" is therefore the highest-risk publication for a commercial operator.

**Framing checklist** (derived from the case law above; lawyer review recommended)
1. **Publish facts first, verdicts second.** Show the verifiable observations behind every label, e.g. "first seen 2026-03-02, re-published 4×, start date 'ab sofort' for 200 days, no pay information, not found on the employer's careers page on 2026-10-20". Keep timestamped snapshots as evidence: true facts must generally be tolerated, and §4 Nr. 2 UWG and §186 StGB turn on provability.
2. **Present the score as the operator's evaluation** ("our indicator", "Einschätzung", e.g. "Ghost-risk indicator: high"), computed from disclosed criteria and weights, in the style of a credit-rating index (VI ZR 120/10). Avoid accusations of intent or illegality.
3. **Meet Warentest-style quality standards.** Neutral, expert, effort at objectivity, defensible ("vertretbar") methods, applied equally to all employers. Avoid one-sided selection (e.g. only naming firms in a particular dispute), and document validation and error rates.
4. **Be transparent about the method,** as Yelp was: publish the methodology, data sources, known false-positive patterns (e.g. evergreen pools, multi-location retail and staffing postings, apprenticeship cycles) and the date of each data snapshot.
5. **Stay neutral (Jameda).** Do not sell rated employers ways to improve their scores or premium placement. If you monetise, disclose it and keep it strictly separate.
6. **Run a complaint, verification and reply process,** analogous to portal duties (VI ZR 34/15, VI ZR 1244/20, kununu) and the Warentest pre-notification. Let employers flag errors and add a statement (e.g. "position is genuinely open; hiring continues"). Re-check promptly and correct or remove labels. Consider pre-notifying named employers before first publication.
7. **Aggregate before naming.** Publish sector, region and occupation-level rates by default. Name employers only above evidence thresholds (e.g. several independent signals over a minimum observation period), and consider not naming small firms and sole traders, whose names are personal data (spickmich treated ratings of identifiable persons as personal data).
8. **Avoid republishing third-party reviews.** Do not republish kununu or Glassdoor review texts. If F8 data is used, use licensed aggregates. Adopting third-party statements as one's own ("zu eigen machen") would import the reviewers' liability risks and the verification duties described above.

### Gaps
- No German decision on algorithmic labels of job postings or employers as "ghost", "fake" or "phantom" jobs was found. Two questions are untested in court:
  - whether courts would treat a probabilistic classifier output as an opinion (like a credit index) or as a suspicion statement;
  - whether "ghost job" in German usage implies deception.
- Not researched because the search budget ran out:
  - the doctrine on "Prangerwirkung" (pillory effect: publishing even true facts in a shaming list)
  - the classification of statements about a company's intentions ("innere Tatsachen") as facts
  - journalistic due-diligence duties under the Medienstaatsvertrag if the dashboard is editorial
  - whether GDPR Art. 22 or CJEU C-634/21 (SCHUFA scoring) could matter where rated entities are sole traders. Section 7 establishes that scores about sole-trader employers are profiling of natural persons (Recital 14 GDPR); the SCHUFA point itself is unverified.
- The facts of the Jameda II (VI ZR 34/15) verification steps were not re-read in the primary text.
- **A media or IT lawyer should review** the wording of labels, the complaint process, and the UWG position given the operator's actual business model.

## 9. Which sources feed which candidate ghost-job features (summary map)

### Takeaway
On the verified evidence, the **BA Jobsuche data** covers F1, F3, F4 and F5 best, and partly F2 and F6. It is also the most contractually restricted source. **Employer ATS feeds** and **schema.org markup on career sites** are the cleanest sources for F1 and F2. **BA statistics** supply the baselines: occupation medians of vacancy duration, and evidence of postings that are never deregistered. For the remaining features (Section 6):
- **F6:** the denominator comes from average employee numbers in annual accounts (Unternehmensregister/Bundesanzeiger), under tight access limits.
- **F7:** feasible from insolvency and register notices plus licensed funding data.
- **F8:** no lawful bulk source was identified.

### Cited Findings
- **BA Jobsuche fields and facets:** first publication date, modification timestamp, `veroeffentlichtseit`, start date, salary type, `zeitarbeit`, `pav`, `externestellenboersen`, employer hash — [BA Jobsuche v6 response, 2026-10-24](https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs?size=1&page=1); [issue #69](https://github.com/bundesAPI/jobsuche-api/issues/69)
- **ATS date and ID fields:**
  - Personio `createdAt` — [Personio XML](https://personio.jobs.personio.de/xml)
  - Greenhouse `first_published`/`updated_at`/`application_deadline`/`requisition_id`/`pay_input_ranges` — [Greenhouse docs](https://docs.greenhouse.io/job-board.html)
  - Lever `salaryRange` — [Lever README](https://github.com/lever/postings-api)
  - SmartRecruiters `releasedDate`/`refNumber` — [SmartRecruiters API](https://api.smartrecruiters.com/v1/companies/smartrecruiters/postings?limit=1)
  - Ashby `publishedAt`/`compensation` — [Ashby API](https://api.ashbyhq.com/posting-api/job-board/ashby?includeCompensation=true)
- **schema.org fields:** `datePosted`, `validThrough`, `jobStartDate`, `jobImmediateStart`, `baseSalary`, `directApply`, `identifier` — [schema.org/JobPosting](https://schema.org/JobPosting); [Google job posting docs](https://developers.google.com/search/docs/appearance/structured-data/job-posting)
- **BA baselines:** median Vakanzzeit by occupation; the share of vacancies closed after more than 1,000 days rose from 0.1% to 1.5% (2016–2025) — [BA Engpassanalyse](https://statistik.arbeitsagentur.de/DE/Navigation/Statistiken/Interaktive-Statistiken/Fachkraeftebedarf/Engpassanalyse-Nav.html); [BA Hintergrundinfo, Aug 2026](https://statistik.arbeitsagentur.de/DE/Statischer-Content/Grundlagen/Methodik-Qualitaet/Methodenberichte/gemeldete-Arbeitsstellen/Generische-Publikationen/Hintergrundinfo-Medianvakanzzeiten-in-der-Statistik-der-gemeldeten-Arbeitsstellen.pdf)
- **Arbeitnow `created_at`** — [Arbeitnow API](https://www.arbeitnow.com/api/job-board-api)
- **Company-data constraints:**
  - Handelsregister: 60 searches or views per hour, systematic mirroring banned — [Registerportal information](https://www.handelsregister.de/rp_web/information/welcome.xhtml)
  - Small companies must still state employee numbers — [§288 HGB](https://www.gesetze-im-internet.de/hgb/__288.html)
  - Insolvency notices deleted about six months after proceedings end — [§3 InsoBekV](https://www.gesetze-im-internet.de/insobekv/__3.html)
  - Mass-layoff notices not public — [§17 KSchG](https://www.gesetze-im-internet.de/kschg/__17.html)
  - LinkedIn scraping banned — [LinkedIn User Agreement](https://www.linkedin.com/legal/user-agreement)

### Inferences
Mapping, based on the findings above ("unverified" = depends on Section 5–6 gaps):

| Feature | Verified sources and fields | Unverified or likely sources | Legal risk of collection |
|---|---|---|---|
| F1 posting age and reposts | BA `datumErsteVeroeffentlichung`, `veroeffentlichungszeitraum.von`, `aenderungsdatum`; Personio `createdAt`; Greenhouse `first_published` + `requisition_id` (not `updated_at`, which bulk edits change); Lever `createdAt` (undocumented); SmartRecruiters `releasedDate`/`jobId`; Workday `startDate` (= posting date) + `jobReqId`; Recruitee `published_at`/`close_at`; Ashby `publishedAt`; JOIN JSON-LD `datePosted`; schema.org `datePosted`/`validThrough`; Arbeitnow `created_at`; BA median Vakanzzeit as baseline | Board "reposted" labels (LinkedIn), Adzuna `created`, Common Crawl history | BA: high (ToS); ATS: low; schema.org: low–medium; boards: high |
| F2 own careers site vs aggregators only | ATS feeds and schema.org on the employer domain (own channel; Greenhouse `absolute_url`, Workday `externalUrl`) vs BA `externestellenboersen`/`allianzpartnerName`, Arbeitnow, Adzuna (aggregators). Note: JOIN multiposts active jobs to boards by default | Indeed, StepStone, LinkedIn presence (would need licensed access) | Boards: high |
| F3 gap between posting and start date | BA `eintrittszeitraum.von` (caveat: about 78% have start ≤ today, likely "ab sofort"); schema.org `jobStartDate`/`jobImmediateStart`. No ATS feed exposes an employment start date | Text parsing of ATS descriptions | as above |
| F4 salary stated | BA `verguetung` facet/`verguetungsangabe` (≈21.6% structured); Greenhouse `pay_input_ranges`; Lever `salaryRange`; Ashby `compensation`; Recruitee/softgarden `salary`; schema.org `baseSalary` (not `estimatedSalary`) | Adzuna salary fields (exclude predicted) | as above |
| F5 staffing-agency flag | BA `zeitarbeit` (≈21%) and `pav` (≈8.4%) | Name lists of agencies (e.g. top BA posters such as TimePartner, Randstad) | BA: high |
| F6 posting volume vs headcount | Numerator: BA `arbeitgeber` facet/`arbeitgeberKundennummerHash`, ATS feed counts. Denominator: average employee numbers in annual accounts (Unternehmensregister FY2022+, Bundesanzeiger earlier). Small firms must state them; micro firms can avoid it; 1–2-year lag | North Data XL+ financials (licensed). LinkedIn headcount is off-limits (User Agreement §8.2) | Handelsregister: 60 searches/views per hour, no mirroring. Bundesanzeiger: captcha (do not bypass). Licensed data restricts resale and display |
| F7 funding, layoffs, insolvency | insolvenzbekanntmachungen.de (query per day; notices deleted about 6 months after proceedings end); Unternehmensregister insolvency and capital-market notices; startupdetector (German funding rounds, licensed); GDELT and layoffs.fyi (free with attribution) | Crunchbase (needs display rights in the Order Form), Dealroom, EQS ad-hoc news. §17 KSchG mass-layoff notices are not public | Official notices: low (no automated-access clause found; §5 UrhG). Commercial data: contract terms |
| F8 application-experience reviews | No lawful bulk source identified. kununu hosts applicant reviews but no API was found; Glassdoor merged into Indeed on 1 Jul 2026 | Licensed or partnered data only | High (terms unverified; review-authenticity case law, Section 8) |

### Gaps
- Coverage overlap between the BA, ATS feeds and boards (what share of BA postings has an ATS counterpart) has not been measured; a pilot sample would establish it.
- Open items for F6–F8 (Bundesanzeiger terms, Unternehmensregister bulk interface, kununu and Glassdoor terms and fields) are listed under Section 6 Gaps.
