// Offline tests: job pages, client settings files, the MCP server and the HTTP API. Nothing here calls LinkedIn.
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const http = require("http");
const os = require("os");
const path = require("path");
const { InMemoryTransport } = require("@modelcontextprotocol/sdk/inMemory.js");
const { Client } = require("@modelcontextprotocol/sdk/client/index.js");
const { jobIdFrom, parseJobPage } = require("../index");
const { find, withoutTable, tomlCommand } = require("../clients");
const { createServer } = require("../server");
const { startApi } = require("../api");

test("job ids come from ids and LinkedIn links", () => {
  assert.equal(jobIdFrom("1234567890"), "1234567890");
  assert.equal(jobIdFrom("https://www.linkedin.com/jobs/view/data-engineer-at-example-1234567890/"), "1234567890");
  assert.equal(jobIdFrom("https://www.linkedin.com/jobs/search/?currentJobId=1234567890"), "1234567890");
  assert.equal(jobIdFrom("not a job"), null);
});

test("a public job page is read", () => {
  const html = `<html><body>
    <h2 class="top-card-layout__title">Data Engineer (m/w/d)</h2>
    <a class="topcard__org-name-link">Example GmbH</a>
    <span class="topcard__flavor--bullet">Berlin, Germany</span>
    <span class="posted-time-ago__text">3 weeks ago</span>
    <figcaption class="num-applicants__caption">Over 200 applicants</figcaption>
    <ul><li class="description__job-criteria-item">
      <h3 class="description__job-criteria-subheader">Seniority level</h3>
      <span class="description__job-criteria-text">Mid-Senior level</span></li></ul>
    <div class="show-more-less-html__markup"><p>Build data pipelines.</p><ul><li>Python</li></ul></div>
  </body></html>`;
  const job = parseJobPage(html, "1234567890");
  assert.equal(job.position, "Data Engineer (m/w/d)");
  assert.equal(job.company, "Example GmbH");
  assert.equal(job.location, "Berlin, Germany");
  assert.equal(job.applicants, "Over 200 applicants");
  assert.equal(job.seniority, "Mid-Senior level");
  assert.equal(job.acceptingApplications, true);
  assert.match(job.description, /Build data pipelines\.\n+• Python/);
});

test("connecting keeps the other servers and settings", () => {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), "linkedin-jobs-"));
  const saved = { HOME: process.env.HOME, USERPROFILE: process.env.USERPROFILE, CODEX_HOME: process.env.CODEX_HOME };
  process.env.HOME = home;
  process.env.USERPROFILE = home;
  process.env.CODEX_HOME = path.join(home, ".codex");
  try {
    const cmd = { command: path.join(home, "linkedin-jobs-mcp.exe"), args: ["mcp"] };
    const [codex, cursor] = find(["codex", "cursor"]);

    const json = path.join(home, ".cursor", "mcp.json");
    fs.mkdirSync(path.dirname(json));
    fs.writeFileSync(json, JSON.stringify({ mcpServers: { other: { command: "other" } } }, null, 4));
    assert.equal(cursor.connect(cmd).ok, true);
    assert.deepEqual(Object.keys(JSON.parse(fs.readFileSync(json, "utf8")).mcpServers), ["other", "linkedin-jobs"]);
    assert.match(fs.readFileSync(json, "utf8"), /^ {4}"mcpServers"/m);
    assert.equal(cursor.registered(), cmd.command);
    assert.ok(fs.existsSync(`${json}.linkedin-jobs.bak`));
    cursor.disconnect();
    assert.equal(cursor.registered(), null);

    const toml = path.join(process.env.CODEX_HOME, "config.toml");
    fs.mkdirSync(process.env.CODEX_HOME);
    fs.writeFileSync(toml, 'model = "x"\n\n[mcp_servers.other]\ncommand = "other"\n');
    codex.connect(cmd);
    assert.equal(codex.registered(), cmd.command);
    codex.disconnect();
    assert.equal(codex.registered(), null);
    assert.match(fs.readFileSync(toml, "utf8"), /\[mcp_servers\.other\]/);
  } finally {
    for (const [key, value] of Object.entries(saved)) {
      if (value === undefined) delete process.env[key];
      else process.env[key] = value;
    }
    fs.rmSync(home, { recursive: true, force: true });
  }
});

test("only the linkedin-jobs table is removed from TOML", () => {
  const text = 'a = 1\n\n[mcp_servers."linkedin-jobs"]\ncommand = "old"\n\n[mcp_servers.linkedin-jobs.env]\nX = "1"\n\n[other]\nb = 2\n';
  assert.equal(withoutTable(text), "a = 1\n\n[other]\nb = 2");
  assert.equal(tomlCommand(text), "old");
});

test("the MCP server lists both tools", async () => {
  const [serverSide, clientSide] = InMemoryTransport.createLinkedPair();
  await createServer().connect(serverSide);
  const client = new Client({ name: "test", version: "1.0.0" });
  await client.connect(clientSide);
  const { tools } = await client.listTools();
  assert.deepEqual(tools.map((t) => t.name), ["search_linkedin_jobs", "get_linkedin_job_details"]);
  await client.close();
});

test("the HTTP API answers on this computer and refuses other hosts", async () => {
  const server = startApi(0, "127.0.0.1");
  await new Promise((resolve) => server.once("listening", resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  try {
    assert.deepEqual(await (await fetch(`${base}/health`)).json(), { ok: true });

    const res = await fetch(`${base}/mcp`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json, text/event-stream" },
      body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "tools/list" }),
    });
    assert.match(await res.text(), /get_linkedin_job_details/);

    const status = await new Promise((resolve, reject) => {
      http.get(`${base}/health`, { headers: { Host: "evil.example" } }, (r) => {
        r.resume();
        resolve(r.statusCode);
      }).on("error", reject);
    });
    assert.equal(status, 403);
  } finally {
    server.closeAllConnections();
    server.close();
  }
});
