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

async function mcpClient() {
  const [serverSide, clientSide] = InMemoryTransport.createLinkedPair();
  await createServer().connect(serverSide);
  const client = new Client({ name: "test", version: "1.0.0" });
  await client.connect(clientSide);
  return client;
}

test("the MCP server lists its tools", async () => {
  const client = await mcpClient();
  const { tools } = await client.listTools();
  assert.deepEqual(tools.map((t) => t.name), ["search_linkedin_jobs", "get_linkedin_job_details", "check_ghost_job"]);
  await client.close();
});

test("check_ghost_job asks Ghost Job Radar and shortens its answer", async () => {
  let asked = null;
  const radar = http.createServer((req, res) => {
    let body = "";
    req.on("data", (chunk) => (body += chunk));
    req.on("end", () => {
      asked = { path: req.url, body: JSON.parse(body) };
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({
        mode: "fetched",
        notes: [],
        sources_used: [],
        result: {
          posting: { title: "Data Engineer", company: "Example GmbH", location: "Berlin", url: "https://example.com/jobs/1" },
          score: {
            risk: 52, grade: "elevated", grade_label: "Elevated ghost-risk", confidence: "medium",
            types: [{ key: "stale", label: "Possibly filled or abandoned", score: 0.6 }, { key: "pool", label: "Candidate pool", score: 0.1 }],
            competition: { chance: "low", text: "120 applicants." },
            communication: { text: "No applications to this employer recorded yet." },
            advice: "Verify first.",
            reasons: [
              { label: "Online much longer than usual", fact: "Online for 300 days.", direction: "raises", points: 18 },
              { label: "No pay stated", fact: "Not scored.", direction: "info", points: 0 },
            ],
            caveats: [],
          },
        },
      }));
    });
  });
  await new Promise((resolve) => radar.listen(0, "127.0.0.1", resolve));
  process.env.GHOSTRADAR_URL = `http://127.0.0.1:${radar.address().port}`;
  const client = await mcpClient();
  try {
    const res = await client.callTool({ name: "check_ghost_job", arguments: { job: "https://example.com/jobs/1" } });
    const out = JSON.parse(res.content[0].text);
    assert.deepEqual(asked, { path: "/api/check", body: { url: "https://example.com/jobs/1", company: null, with_news: false } });
    assert.equal(out.ghost_risk.grade, "elevated");
    assert.deepEqual(out.patterns, [{ pattern: "Possibly filled or abandoned", strength: 0.6 }]);
    assert.deepEqual(out.reasons.map((r) => r.signal), ["Online much longer than usual"]);
    assert.equal(out.your_chance.chance, "low");
  } finally {
    await client.close();
    radar.close();
    delete process.env.GHOSTRADAR_URL;
  }
});

test("check_ghost_job says how to start the radar when it is not running", async () => {
  const closed = http.createServer();
  await new Promise((resolve) => closed.listen(0, "127.0.0.1", resolve));
  const { port } = closed.address();
  await new Promise((resolve) => closed.close(resolve));
  process.env.GHOSTRADAR_URL = `http://127.0.0.1:${port}`;
  const client = await mcpClient();
  try {
    const res = await client.callTool({ name: "check_ghost_job", arguments: { job: "Senior data engineer, Berlin" } });
    assert.equal(res.isError, true);
    assert.match(res.content[0].text, /linkedin-jobs-mcp radar/);
  } finally {
    await client.close();
    delete process.env.GHOSTRADAR_URL;
  }
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
