// Starts Ghost Job Radar, the ghost-job dashboard in radar/ (Python), together with the LinkedIn data API, and opens it.
// The first start creates a Python environment in the radar's data folder and installs the radar's packages.
const crypto = require("crypto");
const fs = require("fs");
const http = require("http");
const net = require("net");
const os = require("os");
const path = require("path");
const { spawn, spawnSync } = require("child_process");
const { version } = require("./package.json");

const MIN_PYTHON = [3, 11];

// Your database and .env (GHOSTRADAR_HOME moves them)
function radarHome() {
  if (process.env.GHOSTRADAR_HOME) return process.env.GHOSTRADAR_HOME;
  const base =
    process.platform === "win32"
      ? process.env.LOCALAPPDATA || path.join(os.homedir(), "AppData", "Local")
      : process.platform === "darwin"
        ? path.join(os.homedir(), "Library", "Application Support")
        : process.env.XDG_DATA_HOME || path.join(os.homedir(), ".local", "share");
  return path.join(base, "linkedin-jobs-mcp", "radar");
}

// The radar's code: next to this file (npm, source checkout), or unpacked from the Windows app
function radarCode(home) {
  let sea = null;
  try {
    sea = require("node:sea");
  } catch {
    // Node without single executable support
  }
  if (!sea || !sea.isSea()) return path.join(__dirname, "radar");
  const dir = path.join(home, `app-${version}`);
  if (!fs.existsSync(path.join(dir, ".complete"))) {
    for (const key of JSON.parse(sea.getAsset("radar-files.json", "utf8"))) {
      const target = path.join(dir, ...key.split("/").slice(1));
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.writeFileSync(target, Buffer.from(sea.getAsset(key)));
    }
    fs.writeFileSync(path.join(dir, ".complete"), "");
  }
  return dir;
}

function findPython() {
  const tries = process.platform === "win32" ? [["py", ["-3"]], ["python", []]] : [["python3", []], ["python", []]];
  for (const [cmd, pre] of tries) {
    const r = spawnSync(cmd, [...pre, "-c", "import sys; print(*sys.version_info[:2])"], { encoding: "utf8", windowsHide: true });
    if (r.status !== 0) continue;
    const [major, minor] = r.stdout.trim().split(" ").map(Number);
    if (major > MIN_PYTHON[0] || (major === MIN_PYTHON[0] && minor >= MIN_PYTHON[1])) return [cmd, pre];
  }
  return null;
}

function run(cmd, args) {
  const r = spawnSync(cmd, args, { stdio: "inherit", windowsHide: true });
  if (r.status !== 0) throw new Error(`Could not run ${path.basename(cmd)} ${args.slice(0, 3).join(" ")}`);
}

// A virtual environment in the data folder, reinstalled only when the requirements change
function pythonEnv(home, code) {
  const venv = path.join(home, "venv");
  const exe = process.platform === "win32" ? path.join(venv, "Scripts", "python.exe") : path.join(venv, "bin", "python");
  const requirements = path.join(code, "requirements.txt");
  const stamp = crypto.createHash("sha256").update(fs.readFileSync(requirements)).digest("hex").slice(0, 12);
  const marker = path.join(venv, `.installed-${stamp}`);
  if (fs.existsSync(marker)) return exe;
  if (!fs.existsSync(exe)) {
    const python = findPython();
    if (!python) throw new Error(`Ghost Job Radar needs Python ${MIN_PYTHON.join(".")} or newer: https://www.python.org/downloads/`);
    console.error("Creating the radar's Python environment (first start only)…");
    run(python[0], [...python[1], "-m", "venv", venv]);
  }
  console.error("Installing the radar's packages…");
  run(exe, ["-m", "pip", "install", "--disable-pip-version-check", "--quiet", "-r", requirements]);
  for (const old of fs.readdirSync(venv).filter((n) => n.startsWith(".installed-"))) fs.rmSync(path.join(venv, old));
  fs.writeFileSync(marker, "");
  return exe;
}

function linkedinApiFromEnvFile(home) {
  const file = path.join(home, ".env");
  if (!fs.existsSync(file)) return null;
  const line = fs.readFileSync(file, "utf8").split(/\r?\n/).find((l) => /^\s*LINKEDIN_JOBS_API\s*=/.test(l));
  return line ? line.split("=").slice(1).join("=").trim().replace(/^["']|["']$/g, "") || null : null;
}

const answers = (url) =>
  new Promise((resolve) => {
    http.get(url, (res) => {
      res.resume();
      resolve(res.statusCode === 200);
    }).on("error", () => resolve(false));
  });

const portFree = (port) =>
  new Promise((resolve) => {
    const probe = net.createServer().once("error", () => resolve(false));
    probe.once("listening", () => probe.close(() => resolve(true))).listen(port, "127.0.0.1");
  });

function openBrowser(url) {
  const [cmd, args] =
    process.platform === "win32" ? ["cmd", ["/c", "start", "", url]] : process.platform === "darwin" ? ["open", [url]] : ["xdg-open", [url]];
  spawn(cmd, args, { stdio: "ignore", detached: true, windowsHide: true }).on("error", () => {}).unref();
}

async function runRadar({ port = 8000, browser = true } = {}) {
  const url = `http://127.0.0.1:${port}/`;
  if (!(await portFree(port))) {
    if (await answers(`${url}api/meta`)) {
      console.error(`Ghost Job Radar is already running: ${url}`);
      if (browser) openBrowser(url);
      return;
    }
    throw new Error(`Port ${port} is in use; choose another with --port`);
  }
  const home = radarHome();
  fs.mkdirSync(home, { recursive: true });
  const code = radarCode(home);
  const python = pythonEnv(home, code);

  // the radar's LinkedIn source: your own setting, or this program's REST API on a free port
  let linkedinApi = process.env.LINKEDIN_JOBS_API || linkedinApiFromEnvFile(home);
  let api = null;
  if (!linkedinApi) {
    api = require("./api").startApi(0, "127.0.0.1");
    await new Promise((resolve) => api.once("listening", resolve));
    linkedinApi = `http://127.0.0.1:${api.address().port}`;
  }

  const radar = spawn(python, ["-m", "uvicorn", "ghostradar.main:app", "--host", "127.0.0.1", "--port", String(port), "--log-level", "warning"], {
    cwd: code,
    env: { ...process.env, GHOSTRADAR_HOME: home, LINKEDIN_JOBS_API: linkedinApi },
    stdio: "inherit",
  });
  const stop = () => {
    radar.kill();
    if (api) api.close();
  };
  process.once("SIGINT", stop);
  process.once("SIGTERM", stop);
  radar.on("exit", (exitCode) => {
    if (api) api.close();
    process.exit(exitCode ?? 0);
  });

  for (let waited = 0; waited < 90000; waited += 500) {
    if (await answers(`${url}api/meta`)) {
      console.error(`Ghost Job Radar: ${url}  (data in ${home}; Ctrl+C stops it)`);
      if (browser) openBrowser(url);
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  console.error("Ghost Job Radar did not start within 90 seconds.");
  stop();
}

module.exports = { runRadar, radarHome };
