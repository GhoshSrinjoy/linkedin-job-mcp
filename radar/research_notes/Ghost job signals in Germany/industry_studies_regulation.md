# Ghost jobs: industry studies, employer surveys, regulation and platform policy (US, UK, Canada; EU/DE in brief)

Scope note: covers studies, surveys, laws, bills and platform policies, 2022–Oct 2026. Academic economics, detection tools, German labour law, German data sources, scraping law and ML are out of scope (other researchers). "Ghost job" here means a posting for a role that does not exist or that the employer does not intend to fill soon. Scam or fraudulent ads (fake employers, phishing, payment requests) are a separate category and are flagged wherever a study mixes the two. Research date: 24 Oct 2026. The shared web-search budget ran out partway through, so some items are marked "search excerpt" (seen only in a search-result summary, not on a fetched page) or listed as gaps.

---

## Q1. Study catalogue: what exactly was measured, and how credible is each figure?

### Takeaway
No figure in this literature measures "postings with no intent to hire" directly. They fall into six families that cannot be compared: (1) platform outcome data (Greenhouse 18–22%, Revelio's hires-per-posting ratio); (2) listing-age or heuristic scrapes (StandOut CV 34.4%, ResumeUp.AI 27.4%, the Outten & Golden analysts' 26.4%, JobsPipe); (3) a macro openings-to-hires gap (MyPerfectResume's ~30% from JOLTS), which is not a ghost-job measure at all; (4) employer or recruiter self-report surveys that measure the share of *respondents*, not postings (ResumeBuilder 40%, LiveCareer 45%, MyPerfectResume 81%, Clarify Capital); (5) job-seeker perception surveys; (6) official sources (CRS, BLS), which say there is no official measure. Almost every source has a commercial interest: resume builders, ATS vendors, job-data vendors, or a plaintiff-side law firm's analysts. The most defensible numbers are Greenhouse's platform figure and Revelio's ratio, and even those have unpublished or proxy definitions.

### Cited Findings

#### A. Platform / ATS-measured data

**Greenhouse platform data: "18–22% of postings in any given quarter"**
- Who and when: Greenhouse (an ATS vendor) disclosed it in its *2024 State of Job Hunting* report (blog dated 10 Dec 2024). The report says "18–22% of jobs posted on the Greenhouse platform in any given quarter were classified as ghost jobs". This is platform data, not survey data. The report defines ghost jobs as "positions advertised with no intent to hire". — [Greenhouse UK blog](https://www.greenhouse.com/uk/blog/greenhouse-2024-state-of-job-hunting-report); [ClearStar summary](https://www.clearstar.net/?p=6218)
- Method: Greenhouse has not published its classification rule. ClearStar's write-up says the methodology for classifying ghost jobs is "not provided" — [ClearStar](https://www.clearstar.net/?p=6218). A secondary German blog says Greenhouse platform data treats a ghost job as a posting with no hiring activity: no interviews, scorecards or hires. I could not confirm this in any Greenhouse document. — [morethancareer.de](https://morethancareer.de/blog/pharma-bloodbath-part-xvii-ghost-jobs-ghost-candidates-german-data.html)
- Companion figures: "almost 70% of companies using the platform posted at least one ghost job in Q2 2024". Jon Stross, Greenhouse president, told the WSJ it was "kind of a horror show". — [Fortune, 16 Jan 2025](https://fortune.com/2025/01/16/job-market-rife-fake-listing-ghosting-hiring-managers/)
- Industry figures attributed to Greenhouse: construction 38%, art 34%, legal 29%, corporate services nearly 31% (Q2 2024). The Fox article gives no method and links only to the 2024 report, which does not contain these figures. — [Fox (14 Jan 2025)](https://www.fox5ny.com/news/ghost-jobs-greenhouse-analysis). The same industry figures are repeated in [Fisher Phillips (1 Apr 2025)](https://www.fisherphillips.com/en/news-insights/california-lawmakers-want-to-ban-ghost-job-postings.html)
- Later and unverified: a Sept 2025 trade article reportedly says Greenhouse's internal Q2 2025 data put ghost jobs at 30% of postings, with four in five companies posting at least one. The page returned 403, so this was seen only in a search excerpt. — [Recruiter.co.uk (unverified)](https://www.recruiter.co.uk/news/2025/09/disturbing-number-ghost-jobs-rise-uk)
- WSJ-linked context: LinkedIn worked with Greenhouse on "verified" labels, and the WSJ was cited as saying ghost jobs were "one in five LinkedIn job postings". Note that Greenhouse's figure covers Greenhouse's platform, not LinkedIn. — [The Peak (14 Jan 2025), citing WSJ](https://www.readthepeak.com/p/01-25-ghost-listings-flood-linkedin)
- Credibility: medium. It is measured outcome data from real ATS activity, which makes it the closest thing to ground truth available. But the definition and denominator are unpublished, the industry figures cannot be traced to a primary document, and Greenhouse sells products positioned as fixes (Dream Job, Greenhouse Verified, Real Talent).

**Revelio Labs: hires-per-posting ratio (Oct 2023; page updated 18 Jun 2026)**
- Who: Stephanie Hao and Lisa K. Simon of Revelio Labs, a workforce-data vendor, working with Bloomberg. Method: a posting counts as matched to a hire if a position started within 6 months of the posting date and shares the posting's company, role, seniority and state. — [Revelio Labs](https://www.reveliolabs.com/news/macro/ghost-job-postings)
- Headline: US hires per open posting fell from 0.75 (2018) to below 0.5 (2023). The decline began in 2020 and accelerated through 2022. — [Revelio Labs](https://www.reveliolabs.com/news/macro/ghost-job-postings); [Revelio chart](https://www.reveliolabs.com/charts/ghost-job-postings/fig-1)
- Sectors with the biggest falls in the ratio, 2018–2022: Administration & Support −55.2%, Construction −54.9%. Education, Healthcare, Management and Finance also fell sharply. — [Revelio Labs](https://www.reveliolabs.com/news/macro/ghost-job-postings)
- Ghosting proxy: the share of interview reviews mentioning recruiter ghosting rose 120% over about five years, relative to Jan 2018. The authors argue this means the ratio decline is not only due to labour shortages. — [Revelio Labs](https://www.reveliolabs.com/news/macro/ghost-job-postings)
- The study gives no formal definition of a ghost job and hedges its conclusions: a falling ratio "can have many reasons". — [Revelio Labs](https://www.reveliolabs.com/news/macro/ghost-job-postings)
- Credibility: medium to high for the trend. It is measured and the method is described, but it depends on online-profile coverage and the 6-month matching window. The ratio cannot separate ghost postings from duplication, reposting or slower hiring.

#### B. Listing-scrape heuristics (posting age, missing fields, duplicates)

**StandOut CV (UK): "34.4% of listings are ghost jobs". This is the main source of the UK "~34%" claim.**
- Who and when: Andrew Fennell of StandOut CV, a CV-writing site. The page was updated 6 Mar 2025, but the data are from Indeed UK scrapes on 19 May 2023 and 27 Jun 2023. — [StandOut CV](https://standout-cv.com/stats/ghost-job-listings-statistics-uk)
- Method: the proxy for a ghost job is Indeed's "30+ days ago" tag. There are two datasets: 91,318 listings across the 30 largest UK cities and boroughs, and 60,983 listings for 20 popular roles. The 34.4% (May 34.8%, June 33.4%) comes from the 20-role set. The study multiplies 34.4% by the ONS average of 344,666 vacancies (Apr–Jun 2023) to estimate about 118,565 ghost jobs a month. — [StandOut CV](https://standout-cv.com/stats/ghost-job-listings-statistics-uk)
- Breakdowns: veterinary nurse 59.1%, software engineer 46.5%, cybersecurity analyst 45.7%, insurance broker 43.5%, graphic designer 42.4%, web developer 42.3%, data analyst 38.6%, pilot 34.8%, accountant 34.0%, project manager 31.6%. By place: Islington 26.1%, Southend-on-Sea 23.7%, Birkenhead 22.7%; lowest were London 10.0%, Edinburgh 10.9% and Bristol 11.1%. — [StandOut CV](https://standout-cv.com/stats/ghost-job-listings-statistics-uk)
- Misdating: a Feb 2026 Robert Walters release cites "34.4% of postings across 20 common UK roles in 2025", but the underlying data are from 2023. — [Workplace Journal (26 Feb 2026)](https://workplacejournal.co.uk/2026/02/ghost-job-listings-stalling-uk-job-searches-survey-finds/)
- Credibility: low. It is a single-board, two-snapshot age proxy with no validation and comes from a vendor with a commercial interest. Long-open roles in shortage occupations look identical to ghosts under this rule.

**A second UK "34%": a Greenhouse employer survey reported by HRreview (23 Dec 2025)**
- HRreview reports that a Greenhouse survey of "over 1,200 employers" in the UK, US and Germany found that "as many as 34 percent of UK roles posted online were never actively being recruited for", and 22% across the three countries. It gives no country breakdown for Germany or the US and no method. — [HRreview](https://hrreview.co.uk/?p=385524)
- I could not find this release in Greenhouse's newsroom, whose visible listings run only from May 2026 to Oct 2026. — [Greenhouse UK newsroom](https://www.greenhouse.com/uk/newsroom). A German blog repeats it (UK 34%, three-country 22%, no German figure). — [morethancareer.de](https://morethancareer.de/blog/pharma-bloodbath-part-xvii-ghost-jobs-ghost-candidates-german-data.html)
- Credibility: low until the primary is found. The 22% matches Greenhouse's platform figure, so platform data and an employer survey may have been conflated.

**ResumeUp.AI: "27.4% of US LinkedIn listings are likely ghost jobs"**
- Who and when: ResumeUp.AI, a career website, reported by Entrepreneur on 3 Sep 2025. Some later sources date it to January 2026, a conflict I could not resolve. — [Entrepreneur](https://www.entrepreneur.com/business-news/one-quarter-of-jobs-posted-online-are-fake-ghost-jobs-study/496683)
- Method: jobs posted more than 30 days earlier, divided by all jobs posted in 2025, using windows of 30, 60, 90, 120 and 233 days. No sample size is given, and the article links only to the ResumeUp.AI homepage. — [Entrepreneur](https://www.entrepreneur.com/business-news/one-quarter-of-jobs-posted-online-are-fake-ghost-jobs-study/496683)
- Breakdowns by city: Los Angeles 30.5%, Philadelphia 30.1%, Indianapolis 27.8%, New York 26.7% (highest volume, about 23,000 listings), San Francisco 26.0%; lowest were Seattle 16.6%, Boston 18.7%, Dallas 20.1%. By country: US 27.4%, Canada 24.9%, UK 14.2%, Australia 10.9%. — [Entrepreneur](https://www.entrepreneur.com/business-news/one-quarter-of-jobs-posted-online-are-fake-ghost-jobs-study/496683)
- A 2026 review says the 27.4% figure "could not be traced to a solid report with a stated methodology" (search excerpt). — [Enterprise (28 Jul 2026)](https://enterpriseam.com/egypt/2026/07/28/ghost-jobs-scam-listings-pipeline-plays-why-is-linkedin-full-of-postings-that-go-nowhere/)
- Credibility: low. It is a posting-age share with no ground truth, it is sensitive to the time window and to LinkedIn's free/paid expiry rules (see Q5), and the source is a vendor.

**"Outten & Golden" 26.4%: it exists, but it is a slide deck by two of the firm's data analysts, not a firm publication**
- Title: *Ghost Jobs, Real Costs: Labor Market Distortions from Ghost Jobs Postings*, by Steven Singer and Derya Oktay, both listed as "Data Analyst, Outten & Golden, LLP" (affiliated with Northwestern and Duke). It carries the disclaimer: "This is independent research not necessarily reflective of the viewpoint of Outten & Golden LLP." The 17-slide deck is hosted on a Constant Contact file server. — [O&G analysts' deck (PDF)](https://files.constantcontact.com/668faa28001/2cbc2d97-db5a-4af4-91c8-85fa1e34df19.pdf)
- Data: LinkedIn postings via CoreSignal for a single week, 3–7 Mar 2025. About 20,000 postings (regression N = 20,084) in arts, food service, construction, legal, finance and engineering. Geography: pay-transparency jurisdictions (CO, DC, HI, IL, MD, MA, MN, NJ, NY, VT, WA, CA). — [O&G deck](https://files.constantcontact.com/668faa28001/2cbc2d97-db5a-4af4-91c8-85fa1e34df19.pdf)
- Flags: (1) no pay transparency, 30.1%; (2) no valid external URL, 71.4%; (3) duplicate posting, 3.1%. The total of 5,294 "ghost posts" (26.4%) equals the sum of the pairwise and all-three overlaps (4,752 + 19 + 239 + 284). In effect, a ghost post is one meeting at least two of the three criteria. Their example ghost post was "posted 25 times on 3/7/2025". — [O&G deck](https://files.constantcontact.com/668faa28001/2cbc2d97-db5a-4af4-91c8-85fa1e34df19.pdf)
- Equity analysis: logistic regressions on ACS occupation demographics. A 10% rise in Black workers in an occupation means 10–14% higher odds of a ghost posting; Hispanic workers, 5–7% higher; White workers, 6–7% lower. Low-education fields are "most at risk". The deck calls flagged posts "fraudulent", which mixes the ghost and fraud labels, and it calls for "stronger legal or regulatory frameworks". — [O&G deck](https://files.constantcontact.com/668faa28001/2cbc2d97-db5a-4af4-91c8-85fa1e34df19.pdf)
- Credibility: low to medium. The method is transparent and reproducible, but the heuristic is weak and dominated by "no salary + no external URL". It covers one week and is not peer-reviewed. Outten & Golden is a plaintiff-side employment law firm, a potential interest even with the disclaimer.

**JobsPipe (job-data vendor, data generated 9 Sep 2026)**
- Method: an index of 10 boards (LinkedIn, Indeed, Greenhouse, Lever, Ashby, Workable, SmartRecruiters, Workday, Paylocity, YC). A posting is scored if it was seen at least twice or is older than 14 days. Sightings begin June–July 2026. — [JobsPipe](https://jobspipe.dev/ghost-jobs/linkedin)
- On LinkedIn, 21.2% of scored active postings carry at least one warning sign, against 17.8% across all boards. Signal prevalence on LinkedIn: no salary 76.9%; mass poster (500+ open roles) 20.2%; reposted after a gap of 10+ days 8.4% (9.9% in the headline base); open 45+ days 3.0%; description under 400 characters 1.7%; posted date far behind first sighting 0.9%. First sighted more than 30 days ago: 31.1% on LinkedIn, 28.6% across boards. The median LinkedIn posting is live 30 days when closed, with closures clustering at the 30-day expiry. — [JobsPipe](https://jobspipe.dev/ghost-jobs/linkedin)
- JobsPipe itself says the score is a warning-sign score, "not proof that a posting is fake". — [JobsPipe](https://jobspipe.dev/ghost-jobs/linkedin)
- Credibility: low to medium as prevalence data; the signal definitions are useful.

**Clarify Capital listing analysis: "one in seven of 175,000 live Indeed listings"**
- Cited by Spectrum News (30 Apr 2026). I did not locate the primary, its date or its method. — [Spectrum News](https://spectrumlocalnews.com/nys/capital-region/politics/2026/04/30/n-y--state-senate-passes-bill-to-crack-down-on--ghost-job--postings)

#### C. Macro openings-to-hires gap (not a ghost-job measure)

**MyPerfectResume, "Ghost Job Economy" (Nov 2025): "30% of openings never resulted in a hire" (June 2025)**
- Who: MyPerfectResume, a resume-building service, which commissioned the report; career expert Jasmine Escalera is quoted. Data: BLS JOLTS openings compared with hires. — [CPA Practice Advisor (12 Nov 2025)](https://www.cpapracticeadvisor.com/2025/11/12/ghost-jobs-up-to-1-in-3-job-listings-dont-result-in-hires/173044/)
- Numbers: June 2025, 30% (over 2.2 million) openings with no hire. The gap was 28–38% each month since 2021 and 28–32% in 2023–25. The report says gaps in 2010–2019 "rarely exceeded 10%". — [CPA Practice Advisor](https://www.cpapracticeadvisor.com/2025/11/12/ghost-jobs-up-to-1-in-3-job-listings-dont-result-in-hires/173044/). The underlying 7.4M openings against 5.2M hires came from a search excerpt. — [HR Dive](https://www.hrdive.com/news/us-job-listings-go-nowhere-creating-a-ghost-job-economy/805448/)
- Sectors (June 2025): government nearly 60%, education & health 50%, information 48%, financial activities 44%. In construction and hospitality, hires match or exceed openings. — [CPA Practice Advisor](https://www.cpapracticeadvisor.com/2025/11/12/ghost-jobs-up-to-1-in-3-job-listings-dont-result-in-hires/173044/). The BambooHR newsroom's write-up says the reasons "aren't always malicious" and include budget freezes and filled roles not being removed. — [BambooHR News (19 Nov 2025)](https://newsroom.bamboohr.com/?p=1887)
- Why it is not a ghost measure: JOLTS defines openings as positions open on the last business day of the month where "a specific position exists", the job "could start within 30 days", and "there is active recruiting". Hires are "all additions to the payroll during the month". — [BLS JOLTS definitions](https://www.bls.gov/jlt/jltdef.htm). CRS notes that if employers answer honestly, JOLTS openings "are unlikely to be ghost jobs". — [CRS IF12977 (25 Apr 2025)](https://www.everycrsreport.com/reports/IF12977.html)
- Credibility: low as a ghost-job estimate. It compares a stock with a flow, conflates long time-to-fill and turnover with ghosting, and comes from a commercial source. It is valid only as a crude aggregate.

**Enhancv's JOLTS comparison (Jan 2026)**: vacancy gaps of Information 46.8%, Finance 42.8%, Professional & business services 25.9%, Manufacturing 25.8%, Education & health 49.7%. Enhancv itself notes that its survey "ghost rate" measures perceived deception and is not comparable with the BLS gap. — [Enhancv](https://enhancv.com/blog/ghost-jobs-survey-2026-bls-data-comparison/)

#### D. Employer / recruiter self-report surveys

**ResumeBuilder 2024 hiring-manager survey: "40% posted a fake job; 3 in 10 have one live"**
- Commissioned by ResumeBuilder.com and run on Pollfish, launched 22 May 2024. 1,641 hiring managers were screened and 649 completed the full survey. Screening criteria: over 25, household income of at least $75k, more than high-school education, manager level or above, company with more than 10 employees, involved in hiring. To take the full survey, a respondent had to say their company had posted "a fake job listing for a position that it didn't intend to fill" in the past year. The page does not say the sample is US-only. — [ResumeBuilder](https://www.resumebuilder.com/3-in-10-companies-currently-have-fake-job-posting-listed/)
- Headline: 40% posted a fake listing in the past year. Of those, 79% still have active fake listings, which gives "about 3 in 10" overall. Number posted: 26% posted 1–3, 19% posted 5, 19% posted 10, 10% posted 25, 11% posted 50, and 13% posted 75 or more. — [ResumeBuilder](https://www.resumebuilder.com/3-in-10-companies-currently-have-fake-job-posting-listed/)
- Levels advertised: entry 63%, mid 68%, senior 53%, executive 45%. Duration: under 1 week 6%, a few weeks 28%, about a month 31%, about 3 months 19%, about 6 months 7%, 1 year or more 9%. Platforms: company website 72%, LinkedIn 70%, ZipRecruiter 58%, Indeed 49%, Glassdoor 48%. — [ResumeBuilder](https://www.resumebuilder.com/3-in-10-companies-currently-have-fake-job-posting-listed/)
- Candidate contact: always 39%, sometimes 45%, rarely 12%, never 5%. Of firms that contacted applicants, 85% say candidates were interviewed. Acceptability: definitely 43%, probably 27% ("7 in 10"). Reported impact: 68% say revenue was positive, 77% productivity, 65% morale. — [ResumeBuilder](https://www.resumebuilder.com/3-in-10-companies-currently-have-fake-job-posting-listed/)
- Who proposed the practice: HR 37%, senior management 29%, executives 25%, investors 5%, consultants 4%. — [ResumeBuilder](https://www.resumebuilder.com/3-in-10-companies-currently-have-fake-job-posting-listed/)
- Secondary coverage misquotes it. Fortune gives "make workers feel replaceable" as 66%, but the primary says 62%. — [Fortune](https://fortune.com/2025/01/16/job-market-rife-fake-listing-ghosting-hiring-managers/) against [ResumeBuilder](https://www.resumebuilder.com/3-in-10-companies-currently-have-fake-job-posting-listed/). Newsweek turns it into "3 in 10 online job listings", a share of postings that the survey never measured. — [Newsweek](https://www.newsweek.com/ghost-jobs-rise-1924351)
- Credibility: low. It uses an opt-in mobile panel with self-identified hiring managers, and the unit is the respondent, not the firm or posting. Implausible answers (13% posting 75 or more fakes; 77% reporting a productivity gain) suggest low-quality responses. The sponsor is a resume vendor.

**ResumeBuilder 2026 job-seeker survey (fielded 27 Aug 2026; page updated 13 Oct 2026)**
- 1,011 US adults who had searched for a job in the past 24 months: 33% millennials, 29% Gen X, 20% Gen Z, 18% boomers. 86% have encountered a suspected ghost job. 58% have interviewed for a role they later suspected was a ghost (31% multiple times). Warning signs cited: listing active too long or outdated 38%; repeated removal or reposting 34%. Behaviour: 34% check original posting dates and 32% verify on employer career sites. Respondents were asked about postings they "suspected wasn't tied to an active hiring need". — [ResumeBuilder](https://www.resumebuilder.com/ghost-jobs/)
- Credibility: low as prevalence; it is useful for knowing which cues job seekers use.

**Clarify Capital (small-business lender): a 2022 survey, often misdated to 2023, and a 2025 follow-up**
- The 2022 wave was about 1,000 hiring managers in summer 2022 (via WSJ reporting). 27% leave postings up more than four months. — [Fortune (22 Mar 2023)](https://fortune.com/2023/03/22/ghost-jobs-companies-posting-fake-listings). CRS dates the "survey of managers by a business lending firm" to September 2022. — [CRS IF12977](https://www.everycrsreport.com/reports/IF12977.html)
- Other 2022 figures from search excerpts of Scripps "Don't Waste Your Money" coverage: about half list jobs they don't necessarily intend to fill because they are "always open to new people"; 43% want to keep employees motivated or appear to be growing; 96% say they try to fill roles quickly, yet 40% don't expect to fill them for 2–3 months; 68% had postings active more than 30 days. — [WMAR2 (search excerpt)](https://www.wmar2news.com/what-are-ghost-jobs-and-why-are-there-so-many-of-them)
- Newsweek instead dates a Clarify survey of 1,000 hiring managers to October 2023, reporting that 50% posted roles to keep a warm talent pool "at the ready". — [Newsweek](https://www.newsweek.com/ghost-jobs-rise-1924351). This conflicts with the 2022 date, and the two may be the same survey.
- The 2025 wave covered 1,000 American employers. It found about a third of listings are from companies not actively hiring, "roughly halved" compared with 2022. 57% keep positions online to build a candidate pool; 6% to look like they are growing. — [TheJournal.ie (28 Jul 2025)](https://www.thejournal.ie/article.php?id=6772517)
- Credibility: low to medium. The method was not disclosed (the primary page returned 403), and the definitions changed between waves.

**MyPerfectResume 2024 recruiter survey: "81% of recruiters say their employer posts ghost jobs"**
- Reported 19 Aug 2024; the sample size and dates are not given in coverage. The definition is "positions that either don't exist or are already filled", which counts stale ads. About 17% say up to three-quarters of their ads are not genuine; 21.5% say half; 36% say a quarter; 18% say less than a tenth. — [Fortune](https://www.fortune.com/2024/08/19/recruiters-posting-ghost-jobs-problem-job-seekers)
- The 81% figure "could not be traced to a solid report with a stated methodology" (search excerpt). — [Enterprise](https://enterpriseam.com/egypt/2026/07/28/ghost-jobs-scam-listings-pipeline-plays-why-is-linkedin-full-of-postings-that-go-nowhere/)
- Credibility: low.

**LiveCareer HR survey (2025): "45% regularly post ghost jobs"**
- 918 HR professionals, fieldwork March 2025 (search excerpt of the LiveCareer page; the page itself timed out twice). — [LiveCareer](https://livecareer.com/resources/careers/ghost-jobs). HRD reported "more than 900" respondents on 29 May 2025: 45% post ghost jobs regularly; 48% use them for "special needs such as seasonal hiring or building a talent pipeline"; 5% only in "special circumstances". Listings stay up 1–4 weeks (43%), 1–3 months (37%) or under a week (15%). 47% have received multiple complaints about ghost jobs. — [HRD Canada](https://www.hcamag.com/ca/specialization/recruitment/nearly-half-of-hr-professionals-admit-they-regularly-post-ghost-job-ads-survey/537439)
- LiveCareer's own page reportedly adds that 69% often close searches and stop responding to candidates without notice (search excerpt). — [LiveCareer](https://livecareer.com/resources/careers/ghost-jobs)
- A German trade outlet criticised it for not disclosing respondents' countries or how representative the sample is (search excerpt). — [ingenieur.de (8 Jul 2026)](https://www.ingenieur.de/karriere/arbeitsleben/ghost-jobs-wenn-die-traumstelle-nur-ein-koder-ist/)
- Credibility: low. Taken together, 45% + 48% + 5% means about 98% admit to posting ghost jobs at least sometimes, which points to a leading question design.

#### E. Job-seeker perception surveys (measure suspicion or encounters, not prevalence)
- **Greenhouse *2024 State of Job Hunting*** (2,500 workers in the US, UK and Germany; pollster not named): three in five suspect they have encountered a ghost job; 61% were ghosted after an interview, up 9 points since April 2024. — [Greenhouse UK blog](https://www.greenhouse.com/uk/blog/greenhouse-2024-state-of-job-hunting-report). In the US, 71% of Gen Z suspect they have encountered one. ClearStar writes that "60% have applied to suspected ghost jobs", but its own split (29% applied anyway, 31% chose not to) shows the 60% is suspected encounters. — [ClearStar](https://www.clearstar.net/?p=6218). Germany: 21% applied anyway and 38% did not; UK: 27% and 33% (secondary). — [morethancareer.de](https://morethancareer.de/blog/pharma-bloodbath-part-xvii-ghost-jobs-ghost-candidates-german-data.html)
- **Greenhouse *2026 Future of Hiring Candidate Report*** (20 Oct 2026; 2,800+ job seekers in the US, UK, Ireland, Germany and Australia; figures are US, n=1,200): it does not use the term "ghost job". 81% of US candidates were rejected in the past year without speaking to anyone; among interviewees, the top complaint was being ghosted (45%). — [Greenhouse newsroom](https://www.greenhouse.com/newsroom/6-in-10-job-seekers-are-rethinking-how-they-write-to-avoid-sounding-like-ai-even-as-most-use-it-in-their-search)
- **Resume Genius 2026** (1,000 active US job seekers, Pollfish, launched 16 Mar 2026): 67% suspected a ghost job a few or many times. The "red flags" they cite are mostly scam cues: typos 52%, vague company 52%, requests for personal or financial details 39%, requests to move off-platform 21%. This shows the ghost/scam conflation in seeker data. — [CPA Practice Advisor (30 Apr 2026)](https://www.cpapracticeadvisor.com/2026/04/30/ghost-jobs-still-haunting-67-of-job-seekers-report-finds/182536/)
- **Enhancv 2026** (1,000 US professionals, March 2026, including 411 senior): 47% applied to a role they later found never existed; 25% reached interviews; 37% incurred costs. Red flags: job age of 3+ months 27.2%; rejection-then-repost loop 16.1%; recruiter admitted not hiring 15.5%. — [Enhancv](https://enhancv.com/blog/ghost-jobs-survey-2026-bls-data-comparison/)
- **Software Finder** (1,020 Americans who job-hunted in the past 18 months): 75% have been ghosted by an employer; 47% had to do unpaid work during the interview process. I found no ghost-job prevalence figure and no Harris Poll involvement (search excerpt). — [Software Finder](https://softwarefinder.com/resources/interview-process-from-hell)
- **Employment Hero UK** (OnePoll, 1,000 UK workers, Nov 2025; published 22 Jan 2026): 24% believe they applied for a ghost job in the past year (37% of 18–34s); 42% were ghosted after interview; 80% had applied and got no response. Its ghost definition is roles "advertised despite the employer not genuinely recruiting". — [HRreview](https://hrreview.co.uk/?p=385860)
- **Robert Walters UK** (26 Feb 2026; sample not stated): 44% say ghost listings stalled their search; 35% say they lowered trust; only 9% feel confident identifying ghost jobs. Among hiring managers, 40% call application volumes a major challenge. — [Workplace Journal](https://workplacejournal.co.uk/2026/02/ghost-job-listings-stalling-uk-job-searches-survey-finds/)

#### F. Official sources
- CRS In Focus IF12977 (25 Apr 2025): "No official statistics measure the number of ghost jobs." It notes that industry survey firms sell hiring services and disclose varying levels of method, and that some ghost postings are unintentional (job boards auto-copying filled listings). FTC reports of job scams nearly tripled 2020–2024; that is fraud, a separate category. — [CRS IF12977](https://www.everycrsreport.com/reports/IF12977.html)

#### Comparability matrix (unit and definition)

| Study | Unit of the % | Definition / proxy | Ground truth? |
|---|---|---|---|
| Greenhouse 18–22% | postings per quarter (Greenhouse ATS) | "no intent to hire"; reportedly no hiring activity (unconfirmed) | ATS activity |
| Greenhouse "~70% of companies" | companies with ≥1 ghost posting | same | ATS activity |
| Revelio 0.75 → <0.5 | hires per posting | no matched hire within 6 months | profile data |
| StandOut CV 34.4% | Indeed UK listings (20 roles) | "30+ days ago" tag | none |
| ResumeUp.AI 27.4% | LinkedIn listings | older than 30 days | none |
| O&G analysts 26.4% | LinkedIn postings, 1 week | ≥2 of: no pay, no external URL, duplicate | none |
| MyPerfectResume 30% | JOLTS openings vs hires | 1 − hires/openings | aggregate stock vs flow |
| ResumeBuilder 40% / 3 in 10 | screened hiring managers | company posted a role it "didn't intend to fill" | self-report |
| LiveCareer 45% | HR professionals | "regularly post" | self-report |
| MyPerfectResume 81% | recruiters | ads that "don't exist or are already filled" | self-report |
| Clarify 2025 "~1/3" | employers' listings | not actively hiring | self-report |
| Seeker surveys 24–86% | job seekers | suspected encounter | perception |

### Inferences
- The ResumeBuilder "40%" is a screener pass rate: 649 of 1,641 is 39.5%. The "3 in 10" is 39.5% × 79% ≈ 31% of respondents, not of companies or postings. Every later percentage is conditional on having posted a fake job.
- Company-level "at least one ghost job" figures are inflated by posting volume. At a 20% per-posting rate, a firm posting 5–6 jobs a quarter has a 67–74% chance of at least one (1 − 0.8^n). So Greenhouse's "almost 70% of companies" adds little beyond the 18–22% posting rate.
- Self-reported durations argue against a simple age cutoff. 34% of ResumeBuilder fake listings came down within a few weeks, and 58% of LiveCareer respondents' ghost listings stay up a month or less. A 30-day threshold, as used by StandOut CV and ResumeUp.AI, therefore misses many ghosts and catches genuine hard-to-fill roles; the 59.1% "ghost" rate for UK veterinary nurses more plausibly reflects shortage than fake ads.
- The O&G analysts' 26.4% is dominated by one pair of criteria. 4,752 of 5,294 flagged posts (89.8%) are "no salary + no external URL", and the 71.4% "no external URL" rate probably reflects LinkedIn on-platform apply flows rather than intent. This is unverified.
- The MyPerfectResume pre-2020 baseline ("gap rarely exceeded 10%") should be checked against the BLS series. From memory, and unverified here, openings exceeded hires by roughly 15–20% in 2018–2019, which would undercut the claimed structural break.
- Figures are not comparable across families. Construction is the *worst* industry in Greenhouse's data and among the steepest decliners in Revelio's, yet the *best* in the JOLTS gap. The JOLTS gap rewards high-churn sectors, where hires exceed openings.

### Gaps
- Primary methods for Greenhouse's 18–22%, its industry split and the Q2 2025 30% claim were not found. WSJ coverage (Jan 2025) was not accessible.
- The Greenhouse "1,200 employers / UK 34% / three-country 22%" survey (HRreview, Dec 2025) could not be traced to a Greenhouse release, so no German figure is known.
- Clarify Capital primary pages (2022 and 2025 waves, and the 175,000-Indeed-listings analysis) returned 403 or were not found. The October 2023 dating could not be resolved.
- The MyPerfectResume 2024 recruiter survey's sample size and dates were not found. The LiveCareer page timed out, so 918 and March 2025 rest on a search excerpt.
- **Harris Poll:** I found no Harris Poll survey on ghost jobs. **Software Finder:** found only a ghosting and unpaid-work survey with no ghost-job prevalence figure. The pairing in the brief may be mistaken.
- ResumeUp.AI's primary report, sample size and exact date were not found.

---

## Q2. What motives do employers report, with percentages per survey?

### Takeaway
Self-reported motives cluster into four groups: (a) **pipeline or always-open**, the most common in neutral wording; (b) **signalling**, meaning appearing to grow or being open to talent, aimed at investors, clients and competitors; (c) **internal workforce management**, meaning making staff feel replaceable or placating overworked staff; (d) **information-gathering**, meaning testing job descriptions, salaries and the market. **Administrative neglect** (forgetting to remove filled ads) and **compliance formality** (posting when an internal candidate is already chosen) are cited mainly by journalists and CRS, not measured in surveys. Percentages depend heavily on question wording and on which respondents are filtered in.

### Cited Findings
- **ResumeBuilder 2024** (n=649 hiring managers whose company posted a fake job; multi-select): appear open to external talent 67%; appear to be growing 66%; make employees believe workload relief is coming 63%; make employees feel replaceable 62%; collect resumes for later 59%. — [ResumeBuilder](https://www.resumebuilder.com/3-in-10-companies-currently-have-fake-job-posting-listed/)
- **Clarify Capital 2022** (about 1,000 hiring managers): about 50% are "always open to new people"; 43% want to keep employees motivated or give an impression of growth (search excerpt). — [WMAR2](https://www.wmar2news.com/what-are-ghost-jobs-and-why-are-there-so-many-of-them). Listed reasons without percentages: false impression of growth, candidate pool, reassuring overworked staff. — [Fortune 2023](https://fortune.com/2023/03/22/ghost-jobs-companies-posting-fake-listings)
- **Clarify Capital 2025** (1,000 employers): building a candidate pool 57%; appearing to grow 6%. — [TheJournal.ie](https://www.thejournal.ie/article.php?id=6772517)
- **MyPerfectResume 2024** (recruiters): keep a presence on job boards when not hiring 38%; test how effective job descriptions are 36%; build a talent pool 26%; market or competitor insight 26%; gauge how hard it would be to replace certain employees 25%; look as if there is no hiring freeze ~25%; improve reputation ~20%. — [Fortune](https://www.fortune.com/2024/08/19/recruiters-posting-ghost-jobs-problem-job-seekers)
- **LiveCareer 2025** (HR): 48% use them for "special needs such as seasonal hiring or building a talent pipeline"; 5% only in "special circumstances". — [HRD Canada](https://www.hcamag.com/ca/specialization/recruitment/nearly-half-of-hr-professionals-admit-they-regularly-post-ghost-job-ads-survey/537439)
- **Greenhouse 2025 employer survey (as reported by HRreview)**: motives listed without percentages: collecting CVs and building talent pools, giving an impression of growth, gathering candidate data. — [HRreview](https://hrreview.co.uk/?p=385524)
- **Employment Hero UK**: candidate pipeline, testing salary expectations, benchmarking the market (no percentages). — [HRreview](https://hrreview.co.uk/?p=385860)
- **CRS**: to evaluate candidate pools, to signal that employees are replaceable, to suggest growth to investors; also unintentional posts from job boards auto-copying filled ads. — [CRS IF12977](https://www.everycrsreport.com/reports/IF12977.html); the same summary appears in [HR Dive](https://www.hrdive.com/news/new-york-passed-bill-imted-at-halting-ghost-jobs/822620/)
- **Revelio**: labour shortages (roles reposted unfilled), economic uncertainty (hiring slowed while ads stay up), and low cost of keeping postings open. — [Revelio Labs](https://www.reveliolabs.com/news/macro/ghost-job-postings)
- **Forgetting to remove ads; internal-candidate formality**: listings are sometimes "an accident" (the company forgets to remove a filled role), and firms that have chosen an internal candidate may be "legally bound to post the role" (search excerpt of Fortune). — [Fortune (28 Jan 2025)](https://fortune.com/2025/01/28/how-to-spot-ghost-job-listings). Administrative failures and budget freezes are also cited by the BambooHR write-up of MyPerfectResume. — [BambooHR News](https://newsroom.bamboohr.com/?p=1887)
- **Overload rather than intent (UK)**: Robert Walters suggests some apparent ghost listings come from hiring processes overwhelmed by AI-driven application volumes. — [Workplace Journal](https://workplacejournal.co.uk/2026/02/ghost-job-listings-stalling-uk-job-searches-survey-finds/)
- **German compliance analogues (brief; covered by another researcher)**: §93 BetrVG (works council can require internal advertising) and §164(1) SGB IX duties can produce formality postings. — [morethancareer.de](https://morethancareer.de/blog/pharma-bloodbath-part-xvii-ghost-jobs-ghost-candidates-german-data.html)

### Inferences
- Signalling motives (growth or open to talent at about 66%) top only ResumeBuilder's list, which filters in admitted fake-posters and offers leading options. In Clarify's 2025 neutral framing, growth signalling falls to 6% and pipeline building leads at 57%. Wording, not the market, drives the ranking.
- For signal design, the motives map onto different observable traces. Pipeline and evergreen postings are long-lived or recurring with generic text. Signalling postings are volume spikes without matching hiring. Stale or forgotten postings are age with no repost. Compliance postings are short-lived and have an internal hire.

### Gaps
- No survey quantifies "forgot to remove the ad" or "compliance or internal-candidate formality" with a percentage.
- No motive data broken down by company size or industry was found.

---

## Q3. Which industries, seniority levels, company sizes and role types are flagged as most affected?

### Takeaway
The evidence conflicts by method. ATS and profile-matching data flag **construction, admin and support, legal, arts and corporate services**. The macro JOLTS gap flags **government, education and health, information and finance** and clears construction and hospitality. UK listing-age data flags **tech roles (software, cyber, data, web) and veterinary nursing**. On seniority, admitted fake postings span all levels, with mid and entry level most common. Company size is almost never broken down, so it is a genuine evidence gap.

### Cited Findings
- **Industries (Greenhouse platform, via secondary coverage)**: construction 38%, art 34%, legal 29%, corporate services about 31% (Q2 2024). — [Fox](https://www.fox5ny.com/news/ghost-jobs-greenhouse-analysis); [Fisher Phillips](https://www.fisherphillips.com/en/news-insights/california-lawmakers-want-to-ban-ghost-job-postings.html)
- **Industries (Revelio, decline in hires per posting 2018–22)**: Administration & Support −55.2%, Construction −54.9%; large drops also in Education, Healthcare, Management and Finance. — [Revelio Labs](https://www.reveliolabs.com/news/macro/ghost-job-postings)
- **Industries (JOLTS gap, MyPerfectResume, June 2025)**: government about 60%, education & health 50%, information 48%, financial activities 44%; construction and hospitality have hires of at least openings. — [CPA Practice Advisor](https://www.cpapracticeadvisor.com/2025/11/12/ghost-jobs-up-to-1-in-3-job-listings-dont-result-in-hires/173044/)
- **Industries (seeker encounter rates, Enhancv)**: marketing & advertising 87.5%, telecom & tech 85.7%, manufacturing 82.6%, business support & logistics 71.4%, retail 68.9%, finance 66.7%, healthcare & pharma 63.7%. — [Enhancv](https://enhancv.com/blog/ghost-jobs-survey-2026-bls-data-comparison/)
- **Occupations or roles (UK, StandOut CV, 2023 data)**: veterinary nurse 59.1%, software engineer 46.5%, cybersecurity analyst 45.7%, insurance broker 43.5%, graphic designer 42.4%, web developer 42.3%, data analyst 38.6%. — [StandOut CV](https://standout-cv.com/stats/ghost-job-listings-statistics-uk)
- **Occupations by demographics (O&G analysts)**: occupations with higher shares of Black and Hispanic workers and lower education have higher odds of flagged postings. — [O&G deck](https://files.constantcontact.com/668faa28001/2cbc2d97-db5a-4af4-91c8-85fa1e34df19.pdf)
- **Seniority (ResumeBuilder 2024)**: of firms posting fakes, mid-level 68%, entry 63%, senior 53%, executive 45%. — [ResumeBuilder](https://www.resumebuilder.com/3-in-10-companies-currently-have-fake-job-posting-listed/)
- **Seniority or experience (Enhancv)**: respondents with 8+ years' experience had the highest encounter rate (51%). 31% of seniors were asked for consultative work ("strategy decks", "market intelligence") in interviews, against 22% of juniors, which points to information-harvesting interviews. — [Enhancv](https://enhancv.com/blog/ghost-jobs-survey-2026-bls-data-comparison/)
- **Age**: 71% of US Gen Z suspect they have encountered a ghost job (Greenhouse). — [ClearStar](https://www.clearstar.net/?p=6218). In the UK, 37% of 18–34s believe they applied to one, against 24% of all workers (Employment Hero). — [HRreview](https://hrreview.co.uk/?p=385860)
- **Geography**: LinkedIn ghost-proxy share by city is highest in Los Angeles (30.5%) and lowest in Seattle (16.6%); by country, US 27.4%, Canada 24.9%, UK 14.2%, Australia 10.9% (ResumeUp.AI). — [Entrepreneur](https://www.entrepreneur.com/business-news/one-quarter-of-jobs-posted-online-are-fake-ghost-jobs-study/496683). UK towns: Islington 26.1% highest, London 10.0% lowest (StandOut CV). — [StandOut CV](https://standout-cv.com/stats/ghost-job-listings-statistics-uk)
- **Company size**: ResumeBuilder sampled only firms with more than 10 employees and gives no size split. — [ResumeBuilder](https://www.resumebuilder.com/3-in-10-companies-currently-have-fake-job-posting-listed/). JobsPipe finds that 20.2% of scored LinkedIn postings come from "mass posters" with 500+ open roles. — [JobsPipe](https://jobspipe.dev/ghost-jobs/linkedin). Laws use size thresholds (Ontario 25+, NY 100+, Kentucky penalty tiers at 50; see Q4).

### Inferences
- The industry rankings mostly reflect method: churn and time-to-fill in JOLTS, ATS customer mix at Greenhouse, and profile coverage at Revelio. None can be carried over to Germany as a prior without checking against German data.
- Tech, data and creative roles rank high in both listing-age (StandOut CV) and seeker data (Enhancv), so they are a reasonable "watch" segment. Shortage occupations (vet nurses, construction trades) will produce false positives under age-based rules.

### Gaps
- No study provides a credible breakdown by company size, and none by public vs private sector except the JOLTS-gap government figure.
- No German industry or seniority breakdown exists in these industry studies (Greenhouse's Germany sample is not reported separately).

---

## Q4. What regulation has been adopted or proposed, its status as of late Oct 2026, and what its disclosure fields mean as data features

### Takeaway
Only **Ontario** has an in-force ghost-job law: the ESA Part III.1 job-posting rules, in force since 1 Jan 2026. **New York S8877/A6292-A** passed both chambers (28 Apr and 2 Jun 2026) and, as of the latest sources, awaits Governor Hochul's action. Every other US effort (NJ, CA, KY, PA) is stuck in committee or the second chamber. **No federal bill** has been introduced; the "Truth in Job Advertising and Accountability Act" is an advocacy draft. Enforcement is instead arriving through consumer-protection law: in July 2026 Texas sent LinkedIn a civil investigative demand. I found no UK legislation. The EU Pay Transparency Directive is not about ghost jobs but changes salary fields in postings. The laws converge on a common data schema: a **vacancy-status flag** (existing or current vs future or pipeline), an **expected fill date or horizon**, **removal latency after fill**, and **candidate-response deadlines**.

### Cited Findings

**Ontario (in force 1 Jan 2026): ESA Part III.1 (Bill 149, Working for Workers Four Act 2024; Bill 190, Working for Workers Five Act 2024)**
- Scope: employers with 25 or more employees on the day the posting is published. It applies to "publicly advertised job postings", excluding general recruitment campaigns or "help wanted" signs not tied to a specific position, internal-only postings, and work performed outside Ontario. — [Norton Rose Fulbright (6 Dec 2024)](https://www.nortonrosefulbright.com/en/knowledge/publications/f3b6cad0/ontario-updates-rules-on-job-postings-and-more); [DLA Piper (18 Dec 2024)](https://www.dlapiper.com/insights/publications/2024/12/ontario-confirms-new-regulation-addressing-pay-transparency-and-job-posting-requirements)
- Requirements:
  - **Existing vacancy**: a statement whether the posting is for an existing vacancy. No wording is prescribed.
  - **Pay**: expected compensation or a range, with the range no wider than CAD 50,000. Exempt where pay or the top of the range exceeds CAD 200,000.
  - **AI**: a statement whether AI is used to screen, assess or select applicants.
  - **Canadian experience**: no Canadian-experience requirements.
  - **45-day notice**: interviewees must be told whether a hiring decision has been made within 45 days of the (last) interview. Notice can be in person, in writing or by technology. Preliminary screening does not count as an interview.
  - **Records**: postings and application forms kept 3 years after the posting comes down; interview notices kept 3 years.
  
  — [Norton Rose Fulbright](https://www.nortonrosefulbright.com/en/knowledge/publications/f3b6cad0/ontario-updates-rules-on-job-postings-and-more); [DLA Piper](https://www.dlapiper.com/insights/publications/2024/12/ontario-confirms-new-regulation-addressing-pay-transparency-and-job-posting-requirements)
- The statement distinguishes a live opening from building a bank of candidates for future vacancies, and no regulation prescribes extra content for it (search excerpts of law-firm guidance). — [Fasken (Dec 2025)](https://www.fasken.com/en/knowledge/2025/12/what-ontario-employers-need-to-know-about-job-posting-obligations-for-2026). The 25-employee test applies on the posting date (search excerpt). — [Powerpay (Jan 2026)](https://www.powerpay.ca/Resources/Ontario’s-New-Job-Posting-Laws-Are-Now-in-Effect-What-Employers-Need-to-Know-in-2026)
- **As data features**:
  - `existing_vacancy` ∈ {yes, no/future or pool, missing}. "No" is an explicit, legally compelled self-label of a pipeline posting.
  - `ai_screening` ∈ {yes, no, missing}.
  - `pay_min`, `pay_max` and `pay_range_width` (≤ 50k); missing pay is allowed only above 200k.
  - The 45-day response duty cannot be seen in postings; it shows up only in candidate reviews or complaints.
  - A missing statement on a covered employer's Ontario posting is a non-compliance marker, but it cannot be told apart from an exempt small employer unless size is known.

**New York S8877 / A6292-A (passed legislature; awaiting governor)**
- Sponsors: Sen. Michael Gianaris and Asm. Jonathan Jacobson. Timeline: Senate Labor Committee 21 Apr 2026; Senate passage 28 Apr 2026 (39–19); Assembly passage 2 Jun 2026, substituted for A6292-A. The bill page shows no delivery to the governor, signature, veto or chapter number. — [NY Senate S8877](https://www.nysenate.gov/legislation/bills/2025/S8877)
- Coverage: employers with 100 or more employees (excluding government) and "third-party job posting entities". It adds Labor Law §219-b. — [NY Senate S8877](https://www.nysenate.gov/legislation/bills/2025/S8877)
- Required statement, in **bold capitals**, one of: (i) current vacancy the employer intends to fill by a stated date (within 90 days); (ii) the employer intends to fill it "NO SOONER THAN" a stated date (more than 90 days away); (iii) not a current vacancy, with resumes sought for future openings. — [NY Senate S8877](https://www.nysenate.gov/legislation/bills/2025/S8877); [Morgan Lewis (13 Jul 2026)](https://www.morganlewis.com/pubs/2026/07/new-york-severance-agreement-and-job-posting-bills-await-governors-signature)
- Removal: employers must take postings down within 2 weeks of filling. Third parties must do so within 2 weeks of knowing (or having reason to know) the role was filled or expired, and employers must notify third parties that reposted independently. — [Morgan Lewis](https://www.morganlewis.com/pubs/2026/07/new-york-severance-agreement-and-job-posting-bills-await-governors-signature)
- Penalties: $2,500 per print publication or digital platform; $5,000 if uncured after 30 days, doubling each further uncured 30 days. Enforced by Department of Labor audits and complaints. Effective immediately on signing. — [NY Senate S8877](https://www.nysenate.gov/legislation/bills/2025/S8877); [Morgan Lewis](https://www.morganlewis.com/pubs/2026/07/new-york-severance-agreement-and-job-posting-bills-await-governors-signature); [Asm. Jacobson release (18 Jun 2026)](https://assembly.state.ny.us/mem/Jonathan-G-Jacobson/story/119083)
- Status: "awaiting delivery to Gov. Kathy Hochul". — [HR Dive (11 Jun 2026)](https://www.hrdive.com/news/new-york-passed-bill-imted-at-halting-ghost-jobs/822620/). An October 2026 overview says it still awaits signature (search excerpt). — [noon.ai](https://www.noon.ai/blog/articles/196-ghost-jobs). One outlet's headline implies it was signed, but its body says it would become law only if signed. — [The HR Digest](https://www.thehrdigest.com/new-york-declares-war-on-ghost-jobs-with-bill-s8877/)
- **As data features**:
  - `vacancy_status` ∈ {current_≤90d, future_>90d, not_current/resume_collection}.
  - `intended_fill_date` or `no_sooner_than_date`.
  - Derived: posting still live more than 14 days after `intended_fill_date` is an "overdue/stale" marker.
  - The bold-capital format makes regex extraction easy.
  - Third-party removal duties would shorten stale-posting tails on aggregators, a structural break for age-based signals in NY data.

**New Jersey (pending)**
- S3509 (Moriarty; 2024–25 session; companion A4625): statement of whether the posting is for an existing vacancy and, if so, an estimated time to fill; removal once filled; other information the Labor Commissioner deems appropriate; civil penalty $1,000–$5,000. Cleared Senate Labor Committee 3–2 on 3 Mar 2025. — [InsiderNJ](https://www.insidernj.com/press-release/moriarty-bill-to-prohibit-employers-from-posting-ghost-job-openings-clears-labor-committee/); [CRS IF12977](https://www.everycrsreport.com/reports/IF12977.html)
- 2026: the Assembly Labor Committee advanced a bill on 16 Mar 2026 requiring employers or third-party posting companies to state "existing position or anticipated vacancy" (search excerpt). — [NJ Assembly Democrats](https://www.assemblydems.com/CivicAlerts.asp?AID=13001). S2136 requires existing-role disclosure among other things. — [HR Dive](https://www.hrdive.com/news/new-york-passed-bill-imted-at-halting-ghost-jobs/822620/). A summary of the bill text adds that interviewed applicants must be told, within the time frame stated in the ad, whether the job is filled; that third-party posters must remove filled jobs; and that the state can run audits (search excerpt). — [Ask the Headhunter](https://www.asktheheadhunter.com/17466/nj-outlaw-ghost-jobs-ghosting-job-seekers)
- No floor passage was found.
- **As data features**: `existing_vacancy`, `estimated_time_to_fill`, removal after fill, and a response deadline set by the posting.

**California AB 1251 (Berman; introduced 21 Feb 2025)**
- Would require every private employer that publicly advertises a job to state "whether the posting is for a vacancy". Violations would be unfair competition. — [Fisher Phillips (1 Apr 2025)](https://www.fisherphillips.com/en/news-insights/california-lawmakers-want-to-ban-ghost-job-postings.html). The enforcement body changed during drafting: the California Privacy Protection Agency (CPPA) in Fisher Phillips' reading, the Labor Commissioner per CRS. — [CRS IF12977](https://www.everycrsreport.com/reports/IF12977.html)
- Status: Newsweek (around July 2026) calls it "advancing". — [Newsweek](https://www.newsweek.com/new-york-crack-down-ghost-jobs-who-could-follow-12083123). A search excerpt said it passed the Assembly, reached the Senate in June 2025, and has been held in Senate Appropriations since Aug 2025. I found no evidence it was enacted.
- **As data features**: a binary `is_vacancy` statement.

**Kentucky HB 57 (2025) and HB 342 (2026), both stalled**
- HB 342 text: a "ghost job" is any job posting "not intended to be filled within a reasonable time frame or is posted by an employer without the intention to hire". It covers public **or internal** postings, electronic or print. The bill prohibits ghost-job postings and requires every posting to state whether it is "for an existing vacancy or a future vacancy which occurs no later than sixty (60) days after the initial posting date". Penalties: $100 per offence for employers with 50 or fewer staff; for 51 or more staff, $100 first, at least $1,000 second, doubling thereafter. — [KY HB 342 bill text (PDF)](https://apps.legislature.ky.gov/recorddocuments/bill/26RS/hb342/orig_bill.pdf)
- Status: introduced 13 Jan 2026; referred to the Economic Development & Workforce Investment committee 21 Jan 2026; no further action. — [KY HB 342 record](https://apps.legislature.ky.gov/record/26rs/hb342.html). The predecessor HB 57's last action was a committee referral on 4 Feb 2025 (search excerpt). — [KY HB 57 record](https://apps.legislature.ky.gov/record/25RS/HB57.html)
- **As data features**: `vacancy_type` ∈ {existing, future ≤ 60 days}. The 60-day horizon is a ready-made operational cut-off.

**Pennsylvania HB 2321, "Ghost Job Postings Prevention Act" (introduced 26 Mar 2026)**
- Would require postings to state role type, estimated time to fill, hire and start dates, and the extent of AI use in hiring. — [HR Dive](https://www.hrdive.com/news/new-york-passed-bill-imted-at-halting-ghost-jobs/822620/)
- Status beyond introduction was not found.

**Massachusetts**: I found no ghost-job bill. The only nearby item, S.1292 (194th General Court), concerns routing state-agency job postings through the state HR division and is not a ghost-job measure (search excerpt). — [malegislature.gov S1292](https://malegislature.gov/Bills/194/S1292)

**Federal (US)**
- CRS (Apr 2025): "No bills explicitly addressing ghost postings have been introduced in Congress." Policy options it lists: posting requirements enforced as FTC Act §5 violations, or FTC trade regulation rules. Existing hooks: FTC Act §5, the Impersonation Rule, the FTC Joint Labor Task Force (Feb 2025, covering deceptive job ads) and Title VII. Proving intent is hard. — [CRS IF12977](https://www.everycrsreport.com/reports/IF12977.html)
- June 2026: still no federal bills pending (citing CRS). Truthinjobads.org is pushing its proposed **Truth in Job Advertising and Accountability Act (TJAAA)**. — [HR Dive](https://www.hrdive.com/news/new-york-passed-bill-imted-at-halting-ghost-jobs/822620/)
- TJAAA (advocacy draft, not a bill): a change.org petition by Eric Thompson, created 26 Aug 2025, with 61,678 verified signatures when fetched. Proposed content:
  - a funded role, an authorised posting date, and a firm expiry or close when hiring is paused or complete;
  - pay range, location mode and core requirements, plus AI-screening disclosure;
  - a stop to open-ended "talent pool" postings, except good-faith high-turnover entry-level roles;
  - limits on use of applicant data;
  - recruiting records;
  - penalties, a private right of action and whistleblower protections.
  
  — [change.org petition](https://www.change.org/p/end-ghost-jobs-and-protect-job-seeker-privacy). An Oct 2025 update reported meetings with staff of Sen. James Lankford and representatives from Texas and Georgia (search excerpt). — [change.org StopGhostJobs](https://www.change.org/StopGhostJobs)
- **As data features (if enacted)**: `posting_date`, `close/expiry_date`, `funded_role` attestation, an evergreen ban, pay range, AI flag.

**Enforcement via consumer protection: Texas v. LinkedIn (CID, July 2026)**
- On 14 Jul 2026 the Texas Attorney General opened an investigation into whether LinkedIn "misled Texans by promoting and profiting from 'ghost jobs'". The CID covers advertising, marketing, verification practices and representations about Premium (about $39.99–$69.99 a month). The office defines a ghost job as a listing with no corresponding open position, or one posted with no immediate plan to fill. No charges have been filed. LinkedIn says its "policies require that jobs posted be authentic and accurately represented". — [Fox Business (15 Jul 2026)](https://www.foxbusiness.com/technology/texas-investigates-linkedin-over-alleged-ghost-jobs-targeting-job-seekers)
- The AG's office says LinkedIn "does not independently verify the hiring status of most listings" and cites studies putting ghost jobs at one-fifth to one-third of listings. The legal basis is reported as the Texas DTPA (search excerpts; the AG release itself returned 402). — [Texas AG release](https://www.texasattorneygeneral.gov/news/releases/attorney-general-ken-paxton-investigates-linkedin-advertising-fake-and-misleading-job-opportunities); [Staffing Industry Analysts](https://www.staffingindustry.com/news/global-daily-news/linkedin-investigated-over-listings-for-ghost-jobs)

**UK**: I found no ghost-job legislation, regulator guidance or government initiative. UK coverage of the Robert Walters and Employment Hero surveys mentions no regulatory measures. — [Workplace Journal](https://workplacejournal.co.uk/2026/02/ghost-job-listings-stalling-uk-job-searches-survey-finds/); [HRreview](https://hrreview.co.uk/?p=385860)

**EU / Germany (brief; covered in depth by another researcher)**
- EU Pay Transparency Directive (EU) 2023/970, Art. 5: applicants are entitled to the initial pay or its range, provided in the vacancy notice **or before the interview**; transposition deadline 7 June 2026. Not re-fetched in this session; EUR-Lex did not render. — [EUR-Lex 2023/970](https://eur-lex.europa.eu/eli/dir/2023/970/oj)
- A secondary blog reports Germany missed the deadline, with a national law expected in 2027. — [morethancareer.de](https://morethancareer.de/blog/pharma-bloodbath-part-xvii-ghost-jobs-ghost-candidates-german-data.html)
- I found no EU or German ghost-job-specific law.

### Inferences
- **Common legal schema**: (1) vacancy status (existing or current vs future or pipeline); (2) fill horizon (KY 60 days, NY 90 days, NJ "estimated timeframe", PA hire and start dates); (3) removal latency after fill (NY 14 days); (4) candidate-response duty (Ontario 45 days; NJ the period stated in the ad). These give natural labelled fields for a classifier and natural thresholds: 60 or 90 days for "future", 14 days for "stale after fill".
- **Measurement caveat**: legal disclosures are self-declarations. Strategic employers will choose "existing vacancy" by default, so a "yes" is weak evidence of genuineness. A "no / pipeline" is strong evidence of a pipeline posting, a self-admitted ghost under most definitions. A missing statement where the law applies is a compliance signal, not proof of ghosting.
- **For Germany**: none of these fields is legally required. After PTD transposition, missing pay in a German posting will still be lawful if pay is given before the interview, so "no salary" stays a weak ghost signal in Germany.
- Laws that put duties on **third-party platforms** (NY; NJ 2026) would change aggregator dynamics. Scraped age and repost features would shift after enactment, so models trained before a law takes effect would need re-baselining.

### Gaps
- The NY governor's action (signature or veto) as of 24 Oct 2026 is unconfirmed; the latest sources say pending.
- California AB 1251's final 2026 status is unverified on leginfo.
- The NJ 2026 bill numbers and progress are not fully verified (the Assembly Democrats page returned 403).
- No evidence was found on Ontario compliance rates, enforcement actions or measured effects of the existing-vacancy statement since Jan 2026.
- A claim that Sen. Ruben Gallego wrote to DOL, FTC and BLS about ghost jobs appeared only in an unsourced search excerpt and is unverified.
- The Ontario statute section numbers and O. Reg. 476/24 text were not retrieved; ontario.ca e-Laws did not render.
- No UK parliamentary petition or early-day motion was located; the search budget ran out.

---

## Q5. What have platforms and ATS vendors changed, and what does it mean for scraped signals?

### Takeaway
Platform changes so far target **identity and fraud** (verified posters, verified candidates, company email) and **posting hygiene** (auto-expiry, removal of expired jobs, application caps). They do not certify **hiring intent**. LinkedIn explicitly says its badge does not verify the job's status. These rules mechanically shape the age, repost and closure features that ghost-job studies rely on, so scraped "age" and "repost" signals partly measure platform rules rather than employer intent.

### Cited Findings

**LinkedIn**
- Job-post verification badge: shows the company has a verified Page and the poster has verified they work there (work email, Entra Verified ID, LinkedIn Learning licence; identity via CLEAR in the US). It "does not mean" an applicant is more likely to be hired, and it is piloted with "a select number of LinkedIn Jobs customers". A missing badge does not imply fraud. — [LinkedIn Help a1492056](https://www.linkedin.com/help/linkedin/answer/a1492056)
- Jan 2025: LinkedIn worked with Greenhouse on "verified" labels for postings "confirmed to be genuine" (WSJ via The Peak). — [The Peak](https://www.readthepeak.com/p/01-25-ghost-listings-flood-linkedin)
- Free job posts: active for up to 14 days, then paused; auto-closed after 30 days unless promoted. Application caps of about 10–30; one active free post at a time; a paused post shows as closed via direct links. — [LinkedIn Help a517777](https://www.linkedin.com/help/linkedin/answer/a517777)
- Since 1 Jan 2026, organisations using Apply Connect and Limited Listings (the ATS feeds) must include a company email address. — [Greenhouse support](https://support.greenhouse.io/hc/en-us/articles/115003795152)
- LinkedIn says it shows a company's response time on many jobs and whether it is reviewing candidates, and that it invests in verifying jobs, recruiters and company pages. — [Fox Business](https://www.foxbusiness.com/technology/texas-investigates-linkedin-over-alleged-ghost-jobs-targeting-job-seekers)
- "Reposted" label: no official LinkedIn documentation found. Third-party observation: LinkedIn closures cluster at the 30-day expiry (median 30 days live), and 9.9% of LinkedIn postings reappear after a gap of 10+ days. — [JobsPipe](https://jobspipe.dev/ghost-jobs/linkedin)

**Indeed**
- Indeed states "Our policies do not allow ghost jobs". It removes "millions of job posts that don't meet our strict quality standards" every month; legitimacy checks look for a description, location, title and application method. — [TheJournal.ie (28 Jul 2025)](https://www.thejournal.ie/article.php?id=6772517)
- Expired-jobs policy: jobs "no longer open must be removed or shown with reduced visibility" (e.g., application or start date passed; employer says it is no longer hiring). Jobs submitted more than 60 days before the start date may get reduced visibility. Jobs with broken third-party URLs may be removed. — [Indeed Help (UK)](https://uk.indeed.com/help/employers/articles/unavailable-jobs-on-indeed)
- Responsive Employer badge: reportedly needs an Employer Response Rate above 51%, recalculated weekly over the previous 30 days; ATS-connected jobs count if the ATS supports Disposition Sync and more than half of Indeed applicants get status updates. This comes from a third-party help page (search excerpt) and was not verified against Indeed's own documentation. — [Augusta help page](https://support.augusta.care/hc/en-us/articles/48158600621453)

**Greenhouse**
- Greenhouse Verified: badges on job posts for Fair, Prepared, Respectful and Communicative. They are earned through use of features such as email stage notifications, candidate surveys and "percentage of active applicants", refresh daily, cannot be bought, and are tier-dependent. — [Greenhouse support](https://support.greenhouse.io/hc/en-us/articles/28106556004891-Greenhouse-Verified-Overview)
- Real Talent: candidate identity verification and fraud flags, launched June 2025, with CLEAR ID checks. This is candidate-side, not job-side. — [Greenhouse release (15 Oct 2026)](https://www.greenhouse.com/newsroom/greenhouse-launches-the-orchestrated-hiring-ecosystem-to-break-ais-hiring-doom-loop); [Greenhouse–CLEAR](https://www.greenhouse.com/de/newsroom/greenhouse-and-clear-announce-partnership-to-enable-candidate-verification)
- Dream Job (5 Jun 2025): candidates flag one application a month. It addresses "black-hole applications … ghosting", not posting authenticity. — [Greenhouse release](https://www.greenhouse.com/uk/newsroom/greenhouse-launches-dream-job-to-fix-job-hunting-and-boost-candidates-chances-of-getting-hired)
- The Oct 2026 "Orchestrated Hiring Ecosystem" release mentions no verified jobs, job-status transparency or ghost-job detection. — [Greenhouse release](https://www.greenhouse.com/newsroom/greenhouse-launches-the-orchestrated-hiring-ecosystem-to-break-ais-hiring-doom-loop)

**Workday and others**: no ghost-job policy change was found. JobsPipe indexes Workday, Lever, Ashby, SmartRecruiters, Workable and Paylocity, but reports only aggregate signal rates. — [JobsPipe](https://jobspipe.dev/ghost-jobs/linkedin)

### Inferences
- **Censoring and truncation**: LinkedIn's free-post 30-day auto-close and Indeed's expiry rules truncate posting lifetimes. Age-based proxies (ResumeUp.AI's ">30 days", StandOut CV's "30+ days" tag) therefore mostly capture paid, promoted or ATS-fed postings and the platform's display rules. StandOut CV's Indeed tag is also right-censored at "30+". Cross-country differences (US 27.4% vs UK 14.2%) may reflect product mix, not intent.
- **Survivorship**: scraped snapshots come after moderation (Indeed removes millions a month), so prevalence estimates from scrapes are platform-specific.
- **Verification ≠ intent**: LinkedIn's verified badge and Greenhouse Real Talent mainly address scams and identity fraud. Treat the badge as a negative scam signal and, at best, a weak negative ghost signal.
- **Usable scraped trust features**: Greenhouse "Communicative" badge presence; Indeed Responsive Employer badge; LinkedIn response-time and "reviewing applicants" displays. Each is a platform-computed responsiveness metric correlated with active hiring. Their thresholds are not documented, except the third-party 51% claim.
- **Repost detection must be platform-aware**: on LinkedIn, auto-close followed by re-posting can be routine product behaviour (free posts must be promoted or reposted), so reposts need gap and frequency thresholds (JobsPipe uses 10+ days).

### Gaps
- No official documentation of LinkedIn's "Reposted" label logic or of Indeed's Responsive Employer threshold was found.
- I found no Workday, SmartRecruiters, StepStone or Indeed DE policy specific to ghost jobs. German platforms belong to the other researcher's scope.
- Whether the LinkedIn–Greenhouse "verified" labels from Jan 2025 still exist, and how they relate to LinkedIn's piloted badge, is unclear.

---

## Q6. Signal catalogue implied by these studies and laws (operational definition, data, direction, evidence strength)

### Takeaway
Most usable signals are cheap to scrape (age, reposts, duplicates, missing fields), but none has been validated against true hiring outcomes in public industry work. The strongest evidence comes from **legal self-declarations** (Ontario, and NY if signed) and **platform outcome data** (Greenhouse ATS activity, Revelio hires per posting), and neither is generally available in German scrapes.

### Cited Findings

| # | Signal | Operational definition | Data needed | Direction | Evidence strength | Source |
|---|---|---|---|---|---|---|
| 1 | Posting age | days since first post (or first sighting) > 30 (StandOut CV, ResumeUp.AI) or > 45 (JobsPipe) | repeated scrapes; posted_date; first_seen | older → more likely ghost | measured proxy, not validated; censored by platform expiry | [StandOut CV](https://standout-cv.com/stats/ghost-job-listings-statistics-uk); [Entrepreneur](https://www.entrepreneur.com/business-news/one-quarter-of-jobs-posted-online-are-fake-ghost-jobs-study/496683); [JobsPipe](https://jobspipe.dev/ghost-jobs/linkedin) |
| 2 | Repost after gap | same employer + title + location reappears after ≥ 10 days offline | daily or weekly snapshots; entity matching | reposting → more likely ghost | measured prevalence (vendor); seeker self-report as a cue (34%; 16.1%) | [JobsPipe](https://jobspipe.dev/ghost-jobs/linkedin); [ResumeBuilder 2026](https://www.resumebuilder.com/ghost-jobs/); [Enhancv](https://enhancv.com/blog/ghost-jobs-survey-2026-bls-data-comparison/) |
| 3 | Duplicate postings | same posting posted many times on the same day (e.g., 25 copies) | cross-board de-duplication | duplicates → more likely ghost (or spam) | measured heuristic, weak | [O&G deck](https://files.constantcontact.com/668faa28001/2cbc2d97-db5a-4af4-91c8-85fa1e34df19.pdf) |
| 4 | Missing salary | no pay figure where the law requires one | parsed pay fields; jurisdiction | missing → slightly more likely | heuristic; legal requirement in pay-transparency jurisdictions only; weak in Germany | [O&G deck](https://files.constantcontact.com/668faa28001/2cbc2d97-db5a-4af4-91c8-85fa1e34df19.pdf); [JobsPipe](https://jobspipe.dev/ghost-jobs/linkedin) |
| 5 | No valid external or ATS apply URL | apply link missing or broken | link resolution | missing → more likely (but confounded by on-platform apply) | heuristic, weak; Indeed removes broken-URL jobs | [O&G deck](https://files.constantcontact.com/668faa28001/2cbc2d97-db5a-4af4-91c8-85fa1e34df19.pdf); [Indeed Help](https://uk.indeed.com/help/employers/articles/unavailable-jobs-on-indeed) |
| 6 | Posted date far behind first sighting / refreshed dates | platform posted_date earlier than first seen, or date refreshed without content change | snapshots | mismatch → more likely | measured (vendor), rare (0.9%) | [JobsPipe](https://jobspipe.dev/ghost-jobs/linkedin) |
| 7 | Thin or generic description | description under 400 characters; generic or AI text | text | thin → more likely (weak); overlaps scam cues | heuristic; seeker self-report (14.2% cite AI-generic text) | [JobsPipe](https://jobspipe.dev/ghost-jobs/linkedin); [Enhancv](https://enhancv.com/blog/ghost-jobs-survey-2026-bls-data-comparison/) |
| 8 | Mass poster | employer with 500+ open roles on a board | employer-level counts | ambiguous (volume or pipeline) | measured (vendor), not validated | [JobsPipe](https://jobspipe.dev/ghost-jobs/linkedin) |
| 9 | Hires per posting (firm or occupation) | postings matched to new hires within 6 months by company, role, seniority, region | posting data + worker-profile or hire data | low ratio → more ghosting | measured (Revelio), trend-level | [Revelio Labs](https://www.reveliolabs.com/news/macro/ghost-job-postings) |
| 10 | ATS "no hiring activity" | posting with no interviews, scorecards or hires (reported definition) | ATS internal data | none → ghost | measured by vendor; definition unconfirmed; not scrapable | [Greenhouse blog](https://www.greenhouse.com/uk/blog/greenhouse-2024-state-of-job-hunting-report); [morethancareer.de](https://morethancareer.de/blog/pharma-bloodbath-part-xvii-ghost-jobs-ghost-candidates-german-data.html) |
| 11 | Employer responsiveness | platform badge or metric (Indeed Responsive Employer >51% response rate over 30 days, reportedly; LinkedIn response time; Greenhouse "Communicative") | scraped badges or labels | responsive → less likely ghost | platform-measured; thresholds partly undocumented | [Augusta](https://support.augusta.care/hc/en-us/articles/48158600621453); [Fox Business](https://www.foxbusiness.com/technology/texas-investigates-linkedin-over-alleged-ghost-jobs-targeting-job-seekers); [Greenhouse Verified](https://support.greenhouse.io/hc/en-us/articles/28106556004891-Greenhouse-Verified-Overview) |
| 12 | Recruiter-ghosting reviews | share of interview reviews mentioning ghosting (employer-level) | employer review text | higher → more ghost-prone employer | measured (Revelio: +120% since 2018) | [Revelio Labs](https://www.reveliolabs.com/news/macro/ghost-job-postings) |
| 13 | Existing-vacancy statement | "existing vacancy" yes / no / missing (Ontario); NY three-way status; NJ/CA/KY equivalents | text extraction; jurisdiction; employer size | "no / pipeline" → self-declared ghost or pipeline; "missing" where required → non-compliance | legal requirement (Ontario in force; others proposed) | [Norton Rose](https://www.nortonrosefulbright.com/en/knowledge/publications/f3b6cad0/ontario-updates-rules-on-job-postings-and-more); [NY S8877](https://www.nysenate.gov/legislation/bills/2025/S8877) |
| 14 | Fill horizon | stated fill date; ≤ 90 vs > 90 days (NY); future vacancy ≤ 60 days (KY); NJ estimated time to fill; PA hire and start dates | text extraction (dates) | longer horizon → pipeline | legal requirement (proposed or pending) | [NY S8877](https://www.nysenate.gov/legislation/bills/2025/S8877); [KY HB 342 text](https://apps.legislature.ky.gov/recorddocuments/bill/26RS/hb342/orig_bill.pdf); [HR Dive](https://www.hrdive.com/news/new-york-passed-bill-imted-at-halting-ghost-jobs/822620/) |
| 15 | Overdue after stated fill date | still live more than 14 days after the stated intended fill date (NY rule) | stated date + snapshots | overdue → stale or ghost | derived from a pending legal requirement | [Morgan Lewis](https://www.morganlewis.com/pubs/2026/07/new-york-severance-agreement-and-job-posting-bills-await-governors-signature) |
| 16 | Post-interview response | decision communicated within 45 days (Ontario) | candidate reports or reviews | breach → ghosting (process, not posting) | legal requirement; not observable in postings | [DLA Piper](https://www.dlapiper.com/insights/publications/2024/12/ontario-confirms-new-regulation-addressing-pay-transparency-and-job-posting-requirements) |
| 17 | Evergreen or talent-pool language | phrases like "talent pool", "future opportunities", "always accepting" | text classifier | present → pipeline posting | legal or policy category (NY option iii; TJAAA evergreen ban; Ontario "bank of candidates") | [NY S8877](https://www.nysenate.gov/legislation/bills/2025/S8877); [change.org TJAAA](https://www.change.org/p/end-ghost-jobs-and-protect-job-seeker-privacy) |
| 18 | Hiring freeze or layoffs alongside postings | firm announces freeze or layoffs while posting "urgent" roles | news or event data + postings | co-occurrence → signalling ghost | survey self-report (freeze-masking about 25% of recruiters; 7.6% of seekers cite it) | [Fortune 2024](https://www.fortune.com/2024/08/19/recruiters-posting-ghost-jobs-problem-job-seekers); [Enhancv](https://enhancv.com/blog/ghost-jobs-survey-2026-bls-data-comparison/) |
| 19 | Verification badge | LinkedIn verified-poster badge | scraped badge | present → fewer scams; not evidence on intent | platform policy (pilot) | [LinkedIn Help](https://www.linkedin.com/help/linkedin/answer/a1492056) |
| 20 | Macro openings-to-hires gap | 1 − hires/openings (JOLTS sector-month) | official statistics | context only; not posting-level | aggregate, not valid for ghost prevalence | [BLS](https://www.bls.gov/jlt/jltdef.htm); [CRS](https://www.everycrsreport.com/reports/IF12977.html) |

### Inferences
- **Evidence ladder for a German model**: (a) legally compelled self-declarations are unavailable in Germany, though Ontario and NY data could provide labelled training examples for text-based pipeline detection; (b) outcome-linked measures (hires per posting, ATS activity) need hire data; (c) scrape-only heuristics (age, repost, duplicates, missing fields) are cheap but unvalidated and platform-rule-dependent; (d) survey self-reports only guide which features to try.
- The German IAB vacancy survey's "sofort zu besetzen" share (about 79% in Q1 2026, per a secondary blog) is conceptually close to the NY "within 90 days" or KY "within 60 days" split and could serve as an aggregate benchmark for a "future/pipeline" share. — [morethancareer.de](https://morethancareer.de/blog/pharma-bloodbath-part-xvii-ghost-jobs-ghost-candidates-german-data.html). The German data-source researcher should verify this.
- Keep ghost and scam separate in feature design. Typos, requests for personal or financial data, off-platform contact and identity badges are fraud features (Resume Genius red flags; LinkedIn and CLEAR verification), not ghost features.

### Gaps
- I found no public industry study that validates any scrape-only signal against confirmed hiring outcomes (precision or recall). Validation would need ATS or hire-matched data.
- The thresholds (30, 45, 60 or 90 days; repost gap of 10 days) are conventions or legal cut-offs, not empirically tuned values.
