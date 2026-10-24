# Ghost-job signals: tools, platform UI labels and practitioner checklists (EN/DE), with consensus, evidence and German scrapability

Research date: 2026-10-24. Scope: concrete ghost-job signals used by tools, job platforms and practitioners, plus how tools score them and which can be scraped from German job boards. Out of scope (other researchers): academic papers, industry statistics, regulation and labour-law verification, API/scraping law, ML methods.

Method limits:
- Reddit could not be accessed: the research tools return "domain not accessible" for reddit.com.
- The shared web-search budget ran out near the end, so a few items rest on search-result snippets. These are marked "(snippet)".
- Chrome Web Store pages redirect to a Google consent page from a German IP, so extension user counts come from the chromeboard.com mirror.

## 1. Which ghost-job detection tools exist, how do they work, and what do they claim?

### Takeaway
I found about 15 tools with documented signal logic. They fall into four groups:
- browser extensions that read LinkedIn and Indeed pages
- paste-in web checkers
- trackers that follow public ATS feeds over time (Greenhouse, Lever, Ashby, Workday, SmartRecruiters)
- one job board's own ghost score

All are small 2025–2026 products, and the larger ones have only dozens of users. None covers StepStone, XING, Indeed.de or the BA Jobbörse. None publishes accuracy, precision or validation figures. Several cite prevalence statistics in place of accuracy.

### Cited Findings

**Browser extensions that read LinkedIn and Indeed pages**

- **Skip This Job (Chrome).** The most fully documented scoring scheme found.
  - Scores LinkedIn and Indeed listings 0–100 from 25 checks in six groups: listing age and reposts; applicants and engagement; pay and contact; description quality; combined red flags; employer record.
  - Score bands: 0–34 "Worth Applying", 35–54 "Proceed with Caution", 55–74 "Likely a Waste of Time", 75–100 "Skip This Job".
  - Missing or unparsed data adds 0 points.
  - [Skip This Job – How it works](https://www.skipthisjob.com/how-it-works)
- **Skip This Job: points for listing signals** ([how it works](https://www.skipthisjob.com/how-it-works)):
  - **Age.** Posted within 2 days: −10 on LinkedIn, −8 on Indeed. Open longer: 7d +4, 14d +8, 30d +15, 60d +20, 90d+ +25. Minimum scores apply once a listing is old: 50 at 60d+, 75 at 90d+, 88 at 120d+.
  - **Reposts.** "Reposted": +24.
  - **Applicants.** 100+ applicants +8, 200+ +10, 500+ +15. On LinkedIn, a post 30d+ old with 200+ applicants scores +16.
  - **Easy Apply on an old post (LinkedIn only).** 60d+ +8, 90d+ +10, 120d+ +12.
  - **"Actively reviewing applicants".** −8 under 60d, −3 at 60–89d, −2 at 90–119d, 0 at 120d+. No review activity at 14d+: +10.
  - **Salary.** Missing on the job page +5, missing on a search card +4, shown on a search card −2.
  - **Poster and contact.**
    - Staffing agency or job board as poster: +12.
    - No hiring contact on LinkedIn: +10.
    - "Responses managed off LinkedIn": +10.
    - LinkedIn "no response insights": +8.
  - **Indeed-specific.**
    - No "often replies" line: +8. "Often replies" present: −5.
    - Apply button leaves Indeed: +5.
    - Indeed employer rating: under 2.5 +10, 2.5 to under 3.0 +5, 4.0+ −3.
  - **Description, LinkedIn.** Under 200 characters +12, under 500 +6. Heavily generic +12.
  - **Description, Indeed.** Under 280 characters +5. Heavily generic +11.
  - **Template and mismatch checks.**
    - Leftover template tokens: +10.
    - Title and experience don't match: +14 on LinkedIn, +13 on Indeed.
    - Work-arrangement tag contradicts the description: +8.
  - **Combined gaps.**
    - LinkedIn +20: post 14d+ old, no contact, description under 300 characters, no salary.
    - Indeed +24: a similar set of gaps.
- **Skip This Job: employer record** ([how it works](https://www.skipthisjob.com/how-it-works)):
  - Community ghost reports: 3+ reports in 90 days with ≥75% ghost or no-response sets a minimum score of 68. Between 55% and 75% sets a minimum of 52.
  - Same role tracked 6+ times sets a minimum of 75. Tracked 4–5 times sets a minimum of 62.
  - Description reused across reposts: +6.
  - The company score starts from the median of up to 50 recent listing scores. The score sent to the extension is 45% that saved score plus 55% the adjusted score.
  - Glassdoor rating and offer rate are shown but add no points.
  - No accuracy or validation claims.
- **Skip This Job: data, price and users.**
  - Reads the page automatically and sends listing details, including a hash of the description, to skipthisjob.com.
  - Anonymous thumbs-down reports feed the employer record. [skipthisjob.com](https://www.skipthisjob.com/)
  - Free, no account needed. 58 users, v0.2.6, updated 2026-10-04. Developer listed as Vibe Labs Marketing (San Antonio, TX). [Chromeboard mirror](https://chromeboard.com/extension/skip-this-job-ghost-job-d-nodldfdkjomniknohmejdimjlejfongd)
- **GhostJob – Ghost Job Detector (Chrome, ID clbbop…).**
  - LinkedIn only. Gives a 0–100 "Trust Score", where higher means safer.
  - Risk signals: reposted jobs, urgency language, buzzy titles, vague compensation, understaffed language, unrealistic experience requirements, thin descriptions, AI-style language, stale listings.
  - Transparency checks: compensation, location, work mode, team context, hiring contact.
  - Trust boosters: salary transparency, benefits, flexible work, growth opportunities, clear responsibilities.
  - Company-level check: looks for an active careers site and tries to match the role there. Blocked or inconclusive checks count as "unknown" and are not penalised.
  - May send company name, title, location, description and local scan results to the GhostJob API.
  - 63 users, v1.2.2 (2026-06-09). Pricing not stated.
  - [Chromeboard mirror](https://chromeboard.com/extension/ghostjob-ghost-job-detect-clbbopifmidceplphamfdfapgacgbhnd)
  - The listing cites a 43% ghost-job figure from a 2024 Resume Builder survey (snippet). [Chrome Web Store](https://chromewebstore.google.com/detail/ghostjob-ghost-job-detect/clbbopifmidceplphamfdfapgacgbhnd)
- **GhostCheck (Chrome).**
  - Covers LinkedIn, Indeed and ZipRecruiter.
  - Six heuristic signals: post age over 30 days, salary missing, vague description, "applicant flood" of 200+, reposted, Easy Apply.
  - Shows green, yellow or red badges on job cards. Weights not disclosed. Processing is local.
  - Free tier: 10 scans per day. Pro: $4.99 one-time (unlimited scans; hide or dim ghost jobs).
  - Says it gives "a likelihood score, not a guarantee". No user count given.
  - [GhostCheck](https://ghostcheck.app/)
- **Ghost-Job Detector (Chrome, ID gpalk…).**
  - Covers LinkedIn and Indeed.
  - Verdict badge: Likely real (green), Questionable (yellow), Likely ghost (red). Reports "unknown" when data is thin.
  - Evidence shown: repost counts, how long the listing has been live, and how many boards it appears on, checked against a "broad, continuously-updated dataset".
  - Price: 7-day trial, then $6.99 for a 90-day pass or $14.99 lifetime.
  - v0.1.2 (2026-08-29). User count not listed.
  - [Chromeboard mirror](https://chromeboard.com/extension/ghost-job-detector-gpalkeokdmojnnlhgpelfnfmnffnkmhi)
- **Adsidera/ghost-job-detector (open source, GitHub).**
  - Reads the LinkedIn job page directly in the browser.
  - Posting age: 30+ days is a mild flag, 60+ days stronger.
  - Uses LinkedIn's "reposted" marker, applicant count against posting age, missing pay range, urgency wording on a listing open for weeks, and short or buzzword-heavy descriptions.
  - Output: 0–100 with low, medium or high. No weights in the README and no validation.
  - 0 stars, 4 commits.
  - [GitHub](https://github.com/Adsidera/ghost-job-detector)
- **pulkitchowdry/ghostjobdetector (open source, GitHub).**
  - Weighted legitimacy score: ATS verification 25% (does the job appear on the company's official ATS?), description quality 20%, freshness 15% (ideally within two weeks), applicant ratio 10%, uniqueness 15% (not reposted, unique description), community signals 15% (reported interviews and HR responses).
  - Verdict bands: 80–100 strong, 60–79 mostly positive, 40–59 mixed, 20–39 multiple warning signs, 0–19 high likelihood of a ghost job.
  - ATS check covers Greenhouse and SmartRecruiters by URL pattern. Workday and Lever are "coming soon".
  - Chrome badge works on LinkedIn only. No validation. 0 stars.
  - [GitHub](https://github.com/pulkitchowdry/ghostjobdetector)
- **Smaller or less documented extensions:**
  - "Ghost Job & Fake Listing Detector — GhostJob" (Chrome): reportedly scores Indeed, LinkedIn and Glassdoor 0–100, locally, from posting age and vagueness. Free 10 checks per day; Pro $6 per month or $59 one-time (snippet). Its name mixes "fake listing" (scam) language with ghost detection. [Chrome Web Store](https://chromewebstore.google.com/detail/ghost-job-fake-listing-de/mdjchaohgneaiflafheajamfomeccach)
  - Potential Ghost Job Detector (Firefox): 5 users, v2.1 (25 Sep 2026). Works on LinkedIn "for the most part"; Indeed and Glassdoor in progress. No signal description. [Firefox Add-ons](https://addons.mozilla.org/en-CA/firefox/addon/potential-ghost-job-detector/)
  - Trouvr (Chrome) exists but its page could not be retrieved (HTTP 403). [Chrome Web Store](https://chromewebstore.google.com/detail/trouvr-ghost-job-detector/gmiggnoakdoiombhiofncfmghbnoidlp)
  - jobghost.io returned only a title: "Free LinkedIn Ghost Job Checker". [jobghost.io](https://www.jobghost.io/)

**Paste-in web checkers**

- **Ghost Job Detector web checker (ghostjobdetector.app; the old ghostjobdetector.onrender.com URL redirects here with a 301).**
  - Free, rule-based, no AI: "same input gives the same score".
  - 11 weighted red flags totalling 114 points, normalised to 0–100. Bands: 0–24 low, 25–54 moderate, 55–100 high.
  - Input: pasted job text or URL.
  - Posting age and repost history are often hidden by boards, so the tool tells users to check them by hand.
  - No accuracy or validation claims. [How it works](https://ghostjobdetector.app/how-it-works)
- **ghostjobdetector.app flag weights** ([/api/v1/flags](https://ghostjobdetector.app/api/v1/flags)):

  | Flag | Points (of 114) |
  |---|---|
  | No salary range | 18 |
  | Posting older than 30 days | 16 |
  | Reposted again and again (cites LinkedIn "Reposted" label docs) | 14 |
  | Boilerplate description | 12 |
  | Vague or stacked title | 10 |
  | "Always hiring" / talent-pipeline language (cites Clarify Capital 2022) | 10 |
  | No named hiring manager | 8 |
  | No concrete details | 8 |
  | Urgent hiring with zero specifics | 6 |
  | Implausibly wide salary range (top at least 2× bottom) | 6 |
  | Masked employer | 6 |

  Most flags are "internal heuristics".
- **ghostjobdetector.app board coverage.**
  - It estimates how many warning signs each of 10 large boards lets you check: average 76.2%.
    - USAJOBS 93.9%, LinkedIn 83.3%, Glassdoor 77.2%, Indeed 70.2%, ZipRecruiter and CareerBuilder 63.2%.
    - Indeed and Glassdoor hide repost history. ZipRecruiter and CareerBuilder also hide the posting date.
    - Applicant count is not tracked.
    - No German board is included.
    - [/api/v1/boards](https://ghostjobdetector.app/api/v1/boards)
  - It claims ghost listings cost about 20.2 hours per 100 applications (27 ghost applications × 45 minutes). This is the tool's own estimate. [llms.txt](https://ghostjobdetector.app/llms.txt)
  - Public API with no key (`/api/analyze`, `/api/v1/flags`, `/api/v1/boards`). [llms.txt](https://ghostjobdetector.app/llms.txt)
- **MintCareer Ghost Detection.**
  - 10 "weighted" signals, weights not disclosed:
    - vague responsibilities
    - missing salary
    - unrealistic requirements
    - stale posting date (60+ days; cites 35–44 days average time to fill)
    - company verification (is the company hiring; are its other postings stale?)
    - recruiter legitimacy (real hiring manager attached)
    - generic or recycled language
    - no hiring timeline
    - seniority vs pay mismatch
    - application red flags (early requests for personal information, broken links)
  - Output: Low, Medium or High. Free 5 analyses per month; Premium price not shown. Trustpilot 4.1 from 5 reviews. Updated May 2026.
  - [MintCareer](https://mintcareer.ai/ghost-jobs)

**ATS-feed and longitudinal trackers**

- **JobGhosting (jobghosting.leveragepointadvisory.co).**
  - Free web tool, "est. 2026". Listed on PeerPush on 6 Aug 2026 (4 upvotes, 0 reviews). [PeerPush](https://peerpush.com/p/jobghosting)
  - Rules ([transparency page](https://jobghosting.leveragepointadvisory.co/transparency)):
    - **Ghost:** 3 or more job-ID rotations for the same normalised title over 90+ cumulative days.
    - **Suspected ghost:** 2 rotations, or 60+ days open with "suspicious patterns".
    - **Stale:** a single ID open 60+ days.
    - **Evergreen:** talent-pool language or department; kept separate from ghost.
  - Matching: titles are normalised (remote tags, locations and punctuation stripped), and description hashes catch reposts under renamed titles.
  - Data:
    - Public ATS endpoints (Greenhouse, Lever, Ashby, Workday, Workable, Rippling), pulled every 6 hours and reclassified nightly.
    - LinkedIn guest search, used for enrichment only and run weekly. LinkedIn has no official API for this.
- **JobGhosting scale and a disclosed data error.**
  - Claims 156,000+ tracked jobs, 25,951 "ghost-class" listings and 106 "repeat offender" companies. [JobGhosting](https://jobghosting.leveragepointadvisory.co/)
  - It disclosed a bug: from 29 June to 10 Aug 2026 its Workday reader stopped after 40 openings per board. That caused 28,246 false closures across 311 employers and false "filled quickly" evidence on 2,345 job streams.
  - No accuracy figures. [Transparency](https://jobghosting.leveragepointadvisory.co/transparency)
- **Apify "Ghost Job Detector: Is This Job Real?" (robotninja).**
  - Scores Greenhouse, Lever and Ashby jobs through their official APIs. Points are additive and capped at 100:
    - Open more than 60, 90 or 180 days: +20, +30 or +40.
    - Open more than 1 year or 2 years: +50 or +60.
    - Reposted under a new ID: +15 per repost, maximum +30.
    - Refreshed old ad (Greenhouse only): +5.
    - Talent-pool or general-application title: +15.
    - Company's openings barely changed in 90 days: +15.
  - Bands: 0–29 low, 30–59 unclear, 60–100 high.
  - Price: $3 per 1,000 scored jobs. 2 users. History tracking started 12 Oct 2026.
  - Says scores are "risk estimates … not proof". [Apify](https://apify.com/robotninja/ghost-job-detector)
- **Apify Job Lifecycle Monitor (gganbukim).**
  - Covers Greenhouse, Ashby, Lever and SmartRecruiters. Explicitly no Personio or other German ATS.
  - Scores each role 0–100 against its board's median age and its republish history.
    - Reposts are matched by a fingerprint of normalised title and location.
    - With age only, the maximum score is 65. Republish history adds up to 40.
  - Default threshold 40; lower scores are "noisy" on boards with evergreen roles.
  - Price: $0.40 per 1,000 change events and $0.20 per 1,000 ghost suspects. 2 users. No accuracy claims.
  - [Apify](https://apify.com/gganbukim/job-lifecycle-monitor)
- **Remote Rocketship's own ghost score.** A job board scoring its own listings; written by Lior Neu-ner, 27 Aug 2026.
  - Score of 0–100 from five weighted signals:
    - age compared with the company's own fill-time baseline (35); the market median is 31 days, and listings under 21 days are capped at a score of 25
    - reposting (20)
    - open roles compared with LinkedIn headcount (20)
    - company slow-close rate, the share of closed listings that took 180+ days (15)
    - salary transparency (10)
  - Missing data is not penalised. "Likely ghost" means a score of 60 or more; 40–59 is a warning band.
  - Dataset: 512,744 live listings from 46,517 companies.
  - [Remote Rocketship report](https://www.remoterocketship.com/advice/ghost-jobs-report/)

**Job-search platforms and community sites**

- **HiringCafe.**
  - Indexes employer career sites. A listing disappears when the underlying careers-page job is removed, which the review says reduces reposting and broken-link problems.
  - Removes outside recruiting agencies and "fake consulting firms".
  - No ghost-specific filter. The closest is a "Date Posted" filter.
  - Free for job seekers. Claims 5.7M jobs and over 2M monthly users; these figures come from HiringCafe via a competitor's review.
  - $6.8M pre-seed round announced 28 Sep 2026.
  - [Scoutify review](https://scoutify.com/blog/hiringcafe-review)
- **GhostJobs.io.**
  - Free job site with community reports (267) in categories such as "Vague Job Postings", "Frequently Reposted" and "Poor Follow-up Process".
  - Says it monitors 13,000+ listings and 300K+ companies. A "ghost job detector" is only planned.
  - [GhostJobs.io](https://ghostjobs.io/)
- **Ghost Jobs Index (ghostjobs.net).**
  - Anonymous complaints: 609 complaints about 573 companies, ranked by upvotes.
  - Categories mix ghost postings, interview ghosting and "data harvesting", which is a scam or fraud category.
  - [ghostjobs.net](https://ghostjobs.net/)
- **No ghost-job feature found:**
  - Jobright: its related product is fake-*candidate* detection for recruiters. [Jobright](https://jobright.ai/fake-candidate-detection)
  - Simplify Copilot: autofill and tracking. [Simplify](https://simplify.jobs/copilot)
  - Teal and Huntr: job trackers. [Teal vs Huntr](https://www.tealhq.com/post/teal-vs-huntr); [Huntr vs Teal](https://huntr.co/blog/huntr-vs-teal)
  - TrueUp: only a company page surfaced, with no ghost flags. [TrueUp](https://trueup.io/co/dayone-cloud)
  - These are search-only results, so absence is not proven.

**German and EU tools**

- No ghost-job checker for StepStone, XING, Indeed.de or the BA Jobbörse was found in German or English searches.
- StepStone tooling found is data extraction only, not ghost detection: an Apify StepStone scraper and an MCP server. [Apify StepStone scraper](https://apify.com/hello.datawizards/stepstone-jobs-scraper); [GitHub mcp-stepstone](https://github.com/kdkiss/mcp-stepstone)

**How tools combine signals into a score (patterns)**

1. **Additive points with minimum scores, plus an employer-history blend** (Skip This Job). [How it works](https://www.skipthisjob.com/how-it-works)
2. **Weighted sum normalised to 0–100** (ghostjobdetector.app, 114 points). [How it works](https://ghostjobdetector.app/how-it-works)
3. **Weighted average of the signals that are available,** with missing data neutral and young listings capped (Remote Rocketship). [Report](https://www.remoterocketship.com/advice/ghost-jobs-report/)
4. **Additive thresholds capped at 100** (Apify robotninja). [Apify](https://apify.com/robotninja/ghost-job-detector)
5. **Age relative to the board's median,** with a score ceiling that depends on how much history exists (Job Lifecycle Monitor). [Apify](https://apify.com/gganbukim/job-lifecycle-monitor)
6. **Fixed category rules on ID rotations and days open** (JobGhosting). [Transparency](https://jobghosting.leveragepointadvisory.co/transparency)
7. **Weighted category sub-scores into a "legitimacy" score** (pulkitchowdry). [GitHub](https://github.com/pulkitchowdry/ghostjobdetector)
8. **Badges with undisclosed weights** (GhostCheck, Ghost-Job Detector, MintCareer). [GhostCheck](https://ghostcheck.app/); [Chromeboard](https://chromeboard.com/extension/ghost-job-detector-gpalkeokdmojnnlhgpelfnfmnffnkmhi); [MintCareer](https://mintcareer.ai/ghost-jobs)

Common design rules:
- Unknown data is treated as neutral. [Skip This Job](https://www.skipthisjob.com/how-it-works); [Remote Rocketship](https://www.remoterocketship.com/advice/ghost-jobs-report/); [GhostJob](https://chromeboard.com/extension/ghostjob-ghost-job-detect-clbbopifmidceplphamfdfapgacgbhnd)
- "No single signal triggers a flag". [PeerPush/JobGhosting](https://peerpush.com/p/jobghosting)
- Scores are framed as probabilities, "never accusations". [ghostjobdetector](https://ghostjobdetector.app/how-it-works); [Apify robotninja](https://apify.com/robotninja/ghost-job-detector)

**Accuracy claims**

- None of the tools publishes precision, recall or a test against known outcomes.
- Prevalence statistics are used as marketing in their place:
  - 43% from Resume Builder (GhostJob, snippet). [Chrome Web Store](https://chromewebstore.google.com/detail/ghostjob-ghost-job-detect/clbbopifmidceplphamfdfapgacgbhnd)
  - A WSJ figure of about 1 in 5 Greenhouse-client job ads in Q2 2026 (Apify). [Apify](https://apify.com/robotninja/ghost-job-detector)
  - 40–60% of listings in GhostCheck's FAQ. [GhostCheck](https://ghostcheck.app/)
- Remote Rocketship did check one signal at group level: its headcount signal against independent historical headcount data (CoreSignal) for 125 companies. It also fixed a bug that over-flagged evergreen government postings. [Report](https://www.remoterocketship.com/advice/ghost-jobs-report/)

### Inferences
- **Two technical routes.**
  - Extensions that read pages can only use what the board shows, which on LinkedIn means the "Reposted" label, age, applicants, salary, hiring contact and responsiveness labels.
  - ATS trackers can measure days open and ID rotations directly, but only for employers on supported ATSs. German Mittelstand ATSs such as Personio are not covered by any tool found.
- **The weights are designers' judgement.** ghostjobdetector.app makes missing salary its heaviest flag (18 of 114). Pay ranges are not yet required for German private employers (see section 3, MoreThanCareer), so missing salary would fire on most German ads and say little. It would need re-weighting for Germany.
- **German text is unsupported.** Every description and wording heuristic found works on English-language patterns (boilerplate, urgency, "always hiring"). None handles German text, which is a gap for StepStone, XING and BA ads.
- **Legitimate uses of longitudinal trackers.** They already single out evergreen and talent-pool roles as a separate class (JobGhosting "Evergreen"; Apify `includeEvergreen` off by default). This matches Wenske's scale-up pattern of evergreen listings that are not "ghosts" in the frozen-role sense.

### Gaps
- No tool publishes validation against ground truth (hires or no hires). Remote Rocketship's numbers describe patterns and are partly circular (section 5).
- Official Chrome Web Store user counts and ratings could not be fetched (consent redirect). Chromeboard counts may lag.
- Scoring details are missing for GhostCheck, MintCareer, the "Ghost Job & Fake Listing Detector", Trouvr and jobghost.io.
- No German or EU tool was found. Because the search budget ran out, a targeted search (for example "Ghost Job Erweiterung StepStone") was not completed.
- An Indie Hackers post titled "Ghost jobs are the most requested feature I decided not to build" could not be read (HTTP 403). It may contain a builder's reasons against detection. [Indie Hackers](https://www.indiehackers.com/post/ghost-jobs-are-the-most-requested-feature-i-decided-not-to-build-31747885f0)

## 2. What do job platforms show (UI and data) that bears on ghost likelihood, and which labels exist on the German sites?

### Takeaway
LinkedIn and Indeed show responsiveness labels that exist in German and are confirmed from official help pages:
- LinkedIn: „Bewerber:innen werden aktiv geprüft“ and „Die Prüfungszeit beträgt in der Regel 1 Woche“
- Indeed: „Aktiver Arbeitgeber“

Both count automatic rejections as "responses", so they show activity in the employer's account, not that a vacancy is being filled.

Indeed's „Dringend gesucht“ ("Urgently hiring") is a paid Sponsored Jobs feature, not an urgency signal.

On the German boards:
- StepStone's documented labels describe how easy it is to apply („Schnelle Bewerbung“, „Anschreiben nicht erforderlich“). No responsiveness or repost label was found.
- The BA Jobbörse API exposes the richest machine-readable data: first vs current publication date, last-modified time, start date, number of openings, fixed-term status, temp-agency filters and an anonymous-ad flag.

### Cited Findings

**LinkedIn**

- **„Actively reviewing applicants“.** LinkedIn's help page, updated about 1 week before the fetch, says:
  - The label shows when the recruiter "has reviewed one or more applications in the past two weeks" and is updated daily.
  - A "review" includes InMail, rejection (auto, bulk or manual), moving a candidate past "uncontacted" in Recruiter, viewing an application, viewing a profile, or downloading a resume.
  - [LinkedIn Help – Hirer responsiveness insights FAQ](https://www.linkedin.com/help/learning/answer/a1655396)
- **"Review time is typically 1 week".** Based on the average response or review time for at least 35% of on-site and Apply Connect applications over the last 30 days. Hidden if the average is over 21 days. [LinkedIn Help](https://www.linkedin.com/help/learning/answer/a1655396)
- **"No response insights available yet".** Shown when fewer than 35% of applications were reviewed or none in the past two weeks. [LinkedIn Help](https://www.linkedin.com/help/learning/answer/a1655396)
- **"Responses managed off LinkedIn".** Shown for jobs posted through an external ATS, where "LinkedIn does not have responsiveness data". Jobs that send applicants to an external site are not eligible for the insights. [LinkedIn Help](https://www.linkedin.com/help/learning/answer/a1655396)
- **German labels, confirmed from LinkedIn's German help page:**
  - „Bewerber:innen werden aktiv geprüft“
  - „Die Prüfungszeit beträgt in der Regel 1 Woche“
  - „Noch keine Antwort verfügbar“
  - „Außerhalb von LinkedIn verwaltete Antworten“
  - [LinkedIn Hilfe (DE)](https://www.linkedin.com/help/linkedin/answer/a1655396?lang=de)
- **Verification badge on job posts.**
  - Means "the company has a verified LinkedIn Page" and the poster has verified their workplace (work email, Microsoft Entra Verified ID or company LinkedIn Learning licence). Government-ID checks via CLEAR are US-only.
  - "Currently being piloted with a select number of LinkedIn Jobs customers."
  - "Applying to a job with a verification badge does not mean you are more likely to be hired."
  - Page updated about 6 months before the fetch. [LinkedIn Help – Verification badge on job posts](https://www.linkedin.com/help/linkedin/answer/a1492056)
- **Reposting.** Employers can repost a closed, expired or modified job "at any time" from Manage job posts (snippet). [LinkedIn Help – Repost a closed or expired job](https://www.linkedin.com/help/learning/answer/a522249)
  - A LinkedIn help page defining the job seeker's "Reposted" label was not found.
  - Several tools read the label from the page: Skip This Job (+24) and Adsidera. ghostjobdetector cites "LinkedIn 'Reposted' label help docs". [Skip This Job](https://www.skipthisjob.com/how-it-works); [Adsidera](https://github.com/Adsidera/ghost-job-detector); [ghostjobdetector flags](https://ghostjobdetector.app/api/v1/flags)
- **Other LinkedIn page elements tools rely on:**
  - applicant counts (100+, 200+, 500+)
  - Easy Apply
  - the hiring contact in the detail pane
  - [Skip This Job](https://www.skipthisjob.com/how-it-works); [GhostCheck](https://ghostcheck.app/)
  - LinkedIn's own definitions of these, and their German wording, were not verified (see Gaps).

**Indeed**

- **„Aktiver Arbeitgeber“ (English: "Responsive Employer" badge).**
  - Fetched from a German IP, Indeed's employer help article was served in German and names the badge „Aktiver Arbeitgeber“: a small symbol showing the company "schnell auf Bewerbungen antwortet".
  - Requires an Antwortrate over 51% in the last 30 days, recalculated weekly.
  - Responses that count include automatic emails to unsuccessful candidates, sent at any time, "auch wenn Sie eine Stellenanzeige schließen" (even after closing a listing).
  - Indexed jobs using Indeed Apply need an ATS with status sync and status updates on more than 50% of Indeed applications.
  - [Indeed Help – What is a Responsive Employer Badge?](https://www.indeed.com/help/employers/articles/what-is-an-employer-response-badge)
- **„Dringend gesucht“ ("Urgently hiring").**
  - Unlocked through paid Sponsored Jobs: Sponsored Jobs "schalten … das Label ‚Dringend gesucht‘ frei".
  - Indeed claims such jobs get 2.4× more applications; no method is given.
  - [Indeed für Arbeitgeber (DE)](https://de.indeed.com/arbeitgeber/recruitingloesungen/attract)
- **"Employer active X days ago" / "Employer actively reviewed candidates X days ago".** No official definition was found. Forum users report different values for the same ad (snippet). [City-Data forum](https://www.city-data.com/forum/work-employment/3264375-indeed-employer-actively-reviewed-candidates-days.html); [GirlsAskGuys](https://www.girlsaskguys.com/education-career/q4847678-any-idea-what-it-means-when-it-says-employer-reviewed-job-x-days-ago)
- **Other Indeed page elements tools use:** the "often replies" line, the apply button leaving Indeed, and the Indeed employer star rating. [Skip This Job](https://www.skipthisjob.com/how-it-works)
- **What Indeed discloses, per ghostjobdetector's board analysis (indeed.com, not .de):** repost cycle hidden; salary, posting age and wide-salary range only partly visible. [ghostjobdetector boards](https://ghostjobdetector.app/api/v1/boards)

**Glassdoor**

- Glassdoor shows posting age capped at "30d+", and reposts appear as new listings with fresh dates (snippet, from ghostjobdetector's Glassdoor board page). [ghostjobdetector – Glassdoor](https://ghostjobdetector.onrender.com/boards/glassdoor)
- Glassdoor's chief economist reported (snippet; page returned 403):
  - Interview reviews mentioning ghosting rose 11% year on year as of August 2024.
  - In 2024, ghosting appeared in 6.5% of reviews for interviews obtained through recruiter outreach, 4.9% through online applications, and 3% through employee referrals.
  - [Glassdoor blog – Ghosting creeps higher](https://www.glassdoor.com/blog/conversation-starter-ghosting-2024)

**StepStone**

- Employer-set "info labels" include „Schnelle Bewerbung“, a green label meaning the form opens pre-filled from the profile, and „Anschreiben nicht erforderlich“. StepStone presents them as information about application effort (snippet). [StepStone – Bewerbung leicht gemacht](https://www.stepstone.de/e-recruiting/hr-wissen/recruiting/bewerbung-leicht-gemacht)
- No source found for a StepStone repost label, employer-responsiveness badge, applicant count, or the meaning of „Neu“ (searched; not found).

**XING and kununu**

- XING added kununu employer ratings (1–5 scale) to job ads in 2014 (snippet). Whether this is still live was not verified. [finews.ch (2014)](https://www.finews.ch/themen/leben-karriere/12654-xing-job-anzeige-kununu-bewertung)
- kununu applicant reviews include application-process criteria. In a Staufenbiel/kununu analysis of 32,633 reviews (2015–2016), „Zeitgerechte Zu- oder Absage“ (timely acceptance or rejection) was the weakest criterion at 3.07 points (snippet; dated). [Personalwirtschaft](https://www.personalwirtschaft.de/?p=104637)

**Bundesagentur für Arbeit Jobbörse (Jobsuche API, community-documented)**

- **Search results.** Each item includes `refnr`, `arbeitgeber`, `aktuelleVeroeffentlichungsdatum`, `eintrittsdatum`, `modifikationsTimestamp`, `arbeitsort` and `externeUrl` (link to an external posting). [bundesAPI OpenAPI spec](https://raw.githubusercontent.com/bundesAPI/jobsuche-api/main/openapi.yaml)
- **Job details.** These add:
  - `ersteVeroeffentlichungsdatum` (first publication date; details only) and `anzahlOffeneStellen` (number of openings)
  - `befristung`, `verguetung` (pay, free text), `betriebsgroesse`, `branche`
  - `arbeitgeberdarstellungUrl`, `fertigkeiten`, `fuehrungskompetenzen`
  - flags: `anzeigeAnonym`, `nurFuerSchwerbehinderte`, `istBetreut`, `istGoogleJobsRelevant`, `allianzpartner`
  - There are no contact-person (Ansprechpartner) fields.
  - [bundesAPI OpenAPI spec](https://raw.githubusercontent.com/bundesAPI/jobsuche-api/main/openapi.yaml)
- **Query parameters.**
  - `veroeffentlichtseit`: days since publication, 0–100.
  - `zeitarbeit`: include temp-agency jobs (default true).
  - `pav`: Private Arbeitsvermittlung (private placement agencies).
  - `arbeitgeber`, `befristung`, `angebotsart`, `arbeitszeit`.
  - [bundesAPI README](https://github.com/bundesAPI/jobsuche-api); [OpenAPI spec](https://raw.githubusercontent.com/bundesAPI/jobsuche-api/main/openapi.yaml)

**ATS-side badges (Greenhouse)**

- Greenhouse Verified awards up to four badges based on the employer's hiring practices:
  - Fair: anonymised review, same criteria for all applicants.
  - Prepared: approved questions and interview guides, written rating rationales.
  - Respectful: confirmation emails, candidate feedback.
  - Communicative: rejection notices "in a timely manner", which is not defined.
  - [Greenhouse Verified](https://www.greenhouse.com/greenhouse-verified)
- Greenhouse's FAQ says badges reflect "track record" and companies cannot pay for them. Badges are visible in MyGreenhouse (snippet). [MyGreenhouse – Greenhouse Verified](https://my.greenhouse.com/greenhouse-verified)

**Aggregator date caveat (German practitioner)**

- An aggregator's "Just posted" badge reflects the last data sync, not the job's status. Job seekers should check the requisition ID and posting date on the employer's own careers site. [MoreThanCareer.de](https://morethancareer.de/blog/pharma-bloodbath-part-xvii-ghost-jobs-ghost-candidates-german-data.html)

### Inferences
- **Responsiveness labels are weak evidence of a live requisition.**
  - On LinkedIn, an automatic rejection or a profile view counts as a "review".
  - On Indeed, automatic rejection emails count, even after a listing is closed.
  - A frozen role with auto-reject rules can therefore still earn „Bewerber:innen werden aktiv geprüft“ or „Aktiver Arbeitgeber“.
  - Their absence is more informative: „Noch keine Antwort verfügbar“ at 14+ days means no recorded activity.
- **Paid visibility is not urgency.** „Dringend gesucht“ (Indeed) and LinkedIn promotion are paid features. A paid boost does suggest current budget, but no source tested whether paid jobs are less often ghosts.
- **The BA API is the most usable German source for age and repost signals.** First vs current publication date on the same `refnr` exposes re-publication without crawling. Other useful fields:
  - `anzahlOffeneStellen` with `betriebsgroesse` approximates "open roles relative to company size"
  - `eintrittsdatum` gives the start-date signal
  - `zeitarbeit`, `pav` and `anzeigeAnonym` give the agency or masked-employer signal
  - What reposts under a new `refnr` look like was not tested.
- On StepStone and XING, age and repost signals would need your own repeated crawling and fingerprinting, as JobGhosting and Job Lifecycle Monitor do for ATS feeds. No platform-native label was found.

### Gaps
- No German UI text was verified for LinkedIn "Reposted", "Promoted", "Easy Apply" or applicant counts, or for Indeed "Employer active X days ago", "Posted 30+ days ago" or "Hiring multiple candidates". The help pages found did not cover them, and the search budget ran out.
- No official LinkedIn definition of the job-seeker "Reposted" label, and none of when "Promoted" appears.
- No source for StepStone date or „Neu“ logic, XING's current job-ad features, Glassdoor.de labels, or kununu's current applicant-review criteria.
- Whether LinkedIn's job-verification pilot runs in Germany is not stated.
- Indeed's help page shows no date; the 51% threshold may have changed.

## 3. Which signals recur in practitioner checklists and German-language coverage? (incl. Bernd Wenske)

### Takeaway
English checklists and German media agree on a core set:
- long posting age
- repeated reposting
- vague or generic descriptions
- absence from the employer's careers page
- no named contact
- no response after applying

German coverage leans heavily on US statistics and adds DACH-specific "pro-forma" signals:
- tailored or hyper-specific requirements („Detailliertes Stellenangebot“, „Spezielle Anforderungen“)
- novel job titles („Neuartige Jobtitel“)
- statutory or works-council postings (public sector, § 93 BetrVG)

Wenske's 1 Sep 2026 article is the only piece found that turns works-council language, start-date and probation details, and clusters of openings into explicit signals. It is also the main dissent on posting age.

### Cited Findings

**English-language checklists**

- **Mondo (staffing agency).** "Identifying Ghost Jobs: 12 Signs a Job Posting May Not Be Real", by Sarah Magazzo, byline "AI Drafted & Human Crafted". Undated; the image path suggests about May 2026.
  - The 12 signs: posted for months without changes; constantly reposted; extremely generic description; no operational context (no department, manager or business reason); missing or unrealistic salary; layoffs alongside aggressive hiring; instant automated rejections; unrealistic requirements; on job boards but not the company website; multiple agencies advertising the same job; "always hiring" language; employees mentioning hiring freezes online.
  - No thresholds or sources. Several signs overlap with fraud indicators.
  - [Mondo](https://mondo.com/insights/identifying-ghost-jobs-signs-a-job-posting-may-not-be-real/)
- **The Interview Guys.** By Jeff Gillis; published 29 Apr 2025, modified 18 Aug 2026.
  - 10 red flags: perpetual posting (60+ days; "typically fill within 30-45 days", unsourced); vague description; missing management structure; "unicorn" requirements; identical postings in many cities; missing salary; instant rejection; company in crisis; outdated information; recurring phantom ("every few months").
  - Five-step verification: company research, posting analysis, social proof, application process, direct verification.
  - "Three strikes": drop a company after the same job is posted three times without a hire.
  - Explicitly separates ghosts from scams.
  - [The Interview Guys](https://blog.theinterviewguys.com/?p=2291)
- **Orbyt Labs (job-tracker vendor).** "Ghost Jobs: How to Spot Postings That Will Never Hire (2026)", by Justin Bartak, 15 Jun 2026.
  - 7-point test: age over 30 days (it "overcounts slow-but-real hiring", especially for senior roles); repost cycling; no salary band; no careers-page match ("the fastest disqualifier there is"); no named human; evergreen copy; zero-response history.
  - Scoring rule: 0–2 signals, apply normally; 3–4, cap your time and pair the application with outreach to a named person; 5+, skip.
  - Scam tells are listed separately: fees, personal data before an offer, messaging-app-only interviews, offers without an interview, check cashing.
  - [Orbyt Labs](https://www.orbytlabs.ai/blog/how-to-spot-ghost-jobs)
- **The Muse.** By Amanda Cardoso; updated 13 Feb 2025.
  - Signs: listing up for "several months" without updates; on a third-party site but not the careers page; no recruiter engagement; vague, template-like or possibly AI-written description.
  - Suggests emailing the hiring manager after applying.
  - Cites Clarify Capital 2022: 50% of hiring managers say the company is "always open" to new people; 37% keep an applicant pool; 27% forgot to delete a filled listing.
  - Separates scams.
  - [The Muse](https://www.themuse.com/advice/ghost-jobs)

**Bernd Wenske, "Decoding the Ghost Job" (LinkedIn Pulse, 1 Sep 2026)**

- **Article details.** Part of his newsletter *Inside the German Job Market* (745 followers when fetched); 14 reactions and 11 comments. It cites unnamed "independent studies" putting ghost postings at roughly 1 in 7 to 1 in 3. [LinkedIn – Wenske](https://www.linkedin.com/pulse/decoding-ghost-job-how-spot-frozen-roles-german-market-bernd-wenske-vys6e/)
- **Posting age.** He argues US-style "3–6 months = fake" advice doesn't fit Germany. A long-open German posting may reflect a slow but real process, because the ad is only withdrawn after the hire completes the Probezeit. So posting age is a weak signal. The mechanism is stated without a source; labour-law checking belongs to another researcher. [LinkedIn – Wenske](https://www.linkedin.com/pulse/decoding-ghost-job-how-spot-frozen-roles-german-market-bernd-wenske-vys6e/)
- **Patterns by employer type** ([LinkedIn – Wenske](https://www.linkedin.com/pulse/decoding-ghost-job-how-spot-frozen-roles-german-market-bernd-wenske-vys6e/)):
  - **Multinationals:** internal mobility, budget freezes, hyper-niche requirements matching one internal employee.
  - **Corporates with a Betriebsrat:** information and objection rights, plus internal posting first. This produces "short, templated windows" and postings that partly serve compliance.
  - **Mittelstand:** informal approval chains and unfunded headcount leave static postings up for months, "often through oversight".
  - **Tech companies and scale-ups:** evergreen, auto-refreshed generic listings for talent pools and PR.
  - The coordinator's brief also mentions a "one-week objection right" and "stale static PDF ads". My fetched rendering of the article did not show those specific details.
- **Seven signals** ([LinkedIn – Wenske](https://www.linkedin.com/pulse/decoding-ghost-job-how-spot-frozen-roles-german-market-bernd-wenske-vys6e/)):
  1. Reposting pattern on the company's own careers page. Frequent reposting there indicates ongoing investment, more than an old date on an aggregator.
  2. Recent posts by the named hiring manager or team lead about growth, launches or expansion.
  3. Public company signals: restructuring, freezes, layoffs, funding news.
  4. Specific requirements: unusually narrow profiles or odd certification and regional-site combinations suggest an internal placeholder; generic profiles suggest external hiring.
  5. Works-council or statutory posting language.
  6. Interview timeline indicators: start dates, clear interview timelines, probation details.
  7. Cross-department patterns: clusters of related openings suggest active recruiting; an isolated posting may be frozen.
- **Effort tiers** ([LinkedIn – Wenske](https://www.linkedin.com/pulse/decoding-ghost-job-how-spot-frozen-roles-german-market-bernd-wenske-vys6e/)):
  - **High:** named hiring manager with recent posts, several aligned signals, no conflicting news.
  - **Medium:** mixed signals.
  - **Low:** "light touch", a shorter application as a hedge.
  - **No signal:** skip or archive. Several red flags, a freeze or recent layoffs, or an internal-placeholder profile.
- **Eight-question checklist** ([LinkedIn – Wenske](https://www.linkedin.com/pulse/decoding-ghost-job-how-spot-frozen-roles-german-market-bernd-wenske-vys6e/)):
  1. Is the role on the company's own careers page?
  2. Has it been reposted with only cosmetic changes?
  3. Is the profile unusually narrow?
  4. Is there a named, recently active hiring manager?
  5. Are there freeze, restructuring or layoff signals?
  6. Is there Betriebsrat or statutory posting language?
  7. Does the role merit full effort?
  8. Are there higher-signal roles to prioritise?
- **Case study.** An anecdote, not a test: an engineer applying in the German energy sector put in light effort on a role open four months, with oddly specific requirements and two near-identical careers-page reposts. They put more effort into fresher roles at the same company that showed hiring-manager posts, a funding announcement and expansion language. [LinkedIn – Wenske](https://www.linkedin.com/pulse/decoding-ghost-job-how-spot-frozen-roles-german-market-bernd-wenske-vys6e/)

**Other Germany-specific practitioner pieces**

- **MoreThanCareer.de** (Andreas Schulz, Berlin pharma career strategist; updated 11 Aug 2026). [MoreThanCareer.de](https://morethancareer.de/blog/pharma-bloodbath-part-xvii-ghost-jobs-ghost-candidates-german-data.html)
  - **Heuristics:**
    - Verify the requisition ID and date on the careers site; aggregator "Just posted" reflects sync.
    - A role on several boards but absent from the company site suggests "agency fishing" or a broken feed.
    - "Talent pool" or "future opportunities" listings are not active vacancies.
    - Ask the named contact in writing about approved headcount and target start date. A vague answer or silence is itself a signal.
    - Ask for the salary band, citing the EU Pay Transparency Directive.
    - For pharma roles, check the product pipeline (for example, a product nearing loss of exclusivity).
  - **Context it cites:**
    - IAB Q1 2026: about 79% of vacancies "sofort zu besetzen" (to be filled immediately). The article derives that about 21% are planned for later.
    - 2025 hiring channels: personal contacts 27%, job boards 21%, own careers pages 20%.
    - § 93 BetrVG, Art. 33(2) GG, § 164(1) SGB IX.
    - A BAG case (27 Mar 2025) where the advert stayed online after selection had been finalised.
    - Germany missed the 7 June 2026 pay-transparency transposition deadline. Private employers are not yet bound.
  - Statistics and law are noted for other researchers, not verified here.
- **Karrierebibel, "Pro-forma-Ausschreibung: 6 verräterische Anzeichen"** (Jochen Mai; updated 16.08.2026). [Karrierebibel – Pro-forma](https://karrierebibel.de/pro-forma-ausschreibung/)
  - The six signs: „Detailliertes Stellenangebot“, „Spezielle Anforderungen“, „Neuartige Jobtitel“, „Umfangreiche Anforderungen“ ("eierlegende Wollmilchsau"), „Befristetes Angebot“ (a fixed term alone is not a sign), „Wiederkehrende Anzeige“ ("alle paar Monate"; may also indicate turnover).
  - Reasons: public-sector duty to advertise and § 93 BetrVG. It also lists "Datenhandel" (shell companies collecting applicant data), which is a scam motive.

**German-language media and career sites**

- **Karrierebibel, "Ghost Jobs"** (Jochen Mai; updated 16.08.2026).
  - Signals: „Detailliertes Stellenangebot“, „Unklare Stellenbeschreibung“, „Neuartige Jobtitel“, „Wiederkehrende Anzeige“ (with no named contact; "alle paar Monate"), „Umfangreiche Anforderungen“.
  - Checks: company website and social media, other applicants' experiences, employer review portals ("Arbeitgeberbewertungsportale"), asking HR whether the job is still current, your network.
  - No German figures; a US "one third" claim without a source.
  - [Karrierebibel](https://karrierebibel.de/ghost-jobs/)
- **t3n** (Noëlle Bölling, 30.01.2025).
  - Three signals from Kickresume CEO Peter Duris: „Fehlendes oder veraltetes Veröffentlichungsdatum“ (several months), „Wiederholte oder zu häufige Postings“, „Keine Erwähnung auf der Unternehmenswebsite“. Plus checking Glassdoor reviews.
  - Cites the Greenhouse 2024 report (2,500 employees in DE, UK and US): 21% of German respondents applied despite suspecting a fake.
  - [t3n](https://t3n.de/news/vorsicht-vor-ghost-jobs-so-erkennst-du-fake-stellenanzeigen-1670553/)
- **Golem Karrierewelt** (undated, no author).
  - Ads online "länger als 60 bis 90 Tage".
  - Ads with "mehreren Hundert oder Tausend Bewerbungen" often have no active selection.
  - Vague or inflated wording and titles (for example "Superstar Sales Guru").
  - Missing from the company's career page.
  - "Ausweichende Reaktionen" (evasive replies) about status or timeline.
  - Notes there are "noch keine Korrelationsstudien".
  - [Golem Karrierewelt](https://karrierewelt.golem.de/blogs/karriere-ratgeber/ghost-jobs-wenn-stellenanzeigen-nur-der-imagepflege-dienen)
- **Heidelberg24** (Stand 10.07.2026; produced in cooperation with Newsweek and syndicated across Ippen sites).
  - Posting age 30/60/90+ days. Nathan Putsey (JobLeads): "alles, was länger als drei Monate online ist, ist fast immer ein Ghost Job".
  - On LinkedIn or Indeed but not the career page.
  - Same ad reappears every few weeks with identical wording.
  - Template text with no team, task area or reporting line.
  - Unusually wide salary range (70,000–180,000 dollars).
  - LinkedIn headcount flat or shrinking while dozens of roles are "offen".
  - Searching Glassdoor or Reddit for "Firmenname" + "Interview".
  - Caveat: a delayed reply alone is no proof.
  - [Heidelberg24](https://www.heidelberg24.de/verbraucher/ghost-jobs-so-erkennen-sie-fake-stellenanzeigen-im-netz-zr-94391464.html)
- **Heidelberg24** (Sabrina Reisinger, 20.12.2024).
  - Signals: „Lange Laufzeit“; vague description; „Regelmäßiges Wiedereinstellen“; no named contact (impersonal info@ addresses); job portals only.
  - HWZ personnel expert Matthias Mölleney (via RND) says fakes are "wenig bis gar nicht" distinguishable from real ads.
  - [Heidelberg24 (2024)](https://www.heidelberg24.de/ratgeber/das-raetsel-der-ghost-jobs-warum-bewerbungen-ins-leere-laufen-zr-93433508.html)
- **NachhaltigeJobs, "Geister-Jobs"** (Charlotte Clarke, 16.06.2026).
  - Indicators:
    - online more than "2-3 Monate" without changes, or reposted
    - vague tasks
    - interview processes with no clear decision path
    - long silences or no feedback
    - salary and contract terms never discussed across rounds
    - many "active" postings without visible growth
    - non-profit roles "vorbehaltlich einer Förderzusage" (subject to a funding decision)
    - public-sector requirements tailored to one person, which it says often means a real vacancy with an internal candidate
  - Stresses that only combinations of signals matter.
  - [NachhaltigeJobs](https://www.nachhaltigejobs.de/geister-jobs/m)
- **HR monkeys** (Vanessa Kammler; undated).
  - Signals: unusually long online duration; „regelmäßig neu veröffentlicht“; no reaction even after following up; „dauerhaft ausgeschrieben“ with no visible hiring process; talent-pool ads not labelled as such; weeks of silence.
  - "Dafür gibt es keine allgemeingültige Dauer" (there is no universal time limit).
  - Ghost Jobs "sind nicht automatisch verboten" (not automatically illegal).
  - [HR monkeys](https://hr-monkeys.de/blog/ghost-jobs/)
- **OnlineMarketing.de** (Marié Detlefsen, 17.11.2025).
  - Signals: postings that „lange online bleiben“; drawn-out processes; missing responses.
  - Headline "Knapp 30 Prozent" comes from US JOLTS data.
  - States the phenomenon exists in Germany "in abgeschwächter Form" (in weaker form), without German figures.
  - [OnlineMarketing.de](https://onlinemarketing.de/karriere/human-resources/ghost-jobs-jede-dritte-stelle-existiert-nicht)
- **Business Punk** (Redaktion; 25.07.2024, updated 14.05.2025).
  - Synonyms: "Fake Jobs", "Geisterstellen".
  - Page 1 signs: no reply while the ad stays online; reposting.
  - A search snippet adds months or years online, vague text, and listings on portals only. Pages 2–3 were not fetched.
  - [Business Punk](https://www.business-punk.com/work/arbeitgeber-tricks-was-hinter-ghost-jobs-steckt-und-wie-man-sie-erkennt/)
- **Handelsblatt / WirtschaftsWoche** (Anabel Schröter, 09.05.2026; text truncated).
  - Calls ghost jobs "Karteileichen" and "Attrappen".
  - Signals from LinkedIn testimonials: routine interviews with a disengaged interviewer, then no contact, feedback or closure.
  - [Handelsblatt](https://www.handelsblatt.com/karriere/ghost-jobs-bewerberfrust-am-arbeitsmarkt-was-steckt-dahinter/100222908.html)
- **politjobs** (06.05.2026). Its "Ghost Jobs" article lists no ghost signals, only scam indicators: messenger contact, requests for personal data, unrealistic terms. [politjobs](https://politjobs.com/de/de/magazin/ghost-jobs-und-ghosting-am-arbeitsmarkt-20260506)
- **LiveCareer "45% der Personaler" survey.** Published in German on livecareer.de and picked up by German HR outlets, but it surveyed 918 US HR professionals on 25 Mar 2025.
  - How long ghost ads stay online: under 1 week 15%, 1–4 weeks 43%, 1–3 months 37%, indefinitely 5%.
  - 69% "often" close postings without notice and stop responding.
  - [personalintern.de](https://www.personalintern.de/artikel/45-prozent-der-personaler-geben-zu-regelmaessig-ghost-jobs-auszuschreiben/)
- **Not found:** no dedicated ghost-job article from Spiegel, Haufe/Personalwirtschaft, or the StepStone, Indeed DE or XING editorial blogs.
  - The searches surfaced only the Handelsblatt/WiWo piece and third-party HR blogs.
  - Searches for „Scheinstellen“ returned no dedicated article. „Daueranzeige“ and „Talentpool“ returned general talent-pool explainers.
  - [Search context: YoungCapital Talentpool explainer](https://www.youngcapital.de/hr-lexikon/recruitment-marketing/talent-pool)

**German terminology found**

- "Ghost Jobs" is dominant.
- Also used:
  - „Geisterstellen“, „Fake Jobs“ ([Business Punk](https://www.business-punk.com/work/arbeitgeber-tricks-was-hinter-ghost-jobs-steckt-und-wie-man-sie-erkennt/))
  - „Geister-Jobs“ ([NachhaltigeJobs](https://www.nachhaltigejobs.de/geister-jobs/m))
  - „Pseudo-Ausschreibung“, „Scheinausschreibung“, „Fake-Stellenanzeige“, „Pro-forma-Ausschreibung“ ([Karrierebibel](https://karrierebibel.de/pro-forma-ausschreibung/))
  - „Karteileichen“, „Attrappen“ ([Handelsblatt/WiWo](https://www.handelsblatt.com/karriere/ghost-jobs-bewerberfrust-am-arbeitsmarkt-was-steckt-dahinter/100222908.html))
  - „Phantom-Stellenanzeigen“ (snippet) ([Manatal DE](https://www.manatal.com/de/blog/ghost-jobs))

**Where ghost and scam signals are mixed up**

- **Mixed:**
  - Mondo signs 8–10 overlap with fraud markers. [Mondo](https://mondo.com/insights/identifying-ghost-jobs-signs-a-job-posting-may-not-be-real/)
  - MintCareer's signal 10 flags early personal-data requests and broken links. [MintCareer](https://mintcareer.ai/ghost-jobs)
  - Ghost Jobs Index includes "data harvesting". [ghostjobs.net](https://ghostjobs.net/)
  - Karrierebibel lists "Datenhandel" as a pro-forma motive. [Karrierebibel](https://karrierebibel.de/pro-forma-ausschreibung/)
  - politjobs lists only scam indicators under a ghost-job headline. [politjobs](https://politjobs.com/de/de/magazin/ghost-jobs-und-ghosting-am-arbeitsmarkt-20260506)
  - A Chrome extension is named "Ghost Job & Fake Listing Detector". [Chrome Web Store](https://chromewebstore.google.com/detail/ghost-job-fake-listing-de/mdjchaohgneaiflafheajamfomeccach)
  - HiringCafe filters "fake consulting firms" alongside agencies. [Scoutify](https://scoutify.com/blog/hiringcafe-review)
- **Kept separate:**
  - Orbyt, The Muse and The Interview Guys. [Orbyt](https://www.orbytlabs.ai/blog/how-to-spot-ghost-jobs); [The Muse](https://www.themuse.com/advice/ghost-jobs); [Interview Guys](https://blog.theinterviewguys.com/?p=2291)
  - Heidelberg24 runs a separate job-scam article. [Heidelberg24 Job-Scamming](https://www.heidelberg24.de/ratgeber/job-scamming-so-vermeiden-sie-betrugsfallen-bei-der-stellensuche-zr-93389239.html)

### Inferences
- **What German coverage adds.** Ad-text cues for "pro-forma" or internal-candidate postings: tailored or hyper-specific requirements, novel titles, recurring ads. It ties them to statutory posting duties (public sector, § 93 BetrVG). US checklists hardly mention these. In the German framing, many such ads are real vacancies with low odds for outsiders, not frozen roles.
- **Posting age is the most contested signal.**
  - Wenske downgrades it for Germany.
  - Orbyt says a 30-day proxy overcounts slow-but-real hiring.
  - The (US) LiveCareer data suggest most self-reported ghost ads come down within 4 weeks, so an age rule misses them.
  - German media (Golem 60–90 days; Heidelberg24 ">3 Monate") still use age thresholds.
- **Most German articles reuse the same few US sources** (Resume Builder, Clarify Capital, Greenhouse, JOLTS). Their agreement on signals is not independent evidence.

### Gaps
- No German practitioner piece offers data or a test linking any signal to outcomes.
- I couldn't verify Wenske's "one-week objection right" and "PDF ads" details in my fetched version (the legal claims belong to another researcher).
- ingenieur.de's ghost-jobs article returned 404 (only search snippets were seen), and Business Punk pages 2–3 were not fetched.
- No German-language career-coach LinkedIn pieces besides Wenske's were found before the search budget ran out.

## 4. What do job-seeker communities report as signals and outcomes?

### Takeaway
Reddit (r/germany, r/cscareerquestionsEU, r/recruitinghell, r/arbeitsleben) could not be accessed. The tools return "domain not accessible" for reddit.com, and general web search surfaced no Reddit threads. Secondary community evidence mostly concerns outcomes (ghosting after applying or interviewing) and benign reasons for reposts. None of it validates signals.

### Cited Findings
- **Reddit is blocked for the research tools:** WebSearch restricted to reddit.com returned "domain not accessible". This is an environment limitation, not a finding about Reddit.
- **LinkedIn reposts.**
  - A Fishbowl user claims that when companies use free LinkedIn job posts, LinkedIn pauses them after a certain number of applicants, so the company reposts. This is a benign reason for reposting; anecdotal (snippet). [Fishbowl](https://www.fishbowlapp.com/post/can-someone-level-with-me-why-do-jobs-on-like-in-with-hundreds-of-apps-keep-appearing-as-reposted)
  - A Blind thread complains that reposting hides when a role was first posted (snippet). [Blind](https://www.teamblind.com/post/linkedin-should-stop-letting-companies-repost-the-same-job-posting-every-day-m1ecfe5m)
- **German LinkedIn testimonials** quoted by WirtschaftsWoche: a routine interview with an interviewer checking the clock, then no follow-up; "30 applications and 30 rejections", several judged to be ghost jobs. [Handelsblatt/WiWo](https://www.handelsblatt.com/karriere/ghost-jobs-bewerberfrust-am-arbeitsmarkt-was-steckt-dahinter/100222908.html)
- **German reader comment** (Uwe Borchert): estimates 50–67% of postings are "Dummies" and says staffing agencies keep "Strukturstellen" in their databases with a single-digit chance of being requested. Anecdotal, unsourced. [OnlineMarketing.de](https://onlinemarketing.de/karriere/human-resources/ghost-jobs-jede-dritte-stelle-existiert-nicht)
- **Germany candidate behaviour (Greenhouse survey via MoreThanCareer):** 21% of German candidates applied to suspected ghost jobs anyway and 38% refused, against 29% in the US and 27% in the UK. [MoreThanCareer.de](https://morethancareer.de/blog/pharma-bloodbath-part-xvii-ghost-jobs-ghost-candidates-german-data.html); [Yahoo/KRON](https://www.yahoo.com/news/ghost-jobs-rise-according-report-182432320.html)
- **Glassdoor interview reviews (2024):** ghosting was mentioned more after recruiter outreach (6.5%) than after online applications (4.9%) or referrals (3%) (snippet). [Glassdoor blog](https://www.glassdoor.com/blog/conversation-starter-ghosting-2024)
- **Community report sites:**
  - Ghost Jobs Index: 609 complaints about 573 companies; the top five are Google, Amazon, Microsoft, Deloitte and Accenture. Mostly US. [ghostjobs.net](https://ghostjobs.net/)
  - GhostJobs.io: 267 reports in categories such as "Frequently Reposted" and "Poor Follow-up Process". [GhostJobs.io](https://ghostjobs.io/)
- **Indeed "employer reviewed X days ago":** forum users see inconsistent values for the same ad, which undermines it as a signal (snippet). [City-Data](https://www.city-data.com/forum/work-employment/3264375-indeed-employer-actively-reviewed-candidates-days.html)
- **Unconfirmed statistic:** an Appinio survey for Indeed (March 2026, 1,000 employees) reportedly found 63.5% got no response to at least one application in 12 months (snippet). The primary source was not located. Politjobs, which appeared to discuss it, did not contain it. [politjobs](https://politjobs.com/de/de/magazin/ghost-jobs-und-ghosting-am-arbeitsmarkt-20260506)

### Inferences
- Community material mostly reports outcomes after the fact (non-response, interview ghosting). Those are the "labels" a validation study would need, not pre-application signals.
- Community report databases (Skip This Job thumbs-down, GhostJobs.io, Ghost Jobs Index) are the only places such outcomes are collected at scale. They are thin, US-centred and not verified.
- Recruiter-outreach interviews being ghosted more than online applications is a caveat for any rule treating recruiter contact as positive. That data comes from Glassdoor's US-centred reviews.

### Gaps
- Reddit threads are unavailable. A German-language community sample (r/arbeitsleben, r/germany, Toytown, iamexpat forums) was not reviewed. A follow-up with a tool that can read Reddit is needed.
- No community-sourced data links a specific pre-application signal (age, repost label, applicant count) to an outcome.

## 5. Consolidated signal catalogue: consensus count, evidence, and German scrapability

### Takeaway
Across 31 sources (15 tools, 6 English-language practitioner pieces of which 2 focus on Germany, 10 German-language articles), the most widely cited signals are:

| Signal | Sources (of 31) |
|---|---|
| Long posting age | 26 |
| Reposting / re-publication | 24 |
| Vague or generic description | 17 |
| Not on the employer's careers page | 13 |
| No response after applying | 13 |
| Missing or implausible salary | 12 |
| No named contact | 9 |
| Negative reviews or community reports | 9 |
| Evergreen / talent-pool wording | 8 |

Only Remote Rocketship's descriptive, partly circular numbers bear on whether any signal works; no source validates one against hiring outcomes. For Germany, the BA Jobbörse API makes age, re-publication, start date, openings, fixed-term status and agency/anonymous flags machine-readable. LinkedIn exposes the "Reposted" label, applicant counts and responsiveness labels on the page. StepStone and XING would need repeated crawling with fingerprints to see age and reposts.

### Cited Findings

**Source key and counting rules**

- A source "cites" a signal if it lists it as a warning or positive sign or uses it in a score. Mentions only as a motive don't count.
- Karrierebibel's two articles share an author and count once (G1).
- Syndicated Ippen copies count once with Heidelberg24 2026 (G4).
- Snippet-only pages (ingenieur.de, wirtschaftsforum.de, Business Punk pages 2–3) are not counted.
- "Independent" means a distinct publisher or maker. Many sources draw on the same US surveys, so agreement is not independent evidence.

Tools (T):
- [T1] GhostJob (Chrome, clbbop…) – https://chromeboard.com/extension/ghostjob-ghost-job-detect-clbbopifmidceplphamfdfapgacgbhnd
- [T2] Skip This Job – https://www.skipthisjob.com/how-it-works
- [T3] ghostjobdetector.app – https://ghostjobdetector.app/how-it-works
- [T4] JobGhosting – https://jobghosting.leveragepointadvisory.co/transparency
- [T5] Apify robotninja Ghost Job Detector – https://apify.com/robotninja/ghost-job-detector
- [T6] Apify Job Lifecycle Monitor – https://apify.com/gganbukim/job-lifecycle-monitor
- [T7] GhostCheck – https://ghostcheck.app/
- [T8] Adsidera (GitHub) – https://github.com/Adsidera/ghost-job-detector
- [T9] pulkitchowdry (GitHub) – https://github.com/pulkitchowdry/ghostjobdetector
- [T10] Ghost-Job Detector (Chrome, gpalk…) – https://chromeboard.com/extension/ghost-job-detector-gpalkeokdmojnnlhgpelfnfmnffnkmhi
- [T11] MintCareer – https://mintcareer.ai/ghost-jobs
- [T12] GhostJobs.io – https://ghostjobs.io/
- [T13] Ghost Jobs Index – https://ghostjobs.net/
- [T14] HiringCafe (via Scoutify) – https://scoutify.com/blog/hiringcafe-review
- [T15] Remote Rocketship ghost score – https://www.remoterocketship.com/advice/ghost-jobs-report/

English-language practitioners (P):
- [P1] Mondo – https://mondo.com/insights/identifying-ghost-jobs-signs-a-job-posting-may-not-be-real/
- [P2] The Interview Guys – https://blog.theinterviewguys.com/?p=2291
- [P3] Orbyt Labs – https://www.orbytlabs.ai/blog/how-to-spot-ghost-jobs
- [P4] The Muse – https://www.themuse.com/advice/ghost-jobs
- [P5] Bernd Wenske (Germany) – https://www.linkedin.com/pulse/decoding-ghost-job-how-spot-frozen-roles-german-market-bernd-wenske-vys6e/
- [P6] MoreThanCareer.de (Germany) – https://morethancareer.de/blog/pharma-bloodbath-part-xvii-ghost-jobs-ghost-candidates-german-data.html

German-language articles (G):
- [G1] Karrierebibel (Ghost Jobs and Pro-forma) – https://karrierebibel.de/ghost-jobs/
- [G2] t3n – https://t3n.de/news/vorsicht-vor-ghost-jobs-so-erkennst-du-fake-stellenanzeigen-1670553/
- [G3] Golem Karrierewelt – https://karrierewelt.golem.de/blogs/karriere-ratgeber/ghost-jobs-wenn-stellenanzeigen-nur-der-imagepflege-dienen
- [G4] Heidelberg24 (2026) – https://www.heidelberg24.de/verbraucher/ghost-jobs-so-erkennen-sie-fake-stellenanzeigen-im-netz-zr-94391464.html
- [G5] Heidelberg24 (2024) – https://www.heidelberg24.de/ratgeber/das-raetsel-der-ghost-jobs-warum-bewerbungen-ins-leere-laufen-zr-93433508.html
- [G6] NachhaltigeJobs – https://www.nachhaltigejobs.de/geister-jobs/m
- [G7] HR monkeys – https://hr-monkeys.de/blog/ghost-jobs/
- [G8] OnlineMarketing.de – https://onlinemarketing.de/karriere/human-resources/ghost-jobs-jede-dritte-stelle-existiert-nicht
- [G9] Business Punk (page 1) – https://www.business-punk.com/work/arbeitgeber-tricks-was-hinter-ghost-jobs-steckt-und-wie-man-sie-erkennt/
- [G10] Handelsblatt/WiWo – https://www.handelsblatt.com/karriere/ghost-jobs-bewerberfrust-am-arbeitsmarkt-was-steckt-dahinter/100222908.html

Platform and data documentation:
- [L1] LinkedIn responsiveness insights – https://www.linkedin.com/help/learning/answer/a1655396 (German: https://www.linkedin.com/help/linkedin/answer/a1655396?lang=de)
- [L2] LinkedIn job verification badge – https://www.linkedin.com/help/linkedin/answer/a1492056
- [L3] LinkedIn repost help – https://www.linkedin.com/help/learning/answer/a522249
- [I1] Indeed „Aktiver Arbeitgeber“ / Responsive Employer – https://www.indeed.com/help/employers/articles/what-is-an-employer-response-badge
- [I2] Indeed „Dringend gesucht“ – https://de.indeed.com/arbeitgeber/recruitingloesungen/attract
- [B1] BA Jobsuche API spec – https://raw.githubusercontent.com/bundesAPI/jobsuche-api/main/openapi.yaml
- [S1] StepStone info labels (snippet) – https://www.stepstone.de/e-recruiting/hr-wissen/recruiting/bewerbung-leicht-gemacht
- [GH1] Greenhouse Verified – https://www.greenhouse.com/greenhouse-verified
- [LC] LiveCareer survey (US) via personalintern – https://www.personalintern.de/artikel/45-prozent-der-personaler-geben-zu-regelmaessig-ghost-jobs-auszuschreiben/
- [GD] Glassdoor ghosting data (snippet) – https://www.glassdoor.com/blog/conversation-starter-ghosting-2024

[T1]: https://chromeboard.com/extension/ghostjob-ghost-job-detect-clbbopifmidceplphamfdfapgacgbhnd
[T2]: https://www.skipthisjob.com/how-it-works
[T3]: https://ghostjobdetector.app/how-it-works
[T4]: https://jobghosting.leveragepointadvisory.co/transparency
[T5]: https://apify.com/robotninja/ghost-job-detector
[T6]: https://apify.com/gganbukim/job-lifecycle-monitor
[T7]: https://ghostcheck.app/
[T8]: https://github.com/Adsidera/ghost-job-detector
[T9]: https://github.com/pulkitchowdry/ghostjobdetector
[T10]: https://chromeboard.com/extension/ghost-job-detector-gpalkeokdmojnnlhgpelfnfmnffnkmhi
[T11]: https://mintcareer.ai/ghost-jobs
[T12]: https://ghostjobs.io/
[T13]: https://ghostjobs.net/
[T14]: https://scoutify.com/blog/hiringcafe-review
[T15]: https://www.remoterocketship.com/advice/ghost-jobs-report/
[P1]: https://mondo.com/insights/identifying-ghost-jobs-signs-a-job-posting-may-not-be-real/
[P2]: https://blog.theinterviewguys.com/?p=2291
[P3]: https://www.orbytlabs.ai/blog/how-to-spot-ghost-jobs
[P4]: https://www.themuse.com/advice/ghost-jobs
[P5]: https://www.linkedin.com/pulse/decoding-ghost-job-how-spot-frozen-roles-german-market-bernd-wenske-vys6e/
[P6]: https://morethancareer.de/blog/pharma-bloodbath-part-xvii-ghost-jobs-ghost-candidates-german-data.html
[G1]: https://karrierebibel.de/ghost-jobs/
[G2]: https://t3n.de/news/vorsicht-vor-ghost-jobs-so-erkennst-du-fake-stellenanzeigen-1670553/
[G3]: https://karrierewelt.golem.de/blogs/karriere-ratgeber/ghost-jobs-wenn-stellenanzeigen-nur-der-imagepflege-dienen
[G4]: https://www.heidelberg24.de/verbraucher/ghost-jobs-so-erkennen-sie-fake-stellenanzeigen-im-netz-zr-94391464.html
[G5]: https://www.heidelberg24.de/ratgeber/das-raetsel-der-ghost-jobs-warum-bewerbungen-ins-leere-laufen-zr-93433508.html
[G6]: https://www.nachhaltigejobs.de/geister-jobs/m
[G7]: https://hr-monkeys.de/blog/ghost-jobs/
[G8]: https://onlinemarketing.de/karriere/human-resources/ghost-jobs-jede-dritte-stelle-existiert-nicht
[G9]: https://www.business-punk.com/work/arbeitgeber-tricks-was-hinter-ghost-jobs-steckt-und-wie-man-sie-erkennt/
[G10]: https://www.handelsblatt.com/karriere/ghost-jobs-bewerberfrust-am-arbeitsmarkt-was-steckt-dahinter/100222908.html
[L1]: https://www.linkedin.com/help/learning/answer/a1655396
[L2]: https://www.linkedin.com/help/linkedin/answer/a1492056
[L3]: https://www.linkedin.com/help/learning/answer/a522249
[I1]: https://www.indeed.com/help/employers/articles/what-is-an-employer-response-badge
[I2]: https://de.indeed.com/arbeitgeber/recruitingloesungen/attract
[B1]: https://raw.githubusercontent.com/bundesAPI/jobsuche-api/main/openapi.yaml
[S1]: https://www.stepstone.de/e-recruiting/hr-wissen/recruiting/bewerbung-leicht-gemacht
[GH1]: https://www.greenhouse.com/greenhouse-verified
[LC]: https://www.personalintern.de/artikel/45-prozent-der-personaler-geben-zu-regelmaessig-ghost-jobs-auszuschreiben/
[GD]: https://www.glassdoor.com/blog/conversation-starter-ghosting-2024

**Catalogue, ranked by number of citing sources (of 31)**

Direction: ↑ raises ghost likelihood, ↓ lowers it.

| # | Signal | Operational definition (thresholds as used) | Where to get it | Dir. | Sources citing (T / P / G) |
|---|---|---|---|---|---|
| 1 | Long posting age | Days since first publication, or first seen, above a threshold: 30d [T3] [T7] [P3]; 60d [T4] [T11] [P2]; 60–90d [G3]; ">3 Monate" [G4]; graded 7/14/30/60/90/120d with minimum scores [T2]; 60/90/180d, 1y, 2y [T5]; relative to the company's own fill-time baseline [T15] or the board median [T6]. ≤2 days lowers it [T2] | Board date; ATS `firstPublishedAt`/`updatedAt` [T6]; BA `ersteVeroeffentlichungsdatum`, `aktuelleVeroeffentlichungsdatum`, `modifikationsTimestamp`, filter `veroeffentlichtseit` [B1] | ↑ | **26** = 12 (T1–T11, T15) / 6 (P1–P6; P5 calls it weak in DE) / 8 (G2–G9) |
| 2 | Reposting / re-publication | Same role (normalised title ± location ± description hash) re-published under a new ID or with a refreshed date. LinkedIn "Reposted" label +24 [T2]; Ghost = ≥3 ID rotations over ≥90 days [T4]; +15 per repost, max +30 [T5]; ≥2 revivals = full penalty [T15]; tracked ≥6× sets minimum 75 [T2]; "three strikes" [P2]; „alle paar Monate“ [G1] | LinkedIn "Reposted" label; your own repeated crawl; BA first vs current publication date on the same `refnr` [B1] | ↑ (P5: frequent reposts on the own careers page ↓; cosmetic reposts ↑) | **24** = 13 (T1–T12, T15) / 4 (P1, P2, P3, P5) / 7 (G1, G2, G4, G5, G6, G7, G9) |
| 3 | Vague, generic or boilerplate description | Short text: LinkedIn <200 or <500 characters, Indeed <280 [T2]; high share of generic phrases [T2] [T3]; no named tools, team, reporting line or business reason [P1] [T3]; leftover template tokens [T2] | Description text; BA `stellenbeschreibung` [B1] | ↑ (specific text ↓ [T2] [T1]; P5: generic profile = external hiring ↓) | **17** = 8 (T1, T2, T3, T7, T8, T9, T11, T12) / 4 (P1–P4) / 5 (G1, G3, G4, G5, G6) |
| 4 | Not on the employer's careers page or ATS | No matching posting (title or requisition ID) on the employer's careers site or ATS. "Fastest disqualifier" [P3]; ATS verification weight 25% [T9]; careers-site match [T1]; feed removal tracking [T14] | Employer site or ATS endpoints; BA `externeUrl`, `arbeitgeberdarstellungUrl` [B1] | ↑ (present ↓) | **13** = 3 (T1, T9, T14) / 5 (P1, P3, P4, P5, P6) / 5 (G1–G5) |
| 5 | No response after applying / ghosting record | No acknowledgement after applying and following up; community ghost reports | Own tracker; community reports [T2] [T9] [T12] [T13]; kununu or Glassdoor reviews | ↑ (G4: a delayed reply alone is no proof) | **13** = 4 (T2, T9, T12, T13) / 3 (P2, P3, P4) / 6 (G3, G6, G7, G8, G9, G10) |
| 6 | Salary missing or implausible | No pay figure or only "competitive" (18/114, the top weight) [T3]; range top ≥2× bottom [T3]; +5 / +4, shown −2 [T2]; seniority–pay mismatch [T11]; 70k–180k example [G4] | Salary field; BA `verguetung` (free text) [B1] | ↑ (shown ↓) | **12** = 7 (T1, T2, T3, T7, T8, T11, T15) / 4 (P1, P2, P3, P6) / 1 (G4) |
| 7 | No named hiring manager or contact | No recruiter or manager named; no reporting line; impersonal info@ address [G5] | LinkedIn hiring team / poster pane [T2]; ad text. BA API has no contact fields [B1] | ↑ | **9** = 4 (T1, T2, T3, T11) / 3 (P1, P2, P3) / 2 (G1, G5) |
| 8 | Negative reviews or community reports about the employer | Reports of no interviews or hires for months, ghosting, bait-and-switch; Indeed rating <2.5 +10, ≥4.0 −3 [T2] | Glassdoor, kununu, Reddit; ghost indexes [T12] [T13] | ↑ | **9** = 4 (T2, T9, T12, T13) / 1 (P2) / 4 (G1, G2, G4, G5) |
| 9 | Evergreen / "always hiring" / talent-pool wording | Pipeline phrasing ("always looking", "talent pool", "future opportunities", general application). 10/114 [T3]; +15 [T5]; separate "Evergreen" class [T4] | Title and description text | ↑ for "no specific vacancy" (often treated as its own class) | **8** = 3 (T3, T4, T5) / 4 (P1, P3, P5, P6) / 1 (G7) |
| 10 | Unrealistic or contradictory requirements | Entry-level asking 5+ [P2] or 7–10 years [P1]; title vs experience mismatch +14/+13 [T2]; „eierlegende Wollmilchsau“ [G1] | Text; BA `fertigkeiten`, `fuehrungskompetenzen` [B1] | ↑ | **6** = 3 (T1, T2, T11) / 2 (P1, P2) / 1 (G1) |
| 11 | Staffing agency or job board as poster; masked employer; several agencies | Agency or job-board poster +12 [T2]; unnamed or "confidential" employer +6 [T3]; same job from several agencies [P1]; board-only "agency fishing" [P6] | Poster identity; BA filters `zeitarbeit`, `pav`, flag `anzeigeAnonym` [B1] | ↑ | **6** = 4 (T2, T3, T14, T15) / 2 (P1, P6) / 0 |
| 12 | Employer track record across postings | Company slow-close rate (180+ days or aged out) [T15]; median company score [T2]; company openings unchanged for 90 days [T5]; company's other postings stale [T11]; "repeat offenders" [T4]; three strikes [P2] | Your own history of the employer's postings (longitudinal archive) | ↑ | **6** = 5 (T2, T4, T5, T11, T15) / 1 (P2) / 0 |
| 13 | Company distress or growth news | Freeze, layoffs or restructuring ↑; funding, contracts or expansion ↓ [P5]; product pipeline loss of exclusivity [P6] | News, employer posts, filings (off-board) | ↑ / ↓ | **4** = 0 / 4 (P1, P2, P5, P6) / 0 |
| 14 | Many openings relative to headcount or growth | Live openings ÷ LinkedIn headcount (weight 20) [T15]; headcount flat while dozens of roles open [G4]; many active postings without visible growth [G6]; company board static [T5] | LinkedIn headcount; BA `anzahlOffeneStellen` + `betriebsgroesse` [B1] | ↑ (P5: clusters of related openings ↓) | **4** = 2 (T5, T15) / 0 / 2 (G4, G6) |
| 15 | Concrete timeline (start date, interview steps, deadline, probation) | Present ↓, absent ↑ [T11] [P2] [P3] [P5] [P6] | Text; BA `eintrittsdatum` [B1] | ↓ when present | **5** = 1 (T11) / 4 (P2, P3, P5, P6) / 0 |
| 16 | Applicant volume, especially on old posts | 100+/200+/500+ applicants [T2]; 200+ [T7]; applicants relative to age [T8] [T9]; „mehrere Hundert oder Tausend“ [G3] | LinkedIn applicant count (read by tools) | ↑ (ambiguous: could just be a popular job) | **5** = 4 (T2, T7, T8, T9) / 0 / 1 (G3) |
| 17 | Asking directly; evasive or no answer | Ask whether headcount is approved, the target start date, whether the job is still open [P6] [G1] [P2] [P4]; evasive replies [G3] | Email or phone to the contact | ↑ if evasive | **5** = 0 / 3 (P2, P4, P6) / 2 (G1, G3) |
| 18 | Hyper-specific or tailored requirements (internal candidate, pro-forma ad) | Unusually narrow skill, certification or regional combinations matching one known person [P5] [G1]; public-sector variant [G6] | Text; BA `fertigkeiten` [B1] | ↑ for "not externally fillable" (G6: often a real vacancy) | **3** = 0 / 1 (P5) / 2 (G1, G6) |
| 19 | Novel, hype or stacked job title | „Neuartige Jobtitel“ [G1]; "Superstar Sales Guru" [G3]; vague or stacked title 10/114 [T3]; buzzy titles [T1] | Title | ↑ | **4** = 2 (T1, T3) / 0 / 2 (G1, G3) |
| 20 | Urgency without specifics | "Urgent" wording with no detail [T3]; urgency on a weeks-old listing [T8] [T1] | Text. Indeed DE „Dringend gesucht“ is a **paid** label [I2] | ↑ | **3** = 3 (T1, T3, T8) / 0 / 0 |
| 21 | Easy Apply / low-friction application on old posts | Easy Apply at 60/90/120d+: +8/+10/+12 [T2]; Easy Apply [T7]; "overly simple applications" [P2] | LinkedIn Easy Apply; StepStone „Schnelle Bewerbung“ [S1] (not linked to ghosts by any source) | ↑ | **3** = 2 (T2, T7) / 1 (P2) / 0 |
| 22 | AI-style or template text | AI-style language [T1]; template tokens [T2]; "possibly AI-written" [P4] | Text | ↑ | **3** = 2 / 1 / 0 |
| 23 | Interview-stage behaviour | Routine or disengaged interviews [G10]; no decision path; salary never discussed [G6]; drawn-out processes [G8] | After applying | ↑ | **3** = 0 / 0 / 3 (G6, G8, G10) |
| 24 | Instant automated rejection | Rejection "within minutes" [P2] or "instant" [P1] | After applying | ↑ (but counts as "responsiveness" on LinkedIn and Indeed [L1] [I1]) | **2** = 0 / 2 / 0 |
| 25 | Named hiring manager publicly active about growth | Recent posts by the hiring manager about growth or launches [P5]; "no recruiter or active hiring manager" [P3] | LinkedIn profiles (off-board) | ↓ | **2** = 0 / 2 (P3, P5) / 0 |
| 26 | Identical posts across many locations or boards | Identical posts in "numerous" cities [P2]; number of boards a job appears on [T10] (direction not stated) | Search across boards and locations | ↑ (P2) | **2** = 1 / 1 / 0 |
| 27 | Posting date missing | No date [G2] (↑); missing date scores 0 [T2] | Board | ↑ / neutral | **2** = 1 / 0 / 1 |
| 28 | Platform responsiveness label | LinkedIn "Actively reviewing applicants" (DE „Bewerber:innen werden aktiv geprüft“) −8 (<60d); no review +10; Indeed "often replies" line present −5, missing +8 [T2]. Indeed's separate responsiveness badge is „Aktiver Arbeitgeber“ [I1]; whether T2's "often replies" line is the same element is not stated | LinkedIn [L1]; Indeed [I1] | ↓ when present (weak: auto-rejections count) | **1** = 1 (T2) / 0 / 0 |
| 29 | Off-platform application | "Responses managed off LinkedIn" +10; apply leaves Indeed +5 [T2] | LinkedIn [L1]; Indeed | ↑ per T2 (but the LinkedIn label only means no data; P3 and P5 treat careers-page applications as positive) | **1** = 1 / 0 / 0 |
| 30 | Works-council or statutory posting language | Mentions of Betriebsrat involvement, internal or statutory posting [P5]; mentioned as context only in G1, G6, P6 | Text keywords; BA `nurFuerSchwerbehinderte` flag (relevance is an inference) [B1] | ↑ for a "compliance posting" | **1** = 0 / 1 (P5) / 0 |
| 31 | Cluster of related openings in one department | Several aligned openings ↓; an isolated posting ↑ [P5] | Employer's postings by department; BA `arbeitgeber` filter [B1] | ↓ when clustered | **1** |
| 32 | Fixed-term offer | „Befristetes Angebot“, not a sign on its own [G1] | BA `befristung` [B1] | weak ↑ | **1** |
| 33 | Funding contingency | "vorbehaltlich einer Förderzusage" [G6] | Text (non-profit, public funding) | ↑ | **1** |
| 34 | Outdated information | Old technology references [P2] | Text | ↑ | **1** |
| 35 | Work-arrangement tag contradicts the text | +8 [T2] | Tag vs text | ↑ | **1** |
| 36 | Trust boosters | Benefits, flexible work, growth opportunities, clear responsibilities [T1] | Text | ↓ | **1** |
| 37 | Verification badges | LinkedIn verified job [L2] (used as data by [T11]); Greenhouse Verified [GH1] | LinkedIn; MyGreenhouse | ↓ (LinkedIn: "does not mean you are more likely to be hired") | **1** |
| 38 | Employer-type prior | Multinational, Betriebsrat corporate, Mittelstand, scale-up [P5]; public sector, NGOs [G6]; public sector, health, large corporations [G8] | BA `betriebsgroesse`, `branche` [B1] | context | **3** = 0 / 1 / 2 |

**Germany-relevant ranking.** The 10 German-language articles plus the 2 Germany-focused English pieces (P5, P6), 12 sources in all:

| Signal | Germany-relevant sources (of 12) |
|---|---|
| Posting age | 10 (but P5 calls it weak) |
| Reposting | 8 |
| Careers-page absence | 7 |
| No response after applying | 6 |
| Vague description | 5 |
| Negative reviews | 4 |
| Hyper-specific requirements | 3 (G1, G6, P5) |
| Asking directly | 3 |
| Evergreen wording | 3 |
| Interview-stage behaviour | 3 |
| Salary | 2 (G4, P6) |
| Novel titles | 2 |
| Openings vs growth | 2 |
| Timeline | 2 |
| Company news | 2 |
| Works-council language | 1 (P5) |

Sources as per the catalogue rows above.

**Evidence that signals work (all sources found)**

- **Posting age.**
  - At Remote Rocketship, the median company fills a role in about 35 days, the median "likely ghost" has been open 187 days (average 208), and healthy listings average 50 days. [T15]
  - This is circular: age is 35% of the score that defines "likely ghost".
  - Counter-evidence (US): in the LiveCareer survey, HR staff reported ghost ads stay online under 1 week 15%, 1–4 weeks 43%, 1–3 months 37%, indefinitely 5%. A 30-day rule would miss most self-reported ghost ads. [LC]
  - Orbyt says the 30-day proxy overcounts slow senior hiring [P3]. Wenske's Probezeit argument is unsourced [P5]. Aggregator "Just posted" dates reflect data syncs [P6].
- **Salary.** 92% of likely ghosts hide pay, against 52% of other listings. [T15] Salary is only 10% of that score, but the comparison is still partly circular. In Germany private employers are not yet obliged to post ranges [P6], so the signal is likely to discriminate poorly in Germany (inference).
- **Agency posters.** Staffing agencies make up 3% of listings but 10.8% of likely ghosts. [T15]
- **Open roles vs headcount.** 427 companies advertise more roles than they have employees. The headcount signal was checked at group level against CoreSignal data for 125 companies. [T15]
- **Employer concentration.** 93.2% of companies have no likely ghosts; 6.8% (3,147) produce all of them. Employer-level history is therefore informative, though the finding is descriptive. [T15]
- **Reposting.** Only about 2% of live listings had been revived at least once [T15]. Benign causes:
  - LinkedIn lets employers repost closed or expired jobs at any time [L3].
  - LinkedIn reportedly pauses free posts after a number of applicants (anecdote) [Fishbowl](https://www.fishbowlapp.com/post/can-someone-level-with-me-why-do-jobs-on-like-in-with-hundreds-of-apps-keep-appearing-as-reposted).
  - Recurring ads can reflect staff turnover [G1].
- **Responsiveness labels.** Auto, bulk and manual rejections, profile views and resume downloads count as a LinkedIn "review" [L1]. Automatic rejection emails count for Indeed's badge, even after a listing closes [I1]. So a label shows activity in the employer's account, not a live requisition.
- **No response after applying.** In 2024 Glassdoor reviews, ghosting was mentioned in 6.5% of recruiter-outreach interviews, 4.9% of online-application interviews and 3% of referral interviews [GD]. 69% of US HR staff "often" close postings without notice [LC].
- **Evergreen wording.** Clarify Capital 2022 (via The Muse): 50% of hiring managers say the company is "always open", 37% keep an applicant pool [P4]. Remote Rocketship had to fix a bug that over-flagged evergreen government postings [T15].
- **Everything else** (description quality, careers-page absence, named contact, hyper-specific requirements, works-council language, timelines, titles, urgency, Easy Apply, applicant volume): no evidence found that it predicts outcomes.
- **Data-quality risk.** JobGhosting's Workday reader bug (29 Jun to 10 Aug 2026; 28,246 false closures) shows that longitudinal signals depend on complete crawls. [T4]

**Where each signal can be scraped from German platforms (only sourced facts; "unverified" = not established in this research)**

| Signal | BA Jobbörse (API) | LinkedIn (DE) | Indeed (DE) | StepStone / XING | Employer careers / ATS |
|---|---|---|---|---|---|
| Posting age | Yes: first and current publication dates, `modifikationsTimestamp`, `veroeffentlichtseit` [B1] | Yes, read on page by tools [T2] [T8]; DE wording unverified | Partly visible (indeed.com analysis) [T3]; DE unverified | Unverified; build your own first-seen dates | Yes: Greenhouse/Lever/Ashby/SmartRecruiters timestamps [T5] [T6]; Personio not covered by any tool [T6] |
| Reposting | Yes for re-publication under the same `refnr` (first vs current date) [B1]; new-`refnr` reposts need fingerprinting (inference) | "Reposted" label read by tools [T2] [T8]; DE wording unverified | Repost history hidden (indeed.com) [T3] | No label found; repeated crawl plus fingerprint as in [T4] [T6] | ID-rotation tracking [T4] [T6] |
| Careers-page / ATS presence | `externeUrl`, `arbeitgeberdarstellungUrl` give links [B1] | "Responses managed off LinkedIn" = external ATS [L1] | Apply leaves Indeed [T2] | Unverified | Match against ATS endpoints [T4] [T9] |
| Salary | `verguetung` free text [B1] | Partly visible [T3] | Partly visible (indeed.com) [T3] | Unverified | Some ATS expose `salaryRange` [T6] |
| Named contact | **No contact fields** in the API [B1] | Hiring-team pane read by tools [T2] | Unverified | Unverified (ad text) | Varies |
| Applicant count | Not in API [B1] | Yes, read by tools [T2] [T7] [T8] | Not found | Not found | No |
| Responsiveness label | No | „Bewerber:innen werden aktiv geprüft“, „Die Prüfungszeit beträgt …“, „Noch keine Antwort verfügbar“, „Außerhalb von LinkedIn verwaltete Antworten“ [L1] | „Aktiver Arbeitgeber“ [I1] | None found | No |
| Agency or masked employer | `zeitarbeit` and `pav` filters, `anzeigeAnonym` flag [B1] | Tool detection, method undisclosed [T2] | Same [T2] | Unverified | n/a |
| Openings vs size | `anzahlOffeneStellen`, `betriebsgroesse` [B1] | Headcount [T15] (scraping legality out of scope) | No | Unverified | Count of open requisitions [T4] |
| Timeline / start date | `eintrittsdatum` [B1] | Text | Text | Text | Text |
| Fixed-term | `befristung` [B1] | Text | Text | Text | Text |
| Text-based signals (vague, evergreen, tailored, works council, urgency, titles) | `stellenbeschreibung`, `titel`, `fertigkeiten` [B1] | Text | Text | Text | Text |
| Paid urgency label | n/a | Unverified ("Promoted") | „Dringend gesucht“ = paid [I2] | „Schnelle Bewerbung“ and „Anschreiben nicht erforderlich“ = employer-set labels [S1] | n/a |
| Reviews | n/a | n/a | Indeed employer rating [T2] | XING showed kununu ratings (2014; unverified now) | kununu, Glassdoor |

**Wenske's seven signals compared with the consensus**

| Wenske signal | Catalogue row | Agreement |
|---|---|---|
| 1. Repost pattern on own careers page vs aggregators | #2 (24) and #4 (13) | Broad agreement that reposts and careers-page checks matter. Wenske's "frequent careers-page reposting = ongoing investment" is a minority view; his "cosmetic reposts" red flag matches the majority. |
| 2. Named hiring-manager activity | #25 (2); related #7 (9) | Rare as a positive signal; only Orbyt and Wenske. |
| 3. Public company signals | #13 (4), #14 (4) | Practitioner-only; no tool checks news. |
| 4. Hyper-specific requirements | #18 (3) | Only DACH sources: Wenske, Karrierebibel, NachhaltigeJobs. |
| 5. Works-council or statutory language | #30 (1) | Wenske is the only source that turns it into a text signal; others mention it as a motive. |
| 6. Timeline details | #15 (5) | Moderate. BA `eintrittsdatum` makes the start date machine-readable [B1]. |
| 7. Clusters vs isolated postings | #31 (1) | Unique to Wenske. Conflicts with #14 (many openings without growth ↑) [T15] [G4] [G6]. |
| Posting age weak in Germany | #1 (26) | Contradicts most sources. Partly supported by Orbyt's caveat [P3], the (US) LiveCareer duration data [LC] and the aggregator-date caveat [P6]. |

### Inferences
- **Signals cluster into three families:**
  1. Posting lifecycle (age, reposts, careers-page presence). This is the largest consensus and the most machine-readable family. Validation is weakest because it is circular.
  2. Ad text (vagueness, salary, contact, evergreen, tailored requirements, titles). Easy to compute but needs German NLP; nothing validated.
  3. Employer-level behaviour (track record, responsiveness, community reports, headcount ratio). This family has the only non-trivial descriptive evidence, Remote Rocketship's strong employer concentration.
  - For Germany, a design built on employer-level history from repeated BA and StepStone crawls is likely to beat per-ad text heuristics. This is an inference, not tested.
- **Probably weak or misleading in Germany** (inference from the sourced facts above):
  - Missing salary: no legal obligation yet for private employers [P6].
  - Platform responsiveness labels: auto-rejections count [L1] [I1].
  - "Urgent" labels: paid [I2].
  - Raw posting age: Wenske's Probezeit claim [P5] and the BAG example of ads staying online after selection [P6].
- **The pro-forma family should be scored separately from "frozen" ghosts.** Hyper-specific requirements, works-council or statutory language, public-sector employers and short internal windows describe real vacancies that are not externally fillable [G6] [P5]. They need a different label from "frozen role", which is what Wenske means by ghost.
- **Scam signals should be excluded from a ghost score.** Money or fee requests, early personal-data requests, messenger-only contact, broken links and "Datenhandel" are fraud markers that several sources mix in [T11] [T13] [P1].

### Gaps
- No source validates any signal against hiring outcomes in Germany or elsewhere. Remote Rocketship's associations are partly circular, and LiveCareer's duration data are US self-reports.
- German UI wording for LinkedIn and Indeed age, repost, Promoted, Easy Apply and applicant-count labels is unverified. So are StepStone, XING and Glassdoor DE label semantics and current XING–kununu integration.
- Unknown whether the BA Jobbörse re-uses `refnr` across re-publications or issues new ones. That decides whether first vs current publication date captures all reposts.
- No German-language implementations of the text heuristics were found. Thresholds for German ads (for example, minimum description length) are undefined.
- Reddit and other community sources could not be accessed, so the community consensus count is missing from this catalogue.
