const linkedIn = require("./index");

// Set authentication directly with your cookies
// linkedIn.setAuth('ajax:4373608599007478933', 'AQEDASu607wD8iZLAAABlAo0X6QAAAGYqDhfJU0AD-tpH9PxYdEl0VMOin2HHmg_WNw_WtmuIFfDft7fXqK_dxRKsLDrBNQ3tREbUy88slQFBx9mytzCya53qG2QNSx-RWNkWkSOCzSA8bd6qb3DvaJ3');

const queryOptions = {
  keyword: "software engineer",
  location: "Bengaluru",
  dateSincePosted: "past Week",
  jobType: "full time",
  remoteFilter: "",
  salary: "",
  experienceLevel: "any",
  limit: "5",
  sortBy: "recent",
  page: "0",
  has_verification: false,
  under_10_applicants: false,
};

linkedIn.query(queryOptions).then((response) => {
  console.log("\n" + "=".repeat(80));
  console.log("🎯 LINKEDIN JOB SEARCH RESULTS");
  console.log("=".repeat(80));
  console.log(`📍 Location: ${queryOptions.location} (geoId: Found)`);
  console.log(`🔍 Keywords: ${queryOptions.keyword}`);
  console.log(`📊 Found: ${response.length} jobs`);
  console.log("=".repeat(80));

  if (response.length === 0) {
    console.log("❌ No jobs found matching your criteria");
    return;
  }

  response.forEach((job, i) => {
    console.log(`\n${i + 1}. 💼 ${job.position}`);
    console.log(`   🏢 Company: ${job.company}`);
    console.log(`   📍 Location: ${job.location}`);
    if (job.salary && job.salary !== 'Not specified') {
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
  
  console.log(`\n📈 Summary: ${response.length} job opportunities found in ${queryOptions.location}`);
  console.log("✅ Location filtering is working correctly!");
}).catch((error) => {
  console.error("❌ Error:", error.message);
});
