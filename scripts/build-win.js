// Builds the Windows app: one .exe with Node.js and the server inside (a Node.js single executable application).
// Run on Windows with Node.js 20 or newer: npm run build:win. esbuild and postject are fetched by npx at fixed versions.
const { execSync } = require("child_process");
const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

const ESBUILD = "esbuild@0.25.12";
const POSTJECT = "postject@1.0.0-alpha.6";
const FUSE = "NODE_SEA_FUSE_fce680ab2cc467b6e072b8b5df1996b2";

const root = path.join(__dirname, "..");
const dist = path.join(root, "dist");
const bundle = path.join(dist, "app.cjs");
const blob = path.join(dist, "sea-prep.blob");
const seaConfig = path.join(dist, "sea-config.json");
const exe = path.join(dist, "linkedin-jobs-mcp.exe");

const q = (p) => `"${p}"`;
const run = (cmd) => execSync(cmd, { cwd: root, stdio: "inherit" });

const major = Number(process.versions.node.split(".")[0]);
if (process.platform !== "win32") throw new Error("Build the Windows app on Windows");
if (major < 20) throw new Error("Building the app needs Node.js 20 or newer");

fs.rmSync(dist, { recursive: true, force: true });
fs.mkdirSync(dist);

// 1. one CommonJS file with every dependency
run(`npx --yes ${ESBUILD} app.js --bundle --platform=node --target=node${major} --format=cjs --log-level=warning --outfile=${q(bundle)}`);

// 2. Ghost Job Radar's code travels inside the app as assets; the radar command unpacks it on first use
const radarFiles = [path.join(root, "radar", "requirements.txt"), path.join(root, "radar", "data", "ba_engpass.csv")];
(function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name !== "__pycache__") walk(full);
    } else if (!entry.name.endsWith(".pyc")) {
      radarFiles.push(full);
    }
  }
})(path.join(root, "radar", "ghostradar"));
const assets = Object.fromEntries(radarFiles.map((f) => [path.relative(root, f).split(path.sep).join("/"), f]));
fs.writeFileSync(path.join(dist, "radar-files.json"), JSON.stringify(Object.keys(assets)));
assets["radar-files.json"] = path.join(dist, "radar-files.json");

// 3. the blob Node.js runs at start, injected into a copy of this node.exe
fs.writeFileSync(seaConfig, JSON.stringify({ main: bundle, output: blob, disableExperimentalSEAWarning: true, assets }, null, 2));
run(`${q(process.execPath)} --experimental-sea-config ${q(seaConfig)}`);
fs.copyFileSync(process.execPath, exe);
run(`npx --yes ${POSTJECT} ${q(exe)} NODE_SEA_BLOB ${q(blob)} --sentinel-fuse ${FUSE}`);

const hash = crypto.createHash("sha256").update(fs.readFileSync(exe)).digest("hex");
fs.writeFileSync(`${exe}.sha256`, `${hash}  ${path.basename(exe)}\n`);
console.log(`\nBuilt ${path.relative(root, exe)} (${Math.round(fs.statSync(exe).size / 1e6)} MB, Node.js ${process.versions.node})`);
console.log(`SHA-256 ${hash}`);
