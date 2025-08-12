const linkedIn = require("./index");

const queryOptions = {
  keyword: "AI Engineer AND Machine Learning Engineer AND Data Scientist",
  location: "Nüremberg",
  dateSincePosted: "past Week",
  jobType: "full time",
  remoteFilter: "",
  salary: "80000",
  experienceLevel: "any",
  limit: "10",
  sortBy: "recent",
  page: "1",
  has_verification: false,
  under_10_applicants: false,
};

linkedIn.query(queryOptions).then((response) => {
  console.log(response); // An array of Job objects
});
