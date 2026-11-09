#!/usr/bin/env node

const { Server } = require("@modelcontextprotocol/sdk/server/index.js");
const { StdioServerTransport } = require("@modelcontextprotocol/sdk/server/stdio.js");
const {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} = require("@modelcontextprotocol/sdk/types.js");
const linkedIn = require("./index.js");
const { version } = require("./package.json");

const radarUrl = () => (process.env.GHOSTRADAR_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");

// Ghost Job Radar's verdict on one posting, shortened for an AI app
async function checkGhostJob({ job, company, with_news: withNews = false }) {
  const input = String(job || "").trim();
  if (!input) throw new Error("Give a job link or the ad text");
  let res;
  try {
    res = await fetch(`${radarUrl()}/api/check`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ [/^https?:\/\//i.test(input) ? "url" : "text"]: input, company: company || null, with_news: Boolean(withNews) }),
      signal: AbortSignal.timeout(120000),
    });
  } catch (err) {
    throw new Error(err.name === "TimeoutError"
      ? "Ghost Job Radar did not answer within 2 minutes"
      : "Ghost Job Radar is not running. Start it with: linkedin-jobs-mcp radar");
  }
  if (!res.ok) throw new Error(`Ghost Job Radar returned HTTP ${res.status}`);
  const data = await res.json();
  const r = data.result;
  if (!r) return { success: false, mode: data.mode, notes: data.notes };
  const s = r.score;
  return {
    success: true,
    job: { title: r.posting.title, company: r.posting.company, location: r.posting.location, url: r.posting.url },
    ghost_risk: { grade: s.grade, label: s.grade_label, score: s.risk, confidence: s.confidence },
    patterns: s.types.filter((t) => t.score >= 0.3).map((t) => ({ pattern: t.label, strength: t.score })),
    your_chance: { chance: s.competition.chance, text: s.competition.text || null },
    communication: s.communication?.text || null,
    advice: s.advice,
    reasons: s.reasons.filter((x) => x.direction !== "info").map((x) => ({ signal: x.label, fact: x.fact, points: x.points })),
    caveats: s.caveats,
    notes: data.notes,
  };
}

class LinkedInJobsServer {
  constructor() {
    this.server = new Server(
      {
        name: "linkedin-jobs-mcp",
        version,
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();
  }

  setupToolHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: "search_linkedin_jobs",
            description:
              "Find open jobs on LinkedIn by keyword and location, newest first. Read-only: it reads " +
              "LinkedIn's public job search without signing in, spaces its requests out and keeps each " +
              "search for an hour, so repeating a search answers at once. Returns JSON with total_jobs and " +
              "jobs, each with position, company, location, date, agoTime, salary (when LinkedIn shows one), " +
              "jobUrl and companyLogo; on failure, such as LinkedIn limiting requests, success is false with " +
              "an error. LinkedIn serves 10 jobs per request, so every 10 jobs asked for add about a second. " +
              "Use get_linkedin_job_details on a jobUrl for the full description and applicant count, and " +
              "check_ghost_job to see whether a posting is really open.",
            inputSchema: {
              type: "object",
              properties: {
                keyword: {
                  type: "string",
                  description: "Job title, skill or company, e.g. 'data engineer'. Leave out to list all jobs in the location",
                },
                location: {
                  type: "string",
                  description: "City, region or country, e.g. 'Berlin, Germany'. Leave out to search worldwide",
                },
                city: {
                  type: "string",
                  description: "City to search in; when given, it is searched instead of location, e.g. 'Munich'",
                },
                country: {
                  type: "string",
                  description: "Country to search in when location is left out, e.g. 'Germany'",
                },
                geoId: {
                  type: "string",
                  description:
                    "LinkedIn's numeric location id, e.g. '103644278' for the United States. Use it when a place " +
                    "name finds the wrong location",
                },
                dateSincePosted: {
                  type: "string",
                  description: "Only jobs posted within this period ('24hr' and 'today' mean the past 24 hours). Leave out for any date",
                  enum: ["past 24 hours", "past week", "past month", "24hr", "today"],
                },
                jobType: {
                  type: "string",
                  description: "Only this type of employment. Leave out for all types",
                  enum: ["full time", "part time", "contract", "temporary", "volunteer", "internship"],
                },
                remoteFilter: {
                  type: "string",
                  description: "Only this workplace type. Leave out for all",
                  enum: ["on site", "remote", "hybrid"],
                },
                under_10_applicants: {
                  type: "boolean",
                  description: "Only jobs that fewer than 10 people have applied to so far",
                  default: false,
                },
                limit: {
                  type: "string",
                  description: "How many jobs to return, as a number in a string, e.g. '25'",
                  default: "10",
                },
                page: {
                  type: "string",
                  description: "Which page of results, from '0'. A page is limit jobs long: page '1' with limit '10' returns jobs 11 to 20",
                  default: "0",
                },
                sortBy: {
                  type: "string",
                  description: "'recent' for newest first or 'relevant' for LinkedIn's best matches first",
                  enum: ["recent", "relevant"],
                  default: "recent",
                },
              },
            },
          },
          {
            name: "get_linkedin_job_details",
            description:
              "Get one LinkedIn job's full description, criteria (seniority, employment type, industries), " +
              "posted time and the applicant count shown on the public job page",
            inputSchema: {
              type: "object",
              properties: {
                job: {
                  type: "string",
                  description: "LinkedIn job id (e.g. '1234567890') or job URL",
                },
              },
              required: ["job"],
            },
          },
          {
            name: "check_ghost_job",
            description:
              "Grade a job posting with Ghost Job Radar: how likely it is to be a ghost job (not really open), " +
              "your chance against the competition, and the facts behind the grade. Needs the radar running " +
              "(linkedin-jobs-mcp radar)",
            inputSchema: {
              type: "object",
              properties: {
                job: {
                  type: "string",
                  description: "Job link (LinkedIn, the employer's site or a job board) or the pasted ad text",
                },
                company: {
                  type: "string",
                  description: "Company name, when the job is pasted text",
                },
                with_news: {
                  type: "boolean",
                  description: "Also check company news (slower)",
                  default: false,
                },
              },
              required: ["job"],
            },
          },
        ],
      };
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      if (name === "search_linkedin_jobs") {
        try {
          const queryOptions = {
            keyword: args.keyword || "",
            location: args.location || "",
            city: args.city || "",
            country: args.country || "",
            geoId: args.geoId || "",
            dateSincePosted: args.dateSincePosted || "",
            jobType: args.jobType || "",
            remoteFilter: args.remoteFilter || "",
            under_10_applicants: args.under_10_applicants === true || args.under_10_applicants === "true",
            limit: args.limit || "10",
            sortBy: args.sortBy || "recent",
            page: args.page || "0",
          };

          console.error("Searching with options:", queryOptions);
          const jobs = await linkedIn.query(queryOptions);

          return {
            content: [
              {
                type: "text",
                text: JSON.stringify({
                  success: true,
                  total_jobs: jobs.length,
                  jobs: jobs.map(job => ({
                    position: job.position,
                    company: job.company,
                    location: job.location,
                    date: job.date,
                    agoTime: job.agoTime,
                    salary: job.salary,
                    jobUrl: job.jobUrl,
                    companyLogo: job.companyLogo,
                  })),
                  search_params: queryOptions,
                }, null, 2),
              },
            ],
          };
        } catch (error) {
          console.error("Error in search:", error);
          return {
            content: [
              {
                type: "text",
                text: JSON.stringify({
                  success: false,
                  error: error.message,
                  search_params: args,
                }, null, 2),
              },
            ],
            isError: true,
          };
        }
      }

      if (name === "get_linkedin_job_details") {
        try {
          const job = await linkedIn.getJobDetails(args.job);
          return {
            content: [{ type: "text", text: JSON.stringify({ success: !job.removed, ...job }, null, 2) }],
          };
        } catch (error) {
          console.error("Error in job details:", error);
          return {
            content: [{ type: "text", text: JSON.stringify({ success: false, error: error.message, job: args.job }, null, 2) }],
            isError: true,
          };
        }
      }

      if (name === "check_ghost_job") {
        try {
          return { content: [{ type: "text", text: JSON.stringify(await checkGhostJob(args || {}), null, 2) }] };
        } catch (error) {
          return {
            content: [{ type: "text", text: JSON.stringify({ success: false, error: error.message }, null, 2) }],
            isError: true,
          };
        }
      }

      throw new Error(`Unknown tool: ${name}`);
    });
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("LinkedIn Jobs MCP server running on stdio");
  }
}

// One configured MCP server per connection (stdio, or one per HTTP request in stateless mode)
function createServer() {
  return new LinkedInJobsServer().server;
}

async function runStdio() {
  await new LinkedInJobsServer().run();
}

module.exports = { LinkedInJobsServer, createServer, runStdio };

if (require.main === module) {
  runStdio().catch(console.error);
}
