# LinkedIn Jobs MCP Server

A Model Context Protocol (MCP) server that provides LinkedIn job search capabilities to LLMs with dynamic location geocoding.

## Features

- 🔍 Search LinkedIn jobs with various filters
- 🌍 Dynamic location geocoding using OpenStreetMap
- 🇩🇪 Auto-detection of German LinkedIn domain for EU locations
- 📊 Support for location, keywords, experience level, salary, remote work preferences
- ⚡ Caching for better performance
- 🛡️ Rate limiting to avoid being blocked
- 📄 JSON response format for easy parsing
- 🎯 Location-based job filtering for better results

## ⚠️ EU/GDPR Compliance Notice

**Important**: Due to EU regulations and GDPR compliance, LinkedIn has implemented restrictions that affect job location filtering:

### Current Limitations
- **German/EU location filtering may not work as expected** due to GDPR compliance measures
- LinkedIn intentionally **ignores location parameters** from EU regions to comply with data protection laws
- **Dutch Data Protection Authority** considers most data scraping as GDPR violations
- LinkedIn **closed public API access** and requires Partner Program membership

### Why This Happens
1. **GDPR Compliance**: LinkedIn restricts targeted data collection from EU locations
2. **Data Minimization**: EU regulations require limiting data collection scope  
3. **Commercial Use**: EU authorities don't consider commercial interests as "legitimate interests"
4. **User Protection**: Prevents targeted collection of German/EU user data

### Legal Alternatives
- Use **official LinkedIn Partner Program** (expensive, requires approval)
- Try **alternative job sites**: StepStone, Xing, Indeed Germany
- **Manual search** on LinkedIn (most compliant)
- Consider **non-EU job markets** where restrictions are less strict

*This tool is provided for educational purposes. Users are responsible for compliance with applicable laws and LinkedIn's Terms of Service.*

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

**1. Empty Results for German/EU Locations**
- Expected due to GDPR compliance
- Try non-EU locations (US, Canada, Asia)
- Consider alternative job sites for EU positions

**2. Rate Limiting/Blocking**
```bash
# Add delays between requests
# Use different user agents
# Respect LinkedIn's robots.txt
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

## 👤 Author

**Srinjoy Ghosh**
- GitHub: [@srinjoy-ghosh](https://github.com/srinjoy-ghosh)
- Email: contact@srinjoy.dev

## 📄 License

Apache License - see [LICENSE](LICENSE) file for details

---

⭐ **Star this repo** if you find it useful!  
🐛 **Report issues** on GitHub  
💬 **Contribute** via pull requests
