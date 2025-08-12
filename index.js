// const cheerio = require("cheerio");
// const axios = require("axios");
// const randomUseragent = require("random-useragent");
// const readline = require('readline');

// // LinkedIn Authentication Storage
// let linkedinAuth = {
//   jsessionid: null,
//   li_at: null,
//   isAuthenticated: false
// };

// // Function to set authentication directly (for testing)
// function setAuthentication(jsessionid, li_at) {
//   linkedinAuth.jsessionid = jsessionid.replace(/"/g, '');
//   linkedinAuth.li_at = li_at;
//   linkedinAuth.isAuthenticated = true;
//   console.log('✅ Authentication set directly');
// }

// // Utility functions
// const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// // Cache implementation
// class JobCache {
//   constructor() {
//     this.cache = new Map();
//     this.TTL = 1000 * 60 * 60; // 1 hour
//   }

//   set(key, value) {
//     this.cache.set(key, {
//       data: value,
//       timestamp: Date.now(),
//     });
//   }

//   get(key) {
//     const item = this.cache.get(key);
//     if (!item) return null;
//     if (Date.now() - item.timestamp > this.TTL) {
//       this.cache.delete(key);
//       return null;
//     }
//     return item.data;
//   }

//   clear() {
//     const now = Date.now();
//     for (const [key, value] of this.cache.entries()) {
//       if (now - value.timestamp > this.TTL) {
//         this.cache.delete(key);
//       }
//     }
//   }
// }

// const cache = new JobCache();

// // Generate a unique cache key based on the query parameters
// Query.prototype.getCacheKey = function () {
//   return `${this.url(0)}_limit:${this.limit}`;
// };

// // Main query function
// module.exports.query = (queryObject) => {
//   const query = new Query(queryObject);
//   return query.getJobs();
// };

// // Location and host mapping
// const COUNTRY_HOSTS = {
//   'germany': 'de.linkedin.com',
//   'deutschland': 'de.linkedin.com',
//   'german': 'de.linkedin.com',
//   'bayern': 'de.linkedin.com',
//   'bavaria': 'de.linkedin.com',
//   'munich': 'de.linkedin.com',
//   'münchen': 'de.linkedin.com',
//   'berlin': 'de.linkedin.com',
//   'hamburg': 'de.linkedin.com',
//   'cologne': 'de.linkedin.com',
//   'köln': 'de.linkedin.com',
//   'frankfurt': 'de.linkedin.com',
//   'stuttgart': 'de.linkedin.com',
//   'düsseldorf': 'de.linkedin.com',
//   'dortmund': 'de.linkedin.com',
//   'essen': 'de.linkedin.com',
//   'leipzig': 'de.linkedin.com',
//   'bremen': 'de.linkedin.com',
//   'dresden': 'de.linkedin.com',
//   'hannover': 'de.linkedin.com',
//   'nürnberg': 'de.linkedin.com',
//   'nuremberg': 'de.linkedin.com',
//   'nüremberg': 'de.linkedin.com',
//   'france': 'fr.linkedin.com',
//   'spain': 'es.linkedin.com',
//   'italy': 'it.linkedin.com',
//   'netherlands': 'nl.linkedin.com',
//   'uk': 'uk.linkedin.com',
//   'britain': 'uk.linkedin.com',
//   'england': 'uk.linkedin.com'
// };

// const LOCATION_GEOIDS = {
//   // United States
//   'new york': '102571732',
//   'california': '102095887', 
//   'san francisco': '102277331',
//   'los angeles': '103644278',
//   'chicago': '103112676',
//   'boston': '100293800',
//   'seattle': '103816755',
//   'united states': '103644278',
//   'usa': '103644278',
  
//   // Germany
//   'germany': '101282230',
//   'deutschland': '101282230',
//   'berlin': '102890712',
//   'munich': '106808217',
//   'münchen': '106808217',
//   'hamburg': '102890715',
//   'cologne': '102890714',
//   'köln': '102890714',
//   'frankfurt': '102890713',
//   'stuttgart': '102890716',
//   'nuremberg': '106808217',
//   'nürnberg': '106808217',
//   'nüremberg': '106808217',
//   'bavaria': '102890719',
//   'bayern': '102890719',
  
//   // Australia  
//   'australia': '101452733',
//   'sydney': '104769905',
//   'melbourne': '104769900',
//   'victoria': '104769900',
//   'brisbane': '104769906',
  
//   // United Kingdom
//   'uk': '102257491',
//   'united kingdom': '102257491',
//   'london': '90010383',
  
//   // Japan
//   'japan': '101355337',
//   'tokyo': '104038894',
//   'osaka': '104038895',
//   'kyoto': '104038896',
//   'yokohama': '104038897',
  
//   // Other Asian locations
//   'singapore': '104038910',
//   'hong kong': '102257491',
//   'seoul': '104038900',
//   'bangalore': '105214831',
//   'mumbai': '105214830',
//   'delhi': '105214832',
  
//   // Other
//   'brazil': '106057199',
//   'são paulo': '104994530',
//   'canada': '101174742'
// };

// const LOCATION_FORMATS = {
//   // Keep text formats as backup
//   'bavaria': 'Bayern, Deutschland',
//   'bayern': 'Bayern, Deutschland',
//   'munich': 'München, Deutschland',
//   'münchen': 'München, Deutschland',
//   'nuremberg': 'Nürnberg, Deutschland',
//   'nürnberg': 'Nürnberg, Deutschland',
//   'nüremberg': 'Nürnberg, Deutschland',
//   'berlin': 'Berlin, Deutschland',
//   'hamburg': 'Hamburg, Deutschland',
//   'cologne': 'Köln, Deutschland',
//   'köln': 'Köln, Deutschland',
//   'frankfurt': 'Frankfurt am Main, Deutschland',
//   'stuttgart': 'Stuttgart, Deutschland',
//   'germany': 'Deutschland'
// };

// // Prompt user for LinkedIn cookies if not authenticated
// async function ensureAuthentication() {
//   if (linkedinAuth.isAuthenticated) {
//     return true;
//   }
  
//   console.log('\n🔐 LinkedIn Authentication Required');
//   console.log('Please provide your LinkedIn session cookies:');
//   console.log('1. Open LinkedIn in your browser and login');
//   console.log('2. Open Developer Tools (F12) > Application/Storage > Cookies');
//   console.log('3. Find linkedin.com cookies and copy the values below:\n');
  
//   const rl = readline.createInterface({
//     input: process.stdin,
//     output: process.stdout
//   });
  
//   try {
//     const jsessionid = await new Promise(resolve => {
//       rl.question('Enter JSESSIONID cookie value: ', resolve);
//     });
    
//     const li_at = await new Promise(resolve => {
//       rl.question('Enter li_at cookie value: ', resolve);
//     });
    
//     if (jsessionid && li_at) {
//       linkedinAuth.jsessionid = jsessionid.replace(/"/g, ''); // Remove quotes
//       linkedinAuth.li_at = li_at;
//       linkedinAuth.isAuthenticated = true;
//       console.log('✅ Authentication configured successfully\n');
//       return true;
//     } else {
//       console.log('❌ Invalid cookies provided');
//       return false;
//     }
//   } finally {
//     rl.close();
//   }
// }

// // Get real LinkedIn geoIds by checking the redirect URL from LinkedIn job search
// async function searchLinkedInLocations(location) {
//   if (!location) return [];
  
//   try {
//     console.log(`🔍 Getting LinkedIn geoId for "${location}"...`);
    
//     // Try different LinkedIn location APIs 
//     const apiUrls = [
//       // Guest location autocomplete (might not need auth)
//       `https://www.linkedin.com/voyager/api/graphql?variables=(query:${encodeURIComponent(location)},start:0,count:10)&queryId=voyagerSearchDashClusters.cb3b6c2bbf8c7a488d78f966c52c7a6c`,
//       // Typeahead API with authentication
//       linkedinAuth.isAuthenticated ? `https://www.linkedin.com/voyager/api/voyagerAutocompleteGeoGraphicalLocationSearch?query=${encodeURIComponent(location)}&count=10&start=0` : null,
//       // Job search location typeahead
//       `https://www.linkedin.com/voyager/api/typeahead/searchQueries?q=universalSearch&query=${encodeURIComponent(location)}&types=List(GEO)`
//     ].filter(Boolean);
    
//     for (const apiUrl of apiUrls) {
//       try {
//         console.log(`🌐 Trying LinkedIn API: ${apiUrl.substring(0, 100)}...`);
        
//         const headers = {
//           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
//           'Accept': 'application/vnd.linkedin.normalized+json+2.1',
//           'Accept-Language': 'en-US,en;q=0.9',
//           'Accept-Encoding': 'gzip, deflate, br',
//           'Referer': 'https://www.linkedin.com/jobs',
//           'X-Requested-With': 'XMLHttpRequest'
//         };
        
//         // Add authentication headers if available
//         if (linkedinAuth.isAuthenticated) {
//           headers['Csrf-Token'] = linkedinAuth.jsessionid;
//           headers['Cookie'] = `JSESSIONID="${linkedinAuth.jsessionid}"; li_at=${linkedinAuth.li_at}`;
//         }
        
//         const response = await axios.get(apiUrl, { 
//           headers, 
//           timeout: 15000,
//           validateStatus: function (status) {
//             return status >= 200 && status < 400;
//           }
//         });
        
//         if (response.data) {
//           const data = response.data;
          
//           // Check different response formats
//           let locations = [];
//           if (data.data && data.data.elements) {
//             locations = data.data.elements;
//           } else if (data.elements) {
//             locations = data.elements;
//           } else if (data.typeaheadResults) {
//             locations = data.typeaheadResults;
//           }
          
//           if (locations.length > 0) {
//             console.log(`✅ Found ${locations.length} location suggestions from LinkedIn API`);
            
//             const results = [];
//             for (const loc of locations) {
//               let geoId = null;
              
//               // Try different ways to extract geoId
//               if (loc.entityUrn) {
//                 geoId = extractGeoIdFromUrn(loc.entityUrn);
//               } else if (loc.urn) {
//                 geoId = extractGeoIdFromUrn(loc.urn);
//               } else if (loc.geoId) {
//                 geoId = loc.geoId;
//               }
              
//               if (geoId) {
//                 results.push({
//                   name: loc.title?.text || loc.displayName || loc.text || location,
//                   geoId: geoId,
//                   subtext: `${loc.subtitle?.text || loc.subline || ''} (LinkedIn API)`.trim()
//                 });
//               }
//             }
            
//             if (results.length > 0) {
//               return results;
//             }
//           }
//         }
        
//       } catch (apiError) {
//         console.log(`⚠️ LinkedIn API failed: ${apiError.message}`);
//         continue;
//       }
//     }
    
//     // Fallback: Try regular job search pages
//     const searchUrls = [
//       `https://www.linkedin.com/jobs/search?keywords=&location=${encodeURIComponent(location)}`,
//       `https://www.linkedin.com/jobs/search?location=${encodeURIComponent(location)}`,
//       `https://www.linkedin.com/jobs/search?keywords=software&location=${encodeURIComponent(location)}`
//     ];
    
//     const searchHeaders = {
//       'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
//       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
//       'Accept-Language': 'en-US,en;q=0.5',
//       'Accept-Encoding': 'gzip, deflate, br',
//       'DNT': '1',
//       'Connection': 'keep-alive',
//       'Upgrade-Insecure-Requests': '1'
//     };
    
//     for (const searchUrl of searchUrls) {
//       try {
//         console.log(`🌐 Trying search page: ${searchUrl}`);
        
//         const response = await axios.get(searchUrl, { 
//           headers: searchHeaders, 
//           timeout: 20000,
//           maxRedirects: 10,
//           validateStatus: function (status) {
//             return status >= 200 && status < 400;
//           }
//         });
        
//         if (response.data) {
//           const html = response.data;
          
//           // Enhanced patterns to find geoId in LinkedIn's HTML
//           const patterns = [
//             // Direct geoId patterns
//             /"geoId":\s*"?(\d+)"?/g,
//             /"geoId":"(\d+)"/g,
//             /geoId["\s]*[:=]["\s]*(\d+)/gi,
            
//             // LinkedIn URN patterns  
//             /urn:li:fsd_geo:(\d+)/g,
//             /urn:li:geo:(\d+)/g,
//             /urn:li:fs_geo:(\d+)/g,
            
//             // URL parameter patterns
//             /[?&]geoId=(\d+)/g,
//           ];
          
//           for (const pattern of patterns) {
//             let match;
//             while ((match = pattern.exec(html)) !== null) {
//               const geoId = match[1];
//               if (geoId && geoId.length >= 6) {
//                 console.log(`✅ Found LinkedIn geoId for "${location}": ${geoId}`);
                
//                 return [{
//                   name: location,
//                   geoId: geoId,
//                   subtext: `LinkedIn geoId extracted from search page`,
//                 }];
//               }
//             }
//           }
//         }
        
//       } catch (error) {
//         console.log(`⚠️ Failed to fetch ${searchUrl}: ${error.message}`);
//         continue;
//       }
//     }
    
//     console.log(`⚠️ Could not extract geoId from LinkedIn for "${location}"`);
//     return [];
    
//   } catch (error) {
//     console.log(`⚠️ LinkedIn search failed: ${error.message}`);
//     return [];
//   }
// }

// function extractGeoIdFromUrn(urn) {
//   if (!urn) return null;
  
//   // Try different LinkedIn URN patterns
//   const patterns = [
//     /urn:li:fsd_geo:(\d+)/,
//     /urn:li:geo:(\d+)/,
//     /urn:li:fs_geo:(\d+)/,
//     /urn:li:fsdGeo:(\d+)/,
//     /fsd_geo:(\d+)/,
//     /geo:(\d+)/
//   ];
  
//   for (const pattern of patterns) {
//     const match = urn.match(pattern);
//     if (match && match[1]) {
//       return match[1];
//     }
//   }
  
//   return null;
// }

// async function getLocationGeoId(location) {
//   if (!location) return null;
  
//   const locationLower = location.toLowerCase().trim();
  
//   // First try dynamic LinkedIn location search
//   console.log(`🔍 Searching LinkedIn for location: "${location}"`);
//   const linkedinLocations = await searchLinkedInLocations(location);
  
//   if (linkedinLocations.length > 0) {
//     if (linkedinLocations.length === 1) {
//       const loc = linkedinLocations[0];
//       console.log(`🌍 Found exact match: "${loc.name}" (${loc.geoId})`);
//       return loc.geoId;
//     } else {
//       // Multiple matches - let user choose
//       console.log(`🌍 Found ${linkedinLocations.length} possible locations:`);
//       linkedinLocations.forEach((loc, i) => {
//         console.log(`   ${i + 1}. ${loc.name}${loc.subtext ? ` - ${loc.subtext}` : ''} (geoId: ${loc.geoId})`);
//       });
      
//       const rl = require('readline').createInterface({
//         input: process.stdin,
//         output: process.stdout
//       });
      
//       try {
//         const choice = await new Promise(resolve => {
//           rl.question(`Please select location (1-${linkedinLocations.length}): `, resolve);
//         });
        
//         const index = parseInt(choice) - 1;
//         if (index >= 0 && index < linkedinLocations.length) {
//           const selectedLoc = linkedinLocations[index];
//           console.log(`✅ Selected: "${selectedLoc.name}" (${selectedLoc.geoId})`);
//           return selectedLoc.geoId;
//         }
//       } finally {
//         rl.close();
//       }
//     }
//   }
  
//   // Fallback to hardcoded mappings
//   console.log(`🔄 Falling back to hardcoded mappings for "${location}"`);
  
//   // Direct lookup in hardcoded mappings
//   if (LOCATION_GEOIDS[locationLower]) {
//     console.log(`🌍 Found in fallback: "${location}": ${LOCATION_GEOIDS[locationLower]}`);
//     return LOCATION_GEOIDS[locationLower];
//   }
  
//   // Partial match lookup in hardcoded mappings
//   for (const [key, geoId] of Object.entries(LOCATION_GEOIDS)) {
//     if (locationLower.includes(key) || key.includes(locationLower)) {
//       console.log(`🌍 Partial match in fallback: "${location}" -> "${key}": ${geoId}`);
//       return geoId;
//     }
//   }
  
//   console.log(`⚠️  No geoId found for "${location}", using default US`);
//   return LOCATION_GEOIDS['united states']; // Final fallback
// }


// // Query constructor
// function Query(queryObj) {
//   this.keyword = queryObj.keyword?.trim() || "";
//   this.location = queryObj.location?.trim() || "";
//   this.geoId = null; // Will be set async during getJobs()
//   this.dateSincePosted = queryObj.dateSincePosted || "";
//   this.jobType = queryObj.jobType || "";
//   this.remoteFilter = queryObj.remoteFilter || "";
//   this.salary = queryObj.salary || "";
//   this.experienceLevel = queryObj.experienceLevel || "";
//   this.sortBy = queryObj.sortBy || "";
//   this.limit = Number(queryObj.limit) || 25;
//   this.page = parseInt(queryObj.page) || 0;
//   this.has_verification = queryObj.has_verification || false;
//   this.under_10_applicants = queryObj.under_10_applicants || false;
// }

// // Query prototype methods
// Query.prototype.getDateSincePosted = function () {
//   const dateRange = {
//     "past month": "r2592000",
//     "past week": "r604800",
//     "24hr": "r86400",
//   };
//   return dateRange[this.dateSincePosted.toLowerCase()] || "";
// };

// Query.prototype.getExperienceLevel = function () {
//   const experienceRange = {
//     internship: "1",
//     "entry level": "2",
//     associate: "3",
//     senior: "4",
//     director: "5",
//     executive: "6",
//   };
//   return experienceRange[this.experienceLevel.toLowerCase()] || "";
// };

// Query.prototype.getJobType = function () {
//   const jobTypeRange = {
//     "full time": "F",
//     "full-time": "F",
//     "part time": "P",
//     "part-time": "P",
//     contract: "C",
//     temporary: "T",
//     volunteer: "V",
//     internship: "I",
//   };
//   return jobTypeRange[this.jobType.toLowerCase()] || "";
// };

// Query.prototype.getRemoteFilter = function () {
//   const remoteFilterRange = {
//     "on-site": "1",
//     "on site": "1",
//     remote: "2",
//     hybrid: "3",
//   };
//   return remoteFilterRange[this.remoteFilter.toLowerCase()] || "";
// };

// Query.prototype.getSalary = function () {
//   const salaryRange = {
//     40000: "1",
//     60000: "2",
//     80000: "3",
//     100000: "4",
//     120000: "5",
//   };
//   return salaryRange[this.salary] || "";
// };

// Query.prototype.getHasVerification = function () {
//   return this.has_verification ? "true" : "false";
// };

// Query.prototype.getUnder10Applicants = function () {
//   return this.under_10_applicants ? "true" : "false";
// };

// Query.prototype.getPage = function () {
//   const pageNum = isNaN(this.page) ? 0 : this.page;
//   return pageNum * 25;
// };

// Query.prototype.url = function (start) {
//   // Use exact format from Stack Overflow example
//   let queryString = `(origin:JOB_SEARCH_PAGE_SEARCH_BUTTON`;
  
//   if (this.keyword) {
//     queryString += `,keywords:${this.keyword}`;
//   }
  
//   if (this.geoId) {
//     queryString += `,locationUnion:(geoId:${this.geoId})`;
//   }
  
//   queryString += ')';
  
//   // Manually build params exactly as shown in Stack Overflow
//   const params = {
//     decorationId: 'com.linkedin.voyager.dash.deco.jobs.search.JobSearchCardsCollection-210',
//     q: 'jobSearch',
//     query: queryString,
//     count: 25,
//     start: start + this.getPage()
//   };
  
//   // Manual param encoding as shown in Stack Overflow
//   const paramString = Object.entries(params)
//     .map(([key, value]) => `${key}=${value}`)
//     .join('&');
  
//   return `https://www.linkedin.com/voyager/api/voyagerJobsDashJobCards?${paramString}`;
// };

// Query.prototype.getJobs = async function () {
//   let allJobs = [];
//   let start = 0;
//   const BATCH_SIZE = 25;
//   let hasMore = true;
//   let consecutiveErrors = 0;
//   const MAX_CONSECUTIVE_ERRORS = 3;
  
//   try {
//     // Ensure we have LinkedIn authentication
//     const isAuthenticated = await ensureAuthentication();
//     if (!isAuthenticated) {
//       throw new Error('LinkedIn authentication required');
//     }
    
//     // Get geoId for location
//     if (this.location && !this.geoId) {
//       this.geoId = await getLocationGeoId(this.location);
//     }
    
//     console.log(this.url(0));
//     console.log(this.getCacheKey());
    
//     // Check cache first
//     const cacheKey = this.getCacheKey();
//     const cachedJobs = cache.get(cacheKey);
//     if (cachedJobs) {
//       console.log("Returning cached results");
//       return cachedJobs;
//     }

//     while (hasMore) {
//       try {
//         const jobs = await this.fetchJobBatch(start);

//         if (!jobs || jobs.length === 0) {
//           hasMore = false;
//           break;
//         }

//         allJobs.push(...jobs);
//         console.log(`Fetched ${jobs.length} jobs. Total: ${allJobs.length}`);

//         if (this.limit && allJobs.length >= this.limit) {
//           allJobs = allJobs.slice(0, this.limit);
//           break;
//         }

//         // Reset error counter on successful fetch
//         consecutiveErrors = 0;
//         start += BATCH_SIZE;

//         // Add reasonable delay between requests
//         await delay(2000 + Math.random() * 1000);
//       } catch (error) {
//         consecutiveErrors++;
//         console.error(
//           `Error fetching batch (attempt ${consecutiveErrors}):`,
//           error.message
//         );

//         if (consecutiveErrors >= MAX_CONSECUTIVE_ERRORS) {
//           console.log("Max consecutive errors reached. Stopping.");
//           break;
//         }

//         // Exponential backoff
//         await delay(Math.pow(2, consecutiveErrors) * 1000);
//       }
//     }

//     // No filtering needed - LinkedIn will return location-appropriate results
//     let filteredJobs = allJobs;

//     // Cache results if we got any
//     if (filteredJobs.length > 0) {
//       cache.set(this.getCacheKey(), filteredJobs);
//     }

//     return filteredJobs;
//   } catch (error) {
//     console.error("Fatal error in job fetching:", error);
//     throw error;
//   }
// };

// Query.prototype.fetchJobBatch = async function (start) {
//   const headers = {
//     'Accept': 'application/vnd.linkedin.normalized+json+2.1',
//     'Accept-Language': 'en-US,en;q=0.9',
//     'Accept-Encoding': 'gzip, deflate, br',
//     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
//     'Referer': 'https://www.linkedin.com/jobs',
//     'X-Requested-With': 'XMLHttpRequest',
//     'Csrf-Token': linkedinAuth.jsessionid,
//     'Cookie': `JSESSIONID="${linkedinAuth.jsessionid}"; li_at=${linkedinAuth.li_at}`,
//     'Cache-Control': 'no-cache'
//   };

//   try {
//     const response = await axios.get(this.url(start), {
//       headers,
//       validateStatus: function (status) {
//         return status === 200;
//       },
//       timeout: 15000,
//     });

//     return parseVoyagerJobList(response.data);
//   } catch (error) {
//     console.log('Response status:', error.response?.status);
//     console.log('Response data:', error.response?.data);
    
//     if (error.response?.status === 429) {
//       throw new Error("Rate limit reached");
//     }
//     if (error.response?.status === 401 || error.response?.status === 403) {
//       throw new Error("Authentication failed - please check your LinkedIn cookies");
//     }
//     throw error;
//   }
// };

// function parseJobList(jobData) {
//   try {
//     const $ = cheerio.load(jobData);
//     const jobs = $("li");

//     return jobs
//       .map((index, element) => {
//         try {
//           const job = $(element);
//           const position = job.find(".base-search-card__title").text().trim();
//           const company = job.find(".base-search-card__subtitle").text().trim();
//           const location = job.find(".job-search-card__location").text().trim();
//           const dateElement = job.find("time");
//           const date = dateElement.attr("datetime");
//           const salary = job
//             .find(".job-search-card__salary-info")
//             .text()
//             .trim()
//             .replace(/\s+/g, " ");
//           const jobUrl = job.find(".base-card__full-link").attr("href");
//           const companyLogo = job
//             .find(".artdeco-entity-image")
//             .attr("data-delayed-url");
//           const agoTime = job.find(".job-search-card__listdate").text().trim();

//           // Only return job if we have at least position and company
//           if (!position || !company) {
//             return null;
//           }

//           return {
//             position,
//             company,
//             location,
//             date,
//             salary: salary || "Not specified",
//             jobUrl: jobUrl || "",
//             companyLogo: companyLogo || "",
//             agoTime: agoTime || "",
//           };
//         } catch (err) {
//           console.warn(`Error parsing job at index ${index}:`, err.message);
//           return null;
//         }
//       })
//       .get()
//       .filter(Boolean);
//   } catch (error) {
//     console.error("Error parsing job list:", error);
//     return [];
//   }
// }

// function parseVoyagerJobList(data) {
//   try {
//     const jobs = [];
    
//     // LinkedIn Voyager API returns data in data.data.elements, not data.elements
//     const elements = data?.data?.elements;
//     const included = data?.included || [];
    
//     // console.log('🔍 Found elements:', elements?.length || 0);
//     // console.log('🔍 Found included items:', included.length);
    
//     if (!elements || elements.length === 0) {
//       console.log('No job elements found in response');
//       return jobs;
//     }

//     // Create lookup map for included items
//     const includedMap = {};
//     for (const item of included) {
//       if (item.entityUrn) {
//         includedMap[item.entityUrn] = item;
//       }
//     }
    
//     for (const element of elements) {
//       try {
//         // Get job posting card reference from jobCardUnion
//         const jobPostingCardUrn = element?.jobCardUnion?.['*jobPostingCard'];
//         if (!jobPostingCardUrn) continue;
        
//         // Find the job data in included items
//         const jobData = includedMap[jobPostingCardUrn];
//         if (!jobData) continue;
        
//         // Debug first job data structure (commented out)
//         // if (jobs.length === 0) {
//         //   console.log('🔍 Job data keys:', Object.keys(jobData));
//         //   console.log('🔍 Job data sample:', JSON.stringify(jobData, null, 2).substring(0, 800) + '...');
//         // }
        
//         // Extract job URL from cardActionV2Union
//         let jobUrl = '';
//         if (jobData.cardActionV2Union?.primaryActionV2?.url) {
//           jobUrl = jobData.cardActionV2Union.primaryActionV2.url;
//         } else if (jobData.primaryActionV2Union?.primaryActionV2?.url) {
//           jobUrl = jobData.primaryActionV2Union.primaryActionV2.url;
//         }
        
//         const job = {
//           position: jobData.title?.text || 'Unknown Position',
//           company: jobData.primaryDescription?.text || 'Unknown Company',
//           location: jobData.secondaryDescription?.text || 'Unknown Location',
//           date: jobData.listedDate || null,
//           salary: jobData.salaryRange?.text || 'Not specified',
//           jobUrl: jobUrl,
//           companyLogo: '',
//           agoTime: jobData.listedDate ? new Date(jobData.listedDate).toDateString() : ''
//         };

//         // Only add jobs with basic required info
//         if (job.position !== 'Unknown Position' && job.company !== 'Unknown Company') {
//           jobs.push(job);
//         }
//       } catch (err) {
//         console.warn('Error parsing individual job:', err.message);
//       }
//     }

//     return jobs;
//   } catch (error) {
//     console.error('Error parsing Voyager job list:', error);
//     return [];
//   }
// }

// // Export additional utilities for testing and monitoring
// module.exports.JobCache = JobCache;
// module.exports.clearCache = () => cache.clear();
// module.exports.getCacheSize = () => cache.cache.size;
// module.exports.setAuth = setAuthentication;


const cheerio = require("cheerio");
const axios = require("axios");
const randomUseragent = require("random-useragent");
const readline = require('readline');
const { Builder, By, until, Key } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const puppeteer = require('puppeteer');


// Helper to normalize user-provided location strings
function normalize(str) {
  return (str || "")
    .toLowerCase()
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .replace(/\s+/g, ' ')
    .trim();
}

// LinkedIn Authentication Storage
let linkedinAuth = {
  jsessionid: null,
  li_at: null,
  isAuthenticated: false
};

// Function to set authentication directly (for testing)
function setAuthentication(jsessionid, li_at) {
  linkedinAuth.jsessionid = jsessionid.replace(/"/g, '');
  linkedinAuth.li_at = li_at;
  linkedinAuth.isAuthenticated = true;
  console.log('✅ Authentication set directly');
}

// Utility functions
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// Cache implementation
class JobCache {
  constructor() {
    this.cache = new Map();
    this.TTL = 1000 * 60 * 60; // 1-hour TTL
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

// Generate a unique cache key based on the query parameters
Query.prototype.getCacheKey = function () {
  return `${this.url(0)}_limit:${this.limit}`;
};

// Main query function
module.exports.query = async (queryObject) => {
  const query = new Query(queryObject);
  
  // Resolve geoId BEFORE generating cache key or URLs
  if (query.flag_dynamic_location && !query.geoId) {
    try {
      let location = query.locationQuery();
      let city = query.city;
      let country = query.country;
      if (!!city) location += (location ? ', ' : '') + city;
      
      const geoId = await getLocationGeoId(location || country || city);
      if (geoId) {
        query.geoId = geoId;
        console.log(`✅ Using geoId=${geoId} for location="${location || country || city}"`);
      }
    } catch (e) {
      console.warn('⚠️ Dynamic geoId lookup failed:', e?.message || e);
    }
  }
  
  const cacheKey = query.getCacheKey();
  // Check if the result is in the cache
  let cachedResult = cache.get(cacheKey);
  if (cachedResult) {
    console.log("Cache hit for:", cacheKey);
    return cachedResult;
  }
  console.log('Cache missed:', cacheKey);
  console.log('Query ' + query.url(0));

  const getUrls = (count) => {
    let urls = [query.url(0)];
    let start = 25;
    while (count > 25) {
      urls.push(query.url(start));
      count -= 25;
      start += 25;
    }
    return urls;
  }

  return new Promise((resolve, reject) => {
    const scrapPromises = getUrls(query.limit).map(url => scrapPageAndExtractData(query.withUrl(url)));
    Promise.all(scrapPromises).then(results => {
      const output = results
        .reduce((res, i) => [...res, ...i], [])
        .filter(s => s && s.company && s.company.name);

      // Save the result in the internal cache
      cache.set(cacheKey, output);
      resolve(output);
    }).catch(reject);
  })
}

// Function to format job details text
const formatJobText = function (item, skipDate = false) {
  let details = '';
  let date = item.posted_date || item.listed_at;
  if (!skipDate) {
    details += `📅 Posted Date: ${date || 'N/A'}\n`;
  }
  details += `🧰 Job Type: ${item.formatted_job_type || item.job_type || 'N/A'}\n`;
  details += `🏢 Workplace: ${item.formatted_workplace || item.workplace || 'N/A'}\n`;
  details += `📍 Location: ${item.city || item.location || 'N/A'}\n`;
  details += `📎 Job URL: ${item.link || 'N/A'}\n`;

  return details;
};

// Function to replace placeholders in a message template
const replacePlaceholders = function (template, item) {
  const templates = {
    "%details%": formatJobText(item),
    "%company_name%": item.company ? item.company.name : "N/A",
    "%job_title%": item.title || "N/A",
    "%workplace%": item.formatted_workplace || item.workplace || "N/A",
    "%job_type%": item.formatted_job_type || item.job_type || "N/A",
    "%country%": item.country || "N/A",
    "%city%": item.city || "N/A",
    "%temp%": item.temp || "",
    "%internship%": item.internship || "",
    "%remote%": item.remote || "",
    "%link%": item.link || "N/A",
    "%keywords%": item.keywords ? item.keywords.join(", ") : "N/A",
    "%applinks%": item.applinks || 'N/A',
    "%job_format%": item.job_format || "N/A",
    "%job_position%": Array.isArray(item.title) ? item.title.join(", ") : (item.title || "N/A"),
  };

  return Object.keys(templates).reduce((result, placeholder) => {
    return result.replace(new RegExp(placeholder, 'g'), templates[placeholder]);
  }, template);
};

// Function to send a job message to Telegram
const sendJobMessage = async function (telegram, item, chat, message) {
  const finalMessage = replacePlaceholders(message, item);
  const result = await telegram.sendMessage(chat, finalMessage, { parse_mode: 'Markdown' });
  return result;
};

const escapeXML = that => that.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const ul = (n, c, i = '\t') => `<ul>\n${c.map((a) => `${i}<li><a href="${escapeXML(a[1])}">${escapeXML(a[0])}</a></li>`).join('\n')}\n</ul>`;
const hN = (n, c) => `<h${n}>${c}</h${n}>`;
const link = (t, u) => `<a href="${escapeXML(u)}">${escapeXML(t)}</a>`
const cleanText = function (that) { return (that || '').replace(new RegExp(String.fromCharCode(10), 'g'), ' ') };

function cleanString(input) {
  return input.replace(/[^\x20-\x7E\n\r]+/g, "");
}

function formatDate(timestamp) {
  let date = new Date(timestamp)
  let dateOptions = { year: "numeric", month: "2-digit", day: "2-digit" }
  return date ? date.toLocaleDateString('en-GB', dateOptions) : undefined;
}

function processDate(dateString) {
  if (dateString && dateString.trim() !== "") {
    const date = new Date(dateString);
    if (!isNaN(date.getTime())) {
      return date;
    }
  }
  return null;
}

function readMoreDescription(description, title, companyName) {
  const descriptionItem = `TITLE\n${title}\nCompany name: \n${companyName}\n${description}`;
  return `${descriptionItem}`;
}

// Array of hosts to try
const hosts = [
  "www.linkedin.com",          // Main domain
  "de.linkedin.com",           // German domain
  "fr.linkedin.com",           // French domain
  "uk.linkedin.com",           // UK domain
  "ca.linkedin.com",           // Canadian domain
  "in.linkedin.com",           // Indian domain
  "es.linkedin.com",           // Spanish domain
  "it.linkedin.com",           // Italian domain
  "br.linkedin.com",           // Brazilian domain
  "nl.linkedin.com",           // Dutch domain
  "au.linkedin.com",           // Australian domain
  "jp.linkedin.com"            // Japanese domain
];

const PATH = "jobs-guest/jobs/api/seeMoreJobPostings/search"
const linkedinIds = [];

function mapDateSincePosted(s) {
  if (!s) return 'r86400';
  const n = s.toLowerCase();
  if (n.includes('past 24') || n.includes('day')) return 'r86400';
  if (n.includes('week')) return 'r604800';
  if (n.includes('month')) return 'r2592000';
  return 'r86400';
}

function Query(queryObject) {
  // map inputs from both old and your test.js shape
  const location = queryObject.location || '';
  const keyword = queryObject.keyword || queryObject.keywords || queryObject.title || queryObject.job_position || '';
  const dateSincePosted = queryObject.dateSincePosted || '';
  const jobType = queryObject.jobType || queryObject.job_format || '';
  const remoteFilter = queryObject.remoteFilter || queryObject.workplace || '';

  this.title = keyword || '';
  this.country = queryObject.country || location || 'United States';
  this.company = queryObject.company || queryObject.company_name || '';
  this.city = queryObject.city || '';
  this.field = queryObject.field || '';
  this.workplace = remoteFilter || 'remote';
  this.workplaceBoolean = queryObject.workplaceBoolean || false;
  this.experienceMultiple = queryObject.experienceMultiple || false;
  this.link = queryObject.link || '';
  this.applinks = queryObject.applinks || '';
  this.message = queryObject.message || '';
  this.job_format = jobType || 'full time';
  this.resultLimit = queryObject.limit || 100;
  this.limit = this.resultLimit;
  this.filter_timePostedRange = queryObject.filter_timePostedRange || mapDateSincePosted(dateSincePosted);
  this.buttonCount = queryObject.buttonCount || 2;
  this.remote = queryObject.remote || '';
  this.temp = queryObject.temp || '';
  this.internship = queryObject.internship || '';
  this.jobType = jobType || '';
  this.titleArray = Array.isArray(keyword) ? keyword : [keyword || ''];
  this.keywords = queryObject.keywords || [];
  this.filter_outApplicantCount = queryObject.filter_outApplicantCount || '';
  this.hide_duplicated_jobs = queryObject.hide_duplicated_jobs !== undefined ? queryObject.hide_duplicated_jobs : true;
  this.sendMessage = queryObject.sendMessage || false;
  this.title_or_company = queryObject.title_or_company || false;
  this.flag_dynamic_host = queryObject.flag_dynamic_host !== undefined ? queryObject.flag_dynamic_host : true;
  this.flag_dynamic_location = queryObject.flag_dynamic_location !== undefined ? queryObject.flag_dynamic_location : true;
  this.flag_regional_host = queryObject.flag_regional_host !== undefined ? queryObject.flag_regional_host : true;
  this.flag_sms = queryObject.flag_sms || false;
  this.disableCompanyFilter = queryObject.disableCompanyFilter || false;
  this.disableJobFilter = queryObject.disableJobFilter || false;
  this.forceSearchUrl = queryObject.forceSearchUrl || false;
  this.companyList = Array.isArray(queryObject.company_name) ? queryObject.company_name : (queryObject.company_name ? [queryObject.company_name] : []);
  this.companyRatingThreshold = queryObject.companyRatingThreshold || null;
}

Query.prototype.getWorkplaceFilter = function () {
  if (!this.workplaceBoolean) {
    return '';
  }
  const filterMap = {
    remote: "f_WT=2",
    hybrid: "f_WT=3",
    onsite: "f_WT=1",
  };

  if (!this.workplace) {
    return '';
  }

  const selectedFilter = filterMap[this.workplace];

  if (selectedFilter) {
    return selectedFilter;
  }

  return '';
};

Query.prototype.getCompanyConstraint = function () {
  let that = this.company;
  if (that && that.trim()) return encodeURIComponent(`"${that}"`);
  if (this.companyList.length > 0) return "(" + this.companyList
    .map(c => `"${c}"`)
    .map(encodeURIComponent)
    .join("+OR+") + ")";
  return '';
}

Query.prototype.getKeyWord = function () {
  let keyword = this.keywords;
  let input;
  if (!keyword.length) {
    input = [];
  } else if (!!keyword && typeof keyword === "string") {
    input = keyword.split(" ").map((el) => el.trim());
  } else {
    input = keyword;
  }

  return input;
}

Query.prototype.getSalariesLinkedIn = function () {
  let that = this.salary;
  if (that) {
    let out = Array.isArray(that) ? that : that.split(' ');
    const code = {
      '1000': 'r,1',
      '2000': 'r,2',
      '3000': 'r,3',
      '4000': 'r,4',
      '10000': 'r,10',
      '20000': 'r,20',
      '30000': 'r,30',
      '40000': 'r,40',
      '100k': 'r,100',
      '200k': 'r,200',
      '300k': 'r,300',
      '400k': 'r,400',
    };
    let res = out.map(v => code[v.toLowerCase()]).filter(Boolean);
    if (res.length > 0) return "f_SB2=" + res.map(encodeURIComponent).join(",");
  }
  return '';
}

Query.prototype.getJobTypeRange = function () {
  const jobTypeRange = {
    fulltime: "F",
    "full time": "F",
    parttime: "P",
    "part time": "P",
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
  return remoteFilterRange[(this.workplace || '').toLowerCase()] || "";
};

Query.prototype.url = function (start) {
  console.log("Query: ", JSON.stringify(this, null, 2));
  console.log(JSON.stringify({
    details: 'Query from url',
    title: this.title,
    company: this.company,
    title_or_company: !!this.title_or_company,
    titleArray: this.titleArray,
    country: this.country,
    city: this.city,
    job_format: this.job_format,
  }, null, 2));

  const host = this.host();
  const base = host.startsWith('http') ? host : `https://${host}`;

  const params = [
    this.titleQuery() ? `keywords=${encodeURIComponent(this.titleQuery().replace(/"/g, ''))}` : null,
    this.locationQuery() ? `location=${encodeURIComponent(this.locationQuery())}` : null,
    this.geoId ? `geoId=${this.geoId}` : null,
    `f_TPR=${this.filter_timePostedRange}`,
    this.getRemoteFilter() ? `f_WT=${this.getRemoteFilter()}` : null,
    this.getJobTypeFilter(),
    `start=${start || 0}`,
    `count=25`
  ].filter(Boolean);
  
  return `${base}/${PATH}?${params.join('&')}`
};

Query.prototype.withUrl = function (url) {
  // preserve prototype so later methods (like locationQuery) still exist
  const r = Object.create(Object.getPrototypeOf(this));
  Object.assign(r, this);
  r.url = () => url;
  return r;
}

Query.prototype.locationQuery = function () {
  let that = this.country || this.city;
  if (!that) that = this.country;
  if (!!that) return that;
  return '';
}

Query.prototype.titleQuery = function () {
  let that = this.title || this.titleArray;
  if (!!that) {
    if (Array.isArray(that)) {
      return that.map((el) => `"${el}"`).join(" OR ");
    } else {
      return `"${that}"`;
    }
  }
  return '';
}

Query.prototype.companyQuery = function () {
  if (this.title_or_company) {
    let that = this.company || this.companyList;
    if (!!that) {
      if (Array.isArray(that)) {
        return that.map((el) => `"${el}"`).join(" OR ");
      } else {
        return `"${that}"`;
      }
    }
  }

  return ''
};

Query.prototype.host = function () {
  // Always use www.linkedin.com to avoid bot-protected regional domains
  return 'www.linkedin.com';
}

Query.prototype.getBenefitsFilter = function () {
  let that = this.benefits;
  if (that) {
    let out = Array.isArray(that) ? that : that.split(' ');
    const code = {
      1: 'f_E=1%2C2%2C3',
      2: 'f_E=2',
      3: 'f_E=3'
    };
    let res = out.map(v => code[parseInt(v)]).filter(Boolean);
    if (res.length > 0) return res.join('&');
  }
  return '';
}

Query.prototype.getJobTypeFilter = function () {
  let jobTypeRange = {
    'full time': 'F',
    'part time': 'P',
    'contract': 'C',
    'temporary': 'T',
    'volunteer': 'V',
    'internship': 'I',
  };
  let that = this.job_format;
  if (that) {
    let res = jobTypeRange[that.toLowerCase()];
    if (!!res) return "f_JT=" + res;
  }
  return '';
}

Query.prototype.getExperienceRestrictionFilter = function () {
  let experienceMap = {
    1: '1%2C2', // Entry level
    2: '2',     // Associate
    3: '3%2C4', // Mid-Senior level
    4: '4',     // Director
    5: '5%2C6', // Executive
  };
  let that = this.experienceMultiple;
  if (that) {
    let out = Array.isArray(that) ? that : that.split(' ');
    let res = out.map(v => experienceMap[parseInt(v, 10)]).filter(Boolean);
    if (res.length > 0) return "f_E=" + res.join("%2C");
  }
  return '';
}

Query.prototype.getIndustryFilter = function () {
  let industryMap = {
    t: 'I',
    st: 'Sh',
    rec: 'Sh',
    hr: 'Sh',
    m: 'I',
    i: 'I',
  };
  let that = this.industry;
  if (that) {
    let out = Array.isArray(that) ? that : that.split(' ');
    let res = out.map(v => industryMap[v.toLowerCase()]).filter(Boolean);
    if (res.length > 0) return "f_I=" + res.join("%2C");
  }
  return '';
}

function includesCityName(text, city) {
  if (!text || !city) return false;

  // Normalize both text and city for comparison
  const normalizedText = normalize(text);
  const normalizedCity = normalize(city);

  // Refined flexible matching using dynamic pattern construction
  const cityPatterns = [
    normalizedCity,                        // Exact city name (case-insensitive)
    normalizedCity.replace(/\s+/g, '[-\\s]?'), // Allow spaces or hyphens in city name
  ];

  // Check if any of the patterns matches the normalized text
  return cityPatterns.some(pattern =>
    new RegExp(`\\b${pattern}\\b`, 'i').test(normalizedText)
  );
}

function includesCountryName(text, country) {
  if (!text || !country) return false;
  const normalizedText = normalize(text);
  const normalizedCountry = normalize(country);
  return new RegExp(`\\b${normalizedCountry}\\b`, 'i').test(normalizedText);
}

function extractLinkedInJobId(url) {
  try {
    const match = url.match(/\/view\/(\d+)\//);
    return match ? match[1] : null;
  } catch (error) {
    console.error('Error extracting job ID:', error);
    return null;
  }
}

/**
 * Attempt to search LinkedIn for location information using multiple endpoints, with or without authentication.
 */
async function searchLinkedInLocations(location) {
  // The LinkedIn Voyager APIs are deprecated and require authentication
  // For now, we'll skip the API calls and rely on hardcoded mappings
  // To use the proper LinkedIn Geo API (https://api.linkedin.com/v2/geo/), 
  // you would need OAuth authentication, not session cookies
  
  console.log(`🔍 Searching LinkedIn for location: "${location}"`);
  
  // Skip API calls for now - they were returning 404s
  // Future improvement: implement OAuth authentication for LinkedIn Geo API
  
  return [];
}

/**
 * Try to parse the jobs list returned by LinkedIn's "see more" HTML endpoint.
 */
const parseVoyagerJobList = html => {
  try {
    const $ = cheerio.load(html);
    const jobs = [];

    $('li').each((index, element) => {
      let link = $(element).find('a').first().attr('href');
      let title = cleanText($(element).find('.base-search-card__title').text().trim());
      let company = cleanText($(element).find('.base-search-card__subtitle a, .base-search-card__subtitle').text().trim());
      let city = cleanText($(element).find('.job-search-card__location').text().trim());
      let listed_at = cleanText($(element).find('time').attr('datetime') || $(element).find('time').text().trim());

      // Extract LinkedIn job ID from the link
      const jobId = extractLinkedInJobId(link);

      if (!!title) {
        jobs.push({
          id: jobId || null,
          title: title,
          city: (city || '').trim(),
          link: link && link.startsWith('http') ? link : `https://www.linkedin.com${link}`,
          posted_date: listed_at,
          listed_at: listed_at,
          applinks: '',
          company: {
            name: (company || '').trim(),
          }
        });
      }
    });

    return jobs;
  } catch (error) {
    console.error('Error parsing Voyager job list:', error);
    return [];
  }
}

// ----------------------------------------------------------------------------
// DYNAMIC GEOLOCATION RESOLUTION
// ----------------------------------------------------------------------------

/**
 * Determine the appropriate LinkedIn geoId for a given location input.
 * Dynamic-first: LinkedIn API(s), OSM standardization retry, then hardcoded fallback.
 */
async function getLocationGeoId(location) {
  if (!location) return null;
  
  const original = location.trim();
  const locationLower = normalize(location);
  
  // Accept raw numeric geoIds
  if (/^\d{5,}$/.test(locationLower)) return locationLower;
  
  // First try dynamic LinkedIn location search
  console.log(`🔍 Searching LinkedIn for location: "${location}"`);
  const linkedinLocations = await searchLinkedInLocations(location);
  
  // If no match, standardize with OSM then retry LinkedIn once
  if (linkedinLocations.length === 0) {
    try {
      const osmResp = await axios.get('https://nominatim.openstreetmap.org/search', {
        params: { q: original, format: 'json', addressdetails: 1, limit: 1 },
        headers: { 'User-Agent': 'Mozilla/5.0' },
        timeout: 12000
      });
      if (Array.isArray(osmResp.data) && osmResp.data.length) {
        const addr = osmResp.data[0].address || {};
        const pieces = [
          addr.city || addr.town || addr.village || addr.municipality || (osmResp.data[0].display_name || '').split(',')[0],
          addr.state || addr.region || addr.county,
          addr.country
        ].filter(Boolean);
        const standardized = pieces.join(', ');
        const retry = await searchLinkedInLocations(standardized);
        if (retry.length) {
          const loc = retry[0];
          console.log(`🌍 Standardized via OSM -> "${standardized}", using "${loc.name}" (${loc.geoId})`);
          return loc.geoId;
        }
      }
    } catch (e) {
      console.warn('OSM standardization failed:', e?.message || e);
    }
  }
  
  if (linkedinLocations.length > 0) {
    if (linkedinLocations.length === 1) {
      const loc = linkedinLocations[0];
      console.log(`🌍 Found exact match: "${loc.name}" (${loc.geoId})`);
      return loc.geoId;
    } else {
      console.log(`📍 Multiple matches found for "${location}":`);
      linkedinLocations.forEach((loc, index) => {
        console.log(`${index + 1}. ${loc.name} (geoId: ${loc.geoId})`);
      });
      
      // Interactive selection if running in terminal
      const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
      });

      try {
        const choice = await new Promise(resolve => {
          rl.question(`Please select location (1-${linkedinLocations.length}): `, resolve);
        });
        
        const index = parseInt(choice) - 1;
        if (index >= 0 && index < linkedinLocations.length) {
          const selectedLoc = linkedinLocations[index];
          console.log(`✅ Selected: "${selectedLoc.name}" (${selectedLoc.geoId})`);
          return selectedLoc.geoId;
        }
      } finally {
        rl.close();
      }
    }
  }
  
  // Fallback to hardcoded mappings
  console.log(`🔄 Falling back to hardcoded mappings for "${location}"`);
  
  // Direct lookup in hardcoded mappings
  if (LOCATION_GEOIDS[locationLower]) {
    console.log(`🌍 Found in fallback: "${location}": ${LOCATION_GEOIDS[locationLower]}`);
    return LOCATION_GEOIDS[locationLower];
  }
  
  // Partial match lookup in hardcoded mappings
  for (const [key, geoId] of Object.entries(LOCATION_GEOIDS)) {
    if (locationLower.includes(key) || key.includes(locationLower)) {
      console.log(`🌍 Partial match in fallback: "${location}" -> "${key}": ${geoId}`);
      return geoId;
    }
  }
  
  // Default fallback if no match is found
  console.log(`⚠️ No match found. Defaulting to United States (103644278).`);
  return LOCATION_GEOIDS['united states'] || '103644278';
}

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
  'france': 'fr.linkedin.com',
  'français': 'fr.linkedin.com',
  'francais': 'fr.linkedin.com',
  'paris': 'fr.linkedin.com',
  'spain': 'es.linkedin.com',
  'españa': 'es.linkedin.com',
  'espana': 'es.linkedin.com',
  'madrid': 'es.linkedin.com',
  'italy': 'it.linkedin.com',
  'italia': 'it.linkedin.com',
  'rome': 'it.linkedin.com',
  'uk': 'uk.linkedin.com',
  'united kingdom': 'uk.linkedin.com',
  'england': 'uk.linkedin.com',
  'london': 'uk.linkedin.com',
  'canada': 'ca.linkedin.com',
  'toronto': 'ca.linkedin.com',
  'india': 'in.linkedin.com',
  'भारत': 'in.linkedin.com',
  'mumbai': 'in.linkedin.com',
  'bengaluru': 'in.linkedin.com',
  'brazil': 'br.linkedin.com',
  'brasil': 'br.linkedin.com',
  'são paulo': 'br.linkedin.com',
  'sao paulo': 'br.linkedin.com',
  'netherlands': 'nl.linkedin.com',
  'amsterdam': 'nl.linkedin.com',
  'australia': 'au.linkedin.com',
  'sydney': 'au.linkedin.com',
  'japan': 'jp.linkedin.com',
  '日本': 'jp.linkedin.com',
  'tokyo': 'jp.linkedin.com',
};

const LOCATION_GEOIDS = {
  "united states": "103644278",
  "germany": "101282230",
  "deutschland": "101282230",
  "france": "103644220",
  "india": "102713980",
  "united kingdom": "102257491",
  "uk": "102257491",
  "italy": "103350119",
  "spain": "105646813",
  "canada": "101174742",
  "australia": "101452733",
  "netherlands": "102890719",
  "brazil": "106057199",
  "japan": "103644525",
  "munich": "106430259",
  "muenchen": "106430259",
  "münchen": "106430259",
  "berlin": "106967730",
  "hamburg": "106867798",
  "cologne": "106499694",
  "köln": "106499694",
  "fürth": "106430259",
  "furth": "106430259",
  "nuremberg": "106430259",
  "nürnberg": "106430259",
  "bavaria": "101282230",
  "bayern": "101282230",
  "paris": "105015875",
  "madrid": "105646813",
  "rome": "103350119",
  "london": "102257491",
  "toronto": "101174742",
  "mumbai": "102713980",
  "bengaluru": "106506694",
  "são paulo": "106057199",
  "sao paulo": "106057199",
  "amsterdam": "102890719",
  "sydney": "101452733",
  "tokyo": "103644525"
};

// Heuristic to choose host based on country/city
function getHostFromLocation(country, city) {
  const normCountry = normalize(country);
  const normCity = normalize(city);

  if (COUNTRY_HOSTS[normCity]) {
    return COUNTRY_HOSTS[normCity]; // hostname only
  }
  if (COUNTRY_HOSTS[normCountry]) {
    return COUNTRY_HOSTS[normCountry]; // hostname only
  }
  return 'www.linkedin.com';
}

const scrapPageAndExtractData = query => {
  return new Promise(async (resolve, reject) => {
    let browser = null;
    
    try {
      let location = query.locationQuery();
      let city = query.city;
      let country = query.country;

      if (!!city) location += (location ? ', ' : '') + city;

      // Dynamic geoId resolution (now robust) - MUST happen before URL generation
      if (query.flag_dynamic_location && !query.geoId) {
        try {
          const geoId = await getLocationGeoId(location || country || city);
          if (geoId) {
            query.geoId = geoId;
            console.log(`✅ Using geoId=${geoId} for location="${location || country || city}"`);
          } else {
            console.warn('⚠️ Could not resolve geoId dynamically, continuing without geoId.');
          }
        } catch (e) {
          console.warn('⚠️ Dynamic geoId lookup failed:', e?.message || e);
        }
      }

      // Build LinkedIn jobs search URL
      const baseUrl = 'https://www.linkedin.com/jobs/search';
      const params = new URLSearchParams({
        keywords: query.titleQuery() ? query.titleQuery().replace(/"/g, '') : '',
        location: query.locationQuery() || '',
        ...(query.geoId && { geoId: query.geoId }),
        f_TPR: query.filter_timePostedRange,
        ...(query.getRemoteFilter() && { f_WT: query.getRemoteFilter() }),
        ...(query.getJobTypeFilter() && { f_JT: query.getJobTypeFilter().split('=')[1] })
      });
      
      const url = `${baseUrl}?${params.toString()}`;
      console.log(`🌐 Puppeteer URL: ${url}`);

      console.log(`🤖 Starting Puppeteer browser...`);
      
      // Launch browser with stealth options
      browser = await puppeteer.launch({
        headless: 'new',
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-blink-features=AutomationControlled',
          '--disable-extensions',
          '--disable-dev-shm-usage',
          '--disable-gpu',
          '--window-size=1920,1080',
          '--disable-web-security',
          '--allow-running-insecure-content'
        ],
        defaultViewport: { width: 1920, height: 1080 }
      });

      console.log(`✅ Browser started successfully`);
      const page = await browser.newPage();

      // Set user agent and other headers
      await page.setUserAgent(randomUseragent.getRandom() || 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');

      // Anti-detection measures
      await page.evaluateOnNewDocument(() => {
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        window.chrome = { runtime: {} };
      });

      console.log(`🌐 Navigating to LinkedIn...`);
      await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });
      console.log(`✅ Page loaded`);

      // Wait for page to load and add realistic delay
      await delay(2000 + Math.random() * 2000);

      // Wait for job cards to appear
      try {
        await page.waitForSelector('.job-search-card, .jobs-search-results__list-item', { timeout: 15000 });
        console.log(`✅ Job listings found on page`);
      } catch (e) {
        console.warn(`⚠️ No job listings found, page may not have loaded correctly`);
        // Take screenshot for debugging
        await page.screenshot({ path: 'linkedin-debug.png', fullPage: true });
        console.log(`📷 Debug screenshot saved as linkedin-debug.png`);
      }

      // Extract job data
      const jobs = await page.evaluate(() => {
        const jobs = [];
        const jobCards = document.querySelectorAll('.job-search-card, .jobs-search-results__list-item');
        
        jobCards.forEach(card => {
          try {
            const titleEl = card.querySelector('.base-search-card__title, .job-search-card__title a, .base-search-card__title a');
            const companyEl = card.querySelector('.base-search-card__subtitle, .job-search-card__subtitle a, .base-search-card__subtitle a');
            const locationEl = card.querySelector('.job-search-card__location');
            const linkEl = card.querySelector('.base-card__full-link, .job-search-card__title-link, .base-search-card__title a');
            const dateEl = card.querySelector('time');
            
            const title = titleEl ? titleEl.textContent.trim() : '';
            const company = companyEl ? companyEl.textContent.trim() : '';
            const location = locationEl ? locationEl.textContent.trim() : '';
            const link = linkEl ? linkEl.href : '';
            const date = dateEl ? (dateEl.getAttribute('datetime') || dateEl.textContent.trim()) : '';
            
            if (title && company) {
              jobs.push({
                id: link.match(/\/view\/(\d+)\//)?.[1] || null,
                title: title,
                city: location,
                link: link,
                posted_date: date,
                listed_at: date,
                applinks: '',
                company: {
                  name: company
                }
              });
            }
          } catch (e) {
            console.warn('Error parsing job card:', e);
          }
        });
        
        return jobs;
      });

      console.log(`🎯 Extracted ${jobs.length} jobs using Puppeteer`);
      
      // Add realistic delay before closing
      await delay(1000 + Math.random() * 1000);
      
      resolve(jobs);
      
    } catch (e) {
      console.warn('⚠️ Puppeteer scraping failed:', e?.message || e);
      resolve([]);
    } finally {
      if (browser) {
        try {
          await browser.close();
        } catch (e) {
          console.warn('⚠️ Error closing browser:', e.message);
        }
      }
    }
  });
}

// Export additional utilities for testing and monitoring
module.exports.JobCache = JobCache;
module.exports.clearCache = () => cache.clear();
module.exports.getCacheSize = () => cache.cache.size;
module.exports.setAuth = setAuthentication;

