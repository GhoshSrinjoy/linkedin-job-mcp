// Runs inside the job page (injected on click via chrome.scripting.executeScript).
// It must be self-contained: Chrome serialises the function, not its surrounding scope.
// eslint-disable-next-line no-unused-vars
function extractJob() {
  const host = location.hostname;
  const platform = /(^|\.)linkedin\./.test(host) ? "linkedin"
    : /(^|\.)indeed\./.test(host) ? "indeed"
    : /(^|\.)stepstone\./.test(host) ? "stepstone"
    : /(^|\.)xing\./.test(host) ? "xing"
    : /arbeitsagentur\.de$/.test(host) ? "ba"
    : /(^|\.)glassdoor\./.test(host) ? "glassdoor"
    : "web";
  const text = (el) => (el ? (el.innerText || el.textContent || "").replace(/[ \t]+\n/g, "\n").trim() : "");
  const first = (selectors) => {
    for (const s of selectors) {
      const el = document.querySelector(s);
      if (el && text(el)) return el;
    }
    return null;
  };
  const SELECTORS = {
    linkedin: {
      title: [".job-details-jobs-unified-top-card__job-title", ".jobs-unified-top-card__job-title", "h1.top-card-layout__title", "h1"],
      company: [".job-details-jobs-unified-top-card__company-name", ".jobs-unified-top-card__company-name", "a.topcard__org-name-link", ".topcard__org-name-link"],
      location: [".job-details-jobs-unified-top-card__primary-description-container", ".job-details-jobs-unified-top-card__tertiary-description-container", ".topcard__flavor--bullet"],
      top: [".job-details-jobs-unified-top-card__container--two-pane", ".jobs-unified-top-card", ".job-details-jobs-unified-top-card__primary-description-container", ".top-card-layout__entity-info", ".jobs-details__main-content"],
      description: ["#job-details", ".jobs-description__content", ".jobs-box__html-content", ".show-more-less-html__markup", ".description__text"],
    },
    indeed: {
      title: ['[data-testid="jobsearch-JobInfoHeader-title"]', "h1.jobsearch-JobInfoHeader-title", "h1"],
      company: ['[data-testid="inlineHeader-companyName"]', '[data-company-name="true"]'],
      location: ['[data-testid="inlineHeader-companyLocation"]', '[data-testid="job-location"]'],
      top: [".jobsearch-JobInfoHeader-subtitle", "#jobDetailsSection", ".jobsearch-JobMetadataFooter"],
      description: ["#jobDescriptionText"],
    },
    stepstone: {
      title: ['[data-at="header-job-title"]', "h1"],
      company: ['[data-at="metadata-company-name"]', '[data-at="header-company-name"]'],
      location: ['[data-at="metadata-location"]'],
      top: ['[data-at="job-ad-header"]', '[data-at="metadata-online-date"]', "header"],
      description: ['[data-at="job-ad-content"]', "article", "main"],
    },
    xing: {
      title: ["h1"],
      company: ['[data-testid="job-details-company-info-name"]'],
      location: ['[data-testid="job-details-location"]'],
      top: ['[data-testid="job-details-header"]', "header", "main"],
      description: ['[data-testid="expandable-content"]', "article", "main"],
    },
    ba: {
      title: ["#detail-kopfbereich-titel", "h1"],
      company: ["#detail-kopfbereich-firma"],
      location: ["#detail-kopfbereich-arbeitsort"],
      top: ["#detail-kopfbereich", "header", "main"],
      description: ["#detail-beschreibung-beschreibung", "#detail-beschreibung", "main"],
    },
    glassdoor: {
      title: ['[data-test="job-title"]', "h1"],
      company: ['[data-test="employer-name"]'],
      location: ['[data-test="location"]'],
      top: ['[data-test="job-details-header"]', "header"],
      description: ['[class*="JobDetails_jobDescription"]', ".jobDescriptionContent"],
    },
    web: { title: ["h1"], company: [], location: [], top: ["header", "main"], description: ["main", "article", "body"] },
  }[platform];

  const jsonld = [];
  for (const script of document.querySelectorAll('script[type="application/ld+json"]')) {
    try {
      const data = JSON.parse(script.textContent);
      for (const item of Array.isArray(data) ? data : [data]) if (item && typeof item === "object") jsonld.push(item);
    } catch (_) { /* ignore broken markup */ }
  }

  let top = text(first(SELECTORS.top)).slice(0, 5000);
  const head = text(document.querySelector("main") || document.body).slice(0, 6000);
  if (!top) top = head.slice(0, 2500);
  const haystack = `${top}\n${head}`;
  const find = (re) => { const m = haystack.match(re); return m ? m[0] : null; };
  const applicantText = find(/(?:over|more than|über|mehr als)\s+\d[\d.,]*\s+(?:applicants?|bewerber(?:\*|:|_)?(?:innen)?|bewerbungen)|\d[\d.,]*\s+(?:applicants?|bewerber(?:\*|:|_)?(?:innen)?|bewerbungen)|(?:be among the first|sei unter den ersten)\s+\d+/i);
  const postedText = find(/(?:reposted\s+)?\d+\s*\+?\s*(?:minutes?|hours?|days?|weeks?|months?)\s+ago|(?:erneut gepostet:?\s*)?vor\s+(?:über\s+|mehr als\s+)?\d+\+?\s*(?:minuten|stunden|tagen?|wochen|monaten?)(?:\s+erneut gepostet)?|(?:veröffentlicht|erschienen|online seit)\s*(?:am|seit)?\s*:?\s*\d{1,2}\.\s?\d{1,2}\.\s?\d{4}|just posted|gerade (?:veröffentlicht|geschaltet)/i);
  const badges = [];
  for (const re of [/actively (?:reviewing|recruiting)[^.\n]*/i, /bewerber(?::innen|innen)? werden aktiv geprüft/i,
    /aktiver arbeitgeber/i, /responses managed off linkedin/i, /außerhalb von linkedin verwaltete antworten/i,
    /no response insights[^.\n]*/i, /noch keine antwort verfügbar/i, /reposted[^.\n]{0,30}/i, /erneut gepostet[^.\n]{0,30}/i]) {
    const m = haystack.match(re);
    if (m) badges.push(m[0].slice(0, 120));
  }

  const url = location.href;
  const params = new URL(url).searchParams;
  let jobId = null;
  if (platform === "linkedin") jobId = params.get("currentJobId") || (url.match(/\/jobs\/view\/(?:[^/?#]*-)?(\d{6,})/) || [])[1] || null;
  if (platform === "indeed") jobId = params.get("vjk") || params.get("jk");
  if (platform === "stepstone") jobId = (url.match(/--(\d{5,})-inline\.html/) || url.match(/-(\d{6,})(?:-inline)?\.html/) || [])[1] || null;
  if (platform === "xing") jobId = (url.match(/-(\d{5,})(?:[/?#]|$)/) || [])[1] || null;
  if (platform === "ba") jobId = (url.match(/jobdetail\/([\w-]+)/) || [])[1] || null;
  const pageUrl = platform === "linkedin" && jobId ? `https://www.linkedin.com/jobs/view/${jobId}/` : url;
  const line = (el) => text(el).split("\n")[0].trim();
  return {
    platform,
    url: pageUrl,
    job_id: jobId,
    title: line(first(SELECTORS.title)).slice(0, 300) || document.title.slice(0, 300),
    company: line(first(SELECTORS.company)).slice(0, 200) || null,
    location: line(first(SELECTORS.location)).split(" · ")[0].slice(0, 200) || null,
    description: text(first(SELECTORS.description)).slice(0, 60000) || null,
    top_text: top.slice(0, 8000),
    applicant_text: applicantText,
    posted_text: postedText,
    badges,
    jsonld: jsonld.slice(0, 10),
  };
}
