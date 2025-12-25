#!/usr/bin/env node
/**
 * LinkedIn Jobs MCP Server
 *
 * This is a proper Model Context Protocol (MCP) server that exposes
 * LinkedIn job search as a tool that can be used by any MCP client.
 *
 * Usage:
 *   node mcp-server.js
 *
 * This server uses stdio transport and can be configured in MCP clients.
 */

const { Server } = require("@modelcontextprotocol/sdk/server/index.js");
const { StdioServerTransport } = require("@modelcontextprotocol/sdk/server/stdio.js");
const { ListToolsRequestSchema, CallToolRequestSchema } = require("@modelcontextprotocol/sdk/types.js");
const linkedIn = require("../index");

// Create MCP server
const server = new Server(
  {
    name: "linkedin-jobs-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Define the LinkedIn job search tool
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "search_linkedin_jobs",
        description: "Search for jobs on LinkedIn with various filters including location, job type, date posted, and more",
        inputSchema: {
          type: "object",
          properties: {
            keyword: {
              type: "string",
              description: "Job title or keyword to search for (e.g., 'Software Engineer', 'Data Scientist')",
            },
            location: {
              type: "string",
              description: "Location for the job search (city, country, or 'Worldwide')",
            },
            city: {
              type: "string",
              description: "Specific city for the job search (optional, overrides location if provided)",
            },
            country: {
              type: "string",
              description: "Country for the job search (optional)",
            },
            geoId: {
              type: "string",
              description: "LinkedIn geographic ID (optional, if you know the specific geoId)",
            },
            dateSincePosted: {
              type: "string",
              description: "Filter by posting date",
              enum: ["past 24 hours", "past week", "past month"],
            },
            jobType: {
              type: "string",
              description: "Type of employment",
              enum: ["full time", "part time", "contract", "temporary", "volunteer", "internship"],
            },
            remoteFilter: {
              type: "string",
              description: "Remote work filter",
              enum: ["on site", "remote", "hybrid"],
            },
            limit: {
              type: "number",
              description: "Maximum number of results to return (default: 25)",
              default: 25,
            },
            sortBy: {
              type: "string",
              description: "Sort results by relevance or date",
              enum: ["recent", "relevant"],
            },
          },
          required: ["keyword", "location"],
        },
      },
    ],
  };
});

// Handle tool execution
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name !== "search_linkedin_jobs") {
    throw new Error(`Unknown tool: ${request.params.name}`);
  }

  try {
    const args = request.params.arguments || {};

    // Execute the LinkedIn job search
    const jobs = await linkedIn.query(args);

    // Format the results as text content
    let resultText = `Found ${jobs.length} job(s):\n\n`;

    jobs.forEach((job, index) => {
      resultText += `${index + 1}. ${job.position}\n`;
      resultText += `   Company: ${job.company}\n`;
      resultText += `   Location: ${job.location}\n`;
      if (job.salary && job.salary !== "Not specified") {
        resultText += `   Salary: ${job.salary}\n`;
      }
      if (job.agoTime) {
        resultText += `   Posted: ${job.agoTime}\n`;
      }
      resultText += `   URL: ${job.jobUrl}\n\n`;
    });

    return {
      content: [
        {
          type: "text",
          text: resultText,
        },
      ],
    };
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: `Error searching LinkedIn jobs: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
});

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("LinkedIn Jobs MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
