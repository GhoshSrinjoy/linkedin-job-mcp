const axios = require("axios");
const cheerio = require("cheerio");
const randomUseragent = require("random-useragent");
const {
  USER_AGENT,
  REQUEST_TIMEOUT_MS,
  CACHE_TTL_MS,
  DETAIL_MIN_INTERVAL_MS,
  DETAIL_CACHE_TTL_MS,
} = require("./config");

// Simple delay helper for retries/backoff
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// Basic in-memory cache with TTL (1 hour)
class JobCache {
  constructor() {
    this.cache = new Map();
    this.TTL = CACHE_TTL_MS;
  }

  set(key, value) {
    this.cache.set(key, { value, timestamp: Date.now() });
  }

  get(key) {
    const entry = this.cache.get(key);
    if (!entry) return null;
    if (Date.now() - entry.timestamp > this.TTL) {
      this.cache.delete(key);
      return null;
    }
    return entry.value;
  }

  clear() {
    this.cache.clear();
  }
}

const cache = new JobCache();
const BASE_URL =
  "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search";
const PAGE_SIZE = 25;
const DEFAULT_USER_AGENT =
  USER_AGENT ||
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36";

// ---------------------------------------------------------------------------
// Helpers to normalize inputs and map filters to LinkedIn params
// ---------------------------------------------------------------------------
function normalizeStr(str) {
  return (str || "").trim();
}

function mapDateSincePosted(dateSincePosted) {
  if (!dateSincePosted) return "";
  const key = dateSincePosted.toLowerCase();
  if (key.includes("24")) return "r86400";
  if (key.includes("week")) return "r604800";
  if (key.includes("month")) return "r2592000";
  return "";
}

function mapRemoteFilter(remoteFilter) {
  const key = (remoteFilter || "").toLowerCase();
  if (key === "on site" || key === "on-site") return "1";
  if (key === "remote") return "2";
  if (key === "hybrid") return "3";
  return "";
}

function mapJobType(jobType) {
  const key = (jobType || "").toLowerCase();
  const map = {
    "full time": "F",
    "full-time": "F",
    "part time": "P",
    "part-time": "P",
    contract: "C",
    temporary: "T",
    volunteer: "V",
    internship: "I",
  };
  return map[key] || "";
}

function mapSortBy(sortBy) {
  const key = (sortBy || "").toLowerCase();
  if (key === "recent") return "DD"; // date descending
  return ""; // default is "relevance"
}

// Accept numeric geoId or a small fallback map; otherwise omit (works for most searches)
const LOCATION_GEOIDS = {
  "united states": "103644278",
  "germany": "101282230",
  "india": "102713980",
  "united kingdom": "102257491",
  uk: "102257491",
  "canada": "101174742",
  "australia": "101452733",
  "netherlands": "102890719",
  "brazil": "106057199",
  "france": "103644220",
  "italy": "103350119",
  "spain": "105646813",
  "japan": "103644525",
  "berlin": "106967730",
  "munich": "106430259",
  "madrid": "105646813",
  "paris": "105015875",
  "rome": "103350119",
  "london": "102257491",
  "toronto": "101174742",
  "sydney": "101452733",
  "tokyo": "103644525",
  "bengaluru": "106506694",
  "mumbai": "102713980",
};

function resolveGeoId(location) {
  if (!location) return "";
  const trimmed = normalizeStr(location);
  if (/^\d{5,}$/.test(trimmed)) return trimmed; // numeric geoId provided
  const key = trimmed.toLowerCase();
  return LOCATION_GEOIDS[key] || "";
}

// ---------------------------------------------------------------------------
// Query class
// ---------------------------------------------------------------------------
class Query {
  constructor(queryObject) {
    this.keyword =
      queryObject.keyword ||
      queryObject.keywords ||
      queryObject.title ||
      queryObject.job_position ||
      "";
    this.location = queryObject.location || queryObject.country || "";
    this.city = queryObject.city || "";
    this.limit = Number(queryObject.limit || queryObject.resultLimit || 25);
    this.page = Number(queryObject.page || 0);
    this.dateSincePosted = queryObject.dateSincePosted || "";
    this.jobType = queryObject.jobType || queryObject.job_format || "";
    this.remoteFilter = queryObject.remoteFilter || queryObject.workplace || "";
    this.experienceLevel = queryObject.experienceLevel || "";
    this.sortBy = queryObject.sortBy || "";
    this.geoId =
      queryObject.geoId || resolveGeoId(this.location || this.city || "");
  }

  cacheKey() {
    const key = {
      keyword: normalizeStr(this.keyword).toLowerCase(),
      location: normalizeStr(this.location).toLowerCase(),
      city: normalizeStr(this.city).toLowerCase(),
      limit: this.limit,
      page: this.page,
      dateSincePosted: mapDateSincePosted(this.dateSincePosted),
      jobType: mapJobType(this.jobType),
      remoteFilter: mapRemoteFilter(this.remoteFilter),
      sortBy: mapSortBy(this.sortBy),
      geoId: this.geoId,
    };
    return JSON.stringify(key);
  }

  buildParams(start, count) {
    const params = {
      keywords: normalizeStr(this.keyword),
      location: normalizeStr(this.city || this.location || "Worldwide"),
      start,
      count,
    };

    const timeRange = mapDateSincePosted(this.dateSincePosted);
    if (timeRange) params.f_TPR = timeRange;

    const remote = mapRemoteFilter(this.remoteFilter);
    if (remote) params.f_WT = remote;

    const jt = mapJobType(this.jobType);
    if (jt) params.f_JT = jt;

    const sortBy = mapSortBy(this.sortBy);
    if (sortBy) params.sortBy = sortBy;

    if (this.geoId) params.geoId = this.geoId;

    return params;
  }
}

// ---------------------------------------------------------------------------
// Fetching + parsing
// ---------------------------------------------------------------------------
async function fetchJobsPage(params, attempt = 1) {
  const headers = {
    "User-Agent": randomUseragent.getRandom() || DEFAULT_USER_AGENT,
    "Accept-Language": "en-US,en;q=0.9",
    Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    Connection: "keep-alive",
  };

  const url = `${BASE_URL}?${new URLSearchParams(params).toString()}`;
  try {
    const resp = await axios.get(url, {
      headers,
      timeout: REQUEST_TIMEOUT_MS,
      validateStatus: (s) => s >= 200 && s < 400,
    });
    return resp.data;
  } catch (error) {
    const status = error.response?.status;
    if (attempt < 2 && (status === 429 || status === 403 || status === 999)) {
      await delay(1500 * attempt);
      return fetchJobsPage(params, attempt + 1);
    }
    throw error;
  }
}

function parseJobCards(html) {
  const $ = cheerio.load(html);
  const jobs = [];

  $("li").each((_, el) => {
    const title = $(el).find(".base-search-card__title").text().trim();
    const company = $(el)
      .find(".base-search-card__subtitle a, .base-search-card__subtitle")
      .text()
      .trim();
    const location = $(el).find(".job-search-card__location").text().trim();
    const dateNode = $(el).find("time");
    const date =
      dateNode.attr("datetime") || dateNode.text().trim() || undefined;
    const agoTime = $(el).find(".job-search-card__listdate").text().trim();
    const salary = $(el)
      .find(".job-search-card__salary-info")
      .text()
      .trim()
      .replace(/\s+/g, " ");
    const link = $(el).find(".base-card__full-link").attr("href");
    const companyLogo =
      $(el).find(".artdeco-entity-image").attr("data-delayed-url") ||
      $(el).find(".artdeco-entity-image").attr("data-ghost-url") ||
      $(el).find("img").attr("src") ||
      "";

    if (!title || !company) return;

    jobs.push({
      position: title,
      company: company,
      location: location,
      date: date || null,
      agoTime: agoTime || null,
      salary: salary || "Not specified",
      jobUrl: link && link.startsWith("http")
        ? link
        : link
        ? `https://www.linkedin.com${link}`
        : "",
      companyLogo: companyLogo,
    });
  });

  return jobs;
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------
async function query(queryObject = {}) {
  const q = new Query(queryObject);
  const cacheKey = q.cacheKey();
  const cached = cache.get(cacheKey);
  if (cached) {
    return cached;
  }

  const jobs = [];
  let start = q.page * PAGE_SIZE;

  while (jobs.length < q.limit) {
    // Always request a full page to avoid missing results when the API returns fewer than requested.
    const params = q.buildParams(start, PAGE_SIZE);
    const html = await fetchJobsPage(params);
    const batch = parseJobCards(html);

    if (!batch.length) break;

    jobs.push(...batch);
    start += PAGE_SIZE;

    // LinkedIn caps guest paging; stop early if we fetched less than a full page
    if (batch.length < PAGE_SIZE) break;

    // Small polite pause
    await delay(500 + Math.random() * 300);
  }

  const trimmed = jobs.slice(0, q.limit);
  cache.set(cacheKey, trimmed);
  return trimmed;
}

// ---------------------------------------------------------------------------
// Job details: the public (guest) job page with the full description
// ---------------------------------------------------------------------------
const JOB_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting";
const detailCache = new JobCache();
detailCache.TTL = DETAIL_CACHE_TTL_MS;
let detailQueue = Promise.resolve();
let lastDetailAt = 0;

// Accepts a job id or any LinkedIn job URL (jobs/view/<slug>-<id>, ?currentJobId=<id>)
function jobIdFrom(input) {
  const text = normalizeStr(String(input || ""));
  const match =
    text.match(/^(\d{6,})$/) ||
    text.match(/currentJobId=(\d{6,})/) ||
    text.match(/jobs\/view\/(?:[^/?#]*-)?(\d{6,})/) ||
    text.match(/jobPosting\/(\d{6,})/);
  return match ? match[1] : null;
}

function cleanText($, el) {
  const node = $(el).clone();
  node.find("br").replaceWith("\n");
  node.find("li").each((_, li) => {
    $(li).prepend("• ");
    $(li).append("\n");
  });
  node.find("p, ul, ol, h1, h2, h3, h4").each((_, block) => $(block).append("\n"));
  return node
    .text()
    .replace(/[ \t ]+/g, " ")
    .replace(/ *\n */g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function parseJobPage(html, id) {
  const $ = cheerio.load(html);
  const text = (selector) => $(selector).first().text().replace(/\s+/g, " ").trim();
  const criteria = {};
  $(".description__job-criteria-item").each((_, el) => {
    const key = $(el).find(".description__job-criteria-subheader").text().replace(/\s+/g, " ").trim();
    const value = $(el).find(".description__job-criteria-text").text().replace(/\s+/g, " ").trim();
    if (key && value) criteria[key] = value;
  });
  const markup = $(".show-more-less-html__markup").first();
  return {
    id,
    position: text(".top-card-layout__title, .topcard__title"),
    company: text(".topcard__org-name-link, .topcard__flavor a"),
    location: text(".topcard__flavor--bullet"),
    postedAgo: text(".posted-time-ago__text") || null,
    applicants: text(".num-applicants__caption, .num-applicants__figure") || null,
    salary: text(".salary, .compensation__salary") || null,
    seniority: criteria["Seniority level"] || null,
    employmentType: criteria["Employment type"] || null,
    jobFunction: criteria["Job function"] || null,
    industries: criteria["Industries"] || null,
    criteria,
    acceptingApplications: !/no longer accepting applications/i.test($("body").text()),
    description: markup.length ? cleanText($, markup) : "",
    jobUrl: `https://www.linkedin.com/jobs/view/${id}/`,
  };
}

async function fetchJobPage(id, attempt = 1) {
  const resp = await axios.get(`${JOB_URL}/${id}`, {
    headers: {
      "User-Agent": DEFAULT_USER_AGENT,
      "Accept-Language": "en-US,en;q=0.9",
      Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    },
    timeout: REQUEST_TIMEOUT_MS,
    validateStatus: (s) => s >= 200 && s < 500,
  });
  if ((resp.status === 429 || resp.status === 999) && attempt < 2) {
    await delay(3000);
    return fetchJobPage(id, attempt + 1);
  }
  return resp;
}

/**
 * Full details of one job: description, criteria, posted time and the applicant count shown on the page.
 * Requests run one at a time, at least DETAIL_MIN_INTERVAL_MS apart, and are cached for DETAIL_CACHE_TTL_MS.
 * Returns { id, removed: true } when LinkedIn no longer has the job.
 */
async function getJobDetails(input) {
  const id = jobIdFrom(input);
  if (!id) {
    const err = new Error("Give a LinkedIn job id or a LinkedIn job URL");
    err.status = 400;
    throw err;
  }
  const cached = detailCache.get(id);
  if (cached) return { ...cached, cached: true };
  const run = async () => {
    const again = detailCache.get(id);
    if (again) return { ...again, cached: true };
    const wait = lastDetailAt + DETAIL_MIN_INTERVAL_MS - Date.now();
    if (wait > 0) await delay(wait);
    lastDetailAt = Date.now();
    const resp = await fetchJobPage(id);
    if (resp.status === 404 || resp.status === 410) {
      const gone = { id, removed: true, jobUrl: `https://www.linkedin.com/jobs/view/${id}/` };
      detailCache.set(id, gone);
      return gone;
    }
    if (resp.status >= 400) {
      const err = new Error(`LinkedIn returned HTTP ${resp.status}`);
      err.status = resp.status === 429 || resp.status === 999 ? 429 : 502;
      throw err;
    }
    const job = parseJobPage(resp.data, id);
    if (!job.position) {
      const err = new Error("The job page had no job data (layout change or a block page)");
      err.status = 502;
      throw err;
    }
    detailCache.set(id, job);
    return job;
  };
  const result = detailQueue.then(run, run);
  detailQueue = result.catch(() => {});
  return result;
}

// Stub kept for compatibility; guest endpoint does not need auth
function setAuth(jsessionid, li_at) {
  console.log(
    "LinkedIn guest endpoint is used; setAuth retained only for compatibility."
  );
  return { jsessionid, li_at };
}

module.exports = {
  query,
  getJobDetails,
  jobIdFrom,
  parseJobPage,
  JobCache,
  clearCache: () => {
    cache.clear();
    detailCache.clear();
  },
  getCacheSize: () => cache.cache.size,
  setAuth,
};
