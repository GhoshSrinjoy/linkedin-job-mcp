// The MCP clients the app can connect to: each one starts the app itself (stdio) when it needs the tools.
// Settings files are merged, never replaced: other servers and settings stay, the first change keeps a copy
// next to the file (<file>.linkedin-jobs.bak), and a file that is not plain JSON (for example with comments)
// is left unchanged with the entry to add by hand instead.
const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawnSync } = require("child_process");

const NAME = "linkedin-jobs";
const BACKUP = `.${NAME}.bak`;

const home = (...parts) => path.join(os.homedir(), ...parts);

function appData(...parts) {
  if (process.platform === "win32") return path.join(process.env.APPDATA || home("AppData", "Roaming"), ...parts);
  if (process.platform === "darwin") return home("Library", "Application Support", ...parts);
  return path.join(process.env.XDG_CONFIG_HOME || home(".config"), ...parts);
}

const quote = (arg) => (/[\s"&|<>^()%!,;=]/.test(arg) ? `"${arg.replace(/"/g, '\\"')}"` : arg);

function runCli(cmd, args) {
  // npm-installed tools are .cmd files on Windows, which only start through the shell, so arguments are quoted here
  const shell = process.platform === "win32";
  const r = spawnSync(cmd, shell ? args.map(quote) : args, { encoding: "utf8", shell, windowsHide: true });
  return { ok: r.status === 0, out: `${r.stdout || ""}${r.stderr || ""}`.trim() };
}

const found = new Map();
function onPath(cmd) {
  if (!found.has(cmd)) {
    const r = spawnSync(process.platform === "win32" ? "where" : "which", [cmd], { encoding: "utf8", windowsHide: true });
    found.set(cmd, r.status === 0);
  }
  return found.get(cmd);
}

function readJson(file) {
  if (!fs.existsSync(file)) return { data: {}, existed: false, indent: 2, crlf: false };
  const text = fs.readFileSync(file, "utf8").replace(/^﻿/, "");
  const style = { existed: true, indent: (text.match(/^([ \t]+)"/m) || [null, 2])[1], crlf: text.includes("\r\n") };
  if (!text.trim()) return { data: {}, ...style };
  try {
    const data = JSON.parse(text);
    if (data && typeof data === "object" && !Array.isArray(data)) return { data, ...style };
  } catch {
    // comments or trailing commas: handled below
  }
  return { error: `${file} is not plain JSON (it may contain comments), so it was left unchanged` };
}

function writeText(file, text, existed, crlf = false) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  if (existed && !fs.existsSync(file + BACKUP)) fs.copyFileSync(file, file + BACKUP);
  fs.writeFileSync(file, crlf ? text.replace(/\r?\n/g, "\r\n") : text);
}

const writeJson = (file, r) => writeText(file, `${JSON.stringify(r.data, null, r.indent)}\n`, r.existed, r.crlf);

const describe = (server) => (server ? server.command || server.url || "(registered)" : null);

function jsonClient({ id, label, file, key, entry, detect }) {
  return {
    id,
    label,
    where: file,
    detect: () => fs.existsSync(detect()),
    registered() {
      const r = readJson(file());
      return r.error ? null : describe(r.data[key] && r.data[key][NAME]);
    },
    connect(cmd) {
      const target = file();
      const r = readJson(target);
      if (r.error) return { ok: false, message: `${r.error}. Add this:\n${this.snippet(cmd)}` };
      if (!r.data[key] || typeof r.data[key] !== "object") r.data[key] = {};
      r.data[key][NAME] = entry(cmd);
      writeJson(target, r);
      return { ok: true, message: target };
    },
    disconnect() {
      const target = file();
      const r = readJson(target);
      if (r.error) return { ok: false, message: r.error };
      if (!(r.data[key] && r.data[key][NAME])) return { ok: true, message: "was not connected" };
      delete r.data[key][NAME];
      writeJson(target, r);
      return { ok: true, message: target };
    },
    snippet: (cmd) => JSON.stringify({ [key]: { [NAME]: entry(cmd) } }, null, 2),
  };
}

// Codex: ~/.codex/config.toml (CODEX_HOME moves it). Only our own table is rewritten, line by line.
const TABLE = `mcp_servers.${NAME}`;

function tableName(line) {
  const m = line.trim().match(/^\[\[?([^\]]+)\]\]?\s*(?:#.*)?$/);
  if (!m) return null;
  return m[1]
    .split(".")
    .map((part) => part.trim().replace(/^(["'])(.*)\1$/, "$2"))
    .join(".");
}

const ours = (name) => name === TABLE || name.startsWith(`${TABLE}.`);

function withoutTable(text) {
  const kept = [];
  let skipping = false;
  for (const line of text.split(/\r?\n/)) {
    const name = tableName(line);
    if (name !== null) skipping = ours(name);
    if (!skipping) kept.push(line);
  }
  return kept.join("\n").replace(/\n{3,}/g, "\n\n").trimEnd();
}

function tomlCommand(text) {
  let inside = false;
  let registered = null;
  for (const line of text.split(/\r?\n/)) {
    const name = tableName(line);
    if (name !== null) {
      inside = name === TABLE;
      if (inside) registered = registered || "(registered)";
      continue;
    }
    const m = inside && line.match(/^\s*command\s*=\s*("(?:[^"\\]|\\.)*"|'[^']*')/);
    if (m) {
      try {
        registered = m[1].startsWith("'") ? m[1].slice(1, -1) : JSON.parse(m[1]);
      } catch {
        registered = "(registered)";
      }
    }
  }
  return registered;
}

const tomlBlock = (cmd) =>
  `[${TABLE}]\ncommand = ${JSON.stringify(cmd.command)}\nargs = [${cmd.args.map((a) => JSON.stringify(a)).join(", ")}]\n`;

const codexHome = () => process.env.CODEX_HOME || home(".codex");

const codex = {
  id: "codex",
  label: "Codex",
  where: () => path.join(codexHome(), "config.toml"),
  detect: () => fs.existsSync(codexHome()) || onPath("codex"),
  registered() {
    const file = this.where();
    return fs.existsSync(file) ? tomlCommand(fs.readFileSync(file, "utf8")) : null;
  },
  connect(cmd) {
    const file = this.where();
    const existed = fs.existsSync(file);
    const text = existed ? fs.readFileSync(file, "utf8") : "";
    const kept = withoutTable(text);
    writeText(file, `${kept ? `${kept}\n\n` : ""}${tomlBlock(cmd)}`, existed, text.includes("\r\n"));
    return { ok: true, message: file };
  },
  disconnect() {
    const file = this.where();
    if (!this.registered()) return { ok: true, message: "was not connected" };
    const text = fs.readFileSync(file, "utf8");
    const kept = withoutTable(text);
    writeText(file, kept ? `${kept}\n` : "", true, text.includes("\r\n"));
    return { ok: true, message: file };
  },
  snippet: (cmd) => tomlBlock(cmd).trimEnd(),
};

// Claude Code keeps its settings in a state file it rewrites often, so its own command adds the server
const claudeState = () => path.join(process.env.CLAUDE_CONFIG_DIR || os.homedir(), ".claude.json");

const claudeCode = {
  id: "claude-code",
  label: "Claude Code",
  where: () => "claude mcp, user scope",
  detect: () => onPath("claude") || fs.existsSync(claudeState()),
  registered() {
    const r = readJson(claudeState());
    if (r.existed && !r.error) return describe(r.data.mcpServers && r.data.mcpServers[NAME]);
    return onPath("claude") && runCli("claude", ["mcp", "get", NAME]).ok ? "(registered)" : null;
  },
  connect(cmd) {
    if (!onPath("claude")) return { ok: false, message: `the claude command was not found. Run:\n${this.snippet(cmd)}` };
    runCli("claude", ["mcp", "remove", "--scope", "user", NAME]);
    const r = runCli("claude", ["mcp", "add", "--scope", "user", NAME, "--", cmd.command, ...cmd.args]);
    return { ok: r.ok, message: r.ok ? "claude mcp add, user scope" : r.out || "claude mcp add failed" };
  },
  disconnect() {
    if (!onPath("claude")) return { ok: false, message: `the claude command was not found. Run: claude mcp remove --scope user ${NAME}` };
    const r = runCli("claude", ["mcp", "remove", "--scope", "user", NAME]);
    return { ok: true, message: r.ok ? "claude mcp remove, user scope" : "was not connected" };
  },
  snippet: (cmd) => `claude mcp add --scope user ${NAME} -- ${[cmd.command, ...cmd.args].map(quote).join(" ")}`,
};

const stdio = (cmd) => ({ command: cmd.command, args: cmd.args });

const CLIENTS = [
  claudeCode,
  codex,
  jsonClient({
    id: "vscode", label: "VS Code", key: "servers",
    file: () => appData("Code", "User", "mcp.json"), detect: () => appData("Code", "User"),
    entry: (cmd) => ({ type: "stdio", ...stdio(cmd) }),
  }),
  jsonClient({
    id: "vscode-insiders", label: "VS Code Insiders", key: "servers",
    file: () => appData("Code - Insiders", "User", "mcp.json"), detect: () => appData("Code - Insiders", "User"),
    entry: (cmd) => ({ type: "stdio", ...stdio(cmd) }),
  }),
  jsonClient({
    id: "claude-desktop", label: "Claude Desktop", key: "mcpServers",
    file: () => appData("Claude", "claude_desktop_config.json"), detect: () => appData("Claude"),
    entry: stdio,
  }),
  jsonClient({
    id: "cursor", label: "Cursor", key: "mcpServers",
    file: () => home(".cursor", "mcp.json"), detect: () => home(".cursor"),
    entry: stdio,
  }),
  jsonClient({
    id: "windsurf", label: "Windsurf", key: "mcpServers",
    file: () => home(".codeium", "windsurf", "mcp_config.json"), detect: () => home(".codeium", "windsurf"),
    entry: stdio,
  }),
  jsonClient({
    id: "gemini-cli", label: "Gemini CLI", key: "mcpServers",
    file: () => home(".gemini", "settings.json"), detect: () => home(".gemini"),
    entry: stdio,
  }),
  jsonClient({
    id: "lm-studio", label: "LM Studio", key: "mcpServers",
    file: () => home(".lmstudio", "mcp.json"), detect: () => home(".lmstudio"),
    entry: stdio,
  }),
  jsonClient({
    id: "cline", label: "Cline", key: "mcpServers",
    file: () => appData("Code", "User", "globalStorage", "saoudrizwan.claude-dev", "settings", "cline_mcp_settings.json"),
    detect: () => appData("Code", "User", "globalStorage", "saoudrizwan.claude-dev"),
    entry: (cmd) => ({ ...stdio(cmd), disabled: false }),
  }),
];

function find(ids) {
  const unknown = ids.filter((id) => !CLIENTS.some((c) => c.id === id));
  if (unknown.length) {
    throw new Error(`Unknown app: ${unknown.join(", ")}. Known: ${CLIENTS.map((c) => c.id).join(", ")}`);
  }
  return CLIENTS.filter((c) => ids.includes(c.id));
}

module.exports = { NAME, CLIENTS, find, withoutTable, tomlCommand, quote };
