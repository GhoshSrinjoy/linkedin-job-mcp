*"My AI found five openings before I finished my coffee. That's productivity !'"*

# 💼 LinkedIn Jobs MCP Server  

A Model Context Protocol (MCP) server that gives LLMs real-time job search powers — including LinkedIn queries, dynamic geocoding, and intelligent filtering.  
Think of it as your AI-powered recruiter that never sleeps (and actually reads the job description). 🤖  

🔗 **Repo:** https://github.com/GhoshSrinjoy/linkedin-job-mcp
📦 **NPM:** https://www.npmjs.com/package/linkedin-jobs-mcp

[![npm version](https://badge.fury.io/js/linkedin-jobs-mcp.svg)](https://www.npmjs.com/package/linkedin-jobs-mcp)
[![npm downloads](https://img.shields.io/npm/dm/linkedin-jobs-mcp.svg)](https://www.npmjs.com/package/linkedin-jobs-mcp)

---

## Executive Summary  

This MCP server lets AI models search for LinkedIn jobs, filter by location, experience, and salary, and return structured data in JSON format , perfect for autonomous agents, dashboards, or research tools.  

It’s designed to handle:  
- Smart geolocation (via OpenStreetMap)  
- Domain switching (EU/German LinkedIn variants)  
- Rate limiting and caching for performance  
- JSON responses for clean parsing  

Built with Node.js and focused on maintainability, extensibility, and responsible automation.  

---

## Business Problem  

Most LLMs can summarize résumés but can’t *find* you jobs.  
And job platforms like LinkedIn actively block automation through browser fingerprinting, bot detection, and API restrictions.  

This project provides a transparent, research-oriented framework for safe and compliant job data exploration , while educating developers on responsible scraping limits.  

**Why it matters:**  
- Manual searches don’t scale.  
- Official APIs are restricted or costly.  
- Businesses and researchers need structured access to job market data.  


## 🎯 Complete Feature List

### 🔌 Multiple Integration Methods

#### 1. **MCP Server for Claude Desktop** (`server.js`)
- ✅ Full Model Context Protocol implementation
- ✅ Exposes `search_linkedin_jobs` tool to Claude and other MCP clients
- ✅ Stdio transport for seamless integration
- ✅ Auto-discovery by MCP-compatible clients
- **Usage**: `npm start` → Configure in `claude_desktop_config.json`

#### 2. **MCP Server for Ollama** (`ollama_bridge/mcp-server.js`)
- ✅ Interactive terminal UI with `ollmcp` client
- ✅ Works with local LLMs (olmo-3.1, mistral-small3.2, qwen3-coder, gemma3:27b, phi4)
- ✅ Human-in-the-loop mode for tool execution approval
- ✅ Hot-reload servers without restarting
- ✅ Tool enable/disable management
- **Usage**: `cd ollama_bridge && start-ollmcp.bat`

#### 3. **REST API Server** (`api.js`)
- ✅ Express.js REST API with rate limiting
- ✅ `POST /search` - Job search with JSON body
- ✅ `GET /health` - Health check endpoint
- ✅ Configurable rate limits and timeouts
- ✅ CORS enabled for web applications
- **Usage**: `npm run api` → `http://localhost:3000`

#### 4. **Command-Line Interface** (`bin/linkedin-jobs.js`)
- ✅ Standalone CLI tool with argument parsing
- ✅ Works with `npx linkedin-jobs` globally
- ✅ All search parameters via flags
- ✅ JSON output for scripting
- **Usage**: `npx linkedin-jobs --keyword "engineer" --location "Berlin"`

#### 5. **Node.js Library** (`index.js`)
- ✅ Import as npm module: `require('./index')`
- ✅ Async/await promise-based API
- ✅ Direct programmatic access
- ✅ Use in custom Node.js applications
- **Usage**: `const jobs = await linkedIn.query({keyword, location})`

### 🔍 Search & Filtering Capabilities

- **Keywords**: Job titles, skills, technologies (e.g., "Software Engineer", "React Developer")
- **Location**: City, country, or "Worldwide" with auto-geocoding
- **Date Filters**: Past 24 hours, past week, past month
- **Job Type**: Full-time, part-time, contract, temporary, volunteer, internship
- **Remote Work**: On-site, remote, hybrid
- **Salary**: Minimum salary filtering ($40k, $60k, $80k, $100k+)
- **Experience**: Entry level, mid-senior, director, executive
- **Sorting**: By relevance or recent date
- **Limits**: Configure max results (5, 10, 25, etc.)
- **Pagination**: Page through results
- **Verified Jobs**: Filter for verified postings only
- **Low Competition**: Jobs with <10 applicants

### 🌍 Location & Geocoding

- ✅ **Dynamic geocoding** via OpenStreetMap Nominatim API
- ✅ **Built-in geoId mappings** for major countries (US, Germany, India, UK, Canada, Australia, etc.)
- ✅ **Auto-detection** of German LinkedIn domain for EU locations
- ✅ Fallback to location string if geoId not found
- ✅ City and country-specific searches

### ⚡ Performance & Reliability

- **Caching**: 1-hour TTL for repeated searches (configurable via `LINKEDIN_CACHE_TTL_MS`)
- **Rate Limiting**: 2-3 second delays between requests (API: configurable per window)
- **Auto-retry**: Exponential backoff on errors (max 3 retries)
- **Timeout Handling**: Configurable request timeouts (default: 30s)
- **Error Recovery**: Graceful fallback on failed geocoding or network errors

### 🛡️ Security & Configuration

- **Environment Variables**: `.env` file support
  - `LINKEDIN_USER_AGENT` - Custom user agent
  - `LINKEDIN_REQUEST_TIMEOUT_MS` - Request timeout
  - `LINKEDIN_CACHE_TTL_MS` - Cache duration
  - `PORT` - API server port
  - `API_RATE_LIMIT_WINDOW_MS` - Rate limit window
  - `API_RATE_LIMIT_MAX` - Max requests per window
- **Stealth Measures**: Random user agents, realistic headers
- **Session Management**: Cookie-based authentication support

### 📊 Response Format

- **Structured JSON**: Clean, parseable job data
- **Rich Metadata**: Position, company, location, salary, date posted
- **Direct Links**: LinkedIn job URLs and company logos
- **Time Information**: Both ISO dates and human-readable "2 hours ago"
- **Search Context**: Returns search parameters for debugging

### 🧪 Testing & Development

- ✅ Test suite included (`test.js`)
- ✅ Example queries and usage patterns
- ✅ Debug mode with verbose logging
- ✅ Health check endpoints for monitoring
- ✅ Clear error messages and troubleshooting guides


## 🎯 What You Can Do With This Project

### For Job Seekers
- 🤖 **AI Job Assistant**: Let Claude/Ollama find jobs while you focus on applications
- 📧 **Automated Alerts**: Build custom job alert systems
- 📊 **Market Research**: Analyze job market trends and salary ranges
- 🎯 **Smart Filtering**: Find niche opportunities (low applicants, verified only)

### For Developers
- 🔧 **Portfolio Project**: Showcase MCP integration, REST APIs, CLI tools
- 📚 **Learning Resource**: Study web scraping, caching, rate limiting, MCP protocol
- 🛠️ **Build On Top**: Create job dashboards, Slack bots, Discord integrations
- 🧪 **Testing Ground**: Experiment with LLM tool calling and agent workflows

### For Researchers
- 📈 **Labor Market Analysis**: Study job postings, skills demand, geographic trends
- 💼 **Recruitment Patterns**: Analyze posting frequency, company hiring behavior
- 🌍 **Geographic Studies**: Compare job markets across regions
- 💰 **Salary Research**: Track compensation trends by role/location

### For Businesses
- 🏢 **Talent Intelligence**: Monitor competitor hiring and market gaps
- 🎯 **Candidate Sourcing**: Identify hiring opportunities and talent pools
- 📊 **Market Positioning**: Understand salary benchmarks and benefits trends
- 🤝 **Partnership Opportunities**: Find companies hiring in complementary areas

### Integration Examples
```javascript
// Slack bot that posts jobs daily
const jobs = await query({keyword: "Node.js", location: "Remote", dateSincePosted: "past 24 hours"});
slackClient.postMessage(formatJobs(jobs));

// Discord bot command
client.on('message', async msg => {
  if (msg.content.startsWith('!jobs')) {
    const jobs = await query({keyword: msg.content.slice(6), limit: 5});
    msg.reply(formatJobEmbed(jobs));
  }
});

// Personal job dashboard with Express
app.get('/my-jobs', async (req, res) => {
  const jobs = await Promise.all([
    query({keyword: "React", location: "SF"}),
    query({keyword: "Node.js", location: "NYC"}),
  ]);
  res.render('dashboard', {jobs});
});
```

---

## ⚠️ LinkedIn Bot Detection & Access Restrictions

**Important**: LinkedIn employs sophisticated anti-automation measures that prevent programmatic job searching:

### Current Technical Limitations
- **Automated browsers detected** through WebDriver fingerprinting and behavioral analysis¹
- **Redirect loops (ERR_TOO_MANY_REDIRECTS)** when automation is detected²
- **Session-based blocking** even with valid authentication cookies
- **API endpoints returning empty responses** or blocking requests entirely

### How LinkedIn Detects Bots

LinkedIn uses multiple detection methods based on industry research³:

1. **Browser Fingerprinting**⁴:
   - Detection of `navigator.webdriver` property
   - Missing browser APIs that real browsers have
   - Consistent canvas/WebGL rendering signatures
   - Headless browser indicators

2. **Behavioral Analysis**⁵:
   - Lack of human mouse movements and scrolling patterns
   - Too-precise click timing and navigation
   - Missing keystroke dynamics variations
   - Predictable request timing patterns

3. **Network Analysis**⁶:
   - Data center IP addresses vs residential
   - Missing session history and cookies
   - Inconsistent User-Agent headers
   - Rate limiting violations

4. **Authentication State**:
   - Forced login requirements with CAPTCHA challenges
   - Two-factor authentication triggers
   - Account verification requirements

### Why This Happens

**Not primarily GDPR-related** - LinkedIn blocks automation globally:

1. **Business Model Protection**: LinkedIn monetizes job data through recruiting services⁷
2. **Terms of Service Enforcement**: Automated access violates LinkedIn's ToS⁸
3. **Server Load Management**: Preventing resource abuse from bots
4. **Data Quality**: Ensuring human interaction for analytics accuracy

### Legal & Technical Alternatives

**Recommended approaches:**
- **LinkedIn Talent Solutions API**: Official paid access for businesses⁹
- **Manual browsing**: Most reliable method
- **Alternative platforms**: Indeed, Glassdoor, AngelList, Dice
- **RSS job feeds**: Some sites offer structured data access
- **Job aggregator APIs**: Services like Adzuna, JobSpicy, Reed API

### Technical Implementation Status

This tool includes:
- ✅ **Advanced stealth measures**: WebDriver removal, realistic browser fingerprints
- ✅ **Human-like behavior**: Random mouse movements, scrolling, delays  
- ✅ **Location geocoding**: Fixed German/EU location mapping (Fürth→106430259)
- ✅ **Authentication handling**: Session cookie integration
- ❌ **LinkedIn access**: Currently blocked by detection systems

*This tool is provided for educational purposes. Users are responsible for compliance with applicable laws and platform Terms of Service.*

---

### References

1. Acar, G., et al. "Web Browser Fingerprinting" (IEEE Security & Privacy, 2016)
2. "ERR_TOO_MANY_REDIRECTS" - Chrome Network Error Documentation
3. Bursztein, E. "Detecting Automation" (Google Security Blog, 2019)  
4. Laperdrix, P., et al. "Browser Fingerprinting: A Survey" (ACM Computing Surveys, 2020)
5. "Bot Detection Techniques" - Cloudflare Documentation, 2023
6. "Automated Traffic Detection" - LinkedIn Engineering Blog, 2021
7. LinkedIn Corporation Annual Report (SEC Form 10-K, 2023)
8. LinkedIn User Agreement, Section 8.2 - "Dos and Don'ts" (Updated 2024)
9. LinkedIn Talent Solutions API Documentation (Microsoft Developer Network, 2024)

## 🚀 Installation & Setup

### Prerequisites
- **Node.js** (v14 or higher)
- **npm** or **yarn**

### Quick Start
```bash
# Clone or download the repository
cd linkedin-job-mcp

# Install dependencies
npm install

# Test the basic functionality
npm test
```

## 📖 Usage

### Method 1: Direct Script Usage

**Basic Test:**
```bash
# Run the test file
node test.js

# Or use npm script
npm test
```

**Custom Search:**
```bash
node -e "
const linkedIn = require('./index.js');

const options = {
  keyword: 'Data Scientist OR AI Engineer',
  location: 'New York',
  dateSincePosted: 'past week',
  jobType: 'full time',
  limit: '5'
};

linkedIn.query(options).then(jobs => {
  console.log('Found', jobs.length, 'jobs:');
  jobs.forEach((job, i) => {
    console.log(\`\${i+1}. \${job.position} at \${job.company}\`);
    console.log(\`   📍 \${job.location}\`);
    console.log(\`   🔗 \${job.jobUrl}\`);
  });
});
"
```

### Method 2: As MCP Server

**1. Start the MCP Server:**
```bash
npm start
# or
node server.js
```

**2. Configure in Claude Desktop/MCP Client:**

Add to your MCP configuration file (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "linkedin-jobs": {
      "command": "node",
      "args": ["server.js"],
      "cwd": "C:\\path\\to\\linkedin-job-mcp"
    }
  }
}
```

**3. Use with LLM:**

The server exposes the `search_linkedin_jobs` tool.

**Example LLM queries:**
- *"Find AI engineer jobs in California posted this week"*
- *"Search for data scientist positions with 100k+ salary"*
- *"Get remote machine learning jobs from the past month"*

### Method 3: Programmatic Usage

```javascript
const linkedIn = require("./index");

async function searchJobs() {
  const queryOptions = {
    keyword: "Machine Learning Engineer",
    location: "San Francisco",
    dateSincePosted: "past week",
    jobType: "full time",
    remoteFilter: "remote",
    salary: "120000",
    experienceLevel: "senior",
    limit: "10",
    sortBy: "recent"
  };

  try {
    const jobs = await linkedIn.query(queryOptions);
    
    console.log(`Found ${jobs.length} jobs:`);
    jobs.forEach(job => {
      console.log({
        position: job.position,
        company: job.company,
        location: job.location,
        salary: job.salary,
        url: job.jobUrl
      });
    });
  } catch (error) {
    console.error('Error:', error.message);
  }
}

searchJobs();
```

## 🔧 Configuration Parameters

| Parameter | Type | Description | Examples |
|-----------|------|-------------|----------|
| `keyword` | string | Job search terms | "software engineer", "data scientist" |
| `location` | string | Job location (auto-geocoded) | "Berlin", "New York", "Remote" |
| `dateSincePosted` | string | Time filter | "past month", "past week", "24hr" |
| `jobType` | string | Employment type | "full time", "part time", "contract" |
| `remoteFilter` | string | Work arrangement | "on site", "remote", "hybrid" |
| `salary` | string | Minimum salary | "40000", "60000", "80000", "100000" |
| `experienceLevel` | string | Experience required | "entry level", "senior", "director" |
| `limit` | string | Max results | "5", "10", "25" |
| `sortBy` | string | Sort order | "recent", "relevant" |
| `page` | string | Page number | "0", "1", "2" |
| `has_verification` | boolean | Verified jobs only | true, false |
| `under_10_applicants` | boolean | Low competition jobs | true, false |

## 📊 Response Format

### MCP Server Response
```json
{
  "success": true,
  "total_jobs": 5,
  "jobs": [
    {
      "position": "Senior AI Engineer",
      "company": "TechCorp",
      "location": "San Francisco, CA",
      "date": "2025-08-12",
      "agoTime": "1 day ago", 
      "salary": "$150,000 - $200,000",
      "jobUrl": "https://linkedin.com/jobs/view/123456",
      "companyLogo": "https://example.com/logo.jpg"
    }
  ],
  "search_params": {
    "keyword": "AI Engineer",
    "location": "San Francisco",
    "limit": "5"
  }
}
```

### Direct Usage Response
```javascript
[
  {
    position: 'Machine Learning Engineer',
    company: 'OpenAI',
    location: 'San Francisco, CA',
    date: '2025-08-12',
    salary: 'Not specified',
    jobUrl: 'https://linkedin.com/jobs/view/789012',
    companyLogo: 'https://media.licdn.com/...',
    agoTime: '2 hours ago'
  }
]
```

## ⚡ Performance Features

- **🚀 Caching**: 1-hour result caching for faster repeated searches
- **🛡️ Rate Limiting**: 2-3 second delays between requests  
- **🔄 Auto-retry**: Exponential backoff on errors (max 3 retries)
- **🌍 Geocoding**: Dynamic location standardization via OpenStreetMap
- **🎯 Smart Filtering**: Location-based job filtering for better results

## 🐛 Troubleshooting

### Common Issues

**1. Bot Detection / Redirect Loops (ERR_TOO_MANY_REDIRECTS)**
```
⚠️ LinkedIn detected automation and is causing redirect loops
Solutions:
- This is expected behavior with current LinkedIn protection
- Consider using alternative job platforms
- Manual browsing remains most reliable
- Try different IP addresses (residential vs data center)
```

**2. Empty Results or Blocked Requests**
```
⚠️ API endpoints returning empty HTML or blocking entirely
Reasons:
- LinkedIn's anti-bot systems are active globally
- Not specific to EU/GDPR - affects all regions
- Session cookies may trigger additional scrutiny
- WebDriver detection despite stealth measures
```

**3. Authentication Issues**
```bash
# Test without authentication cookies first
// linkedIn.setAuth('...', '...'); // Comment this out

# Authentication may increase detection likelihood
# LinkedIn tracks automated usage of authenticated sessions
```

**4. Installation Issues**
```bash
# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

**5. MCP Server Connection Issues**
- Ensure correct file paths in configuration
- Check Node.js is in PATH
- Verify MCP client supports the protocol version

### Debug Mode
```bash
# Enable verbose logging
DEBUG=linkedin-jobs node test.js

# Test specific location
node -e "console.log(require('./index.js').query({keyword:'test', location:'Tokyo', limit:'1'}))"
```

## 📝 Examples

### Search AI Jobs in US
```bash
node -e "
require('./index.js').query({
  keyword: 'Artificial Intelligence OR Machine Learning',
  location: 'United States',
  dateSincePosted: 'past week',
  jobType: 'full time',
  salary: '100000',
  limit: '10'
}).then(jobs => console.log('Found:', jobs.length, 'AI jobs'))
"
```

### Remote Data Science Positions
```bash
node -e "
require('./index.js').query({
  keyword: 'Data Scientist',
  remoteFilter: 'remote',
  dateSincePosted: 'past month',
  experienceLevel: 'senior',
  limit: '15'
}).then(jobs => {
  const remote = jobs.filter(j => j.location.toLowerCase().includes('remote'));
  console.log('Remote jobs:', remote.length);
})
"
```

## 📋 TODO / Roadmap

- [ ] Add support for more job sites (Indeed, Glassdoor)
- [ ] Implement job alert/monitoring functionality  
- [ ] Add job description content extraction
- [ ] Create web dashboard for job management
- [ ] Add email notification system
- [ ] Implement job application tracking

## ⚖️ Legal & Ethics

This tool is designed for:
- ✅ **Educational purposes**
- ✅ **Personal job searching**  
- ✅ **Research and analysis**

**Not intended for:**
- ❌ Commercial data harvesting
- ❌ Bulk profile scraping
- ❌ Violation of terms of service
- ❌ Personal data collection

*Users must comply with LinkedIn's Terms of Service, applicable data protection laws (GDPR, CCPA), and respect rate limits.*

## Skills  

This project demonstrates Node.js backend development, web automation defense handling, dynamic geocoding, caching, rate limiting, and MCP integration for LLMs.  
It’s a hands-on example of bridging job-market data and AI reasoning — responsibly. 🧠  

---

## Results & Business Recommendation  

**What it delivers**  
- Structured job data in JSON format  
- Geocoded, filterable search results  
- Fast performance with caching  
- Educational transparency about automation risks  

**Recommended use cases**  
- Personal job dashboards  
- Research projects on labor markets  
- LLM-based personal assistants  
- Ethical web automation studies
---

## 👤 Author

**Srinjoy Ghosh**
- GitHub: [@srinjoy-ghosh](https://github.com/srinjoy-ghosh)
- Email: ghoshsrinjoy97@gmail.com

## 📄 License

Apache License - see [LICENSE](LICENSE) file for details

---

⭐ **Star this repo** if you find it useful!
🐛 **Report issues** on GitHub
💬 **Contribute** via pull requests
