#!/usr/bin/env node
const yargs = require("yargs/yargs");
const { hideBin } = require("yargs/helpers");
const { query } = require("../index");

async function main() {
  const argv = yargs(hideBin(process.argv))
    .scriptName("linkedin-jobs")
    .usage("$0 [options]")
    .option("keyword", {
      alias: "k",
      type: "string",
      describe: "Job search keywords/title",
    })
    .option("location", {
      alias: "l",
      type: "string",
      describe: "Location (city, country)",
    })
    .option("city", { type: "string", describe: "City override" })
    .option("country", { type: "string", describe: "Country override" })
    .option("geoId", { type: "string", describe: "LinkedIn geoId override" })
    .option("dateSincePosted", {
      alias: "d",
      type: "string",
      describe: "Date filter: past 24 hours | past week | past month",
    })
    .option("jobType", {
      type: "string",
      describe: "Job type: full time | part time | contract | temporary | volunteer | internship",
    })
    .option("remoteFilter", {
      alias: "r",
      type: "string",
      describe: "Work type: on site | remote | hybrid",
    })
    .option("limit", {
      alias: "n",
      type: "number",
      default: 10,
      describe: "Max results to return",
    })
    .option("sortBy", {
      type: "string",
      default: "recent",
      describe: "Sort order: recent | relevant",
    })
    .help()
    .alias("h", "help").argv;

  try {
    const results = await query(argv);
    console.log(JSON.stringify({ total: results.length, jobs: results }, null, 2));
  } catch (err) {
    console.error("Error:", err.message);
    process.exit(1);
  }
}

main();
