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
            description: "Search for LinkedIn jobs with various filters",
            inputSchema: {
              type: "object",
              properties: {
                keyword: {
                  type: "string",
                  description: "Job search keyword (e.g., 'software engineer')",
                  default: "",
                },
                location: {
                  type: "string",
                  description: "Location to search for jobs (e.g., 'Berlin, Germany')",
                  default: "",
                },
                city: {
                  type: "string",
                  description: "Optional city to refine location (e.g., 'Berlin')",
                  default: "",
                },
                country: {
                  type: "string",
                  description: "Optional country to refine location (e.g., 'Germany')",
                  default: "",
                },
                geoId: {
                  type: "string",
                  description: "Optional LinkedIn geoId to bypass location guessing (e.g., '103644278')",
                  default: "",
                },
                dateSincePosted: {
                  type: "string",
                  description: "Date range for job posting",
                  enum: ["past month", "past week", "past 24 hours", "24hr", "today"],
                  default: "",
                },
                jobType: {
                  type: "string",
                  description: "Type of employment",
                  enum: ["full time", "part time", "contract", "temporary", "volunteer", "internship"],
                  default: "",
                },
                remoteFilter: {
                  type: "string",
                  description: "Remote work preference",
                  enum: ["on site", "remote", "hybrid"],
                  default: "",
                },
                salary: {
                  type: "string",
                  description: "Minimum salary",
                  enum: ["40000", "60000", "80000", "100000", "120000"],
                  default: "",
                },
                experienceLevel: {
                  type: "string",
                  description: "Experience level required",
                  enum: ["internship", "entry level", "associate", "senior", "director", "executive"],
                  default: "",
                },
                limit: {
                  type: "string",
                  description: "Maximum number of jobs to return",
                  default: "10",
                },
                sortBy: {
                  type: "string",
                  description: "Sort results by",
                  enum: ["recent", "relevant"],
                  default: "recent",
                },
                page: {
                  type: "string",
                  description: "Page number (0-based)",
                  default: "0",
                },
                has_verification: {
                  type: "boolean",
                  description: "Filter for verified jobs only",
                  default: false,
                },
                under_10_applicants: {
                  type: "boolean",
                  description: "Filter for jobs with under 10 applicants",
                  default: false,
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
            salary: args.salary || "",
            experienceLevel: args.experienceLevel || "",
            limit: args.limit || "10",
            sortBy: args.sortBy || "recent",
            page: args.page || "0",
            has_verification: args.has_verification || false,
            under_10_applicants: args.under_10_applicants || false,
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
