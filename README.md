*“My AI found five openings before I finished my coffee. That’s productivity !’”*

# LinkedIn Jobs MCP Server

# 💼 LinkedIn Jobs MCP Server  

A Model Context Protocol (MCP) server that gives LLMs real-time job search powers — including LinkedIn queries, dynamic geocoding, and intelligent filtering.  
Think of it as your AI-powered recruiter that never sleeps (and actually reads the job description). 🤖  

🔗 **Repo:** https://github.com/GhoshSrinjoy/linkedin-job-mcp  

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


## Features

- 🔍 Search LinkedIn jobs with various filters
- 🌍 Dynamic location geocoding using OpenStreetMap
- 🇩🇪 Auto-detection of German LinkedIn domain for EU locations
- 📊 Support for location, keywords, experience level, salary, remote work preferences
- ⚡ Caching for better performance
- 🛡️ Rate limiting to avoid being blocked
- 📄 JSON response format for easy parsing
- 🎯 Location-based job filtering for better results

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

**3. Installation Issues**
```bash
# Clear npm cache
npm cache clean --force

# Reinstall dependencies  
rm -rf node_modules package-lock.json
npm install
```

**4. MCP Server Connection Issues**
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
---

## 🚀 New: Library, CLI, REST, and Ollama Integration

- **Library**: `const { query } = require('./index');` then `await query({ keyword, location, dateSincePosted, jobType, remoteFilter, limit, sortBy, geoId, city, country });`
- **CLI**: `npx linkedin-jobs --keyword "data scientist" --location "Germany" --remoteFilter remote --dateSincePosted "past week" --limit 20`
- **REST**: `npm run api` -> `POST /search` with JSON body of the same fields; `GET /health` for probes.
- **Env config**: `LINKEDIN_USER_AGENT`, `LINKEDIN_REQUEST_TIMEOUT_MS`, `LINKEDIN_CACHE_TTL_MS`, `PORT` (API), `API_RATE_LIMIT_WINDOW_MS`, `API_RATE_LIMIT_MAX`. `.env` is supported.
- **MCP Server**: run the MCP server (`npm start`) and point an MCP-capable client at `server.js`; it will expose the `search_linkedin_jobs` tool to local models.

### 🦙 Using with Ollama

This project supports Ollama through the **MCP Client for Ollama** (`ollmcp`)! This allows local LLMs to use LinkedIn job search as a tool through an interactive terminal interface.

**Quick Start:**

1. **Navigate to ollama_bridge directory:**
   ```bash
   cd ollama_bridge
   ```

2. **Set up Python virtual environment** (first time only):
   ```bash
   # Create venv with Python 3.11+
   uv venv .venv --python 3.11

   # Install ollmcp client
   uv pip install --python .venv/Scripts/python.exe ollmcp
   ```

3. **Start the interactive client** (Windows CMD/PowerShell):
   ```cmd
   start-ollmcp.bat
   ```

   Or manually:
   ```cmd
   .venv\Scripts\python.exe -m mcp_client_for_ollama -j mcp-config.json -m olmo-3.1:latest
   ```

4. **Use natural language to search jobs:**
   ```
   User: get me jobs for Software engineer fulltime in this recent week in the area of Erlangen Germany
   ```

The LLM will automatically use the `search_linkedin_jobs` tool!

**Important Notes:**
- Must run from Windows CMD or PowerShell (not Git Bash due to terminal compatibility)
- The MCP server path in `mcp-config.json` needs to be updated to your actual installation directory
- Requires Ollama to be running locally at `http://localhost:11434`

**Supported Ollama Models with Tool Calling:**
- `olmo-3.1:latest` ✅
- `mistral-small3.2:latest` ✅
- `qwen3-coder:latest` ✅
- `gemma3:27b` ✅
- `phi4:latest` ✅

**Interactive Commands:**
- `t` or `tools` - Enable/disable tools (if not showing up)
- `m` or `model` - Switch models
- `rs` or `reload-servers` - Reload MCP servers
- `hil` or `human-in-loop` - Toggle tool execution confirmation
- `q` or `quit` - Exit

**Detailed Documentation:** See [ollama_bridge/README.md](ollama_bridge/README.md) for complete setup instructions and troubleshooting.

**Note**: Check [Ollama's tools models](https://ollama.com/search?c=tools) for the latest list of models supporting function calling.
