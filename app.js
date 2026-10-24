#!/usr/bin/env node
// Entry point of the Windows app (and of `npm run app`): the MCP server for the apps that start it,
// the REST API with MCP over HTTP, connecting MCP clients, and a small command line.
const fs = require("fs");
const os = require("os");
const path = require("path");
const readline = require("readline");
const { spawn } = require("child_process");
const { version } = require("./package.json");
const { CLIENTS, find } = require("./clients");

const APP = "linkedin-jobs-mcp";

const USAGE = `LinkedIn Jobs MCP ${version}
Job search and job details for MCP apps. It has no window: the apps you connect start it in the background.

Usage: ${APP} <command> [options]

  install                 copy the app to your user programs folder and connect the apps found
  connect [app ...]       connect the apps found, or only the named apps
  disconnect [app ...]    remove the connection from every app, or only from the named apps
  status                  which apps are found and connected
  config [app ...]        print the settings to add by hand
  uninstall               disconnect every app and remove the installed copy
  mcp                     MCP server over stdio (what connected apps run)
  serve [--port 3000] [--host 127.0.0.1]
                          REST API plus MCP over HTTP at http://127.0.0.1:3000/mcp
  job <id or url>         one job's details as JSON
  search [options]        search jobs (search --help lists the options)
  --version, --help

Apps: ${CLIENTS.map((c) => c.id).join(", ")}
Without a command it shows a setup menu in a console window, and runs the MCP server when an app starts it.`;

function isSea() {
  try {
    return require("node:sea").isSea();
  } catch {
    return false;
  }
}

const installDir = () =>
  path.join(process.env.LOCALAPPDATA || path.join(os.homedir(), "AppData", "Local"), "Programs", APP);
const installedExe = () => path.join(installDir(), `${APP}.exe`);
const samePath = (a, b) => path.resolve(a).toLowerCase() === path.resolve(b).toLowerCase();

// What an MCP client runs: this program with the "mcp" command
function launchCommand(exe) {
  if (exe) return { command: exe, args: ["mcp"] };
  if (isSea()) return { command: process.execPath, args: ["mcp"] };
  // started through npx: its cache folder can be cleared, so the apps start it through npx too
  if (/[\\/]_npx[\\/]/.test(__dirname)) {
    const npx = ["npx", "-y", APP, "mcp"];
    return process.platform === "win32" ? { command: "cmd", args: ["/c", ...npx] } : { command: npx[0], args: npx.slice(1) };
  }
  return { command: process.execPath, args: [__filename, "mcp"] };
}

// The program connected apps should run: the installed copy once there is one
const preferredCommand = () => launchCommand(isSea() && fs.existsSync(installedExe()) ? installedExe() : undefined);

function parseOptions(args) {
  const opts = { _: [] };
  for (let i = 0; i < args.length; i += 1) {
    const m = args[i].match(/^--?([\w-]+)(?:=(.*))?$/);
    if (!m) opts._.push(args[i]);
    else if (m[2] !== undefined) opts[m[1]] = m[2];
    else if (args[i + 1] !== undefined && !args[i + 1].startsWith("-")) opts[m[1]] = args[++i];
    else opts[m[1]] = true;
  }
  return opts;
}

const indent = (text, pad = "      ") => text.split("\n").join(`\n${pad}`);

function table(rows) {
  const widths = rows[0].map((_, i) => Math.max(...rows.map((r) => r[i].length)));
  for (const row of rows) console.log(`  ${row.map((cell, i) => cell.padEnd(widths[i])).join("   ")}`.trimEnd());
}

function connectedText(registered, current) {
  if (!registered) return "no";
  if (!path.isAbsolute(registered)) return "yes";
  if (!fs.existsSync(registered)) return "yes, program missing";
  return samePath(registered, current.command) ? "yes" : "yes, other copy";
}

function status() {
  const current = preferredCommand();
  console.log(`LinkedIn Jobs MCP ${version}`);
  console.log(`Program apps run: ${[current.command, ...current.args].join(" ")}`);
  if (isSea() && !fs.existsSync(installedExe())) console.log("Not installed yet: install keeps a copy in your user programs folder.");
  console.log("");
  table([
    ["App", "Found", "Connected", "Settings"],
    ...CLIENTS.map((c) => {
      const registered = c.registered();
      const detected = c.detect();
      return [c.label, detected ? "yes" : "no", connectedText(registered, current), detected || registered ? c.where() : ""];
    }),
  ]);
}

function report(results, done) {
  if (!results.length) return;
  for (const { client, ok, message } of results) {
    console.log(`  ${(ok ? done : "not done").padEnd(12)} ${client.label.padEnd(17)} ${indent(message, " ".repeat(33))}`);
  }
}

function each(clients, action) {
  return clients.map((client) => {
    try {
      return { client, ...action(client) };
    } catch (err) {
      return { client, ok: false, message: err.message };
    }
  });
}

function connect(clients, cmd = preferredCommand()) {
  if (!clients.length) {
    console.log("No supported app found. Name one to set it up anyway, for example: connect vscode");
    return;
  }
  report(each(clients, (c) => c.connect(cmd)), "connected");
  console.log("\nRestart these apps (or reload their MCP servers) to load the tools.");
  if (isSea() && !samePath(cmd.command, installedExe())) {
    console.log(`They run ${cmd.command}; keep it there, or use install for a permanent copy.`);
  }
}

function disconnect(clients) {
  if (!clients.length) {
    console.log("No app is connected.");
    return;
  }
  report(each(clients, (c) => c.disconnect()), "removed");
}

function printConfig(clients, cmd = preferredCommand()) {
  for (const c of clients) {
    console.log(`${c.label} (${c.where()}):`);
    console.log(`  ${indent(c.snippet(cmd), "  ")}\n`);
  }
  console.log("Apps that connect by URL: run serve and add http://127.0.0.1:3000/mcp");
}

function install() {
  if (!isSea()) {
    console.log("install is for the Windows app. Connect your apps with: linkedin-jobs-mcp connect");
    return;
  }
  const target = installedExe();
  if (!samePath(process.execPath, target)) {
    fs.mkdirSync(installDir(), { recursive: true });
    // an app may be running the old copy: Windows lets a running program be renamed, not replaced
    if (fs.existsSync(target)) fs.renameSync(target, `${target}.${Date.now()}.old`);
    fs.copyFileSync(process.execPath, target);
  }
  for (const name of fs.readdirSync(installDir()).filter((n) => n.endsWith(".old"))) {
    try {
      fs.rmSync(path.join(installDir(), name), { force: true });
    } catch {
      // still running; removed by a later install or uninstall
    }
  }
  console.log(`Installed ${target}\n`);
  connect(
    CLIENTS.filter((c) => c.detect()),
    launchCommand(target)
  );
}

function uninstall() {
  disconnect(CLIENTS.filter((c) => c.registered()));
  const dir = installDir();
  if (!fs.existsSync(dir)) return;
  if (isSea() && samePath(path.dirname(process.execPath), dir)) {
    // a running program cannot delete itself: a helper removes the folder once this one has closed
    const cmd = `ping -n 3 127.0.0.1 >nul & rmdir /s /q "${dir}"`;
    spawn(process.env.ComSpec || "cmd.exe", ["/d", "/c", cmd], {
      detached: true,
      stdio: "ignore",
      windowsHide: true,
      windowsVerbatimArguments: true,
    }).unref();
    console.log(`\n${dir} is removed when this program closes.`);
    return;
  }
  try {
    fs.rmSync(dir, { recursive: true, force: true });
    console.log(`\nRemoved ${dir}`);
  } catch (err) {
    console.log(`\nCould not remove ${dir} (${err.code}): close the apps that use it, then delete the folder.`);
  }
}

async function mcp() {
  // stdout carries the protocol, so any other output goes to stderr
  console.log = console.error;
  await require("./server").runStdio();
}

function serve(opts) {
  const { API_PORT, API_HOST } = require("./config");
  const port = Number(opts.port || opts.p || API_PORT);
  const host = String(opts.host || API_HOST);
  if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error(`Not a port: ${opts.port || opts.p}`);
  const server = require("./api").startApi(port, host);
  server.on("listening", () => console.error("Ctrl+C stops it."));
  server.on("error", (err) => {
    console.error(err.code === "EADDRINUSE" ? `Port ${port} is in use; choose another with --port` : err.message);
    process.exit(1);
  });
}

async function job(ref) {
  if (!ref) throw new Error(`Usage: ${APP} job <LinkedIn job id or URL>`);
  const details = await require("./index").getJobDetails(ref);
  console.log(JSON.stringify(details, null, 2));
}

async function menu() {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  // the iterator keeps lines typed ahead; the end of input quits
  const lines = rl[Symbol.asyncIterator]();
  const ask = async (question) => {
    process.stdout.write(question);
    const { value, done } = await lines.next();
    return done ? "q" : value.trim().toLowerCase();
  };
  const actions = {
    1: () => (isSea() ? install() : connect(CLIENTS.filter((c) => c.detect()))),
    2: () => disconnect(CLIENTS.filter((c) => c.registered())),
    3: () => printConfig(CLIENTS),
  };
  for (;;) {
    console.log("");
    status();
    console.log(`
  1  ${isSea() ? "Install and connect the apps found" : "Connect the apps found"}
  2  Disconnect from every app
  3  Show the settings to add by hand
  4  Start the HTTP server (http://127.0.0.1:3000/mcp)
  q  Quit
`);
    const choice = await ask("Choose: ");
    if (choice === "q") break;
    if (choice === "4") {
      rl.close();
      serve({});
      return;
    }
    if (!actions[choice]) continue;
    console.log("");
    try {
      actions[choice]();
    } catch (err) {
      console.log(`Failed: ${err.message}`);
    }
    await ask("\nPress Enter to go back to the menu ");
  }
  rl.close();
}

async function main([command, ...rest]) {
  const opts = parseOptions(rest);
  const named = () => (opts._.length ? find(opts._) : null);
  switch (command) {
    case undefined:
      return process.stdin.isTTY ? menu() : mcp();
    case "mcp":
      return mcp();
    case "serve":
      return serve(opts);
    case "install":
      return install();
    case "uninstall":
      return uninstall();
    case "connect":
      return connect(named() || CLIENTS.filter((c) => c.detect()));
    case "disconnect":
      return disconnect(named() || CLIENTS.filter((c) => c.registered()));
    case "status":
      return status();
    case "config":
      return printConfig(named() || CLIENTS);
    case "job":
      return job(opts._[0]);
    case "search":
      return require("./bin/linkedin-jobs").main(rest, `${APP} search`);
    case "version":
    case "--version":
    case "-v":
      return console.log(version);
    case "help":
    case "--help":
    case "-h":
      return console.log(USAGE);
    default:
      throw new Error(`Unknown command: ${command}\n\n${USAGE}`);
  }
}

main(process.argv.slice(2)).catch((err) => {
  console.error(err.message);
  process.exitCode = 1;
});
