const express = require("express");
const { query, getJobDetails } = require("./index");
const {
  API_PORT,
  RATE_LIMIT_WINDOW_MS,
  RATE_LIMIT_MAX,
  CACHE_TTL_MS,
} = require("./config");

const app = express();
app.use(express.json({ limit: "1mb" }));

// Simple per-IP rate limiter
const rateHits = new Map();
function rateLimit(req, res, next) {
  const ip = req.ip || req.connection?.remoteAddress || "unknown";
  const now = Date.now();
  const record = rateHits.get(ip) || { count: 0, start: now };

  if (now - record.start > RATE_LIMIT_WINDOW_MS) {
    record.count = 0;
    record.start = now;
  }

  record.count += 1;
  rateHits.set(ip, record);

  if (record.count > RATE_LIMIT_MAX) {
    return res.status(429).json({ error: "Rate limit exceeded" });
  }
  return next();
}

// Simple in-memory response cache
const cache = new Map();
function cacheKey(opts) {
  const allow = [
    "keyword",
    "location",
    "city",
    "country",
    "geoId",
    "dateSincePosted",
    "jobType",
    "remoteFilter",
    "limit",
    "sortBy",
    "page",
  ];
  const pruned = {};
  allow.forEach((k) => {
    if (opts[k] !== undefined) pruned[k] = opts[k];
  });
  return JSON.stringify(pruned);
}

function getCached(key) {
  const hit = cache.get(key);
  if (!hit) return null;
  if (Date.now() - hit.ts > CACHE_TTL_MS) {
    cache.delete(key);
    return null;
  }
  return hit.data;
}

function setCached(key, data) {
  cache.set(key, { data, ts: Date.now() });
}

app.get("/health", (req, res) => {
  res.json({ ok: true });
});

app.post("/search", rateLimit, async (req, res) => {
  try {
    const body = req.body || {};
    const options = {
      keyword: body.keyword || "",
      location: body.location || "",
      city: body.city || "",
      country: body.country || "",
      geoId: body.geoId || "",
      dateSincePosted: body.dateSincePosted || "",
      jobType: body.jobType || "",
      remoteFilter: body.remoteFilter || "",
      limit: Number(body.limit) || 25,
      sortBy: body.sortBy || "recent",
      page: Number(body.page) || 0,
    };

    const key = cacheKey(options);
    const cached = getCached(key);
    if (cached) {
      return res.json({ cached: true, total: cached.length, jobs: cached });
    }

    const jobs = await query(options);
    setCached(key, jobs);
    res.json({ cached: false, total: jobs.length, jobs });
  } catch (err) {
    console.error("API error:", err.message);
    res.status(500).json({ error: err.message || "Unknown error" });
  }
});

// Job details by id (GET /job/1234567890) or by URL (GET /job?url=https://www.linkedin.com/jobs/view/...)
async function sendJob(ref, res) {
  try {
    const job = await getJobDetails(ref);
    res.status(job.removed ? 404 : 200).json(job);
  } catch (err) {
    console.error("API error:", err.message);
    res.status(err.status || 500).json({ error: err.message || "Unknown error" });
  }
}

app.get("/job/:id", rateLimit, (req, res) => sendJob(req.params.id, res));
app.get("/job", rateLimit, (req, res) => sendJob(req.query.url || req.query.id, res));

app.listen(API_PORT, () => {
  console.log(`LinkedIn Jobs API listening on http://localhost:${API_PORT}`);
});
