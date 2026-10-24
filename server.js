#!/usr/bin/env node

const { Server } = require("@modelcontextprotocol/sdk/server/index.js");
const { StdioServerTransport } = require("@modelcontextprotocol/sdk/server/stdio.js");
const {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} = require("@modelcontextprotocol/sdk/types.js");
const linkedIn = require("./index.js");
const { version } = require("./package.json");

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
