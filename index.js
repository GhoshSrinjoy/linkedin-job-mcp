const cheerio = require("cheerio");
const axios = require("axios");
const randomUseragent = require("random-useragent");

// Utility functions
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// Cache implementation
class JobCache {
  constructor() {
    this.cache = new Map();
    this.TTL = 1000 * 60 * 60; // 1 hour
  }

  set(key, value) {
    this.cache.set(key, {
      data: value,
      timestamp: Date.now(),
    });
  }

  get(key) {
    const item = this.cache.get(key);
    if (!item) return null;
    if (Date.now() - item.timestamp > this.TTL) {
      this.cache.delete(key);
      return null;
    }
    return item.data;
  }

  clear() {
    const now = Date.now();
    for (const [key, value] of this.cache.entries()) {
      if (now - value.timestamp > this.TTL) {
        this.cache.delete(key);
      }
    }
  }
}

const cache = new JobCache();

// Generate a unique cache key based on the query parameters
Query.prototype.getCacheKey = function () {
  return `${this.url(0)}_limit:${this.limit}`;
};

// Main query function
module.exports.query = (queryObject) => {
  const query = new Query(queryObject);
  return query.getJobs();
};

// Location and host mapping
const COUNTRY_HOSTS = {
  'germany': 'de.linkedin.com',
  'deutschland': 'de.linkedin.com',
  'german': 'de.linkedin.com',
  'bayern': 'de.linkedin.com',
  'bavaria': 'de.linkedin.com',
  'munich': 'de.linkedin.com',
  'münchen': 'de.linkedin.com',
  'berlin': 'de.linkedin.com',
  'hamburg': 'de.linkedin.com',
  'cologne': 'de.linkedin.com',
  'köln': 'de.linkedin.com',
  'frankfurt': 'de.linkedin.com',
  'stuttgart': 'de.linkedin.com',
  'düsseldorf': 'de.linkedin.com',
  'dortmund': 'de.linkedin.com',
  'essen': 'de.linkedin.com',
  'leipzig': 'de.linkedin.com',
  'bremen': 'de.linkedin.com',
  'dresden': 'de.linkedin.com',
  'hannover': 'de.linkedin.com',
  'nürnberg': 'de.linkedin.com',
  'nuremberg': 'de.linkedin.com',
  'france': 'fr.linkedin.com',
  'spain': 'es.linkedin.com',
  'italy': 'it.linkedin.com',
  'netherlands': 'nl.linkedin.com',
  'uk': 'uk.linkedin.com',
  'britain': 'uk.linkedin.com',
  'england': 'uk.linkedin.com'
};

const LOCATION_GEOIDS = {
  // German locations with correct LinkedIn geoIds
  'bavaria': '102890719', // Bavaria geoId
  'bayern': '102890719',
  'munich': '106808217', // Munich geoId  
  'münchen': '106808217',
  'nuremberg': '106808217', // Use Munich for now
  'nürnberg': '106808217',
  'berlin': '102890712', // Berlin geoId
  'hamburg': '102890715', // Hamburg geoId
  'cologne': '102890714', // Cologne geoId
  'köln': '102890714',
  'frankfurt': '102890713', // Frankfurt geoId
  'stuttgart': '102890716', // Stuttgart geoId
  'germany': '101282230', // Germany main geoId
  'deutschland': '101282230'
};

const LOCATION_FORMATS = {
  // Keep text formats as backup
  'bavaria': 'Bayern, Deutschland',
  'bayern': 'Bayern, Deutschland',
  'munich': 'München, Deutschland',
  'münchen': 'München, Deutschland',
  'nuremberg': 'Nürnberg, Deutschland',
  'nürnberg': 'Nürnberg, Deutschland',
  'berlin': 'Berlin, Deutschland',
  'hamburg': 'Hamburg, Deutschland',
  'cologne': 'Köln, Deutschland',
  'köln': 'Köln, Deutschland',
  'frankfurt': 'Frankfurt am Main, Deutschland',
  'stuttgart': 'Stuttgart, Deutschland',
  'germany': 'Deutschland'
};

function detectHostFromLocation(location, geoData = null) {
  if (!location) return "www.linkedin.com";
  
  // If we have geocoding data, check the country
  if (geoData && geoData.standardizedName) {
    const standardizedLower = geoData.standardizedName.toLowerCase();
    if (standardizedLower.includes('deutschland') || standardizedLower.includes('germany')) {
      console.log('🇩🇪 Detected German location, using de.linkedin.com');
      return "de.linkedin.com";
    }
  }
  
  const locationLower = location.toLowerCase();
  
  // Check for exact matches first
  for (const [key, host] of Object.entries(COUNTRY_HOSTS)) {
    if (locationLower.includes(key)) {
      console.log(`🌍 Detected ${key}, using ${host}`);
      return host;
    }
  }
  
  return "www.linkedin.com";
}

async function getLocationGeoId(location) {
  if (!location) return null;
  
  try {
    console.log(`🔍 Looking up coordinates for: "${location}"`);
    
    // Use OpenStreetMap Nominatim for geocoding (free, no API key needed)
    const geocodeUrl = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(location)}&limit=1&addressdetails=1`;
    
    const headers = {
      'User-Agent': 'LinkedIn-Jobs-Scraper/1.0 (github.com/user/repo)'
    };
    
    const response = await axios.get(geocodeUrl, { headers, timeout: 10000 });
    
    if (response.data && response.data.length > 0) {
      const result = response.data[0];
      const { lat, lon, display_name, address } = result;
      
      console.log(`✅ Found location: ${display_name}`);
      console.log(`   Coordinates: ${lat}, ${lon}`);
      
      // For LinkedIn, we'll use the standardized location name from geocoding
      const standardizedLocation = getStandardizedLocationName(result, location);
      console.log(`   Standardized: ${standardizedLocation}`);
      
      return { 
        coordinates: { lat: parseFloat(lat), lon: parseFloat(lon) },
        standardizedName: standardizedLocation,
        originalName: display_name
      };
    }
    
    console.log(`⚠️  No coordinates found for "${location}", using original text`);
    return null;
    
  } catch (error) {
    console.log(`❌ Error geocoding "${location}":`, error.message);
    return null;
  }
}

function getStandardizedLocationName(geocodeResult, originalLocation) {
  const { address } = geocodeResult;
  
  if (!address) return originalLocation;
  
  // Build standardized location name
  const parts = [];
  
  if (address.city || address.town || address.village) {
    parts.push(address.city || address.town || address.village);
  }
  
  if (address.state) {
    parts.push(address.state);
  }
  
  if (address.country) {
    parts.push(address.country);
  }
  
  return parts.length > 0 ? parts.join(', ') : originalLocation;
}

function normalizeLocation(location) {
  if (!location) return "";
  
  const locationLower = location.toLowerCase();
  
  // Check for location format standardization
  for (const [key, standardFormat] of Object.entries(LOCATION_FORMATS)) {
    if (locationLower.includes(key)) {
      return standardFormat;
    }
  }
  
  return location;
}

// Query constructor
function Query(queryObj) {
  this.keyword = queryObj.keyword?.trim().replace(/\s+/g, "+") || "";
  this.location = queryObj.location?.trim().replace(/\s+/g, "+") || "";
  this.originalLocation = queryObj.location; // Keep original for geocoding lookup
  this.geoData = null; // Will store geocoding results
  this.host = null; // Will be set after geocoding
  this.dateSincePosted = queryObj.dateSincePosted || "";
  this.jobType = queryObj.jobType || "";
  this.remoteFilter = queryObj.remoteFilter || "";
  this.salary = queryObj.salary || "";
  this.experienceLevel = queryObj.experienceLevel || "";
  this.sortBy = queryObj.sortBy || "";
  this.limit = Number(queryObj.limit) || 0;
  this.page = Number(queryObj.page) || 0;
  this.has_verification = queryObj.has_verification || false;
  this.under_10_applicants = queryObj.under_10_applicants || false;
}

// Query prototype methods
Query.prototype.getDateSincePosted = function () {
  const dateRange = {
    "past month": "r2592000",
    "past week": "r604800",
    "24hr": "r86400",
  };
  return dateRange[this.dateSincePosted.toLowerCase()] || "";
};

Query.prototype.getExperienceLevel = function () {
  const experienceRange = {
    internship: "1",
    "entry level": "2",
    associate: "3",
    senior: "4",
    director: "5",
    executive: "6",
  };
  return experienceRange[this.experienceLevel.toLowerCase()] || "";
};

Query.prototype.getJobType = function () {
  const jobTypeRange = {
    "full time": "F",
    "full-time": "F",
    "part time": "P",
    "part-time": "P",
    contract: "C",
    temporary: "T",
    volunteer: "V",
    internship: "I",
  };
  return jobTypeRange[this.jobType.toLowerCase()] || "";
};

Query.prototype.getRemoteFilter = function () {
  const remoteFilterRange = {
    "on-site": "1",
    "on site": "1",
    remote: "2",
    hybrid: "3",
  };
  return remoteFilterRange[this.remoteFilter.toLowerCase()] || "";
};

Query.prototype.getSalary = function () {
  const salaryRange = {
    40000: "1",
    60000: "2",
    80000: "3",
    100000: "4",
    120000: "5",
  };
  return salaryRange[this.salary] || "";
};

Query.prototype.getHasVerification = function () {
  return this.has_verification ? "true" : "false";
};

Query.prototype.getUnder10Applicants = function () {
  return this.under_10_applicants ? "true" : "false";
};

Query.prototype.getPage = function () {
  return this.page * 25;
};

Query.prototype.url = function (start) {
  let query = `https://${this.host}/jobs-guest/jobs/api/seeMoreJobPostings/search?`;

  const params = new URLSearchParams();

  if (this.keyword) params.append("keywords", this.keyword);
  
  // Use standardized location name from geocoding if available
  const locationToUse = this.geoData && this.geoData.standardizedName ? 
    this.geoData.standardizedName.replace(/\s+/g, "+") : this.location;
    
  if (locationToUse) {
    params.append("location", locationToUse);
  }
  
  if (this.getDateSincePosted())
    params.append("f_TPR", this.getDateSincePosted());
  if (this.getSalary()) params.append("f_SB2", this.getSalary());
  if (this.getExperienceLevel())
    params.append("f_E", this.getExperienceLevel());
  if (this.getRemoteFilter()) params.append("f_WT", this.getRemoteFilter());
  if (this.getJobType()) params.append("f_JT", this.getJobType());
  if (this.getHasVerification())
    params.append("f_VJ", this.getHasVerification());
  if (this.getUnder10Applicants())
    params.append("f_EA", this.getUnder10Applicants());

  params.append("start", start + this.getPage());

  if (this.sortBy === "recent") params.append("sortBy", "DD");
  else if (this.sortBy === "relevant") params.append("sortBy", "R");

  return query + params.toString();
};

Query.prototype.getJobs = async function () {
  let allJobs = [];
  let start = 0;
  const BATCH_SIZE = 25;
  let hasMore = true;
  let consecutiveErrors = 0;
  const MAX_CONSECUTIVE_ERRORS = 3;
  
  try {
    // First, try to get standardized location data
    if (this.originalLocation && !this.geoData) {
      this.geoData = await getLocationGeoId(this.originalLocation);
    }
    
    // Set host based on geocoded location data
    if (!this.host) {
      this.host = detectHostFromLocation(this.originalLocation, this.geoData);
    }
    
    console.log(this.url());
    console.log(this.getCacheKey());
    
    // Check cache first
    const cacheKey = this.getCacheKey();
    const cachedJobs = cache.get(cacheKey);
    if (cachedJobs) {
      console.log("Returning cached results");
      return cachedJobs;
    }

    while (hasMore) {
      try {
        const jobs = await this.fetchJobBatch(start);

        if (!jobs || jobs.length === 0) {
          hasMore = false;
          break;
        }

        allJobs.push(...jobs);
        console.log(`Fetched ${jobs.length} jobs. Total: ${allJobs.length}`);

        if (this.limit && allJobs.length >= this.limit) {
          allJobs = allJobs.slice(0, this.limit);
          break;
        }

        // Reset error counter on successful fetch
        consecutiveErrors = 0;
        start += BATCH_SIZE;

        // Add reasonable delay between requests
        await delay(2000 + Math.random() * 1000);
      } catch (error) {
        consecutiveErrors++;
        console.error(
          `Error fetching batch (attempt ${consecutiveErrors}):`,
          error.message
        );

        if (consecutiveErrors >= MAX_CONSECUTIVE_ERRORS) {
          console.log("Max consecutive errors reached. Stopping.");
          break;
        }

        // Exponential backoff
        await delay(Math.pow(2, consecutiveErrors) * 1000);
      }
    }

    // Filter jobs by location if we're searching for German locations
    let filteredJobs = allJobs;
    
    if (this.geoData && this.geoData.standardizedName && 
        (this.geoData.standardizedName.toLowerCase().includes('deutschland') || 
         this.geoData.standardizedName.toLowerCase().includes('germany'))) {
      
      console.log('🇩🇪 Filtering for German jobs only...');
      
      filteredJobs = allJobs.filter(job => {
        const jobLocation = job.location.toLowerCase();
        return jobLocation.includes('germany') || 
               jobLocation.includes('deutschland') || 
               jobLocation.includes('berlin') || 
               jobLocation.includes('munich') || 
               jobLocation.includes('münchen') || 
               jobLocation.includes('hamburg') || 
               jobLocation.includes('köln') || 
               jobLocation.includes('cologne') || 
               jobLocation.includes('frankfurt') || 
               jobLocation.includes('stuttgart') || 
               jobLocation.includes('düsseldorf') || 
               jobLocation.includes('dortmund') || 
               jobLocation.includes('essen') || 
               jobLocation.includes('leipzig') || 
               jobLocation.includes('bremen') || 
               jobLocation.includes('dresden') || 
               jobLocation.includes('hannover') || 
               jobLocation.includes('nürnberg') || 
               jobLocation.includes('nuremberg') ||
               jobLocation.includes('bayern') ||
               jobLocation.includes('bavaria');
      });
      
      console.log(`🎯 Filtered: ${allJobs.length} → ${filteredJobs.length} German jobs`);
    }

    // Cache results if we got any
    if (filteredJobs.length > 0) {
      cache.set(this.getCacheKey(), filteredJobs);
    }

    return filteredJobs;
  } catch (error) {
    console.error("Fatal error in job fetching:", error);
    throw error;
  }
};

Query.prototype.fetchJobBatch = async function (start) {
  const headers = {
    "User-Agent": randomUseragent.getRandom(),
    Accept: "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    Referer: "https://www.linkedin.com/jobs",
    "X-Requested-With": "XMLHttpRequest",
    Connection: "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Cache-Control": "no-cache",
    Pragma: "no-cache",
  };

  try {
    const response = await axios.get(this.url(start), {
      headers,
      validateStatus: function (status) {
        return status === 200;
      },
      timeout: 10000,
    });

    return parseJobList(response.data);
  } catch (error) {
    if (error.response?.status === 429) {
      throw new Error("Rate limit reached");
    }
    throw error;
  }
};

function parseJobList(jobData) {
  try {
    const $ = cheerio.load(jobData);
    const jobs = $("li");

    return jobs
      .map((index, element) => {
        try {
          const job = $(element);
          const position = job.find(".base-search-card__title").text().trim();
          const company = job.find(".base-search-card__subtitle").text().trim();
          const location = job.find(".job-search-card__location").text().trim();
          const dateElement = job.find("time");
          const date = dateElement.attr("datetime");
          const salary = job
            .find(".job-search-card__salary-info")
            .text()
            .trim()
            .replace(/\s+/g, " ");
          const jobUrl = job.find(".base-card__full-link").attr("href");
          const companyLogo = job
            .find(".artdeco-entity-image")
            .attr("data-delayed-url");
          const agoTime = job.find(".job-search-card__listdate").text().trim();

          // Only return job if we have at least position and company
          if (!position || !company) {
            return null;
          }

          return {
            position,
            company,
            location,
            date,
            salary: salary || "Not specified",
            jobUrl: jobUrl || "",
            companyLogo: companyLogo || "",
            agoTime: agoTime || "",
          };
        } catch (err) {
          console.warn(`Error parsing job at index ${index}:`, err.message);
          return null;
        }
      })
      .get()
      .filter(Boolean);
  } catch (error) {
    console.error("Error parsing job list:", error);
    return [];
  }
}

// Export additional utilities for testing and monitoring
module.exports.JobCache = JobCache;
module.exports.clearCache = () => cache.clear();
module.exports.getCacheSize = () => cache.cache.size;
