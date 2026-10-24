# Ghost Job Radar

A local web app that flags likely "ghost jobs" in the German job market: postings that do not correspond to a
genuinely open, externally fillable role. It turns the findings of
[`reports/Ghost job signals in Germany.md`](reports/Ghost%20job%20signals%20in%20Germany.md) into a working
scoring pipeline and dashboard.

## What it does

| View | What you enter | What you get |
| --- | --- | --- |
| **Overview** | Nothing: it opens with everything stored so far | The radar (every job as a blip, distance = time online against the occupation's norm), grade split, the jobs that need a closer look, top employers and cities, sources, publication months and ghost patterns |
| **Check a posting** | A job link, the pasted ad text, or one click in the browser extension on LinkedIn, Indeed, StepStone, XING or the BA job board (it reads applicant counts and "Reposted" labels) | Ghost-risk grade, the observable facts behind it, which of the five ghost types it resembles, your chances (applicants against the applications per hire typical for the field), verification tips and a suggested application effort |
| **Company** | An employer name (or its careers-page URL) | Every posting from the employer's own job feed and its platform copies, an employer grade adjusted for sample size, team builds, news, and what you know: your notes (for example "internal candidates usually get the jobs"), your application outcomes, and size, growth and funding against the openings |
| **City map** | A city, an optional keyword and a radius | Postings on a map, each marked with its grade (colour plus shape plus glyph), a grade distribution and a table view |
| **Watchlist** | Companies or cities to track | Automatic re-checks every 12 h while the app runs, so reposts, removals and long lifetimes become visible over time |
| **Model** | Audits of sampled postings, plus the outcomes you record | Gold labels, an audit queue with the question to ask the employer, a calibrated model judged against the expert score, survival curves and an estimate of the share of postings that are not genuinely open |
| **How it works** | Your settings: when age starts to count, your applicant thresholds, the history window | The grades, the three verdicts, the five patterns, every signal with its points, and the data sources |

### Interactive views

Hovering opens a floating window everywhere, and keyboard focus works the same way. Clicking opens the full
analysis.

| Visual | What it shows |
| --- | --- |
| Radar (overview) | Every stored job as a blip: distance from the centre = time online ÷ typical advertising time for its occupation (rings at 1×–3×, outer band 4× and more), sector = where it was found (employer site, LinkedIn, Bundesagentur, other boards), shape and colour = grade |
| Score meter and build-up | The 0–100 score as a needle over the four grade bands, and every observable fact as a bar that adds (red) or removes (blue) points |
| Effort scale | Where the suggested application effort sits between "tailored" and "skip" |
| Age bullet | Days online against the typical window, with a tick at each multiple of the norm |
| First published | Jobs per month of first publication (overview and company view) |
| Age-vs-norm chart | One mark per job: time online ÷ typical advertising time for its occupation (Bundesagentur baseline), in lanes by grade |
| Map | Grade markers (colour + shape + glyph). Hovering previews the job and highlights its table row; clicking opens it |
| Who posts the most | Employers by open jobs, split by grade. Clicking analyses that employer |
| Where postings come from | Jobs per source, plus Bundesagentur facts for the search area (partner-board share, private recruiters, largest advertisers) |
| Departments | Open roles per department; team builds (3+ new roles in 90 days) highlighted |
| "Seen on" chips | Every copy of a job (employer feed, LinkedIn, Bundesagentur, …) with its dates; removed copies struck through |
| Lifecycle timeline | Each copy over time, against the typical window for the occupation, with start date, expiry, deadline and captured applicant counts |
| Progress panel | Every check, company and city search runs as a background task with live steps (each source, merging, scoring) |
| Evidence strip | Which of seven kinds of evidence a verdict rests on: age vs. norm, reposts and copies, employer's own site, news, applicants, wording, track record |
| Self-updating news | Company news loads in the background and fills in on its own; scores update when layoffs, insolvency or funding turn up |
| Background enrichment | After a city search the radar looks for the top employers' own job feeds (accepted only if they contain a known job) and refreshes the results |

Each job appears once: copies on several platforms are merged into one entry, and its chips list all of them.
The city filters (posted within, job type, remote, hide staffing agencies, sources) are passed to every source
that supports them.

### Three verdicts, kept apart

A company can be actively hiring and still go silent on candidates, so every posting gets three verdicts, each
with its evidence confidence and the dated observations behind it:

| Verdict | Question | Evidence |
| --- | --- | --- |
| Ghost-risk (vacancy activity) | Is the position inactive, speculative, filled or unapproved? | Age against the occupation norm (from 1× the typical time, adjustable), reposts, the employer's own site, wording (pool, internal, "vorbehaltlich der Budgetfreigabe", project awards), your notes and dated events, news, contracts won, size and funding |
| Your chance | If the job is real, can you get it? | Applicants (exact, "over 200", "fewer than 25", clicks shown apart) against the applications per hire for the field, your own thresholds (default 100 and 200), applicants per day, internal hiring, your interview record at the employer |
| Communication risk | Does the employer answer? | Your recorded applications: no substantive reply within 30 days of applying or of the interview counts as silence, a rejection counts as a reply, withdrawn and recent applications stay out; shown by stage with a 90% interval and the sample size. It describes your experience, not a company-wide rate |

History is limited to your window (past week, month, three months or year, never more than a year): news, contracts,
funding, your events and outcomes, survival lifetimes and model labels. Jobs outside Germany are left out.

### What you know counts, labelled as yours

The company view has panels for knowledge the radar cannot see from outside:

| Panel | What it changes |
| --- | --- |
| Your notes | "Internal candidates usually get the jobs" adds 16 points and the "internal favourite" type to every posting of the employer, shown as your note. One note is one signal, so it never reaches the highest grade on its own. Notes can also be set from any posting, listed on the Watchlist page and imported as `company;practice;note` lines |
| Application outcomes | Stage reached, response, days to response, the date an update was promised, unanswered follow-ups, withdrawal. Internal hires (+10 to +20) and no interviews from 4+ answered applications (+10) raise the employer's postings; interviews in 30% or more lower them. The same records give the communication risk |
| Dated events you know of | Hiring freeze, restructuring, hiring manager left, recruiter reassigned, project cancelled (+12 while the employer keeps advertising); contract won, expansion, confirmed new starters (−3 to −6) |
| Public contracts won | Contract awards from German buyers in the EU procurement journal TED within the window (−4: work that could need staff) |
| Size, growth and funding | Employees now and a year ago, last funding round, and the share of closed jobs that closed within the typical time (likely filled; a removal is not proof of a hire). Openings beyond what the company can plausibly fill (employees × (15% replacement + growth) × 86 days ÷ 365) raise the score; shrinking only counts together with distress news, because shrinking firms still replace leavers (IAB) |

Employer-wide evidence is not capped for postings younger than 21 days, because it does not need time to show. The
radar also flags ads that depend on a project, contract or grant award ("vorbehaltlich der Auftragsvergabe", "bei
Zuschlag", "subject to funding"), and it fills in the ad texts of Bundesagentur copies that came from search results
without text. LinkedIn copies stay without text: linkedin-jobs-mcp offers search only.

Applicant counts give "your chances": 100+ applicants is high competition and 200+ very high in any field, and
fields with few applications per hire (care, social work: about 8) reach high sooner. Very high competition lowers
the suggested effort by one step.

### How the radar learns

The Model view follows the validation design in the research report:

- **Survival baselines.** Kaplan–Meier lifetimes for groups of comparable jobs, with jobs still online censored, jobs
  first seen when already online left-truncated and removals between two checks at the midpoint. Once a group has 20
  observed closures, its tail probability S(age) is used.
- **Ground truth.** Audits (ask the employer whether the post is approved and filled from outside) and outcomes that
  say something about the job (interview, offer, internal candidate chosen). Each label stores the posting's
  features at that moment, so training never sees hindsight.
- **Weak labels.** Labelling functions (cosmetic reposts, extreme age, copies outliving the employer's listing,
  talent-pool wording) are combined in a label model. They help choose what to audit and never train the model,
  which would make it circular.
- **Audit sample.** Drawn per grade with probability proportional to age; each audit keeps its inclusion probability,
  so the audits give a design-weighted estimate of the share of postings that are not genuinely open.
- **Calibrated model.** Bayesian logistic regression with the expert score as its prior. It needs 12 labels with at
  least 4 of each class, and it is judged out of fold by Brier score, log loss, ROC AUC, precision at a 20% review
  budget and calibration, next to the expert score and the base rate. Each posting then shows the model's estimate
  with a 90% interval.

### Five ghost types instead of one verdict

| Type | Typical traces the radar looks for |
| --- | --- |
| Possibly filled or abandoned | Gone from the employer's own feed while copies stay online, far older than the occupation's norm, start date, expiry or application deadline long past |
| Candidate pool | Staffing-agency and client postings, "Talentpool" or "Initiativbewerbung" wording, unchanged periodic reposts |
| Formal posting, internal favourite likely | Internal-posting wording, public employer, reference number with deadline, unusually narrow requirement profile |
| Hiring possibly frozen | Layoff, insolvency or hiring-freeze news while the employer keeps advertising; a job board that never changes |
| Signalling or CV collection | Far more openings than plausible hires (when you enter the headcount), surges after funding without coherent team builds |

"Posting kept open while someone is on probation" shows up as the first type. The research found no evidence
that employers do this deliberately, but an ad that outlives its stated start date or its copy on the employer's
own site is flagged either way.

### German baselines instead of US age rules

Raw posting age misleads in Germany: it takes 86 days from search start to start of work (IAB 2025), and BA
vacancies take 156 days on average to be deregistered. The radar therefore maps every job title to a KldB-2010
occupation group and requirement level. It then compares the posting's total time online, counted across reposts,
with the Bundesagentur's median vacancy duration for that occupation and region (Engpassanalyse 2025, 2,050 rows).

## Run it

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python scripts\update_baselines.py     # refresh the BA baseline table (already included)
.\.venv\Scripts\python -m uvicorn ghostradar.main:app --port 8000
```

Then open <http://127.0.0.1:8000>. Alternatively run `.\run.ps1`. Deep links work too, for example
`http://127.0.0.1:8000/#company=N26` or `#city=Berlin&q=python`.

Tests: `.\.venv\Scripts\python -m pytest`

## Connect the job platforms

Copy `.env.example` to `.env`, then switch on what you need and restart the app. The Sources list in the sidebar
shows which are connected.

| Platform | How | Switch in `.env` |
| --- | --- | --- |
| **LinkedIn** | Your [linkedin-jobs-mcp](https://github.com/GhoshSrinjoy/linkedin-job-mcp) REST API: `npm ci && npm run api` in that repo. Search finds jobs; `GET /job/{id}` adds the full ad text, criteria and the applicant count from the public job page (one page at a time, 1.5 s apart, cached for 6 h) | `LINKEDIN_JOBS_API=http://localhost:3000` |
| **Bundesagentur Jobbörse** (about 1 million postings, with coordinates, first-publication dates and start dates) | Jobsuche API, built in | `BA_JOBSUCHE=1` (read the terms note below first) |
| **Indeed, StepStone, Glassdoor, XING** and employer sites | Google for Jobs through the JSearch API; its apply options also show whether the employer's own site still carries the job | `JSEARCH_API_KEY=…` |
| **Broad German aggregator** | Adzuna API | `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` |
| **Applicant counts, "Reposted" labels, recruiter-activity badges** | Browser extension in `extension/`: in Chrome or Edge open `chrome://extensions`, switch on developer mode, choose "Load unpacked", pick the `extension` folder. On a job page, click the icon and then "Check this job" | none |

The LinkedIn job-details endpoint (`GET /job/{id}`) is new in linkedin-jobs-mcp. If your checkout does not have it
yet, apply `integrations/linkedin-job-mcp/0001-job-details.patch` there with `git am`. Without it, LinkedIn copies
stay without ad text and LinkedIn links fall back to pasting the text.

With LinkedIn or Google for Jobs connected, the company view also collects the employer's postings on those
platforms. It compares them with the employer's own job feed, so a platform copy that outlives the original is
flagged ("gone from the employer's own site").

**Terms of use.** LinkedIn's terms and robots.txt prohibit automated access without permission. The
Bundesagentur's terms (§2a(3)) ban robots and automated data collection without its permission; a draft request
is in [docs/ba-permission-request.md](docs/ba-permission-request.md). The extension reads only the page you are
looking at and only when you click, but LinkedIn's terms also cover browser add-ons. Keep volumes low, use the
results for your own analysis, and get legal advice before publishing anything built on these sources.

## Data sources

| Source | Used for | Notes |
| --- | --- | --- |
| Employer ATS feeds: Personio, Greenhouse, Lever, SmartRecruiters, Ashby, Recruitee, Workday | Exact first-publication dates, requisition IDs, departments, presence on the employer's own channel | Public feeds published for this purpose; found by careers-page link or by guessing the board name (check the match) |
| schema.org JobPosting markup on careers pages | Dates, expiry (`validThrough`), salary, location | robots.txt is respected |
| BA Engpassanalyse (Statistik der Bundesagentur für Arbeit) | Occupation and regional vacancy-duration baselines | © Statistik der Bundesagentur für Arbeit; mapping and "expected days" are our own calculation |
| LinkedIn via linkedin-jobs-mcp (optional) | City search, platform copies of an employer's jobs, checks of LinkedIn job links | Search gives titles and dates; the job page gives the ad text, criteria, posted time and applicant count. Missing texts are read in the background (up to 20 per company view, 15 per city search) |
| Bundesagentur Jobsuche API (optional) | City search, job-link checks, platform copies | First-publication date, start date, coordinates, employer hash; contact details are stripped |
| JSearch / Google for Jobs (optional key) | City search, platform copies, employer-site presence | Covers Indeed, StepStone, Glassdoor, XING and employer sites |
| Browser extension | Single jobs you open: applicant counts, reposts, badges | Observations are stored over time per posting |
| Adzuna API (optional key) and Arbeitnow API | City search | Adzuna: research use permitted, commercial analysis needs Adzuna's written agreement |
| GDELT | Layoff, insolvency, freeze and funding headlines; funding amount and round read from the headline | At most one request every 5 s; cached for 24 h |
| TED (EU procurement journal) | Public contracts the employer won from German buyers in the window | Documented open API, no key; cached for 24 h; `TED_CONTRACTS=0` switches it off |
| OpenStreetMap / Nominatim | Map tiles and rare city lookups | Cached, at most 1 request per second |

## Guardrails (from the research report's legal findings)

- **Job-board pages are never crawled by the app itself.** Platform data comes only through the connectors you
  switch on (above) or through the extension when you click it.
- **How it fetches:** robots.txt is respected for websites. Each host is rate-limited and responses are cached.
  There are no logins, no captcha solving and no IP rotation.
- **Personal data:** recruiter names and contact details are not stored. Only whether a named contact exists is
  recorded.
- **Applicant counts:** from what you enter, from the job page you capture with the extension, or from the LinkedIn
  job page through your linkedin-jobs-mcp. They are stored as dated observations per posting.
- **Wording:** labels describe observations and an evaluation ("reposted with unchanged text", "gone from the
  employer's own site"). They never say "fake job", and grades are not probabilities.
- **Before publishing:** naming companies publicly needs the steps in the report's last chapter first:
  - a published method;
  - a complaint and right-of-reply process;
  - notice to employers before they are named;
  - a review of the wording by a media lawyer.

## Limitations

- Hires themselves are not public in Germany: the radar shows proxies (jobs that closed within the typical time,
  confirmed new starters you record, headcount growth) and says so. TED covers public procurement only.
- The communication risk comes from your own applications; it needs several of them per employer before the
  interval gets narrow.
- The model page is only as good as its labels: until audits and outcomes accumulate, every grade comes from the
  transparent expert weights, and the model's metrics say how far it can be trusted.
- No signal has been validated against hiring outcomes in Germany. Weights are transparent judgements from the
  report and should be recalibrated once you have audited labels, for example from the outcome reports in the app.
- Lifecycle signals (reposts, removals, excess lifetime across reposts) need repeated observation. Track
  employers and cities in the watchlist and the evidence builds up.
- Coverage depends on the connectors you switch on. Without them the city view uses Arbeitnow and tracked
  employer feeds only.
- The extension's page selectors follow each platform's current layout; when a platform redesigns its pages the
  capture falls back to schema.org data and text patterns, and selectors may need updating.
- Title-to-occupation mapping is rule-based (91 rules covering about 600 title keywords) and falls back to the
  national median for unknown titles.

## Project layout

```text
ghostradar/
  main.py            FastAPI app and routes
  services.py        workflows: check posting, company report, city map, watchlist
  http.py            polite HTTP client (domain policy, robots.txt, rate limits, cache)
  db.py              SQLite storage (postings with full lifecycle, companies, events, reports)
  analysis/
    text.py          German and English text features
    baselines.py     KldB mapping and BA vacancy-duration baselines
    dedup.py         MinHash near-duplicates, repost classification, total lifetime
    scoring.py       transparent weights, five ghost types, advice
    company.py       employer track record, team builds, trends
    labels.py        German and English platform labels (applicants, posted, reposted, badges)
  ml/
    survival.py      Kaplan–Meier lifetimes with censoring and left-truncation, per group of comparable jobs
    labels.py        gold labels (audits, outcomes), labelling functions and the label model
    audit.py         audit sample (per grade, proportional to age) and the design-weighted prevalence estimate
    model.py         Bayesian logistic regression with the expert score as prior; out-of-fold evaluation
    features.py      the feature vector stored with every label
  sources/           ATS feeds, schema.org, LinkedIn, Bundesagentur, JSearch, Adzuna, Arbeitnow, GDELT, geocoding
  static/            dashboard (HTML, CSS, JS, Leaflet map)
extension/           Chrome/Edge extension: check the job you are viewing
docs/                Bundesagentur permission request (draft)
scripts/update_baselines.py
data/ba_engpass.csv  BA Engpassanalyse 2025 baseline table
reports/             research report
research_notes/      research notes behind the report
tests/
```
