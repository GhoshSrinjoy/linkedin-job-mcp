const readline = require("readline");
const linkedIn = require("./index");

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

function ask(question, defaultValue = "") {
  return new Promise((resolve) => {
    rl.question(
      `${question}${defaultValue ? ` [${defaultValue}]` : ""}: `,
      (answer) => {
        resolve(answer && answer.trim() ? answer.trim() : defaultValue);
      }
    );
  });
}

async function run() {
  const defaults = {
    keyword: "software engineer",
    location: "Berlin, Germany",
    dateSincePosted: "past week",
    jobType: "full time",
    remoteFilter: "", // on site | remote | hybrid
    limit: "5",
    sortBy: "recent",
  };

  try {
    const keyword = await ask("Job title / keywords", defaults.keyword);
    const location = await ask("Location (city, country)", defaults.location);
    const dateSincePosted = await ask(
      "Date range (past 24 hours | past week | past month)",
      defaults.dateSincePosted
    );
    const jobType = await ask(
      "Job type (full time | part time | contract | temporary | volunteer | internship)",
      defaults.jobType
    );
    const remoteFilter = await ask(
      "Work type (on site | remote | hybrid)",
      defaults.remoteFilter
    );
    const limit = await ask("How many jobs to fetch", defaults.limit);
    const sortBy = await ask("Sort by (recent | relevant)", defaults.sortBy);

    const queryOptions = {
      keyword,
      location,
      dateSincePosted,
      jobType,
      remoteFilter,
      limit,
      sortBy,
    };

    const response = await linkedIn.query(queryOptions);

    console.log("\n" + "=".repeat(80));
    console.log("🎯 LINKEDIN JOB SEARCH RESULTS");
    console.log("=".repeat(80));
    console.log(`📍 Location: ${location}`);
    console.log(`🔍 Keywords: ${keyword}`);
    console.log(`📊 Found: ${response.length} jobs`);
    console.log("=".repeat(80));

    if (response.length === 0) {
      console.log("⚠️ No jobs found matching your criteria");
      return;
    }

    response.forEach((job, i) => {
      console.log(`\n${i + 1}. 💼 ${job.position}`);
      console.log(`   🏢 Company: ${job.company}`);
      console.log(`   📍 Location: ${job.location}`);
      if (job.salary && job.salary !== "Not specified") {
        console.log(`   💰 Salary: ${job.salary}`);
      }
      if (job.date) {
        console.log(`   📅 Posted: ${job.agoTime || job.date}`);
      }
      if (job.jobUrl) {
        console.log(`   🔗 Apply: ${job.jobUrl}`);
      }
      console.log(`   ${"─".repeat(60)}`);
    });

    console.log(
      `\n📈 Summary: ${response.length} job opportunities found in ${location}`
    );
  } catch (error) {
    console.error("⚠️ Error:", error.message);
  } finally {
    rl.close();
  }
}

run();
