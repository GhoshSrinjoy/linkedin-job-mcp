require("dotenv").config();

const intFromEnv = (key, fallback) => {
  const val = process.env[key];
  if (val === undefined) return fallback;
  const parsed = parseInt(val, 10);
  return Number.isNaN(parsed) ? fallback : parsed;
};

module.exports = {
  USER_AGENT: process.env.LINKEDIN_USER_AGENT || "",
  REQUEST_TIMEOUT_MS: intFromEnv("LINKEDIN_REQUEST_TIMEOUT_MS", 15000),
  CACHE_TTL_MS: intFromEnv("LINKEDIN_CACHE_TTL_MS", 60 * 60 * 1000),
  API_PORT: intFromEnv("PORT", 3000),
  // only this computer can reach the API unless HOST is set (for example HOST=0.0.0.0 in a container)
  API_HOST: process.env.HOST || "127.0.0.1",
  RATE_LIMIT_WINDOW_MS: intFromEnv("API_RATE_LIMIT_WINDOW_MS", 60_000),
  RATE_LIMIT_MAX: intFromEnv("API_RATE_LIMIT_MAX", 60),
  // job details: one page at a time, at least this far apart, cached for this long
  DETAIL_MIN_INTERVAL_MS: intFromEnv("LINKEDIN_DETAIL_MIN_INTERVAL_MS", 1500),
  DETAIL_CACHE_TTL_MS: intFromEnv("LINKEDIN_DETAIL_CACHE_TTL_MS", 6 * 60 * 60 * 1000),
};
