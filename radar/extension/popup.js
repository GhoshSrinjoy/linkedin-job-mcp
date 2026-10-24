/* global extractJob, chrome */
const DEFAULT_API = "http://127.0.0.1:8000";
const GRADES = {
  low: ["Low", "✓", "circle"], moderate: ["Moderate", "!", "square"], elevated: ["Elevated", "!!", "diamond"],
  high: ["High", "✕", "triangle"], unknown: ["Not enough data", "?", "circle"], closed: ["No longer online", "–", "circle"],
};
const $ = (id) => document.getElementById(id);

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null) continue;
    if (k === "class") node.className = v; else if (k === "text") node.textContent = v; else node.setAttribute(k, v);
  }
  for (const c of children.flat()) if (c != null) node.append(c instanceof Node ? c : document.createTextNode(String(c)));
  return node;
}

function icon(grade) {
  const [, glyph, shape] = GRADES[grade] || GRADES.unknown;
  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("viewBox", "0 0 26 26"); svg.setAttribute("width", "30"); svg.setAttribute("height", "30");
  svg.setAttribute("class", `g-${["low", "moderate", "elevated", "high"].includes(grade) ? grade : "unknown"}`);
  let s;
  if (shape === "circle") { s = document.createElementNS(ns, "circle"); s.setAttribute("cx", 13); s.setAttribute("cy", 13); s.setAttribute("r", 10.5); }
  else if (shape === "square") { s = document.createElementNS(ns, "rect"); s.setAttribute("x", 3); s.setAttribute("y", 3); s.setAttribute("width", 20); s.setAttribute("height", 20); s.setAttribute("rx", 3.5); }
  else { s = document.createElementNS(ns, "polygon"); s.setAttribute("points", shape === "diamond" ? "13,1.5 24.5,13 13,24.5 1.5,13" : "13,1.8 24.6,23.4 1.4,23.4"); }
  s.setAttribute("class", "shape");
  const t = document.createElementNS(ns, "text");
  t.setAttribute("x", 13); t.setAttribute("y", shape === "triangle" ? 16.5 : 13.5);
  t.textContent = glyph;
  svg.append(s, t);
  return svg;
}

async function settings() {
  const stored = await chrome.storage.local.get(["api", "news"]);
  return { api: (stored.api || DEFAULT_API).replace(/\/$/, ""), news: stored.news !== false };
}

function render(res, api) {
  const out = $("result");
  out.replaceChildren();
  for (const n of res.notes || []) out.append(el("p", { class: "muted", text: n }));
  if (!res.result) return;
  const { score: s, posting: p, features: f } = res.result;
  const [label] = GRADES[s.grade] || GRADES.unknown;
  out.append(el("div", { class: "grade" }, icon(s.grade),
    el("div", {}, el("div", { class: "label", text: s.grade === "closed" ? label : `${label} ghost-risk` }),
      el("div", { class: "meta", text: `Score ${s.risk}/100 · confidence ${s.confidence}` }))));
  out.append(el("div", { class: "muted", text: [p.title, p.company].filter(Boolean).join(" · ") }));
  out.append(el("div", { class: "box" }, el("strong", { text: s.advice })));
  if (s.scam && s.scam.flag) out.append(el("div", { class: "box" }, el("strong", { text: `Scam markers: ${s.scam.reasons.join("; ")}` })));
  const facts = s.reasons.filter((r) => r.points !== 0).slice(0, 4);
  if (facts.length) {
    out.append(el("ul", {}, facts.map((r) => el("li", {},
      el("span", { class: "pts", text: `${r.points > 0 ? "+" : "−"}${Math.abs(r.points)} ` }), `${r.label}: ${r.fact}`))));
  }
  if (s.competition && s.competition.level !== "unknown") out.append(el("div", { class: "box", text: s.competition.text }));
  if (f.live_days != null) out.append(el("p", { class: "muted", text: `Online for about ${f.live_days} days; typical for this occupation: ${f.baseline.expected_days} days.` }));
  if (res.result.posting_id) {
    out.append(el("a", { href: `${api}/#posting=${res.result.posting_id}`, target: "_blank", text: "Open the full analysis ↗" }));
  }
}

$("check").addEventListener("click", async () => {
  const button = $("check");
  button.disabled = true;
  $("status").textContent = "Reading this page…";
  try {
    const { api, news } = await settings();
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const [{ result: page }] = await chrome.scripting.executeScript({ target: { tabId: tab.id }, func: extractJob });
    if (!page || !page.title) throw new Error("No job found on this page.");
    $("status").textContent = "Checking with your Ghost Job Radar…";
    const resp = await fetch(`${api}/api/capture`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...page, with_news: news }),
    });
    if (!resp.ok) throw new Error(`Radar answered ${resp.status}. Is it running at ${api}?`);
    render(await resp.json(), api);
    $("status").textContent = "";
  } catch (err) {
    $("status").textContent = err.message.includes("Failed to fetch")
      ? "Could not reach your Ghost Job Radar. Start it (run.ps1) or fix the address in Settings."
      : err.message;
  } finally {
    button.disabled = false;
  }
});

$("settings-toggle").addEventListener("click", async () => {
  const box = $("settings");
  box.hidden = !box.hidden;
  $("settings-toggle").setAttribute("aria-expanded", String(!box.hidden));
  const { api, news } = await settings();
  $("api").value = api;
  $("news").checked = news;
});

$("save").addEventListener("click", async () => {
  await chrome.storage.local.set({ api: $("api").value.trim() || DEFAULT_API, news: $("news").checked });
  $("settings").hidden = true;
  $("status").textContent = "Saved.";
});
