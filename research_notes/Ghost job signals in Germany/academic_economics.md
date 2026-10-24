# Ghost jobs, phantom vacancies and postings that do not lead to hires: academic and official-statistics evidence, with German baselines

## 1. What do the key papers find, and how do they measure ghost jobs and phantom vacancies?

### Takeaway
Peer-reviewed economics has no representative, validated estimate of how common ghost jobs are. The most-cited figure, "up to 21%" (Ng 2024), is the share of Glassdoor interview reviews that an unvalidated LLM-BERT classifier flags, not a share of job ads. The phantom-vacancy models (Chéron & Decreuse 2017; Albrecht, Decreuse & Vroman 2023) are theory calibrated to US data. They assume, rather than estimate, that half of filled vacancies leave a stale ad behind. The macro papers (Davis, Faberman & Haltiwanger 2013; Gavazza, Mongey & Violante 2018; Mongey & Horwich 2023) show that vacancies are a noisy and drifting measure of hiring effort. That is consistent with posting inflation, but it does not prove it.

### Cited Findings

#### Definitions: three phenomena to keep apart
- **Ghost posting (no genuine or immediate hiring intent).** CRS defines ghost postings as "online job postings for positions that do not exist, or that employers are not planning to fill immediately." It separately lists other causes: unintentional ones (changed circumstances, and job boards copying postings that are not removed after filling), staffing agencies inventing openings, and fraudulent scammers — [CRS In Focus IF12977, 25 Apr 2025](https://www.congress.gov/crs-product/IF12977)
- Ng defines a ghost job as an opening that "does not have an immediate or reasonably foreseeable immediate vacancy." The definition explicitly includes pipeline ads for specialised jobs where firms "want to put out ads to keep a pipeline of talent." It excludes jobs that take a long time to fill because of stringent candidate checks — [Ng 2024, arXiv 2410.21771](https://arxiv.org/abs/2410.21771)
- **Phantom vacancy (already filled, still visible).** "A job listing that continues to be advertised even though the vacancy has already been filled." The concept was introduced by Chéron & Decreuse (2017) — [Albrecht, Decreuse & Vroman, IZA DP 13704 (2020)](https://docs.iza.org/dp13704.pdf)
- **Hard-to-fill or abandoned search (genuine).** The IAB defines an abandoned recruitment (Suchabbruch) as a firm failing to fill a vacancy with a suitable applicant within a reasonable time at the given conditions (wage, qualification requirements, working conditions). It may then be rational to withdraw and re-enter the market later with changed conditions — [IAB-Forschungsbericht 6/2013, Kubis et al.](https://doku.iab.de/forschungsbericht/2013/fb0613.pdf)
- **Scam (fraudulent ad).** CRS notes that FTC Consumer Sentinel reports of job and employment-agency scams "nearly tripled from 2020 to 2024." It treats scams as distinct from ghost postings — [CRS IF12977](https://www.congress.gov/crs-product/IF12977)
- **Official US vacancy concept.** A JOLTS opening requires three things: a specific position with work available, a start possible within 30 days, and active recruiting of outside workers. CRS argues that honestly reported JOLTS openings are "unlikely to be ghost jobs" and that BLS monitors discrepancies between openings and hires, though "active recruiting" intensity is ambiguous — [CRS IF12977](https://www.congress.gov/crs-product/IF12977). This is contradicted by Ng, who argues that the "could start within 30 days" criterion is unverifiable and that "ghost jobs are counted in current vacancy rate surveys" — [Ng 2024](https://arxiv.org/pdf/2410.21771)

#### Ng (2024), "Why is it so hard to find a job now? Enter Ghost Jobs" (arXiv 2410.21771)
- **Status.** Single author, Hunter Ng (Baruch College, CUNY). arXiv v1, 29 Oct 2024, econ.GN, 17 pages of main text, no journal reference (not peer-reviewed as posted) — [arXiv abstract page](https://arxiv.org/abs/2410.21771); [PDF](https://arxiv.org/pdf/2410.21771)
- **Data.** Glassdoor "Interviews" section, scraped in July 2024. The sample is the "first 1,203 companies listed by relevance" (overall-rating filter ≥1.0), with up to 30 pages of reviews each (29,294 pages). This gives 269,347 English-language interview reviews dated 11 Mar 2009 – 16 Jul 2024, covering 1,199 companies in 97 industries. The appendix describes the sample as "randomly" retrieved and "representative," which contradicts the main-text "by relevance" description — [Ng 2024](https://arxiv.org/pdf/2410.21771)
- **Method.** Two approaches. (i) A bag-of-words search with 192 hand-compiled phrases. (ii) ChatGPT-4o labelled 2,000 random reviews with the prompt "If you are 90% sure the interview review indicates a ghost job, say yes", and a BERT model trained on those labels then classified all reviews. No precision, recall or human-validation statistics are reported — [Ng 2024](https://arxiv.org/pdf/2410.21771)
- **Headline prevalence.** BERT flags 56,559 of 269,347 reviews (21%). The keyword method flags 3,624 (1.3% in Table 3; the text says 1.6%). Of the keyword hits, 3,169 come from the word "ghosted", which describes candidates not hearing back rather than non-existent jobs. BERT flags 74.8% of negative-experience reviews but only 4.64% of positive ones. The author concedes that the data do "not explicitly verify whether a job is a ghost job", and that results are biased upward (rejected candidates) and downward (non-reviewers) — [Ng 2024](https://arxiv.org/pdf/2410.21771)
- **By firm size (BERT, share of reviews).** The pattern is an inverted U:

  | Employees | Share flagged |
  |---|---|
  | 1–50 | 14.5% |
  | 51–200 | 16.8% |
  | 201–500 | 23.9% |
  | 501–1,000 | 23.0% |
  | 1,001–5,000 | 24.8% |
  | 5,001–10,000 | 22.7% |
  | 10,000+ | 18.7% |

  — [Ng 2024](https://arxiv.org/pdf/2410.21771)
- **By industry (BERT).** Highest: Publishing 34.4%, Internet & Web Services 30.1%, Grantmaking & Charitable Foundations 29.9%, Commercial Equipment Services 29.8%, Software Development 29.8%. Lowest: Restaurants & Cafes 13.6%, National Agencies 13.2%, Accounting & Tax 12.5%, Religious Institutions 12.4%, Commercial Printing 12.2% — [Ng 2024](https://arxiv.org/pdf/2410.21771)
- **Regression.** Fixed-effects OLS of the BERT flag, N≈194,800, with standard errors clustered at year level. The high-skill job dummy is +0.030***. Size is +0.019*** and size² −0.003*** (without firm fixed effects). Review sentiment ("experience") is −0.302***, review word count +0.002***, and adjusted R² is 0.458–0.467 — [Ng 2024](https://arxiv.org/pdf/2410.21771)
- **Beveridge-curve claim.** A rolling average of flagged reviews is added to the JOLTS openings rate, using a "dynamic scaling factor based on" the average gap between openings and quits. The paper claims the curve "starts to close back up after 2022" — [Ng 2024](https://arxiv.org/pdf/2410.21771)
- **Secondary statistics cited by Ng (methods not reviewed).** Revelio Labs' chief economist Lisa Simon told Connecticut Public Radio that 1 in 5 postings did not result in a hire in 2018, versus 1 in 2 in 2024. A Clarify Capital survey of 1,045 hiring managers (2022) found that only 16% of jobs posted were planned to be filled within one month — [Ng 2024](https://arxiv.org/pdf/2410.21771)

#### Phantom vacancies: Chéron & Decreuse (ReStud 2017) and Albrecht, Decreuse & Vroman (IER 2023)
- **Chéron & Decreuse, "Matching with Phantoms", Review of Economic Studies 84(3):1041–1070 (2017); working paper AMSE 1423 (2014).** Phantoms are traders who have left the market but left traces, a by-product of search with no coordination frictions. The resulting matching function has increasing returns in the short run and constant returns in the long run. The model is embedded in the canonical search-unemployment model, and a calibration to monthly US data matches the standard model's job-finding probability and volatility — [IDEAS, AMSE WP 1423](https://ideas.repec.org/p/aim/wpaimx/1423.html)
- Chéron & Decreuse's empirical motivation comes from Craigslist. The distribution of job listings by age over one month (the point at which Craigslist deletes ads) is uniform by week, which "implies that ads are not withdrawn as soon as the corresponding jobs are filled" — as summarised in [Albrecht, Decreuse & Vroman, IZA DP 13704](https://docs.iza.org/dp13704.pdf)
- The earliest version (Decreuse 2010, HAL) names no dataset and reports no share of phantom ads. It argues that phantom unemployed workers and on-the-job seekers are observationally equivalent — [IDEAS halshs-00472751](https://ideas.repec.org/p/hal/wpaper/halshs-00472751.html)
- **Albrecht, Decreuse & Vroman, "Directed Search with Phantom Vacancies", International Economic Review 64(2):837–869 (May 2023)**, earlier IZA DP 13704 (Sep 2020) and an NBER conference version (June 2016).
  - Job seekers direct their search by listing age. When a match forms with an age-a vacancy, it creates an age-a phantom with some probability, which imposes an externality on all listings aged a or older.
  - Seekers over-apply to young listings, and firms can pay a fee to relist, which resets the listing's age.
  - The model is calibrated with US data, and the abstract mentions no French data. Phantoms contribute "a large" share of frictions, but the planner can improve little on the directed-search allocation.

  — [IDEAS, IER 2023 abstract](https://ideas.repec.org/a/wly/iecrev/v64y2023i2p837-869.html); [IZA DP 13704](https://docs.iza.org/dp13704.pdf); [NBER conference version 2016](https://conference.nber.org/conf_papers/f88698/f88698.pdf)
- **ADV calibration (IZA version).** The probability that a filled vacancy leaves a phantom is set to 0.5 as a baseline, with 0.25 and 0.75 as scenarios. It is chosen, not estimated. Implied unemployment is 3.6% / 5.63% / 11.2% across the three scenarios.
  - Other inputs: mean vacancy duration set to one month; US job-finding and separation rates for 2000–2008; listing-renewal cost of 11% of one month's value added.
  - In the baseline, "half the listings survive job filling and exogenous destruction and become phantoms." The share of listings that are true vacancies declines with listing age.
  - Mean queue: 6.58 job seekers per listing under 24 hours old and 4.51 at 24–48 hours. The first week attracts 68% of job seekers' effort.

  — [IZA DP 13704](https://docs.iza.org/dp13704.pdf)
- **Evidence ADV cite for stale information and age-directed search.**
  - Dice.com (Davis & Samaniego 2019): 47% of applications go to postings under 48 hours old and 63% to postings under 96 hours old; applications per vacancy per unit time "drop sharply as postings age."
  - Van Ours & Ridder (1992), a 5% sample of Dutch establishments: "almost all applications arrive in a short period just after the vacancy has been announced."
  - Belot, Kircher & Muller (2018): seekers favour the younger of two paired listings even one or two days apart.
  - Stale postings on CareerBuilder and Monster (Davis & Samaniego). The AEA's JOE listings rarely remove cancelled searches.
  - Fradkin (2019): about 15% of first Airbnb booking attempts fail because of stale vacancies.
  - Skandalis (2019), French data: media announcements of hiring needs raise applications without any change in postings, consistent with seekers avoiding phantoms.

  — [IZA DP 13704](https://docs.iza.org/dp13704.pdf)

#### Vacancies as a noisy measure of hiring effort: DFH (2013), GMV (2018), Mongey & Horwich (2023)
- **Davis, Faberman & Haltiwanger, "The Establishment-Level Behavior of Vacancies and Hiring", QJE 128(2):581–622 (2013); JOLTS micro data 2001–2011.**
  - The vacancy yield is defined as hires during a month per opening at the end of the previous month.
  - 45% of employment is at establishments reporting no vacancies. Weighting establishments equally, 88% report none.
  - Vacancy incidence is persistent: only 18% of current vacancies are at establishments that had none the previous month.
  - 41.6% of hires occur at establishments with no vacancy at the end of the prior month. A model of daily hiring explains about two-thirds of this (it implies 25–27%). The authors attribute the remaining third to misspecification, under-reporting, and "hires not mediated through vacancies."
  - DFH also cite Faberman & Menzio (2010): 20% of new hires in the 1982 EOPP survey involved no formal vacancy or recruiting time.

  — [DFH 2013 (QJE PDF)](https://www.econ.umd.edu/sites/www.econ.umd.edu/files/pubs/Establishment_Level_Behavior_Vacancies_Hiring_QJE_2013.pdf)
- **DFH fill rates and durations.**
  - The average daily job-filling rate is 5.2%, ranging from 4.0% (Feb 2001) to 6.9% (Jul 2009) and moving countercyclically. Mean vacancy duration is 14–25 days.
  - By industry, the daily fill rate is about 3% in Information, FIRE, Health & Education and Government; 5% in Manufacturing, Transport/Wholesale/Utilities, Professional & Business and Other Services; 7% in Retail and Natural Resources; and 12% in Construction.
  - By turnover, it ranges from 1.1% per day in the lowest turnover quintile to 11.4% in the highest.
  - By growth, it is 1–2% per day at stable establishments and more than 10% per day at those growing 7% or more in a month. Fill rates fall by more than half from small to large establishments.
  - The cross-sectional elasticity of the fill rate with respect to the hires rate is 0.820.
  - US durations are "considerably shorter than those obtained by van Ours and Ridder (1991) for the Netherlands and Andrews et al. (2008) for the United Kingdom."

  — [DFH 2013](https://www.econ.umd.edu/sites/www.econ.umd.edu/files/pubs/Establishment_Level_Behavior_Vacancies_Hiring_QJE_2013.pdf)
- **DFH recruiting intensity.** Recruiting intensity per vacancy fell about 20% from early 2007 to late 2009. The vacancy yield rose 33.5 log points from 2007 to 2009, but would have risen 42 log points had recruiting intensity stayed at its 2007 level — [DFH 2013](https://www.econ.umd.edu/sites/www.econ.umd.edu/files/pubs/Establishment_Level_Behavior_Vacancies_Hiring_QJE_2013.pdf)
- **Gavazza, Mongey & Violante, "Aggregate Recruiting Intensity", AER 108(8):2088–2127 (2018).** In this firm-dynamics model, fast-growing firms spend more on recruiting and fill vacancies faster, and recruiting intensity is procyclical. A financial shock "accounts for approximately one-half of the drop in aggregate matching efficiency observed during the Great Recession through a decline in aggregate recruiting intensity." Changes in the composition of job seekers account for about one-third of the drop. The composition channel explains only about 15% of the model's fall in recruiting intensity — [GMV 2018 (PDF)](https://violante.economics.princeton.edu/sites/g/files/toruqf5621/files/documents/gavazza-et-al-2018-aggregate-recruiting-intensity.pdf)
- **Mongey & Horwich, "Are job vacancies still as plentiful as they appear? Implications for the 'soft landing'" (Minneapolis Fed, 1 Dec 2023).**
  - The US vacancy rate peaked at 7.4% in early 2022, was 6.8 per 100 jobs in late 2022 and 5.7% in late 2023. Unemployment barely moved (3.4% in April to 3.9% in October 2023).
  - Before 2010, vacancies and quits moved together. From 2010 to 2019, vacancies rose sharply relative to quits, and the gap widened after the pandemic.
  - The authors suggest that digital technologies "have dramatically changed the cost to employers of job posting."
  - Adjustment: they fit the quits–vacancies relation over 2001–2010, extend it to 2019, and detrend. The adjusted vacancy rate peaks "well below" the raw series, at early-2000s levels. Results are robust to using hires instead of quits.
  - The authors do not discuss ghost or phantom postings or vacancy yields explicitly.

  — [Mongey & Horwich 2023](https://www.minneapolisfed.org/article/2023/are-job-vacancies-still-as-plentiful-as-they-appear-implications-for-the-soft-landing)

#### Other 2023–2026 work
- **Singer & Oktay (Outten & Golden LLP), "Ghost jobs, real costs: labor market distortions from ghost job postings", Business Economics 60(4):216–229 (Oct 2025).** The paper proposes an empirical framework that uses CoreSignal (LinkedIn-derived) posting data. "Preliminary findings" suggest that a combination of features can reliably flag ghost postings, and it measures harm to jobseekers and the groups affected. Keywords include "knapsack optimization" and "disparate impact." The full text is paywalled, so its features and accuracy were not verified — [IDEAS record](https://ideas.repec.org/a/pal/buseco/v60y2025i4d10.1057_s11369-025-00436-z.html)
- **CRS IF12977 (Apr 2025).**
  - "There are no official statistics on the magnitude of ghost jobs." Industry surveys since a September 2022 survey by a business-lending firm have opaque methods, and the firms behind them sell verification tools.
  - State bills: New Jersey (June 2024) would require disclosing whether a posting is for an existing vacancy and removing postings within two weeks of filling. Kentucky (Jan 2025) would require disclosing existing versus anticipated vacancies. California (Mar 2025) would require a disclosure statement.
  - Ontario's rules take effect in 2026.

  — [CRS IF12977](https://www.congress.gov/crs-product/IF12977)
- **Bhuller, Ferraro, Kostøl & Vigtel, "The Internet, Search Frictions and Aggregate Unemployment" (NBER WP 30911, Feb 2023).** The paper uses Norway's broadband rollout as a natural experiment. After the rollout, more firms recruited online, vacancy durations fell about 9% and unsuccessful hiring attempts fell about 13%. Job-finding rose 2.4% and starting wages about 6%. The model implies steady-state unemployment up to 14% lower — [NBER w30911](https://www.nber.org/papers/w30911)
- **Mueller, Osterwalder, Zweimüller & Kettemann, "Vacancy Durations and Entry Wages", Review of Economic Studies 91(3):1807–1841 (2024); NBER WP 25118 (2018, rev. 2020).** The paper uses linked vacancy–employer–employee administrative data. Longer vacancy durations correlate negatively with the starting wage (elasticity −0.04) and with its establishment component (−0.10). Firms' wage policies explain only a small share of the variation in how fast vacancies fill — [NBER w25118](https://www.nber.org/papers/w25118)

### Inferences
- **(a) Prevalence.** The academic literature supports a qualitative claim: stale and never-genuine postings exist and matter for frictions. It does not support a numeric base rate. A German model should not import "21%" as a prior.
  - Ng's 21% is a share of interview experiences, heavily confounded with negative sentiment (the sentiment coefficient dominates the regression).
  - Its keyword component is mostly "ghosted," which is employer non-response, not a non-existent job.
  - It has no ground truth.
- ADV's 50% phantom-birth probability is a modelling assumption. Its sensitivity analysis shows that unemployment more than triples between 25% and 75%, so the parameter is consequential but empirically unpinned.
- **(b) Predictors suggested by the academic work.** Listing age (phantom theory), employer growth and size (DFH, GMV), and high-skill or specialised roles and mid-to-large firms (Ng, weak evidence). Only the growth→fill-rate and size→fill-rate relationships are empirically established, and they come from JOLTS rather than from ghost labels.
- **Transfer to Germany.** The phantom mechanism (ads not withdrawn after filling, boards copying ads) is platform-generic and transfers directly. DFH's 14–25-day US durations do not transfer: German recruitment durations are 3–4 times longer (Section 3). The 30-day JOLTS rule also differs from the IAB concept, which includes "später zu besetzende" vacancies.

### Gaps
- No French public-employment-service (Pôle emploi / France Travail) estimate was found of the share of visible ads that are already filled, in either Chéron & Decreuse or ADV. Both papers' abstracts, and the IZA and NBER versions I read, use US data, and ADV assume the phantom probability. I read the 2020 IZA and 2016 NBER versions of ADV, not the 2023 IER full text, so its numbers may differ slightly.
- A search snippet attributed French Pôle emploi 2017 data to Slate: about 97,000 offers cancelled because the need disappeared, and about 150,000 (4.7%) abandoned for lack of candidates. The Slate page returned HTTP 403, so this is unverified.
- I could not see Singer & Oktay's (2025) feature set, accuracy metrics or prevalence estimates (paywall).
- The Revelio Labs figures (1 in 5 in 2018, 1 in 2 in 2024 postings not leading to a hire) are available only second-hand through Ng and a radio interview. Their matching method was not reviewed.
- Search budget: the shared web-search budget for this session ran out midway, so I could not search for further 2023–2026 working papers on "zombie" or evergreen postings, reposting or posting inflation (e.g., SSRN/IZA/Fed notes). Remaining material was gathered by direct fetches of known URLs. A follow-up search pass is recommended.

## 2. How well do online job postings track actual vacancies and hires, and does posting duration or removal track hiring?

### Takeaway
Online postings track the industry mix of official vacancies reasonably well. They over-represent white-collar and IT occupations, and posting counts can drift away from survey vacancies. In Germany, Indeed postings have fallen far less than IAB survey vacancies relative to pre-pandemic levels.

A posting's lifetime is a poor proxy for a vacancy's lifetime: removal lags filling, and many hires are not mediated by any posting. No study links German online postings to realised hires, so posting-duration features cannot be validated against hiring outcomes with public data.

### Cited Findings
- **Burning Glass validation (Hershbein & Kahn, NBER WP 22762, 2016; published AER 2018).**
  - Coverage: as of 2014, 60–70% of all job postings could be found online (Carnevale, Jayasundera & Repnikov 2014). An audit found occupation, education and experience coding at least 80% accurate.
  - Industry mix versus JOLTS "match each other reasonably well." Burning Glass over-represents health care & social assistance, finance & insurance and education. It under-represents accommodation & food, public administration and construction.
  - Occupation mix: computer & mathematical occupations exceed four times their OES and CPS shares. Management, healthcare-practitioner and business/financial roles are also over-represented. Transport, food preparation, production and construction are under-represented.
  - Comprehensiveness depends on the vendor's deduplication algorithms.

  — [Hershbein & Kahn, NBER w22762](https://www.nber.org/system/files/working_papers/w22762/w22762.pdf)
- **Hires not mediated by measured vacancies (US).** 41.6% of JOLTS hires occur at establishments that reported no vacancy at the end of the prior month. About one-third of that is unexplained by short-duration vacancies. Faberman & Menzio found that 20% of hires involve no formal vacancy or recruiting time — [DFH 2013](https://www.econ.umd.edu/sites/www.econ.umd.edu/files/pubs/Establishment_Level_Behavior_Vacancies_Hiring_QJE_2013.pdf)
- **Hires not attributable to postings (Germany, 2025).** Personal contacts and own employees were the decisive channel for 27% of hires. Online channels combined (BA Jobsuche, private boards, company homepage, social media) were decisive for 52% (47% in 2024), and 82% of hires involved at least one digital channel.

  | Channel (2025) | Used in share of hires | Decisive for share of hires |
  |---|---|---|
  | Own company homepage | 70% | 20% |
  | Internet job boards (excluding BA) | 57% | 21% |
  | Own employees / personal contacts | 48% | 27% |

  — [IAB-Forum, Kubis, 8 Jun 2026](https://iab-forum.de/online-medien-sind-bei-der-personalsuche-auf-dem-vormarsch/)
- **Stale postings and removal.** Online ads are "often not withdrawn" after filling. Older listings are therefore less likely to be real vacancies, and firms relist to signal that a job is still open — [ADV IZA DP 13704](https://docs.iza.org/dp13704.pdf). When an employer removes a filled posting from the original site, copies made by job boards can persist — [CRS IF12977](https://www.congress.gov/crs-product/IF12977)
- **Application timing.** 47% of Dice.com applications go to postings under 48 hours old and 63% to postings under 96 hours old. Applications per vacancy per unit time drop sharply with age (Davis & Samaniego). Van Ours & Ridder found the same pattern in Dutch data — [ADV IZA DP 13704](https://docs.iza.org/dp13704.pdf)
- **German register: deregistration is only a proxy for filling.**
  - The deregistration date is a proxy for the filling date, and the lag between them "cannot be quantified" — [BA Statistik, Engpassanalyse indicator definitions](https://statistik.arbeitsagentur.de/DE/Navigation/Statistiken/Interaktive-Statistiken/Fachkraeftebedarf/Engpassanalyse-Nav.html)
  - Registered vacancies are deregistered "if they were filled or firms abandon the search."
  - An operational change in BA vacancy handling in August 2026 produced a "deutlichen Anstieg" (marked rise) in measured completed vacancy durations in practically all Länder, which reversed in September.

  — [BA Monatsbericht, Sept 2026](https://statistik.arbeitsagentur.de/Statistikdaten/Detail/202609/arbeitsmarktberichte/monatsbericht-monatsbericht/monatsbericht-d-0-202609-pdf.pdf)
- **BA register versus IAB survey.** The BA states that the survey-based count of registered vacancies (IAB) lies below the BA register count. Outside temporary agency work, the gaps reflect reference-date concepts, sampling error and a "quasi-natural" lag in deregistration. The main gap comes from temporary-work agencies (Zeitarbeit):
  - Their registrations "richten sich stärker auf erwartete Aufträge in der Zukunft" (are oriented more toward expected future orders).
  - They register positions "wenn dahinter keine aktuell zu besetzende Stelle steht" (even when no position is currently open).
  - They deregister positions with delay.
  - The BA lists "Bildung von Bewerberpools" (building applicant pools) as a reason for register–survey differences, and says that simple grossing-up with the inverse registration rate (Meldequote) is not possible.

  — [BA Monatsbericht, Sept 2026, Sect. 5.2.3](https://statistik.arbeitsagentur.de/Statistikdaten/Detail/202609/arbeitsmarktberichte/monatsbericht-monatsbericht/monatsbericht-d-0-202609-pdf.pdf)
- **Size of the register–survey gap.** The IAB survey-based number of BA-registered vacancies was 531,900 in Q2 2026 — [IAB-Stellenerhebung indicators, sheet 7](https://doku.iab.de/arbeitsmarktdaten/IAB-Stellenerhebung_Indikatoren.xlsx). The BA register stock was 660,000 in September 2026 (+30,000 year on year) — [BA Monatsbericht, Sept 2026](https://statistik.arbeitsagentur.de/Statistikdaten/Detail/202609/arbeitsmarktberichte/monatsbericht-monatsbericht/monatsbericht-d-0-202609-pdf.pdf). The two figures refer to different months.
- **Indeed Job Postings Index, Germany (Hiring Lab GitHub data).**
  - Method: percentage change in seasonally adjusted postings since 1 Feb 2020, as a 7-day trailing average. "New postings" are those on Indeed for 7 days or fewer. Seasonal adjustment has used a Deutsche Bundesbank method since November 2024. The README does not document deduplication, expiry handling or representativeness — [hiring-lab/job_postings_tracker README](https://github.com/hiring-lab/job_postings_tracker)
  - Germany, total postings (SA, 1 Feb 2020 = 100):

    | Date | Index |
    |---|---|
    | 30 Jun 2022 | 169.3 (approximate peak) |
    | 31 Dec 2023 | 153.0 |
    | 31 Dec 2024 | 129.7 |
    | 30 Jun 2025 | 118.8 |
    | 31 Dec 2025 | 114.8 |
    | 30 Jun 2026 | 105.1 |
    | 30 Sep 2026 | 103.5 |
    | 16 Oct 2026 | 101.8 |

  - New postings stood at 109.9 on 16 Oct 2026.

  — [Indeed DE data file](https://raw.githubusercontent.com/hiring-lab/job_postings_tracker/master/DE/aggregate_job_postings_DE.csv)
- **IAB survey vacancies over the same period.**

  | Quarter | Vacancies (thousands) |
  |---|---|
  | Q2 2019 | 1,376.4 |
  | Q1 2020 | 1,220.6 |
  | Q2 2022 | 1,832.8 |
  | Q2 2026 | 1,023.4 |

  — [IAB-Stellenerhebung indicators, sheet 1](https://doku.iab.de/arbeitsmarktdaten/IAB-Stellenerhebung_Indikatoren.xlsx)
- **Hiring Lab Germany commentary.** Posts on Q1 and Q2 2026 describe an accelerated decline and a "trüben Stellenmarkt" (gloomy job market). A February 2026 post is titled "Mehr Bewerbungen bei weniger Stellen" (more applications, fewer jobs). Entry-level postings have fallen since 2022, faster than the overall market. None of the recent posts addresses ghost jobs or compares postings with IAB or BA statistics — [Indeed Hiring Lab DE](https://hiringlab.indeed.com/de/)

### Inferences
- **Germany's posting/vacancy ratio has risen (my computation from the two sources above).**
  - From Q2 2022 to Q2 2026, IAB vacancies fell 44.2% while Indeed postings fell 37.9% (30 Jun 2022 to 30 Jun 2026).
  - Relative to before the pandemic, Indeed postings are about 5% above February 2020, while IAB vacancies are 16% below Q1 2020 and 26% below Q2 2019.
  - So the ratio of Indeed postings to IAB vacancies is roughly 25–41% higher than before the pandemic.
  - This is consistent with posting inflation (more postings per real vacancy, reposting, aggregator duplication), but also with Indeed gaining coverage or market share. The data cannot separate these explanations.
  - This mirrors the US pattern Mongey & Horwich describe, where openings drift up relative to flows.
- **Posting age is not vacancy age.** Removal is a lagged and noisy signal of filling: German official statistics say so explicitly for the BA register, and there is US theory and evidence for job boards. A ghost/phantom score should therefore treat "still online" as weak evidence of being "still open," and that evidence weakens with age.
- **The register–survey gap.** If the IAB survey-based registered count of about 532k (Q2 2026) is compared with BA register stocks of roughly 630–660k (2025–2026), roughly a fifth of register entries may not correspond to vacancies that firms report as open. The BA attributes most of the gap to temporary agencies' anticipatory registrations and delayed deregistration. This is an order-of-magnitude upper bound for "register phantoms": the months are not aligned, and part of the gap is sampling and timing.
- **Validation.** Because a large share of hires bypass postings (27% decisive via personal contacts in Germany; about 40% of US hires at establishments without a reported vacancy), a "posting that disappeared without a hire being observed" is not evidence of ghosting. Hires are simply under-observed.

### Gaps
- I could not verify any Indeed Hiring Lab study that statistically compares Indeed postings with JOLTS, IAB or BA data (e.g., correlations). It was not found within the fetchable pages, and the search budget was exhausted.
- I could not verify any Lightcast or Textkernel/Jobfeed validation note for Germany, or any IAB or Destatis paper comparing online job-ad volumes with IAB vacancies or hires.
- I found no study linking German online postings to realised hires. The IAB-Stellenerhebung's last-hire module can be linked to administrative employment records (IABSE-ADIAB, 2010–2020), but not to online ads — [FDZ-Datenreport 09/2025](https://doku.iab.de/fdz/reporte/2025/DR_09-25.pdf)
- For Mueller et al. (2024), the NBER page does not name the country of the linked vacancy data. To my knowledge it is the Austrian PES vacancy register linked to social-security records, which would be the closest institutional analogue to Germany. Verify before citing.

## 3. German baselines: what do the IAB and BA sources say about vacancy durations, recruitment processes, abandoned searches and applicants per vacancy?

### Takeaway
German recruitment is slow by design. In 2025, the average time from starting a search to the hire's actual start was 86 days, against a planned 61 days. BA-registered vacancies that closed between October 2025 and September 2026 averaged 156 days from the desired start date to deregistration, and 47% were open for more than three months. Long-lived postings are therefore normal in Germany, especially in construction and craft trades (about 280–300 days).

Labour demand in Q2 2026 is at its lowest since 2016, excluding 2020. There were 1.02 million vacancies, 2.9 unemployed per vacancy and 16 applications per hire. This slack makes long-open postings with many applicants harder to explain by "shortage" in non-shortage occupations.

### Cited Findings

#### IAB-Stellenerhebung (IAB Job Vacancy Survey): stock of vacancies and market tightness
- **Vacancies (thousands, Germany; the IAB workbook updated September 2026 flags figures from 2024 onward as preliminary).**

  | Quarter | Vacancies (thousands) |
  |---|---|
  | Q4 2022 (record) | 1,986.7 |
  | Q4 2023 | 1,713.0 |
  | Q4 2024 | 1,568.3 |
  | Q1 2025 | 1,158.4 |
  | Q2 2025 | 1,058.4 |
  | Q3 2025 | 1,039.8 |
  | Q4 2025 | 1,259.0 |
  | Q1 2026 | 1,153.2 |
  | Q2 2026 | 1,023.4 (West 820.4, East 203.0) |

  — [IAB-Stellenerhebung indicator workbook, sheet 1](https://doku.iab.de/arbeitsmarktdaten/IAB-Stellenerhebung_Indikatoren.xlsx)
- **Revisions.** Earlier IAB-Forum teasers reported Q4 2024 as 1.4 million and Q1 2025 as 1.18 million, versus 1,568.3k and 1,158.4k in the current workbook. Always use the latest vintage — [IAB-Forum author index (Kubis)](https://iab-forum.de/en/?p=3053)
- **Q2 2026 context.**
  - 129,800 fewer vacancies than in Q1 2026 (−11%) and 35,000 fewer than in Q2 2025 (−3%). "Mit Ausnahme der Corona-Lockdowns im Jahr 2020 lag die Arbeitskräftenachfrage seit 2016 nicht mehr auf einem solch niedrigen Niveau" (apart from the 2020 lockdowns, labour demand has not been this low since 2016).
  - About 81% of vacancies were immediately fillable.
  - 291 unemployed per 100 vacancies (East 339, West 279).
  - Survey of 8,529 employers.

  — [IAB-Forum, Kubis, 3 Sep 2026](https://iab-forum.de/iab-stellenerhebung-2-2026-fast-drei-von-vier-bewerbungen-sind-aus-betrieblicher-sicht-ungeeignet/)
- **Q2 2026 indicators.**
  - Share immediately fillable: 80.9%. Over 2015–2026 it ranges between about 67% and 84%, with Q4 peaks.
  - Vacancy rate (Vakanzrate): 2.3%, versus a 4.5% peak in Q4 2022.
  - Unemployed per vacancy: 2.91, versus 1.23 in Q4 2022.

  — [IAB workbook, sheets 3, 10 and 11](https://doku.iab.de/arbeitsmarktdaten/IAB-Stellenerhebung_Indikatoren.xlsx)
- **Registration rate (Meldequote: share of all vacancies registered with the BA).**
  - Recent quarters: Q2 2026 52.0% (West 49.9%, East 60.3%); Q1 2026 50.9%; Q4 2025 43.1%; Q2 2025 48.7%.
  - Earlier years: 2023 about 41–43% per quarter; Q1 2017 52.7%.
  - Q4 values are systematically lowest.

  — [IAB workbook, sheet 8](https://doku.iab.de/arbeitsmarktdaten/IAB-Stellenerhebung_Indikatoren.xlsx). The BA rounds the Q2 2026 value to 52% and gives "Vorjahr: 50 %" (prior year), slightly above the workbook's 48.7% for Q2 2025 — [BA Monatsbericht, Sept 2026](https://statistik.arbeitsagentur.de/Statistikdaten/Detail/202609/arbeitsmarktberichte/monatsbericht-monatsbericht/monatsbericht-d-0-202609-pdf.pdf)

#### IAB-Stellenerhebung: recruitment processes (last successful hire)
- **Recruitment durations, Germany (days).**
  - Planned duration (geplante Besetzungsdauer): from start of search to the desired start date.
  - Actual duration (tatsächliche Besetzungsdauer): from start of search to the actual start of work.
  - Unplanned vacancy duration (ungeplante Vakanzdauer): from the desired start date to the actual start.

  | Year | Planned | Actual | Unplanned |
  |---|---|---|---|
  | 2015 | 57.9 | 84.0 | 26.1 |
  | 2019 | 59.8 | 92.3 | 32.5 |
  | 2020 | 56.9 | 82.5 | 25.6 |
  | 2021 | 60.4 | 87.1 | 26.7 |
  | 2022 | 63.1 | 96.7 | 33.5 |
  | 2023 | 66.6 | 95.6 | 29.0 |
  | 2024 | 66.1 | 94.8 | 28.7 |
  | 2025 (preliminary) | 61.3 | 86.1 | 24.8 |

  East and West are now similar (2025 actual: West 86.0, East 86.5) — [IAB workbook, sheets 14–16](https://doku.iab.de/arbeitsmarktdaten/IAB-Stellenerhebung_Indikatoren.xlsx)
- **Hires with recruitment difficulties (share of all new hires).** 2015 35.8%; 2017 42.7%; 2018 44.2%; 2019 44.0%; 2020 34.0%; 2021 37.0%; 2022 44.2%; 2023 41.1%; 2024 36.3%; 2025 30.5% — [IAB workbook, sheet 12](https://doku.iab.de/arbeitsmarktdaten/IAB-Stellenerhebung_Indikatoren.xlsx)
- **Reasons for difficulty, 2025 (share of all new hires).** Insufficient qualification of applicants 18.7%; too few applicants 18.6% (35.8% in 2022); excessive wage demands 14.0%; unwillingness to accept working conditions 12.5% — [IAB workbook, sheet 13](https://doku.iab.de/arbeitsmarktdaten/IAB-Stellenerhebung_Indikatoren.xlsx)
- **Applications per hire (reference year 2025, hires subject to social insurance, excluding apprentices).**
  - Average: rose from 9 in 2022 to 16 in 2025. Only about 4 per hire (28%) are suitable from the employer's view, so roughly 72% are unsuitable.
  - By qualification: specialist and expert roles receive 22 applications per hire, with the lowest suitable share (23%). Helper roles receive 10.
  - By occupation: IT and natural-science service occupations receive 40 per hire; personal services receive 8.
  - By firm size: firms with 250+ employees receive 27; firms with fewer than 50 receive 8.

  — [IAB-Forum, Kubis, 3 Sep 2026](https://iab-forum.de/iab-stellenerhebung-2-2026-fast-drei-von-vier-bewerbungen-sind-aus-betrieblicher-sicht-ungeeignet/)
- **Channels, 2025.** Company homepage used 70% / decisive 20%; job boards (excluding BA) 57% / 21%; own employees and personal contacts 48% / 27%. Online channels combined were decisive for 52% of hires (47% in 2024), and 82% of hires involved at least one digital channel — [IAB-Forum, Kubis, 8 Jun 2026](https://iab-forum.de/online-medien-sind-bei-der-personalsuche-auf-dem-vormarsch/)
- **Origins of hires.** In 2024, 62.4% of new hires came directly from another job (about 64% in 2023, about 43% in 2010). About 19% came from unemployment (about 18% in 2023, about 38% in 2010) — [IAB-Forum, Kubis, 4 Sep 2025](https://iab-forum.de/iab-stellenerhebung-die-meisten-neueinstellungen-gehen-nach-wie-vor-auf-jobwechsel-zurueck/)
- **Survey design.**
  - A representative establishment survey covering all vacancies, including those not registered with the BA. It has run as a written Q4 survey since 1989, with quarterly telephone follow-ups since 2006.
  - Waves cover 5,150–21,115 establishments.
  - Module 3 asks about the last new hire and the last failed recruitment attempt: channels, search and filling times, applicant numbers, difficulties and compromises.
  - The last hire can be linked to administrative records (IABSE-ADIAB, 2010–2020).
  - Analyses of the last abandoned search use a dedicated weight (greggew*f422).

  — [FDZ-Datenreport 09/2025](https://doku.iab.de/fdz/reporte/2025/DR_09-25.pdf)

#### Abandoned or failed searches
- **The survey question.** The IAB questionnaire asks (Q4 2012 version, question 11): "Ist es in den letzten 12 Monaten vorgekommen, dass Sie die Personalsuche abbrechen mussten, weil Sie kein geeignetes Personal finden konnten?" (In the last 12 months, did you have to abandon a search because you could not find suitable staff?), plus the number of positions. The question concerns only the external labour market — [IAB-Forschungsbericht 6/2013](https://doku.iab.de/forschungsbericht/2013/fb0613.pdf)
- **Firms' reactions to the last abandoned search (2010–2012).** The main reactions are reallocating tasks to existing staff (normal hours or overtime), forgoing orders, and technical or organisational changes. Using temp workers, internal filling and "no need because the market changed" also occur — [IAB-Forschungsbericht 6/2013](https://doku.iab.de/forschungsbericht/2013/fb0613.pdf)
- **Abandonment is often temporary (expert pretest with 50 HR managers, 2013).**
  - Asked to define a "Suchabbruch" (abandoned search) abstractly, 60% understood it as permanent and 34% as temporary.
  - In company practice, 64% said abandonment is temporary and 32% permanent.
  - For the last concrete case, 21 (42%) said it was final, 22 (44%) said a new job ad had already been placed, and 7 (14%) gave no usable answer.

  — [IAB-Forschungsbericht 6/2013](https://doku.iab.de/forschungsbericht/2013/fb0613.pdf)

#### BA register statistics (Statistik der Bundesagentur für Arbeit)
- **September 2026.**
  - Registered stock: 660,000, of which 635,000 (96.2%) are "Vakanzen."
  - Inflow: 132,000. Outflow (Abgang): 128,000, of which 5.8% were "ohne Vakanzzeit" (without vacancy time) and 45.6% were open "über drei Monate" (more than three months).
  - Average vacancy duration of September outflows: 152 days (−13 days, −7.9% year on year).
  - BA-X job index: 104 (2015 = 100).

  — [BA Monatsbericht, Sept 2026](https://statistik.arbeitsagentur.de/Statistikdaten/Detail/202609/arbeitsmarktberichte/monatsbericht-monatsbericht/monatsbericht-d-0-202609-pdf.pdf)
- **Rolling year, October 2025 – September 2026.** Inflows 1,537,000; outflows 1,505,000. 47% of deregistered positions had been vacant for more than three months. The average completed vacancy duration (abgeschlossene Vakanzzeit, from the desired start date to deregistration) was 156 days. That is 13 days fewer than a year earlier but "etwa 70 Tage mehr als zehn Jahre zuvor" (about 70 days more than ten years earlier) — [BA Monatsbericht, Sept 2026](https://statistik.arbeitsagentur.de/Statistikdaten/Detail/202609/arbeitsmarktberichte/monatsbericht-monatsbericht/monatsbericht-d-0-202609-pdf.pdf)
- **Shortage analysis (Engpassanalyse), reference year 2025.**
  - Six shortage indicators are scored 0–3 and averaged, including the median completed vacancy duration. A mean of 2.0 or more means a shortage occupation; 1.5 to under 2.0 means "unter Beobachtung" (under observation).
  - For this indicator, vacancy duration runs from the desired start date to deregistration at the BA employer service. It counts only filled positions (cancelled offers are excluded) and uses the median.
  - Fixed thresholds: under 40 days = 0 points; 40–<60 = 1; 60–<80 = 2; 80 or more = 3.
  - Other indicators: jobseekers per vacancy (Arbeitsuchenden-Stellen-Relation), occupation-specific unemployment rate, change in the foreign-employment share, outflow rate from unemployment, and median wage growth.

  — [BA Statistik, Engpassanalyse](https://statistik.arbeitsagentur.de/DE/Navigation/Statistiken/Interaktive-Statistiken/Fachkraeftebedarf/Engpassanalyse-Nav.html)
- **Shortage occupations, May 2026 analysis.** Shortages appear mainly in nursing, medical occupations, and construction and craft trades, and also for cooks, professional drivers and educators. The BA says there is no general labour or skills shortage — [BA Monatsbericht, Sept 2026](https://statistik.arbeitsagentur.de/Statistikdaten/Detail/202609/arbeitsmarktberichte/monatsbericht-monatsbericht/monatsbericht-d-0-202609-pdf.pdf)
- **Occupations with the longest vacancy durations (BA data, secondary source; article text gives Feb 2025 – Jan 2026; mean or median not stated).**

  | Occupation | Days |
  |---|---|
  | Interior construction and drywall (Aus- und Trockenbau) | 300 |
  | Mining, open-cast mining and blasting | 299 |
  | Natural stone and building materials | 298 |
  | Plumbing, heating and air-conditioning (SHK) | 295 |
  | Floor laying | 292 |
  | Structural construction (Hochbau) | 281 |
  | Driving and sports instructors | 280 |
  | Construction and transport machinery operators | 277 |

  — [Statista infographic, 24 Feb 2026 (BA data)](https://de.statista.com/infografik/35884/berufe-mit-den-laengsten-vakanzzeiten-von-arbeitsstellen-in-deutschland)

### Inferences
- **Baseline for "normal slowness".** In Germany, roughly 3 months (86–97 days in 2022–2025) from search start to actual start is normal for a successful hire. The planned component alone is about 2 months (61–67 days).
  - Online postings typically appear at or near search start, and the hire's start date can come well after the hiring decision. A posting older than about 90 days is therefore not anomalous in itself.
  - IAB durations exclude abandoned searches (survivorship), so the distribution of all postings' lifetimes will be longer still.
- **Means versus medians.**
  - The BA's mean completed vacancy duration (156 days) far exceeds the Engpassanalyse scale, where a median of 80+ days already earns the maximum shortage score.
  - It also far exceeds the IAB's 25-day unplanned vacancy duration, which measures the same span (desired start to filling) for successful hires.
  - Three factors drive the gap: right skew in durations; selection (harder-to-fill vacancies are more likely to be registered); and, plausibly, stale register entries such as delayed deregistration and temporary agencies' anticipatory postings, which the BA itself names.
  - A scoring model should use occupation-specific medians and upper quantiles, not means, and should treat BA register durations as an upper envelope that partly contains phantom time.
- **Use relative, occupation-specific thresholds.** A posting 250 days old for a drywall or SHK job is within the normal range; the same age for an office job in a slack occupation is not.
- **Distinguishing ghost from hard-to-fill.** Hard-to-fill shows up as few or unsuitable applicants (reasons tables). Ghost or pipeline postings are more plausible where applicant inflows are high but no hire follows; in 2025, IT and natural-science roles attracted 40 applications per hire.
- **Slack interacts with candidate experience.** In slack markets (2.9 unemployed per vacancy; 16 applications per hire, 72% unsuitable), "never heard back" experiences become common even for genuine postings. Candidate-experience signals are less diagnostic in 2025–2026 than in 2022.
- **Reposting after abandonment is legitimate German behaviour.** In about 44% of last abandonment cases in the 2013 pretest, a new job ad had already been placed. Reposting should not be scored as ghost behaviour without other evidence, such as unchanged content, no change in conditions, or continuous presence.
- **Seasonality.** Q4 values (vacancies, share immediately fillable, Meldequote) differ systematically from other quarters. Baselines should be quarter-specific.

### Gaps
- **Prevalence of abandoned searches.** I found no recent published figure for the share of German establishments, or of recruitment attempts, that end in abandonment. The question exists in the IAB survey and can be computed from FDZ microdata, but no IAB-Kurzbericht or Forum number was retrievable in this session.
- **Internal hiring.** I found no IAB figure on the share of vacancies filled internally. The IAB survey focuses on external recruitment.
- **BA "abgeschlossene Laufzeit".** The BA duration from registration to deregistration, which is more comparable to a posting's lifetime, and the national median completed vacancy duration for 2025, were not retrieved. The Engpassanalyse tables (CSV) contain occupation-level medians.
- **Number of shortage occupations.** The count in the 2025/26 Engpassanalyse was not retrieved.
- **Unverified durations by qualification level (search snippet only; not used above).** An IAB-Kurzbericht (4/2016) reportedly gives an average search duration of 85 days in 2015: 53 days for unskilled roles and 107 days for academic positions, with about a third of hires via personal contacts. The workbook's 84.0 days for 2015 is consistent, but the breakdown is unverified.
- **German online-ad comparisons.** I found no German study (IAB with Textkernel/Jobfeed, Destatis, Cedefop) comparing online-ad volumes with IAB vacancies or hires. Indeed's German posts in 2025–2026 do not address this.

## 4. Which measurable features does this literature suggest or validate?

### Takeaway
No feature has been validated against ground-truth ghost labels in peer-reviewed work. Singer & Oktay (2025) claim a working feature combination but are paywalled; Ng's labels are unvalidated. The strongest-grounded signals are three:
- Listing age relative to occupation norms, plus evidence of staleness (phantom theory and the evidence on application timing).
- Posting volume relative to employer growth, size and turnover (DFH and GMV establish how fill rates vary with these).
- Employer type, specifically temporary-work agencies, where the BA officially acknowledges registrations without a current opening.

Labour-market tightness and Engpass status are the main controls for separating genuinely slow hiring from ghosting.

### Cited Findings
- **Listing age.** Older listings are less likely to be real vacancies. Firms relist to signal that a job is still open, and relisting is costly (calibrated at 11% of one month's value added) — [ADV IZA DP 13704](https://docs.iza.org/dp13704.pdf). On Craigslist, listing ages are uniformly distributed over the 30-day life of an ad, meaning ads persist after filling — [ADV, citing Chéron & Decreuse](https://docs.iza.org/dp13704.pdf). Applications concentrate on postings under 48–96 hours old — [ADV, citing Davis & Samaniego](https://docs.iza.org/dp13704.pdf)
- **Employer growth, size and turnover.** Job-filling rates rise steeply with growth (1–2% per day when stable versus more than 10% per day at 7%+ monthly growth), fall with size, and rise with turnover (1.1%–11.4% per day across turnover quintiles) — [DFH 2013](https://www.econ.umd.edu/sites/www.econ.umd.edu/files/pubs/Establishment_Level_Behavior_Vacancies_Hiring_QJE_2013.pdf). Fast-growing firms recruit more intensively — [GMV 2018](https://violante.economics.princeton.edu/sites/g/files/toruqf5621/files/documents/gavazza-et-al-2018-aggregate-recruiting-intensity.pdf)
- **Firm size and skill level (weak evidence).** Ng finds an inverted U in firm size (peak 24.8% at 1,001–5,000 employees) and a +3 percentage point effect for high-skill jobs, with specialised industries (publishing, software, internet) highest — [Ng 2024](https://arxiv.org/pdf/2410.21771)
- **Low posting cost.** Posting is free on Indeed, on LinkedIn for the first post, on Glassdoor for 10 jobs for 7 days, and on Handshake; ZipRecruiter costs $16/day and Monster $12/day. In one anecdote, a bundle of three listings for $400/month led an employer to keep extra listings for jobs she was not filling — [Ng 2024](https://arxiv.org/pdf/2410.21771). Mongey & Horwich suggest digital technology "dramatically changed the cost to employers of job posting" — [MH 2023](https://www.minneapolisfed.org/article/2023/are-job-vacancies-still-as-plentiful-as-they-appear-implications-for-the-soft-landing). Counter-evidence: in Norway, cheaper online search shortened vacancy durations by about 9% and cut unsuccessful hiring attempts by about 13% — [Bhuller et al. 2023](https://www.nber.org/papers/w30911)
- **Third-party copies and register delays.** Postings copied by boards are not removed when the original is — [CRS IF12977](https://www.congress.gov/crs-product/IF12977). The BA register suffers delayed deregistration, especially in temporary agency work — [BA Monatsbericht, Sept 2026](https://statistik.arbeitsagentur.de/Statistikdaten/Detail/202609/arbeitsmarktberichte/monatsbericht-monatsbericht/monatsbericht-d-0-202609-pdf.pdf)
- **Temporary-work agencies.** Agencies register positions for expected future orders "wenn dahinter keine aktuell zu besetzende Stelle steht" (even when no position is currently open) and build applicant pools — [BA Monatsbericht, Sept 2026](https://statistik.arbeitsagentur.de/Statistikdaten/Detail/202609/arbeitsmarktberichte/monatsbericht-monatsbericht/monatsbericht-d-0-202609-pdf.pdf). Staffing agencies "may also invent and post job openings to show employers they could recruit talented people" — [CRS IF12977](https://www.congress.gov/crs-product/IF12977)
- **Future versus immediate vacancies.** JOLTS counts only jobs that could start within 30 days — [CRS IF12977](https://www.congress.gov/crs-product/IF12977). The IAB separates immediately fillable vacancies (80.9% in Q2 2026) from later ones — [IAB workbook, sheet 3](https://doku.iab.de/arbeitsmarktdaten/IAB-Stellenerhebung_Indikatoren.xlsx). The Kentucky bill would require disclosing "existing vacancy or an anticipated future vacancy" — [CRS IF12977](https://www.congress.gov/crs-product/IF12977)
- **Tightness and shortage controls.** The BA's shortage scoring (median vacancy-duration thresholds 40/60/80 days; jobseekers per vacancy; occupation-specific unemployment rate) — [BA Engpassanalyse](https://statistik.arbeitsagentur.de/DE/Navigation/Statistiken/Interaktive-Statistiken/Fachkraeftebedarf/Engpassanalyse-Nav.html). Applications per hire by occupation (40 in IT and natural sciences versus 8 in personal services) and the suitable share (23% for specialists and experts) — [IAB-Forum, 3 Sep 2026](https://iab-forum.de/iab-stellenerhebung-2-2026-fast-drei-von-vier-bewerbungen-sind-aus-betrieblicher-sicht-ungeeignet/)
- **Wages.** Longer vacancy durations correlate with lower entry wages, but weakly (elasticities −0.04 and −0.10) — [Mueller et al., NBER w25118](https://www.nber.org/papers/w25118)
- **Macro posting-to-flow ratios.** US openings rose relative to quits from 2010 to 2019 and after the pandemic — [MH 2023](https://www.minneapolisfed.org/article/2023/are-job-vacancies-still-as-plentiful-as-they-appear-implications-for-the-soft-landing). Vacancy yields and recruiting intensity per vacancy vary over the cycle (about −20% in 2007–2009) — [DFH 2013](https://www.econ.umd.edu/sites/www.econ.umd.edu/files/pubs/Establishment_Level_Behavior_Vacancies_Hiring_QJE_2013.pdf)
- **Candidate-experience text.** Interview reviews flagged as ghost cluster on topics such as multiple interview rounds, long waits, no salary negotiation and no follow-up — [Ng 2024](https://arxiv.org/pdf/2410.21771)
- **Abandonment and reposting.** In about 44% of last-case abandonments, a new ad had already been placed — [IAB FB 6/2013](https://doku.iab.de/forschungsbericht/2013/fb0613.pdf)

### Inferences
Below is the feature catalogue synthesised from the findings above. Evidence strength is graded as follows:
- **Empirically validated** means the underlying relationship is established in data. None is validated as a ghost-job predictor.
- **Theoretical** means it is implied by a model.
- **Suggestive** means it rests on anecdotes, official qualitative statements or unvalidated classifiers.

**F1. Relative posting age (age versus the occupation's normal duration)**
- **Definition:** age_days = observation date − first-seen date of the deduplicated job, across all sources and reposts. rel_age = age_days divided by an occupation × region reference duration. Flag ages above that occupation's p75 or p90.
- **Reference duration:** either (i) BA completed vacancy-duration medians by occupation (KldB 2010), plus the IAB planned-duration offset of about 61 days, because BA durations start at the desired start date rather than the posting date; or (ii) the empirical lifetime distribution of postings that disappeared within the same occupation and region.
- **Data:** posting timestamps (first and last seen); KldB coding; BA Engpassanalyse medians; BA occupation-level vacancy-duration statistics; IAB durations.
- **Direction:** raises phantom and ghost likelihood beyond high quantiles. Weight should fall in Engpass occupations.
- **Evidence:** theoretical (ADV, Chéron & Decreuse), plus indirect empirical evidence (Craigslist age distribution; Dice application timing).
- **German caveats:** the normal duration is about 86 days from search start to actual start (2025). Construction and craft trades average about 280–300 days. BA means (156 days) are right-skewed and inflated by register artefacts (the August 2026 operational change; delayed deregistration). Use quarter-specific baselines.

**F2. Origin removal lag (staleness)**
- **Definition:** a job that is no longer on the employer's career page, ATS feed or BA Jobsuche but is still live on aggregators. Measure days since the origin disappeared, or a binary "origin missing."
- **Data:** multi-source crawling with source attribution, including the BA's HR-BA-XML syndicated feeds.
- **Direction:** strongly raises phantom likelihood (already filled or withdrawn).
- **Evidence:** suggestive (CRS on board copying; BA on delayed deregistration; ADV on ads not withdrawn).
- **German caveats:** many boards re-publish BA listings. The BA register itself lags filling by an amount that "cannot be quantified."

**F3. Repost and renewal pattern**
- **Definition:** count of re-listings of the same job in 180 or 365 days (same employer, normalised title, location, near-duplicate text); the gaps between them; a content-change flag (salary, requirements, hours); and "evergreen" status (continuously live for 6 months or more with periodic refresh and no content change).
- **Data:** a posting history with near-duplicate detection.
- **Direction:** ambiguous.
  - Raises ghost or pipeline likelihood when refreshes are periodic, content is unchanged and presence is near-continuous.
  - Lowers it (pointing to a genuine hard-to-fill role) when a repost follows a gap with changed conditions, the "temporary abandonment" pattern.
- **Evidence:** theoretical (in ADV, renewal is a costly signal that a vacancy is still open, which argues against ghosting). There is qualitative German evidence that re-advertising after abandonment is common (44% of last cases).
- **German caveats:** temporary agencies and large employers often post continuously; treat them as a separate class.

**F4. Employer posting intensity versus growth (vacancy-yield proxy)**
- **Definition:** active deduplicated postings divided by expected hires, where expected hires = max(0, Δheadcount) + replacement hires (headcount × sector turnover rate). Alternatively, postings per 100 employees compared with peers in the same sector and size class.
- **Data:** employer headcount over time (company registers or annual reports, LinkedIn or other headcount proxies); sector turnover rates.
- **Direction:** raises ghost likelihood when postings are far above expected hires, especially when headcount is flat or falling.
- **Evidence:** the growth→fill-rate and size→fill-rate relationships are empirically validated (DFH, GMV). Its use as a ghost predictor is suggestive.
- **German caveats:** headcount data for private firms are patchy. Job-to-job churn (62.4% of hires in 2024) means replacement hiring is large, and high-turnover sectors (hospitality, retail, temporary agencies) legitimately post a lot.

**F5. Posting-to-vacancy and posting-to-hire ratios by sector and region (macro prior)**
- **Definition:** deduplicated online postings in a cell divided by IAB vacancies (by sector or size class, quarterly) or by BA-registered stock or inflows. Compare with the cell's pre-2020 ratio.
- **Data:** posting corpus; IAB workbook (sector and size breakdowns); BA statistics by district (Kreis) and occupation.
- **Direction:** a rising ratio raises the prior probability for all postings in the cell.
- **Evidence:** suggestive (MH's US openings/quits drift; Germany's Indeed/IAB ratio up an estimated 25–41% since 2019/20, my computation).
- **German caveats:** IAB regional detail is only West/East. The BA register includes temporary agencies' anticipatory registrations. Indeed's coverage growth may confound the ratio.

**F6. Labour-market tightness and shortage status of the occupation-region**
- **Definition:** BA jobseekers-per-vacancy ratio; occupation-specific unemployment rate; Engpass score (0–3 average) and status (shortage, under observation, none). Optionally, IAB applications per hire by occupation group.
- **Data:** BA Engpassanalyse (annual, KldB occupations); BA monthly statistics; IAB.
- **Direction:** in slack occupations, long-lived postings are harder to explain, so ghost likelihood rises. In shortage occupations, long durations are expected, so ghost likelihood falls.
- **Evidence:** theoretical and suggestive, but the data are officially defined and robust.
- **German caveats:** 2025–2026 is a slack phase overall (2.9 unemployed per vacancy, applications per hire up from 9 to 16), yet shortages persist in care, medical, construction, craft, cooking, driving and education.

**F7. Employer type: temporary-work agency or recruiter**
- **Definition:** sector WZ 78 (temporary-work agencies, WZ 78.2), or text cues such as "für unseren Kunden" (for our client) and pool wording.
- **Data:** employer classification from a register or industry code, plus posting text.
- **Direction:** raises "no current specific vacancy" (pool posting) likelihood. This is not necessarily deceptive.
- **Evidence:** a German official qualitative statement (BA methodological note), plus CRS.
- **German caveats:** temporary agency work is a large, legitimate hiring channel. Score it as a separate class ("pool or anticipatory posting") rather than as "ghost."

**F8. Declared start date and pool wording**
- **Definition:** stated start date more than 30–90 days away; or "Talentpool" (talent pool), "Initiativbewerbung" (unsolicited application) or "Vorratsstelle" (stockpile position) wording; versus "ab sofort" (immediately).
- **Data:** posting text.
- **Direction:** explicit future or pool postings are a transparent future vacancy or pipeline, not deceptive ghosting. Classify them separately. Hidden pipeline intent cannot be detected from this feature.
- **Evidence:** definitional (JOLTS 30-day rule; IAB immediate versus later; disclosure bills).
- **German caveats:** the IAB counts later-to-fill positions (about 19% in Q2 2026) as genuine vacancies.

**F9. Applicant volume versus age (if observable)**
- **Definition:** displayed applicant counts or click counts over time; interaction of high applicants × high relative age.
- **Data:** platform-exposed applicant counters; otherwise unavailable.
- **Direction:** high applicant inflow plus long age raises ghost or pipeline likelihood. Low inflow plus long age points to a genuine hard-to-fill role.
- **Evidence:** suggestive (IAB reasons: too few applicants 18.6% and insufficient qualification 18.7% of 2025 hires; application timing evidence).
- **German caveats:** the application baseline varies widely: 40 per hire in IT and natural sciences, 8 in personal services, 27 at large firms versus 8 at small ones.

**F10. Firm size**
- **Definition:** employee size band.
- **Direction:** a weak rise for mid-to-large firms (Ng's inverted U). But larger firms also have genuinely longer durations (DFH) and more applicants (IAB: 27 versus 8 per hire).
- **Evidence:** weak and suggestive.
- **German caveats:** use only as an interaction or control.

**F11. Skill level and specialisation**
- **Definition:** KldB requirement level (helper, skilled worker, specialist, expert); specialised IT, media or publishing roles.
- **Direction:** a weak rise for specialist and expert roles (pipeline motive).
- **Evidence:** suggestive (Ng; IAB suitable share of 23% for specialists and experts).
- **German caveats:** expert roles also legitimately take longer.

**F12. Distress or freeze context**
- **Definition:** layoffs, insolvency filings, Kurzarbeit (short-time work) reports or falling headcount at the employer while posting volume stays flat.
- **Data:** news, insolvency notices, headcount proxies.
- **Direction:** raises ghost likelihood.
- **Evidence:** suggestive (CRS: changed circumstances alter hiring intent).
- **German caveats:** Kurzarbeit data are not published at firm level.

**F13. Channel and cost**
- **Definition:** posted only on free boards or aggregators with no career-site or BA presence; number of boards.
- **Direction:** free-only postings with no origin raise ghost or phantom likelihood. Multi-channel postings that include the company homepage are the norm for genuine hires: the homepage was used in 70% of 2025 hires and job boards in 57%.
- **Evidence:** suggestive (Ng's cost table; MH). Norway shows lower costs can improve matching.

**F14. Posted wage versus market**
- **Definition:** posted pay relative to the occupation × region median.
- **Direction:** a low wage explains slower genuine filling, so it lowers the ghost interpretation of long age.
- **Evidence:** empirically validated but small effect (Mueller et al.).
- **German caveats:** missing-salary rates in German ads were not researched here.

**F15. Candidate-experience text**
- **Definition:** share of the employer's interview reviews mentioning "Stelle bereits besetzt" (position already filled), "auf Eis gelegt" (put on hold), "nie zurückgemeldet" (never heard back) and similar phrases.
- **Direction:** raises ghost likelihood.
- **Evidence:** weak (Ng's classifier is unvalidated and conflates candidate ghosting with ghost jobs).
- **German caveats:** in slack markets, non-response is common even for genuine postings.

### Gaps
- No peer-reviewed study supplies labelled ghost postings for validating any feature. Singer & Oktay's feature list and accuracy could not be read.
- No German evidence on repost frequency, origin-removal lags or posting-lifetime distributions in online data was found. These would have to be estimated from the project's own crawled data.
- Lightcast and Revelio methods for "postings that never lead to a hire" were not retrieved (out of scope and blocked by the search budget).

## 5. Why do employers post with no immediate intent to hire?

### Takeaway
The literature and official sources list option-value and pipeline motives, information gathering, signalling, process or compliance formalities, and agency business models (applicant pools). There are also non-deliberate causes: changed circumstances, stale or copied ads, and continued advertising after filling to find a better replacement. In Germany, the only officially documented motive is temporary agencies' anticipatory registrations and applicant pools in the BA register. The others are documented mainly from US surveys, anecdotes and theory.

### Cited Findings
- **CRS list of motives.** Evaluating "the potential pool of candidates for future job postings or collect[ing] resumes for hiring at a later time"; suggesting growth, "either to signal to existing employees that they are replaceable or that their workload may soon be more widely shared, or to attract potential investors"; demonstrating a diverse applicant pool when an internal candidate is planned; looking for "extraordinary potential employees"; and interviewing with no intent to hire — [CRS IF12977](https://www.congress.gov/crs-product/IF12977)
- **Non-deliberate causes (CRS).** Changed circumstances alter intent to hire. Job boards copy postings that are not removed after filling. Staffing agencies invent openings to show employers they could recruit talented people. Fraudulent scammers post fake jobs or impersonate employers — [CRS IF12977](https://www.congress.gov/crs-product/IF12977)
- **Ng's speculative motives.**
  - HR "productivity theater" to avoid downsizing.
  - "Constantly advertising vacancies is a strategy to combat long hiring times in specialized jobs."
  - Receiving applications constantly gives an "on-the-ground" sense of applicants and salary expectations, which can also be used to keep current employees "on edge."
  - The low marginal cost of posting.
  - Signalling to shareholders, citing Chen & Li (2023), Review of Accounting Studies, on vacancy duration and future profitability.

  — [Ng 2024](https://arxiv.org/pdf/2410.21771)
- **Formality and grant motives.** A 2013 WSJ article on "phantom job listings" reported colleges posting ads as a "formality" and HR posting ads or risking losing "federal grant money" (via Ng) — [Ng 2024](https://arxiv.org/pdf/2410.21771)
- **Replacement hiring.** In Acharya & Wee (2018), firms that have filled their vacancies keep advertising to find more productive replacement workers, so the longer a job has been advertised, the less likely an application succeeds — [ADV IZA DP 13704](https://docs.iza.org/dp13704.pdf)
- **German official statement.** Temporary-work agencies register positions oriented to expected future orders, including when no position is currently open, and deregister with delay. The BA lists building applicant pools as a cause of register–survey discrepancies — [BA Monatsbericht, Sept 2026](https://statistik.arbeitsagentur.de/Statistikdaten/Detail/202609/arbeitsmarktberichte/monatsbericht-monatsbericht/monatsbericht-d-0-202609-pdf.pdf)
- **Legitimate re-advertising after abandonment.** Abandoning a search can be "Lernprozess" (a learning process) ending in a new advertisement under changed conditions, or in internal solutions. For the last concrete case of abandonment, 44% of 50 firms had already re-advertised — [IAB-Forschungsbericht 6/2013](https://doku.iab.de/forschungsbericht/2013/fb0613.pdf)
- **Lower posting costs.** Mongey & Horwich suggest that lower posting costs from digital technology may have steadily raised measured vacancies relative to flows — [MH 2023](https://www.minneapolisfed.org/article/2023/are-job-vacancies-still-as-plentiful-as-they-appear-implications-for-the-soft-landing). In contrast, Bhuller et al. find that cheaper online recruiting reduced failed hiring attempts in Norway — [NBER w30911](https://www.nber.org/papers/w30911)

### Inferences
Each motive maps onto observable signals:
- **Pipeline or option value:** evergreen postings with unchanged content (F3), high applicant inflow without hiring (F9), specialist roles (F11).
- **Information gathering:** many concurrent similar postings relative to headcount (F4).
- **Signalling growth:** posting surges not matched by headcount growth, possibly around funding or earnings events (F4, F12).
- **Internal-candidate formality:** short or unusual posting windows and public-sector style. German formal requirements (public-sector advertising duties; works-council rights to demand internal postings) are a labour-law topic for other researchers and were not researched here.
- **Agency pools:** temporary-agency employer type (F7) and pool wording (F8).
- **Phantoms:** origin removal lag (F2) and relative age (F1).

Two cautions follow from the theory:
- Relisting can be a signal of genuineness (ADV).
- German firms commonly re-advertise after a temporary abandonment (IAB 2013).

So reposting must be combined with content-change and presence-pattern evidence before it counts toward a ghost score.

### Gaps
- I found no German academic or IAB study quantifying deliberate ghost or pipeline postings by private employers. The only German official evidence concerns temporary agencies in the BA register.
- I did not read Chen & Li (2023) on vacancy duration and firm profitability (the signalling channel) or the WSJ 2013 piece; both are known only through Ng.
- No study tests the signalling motive (posting to impress investors or employees) causally.
