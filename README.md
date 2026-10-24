# LinkedIn Jobs MCP

LinkedIn job search and full job details for your AI apps. A Windows app connects itself to Claude Code, Codex,
VS Code and other MCP clients; the same tools also come as an npm package, a REST API and a command line.

[![npm version](https://img.shields.io/npm/v/linkedin-jobs-mcp.svg)](https://www.npmjs.com/package/linkedin-jobs-mcp)
[![npm downloads](https://img.shields.io/npm/dm/linkedin-jobs-mcp.svg)](https://www.npmjs.com/package/linkedin-jobs-mcp)
[![CI](https://github.com/GhoshSrinjoy/linkedin-job-mcp/actions/workflows/node.js.yml/badge.svg)](https://github.com/GhoshSrinjoy/linkedin-job-mcp/actions/workflows/node.js.yml)
[![License](https://img.shields.io/badge/license-PolyForm%20Noncommercial-blue.svg)](https://github.com/GhoshSrinjoy/linkedin-job-mcp/blob/main/LICENSE)

![The setup menu of the Windows app](https://raw.githubusercontent.com/GhoshSrinjoy/linkedin-job-mcp/main/docs/screenshots/setup-menu.png)

## Tools

| Tool | What your AI app gets |
|------|-----------------------|
| `search_linkedin_jobs` | Jobs by keyword and location, filtered by date, job type, remote work, salary, experience level, verified postings or fewer than 10 applicants |
| `get_linkedin_job_details` | One job's full description, seniority, employment type, industries, posting age and applicant count |

It reads LinkedIn's public job pages, so it needs no account and no browser. Requests are spaced out and cached.

## Install

### Windows app

1. Download `linkedin-jobs-mcp.exe` from the [latest release](https://github.com/GhoshSrinjoy/linkedin-job-mcp/releases/latest).
   It is one file with Node.js inside.
2. Double-click it. The file is not code-signed, so Windows may say "Windows protected your PC": choose
   **More info → Run anyway**.
3. Choose **1 Install and connect the apps found**. The app copies itself to
   `%LOCALAPPDATA%\Programs\linkedin-jobs-mcp\` and adds itself to every supported app it finds.
4. Restart those apps. The app has no window of its own: they start it in the background when they need the tools.

![Installing the app and connecting the apps found](https://raw.githubusercontent.com/GhoshSrinjoy/linkedin-job-mcp/main/docs/screenshots/install.png)

### npm (Windows, macOS, Linux)

Needs Node.js 18 or newer.

```bash
npm install -g linkedin-jobs-mcp
linkedin-jobs-mcp connect
```

Or add it to an app by hand, through npx:

```json
{
  "mcpServers": {
    "linkedin-jobs": { "command": "npx", "args": ["-y", "linkedin-jobs-mcp"] }
  }
}
```

On Windows, some apps need `"command": "cmd", "args": ["/c", "npx", "-y", "linkedin-jobs-mcp"]`.

### From source

```bash
git clone https://github.com/GhoshSrinjoy/linkedin-job-mcp.git
cd linkedin-job-mcp
npm install
npm run app -- connect
```

## Connect your apps

| App | Name for `connect` | Where the setting goes |
|-----|--------------------|------------------------|
| Claude Code | `claude-code` | `claude mcp add --scope user` |
| Codex | `codex` | `~/.codex/config.toml` |
| VS Code | `vscode` | `%APPDATA%\Code\User\mcp.json` |
| VS Code Insiders | `vscode-insiders` | `%APPDATA%\Code - Insiders\User\mcp.json` |
| Claude Desktop | `claude-desktop` | `%APPDATA%\Claude\claude_desktop_config.json` |
| Cursor | `cursor` | `~/.cursor/mcp.json` |
| Windsurf | `windsurf` | `~/.codeium/windsurf/mcp_config.json` |
| Gemini CLI | `gemini-cli` | `~/.gemini/settings.json` |
| LM Studio | `lm-studio` | `~/.lmstudio/mcp.json` |
| Cline | `cline` | `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json` |

`connect` only adds or replaces the `linkedin-jobs` entry: other servers and settings stay, and the first change keeps a
copy of the file next to it (`<file>.linkedin-jobs.bak`). A settings file with comments is left unchanged, and the
entry to add is printed instead.

![The server connected in two apps](https://raw.githubusercontent.com/GhoshSrinjoy/linkedin-job-mcp/main/docs/screenshots/connected.png)

### Commands

| Command | What it does |
|---------|--------------|
| `linkedin-jobs-mcp` | The setup menu in a console window; the MCP server when an app starts it |
| `linkedin-jobs-mcp install` | Copy the Windows app to `%LOCALAPPDATA%\Programs\linkedin-jobs-mcp\` and connect the apps found |
| `linkedin-jobs-mcp connect [app ...]` | Connect the apps found, or only the named ones (also when they are not found) |
| `linkedin-jobs-mcp disconnect [app ...]` | Remove the connection from every app, or only from the named ones |
| `linkedin-jobs-mcp status` | Which apps are found and connected |
| `linkedin-jobs-mcp config [app ...]` | Print the settings to add by hand |
| `linkedin-jobs-mcp serve [--port 3000] [--host 127.0.0.1]` | REST API plus MCP over HTTP |
| `linkedin-jobs-mcp mcp` | MCP over stdio (what the connected apps run) |
| `linkedin-jobs-mcp job <id or URL>` | One job's details as JSON |
| `linkedin-jobs-mcp search --keyword "data engineer" --location "Berlin, Germany"` | Search from the command line |
| `linkedin-jobs-mcp uninstall` | Disconnect every app and remove the installed Windows app |

With the Windows app, run them from its folder, for example `.\linkedin-jobs-mcp.exe status`.

### Add it by hand

Every app needs the same thing: the program, started with the `mcp` argument. VS Code (`mcp.json`):

```json
{
  "servers": {
    "linkedin-jobs": {
      "type": "stdio",
      "command": "C:\\Users\\you\\AppData\\Local\\Programs\\linkedin-jobs-mcp\\linkedin-jobs-mcp.exe",
      "args": ["mcp"]
    }
  }
}
```

Claude Desktop, Cursor, Windsurf, Gemini CLI, LM Studio and Cline take the same entry under `"mcpServers"`, without
`"type"`. Codex (`config.toml`):

```toml
[mcp_servers.linkedin-jobs]
command = "C:\\Users\\you\\AppData\\Local\\Programs\\linkedin-jobs-mcp\\linkedin-jobs-mcp.exe"
args = ["mcp"]
```

Claude Code:

```bash
claude mcp add --scope user linkedin-jobs -- "C:\Users\you\AppData\Local\Programs\linkedin-jobs-mcp\linkedin-jobs-mcp.exe" mcp
```

Ollama, through [mcp-client-for-ollama](https://github.com/jonigl/mcp-client-for-ollama): save the `mcpServers`
entry in a file and start `ollmcp -j servers.json`.

`linkedin-jobs-mcp config` prints all of these with the real path.

### MCP over HTTP

Apps that connect by URL can use the HTTP server instead. Start `linkedin-jobs-mcp serve` (or `npm run api`) and add
`http://127.0.0.1:3000/mcp`:

```bash
claude mcp add --transport http linkedin-jobs http://127.0.0.1:3000/mcp
```

```json
{ "servers": { "linkedin-jobs": { "type": "http", "url": "http://127.0.0.1:3000/mcp" } } }
```

The server listens on this computer only and refuses requests that name another host, so web pages cannot reach it
through DNS rebinding. `HOST=0.0.0.0` makes it reachable from other machines, for example from a container; protect
it yourself then.

## Search options

| Option | Values |
|--------|--------|
| `keyword` | Job title or keywords, e.g. `data engineer` |
| `location` | City, region or country, e.g. `Berlin, Germany` |
| `city`, `country` | Narrow the location |
| `geoId` | LinkedIn location id, skips the location lookup |
| `dateSincePosted` | `past 24 hours`, `past week`, `past month` |
| `jobType` | `full time`, `part time`, `contract`, `temporary`, `volunteer`, `internship` |
| `remoteFilter` | `on site`, `remote`, `hybrid` |
| `salary` | Minimum: `40000`, `60000`, `80000`, `100000`, `120000` |
| `experienceLevel` | `internship`, `entry level`, `associate`, `senior`, `director`, `executive` |
| `limit` | Number of jobs (default 10; 25 in the REST API) |
| `sortBy` | `recent` or `relevant` |
| `page` | Page number, from 0 |
| `has_verification` | Verified jobs only |
| `under_10_applicants` | Jobs with fewer than 10 applicants |

The REST API accepts every option except `salary`, `experienceLevel`, `has_verification` and `under_10_applicants`.

## Responses

A search returns:

```json
{
  "success": true,
  "total_jobs": 1,
  "jobs": [
    {
      "position": "Data Engineer (m/w/d)",
      "company": "Example GmbH",
      "location": "Berlin, Berlin, Germany",
      "date": "2026-10-20",
      "agoTime": "4 days ago",
      "salary": "Not specified",
      "jobUrl": "https://www.linkedin.com/jobs/view/1234567890/",
      "companyLogo": "https://media.licdn.com/…"
    }
  ],
  "search_params": { "keyword": "data engineer", "location": "Berlin, Germany", "limit": "10" }
}
```

Job details return:

```json
{
  "id": "1234567890",
  "position": "Data Engineer (m/w/d)",
  "company": "Example GmbH",
  "location": "Berlin, Berlin, Germany",
  "postedAgo": "3 weeks ago",
  "applicants": "Over 200 applicants",
  "salary": null,
  "seniority": "Mid-Senior level",
  "employmentType": "Full-time",
  "jobFunction": null,
  "industries": "Software Development",
  "criteria": { "Seniority level": "Mid-Senior level", "Employment type": "Full-time", "Industries": "Software Development" },
  "acceptingApplications": true,
  "description": "We are looking for a data engineer to join our platform team. …",
  "jobUrl": "https://www.linkedin.com/jobs/view/1234567890/"
}
```

A job LinkedIn no longer has returns `{ "id": "…", "removed": true }`.

## REST API

`npm run api` or `linkedin-jobs-mcp serve` starts it on `http://127.0.0.1:3000`.

| Endpoint | What it does |
|----------|--------------|
| `POST /search` | Search, with the options above as a JSON body; returns `{ "cached", "total", "jobs" }` |
| `GET /job/:id`, `GET /job?url=<link>` | One job's details; 404 when LinkedIn no longer has it, 400 for an invalid id or link |
| `POST /mcp` | MCP over Streamable HTTP |
| `GET /health` | `{ "ok": true }` |

## Library

```js
const { query, getJobDetails } = require("linkedin-jobs-mcp");

const jobs = await query({ keyword: "data engineer", location: "Berlin, Germany", limit: "10" });
const job = await getJobDetails("https://www.linkedin.com/jobs/view/1234567890/");
```

## Configuration

Set these in the environment or in a `.env` file in the folder you start it from.

| Variable | Default | What it sets |
|----------|---------|--------------|
| `PORT` | `3000` | Port of the REST API and MCP over HTTP |
| `HOST` | `127.0.0.1` | Address the server listens on |
| `LINKEDIN_REQUEST_TIMEOUT_MS` | `15000` | Timeout of one request to LinkedIn |
| `LINKEDIN_CACHE_TTL_MS` | `3600000` | How long search results stay cached |
| `LINKEDIN_DETAIL_MIN_INTERVAL_MS` | `1500` | Minimum gap between two job-page requests |
| `LINKEDIN_DETAIL_CACHE_TTL_MS` | `21600000` | How long job details stay cached |
| `LINKEDIN_USER_AGENT` | | User agent for job-page requests |
| `API_RATE_LIMIT_WINDOW_MS` | `60000` | Rate-limit window of the REST API |
| `API_RATE_LIMIT_MAX` | `60` | Requests per window and address |

## Build the Windows app

On Windows with Node.js 20 or newer:

```bash
npm install
npm run build:win     # dist/linkedin-jobs-mcp.exe and its SHA-256
```

The build bundles the code with esbuild and injects it into a copy of `node.exe` (a Node.js single executable
application). Pushing a tag such as `v1.2.0` builds the app on GitHub Actions and attaches it to a release.

## Tests

```bash
npm test
```

The tests run offline: job-page parsing, settings files, the MCP server and the HTTP API.

## Responsible use

The tools read public job pages slowly and cache what they read, for personal job searching and research. Automated
access can conflict with LinkedIn's User Agreement, so keep the volume low and use it at your own risk.

## License

[PolyForm Noncommercial 1.0.0](https://github.com/GhoshSrinjoy/linkedin-job-mcp/blob/main/LICENSE): free for personal, research and other non-commercial use. For commercial use, ask for permission.

Srinjoy Ghosh ([@GhoshSrinjoy](https://github.com/GhoshSrinjoy), ghoshsrinjoy97@gmail.com)
