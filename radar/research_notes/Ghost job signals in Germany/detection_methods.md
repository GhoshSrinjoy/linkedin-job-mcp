# Ghost-job detection methods for scraped job-posting data (German pipeline): deduplication, lifetimes, classification, labels

*Compiled 2026-10-24. Scope: methods, algorithms, data processing and labelling only; economics, surveys, consumer tools, law and data access are covered by other notes. Dates in parentheses are the publication or version dates of the cited source. "Inference" bullets are my own reasoning, not source claims. The WebSearch budget ran out near the end of the research. Items that could only be confirmed from search snippets are marked "[snippet-level]".*

---

## 1. How do the major OJA producers deduplicate across portals and measure posting lifetimes (first-seen/last-seen, removal, reposts)?

### Takeaway
Every producer deduplicates in layers. First comes an exact or URL/ID pass. Then comes a fuzzy text or normalised-field pass inside a time window, sometimes followed by a pass over structured, classified fields. Thresholds are almost never published. Lifetimes are nearly always crawl-based: first-seen to last-seen, sometimes overridden by a stated publication or expiry date. Vendors also impose caps: Lightcast expires every ad after at most 120 days, and LinkUp-based research drops ads live longer than 180 days. These caps censor exactly the long-lived tail that a ghost-job detector needs. A German pipeline should therefore run its own uncapped, per-source spell tracking and use vendor duration fields only as cross-checks.

### Cited Findings

#### Eurostat Web Intelligence Hub (WIH) OJA (reference metadata PDF generated 2025-05-16; data from 1 Jan 2019)
- Dedup runs in three stages across the pipeline:
  - **Physical**, at ingestion: postings "coming from the same URL" (or with the same unique vacancy id) are duplicates and are not passed on.
  - **Semantic**, in pre-processing: fuzzy matching on the description, under which an OJA is a duplicate if "the description (and the job location) is the same (or very similar)" to an ad already in the database. Metadata matching (reference id, page URL) removes copies on aggregators.
  - **Logical**, after information extraction: ads with the same publication date, occupation, place, skills and industry are merged, even if they come from different sources or are phrased differently. — [Eurostat WIH-OJA reference metadata](https://ec.europa.eu/eurostat/cache/metadata/Annexes/isoc_sk_oja_esmsip2_an_1.pdf)
- Lifetime variables:
  - `first_active_date` is the publication date if one is extracted from the ad, otherwise the date the ad was first detected.
  - `last_active_date` is the date the posting "is not found in any of the sources", or the expiration date "if mentioned in the advertisement". — [Eurostat WIH-OJA metadata](https://ec.europa.eu/eurostat/cache/metadata/Annexes/isoc_sk_oja_esmsip2_an_1.pdf)
- Documented pitfalls:
  - Regex-based date detection can fail.
  - Language-detection errors propagate downstream.
  - Two language-dependent noise filters can misfire: a "No Vacancy Filter" and a "Spam Filter" for non-job content such as training courses.
  - Portals that go down or block crawlers cause unit non-response, which "may happen frequently in a usually small number of sources".
  - Classifiers trained on older ads drift as employer terminology changes. — [Eurostat WIH-OJA metadata](https://ec.europa.eu/eurostat/cache/metadata/Annexes/isoc_sk_oja_esmsip2_an_1.pdf)
- Scale (2022): 413 websites, 65 million ads per year, and a direct running cost of 600 person-days per year (2.7 FTE). — [Eurostat WIH-OJA metadata](https://ec.europa.eu/eurostat/cache/metadata/Annexes/isoc_sk_oja_esmsip2_an_1.pdf)
- Eurostat's own caveat: "A job advertisement might not necessarily correspond to a vacant post and the company's intent to hire remains uncertain"; one OJA may also cover several vacancies. — [Eurostat WIH-OJA metadata](https://ec.europa.eu/eurostat/cache/metadata/Annexes/isoc_sk_oja_esmsip2_an_1.pdf)
- The public WIH page says duplicates are identified from description, location and metadata, then flagged and merged across portals. Data reaches statisticians quarterly through the WIH DataLab. Portals were chosen in landscaping exercises (Cedefop 2017, Eurostat 2021). — [WIH OJA page](https://cros.ec.europa.eu/wih/oja)

#### Eurostat deduplication challenge (Dec 2022 – Apr 2023): the de facto public benchmark
- Data: about 112,000 anonymised OJAs from about 400 websites, including LinkedIn and Xing, in about 24 languages (English, German, French, Dutch, Spanish and Italian dominate).
  - Fields: title, description, location and company (both auto-extracted from the text), country id, retrieval date.
  - Company is missing in about 25% of records and location in about 50%. — [Insee webinar slides, May 2024](https://cros.ec.europa.eu/system/files/2024-05/Webinar%20Deduplication.pdf); [Pasch et al., arXiv 2406.13695, Jun 2024](https://arxiv.org/abs/2406.13695)
- Duplicate typology:
  - **full**: same title and description;
  - **semantic**: same position and characteristics, worded differently or in another language;
  - **temporal**: semantic duplicates with different retrieval dates, which is effectively the repost case;
  - **partial**: same position "but do not necessarily contain the same characteristics". — [Dim10p/deduplication-challenge README](https://github.com/Dim10p/deduplication-challenge); [Insee slides](https://cros.ec.europa.eu/system/files/2024-05/Webinar%20Deduplication.pdf)
- The challenge was announced in December 2022 within the European Statistics Awards Web Intelligence competition and ended in April 2023. — [Eurostat news, 13 Dec 2022](https://ec.europa.eu/eurostat/en/web/products-eurostat-news/w/cn-20221213-1) [snippet-level]; [Insee slides](https://cros.ec.europa.eu/system/files/2024-05/Webinar%20Deduplication.pdf)
- Evaluation was by F1. There was no annotated test set and only a limited number of feedback submissions; 69 teams from 17 countries took part. — [Insee slides](https://cros.ec.europa.eu/system/files/2024-05/Webinar%20Deduplication.pdf); [Pasch et al. 2024](https://arxiv.org/abs/2406.13695)
- The OJA project has scraped and classified 200 million ads since July 2018. — [Insee slides](https://cros.ec.europa.eu/system/files/2024-05/Webinar%20Deduplication.pdf)

#### Cedefop (Skills-OVATE / OJA database)
- OVATE excludes portals without a stable data feed over time, its dashboards do not show every collected ad, and it is updated four times a year. — [Cedefop Skills-OVATE](https://www.cedefop.europa.eu/en/tools/skills-online-vacancies)
- In the Cedefop OJA database, as accessed for Eurostat's 2021 study, each ad carries `general_id`, `grab_date` ("First date of web-scrapping") and `expire_date` ("Last date of web-scrapping or expire date"). — [Beręsewicz & Pater, *Inferring job vacancies from OJAs*, Eurostat 2021](https://ec.europa.eu/eurostat/documents/3888793/12287170/KS-TC-20-008-EN-N.pdf/6a86d53e-d0b8-d608-988d-d91f0cef6c21?t=1611673495829)
- Cedefop, as quoted in that study, put the average vacancy duration in a preliminary experiment at "approximately one month (39.25 days)". It considers the expiry date necessary to build a flow measure. — [Beręsewicz & Pater 2021](https://ec.europa.eu/eurostat/documents/3888793/12287170/KS-TC-20-008-EN-N.pdf/6a86d53e-d0b8-d608-988d-d91f0cef6c21?t=1611673495829)
- Documented limitations:
  - Collection and expiry dates "are based on web-scraping not actual dates from the advertisements".
  - Duplicates may remain after processing.
  - "There are no job offers with the same general_id between different grab_date and expire_date periods", so the same ad cannot be tracked over time.
  - Cedefop dedups "based on comparison of specific fields".
  - Cedefop's online offers were 85% higher than the Eurostat job vacancy survey (JVS) stock. — [Beręsewicz & Pater 2021](https://ec.europa.eu/eurostat/documents/3888793/12287170/KS-TC-20-008-EN-N.pdf/6a86d53e-d0b8-d608-988d-d91f0cef6c21?t=1611673495829)
- Multi-vacancy ads are "expanded" in one of two ways: by selection (one job chosen) or by repetition (one record per job found in the ad). — [Beręsewicz & Pater 2021](https://ec.europa.eu/eurostat/documents/3888793/12287170/KS-TC-20-008-EN-N.pdf/6a86d53e-d0b8-d608-988d-d91f0cef6c21?t=1611673495829)

#### Lightcast (formerly Burning Glass)
- **Two-step dedup.**
  - Spiders skip ads already collected from a source.
  - Ads are then compared across sources on normalised job title, company and location over a 60-day window. The first one seen is the "original posting".
  - This removes "up to 80%" of collected postings.
  - Lightcast's own example: an ad reposted daily for a year would "in theory" be counted 6 times. — [Lightcast JPA methodology](https://kb.lightcast.io/en/articles/6957446-job-posting-analytics-jpa-methodology); [Lightcast: duplicate postings](https://kb.lightcast.io/en/articles/6957661-how-does-lightcast-handle-duplicate-postings)
- **Expiration.**
  - Fetch-based: a revisit that returns phrases like "Page not found" or "This job is no longer active" marks the ad expired.
  - Age-based: an ad expires after "no more than 120 days".
  - A posting seen on several sources expires only when all its ads have expired, still capped at 120 days. — [Lightcast JPA methodology](https://kb.lightcast.io/en/articles/6957446-job-posting-analytics-jpa-methodology)
- **Other processing.**
  - Sites are revisited for up to 14 days after the first scrape, and daily sites have a 36-hour lag.
  - Monthly curation removes about 1% of records (MLM, pay-to-work, spam).
  - Only the first city in an ad is kept.
  - Reclassification every 4 weeks rewrites history. — [Lightcast JPA methodology](https://kb.lightcast.io/en/articles/6957446-job-posting-analytics-jpa-methodology)
- **Duration metric.** Median duration is the median of closed postings, in days, and a posting counts once per month it is active. — [Lightcast API docs](https://docs.lightcast.dev/apis/job-postings). Lightcast presents median duration as a signal of hard-to-fill roles. — [Lightcast blog](https://lightcast.io/resources/blog/posting-duration-experience-level-and-more-8212-now-in-job-posting-analytics)
- **Revisions and drift.** One notice said US dedup improvements would cut posting counts by 2–4% over the prior three years. — [Lightcast status notice](https://status.lightcast.io/notices/itdahya6dam3fpwa-us-postings-implementing-deduplication-improvements). A research user notes that the share filtered out may be falling as more sites are scraped. — [DIGIT](https://digit-research.org/insights/using-job-vacancy-data-to-understand-evolving-demand-for-digital-skills/)
- The newer data-collection page (dated 2026-08-12) names no dedup fields or windows. — [Lightcast data collection & processing](https://kb.lightcast.io/en/articles/7124763-data-collection-and-processing-methodology)

#### Textkernel Jobfeed
- **Method** (undated blog):
  - Ads are split into word shingles (6-word shingles in the worked example). Each shingle is hashed to a 64-bit integer, and M min-wise permutations produce a sketch.
  - An Elasticsearch inverted index over the sketch integers retrieves candidates.
  - Pre-processing strips boilerplate, and a job-ad parser isolates the description and requirements, leaving out company descriptions that repeat across unrelated ads.
  - A classifier decides whether a candidate is the same job, using text overlap plus matches on organisation name, profession category and contact information.
  - There is no fixed threshold, because "true duplicates can have similarity as low as 37%" (179 of 484 shingles shared). — [Textkernel blog](https://www.textkernel.com/learn-support/blog/online-job-postings-have-many-duplicates-but-how-can-you-detect-them-if-they-are-not-exact-copies-of-each-other/)
- **Prevalence.** An average ad is reposted 2–5 times depending on country, so 50–80% of ads are duplicates. — [Textkernel blog](https://www.textkernel.com/learn-support/blog/online-job-postings-have-many-duplicates-but-how-can-you-detect-them-if-they-are-not-exact-copies-of-each-other/). Zhao et al. attribute the 50–80% figure to a 2016 study by V. Jijkoun. — [Zhao et al., ACM WI-IAT](https://doi.org/10.1145/3486622.3493928) [snippet-level]
- **Germany, 2014.** Jobfeed counted 8,890,534 online job ads, which became 4,184,436 after dedup. Each offer appeared in 2.2 different sources on average. — [Crosswater Job Guide, 2015](https://crosswater-job-guide.com/archives/48931/)
- **Feed mechanics.**
  - Feeds can be delivered deduplicated or "including duplicate postings". Each posting has a Job ID.
  - Daily `jobs_new` files list vacancies "found as new on the day prior". Daily `jobs_expired` files list job IDs "marked as inactive on the day prior".
  - The monthly snapshot shows expiration state as of the 1st of the month. — [Textkernel Jobs Data Feeds docs](https://developer.textkernel.com/JobsDataFeed/master/)
- The Jobfeed search interface filters cross-platform duplicates and shows a note on likely duplicates. — [CareerBuilder DE: Textkernel Jobfeed](https://arbeitgeber.careerbuilder.de/textkernel-jobfeed)
- German research use: BIBB's GOJA dataset (EMNLP 2025) sampled 500 German ads from "Textkernel's Jobfeed corpus". — [Krüger et al. 2025](https://aclanthology.org/2025.emnlp-main.1375.pdf)

#### Index Research / index Anzeigendaten (Germany)
- **Collection** (page dated 6 Sep 2022):
  - Ads are captured "tagesaktuell" from about 500 online and print media, the BA job portal and more than 250,000 company websites, covering Germany plus 10 other European countries.
  - ML/AI is used, and quality control takes 1,000 work hours a month.
  - The page cites "mehr als 38 Millionen Stellenangebote" analysed per year and a 2019 German market volume of over 17.4 million offers.
  - Dedup appears only as a goal of avoiding redundancy. No procedure is described. — [index Anzeigendaten: Datenbank für Stellenanzeigen](https://anzeigendaten.index.de/mag/datenbank-stellenanzeigen/)
- Annual volume figures differ between index pages; the FAQ cites "über 62 Millionen Stellenanzeigen im Jahr". — [index FAQ](https://anzeigendaten.index.de/faq/) [snippet-level]
- The product has been renamed index Salesdriver. — [index press release](https://index.de/pressemitteilungen/index-anzeigendaten-wird-zu-index-salesdriver). Index Research calls its database "Europas umfangsreichste strukturierte Datenbank mit Stellenanzeigen". — [index Research](https://research.index.de/)

#### LinkUp
- LinkUp indexes openings daily, directly from employer career sites, and has done so since 2007. It excludes job boards, staffing firms and aggregators because of sponsored, syndicated, duplicate and expired listings. — [LinkUp blog, 9 Apr 2023](https://www.linkup.com/insights/blog/the-absurd-myth-of-ghost-jobs); [LinkUp closed-duration use case](https://www.linkup.com/use-cases/closed-duration-of-full-stack-jobs)
- **Definitions.** Closed duration is the number of days a job was posted before removal from the employer site; LinkUp assumes such jobs were usually filled, but "removal doesn't always mean a hire". Open duration is the age of postings still active. — [LinkUp use case](https://www.linkup.com/use-cases/closed-duration-of-full-stack-jobs); [LinkUp blog](https://www.linkup.com/insights/blog/the-absurd-myth-of-ghost-jobs)
- **US figures, March 2023:**
  - Average closed duration was 45.6 days.
  - Of 2.14M unique removed jobs, 58% were removed within 30 days, 35% after 1–6 months and 7% after more than 6 months.
  - 18% of active openings, about 950k of 5.4M, were at least 6 months old, against a pre-pandemic norm of 20%.
  - 25% of "evergreen" jobs (about 240k) had been posted for at least 24 months, and 77% of those were in retail or accommodation and food. — [LinkUp blog](https://www.linkup.com/insights/blog/the-absurd-myth-of-ghost-jobs)
- Later readings: closed duration was 47 days in March 2025 (43 in February) and 51 days in June 2024. — [LinkUp Mar 2025 recap](https://www.linkup.com/insights/blog/march-2025-jobs-recap); [Jun 2024 recap](https://www.linkup.com/insights/blog/june-2024-jobs-recap-labor-market-analysis)
- LinkUp's CEO argues ghost jobs are largely a myth and treats evergreen postings as real openings for high-turnover roles. — [LinkUp blog](https://www.linkup.com/insights/blog/the-absurd-myth-of-ghost-jobs)

#### Revelio Labs
- COSMOS is the unified postings dataset, "standardized and deduplicated across our different postings sources". Fields include:
  - `Source_*` booleans for each source (company websites, LinkedIn, Indeed and so on);
  - `Post_date`, and `Remove_date` ("If null, it hasn't been removed yet");
  - `Filling_time_avg`, defined as remove date minus post date, in months;
  - `Removed_posting`, a monthly count;
  - `Expected_hires`, per posting. — [Revelio data dictionary](https://www.data-dictionary.reveliolabs.com/data.html)
- Near-duplicates are collapsed into a single posting because one opening appears across many channels. — [Revelio AI Labor Market Tracker appendix, Sep 2026](https://www.reveliolabs.com/ai-labor-market-tracker/us/september-2026/appendix)
- In the ghost-job analysis (31 Oct 2023, updated 18 Jun 2026), postings were matched to new positions starting within 6 months on company, role, seniority and state. Hires per posting fell from 0.75 (2018) to below 0.5 (2023). — [Revelio: ghost job postings](https://www.reveliolabs.com/news/macro/ghost-job-postings)

#### Indeed Hiring Lab
- **Counting rules** (undated FAQ):
  - Indeed dedups "so that when the same job is collected from multiple sources we only show it once", which is aimed at the job-seeker experience.
  - Stock is daily visible postings averaged over a week or month. Flow counts a posting "only when they are first visible".
  - Postings "do not reflect a precise number of available jobs", "may remain online for a period of time after being filled", and one posting may cover more than one opening. — [Indeed data FAQ](https://hiringlab.indeed.com/indeed-data-faq-2/)
- The Job Postings Index is the percentage change in seasonally adjusted postings since 1 Feb 2020, as a 7-day trailing average. Daily seasonal adjustment uses a Bundesbank method adopted in November 2024. There is a German folder with `regional_de.csv`, licensed CC BY 4.0. — [hiring-lab/job_postings_tracker](https://github.com/hiring-lab/job_postings_tracker)
- A third-party explainer says Indeed matches duplicates on location plus job title and merges similar titles at the same company across nearby locations; this describes search display, not necessarily the index. — [RecruitingDaily](https://recruitingdaily.com/did-indeed-hide-your-job-postings-deduplication-explained/)

#### German official-statistics practice (context for a DE pipeline)
- Destatis (WISTA 5/2018, M. Rengers) observes:
  - Duplicates arise both across portals and when the same portal is scraped repeatedly.
  - Heuristic: deduplicate the stock at a point in time, then add only unique flows. Re-request each ad URL at regular intervals to check whether it is still online.
  - Cross-portal dedup has "weniger gut[e]" prospects, so the advice is to avoid hybrid portals, or use only their own ads, or audit their internal dedup.
  - Germany had 1,563 job portals (12 Dec 2017). The BA portal is hybrid and held 470,374 ads on 26 Feb 2018.
  - One ad can contain several vacancies, for example for several locations. — [Destatis WISTA 5/2018](https://www.destatis.de/DE/Methoden/WISTA-Wirtschaft-und-Statistik/2018/05/internetgestuetzte-erfassung-052018.pdf?__blob=publicationFile)

### Inferences
- **Comparison of documented practice:**

| Producer | Dedup keys / method | Window / threshold | Lifetime fields | Removal detection | Key pitfalls for ghost detection |
|---|---|---|---|---|---|
| Eurostat WIH | URL/id → fuzzy description+location + ref-id/URL → identical classified fields | not published | first/last_active_date | not found in any source, or stated expiry | regex date errors; portal outages look like removals |
| Cedefop | field comparison | not published | grab_date / expire_date | scrape-based | same ad can't be tracked across periods (as of 2021) |
| Lightcast | normalised title+company+location | 60 days | (closed duration) | fetch phrases + 120-day cap | 120-day cap truncates the ghost tail; reposts after 60 days count as new ads |
| Textkernel | shingles+MinHash+inverted index → classifier (org, profession, contact) | no fixed threshold; true duplicates can be as low as 37% overlap | daily new/expired files | "marked as inactive" (rule undocumented) | thresholds and accuracy unpublished |
| index | undocumented | – | – | – | no methodology published |
| LinkUp | career sites only (no aggregators) | – | open/closed duration | removal from career site | treats removal as fill; excludes staffing firms |
| Revelio | near-duplicate collapse across sources | not published | post/remove date | not published | removal ≠ hire |
| Indeed | same job from several sources shown once | not published | first visible / daily visible | not published | dedup tuned for display, not statistics |

- A ghost-job pipeline needs repost-preserving dedup. Lightcast's 60-day rule and the WIH logical merge collapse or split reposts in ways that hide refresh behaviour. The data model should keep three levels: raw sighting (source, URL, fetch time, HTML hash); posting instance (one URL or ID lifetime per source); and job-identity cluster (cross-source, cross-time). Repost counts, gaps and refresh cadence are features of the cluster.
- Measure lifetimes per source and per cluster without caps. Never inherit a vendor's 120-day or 180-day truncation. Keep the stated publication date (as WIH does) separately from first-seen, because a date reset with unchanged content is itself a refresh signal.
- Removal detection needs Lightcast-style fetch confirmation (HTTP 404/410, "no longer available" phrases, redirects to search pages) and a rule requiring at least two consecutive misses. This guards against the WIH-documented portal non-response that would otherwise generate false "removals" and false reposts.
- Germany-specific: the Destatis advice to avoid hybrid portals, or keep only their native ads, applies to the BA Jobbörse, which is hybrid. Since index already crawls more than 250k company sites, a LinkUp-style career-site crawl of German employers is the cleanest substrate for removal and repost measurement. Boards and aggregators can then be linked in as additional sightings.

### Gaps
- Cedefop's current dedup rules and thresholds, and whether it has adopted the WIH three-stage pipeline, were not found beyond the 2021 "comparison of specific fields" description.
- Textkernel publishes no production parameters (shingle size, M, classifier type, precision/recall) and no rule for "marked as inactive". I could not confirm IAB or Bertelsmann Stiftung use of Jobfeed: IAB DP 15/2024 (Peede & Stops) uses BA-JOBBÖRSE data, not Jobfeed ([IAB DP 15/2024](https://doku.iab.de/discussionpapers/2024/dp1524.pdf)).
- index Research publishes no dedup, lifetime or repost methodology.
- Revelio's matching logic and removal-detection rule are unpublished. A LinkUp field-level data dictionary (e.g., delete-date semantics) was not retrieved.
- Indeed documents no repost rule and does not say whether the index is built on deduplicated counts.
- The similarity measure and threshold behind WIH "fuzzy matching" are not published.

---

## 2. What academic and engineering work exists on detecting near-duplicate and reposted job ads?

### Takeaway
Public evidence comes from five places: the Eurostat challenge (Insee, and Pasch et al.), a German/English production system (Engelbach et al., Fraunhofer IAO, 2024), Textkernel's MinHash description, a 2021/22 ACM comparison of 24 methods, and practitioner MinHash notes. Four findings recur:
1. Whole-text similarity, whether character overlap, TF-IDF or embeddings, cannot separate true duplicates from same-employer boilerplate or sibling requisitions. Comparing the skill and requirement content is what discriminates.
2. MinHash/LSH is the scalable candidate generator, but it does not match across languages.
3. Multilingual embeddings underperform translate-then-English-embed (F1 0.60 vs 0.82) unless domain rules are added (F1 0.89).
4. Thresholds are dataset-specific and set by manual review of stratified pairs.

### Cited Findings

#### Shingling + MinHash/LSH
- **Textkernel:** word shingles, 64-bit hashes, M min-wise permutations, and an inverted index for candidates. A learned classifier then makes the decision instead of a threshold, since true duplicates can share as little as 37% of shingles. — [Textkernel blog](https://www.textkernel.com/learn-support/blog/online-job-postings-have-many-duplicates-but-how-can-you-detect-them-if-they-are-not-exact-copies-of-each-other/)
- **Insee webinar** (May 2024), presenting the methods of two challenge teams: Spub.Fr (Insee/Dares, 5th on accuracy) and Nins (4th on accuracy, 2nd for reproducibility):
  - Language detection with fastText.
  - Multilingual NER (`Davlan/distilbert-base-multilingual-cased-ner-hrl`) to pull out ORG and LOC.
  - Removal of the most frequent words per language, and special handling of generic per-company descriptions.
  - Exact matches on field subsets: title+description; title+company+location; and company+location+retrieval date for international companies, which "catches many multilingual duplicates".
  - Jaccard and Jaro-Winkler similarity, then MinHash on **4-character shingles** (datasketch) inside the Record Linkage Toolkit.
  - Blocking by detected language and by description-length bands ]0,700], [400,1300], [1000,2000], [1700,3000], [2600,∞[, because unblocked pairs would exceed 12 billion.
  - The team found 3,198 records that were portal boilerplate, such as cookie banners. — [Insee webinar slides, May 2024](https://cros.ec.europa.eu/system/files/2024-05/Webinar%20Deduplication.pdf)
- **Practitioner notes** (Adzuna, about 400k ads; May 2020):
  - Use MinHash LSH. A longer shingle ("a bigger number like 7" words) reduces false positives.
  - TF-IDF weighting gave no real advantage and needs the whole corpus, which makes online use hard.
  - Tune LSH bands and rows by manually reviewing pairs sampled across Jaccard strata. Verify candidates with edit distance, then group with connected components (safe only at high thresholds).
  - Pitfalls: company template boilerplate, and ads that are about 90% identical but adapted for a different location or seniority. — [Skeptric](https://skeptric.com/near-duplicate-review)

#### SimHash
- Manku, Jain & Das Sarma (WWW 2007) used 64-bit simhash fingerprints on 8 billion web pages and called two pages near-duplicates when the fingerprints differ in at most k=3 bits; "both precision and recall are near 0.75" at k=3. — [Manku et al. 2007 (PDF)](https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/33026.pdf); [Google Research page](https://research.google/pubs/detecting-near-duplicates-for-web-crawling/)
- I found no job-ad-specific SimHash evaluation (see Gaps).

#### TF-IDF cosine and overlap measures
- An ACM WI-IAT paper by Zhao et al. compared 24 method combinations. The top two were overlap with skip-grams (OS) and overlap with n-grams (OG), followed by TF-IDF cosine with n-grams (TCG) and with skip-grams (TCS); all four beat the baseline. — [Zhao et al., DOI 10.1145/3486622.3493928](https://doi.org/10.1145/3486622.3493928) [snippet-level; full text blocked]
- Engelbach et al. rejected Levenshtein, TF-IDF and longest-common-subsequence methods because job listings "contain many similar-looking text blocks on a word and character basis, but are often very different in terms of meaning". — [Engelbach et al. 2024](https://arxiv.org/abs/2406.06257)

#### Sentence embeddings
- **Pasch, Petridis & Cutura (Jun 2024)**, Eurostat challenge, 2nd on accuracy and 1st on reproducibility:
  - Light cleaning cut 112k ads to about 61,500 unique texts. Rules alone found 99% of full duplicates.
  - Candidates came from FAISS k-nearest-neighbours with k=100, accepted at L2 distance ≤ 0.25 (thresholds 0.1–0.45 were tested). That cut-off keeps the top 6% of pairs, about 397k.
  - F1 by duplicate type:

    | Approach | Full | Semantic | Temporal |
    |---|---|---|---|
    | Multilingual `distiluse` | 0.99 | 0.60 | 0.57 |
    | Translate (Google) + `all-mpnet-base-v2` | 0.99 | 0.82 | 0.67 |
    | Translate + mpnet + expert rules | 0.99 | 0.89 | 0.92 |

  - The expert rules used "varying thresholds depending on whether company name, language of the text, and job location were identical".
  - Runtime was about 9 hours versus 1 hour (8 hours of it translation).
  - mpnet's 384-token limit truncated 43% of ads, with a median loss of 400 tokens.
  - The multilingual model falsely matched different Lithuanian job titles. — [Pasch et al. 2024](https://arxiv.org/abs/2406.13695)
- **Insee:** transformer embeddings with a cosine threshold "ex: 0.99" gave high recall but poor precision. The team restricted embedding comparisons to international companies to limit the n² cost. — [Insee slides](https://cros.ec.europa.eu/system/files/2024-05/Webinar%20Deduplication.pdf)

#### Entity matching + hybrid scoring: the German/English production case
- **Engelbach, Klau, Kintz & Ulrich (Fraunhofer IAO / Univ. Stuttgart / Contractor Consulting, Munich; LKE 2024).**
- Data and setup:
  - About 45,000 freelance IT project postings in German and English.
  - A skill list of the 25,000 most frequent skills (each seen at least 7 times in resumes), plus a skill blacklist.
  - Validation set: 74 duplicate and 73 look-alike non-duplicate pairs (29 of 176 annotated pairs could not be decided even by experts). Test set: 50 duplicate pairs.
  - Candidates were limited to a publication-date window of "a few weeks".
- Scores compared:
  - Text Overlap Score: shared blocks of at least 15 characters, normalised by text length and averaged in both directions.
  - Skill Overlap Score.
  - Embedding cosine from `distiluse-base-multilingual-cased-v1` on text, skills, title and everything combined.
  - Weighted Skill Score, with inverse-frequency skill weights w = 1/f.
- Validation results:

  | Score | Threshold | P | R | F1 |
  |---|---|---|---|---|
  | Text overlap | 0.40 | 0.48 | 0.66 | 0.55 |
  | Skill overlap | 0.40 | 0.89 | 0.66 | 0.76 |
  | Text embedding | 0.50 | 0.52 | 0.81 | 0.63 |
  | Skill embedding | 0.50 | 0.66 | 0.97 | 0.79 |
  | Title embedding | 0.50 | 0.49 | 0.74 | 0.59 |
  | Weighted skill | 0.20 | 0.84 | 0.97 | 0.90 |
  | **Total** = mean(skill overlap, skill embedding, weighted skill) | 0.35 | 0.89 | 0.99 | **0.94** |

- Production settings: total score ≥ 0.6 and every component ≥ 0.1. In the first six months, 58,860 postings were analysed, 24,995 were flagged as duplicates (about 2.5 duplicates per unique job), and 43,705 unique postings remained.
- Findings: titles alone mislead ("SAP developer wanted"). Embeddings "seem not to be capable of separating fake duplicates from real ones" because of shared boilerplate. Hard cases include the same company and project with front-end vs back-end roles, or onsite vs remote. — [Engelbach et al., arXiv 2406.06257](https://arxiv.org/abs/2406.06257)

#### Duplicate typology and transitivity
- Insee found that making semantic-duplicate clusters transitive (connected components turned into cliques) improved results, while doing the same for partial duplicates reduced precision. Their conclusion: transitivity pays only "when the precision is high and the recall improvable". — [Insee slides](https://cros.ec.europa.eu/system/files/2024-05/Webinar%20Deduplication.pdf)
- In the challenge, "temporal duplicates" (same content, different retrieval dates) are the closest formal analogue of reposts. — [Dim10p README](https://github.com/Dim10p/deduplication-challenge)

#### Repost mechanics on platforms (evidence for repost features)
- On LinkedIn, reposting a closed job creates a new job: prior applicants "won't be included in your new posting". — [LinkedIn Help: Repost a closed or expired job](https://www.linkedin.com/help/learning/answer/a522249) [snippet-level]
- Job boards favour fresh job IDs, which gives employers an incentive to repost evergreen roles under new IDs. — [ExactHire](https://www.exacthire.com/?p=16599) [snippet-level]

### Inferences
- **Threshold reference** (all dataset-specific; recalibrate on German data):

| Method | What it computes | Inputs | Published operating point | Pitfalls | DE suitability |
|---|---|---|---|---|---|
| MinHash/LSH, char 4-grams | estimated Jaccard of shingle sets | normalised text | Insee: 4-char shingles, blocked by language and length band | no cross-lingual matches; boilerplate inflates scores | char n-grams are robust to German compounding and inflection; good first pass |
| MinHash/LSH, word shingles | same, on word n-grams | tokenised text | Textkernel 6-grams (true duplicates ≥37%); practitioner advice ~7 | template boilerplate | strip boilerplate first |
| SimHash 64-bit | Hamming distance of fingerprints | token features | k ≤ 3 bits on web pages (P≈R≈0.75) | coarse for long, template-heavy ads | cheap exact/near-exact refresh detection |
| TF-IDF cosine | weighted term overlap | corpus vocabulary | ranked below overlap measures in Zhao et al. | needs global IDF; poor online | weak |
| Sentence embeddings | semantic cosine/L2 | text ≤ model max tokens | L2 ≤ 0.25 with mpnet (≈ cosine 0.97 if vectors are unit-normalised); cosine 0.99 for "candidates" | truncation (43% of ads at 384 tokens); same-company false positives | needed for DE↔EN matches; chunk long ads |
| Skill-weighted overlap | inverse-frequency-weighted shared skills | skill extraction + lexicon | threshold 0.20 → F1 0.90; combined total ≥ 0.6 in production | lexicon upkeep; drift | best evidence for DE/EN (Engelbach) |
| Entity rules | exact or Jaro-Winkler matches on company, location, language, date gap | extracted entities | thresholds vary by match pattern (Pasch) | missing company in ~25% and location in ~50% (challenge data) | essential; normalise legal forms (GmbH, AG, SE) and locations (PLZ, Kreis) |

- **Recommended DE pipeline:**
  1. Strip boilerplate (cookie banners, portal navigation, repeated employer "Über uns" blocks), using per-employer frequent-block removal.
  2. Exact hash of normalised text.
  3. MinHash/LSH on char 4-grams, blocked by employer, language and length band.
  4. For cross-language pairs, multilingual or translated embeddings blocked by employer.
  5. A pairwise classifier over overlap of the requirements section, weighted skill overlap, title similarity after gender-tag normalisation, location distance, date gap, source pair and reference-ID equality.
  6. Clustering that applies transitivity only to high-precision edges.
- **Cosmetic repost vs genuinely new requisition** (decision features, derived from the cited evidence):
  - Signals of a *cosmetic repost*: same employer and normalised title and location; requirements or skill overlap near 1 (or the same text hash); the previous instance disappeared shortly before; a new posting ID or reset date; recurring cadence (e.g., every 30 days, matching typical portal publishing periods).
  - Signals of a *new requisition*: a different employer reference or requisition ID in the URL or text; a changed skill set, seniority, contract type or location (Engelbach's front-end/back-end and onsite/remote cases; Skeptric's 90%-identical location variants); a long gap after a confirmed close; several concurrent sibling postings.
  - Unresolvable cases, which even Engelbach's experts could not decide in 29 of 176 pairs, should be a separate "uncertain" class, not forced into either label.
- Because a repost is the core ghost signal, dedup must never delete the earlier instances. It should link them, so that repost count, cumulative lifetime and cadence can be computed per cluster.

### Gaps
- No public, job-ad-specific SimHash evaluation was found. No public German job-ad duplicate benchmark exists either: Engelbach's data is proprietary, and the Eurostat challenge data includes German but its labels are not public.
- The full Zhao et al. results (precision/recall per method) and the winning challenge team's method and score were not retrieved.
- I found no study that labels "cosmetic repost vs new requisition" directly; the decision rules above are inferred.

---

## 3. The EMU thesis in full; other ghost-job ML/NLP work; what transfers from fake-job-ad research

### Takeaway
Only two ghost-job-specific academic studies exist, and neither has verified ground truth:
- **Mathison (EMU honors thesis, approved Dec 2025):** 849 LinkedIn postings. Labels are the top 20% of a hand-weighted heuristic score, and a BERT model then learns to reproduce those labels, so the reported metrics measure agreement with the heuristic, not ghost detection.
- **Ng (arXiv, Oct 2024):** 269k Glassdoor interview reviews, labelled by GPT-4o (2,000 reviews) and then BERT, with no reported validation of the LLM labels.

The fraud literature (EMSCAD) offers useful completeness and transparency features, but scams differ from ghost postings: ghost postings come from legitimate employers through legitimate ATS channels. Scam cues such as fees or off-platform contact should therefore drive a separate filter, not the ghost score. Mathison's own showcased "ghost" examples turned out to be scams, which illustrates the confusion.

### Cited Findings

#### Mathison, C. (2025), "Classification of ghost job listings: A two step BERT approach", EMU Senior Honors Thesis no. 881 (Economics; approved Ypsilanti, December 2025; advisors J. Putz, A. Stype, B. Patrick)
- **Data.**
  - Built with a custom Python scraper that called LinkedIn's guest jobs API and paged through results with waits and retries. The scraper was "frequently blocked", sometimes for "multiple days". The author applied for official API access and received no reply.
  - 849 postings dated 2024-02-20 to 2025-02-26, mostly from 2025, from 567 unique companies, focused on San Francisco and New York City.
  - 261 postings listed salary, so salary was reduced to a binary flag.
  - Seniority: Entry 375, Mid-Senior 266, N/A 109, Internship 36, Associate 30, Director 24.
  - Employment type: Full-time 771, Contract 28, Part-time 22, Internship 20.
  - Job function: 42% Engineering & IT. Industry: Software Development 21%, Technology/Internet 13%, IT Services 12%.
  - The summary table, garbled in text extraction, appears to list 82 locations (unconfirmed). — [Mathison 2025, full text](https://commons.emich.edu/context/honors/article/1865/viewcontent/Mathison_Caleb_Honors_Senior_Project.pdf); [record](https://commons.emich.edu/honors/881)
- **Features.**
  - Description length (characters) and word count.
  - Posting age: days between the processing date and the posted date.
  - Company posting frequency: count of the company's postings in the sample. The author warns it "cannot be fully relied upon" without a full dataset.
  - Vagueness count and vagueness density (terms per 100 words), from a 4-category phrase list in Table 7. General terms include "team player", "fast-paced", "self-starter"; responsibilities include "various tasks", "other duties as assigned"; requirements include "relevant experience", "equivalent experience", "or similar"; and an "Additional" group includes "competitive", "exciting", "world-class", "passionate", "results-driven".
  - Has-salary (binary).
  - Missing values were mean-imputed, and features standardised to z-scores. — [Mathison 2025](https://commons.emich.edu/context/honors/article/1865/viewcontent/Mathison_Caleb_Honors_Senior_Project.pdf)
- **Rule-based score.** Ghost Job Score = 1.5·PostingAge − 1.5·DescriptionLength + 1.2·CompanyPostingFrequency − 1.2·WordCount + 1.0·VaguenessDensity − 1.0·HasSalary + 0.8·VaguenessCount.
  - The weights were "manually conceived based on prior literature and apparent firm incentives" (citing Ng 2024; Chen & Li 2023; Parker/Clarify Capital 2025).
  - Postings above the 80th percentile are labelled ghost, "in accordance with Ng (2024)", giving 170 ghost and 679 real.
  - Score distribution: mean −0.31, SD 4.0, range −22.9 to 13.1. Ghost-class mean 5.41; real-class mean −1.74. — [Mathison 2025](https://commons.emich.edu/context/honors/article/1865/viewcontent/Mathison_Caleb_Honors_Senior_Project.pdf)
- **BERT stage.**
  - A "tuned BERT model" (checkpoint not named) is trained on the score-derived labels. Inputs are the description and text features "as well as the numerical salary and posted date".
  - Training used gradient accumulation and cross-validation and optimised F1. Epochs and hyperparameters are not reported. — [Mathison 2025](https://commons.emich.edu/context/honors/article/1865/viewcontent/Mathison_Caleb_Honors_Senior_Project.pdf)
- **Results** on a held-out set of N=170 (136 real, 34 ghost), with the decision threshold optimised at 0.5338:

  | Class | Precision | Recall | F1 |
  |---|---|---|---|
  | Real | 0.91 | 0.85 | 0.88 |
  | Ghost | 0.52 | 0.65 | 0.58 |
  | Macro average | | | 0.73 |
  | Weighted average | | | 0.82 |

  ROC AUC was 0.78. Accuracy is not stated. — [Mathison 2025](https://commons.emich.edu/context/honors/article/1865/viewcontent/Mathison_Caleb_Honors_Senior_Project.pdf)
- **Showcased examples.**
  - "Entry Level Python Dev": score 8.2, 220 words, 161 days open, 45 other postings. A forum describes it as an ad for a $20k software course.
  - "Founding Software Engineer": score 7.8, open 374 days.
  - "Home-Based Scheduling Assistant": score 5.1, open 3 days. A forum reports a required $100 monthly subscription. — [Mathison 2025](https://commons.emich.edu/context/honors/article/1865/viewcontent/Mathison_Caleb_Honors_Senior_Project.pdf)
- **Stated limitation:** ghost status is unconfirmed, and "Future research in this topic would necessitate having a dataset of confirmed ghost job listings". — [Mathison 2025](https://commons.emich.edu/context/honors/article/1865/viewcontent/Mathison_Caleb_Honors_Senior_Project.pdf)

#### Ng, H. (2024), "Why is it so hard to find a job now? Enter Ghost Jobs", arXiv 2410.21771 (29 Oct 2024)
- **Definition.** A ghost job has no "immediate or reasonably foreseeable immediate vacancy". This explicitly includes pipeline postings for specialised roles and excludes slow hiring caused by stringent checks.
- Ng argues that postings open more than 30 days, or posted continuously, "cannot robustly be categorized as ghost jobs", because firms can claim difficulty finding candidates. — [Ng 2024](https://arxiv.org/abs/2410.21771)
- **Data.** Glassdoor interview reviews from the first 1,203 companies by relevance, 29,294 pages scraped in July 2024. Language detection kept 269,347 English reviews across 97 industries. — [Ng 2024](https://arxiv.org/abs/2410.21771)
- **Labels.**
  - A keyword baseline matched 3,624 reviews. The table says 1.3% and the text says 1.6%, an internal inconsistency. "ghosted" alone accounted for 3,169 of the matches.
  - GPT-4o labelled 2,000 random reviews with the prompt "If you are 90% sure the interview review indicates a ghost job, say yes; otherwise, say no".
  - BERT was trained on those labels (3 epochs, batch 16, 500 warm-up steps, weight decay 0.01) and flagged 56,559 reviews (21%).
  - I found no reported agreement between the LLM labels and humans, and no held-out accuracy, in the paper text. — [Ng 2024](https://arxiv.org/abs/2410.21771)
- **Correlates.** Ghost-review shares peak at mid-to-large firms: 1,001–5,000 employees under BERT and 5,001–10,000 under keywords. Ng also notes possible upward bias (some cases were simply better candidates being hired) and downward bias (non-reporting). — [Ng 2024](https://arxiv.org/abs/2410.21771)

#### Other ghost-specific code and data
- GitHub `GarimaDixit2502/ghost-job-detector` (28 commits): scraping, VADER plus a "candidate frustration lexicon", a BERT classifier, and a 0–100 "transparency score". The labelling method and metrics are not published, and the forum-review component is a stub. — [repo](https://github.com/GarimaDixit2502/ghost-job-detector)
- Other GitHub hits are fake-job (fraud) classifiers trained on the Kaggle EMSCAD data. — [Sanjeevs239/fake-job-detection-ml](https://github.com/Sanjeevs239/fake-job-detection-ml); [Prince-SinghDS](https://github.com/Prince-SinghDS/Fake-Job-Detection-NLP)

#### Fraud / fake-ad literature (EMSCAD; Vidros et al. 2017)
- Vidros, Kolias, Kambourakis & Akoglu, "Automatic Detection of Online Recruitment Frauds: Characteristics, Methods, and a Public Dataset", *Future Internet* 9(1):6, published 3 Mar 2017. It releases 17,880 annotated job ads "retrieved from the use of a real-life system". — [Crossref record / DOI](https://doi.org/10.3390/fi9010006)
- 17,014 ads are real and 866 fraudulent. The fields include binary `telecommuting`, `has_company_logo`, `has_questions`; categorical employment type, required experience, required education, industry, function, salary range and department; and free text for company profile, description, requirements and benefits. — [Kaggle mirror (Baselight)](https://baselight.app/u/kaggle/dataset/shivamb_real_or_fake_fake_jobposting_prediction); [TDS analysis](https://towardsdatascience.com/identifying-fraudulent-job-advertisements-using-r-programming-230daa20aec7/) [snippet-level]
- The original authors note that text- and metadata-based classification "can only provide a stepping stone" towards effective scam prediction. — [MDPI article](https://www.mdpi.com/1999-5903/9/1/6) [snippet-level; page blocked to fetch]
- Robustness: manipulating metadata features cut LightGBM fraud recall to 30.06% in one repo's adversarial test. — [Sanjeevs239 repo](https://github.com/Sanjeevs239/fake-job-detection-ml)
- Other work on the same data includes a BiLSTM compared against RF, LightGBM and GBM — [Pillai, arXiv 2304.02019](https://arxiv.org/pdf/2304.02019) — and a 2026 contrastive-loss approach — [arXiv 2609.21599](https://arxiv.org/pdf/2609.21599).

#### Producers' noise filters (related, non-ghost "problematic postings")
- Eurostat WIH runs a "No Vacancy Filter" and a "Spam Filter" (e.g., training courses). — [WIH metadata](https://ec.europa.eu/eurostat/cache/metadata/Annexes/isoc_sk_oja_esmsip2_an_1.pdf)
- Lightcast curation removes about 1% of records a month as MLM, pay-to-work or spam. — [Lightcast JPA](https://kb.lightcast.io/en/articles/6957446-job-posting-analytics-jpa-methodology)

### Inferences
- **Critical assessment of Mathison:**
  1. **Circular labels.** BERT is trained to imitate a hand-weighted score, so the best possible outcome is rediscovering the heuristic; it is not validation.
  2. **Leakage.** The posted date and salary feed both the label formula and the BERT inputs.
  3. **Weak lift.** On the test set, the majority-class baseline is 136/170 = 80% accuracy. The implied BERT accuracy, equal to the weighted-average recall, is (136·0.85 + 34·0.65)/170 ≈ 81%, so the model barely beats predicting "real" for everything. Ghost-class precision is 0.52.
  4. **Tiny sample.** 34 positives in test, from one US platform, two cities and mostly tech roles.
  5. **Ghost vs scam conflated.** Two of three showcased "ghost" postings are scams by the author's own account.
  6. **Fixed prevalence.** The 20% prevalence is imposed from Ng's review-based estimate, not estimated from data.
  - The reusable parts are the feature ideas: age, vagueness density, employer posting volume and salary transparency. The weights and metrics are not reusable.
- **Ng's labels** measure candidate experiences ("ghosted" by a recruiter), which conflate employer non-response with the absence of a vacancy. They are review-level, not posting-level, signals, and are useful at most as an employer-level prior.
- **Feature catalogue for a German ghost score** (inputs → computation; evidence; pitfalls; DE fit):

| Feature | Computes | Inputs | Evidence / threshold | Pitfalls | DE fit |
|---|---|---|---|---|---|
| Excess lifetime | observed age ÷ expected age for occupation×region×source (see §4) | spells, occupation code, region | BA flags occupations at +30% / +40% above the average vacancy duration (§4) | censoring; portal default lifetimes (often 30 days); evergreen high-turnover roles | high, with BA baselines |
| Repost count / cadence | number of re-appearances per cluster in 90/180 days; periodicity | cluster links, posting IDs, dates | LinkedIn reposts create new job IDs | staffing pools; legitimate multi-hire | high |
| Date-reset with unchanged text | stated date changes while text hash is constant | stated date, hash | WIH distinguishes publication date from first detection | portals that auto-refresh dates | high |
| Concurrent near-duplicates | sibling postings with the same title and employer across locations | clusters | Destatis/Indeed: one ad can cover several vacancies | true multi-vacancy hiring | medium |
| Employer posting intensity | postings ÷ employer size; churn of titles | employer registry (e.g., Handelsregister), counts | Mathison's frequency feature (sample-limited) | needs full coverage | medium |
| Salary transparency | salary present / range width | text extraction | Mathison weight −1.0; EMSCAD has a salary field | German pay transparency is uneven, so treat as a weak feature | medium |
| Vagueness density | vague phrases per 100 words | phrase lexicon | Mathison Table 7 (English) | needs a German lexicon ("abwechslungsreiche Tätigkeit", "dynamisches Team", "flache Hierarchien"…) that is validated, not assumed | medium |
| Specificity | requirement/skill entity count, start date, team/project detail | NER/skill extraction (GOJA-style) | Engelbach: skill content discriminates jobs | template ads | high |
| Pool-ad markers | "Initiativbewerbung", "Talentpool", "für zukünftige Positionen", staffing-agency signatures | text, employer type | BA excludes temp-agency postings from vacancy durations because of pooling (§4) | legitimate agencies | high (Germany-specific) |
| Scam markers (separate filter) | fees, upfront payment, off-platform contact, MLM | text, contact fields | WIH spam filter; Lightcast MLM/pay-to-work removal; EMSCAD | do not mix into the ghost score | needed as a pre-filter |

- **Fraud features that transfer** (as weak priors only): missing company profile or logo (employer opacity); missing salary; low specificity (few requirements, generic responsibilities); has_questions or screening questions (their absence may indicate a low-effort posting); and completeness of structured fields (contract type, experience, education).
- **Fraud features that should not transfer:**
  - Payment or fee requests, free-mail contact addresses, off-platform messaging and work-from-home-with-high-pay patterns are scam signatures. Ghost postings are typically polished ATS ads from real employers.
  - EMSCAD's 4.84% positive rate and accuracy-centred reporting mislead: the majority class alone scores about 95% accuracy.
  - EMSCAD is English, and its metadata features proved trivially gameable in the adversarial test.

### Gaps
- No Kaggle dataset or Hugging Face model labelled specifically for ghost jobs was found. The search budget ran out before Kaggle and Hugging Face could be checked exhaustively.
- Vidros et al.'s own classifier accuracies could not be verified because the MDPI page blocks automated fetching; secondary EMSCAD accuracy figures (around 97%) are not reported here as verified.
- No German-language ghost-job or fraud dataset was found.

---

## 4. Which modelling approaches fit posting-lifetime data?

### Takeaway
Treat each job-identity cluster as a survival spell and plan for four data problems:
- right-censoring: the posting is still live when the data ends;
- left-truncation: the posting was already live at the first crawl;
- interval-censoring: removal happens between two crawls;
- false removals: portal outages.

Model expected lifetime conditional on occupation, region, source and employer type, then score each posting by how far it exceeds that expectation and by its repost behaviour. Published distributions are strongly right-skewed and employer-driven: median around 23–37 days, 25% beyond 90 days, and a tail of postings live for years. Germany has a ready-made normalisation precedent in the BA's completed vacancy duration (*abgeschlossene Vakanzzeit*) by occupation and region. Employer-level ghost scores should be shrunk (empirical Bayes) and reported as coarse grades with uncertainty.

### Cited Findings

#### Observed duration distributions and conventions
- Hashizume (2024), as summarised in the NLx paper (Oct 2025):
  - Half of postings from Fortune 500 firms are up for 37 days or less.
  - 25% are up for more than 90 days and 10% for more than 180 days.
  - Twenty postings were live for the full 16 years of NLx data, and some call these "phantom" or "ghost" jobs.
  - Employer differences drive most of the variation in duration. — [Meisenbacher, Nestorov & Norlander, arXiv 2510.01470](https://arxiv.org/html/2510.01470v1)
- Other benchmarks summarised in the same paper:
  - Chen & Li (2023, LinkUp) dropped ads posted for more than 180 days and report a mean of 36.5 and a median of 23 days.
  - Austria: mean 30.5 days (Mueller et al. 2024).
  - UK: mean 17–18 days (Bassier, Manning & Petrongolo 2025).
  - US JOLTS 2001–2009 implies a mean vacancy length of 14–25 days (Davis, Faberman & Haltiwanger 2013).
  - Employers often start with 30-, 60- or 90-day windows and extend them, and several US states purge records after 30, 60 or 90 days. — [arXiv 2510.01470](https://arxiv.org/html/2510.01470v1)
- In NLx, a job is active in every month between `date_acquired` and `date_compiled`. More than half of the postings compiled in a typical month also appear in the prior month, and since 2021, 86% were acquired at most 2 months before compilation. — [arXiv 2510.01470](https://arxiv.org/html/2510.01470v1)
- Cedefop's average vacancy duration is about 39.25 days. — [Beręsewicz & Pater 2021](https://ec.europa.eu/eurostat/documents/3888793/12287170/KS-TC-20-008-EN-N.pdf/6a86d53e-d0b8-d608-988d-d91f0cef6c21?t=1611673495829). LinkUp's closed duration ranges from about 43 to 51 days (2024–25). — [LinkUp recaps](https://www.linkup.com/insights/blog/march-2025-jobs-recap)
- **Biases in using postings as stock** (Beręsewicz & Pater 2021):
  - Filled or withdrawn positions may stay online until automatic removal, "most commonly, websites offer 30 days of publishing a job ad". This is the "aggregate outflow bias" (Turrell et al. 2019).
  - Duration differs by occupation ("differential outflow bias").
  - Some sites keep ads for a fixed paid period, which blurs stock and flow.
  - Turrell et al. note that because paid ads cost the poster money, an ever-growing stock of filled vacancies is less of a concern. — [Beręsewicz & Pater 2021](https://ec.europa.eu/eurostat/documents/3888793/12287170/KS-TC-20-008-EN-N.pdf/6a86d53e-d0b8-d608-988d-d91f0cef6c21?t=1611673495829)
- Audoly, Bhuller & Reiremo (Norway; v3 May 2026) reportedly define vacancy duration as days between posted and unlisted dates, censored to 1–90 days. — [arXiv 2407.13204](https://arxiv.org/abs/2407.13204) [snippet-level; not in the abstract]

#### Normalising by occupation and region: the BA precedent
- **Definition** (BA method report, April 2020): "Die abgeschlossene Vakanzzeit misst die Zeit vom gewünschten Besetzungstermin bis zur Abmeldung einer gemeldeten Arbeitsstelle beim Arbeitgeberservice der BA (AG-S) in Tagen." In English: completed vacancy duration runs from the employer's desired fill date to the vacancy's deregistration, not from the posting date.
- The deregistration date is a proxy for the actual fill date, with a delay "deren Dauer nicht beziffert werden kann".
- A long duration need not mean a skills shortage, since job or firm characteristics matter, and only vacancies reported to the BA are covered.
- **Calculation rules:** only jobs subject to social insurance; only vacancies with a fill duration of at least 7 days; temp-agency (Arbeitnehmerüberlassung) jobs are excluded, partly because of agencies' pooling ("Poolbildung") and overstatement of actual demand.
- The figure is published "in tiefer berufsfachlicher und regionaler Gliederung". The method report charts critical limits at 30% and 40% above the all-occupation average. — [BA Methodenbericht Engpassanalyse, Apr 2020](https://statistik.arbeitsagentur.de/DE/Statischer-Content/Grundlagen/Methodik-Qualitaet/Methodenberichte/Uebergreifend/Generische-Publikationen/Methodenbericht-Engpassanalyse-Methodische-Weiterentwicklung.pdf)
- The current shortage analysis combines several indicators into a points score: 2.0 or more marks a bottleneck and below 1.5 none. — [BA Engpassanalyse page](https://statistik.arbeitsagentur.de/DE/Navigation/Statistiken/Interaktive-Statistiken/Fachkraeftebedarf/Engpassanalyse-Nav.html) [snippet-level]

#### Evergreen and auto-refreshed postings
- LinkUp, March 2023: 18% of active openings were at least 6 months old, and 25% of evergreen jobs had been posted for at least 24 months, concentrated in retail and food service. LinkUp classes these as real, high-turnover openings. — [LinkUp blog](https://www.linkup.com/insights/blog/the-absurd-myth-of-ghost-jobs)
- HR practice:
  - Evergreen requisitions are "not tied to a specific opening" and are used for talent pools and high-turnover roles. — [Mitratech](https://mitratech.com/resource-hub/pressreleases/how-to-properly-manage-evergreen-jobs-to-limit-liability)
  - Greenhouse advises keeping the openings count current and using unique opening IDs per hire; for always-open roles, "leave it at one opening, but leave the role open anytime you make a hire". — [Greenhouse InfoDoc, Apr 2021](https://support.greenhouse.io/hc/en-us/article_attachments/360095785911/2021-04-19_InfoDoc-Managing-Evergreen-Roles-in-Greenhouse.pdf)
- Ng counts pipeline postings as ghost jobs, while LinkUp counts evergreen high-turnover postings as real, a definitional conflict. — [Ng 2024](https://arxiv.org/abs/2410.21771); [LinkUp](https://www.linkup.com/insights/blog/the-absurd-myth-of-ghost-jobs)

#### Employer-level aggregation and shrinkage
- Kline, Rose & Walters (Jun 2023) built an empirical Bayes "report card" that grades 97 large US employers on discrimination. A four-grade scheme keeps the chance that a random pair of firms is mis-ranked at about 5%, the grades explain nearly half the variation in firms' contact gaps, and each grade comes with uncertainty measures. — [Kline, Rose & Walters, arXiv 2306.13005](https://arxiv.org/abs/2306.13005)
- The underlying experiment sent more than 83,000 applications to 108 employers; the between-firm SD of the racial contact gap was 1.9 percentage points. — [IZA DP 14634, 2021](https://docs.iza.org/dp14634.pdf)
- Ng finds ghost-review shares peak at mid-to-large firms. — [Ng 2024](https://arxiv.org/abs/2410.21771). Hashizume finds employer effects dominate duration variation. — [arXiv 2510.01470](https://arxiv.org/html/2510.01470v1)

#### Survival-analysis references
- Hazard and survival functions, right-censoring, Kaplan–Meier, and Cox versus parametric (Weibull, exponential) models. — [Rodríguez, GLM notes ch. 7](https://grodri.github.io/glms/notes/c7.pdf); [Rutgers hazards guide](https://bloustein.rutgers.edu/wp-content/uploads/2014/10/HazardsEcon.pdf)

### Inferences
- **Unit and timing.** The unit is the job-identity cluster from §2, with per-source child spells.
  - Time origin is the stated publication date if available, otherwise first-seen; postings already live at the first crawl are left-truncated.
  - The event is confirmed removal from all sources: two consecutive failed checks, or fetch confirmation.
  - Removal is interval-censored between the last success and the first failure.
  - Postings still live at the data cut-off are right-censored.
  - Portal-wide outages are excluded, not counted as events (WIH non-response).
- **Models.**
  - (a) A Kaplan–Meier or Turnbull baseline per stratum: occupation (KldB/ISCO), NUTS-2 or Kreis, source type, employer type.
  - (b) A parametric AFT model (log-normal or Weibull), which gives an expected median that is easy to interpret, with covariates including salary present, contract type, seniority, staffing-agency flag, firm size and season.
  - (c) A discrete-time hazard model (weekly logit or cloglog) when time-varying covariates matter, such as cumulative reposts or text edits.
  - Cox models suit inference but are less convenient for producing per-posting expected durations.
- **Scores.**
  - *Excess-age score* = current age ÷ predicted median for the posting's covariates, or the tail probability S(age | x). For example, flag when S < 0.05 in the stratum.
  - *Repost-adjusted lifetime* = cumulative live days of the cluster across reposts. Reposts that reset age are exactly what defeats naive age features.
  - Normalise against BA occupation and region baselines, as the BA itself does with its +30%/+40% markers. Note that the BA clock starts at the desired fill date, not the posting date, so BA figures can only calibrate *relative* occupation and region effects, not absolute day counts.
- **Anomaly detection for evergreen and auto-refresh behaviour:**
  - periodicity tests on appearance dates, e.g., spikes every 30 days that match portal default terms;
  - the share of the cluster's life spent "refreshed but unchanged";
  - robust z-scores (median/MAD) of repost rate within occupation×region×source;
  - Isolation Forest over a small vector of lifetime and repost features.
  - Evergreen should be its own label distinct from ghost, given the LinkUp vs Ng definitional split, so downstream users can choose their own policy.
- **Employer ghost score.**
  - Aggregate posting-level probabilities, or flags, with beta-binomial empirical Bayes: posterior mean = (α + Σ flags) / (α + β + n_postings), with α and β fitted to all employers in the same size band and sector. Alternatively, use a hierarchical logistic model with employer random intercepts.
  - Report coarse grades with uncertainty in the Kline–Rose–Walters style, rather than raw ranks, to control mis-ranking among small employers.
  - Keep staffing agencies (Personaldienstleister) as a separate peer group. The BA excludes them from vacancy-duration statistics because pooling distorts demand, so their lifetimes are not comparable to direct employers'.
- **Proxy-duration thresholds** like "older than 30 days" are not defensible as labels: medians run around 23–37 days and the 90-day-plus tail is around 25% in published data. Thresholds must be conditional on stratum.

### Gaps
- No peer-reviewed study fitting survival or hazard models specifically to scraped posting lifetimes for ghost detection was found. The search returned only general survival-analysis material and economics papers on vacancy duration.
- No German statistics on scraped posting lifetimes by occupation were found; BA vacancy durations cover only BA-registered vacancies and use a different clock start.
- No published anomaly-detection method for auto-refreshed postings was found; the approaches above are inferred.

---

## 5. How can ground truth be obtained, and what label noise comes with each option?

### Takeaway
No source offers verified posting-level ghost labels at scale. Every option labels a different construct:
- applicant reviews measure candidate experience;
- posting-to-hire matching measures conversion within a time window;
- employer confirmation measures whether a vacancy is open, which is the closest to the definition but small and prone to self-report bias;
- ATS data measures hiring activity, but is proprietary;
- reposts and removals are behavioural proxies with known delays.

The defensible design triangulates several weak labels and adjudicates a stratified audit sample against an explicit vacancy definition. The Eurostat JVS definition is a good choice: the employer is taking active steps and intends to fill. Eurostat's 2021 audit-sample design is directly reusable.

### Cited Findings

#### Applicant-outcome and review-based labels
- Ng used Glassdoor interview reviews labelled by GPT-4o (2,000 reviews, "90% sure" prompt) and extended to 269,347 reviews with BERT (21% flagged). The keyword baseline was dominated by "ghosted" (3,169 of 3,624 matches). Ng acknowledges upward bias (a better candidate was hired) and downward bias (non-reporting). — [Ng 2024](https://arxiv.org/abs/2410.21771)
- Revelio found the share of interview reviews mentioning recruiter ghosting rose 120% between January 2018 and 2023. It treats this only as "some indication" that falling hires per posting is not purely a shortage effect. — [Revelio](https://www.reveliolabs.com/news/macro/ghost-job-postings)

#### Matching postings to new hires
- Revelio matched postings to new positions started within 6 months on company, role, seniority and state, finding hires per posting fell from 0.75 to below 0.5 between 2018 and 2023. The authors list benign explanations (shortages, uncertainty) next to the "cynical interpretation". — [Revelio](https://www.reveliolabs.com/news/macro/ghost-job-postings)
- Revelio publishes an `Expected_hires` field per posting. — [Revelio data dictionary](https://www.data-dictionary.reveliolabs.com/data.html)

#### Employer confirmation, audit samples and surveys
- Beręsewicz & Pater (Eurostat 2021) propose two independent audit samples per country.
  - Sample s1 checks over-coverage. It is drawn by simple random sampling or by Poisson sampling proportional to days since the ad was placed, and it "requires contacting the company or recruiting agency to verify if the vacancy is in fact open" (e.g., a 1% sample, depending on budget). The results train a binary classifier (out-of-scope vs open vacancy).
  - Sample s2 checks dedup. It samples the most and least likely duplicate pairs and verifies them, with supervised record linkage on top.
  - The two samples are then combined to estimate over-coverage. — [Beręsewicz & Pater 2021](https://ec.europa.eu/eurostat/documents/3888793/12287170/KS-TC-20-008-EN-N.pdf/6a86d53e-d0b8-d608-988d-d91f0cef6c21?t=1611673495829)
- The Eurostat JVS definition of a vacancy: a paid post that is newly created, unoccupied or about to become vacant, for which the employer is taking active steps to find a candidate from outside and which it intends to fill immediately or within a specific period. — [WIH metadata](https://ec.europa.eu/eurostat/cache/metadata/Annexes/isoc_sk_oja_esmsip2_an_1.pdf)
- Germany's IAB Job Vacancy Survey asks establishments whether they are currently searching, both for immediate hires and for later dates. Destatis has benchmarked scraped data against it, and it has run since 1989 in West Germany and 1992 in East Germany, with 13,000–15,000 Q4 responses. — [Destatis WISTA 5/2018](https://www.destatis.de/DE/Methoden/WISTA-Wirtschaft-und-Statistik/2018/05/internetgestuetzte-erfassung-052018.pdf?__blob=publicationFile)

#### ATS-derived labels
- Greenhouse classifies 18–22% of jobs posted on its platform as ghost jobs, defined as "published online, but no hiring activity was ever conducted for it", with construction highest at 38%. — [CPA Practice Advisor, 12 Nov 2025](https://www.cpapracticeadvisor.com/2025/11/12/ghost-jobs-up-to-1-in-3-job-listings-dont-result-in-hires/173044/); [Fox, c. late 2024](https://www.fox5ny.com/news/ghost-jobs-greenhouse-analysis) (no primary Greenhouse methodology found)

#### Behavioural proxy labels
- **Removal as "filled".** LinkUp assumes removal means filled but notes "removal doesn't always mean a hire". — [LinkUp](https://www.linkup.com/use-cases/closed-duration-of-full-stack-jobs). The BA uses deregistration as a proxy for filling, with an unquantifiable delay. — [BA Methodenbericht 2020](https://statistik.arbeitsagentur.de/DE/Statischer-Content/Grundlagen/Methodik-Qualitaet/Methodenberichte/Uebergreifend/Generische-Publikationen/Methodenbericht-Engpassanalyse-Methodische-Weiterentwicklung.pdf). Indeed notes postings may remain online after being filled. — [Indeed FAQ](https://hiringlab.indeed.com/indeed-data-faq-2/)
- **Reappearance.** On LinkedIn a repost is a new job ID with a reset date. — [LinkedIn Help](https://www.linkedin.com/help/learning/answer/a522249) [snippet-level]. Lightcast treats a reappearance after 60 days as a new posting. — [Lightcast](https://kb.lightcast.io/en/articles/6957661-how-does-lightcast-handle-duplicate-postings)
- **Long open duration as a label** is rejected by Ng, because employers can claim difficulty filling the role. — [Ng 2024](https://arxiv.org/abs/2410.21771)

### Inferences
- **Label options:**

| Label source | What it actually measures | Main noise / bias | Feasibility in Germany |
|---|---|---|---|
| Crowdsourced applicant outcomes (response? interview? speed of rejection?) | candidate experience, attributable to a posting only if the URL or ID is captured | selection (frustrated users report more); "ghosted" ≠ no vacancy; a fast rejection may be automated ATS screening; small samples per posting | needs own panel or browser extension; GDPR consent design |
| Hire matching (profiles) | conversion within a window | profile coverage gaps (LinkedIn/Xing penetration varies by occupation, *inference*); internal hires; title and seniority mismatch; lag beyond the window; multi-vacancy ads | possible only through vendors (Revelio-type) or licensed profile data |
| Employer confirmation / audit calls | open-vacancy status per JVS definition | social-desirability bias (employers will not admit "no intent"); non-response; costly; time-point only | feasible at small scale (Eurostat s1 design); align with IAB survey wording |
| ATS hiring activity | whether any candidate advanced or was hired | proprietary; ATS-customer selection | only through partnerships |
| Proxy: repost after being marked filled / repeated refresh | refresh behaviour | evergreen high-turnover roles and staffing pools are legitimate; portal auto-refresh | fully automatable from own crawl |
| Proxy: removal = filled | end of advertising | delays, expiry-driven removal, site outages | automatable; treat as a censoring mechanism, not truth |

- **Validation design:**
  - Define the target as Eurostat JVS non-vacancy, i.e., no active steps or no intent to fill within a period, with evergreen/pipeline as a separate class.
  - Build weak labels (repost-after-close, excess-age, applicant-report rate, no-hire-in-6-months where available) and combine them with a label model. Treat unlabelled postings as unlabelled, not negative: positive-unlabelled learning.
  - Draw a stratified audit sample, oversampling high-score and long-lived postings (Poisson proportional to age, as Eurostat proposes), and adjudicate it with employer contact, applicant follow-up and later-hire checks. Report precision at fixed review budgets and calibration curves, not accuracy.
- **Interpretation.** Never claim prevalence from a classifier trained on imposed-prevalence labels (Mathison's 20%). Estimate prevalence from the audit sample with design weights.

### Gaps
- No primary Greenhouse methodology for the 18–22% figure was found; only press summaries exist.
- No German source of verified applicant-outcome data per posting was found.
- No study quantifying the agreement between different ghost labels (reviews vs hire matching vs employer confirmation) was found.

---

## 6. What NLP issues are specific to German job ads?

### Takeaway
German ads mix German boilerplate with English titles, tech terms and sometimes whole English bodies. They carry gender tags glued to titles, and long compounds hurt word-level matching. Practical answers:
- character n-gram MinHash and subword models for robustness;
- gender-tag normalisation before any title matching;
- per-segment language identification;
- domain-adapted German models: GBERT/GELECTRA base, jobGBERT trained on 4M Swiss German-language ads (non-commercial licence), JobBERT-v3 for multilingual title matching (MIT), and ESCOXLM-R for ESCO-linked tasks.

Translate-then-embed beat multilingual embeddings in the Eurostat challenge. For German↔English specifically, a multilingual model was workable in Engelbach's production system only when combined with skill-based scores.

### Cited Findings

#### Models
- GBERT and GELECTRA (base and large) by Chan, Schweter & Möller (COLING 2020) reported state-of-the-art German classification and NER results; more data and whole-word masking helped. — [ACL Anthology 2020.coling-main.598](https://aclanthology.org/2020.coling-main.598/)
- jobGBERT is `deepset/gbert-base` with continued pretraining on 4 million German-language job ads from Switzerland, 1990–2020 (5.9 GB), licensed CC BY-NC-SA 4.0. It may contain biases and stereotypes common in job ads. — [HF: agne/jobGBERT](https://huggingface.co/agne/jobGBERT). The sibling `jobBERT-de` is based on `bert-base-german-cased`, with the same licence. — [HF: agne/jobBERT-de](https://huggingface.co/agne/jobBERT-de)
- Gnehm, Bühlmann & Clematide (LREC 2022) found domain adaptation "consistently" improves task models. It mitigates data shift over time, and continued in-domain pretraining outperforms general-domain models trained on ten times more data. — [ACL Anthology 2022.lrec-1.414](https://aclanthology.org/2022.lrec-1.414)
- ESCOXLM-R (Zhang, van der Goot & Plank, ACL 2023) is XLM-R-large further pretrained on the ESCO taxonomy in 27 languages, with state-of-the-art results on 6 of 9 job-market datasets across 4 languages. — [ACL Anthology 2023.acl-long.662](https://aclanthology.org/2023.acl-long.662); [arXiv 2305.12092](https://arxiv.org/abs/2305.12092)
- JobBERT-v3 (TechWolf, Jul 2025) does cross-lingual job-title matching in English, German, Spanish and Chinese. It is fine-tuned from `paraphrase-multilingual-mpnet-base-v2` with 1024-dimensional output, a 64-token maximum sequence length and an MIT licence, trained on over 21M titles and evaluated on TalentCLEF 2025. — [HF: TechWolf/JobBERT-v3](https://huggingface.co/TechWolf/JobBERT-v3); [arXiv 2507.21609](https://arxiv.org/abs/2507.21609)
- A German-title-to-ESCO occupation classifier exists as `mischeiwiller/jobbert-de`. — [HF](https://huggingface.co/mischeiwiller/jobbert-de) [snippet-level]. A BA project that adapted gBERT reportedly found that "not all our tasks were able to profit from the domain adaptation". — [Springer chapter](https://link.springer.com/chapter/10.1007/978-3-032-10004-7_9) [snippet-level]
- **Embedding choices in practice:**
  - Engelbach et al. used `distiluse-base-multilingual-cased-v1` on mixed German/English ads and advise "an appropriate embedding model for the target language or a multilingual one". — [Engelbach et al. 2024](https://arxiv.org/abs/2406.06257)
  - Pasch et al. found translation plus `all-mpnet-base-v2` beat `distiluse` (semantic F1 0.82 vs 0.60), especially for less widely used languages. mpnet's 384-token cap truncated 43% of ads. — [Pasch et al. 2024](https://arxiv.org/abs/2406.13695)

#### Datasets
- GOJA (BIBB with HU Berlin and Univ. Köln; EMNLP 2025) contains 500 German job ads sampled from Textkernel Jobfeed (regular employment only). Annotation is compositional (roles, tools, experience levels, attitudes and their relations), with a Krippendorff's α > 0.7 bar for annotators and double annotation plus curation. It is released on GitHub. — [Krüger et al. 2025](https://aclanthology.org/2025.emnlp-main.1375.pdf); [GitHub KruegerETRF/GOJA](https://github.com/KruegerETRF/GOJA)
- The Swiss German job-ad corpus behind jobGBERT spans 1990–2020. Its models and data are released per the LREC paper. — [Gnehm et al. 2022](https://aclanthology.org/2022.lrec-1.414); [HF jobGBERT](https://huggingface.co/agne/jobGBERT)
- The Eurostat challenge set (about 112k ads) includes German as one of the dominant languages. — [Pasch et al. 2024](https://arxiv.org/abs/2406.13695)

#### German-specific text phenomena seen in real data
- Engelbach et al.'s German freelance-ad example shows a German frame ("Aufgaben … Zu Ihren Aufgaben zählt …", "Konnten wir Ihr Interesse wecken") wrapped around English task and requirement text. Scraping glued the gender tag to the next field: "m/w/dStellentyp freiberuflich…". — [Engelbach et al. 2024](https://arxiv.org/abs/2406.06257)
- Eurostat WIH noise filters and classifiers are language-dependent and trained separately per language. Dictionary-based classification is harder for morphologically rich languages, which need base-form dictionaries. — [WIH metadata](https://ec.europa.eu/eurostat/cache/metadata/Annexes/isoc_sk_oja_esmsip2_an_1.pdf); [Beręsewicz & Pater 2021](https://ec.europa.eu/eurostat/documents/3888793/12287170/KS-TC-20-008-EN-N.pdf/6a86d53e-d0b8-d608-988d-d91f0cef6c21?t=1611673495829)
- Insee used fastText language identification. They noted that low-confidence language IDs matter little for dedup, because similar ads get the same (even wrong) language, and that per-language frequent-word filtering helps. — [Insee slides](https://cros.ec.europa.eu/system/files/2024-05/Webinar%20Deduplication.pdf)

### Inferences
- **Gender-tag normalisation.** Strip and record tags before title matching, clustering or vagueness counts. Store a flag; do not use it as a ghost feature without validation.
  - Variants to normalise (validate frequencies on your own corpus): `(m/w/d)`, `(w/m/d)`, `(d/m/w)`, `(m/f/d)`, `(m/w/x)`, `(all genders)`, `(gn)`, `*in`, `:in`, `_in`, `/-in`, `/in`, `-frau/-mann` pairs such as "Kaufmann/-frau", and "Innen" plural forms.
  - Repair glued tokens like "m/w/dStellentyp" by splitting on the tag pattern.
- **Compounds.**
  - For dedup, use char 4-gram shingles (Insee) rather than word shingles.
  - For skill and title extraction, rely on subword tokenisers (GBERT/jobGBERT WordPiece) or a German compound splitter for lexicon lookup, e.g., matching "Lagerlogistik" to "Logistik" skills.
  - Inverse-frequency skill weighting (Engelbach) should be computed after splitting, so that rare compounds do not get spuriously high weight.
- **Mixed German/English text.**
  - Run language ID per paragraph, not per ad.
  - Normalise English titles ("Senior Software Engineer (m/w/d)") with a cross-lingual title model (JobBERT-v3, titles only given its 64-token limit).
  - For full-text similarity across DE/EN versions of the same ad, either translate to one language (Pasch's best F1) or use a multilingual encoder plus skill-based scores (Engelbach).
  - Chunk long ads to avoid the 384-token truncation.
- **Model choice and licensing.** jobGBERT's non-commercial licence (CC BY-NC-SA 4.0) may rule it out for a commercial pipeline. In that case, use GBERT/GELECTRA and continue pretraining on your own German ads, as Gnehm et al. show domain adaptation pays off and resists drift; or use the MIT-licensed JobBERT-v3 for titles. ESCOXLM-R suits ESCO-linked extraction; its licence was not checked.
- **German boilerplate to strip before any text features:** legal and process blocks such as "Wir freuen uns auf Ihre aussagekräftige Bewerbung", privacy/AGG notices and "Über uns" sections, plus portal chrome. Otherwise vagueness and length features measure template length rather than posting effort. This is the same failure Engelbach documents for embeddings.
- **Staffing agencies** (Personaldienstleister/Zeitarbeit) produce German-specific pool ads. Detect agency employers (name patterns, "im Auftrag unseres Kunden", "für unseren Kunden") and model them separately; the BA's exclusion of temp-agency vacancies from duration statistics because of pooling supports this.
- **Occupation coding** for normalisation should map titles to the KldB 2010 and ISCO/ESCO codes used in BA statistics, so lifetimes can be benchmarked against BA occupation and region tables. (KldB coding specifics were not researched here; see Gaps.)

### Gaps
- No public German gold standard exists for ghost-job, duplicate or repost labels; GOJA covers requirements extraction only.
- No benchmark comparing German sentence-embedding models (e.g., multilingual-e5, BGE-M3, German STS models) on job-ad similarity was found; the search budget was exhausted before this could be checked.
- No study of how often each gender-tag variant occurs, or of its link to posting quality, was found.
- Automated KldB/ISCO coding tools and accuracy for German job titles were not researched for lack of search budget.
- ESCOXLM-R's licence and German-specific evaluation numbers were not verified.
