// Ghost Job Radar dashboard: views, forms and the map. Charts and floating windows live in viz.js.
import { $, $$, api, el, fmtDate, fmtDays, median, safeUrl, sourceLabel, svgEl } from "./dom.js";
import {
  GRADE_ORDER, GRADES, TYPE_LABELS, ageBullet, ageMini, ageStrip, barList, copyChips, coverageStrip, effortScale,
  employerBars, flagList, gradeBadge, gradeDistribution, gradeIcon, gradeScale, hideFloating, hoverable, miniBullet,
  miniCells, miniGradeBar, postingCard, progressPanel, publicationMonths, radarScope, ratioBullet, scoreMeter,
  showFloating, survivalChart, calibrationChart, timeline, timelineList, tip, typeBars, weightBars,
} from "./viz.js";

const TIERS = {
  full: "Worth a tailored application",
  standard: "Standard application",
  light: "Short, fast application",
  verify: "Verify before applying",
  skip: "Skip",
};
const DIRECTION = { raises: "▲", lowers: "▼", routes: "◆", info: "•" };
const NEWS_TEXT = {
  ok: "Done (GDELT)",
  not_checked: "Not checked",
  pending: "Still loading in the background",
  rate_limited: "Skipped: GDELT is rate-limiting, try later",
  timeout: "Timed out, try later",
};
const newsText = (status) => NEWS_TEXT[status] || `Failed (${String(status).replace(/^error: ?/, "")})`;
const ORIGIN_TEXT = {
  present: "Also listed on the employer's own channel",
  removed: "Removed from the employer's own channel",
  not_found: "Not found on the employer's own channel",
  is_origin: "This is the employer's own listing",
  unknown: "Not checked",
};
const VIEWS = ["overview", "check", "company", "city", "watch", "model", "about"];
const CONNECTORS = [
  ["linkedin", "LinkedIn"], ["bundesagentur", "Bundesagentur"], ["jsearch", "Google for Jobs"],
  ["adzuna", "Adzuna"], ["arbeitnow", "Arbeitnow"], ["employer_feeds", "Employer feeds"],
];
let META = { connectors: {} };
let OVERVIEW = null;
let overviewRequest = null;
let renderedOverviewAt = null;

const num = (n) => (n ?? 0).toLocaleString("en-GB");
const pct = (part, whole) => (whole ? `${Math.round((100 * part) / whole)}%` : "");
const pts = (v) => (Number.isInteger(v) ? String(Math.abs(v)) : Math.abs(v).toFixed(1));

// ------------------------------------------------------------------ theme, busy state, views

const THEMES = ["auto", "light", "dark"];
function applyTheme(mode) {
  if (mode === "auto") delete document.documentElement.dataset.theme;
  else document.documentElement.dataset.theme = mode;
  for (const b of $$("[data-theme-choice]")) b.setAttribute("aria-pressed", String(b.dataset.themeChoice === mode));
  try { localStorage.setItem("gjr-theme", mode); } catch (_) { /* storage unavailable */ }
}
for (const b of $$("[data-theme-choice]")) b.addEventListener("click", () => applyTheme(b.dataset.themeChoice));
let savedTheme = "auto";
try { savedTheme = localStorage.getItem("gjr-theme") || "auto"; } catch (_) { /* storage unavailable */ }
applyTheme(THEMES.includes(savedTheme) ? savedTheme : "auto");

let busyCount = 0;
function busy(delta) {
  busyCount = Math.max(0, busyCount + delta);
  document.body.classList.toggle("busy", busyCount > 0);
}

function showTab(name, { hash = true } = {}) {
  if (!VIEWS.includes(name)) name = "overview";
  hideFloating();
  for (const btn of $$(".nav-item")) {
    if (btn.dataset.tab === name) btn.setAttribute("aria-current", "page");
    else btn.removeAttribute("aria-current");
  }
  for (const view of $$("main > .view")) view.hidden = view.id !== `tab-${name}`;
  if (hash) history.replaceState(null, "", `#${name}`);
  if (name === "overview") loadOverview();
  if (name === "check") renderCheckIntro();
  if (name === "company") renderCompanyIntro();
  if (name === "city") { ensureMap(); renderCityIntro(); }
  if (name === "watch") loadWatchlist();
  if (name === "model") loadModel();
  window.scrollTo({ top: 0 });
}
for (const btn of $$(".nav-item")) btn.addEventListener("click", () => showTab(btn.dataset.tab));
document.addEventListener("click", (e) => {
  const target = e.target.closest("[data-goto]");
  if (!target) return;
  e.preventDefault();
  showTab(target.dataset.goto);
});

/** Start a background task and show its live progress right under the view's form until the result arrives. */
async function runTask(path, options, out) {
  const view = out.closest(".view");
  const form = view?.querySelector(":scope > form");
  const holder = el("div", { class: "progress-holder" }, progressPanel({ title: "Starting…", fraction: 0, steps: [] }));
  if (form) form.after(holder);
  else out.before(holder);
  out.classList.add("loading");
  busy(1);
  try {
    const { task_id } = await api(path, { method: "POST", ...options });
    for (;;) {
      const data = await api(`/api/tasks/${task_id}`);
      holder.replaceChildren(progressPanel(data.progress));
      if (data.state === "done") return data.result;
      if (data.state === "failed") throw new Error(data.error || "The task failed");
      await new Promise((r) => setTimeout(r, 350));
    }
  } finally {
    holder.remove();
    out.classList.remove("loading");
    busy(-1);
  }
}

function setBusy(container, statusEl, text) {
  container.classList.toggle("loading", Boolean(text));
  statusEl.textContent = text || "";
}

function flash(text) {
  const status = $("main > .view:not([hidden]) .status-line");
  if (status) { status.textContent = text; setTimeout(() => { if (status.textContent === text) status.textContent = ""; }, 5000); }
}

// ------------------------------------------------------------------ building blocks

function panelHead(title, sub, extra) {
  return el("div", { class: "panel-head" },
    el("div", {}, el("h3", { class: "panel-title", text: title }), sub ? el("p", { class: "panel-sub", text: sub }) : null),
    extra || null);
}

function panel(title, sub, ...children) {
  return el("div", { class: "panel" }, title ? panelHead(title, sub) : null, ...children);
}

function section(title, sub, ...children) {
  return el("section", { class: "sec" },
    el("div", { class: "sec-head" }, el("h2", { class: "sec-title", text: title }), sub ? el("p", { class: "sec-sub", text: sub }) : null),
    ...children);
}

/** Lays out one, two or three panels side by side. */
function row(items, cls) {
  const list = items.filter(Boolean);
  if (list.length === 1) return list[0];
  return el("div", { class: `grid ${cls || (list.length === 3 ? "g-3" : "g-2")}` }, list);
}

function kpiBand(...tiles) {
  return el("div", { class: "kpi-band" }, tiles);
}

function kpi(label, value, { unit, note, help, viz } = {}) {
  const tile = el("div", { class: "kpi", tabindex: help ? 0 : null },
    el("div", { class: "kpi-label", text: label }),
    el("div", { class: "kpi-value" }, String(value), unit ? el("span", { class: "kpi-unit", text: unit }) : null),
    el("div", { class: "kpi-viz" }, viz || null),
    note ? el("div", { class: "kpi-note", text: note }) : null);
  if (help) hoverable(tile, () => tip(`${value}${unit ? ` ${unit}` : ""}`, label, help));
  return tile;
}

const shareBar = (part, whole) => el("div", { class: "mini-bullet", role: "img", "aria-label": `${part} of ${whole}` },
  el("span", { class: "fill", style: `width:${whole ? Math.max(2, (100 * part) / whole) : 0}%` }));

function gradeCounts(items) {
  const counts = {};
  for (const s of items) counts[s.score.grade] = (counts[s.score.grade] || 0) + 1;
  return counts;
}

function notesBlock(notes) {
  if (!notes || !notes.length) return null;
  return el("div", { class: "notes" }, notes.map((n) => el("div", { class: "note", text: n })));
}

const topReason = (score) => (score.reasons.find((x) => x.points > 0) || {}).label || "No raising signals";

function reasonsList(reasons) {
  const max = Math.max(10, ...reasons.map((r) => Math.abs(r.points || 0)));
  return el("ul", { class: "reasons" }, reasons.map((r) => {
    const p = r.points || 0;
    return el("li", { class: `reason${r.direction === "info" ? " info" : ""}` },
      el("span", { class: "reason-dir", title: r.direction, text: DIRECTION[r.direction] || "•" }),
      el("span", { class: "reason-text" },
        el("span", { class: "reason-label", text: r.label }),
        el("span", { class: "reason-fact", text: r.fact })),
      el("span", { class: "contrib", "aria-hidden": "true" },
        p ? el("span", { class: `contrib-bar ${p > 0 ? "pos" : "neg"}`, style: `width:${(Math.abs(p) / max) * 50}%` }) : null),
      el("span", { class: "reason-pts", text: p ? `${p > 0 ? "+" : "−"}${pts(p)}` : "" }));
  }));
}

const contribLegend = () => el("div", { class: "contrib-legend" },
  el("span", {}, el("i", { class: "pos" }), "raises the ghost-risk"), el("span", {}, el("i", { class: "neg" }), "lowers it"));

function kvList(pairs) {
  const dl = el("dl", { class: "kv" });
  for (const [k, v] of pairs) {
    if (v === null || v === undefined || v === "") continue;
    dl.append(el("dt", { text: k }), el("dd", {}, v instanceof Node ? v : String(v)));
  }
  return dl;
}

function eventsList(events) {
  return el("ul", { class: "events" }, events.map((e) => {
    const url = safeUrl(e.url);
    return el("li", {},
      el("span", {}, el("span", { class: "chip", text: e.kind }), " ", url
        ? el("a", { href: url, target: "_blank", rel: "noopener noreferrer", text: e.title })
        : e.title),
      el("span", { class: "small muted", text: [fmtDate(e.published_at), e.source].filter(Boolean).join(" · ") }));
  }));
}

/** Company news that fills itself in: spinner while GDELT works, then headlines; `onChanged` re-scores. */
function newsBlock(companyId, status, events, onChanged) {
  const box = el("div", { class: "news-block" });
  const render = (st, evs) => {
    if (st === "pending") {
      box.replaceChildren(el("div", { class: "news-loading" }, el("span", { class: "spinner", "aria-hidden": "true" }),
        el("span", { text: "Searching company news (layoffs, insolvency, funding)…" }),
        el("span", { class: "muted", text: "" })));
    } else if (evs && evs.length) {
      box.replaceChildren(eventsList(evs.slice(0, 8)));
    } else {
      box.replaceChildren(el("p", { class: "secondary", text: st === "ok" ? "No layoff, insolvency or funding headlines found." : `News: ${newsText(st).toLowerCase()}.` }));
    }
  };
  render(status, events);
  if (status === "pending" && companyId) {
    const started = Date.now();
    const tick = setInterval(() => {
      const secs = Math.round((Date.now() - started) / 1000);
      if (!box.isConnected || secs > 90) { clearInterval(tick); return; }
      const label = box.querySelector(".news-loading .muted");
      if (label) label.textContent = `${secs} s`;
    }, 1000);
    const poll = setInterval(async () => {
      if (!box.isConnected || Date.now() - started > 90000) { clearInterval(poll); return; }
      try {
        const data = await api(`/api/company/${companyId}/news`);
        if (data.status === "pending") return;
        clearInterval(poll);
        clearInterval(tick);
        render(data.status, data.events);
        if (data.affects_score && onChanged) onChanged();
      } catch (_) { clearInterval(poll); clearInterval(tick); }
    }, 2500);
  }
  return box;
}

// ------------------------------------------------------------------ overview

function overviewData() {
  if (!overviewRequest) {
    overviewRequest = api("/api/overview")
      .then((data) => { OVERVIEW = data; updateStation(); return data; })
      .finally(() => { overviewRequest = null; });
  }
  return overviewRequest;
}

function withOverview(callback) {
  if (OVERVIEW) callback(OVERVIEW);
  else overviewData().then(callback).catch(() => { /* intros are optional */ });
}

async function loadOverview() {
  const out = $("#overview-result");
  if (!out.children.length) {
    out.replaceChildren(el("div", { class: "kpi-band skeleton", style: "height:124px" }),
      el("div", { class: "grid g-7-5" }, el("div", { class: "skeleton", style: "height:560px" }), el("div", { class: "skeleton", style: "height:560px" })));
  }
  busy(1);
  try {
    const data = await overviewData();
    if (data.generated_at !== renderedOverviewAt || !out.querySelector(".scope-wrap, .empty")) renderOverview(data);
  } catch (err) {
    out.replaceChildren(el("div", { class: "panel" }, el("p", { text: `Could not load the overview: ${err.message}` })));
  } finally { busy(-1); }
}

function renderOverview(data) {
  const out = $("#overview-result");
  const t = data.totals;
  renderedOverviewAt = data.generated_at;
  $("#overview-lead").textContent = t.jobs
    ? `${num(t.jobs)} jobs from ${num(t.employers)} employers in ${num(t.cities)} cities.`
    : "Nothing stored yet. Check a posting, a company or a city to start.";
  if (!t.jobs) { out.replaceChildren(emptyOverview()); return; }
  const jobs = data.jobs;
  const grades = data.grades || {};
  const flagged = (grades.elevated || 0) + (grades.high || 0);
  const links = makeLinks();
  const open = (sp) => openPosting(sp.posting_id);
  const hover = (sp, on) => links.highlight(sp.posting_id, on);
  const raised = jobs.filter((sp) => sp.score.grade === "high" || sp.score.grade === "elevated");
  const closer = (raised.length >= 3 ? raised : jobs).slice(0, 7);
  const beyond = jobs.filter((sp) => (sp.features.excess_ratio ?? 0) >= 2).length;
  const groupRows = Object.entries(data.groups || {}).sort((a, b) => b[1] - a[1])
    .map(([k, v]) => ({ key: k, label: k, value: v }));
  const typeRows = Object.entries(data.types || {}).sort((a, b) => b[1] - a[1])
    .map(([k, v]) => ({ key: k, label: TYPE_LABELS[k] || k, value: v }));
  out.replaceChildren(
    kpiBand(
      kpi("Jobs monitored", num(t.jobs), { note: `${num(t.postings)} postings including copies`, viz: shareBar(t.jobs, t.postings),
        help: "One entry per job: copies of the same job on several platforms are merged. The bar shows jobs as a share of all stored postings." }),
      kpi("Elevated or high", num(flagged), { unit: pct(flagged, t.jobs), note: "of all jobs", viz: miniGradeBar(grades),
        help: "Jobs whose observable facts add up to an elevated or high ghost-risk indicator. The bar shows all four grades." }),
      kpi("Median age vs norm", data.median_ratio != null ? `${data.median_ratio.toFixed(1)}×` : "—", {
        note: data.median_days != null ? `median ${data.median_days} days online` : null,
        viz: data.median_ratio != null ? miniBullet(data.median_ratio) : null,
        help: "Time online divided by the Bundesagentur's typical advertising time for the occupation. The black tick marks 1×, as long as typical." }),
      kpi("Employers", num(t.employers), { note: `${num(t.own_feeds)} with their own job feed found`, viz: shareBar(t.own_feeds, t.employers),
        help: "When an employer's own job feed (Personio, Greenhouse, …) is known, the radar can see jobs disappear there while copies stay online." }),
      kpi("Evidence per job", data.evidence_avg != null ? data.evidence_avg.toFixed(1) : "—", { unit: `of ${data.evidence_total}`,
        note: "kinds of evidence on average", viz: data.evidence_avg != null ? miniCells(data.evidence_avg, data.evidence_total) : null,
        help: "Age vs norm, reposts and copies, employer's own site, news, applicants, wording, track record. More kinds of evidence make a grade firmer." })),
    el("div", { class: "grid g-7-5" },
      el("div", { class: "panel scope-panel" },
        panelHead("The radar", "Each mark is a job. Further out means online longer than usual for its occupation.",
          el("span", { class: "panel-stat", text: `${num(beyond)} at 2× or more` })),
        radarScope(jobs, { onSelect: open, onHover: hover })),
      el("div", { class: "stack" },
        panel("Ghost-risk grades", `${num(t.jobs)} jobs`, gradeDistribution([], { counts: grades })),
        panel("Needs a closer look", raised.length >= 3 ? "Highest ghost-risk first." : "Highest scores so far.",
          flagList(closer, { onSelect: open, onHover: hover })))),
    section("Who advertises, and where", "Split by grade. Click a name to analyse it.",
      el("div", { class: "grid g-5-4-3" },
        panel("Employers with the most jobs", null, employerBars(data.top_employers || [], { onSelect: (name) => openCompany(name) })),
        panel("Cities", null, employerBars((data.top_cities || []).filter((c) => c.company !== "Unknown"), { onSelect: (name) => openCity(name), actionLabel: "Map" })),
        panel("Where the jobs were found", "Each job counted once, at its original source.", barList(groupRows, { unit: "jobs" })))),
    section("Age and pattern", "When jobs were first published, and which patterns the flagged ones fit.",
      el("div", { class: "grid g-7-5" },
        panel("First published", "By month of first publication. Grey: over a year ago.",
          publicationMonths(data.months || {}, { now: new Date(data.generated_at) })),
        panel("Patterns among the jobs", "The strongest pattern per flagged job.",
          typeRows.length ? barList(typeRows, { unit: "jobs", stacked: true }) : el("p", { class: "secondary", text: "No job shows a clear ghost pattern yet." })))),
  );
  if (t.limited) out.append(el("p", { class: "small muted", text: `Showing the ${num(t.postings)} most recently seen postings.` }));
}

function actionCard(title, text, view) {
  return el("button", { class: "action-card", type: "button", "data-goto": view }, el("h3", { text: title }), el("p", { text }));
}

function emptyOverview() {
  return el("div", { class: "panel empty" },
    el("h2", { text: "Start monitoring" }),
    el("p", { text: "Every job you check, analyse or map is stored here and re-checked over time." }),
    el("div", { class: "action-cards" },
      actionCard("Check a posting", "Paste a job link or the ad text and get a ghost-risk grade with the facts behind it.", "check"),
      actionCard("Analyse a company", "Load every posting from an employer's own job feed and its copies on job platforms.", "company"),
      actionCard("Map a city", "See every posting around a city on a map, each marked with its grade.", "city")));
}

// ------------------------------------------------------------------ station rail

function updateStation() {
  const c = META.connectors || {};
  $("#station-sources").replaceChildren(...CONNECTORS.filter(([k]) => k in c).map(([k, label]) => hoverable(
    el("li", { tabindex: 0 }, el("span", { class: `led ${c[k] ? "on" : "off"}`, "aria-hidden": "true" }),
      el("span", { class: "src", text: label }), el("span", { class: "state", text: c[k] ? "on" : "off" })),
    () => tip(c[k] ? "Connected" : "Not connected", label))));
  const t = OVERVIEW?.totals;
  const facts = [];
  if (t) facts.push(["Jobs", num(t.jobs)], ["Employers", num(t.employers)], ["Checks", num(t.checks)]);
  $("#station-facts").replaceChildren(...facts.flatMap(([k, v]) => [el("dt", { text: k }), el("dd", { text: v })]));
}

function updateWatchCount(n) {
  const badge = $("#watch-count");
  badge.textContent = n ? String(n) : "";
  badge.hidden = !n;
}

// ------------------------------------------------------------------ one posting in full

function renderScored(sp, { compact = false } = {}) {
  const { posting: p, features: f, score: s } = sp;
  const b = f.baseline || {};
  const rep = f.repost || {};
  const origin = f.origin || {};
  const url = safeUrl(p.url);
  const g = GRADES[s.grade] || GRADES.unknown;
  const closed = s.grade === "closed";
  const root = el("div", { class: `result${compact ? " compact" : ""}` });

  root.append(el("div", { class: `panel verdict ${g.cls}` },
    el("div", { class: "verdict-plate" }, gradeIcon(s.grade, compact ? 38 : 52)),
    el("div", { class: "verdict-main" },
      el("p", { class: "eyebrow", text: closed ? "Status" : "Ghost-risk" }),
      el("div", { class: "verdict-grade", text: s.grade_label }),
      closed ? null : scoreMeter(s.risk, s.grade),
      closed ? null : el("p", { class: "verdict-meta", text: `Confidence: ${s.confidence}` }),
      !closed && sp.estimate ? estimateLine(sp.estimate) : null),
    !closed && p.company && !compact
      ? el("div", { class: "verdict-actions" },
          el("button", { class: "btn btn-quiet", type: "button", onclick: () => openCompany(p.company) }, "Analyse employer"),
          el("button", { class: "btn btn-ghost", type: "button", onclick: () => addWatch("company", p.company) }, "Track employer"))
      : el("div"),
    el("div", { class: "verdict-posting" },
      el(compact ? "h3" : "h2", { class: "posting-title", text: p.title || "Untitled posting" }),
      el("div", { class: "posting-meta" },
        p.company ? el("span", { text: p.company }) : null,
        p.city || p.location ? el("span", { text: p.city || p.location }) : null,
        b.kldb ? el("span", { class: "tag mono", title: `Occupation (KldB 2010): ${b.kldb_label || ""}`, text: `KldB ${b.kldb}` }) : null,
        url ? el("a", { href: url, target: "_blank", rel: "noopener noreferrer", text: "Open posting ↗" }) : null),
      sp.copies && sp.copies.length ? el("div", { class: "posting-meta" }, el("span", { class: "muted", text: "Seen on" }), copyChips(sp.copies)) : null,
      !compact && sp.posting_id ? employerNoteForm(sp) : null)));

  if (s.scam.flag) {
    root.append(el("div", { class: "alert", role: "alert" }, gradeIcon("high", 22),
      el("div", {}, el("strong", { text: "Scam markers found. " }), s.scam.reasons.join("; "))));
  }
  const advice = el("div", { class: "panel advice" },
    el("p", { class: "eyebrow", text: "Suggested effort" }),
    el("div", { class: "advice-tier", text: TIERS[s.effort_tier] || s.effort_tier }),
    el("p", { class: "advice-text", text: s.advice }),
    effortScale(s.effort_tier));
  if (closed) {
    root.append(row([advice, s.coverage?.length ? el("div", { class: "panel" }, coverageStrip(s.coverage)) : null]));
  } else {
    root.append(section("Three verdicts", "Is the job open, can you get it, and does the employer answer?",
      row([chanceCard(s.competition), communicationCard(s.communication), advice], "g-3")));
    root.append(row([
      s.coverage?.length ? el("div", { class: "panel" }, coverageStrip(s.coverage), confidenceLine(s.confidence)) : null,
      sp.posting_id ? evidencePanel(sp) : null,
    ], "g-5-7"));
  }
  if (closed) {
    root.append(panel("Observable facts", null, reasonsList(s.reasons)));
    return root;
  }

  root.append(section("Why this grade", "What adds or removes points.",
    row([
      panel("Score build-up", `${s.risk} of 100 points`, reasonsList(s.reasons), contribLegend()),
      panel("What kind of ghost-risk", "Strength of each pattern, from 0 to 1.", typeBars(s.types)),
    ], "g-7-5")));

  const holder = el("div", {}, el("p", { class: "secondary small", text: sp.posting_id ? "Loading the lifecycle…" : "Not stored, so no lifecycle yet." }));
  if (sp.posting_id) {
    api(`/api/postings/${sp.posting_id}/timeline`).then((data) => {
      holder.replaceChildren(timeline(data),
        el("details", { class: "twin" }, el("summary", { text: "Show as list" }), timelineList(data)));
    }).catch(() => holder.replaceChildren(el("p", { class: "secondary small", text: "Lifecycle not available." })));
  }
  root.append(section("Lifecycle", "Time online and every place the job was seen.",
    row([
      panel("Time online against the norm", b.expected_days ? `Typical for ${b.kldb_label || "this occupation"}: about ${b.expected_days} days` : null,
        ageBullet(f),
        kvList([
          ["First published", f.first_published ? fmtDate(f.first_published) + (f.first_published_is_lower_bound ? " or earlier" : "") : "Unknown"],
          ["Copies seen", rep.instances > 1 ? `${rep.instances} (${rep.cosmetic} cosmetic repost${rep.cosmetic === 1 ? "" : "s"})` : rep.instances],
          ["Employer's own channel", ORIGIN_TEXT[origin.status] + (origin.feed ? ` (${sourceLabel(origin.feed)})` : "")],
          ["Tracked by the radar for", fmtDays(rep.history_days)],
        ])),
      panel("Every place this job was seen", "Each copy over time. Shaded: the usual advertising time.", holder),
    ], "g-5-7")));

  root.append(section("Context", "The occupation, the employer and the news.", row([
    panel("Occupation", null, kvList([
      ["Job group", b.kldb ? b.kldb_label || b.kldb : "Not recognised"],
      ["Requirement level", b.level],
      ["Usual vacancy duration", b.vakanzzeit_days ? fmtDays(b.vakanzzeit_days) : null],
      ["Region", b.region],
      ["Shortage occupation", b.shortage],
    ])),
    f.company ? companyContextPanel(f.company, sp.posting_id && !compact ? () => refreshPosting(sp.posting_id) : null) : null,

  ])));

  root.append(section("Before you apply", null,
    row([
      panel("Verify before you invest time", null, el("ul", { class: "plain" }, s.verify_tips.map((t) => el("li", { text: t })))),
      panel("Caveats", null, el("ul", { class: "plain small" }, s.caveats.map((c) => el("li", { class: "secondary", text: c })))),
    ]),
    sp.posting_id && !compact ? reportForm(sp) : null));
  return root;
}

function companyContextPanel(c, onChanged) {
  return panel("Employer context", null, kvList([
    ["Employer type", c.employer_type || "Not determined"],
    ["Open postings tracked", c.active_postings],
    ["Team builds (3+ new roles)", c.coherent_departments && c.coherent_departments.length ? c.coherent_departments.join(", ") : "None seen"],
    ["Posting trend", c.posting_trend],
  ]), el("h4", { class: "subhead", text: "Company news" }),
  newsBlock(c.company_id, c.news_status, (c.events || []).filter((e) => e.source !== "TED" && e.source !== "your note").slice(0, 5), onChanged));
}

async function refreshPosting(id, message = "Company news arrived: the score below includes it.") {
  try {
    const sp = await api(`/api/postings/${id}`);
    $("#check-result").replaceChildren(el("div", { class: "note", text: message }), renderScored(sp));
  } catch (_) { /* keep the current view */ }
}

function reportForm(sp) {
  const form = el("form", { class: "panel form-panel" },
    panelHead("Report your outcome", "Saved on this computer. It improves this employer's record."),
    el("div", { class: "form-grid" },
      el("label", { class: "field" }, el("span", { class: "field-label", text: "Applied on" }), el("input", { type: "date", name: "applied_on" })),
      el("label", { class: "field" }, el("span", { class: "field-label", text: "Response" }), el("select", { name: "response" },
        el("option", { value: "none", text: "No reply" }), el("option", { value: "auto_reject", text: "Automatic rejection" }),
        el("option", { value: "reject", text: "Rejection" }), el("option", { value: "internal", text: "Internal candidate chosen" }),
        el("option", { value: "interview", text: "Interview invitation" }), el("option", { value: "offer", text: "Offer" }))),
      el("label", { class: "field" }, el("span", { class: "field-label", text: "Days until response" }), el("input", { type: "number", name: "days_to_response", min: 0 })),
      ...applicationFields()),
    el("div", { class: "form-actions" }, el("span", { class: "small secondary", role: "status" }),
      el("button", { class: "btn btn-quiet", type: "submit", text: "Save report" })));
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = new FormData(form);
    const status = form.querySelector('[role="status"]');
    try {
      await api("/api/reports", { method: "POST", body: JSON.stringify({
        posting_id: sp.posting_id, posting_url: sp.posting.url, company: sp.posting.company,
        applied_on: data.get("applied_on") || null, response: data.get("response") || null,
        days_to_response: data.get("days_to_response") ? Number(data.get("days_to_response")) : null,
        ...applicationValues(data),
      }) });
      status.textContent = "Saved.";
    } catch (err) { status.textContent = `Could not save: ${err.message}`; }
  });
  return form;
}

// ------------------------------------------------------------------ postings table (the table twin of every chart)

function postingsTable(items, { showCompany = true, filter, links } = {}) {
  const tbody = el("tbody");
  const visible = items.filter((sp) => !filter || filter.has(sp.score.grade));
  for (const sp of visible) {
    const p = sp.posting;
    const url = safeUrl(p.url);
    const tr = el("tr", { class: "posting-row", tabindex: 0, "aria-expanded": "false", "data-pid": sp.posting_id },
      el("td", {}, gradeBadge(sp.score.grade)),
      el("td", { class: "title-cell" }, url
        ? el("a", { href: url, target: "_blank", rel: "noopener noreferrer", text: p.title || "Untitled", onclick: (e) => e.stopPropagation() })
        : (p.title || "Untitled"),
        showCompany && p.company ? el("div", { class: "sub", text: p.company }) : null),
      el("td", { class: "hide-sm", text: p.city || p.location || "—" }),
      el("td", { class: "num" }, ageMini(sp.features)),
      el("td", { class: "num hide-sm" }, applicantsCell(sp.score.competition)),
      el("td", { class: "hide-sm" }, copyChips(sp.copies)),
      el("td", { class: "hide-sm signal-cell", text: topReason(sp.score) }));
    const toggle = () => {
      hideFloating();
      const open = tr.nextElementSibling && tr.nextElementSibling.classList.contains("detail-row");
      if (open) { tr.nextElementSibling.remove(); tr.setAttribute("aria-expanded", "false"); return; }
      tr.after(el("tr", { class: "detail-row" }, el("td", { colspan: 7 }, renderScored(sp, { compact: true }))));
      tr.setAttribute("aria-expanded", "true");
    };
    tr.addEventListener("click", toggle);
    tr.addEventListener("keydown", (e) => { if (e.target === tr && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); toggle(); } });
    // floating preview on the grade, title, age and signal cells (the copy chips have their own windows)
    for (const cell of [tr.cells[0], tr.cells[1], tr.cells[3], tr.cells[6]]) hoverable(cell, () => postingCard(sp), { delay: 220 });
    tr.addEventListener("pointerenter", () => links?.highlight(sp.posting_id, true));
    tr.addEventListener("pointerleave", () => links?.highlight(sp.posting_id, false));
    links?.rows.set(sp.posting_id, tr);
    tbody.append(tr);
  }
  const table = el("table", {},
    el("thead", {}, el("tr", {},
      el("th", { text: "Ghost-risk" }), el("th", { text: showCompany ? "Posting / employer" : "Posting" }),
      el("th", { class: "hide-sm", text: "Location" }), el("th", { class: "num", text: "Days online" }),
      el("th", { class: "num hide-sm", text: "Applicants" }),
      el("th", { class: "hide-sm", text: "Seen on" }), el("th", { class: "hide-sm", text: "Strongest signal" }))),
    tbody);
  return el("div", { class: "table-wrap" }, visible.length ? table : el("p", { class: "table-empty", text: "No postings to show." }));
}

/** Linked highlighting between table rows, map markers, chart dots, radar blips and list entries. */
function makeLinks() {
  const links = { rows: new Map(), markers: new Map() };
  links.highlight = (pid, on) => {
    const tr = links.rows.get(pid);
    if (tr) tr.classList.toggle("row-active", on);
    const marker = links.markers.get(pid);
    if (marker && marker.getElement()) {
      marker.getElement().classList.toggle("mk-active", on);
      marker.setZIndexOffset(on ? 1000 : 0);
    }
    for (const node of $$(`.dot[data-pid="${pid}"]`)) node.classList.toggle("dot-active", on);
    for (const node of $$(`.flag-item[data-pid="${pid}"]`)) node.classList.toggle("row-active", on);
  };
  links.select = (sp) => {
    const tr = links.rows.get(sp.posting_id);
    if (!tr) { openPosting(sp.posting_id); return; }
    tr.scrollIntoView({ behavior: "smooth", block: "center" });
    if (tr.getAttribute("aria-expanded") !== "true") tr.click();
  };
  return links;
}

// ------------------------------------------------------------------ check view

for (const btn of $$("#check-form .seg-btn")) {
  btn.addEventListener("click", () => {
    const mode = btn.dataset.mode;
    for (const b of $$("#check-form .seg-btn")) b.setAttribute("aria-pressed", String(b.dataset.mode === mode));
    for (const pane of $$("#check-form [data-pane]")) pane.hidden = pane.dataset.pane !== mode;
    $(`#check-form [data-pane="${mode}"] input, #check-form [data-pane="${mode}"] textarea`)?.focus();
  });
}

function renderCheckIntro() {
  const out = $("#check-result");
  if (out.children.length) return;
  withOverview((data) => {
    if (out.children.length || !data.jobs?.length) return;
    out.replaceChildren(section("Or open a job the radar already knows", "Highest ghost-risk among the stored jobs.",
      el("div", { class: "panel" }, flagList(data.jobs.slice(0, 6), { onSelect: (sp) => openPosting(sp.posting_id) }))));
  });
}

$("#check-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.currentTarget;
  const data = new FormData(form);
  const observations = {};
  if (data.get("applicant_count")) observations.applicant_count = Number(data.get("applicant_count"));
  if (data.get("posted_date_shown")) observations.posted_date_shown = data.get("posted_date_shown");
  if (data.get("responsiveness")) observations.responsiveness = data.get("responsiveness");
  if (data.get("reposted_label")) observations.reposted_label = true;
  if (data.get("applied_on")) observations.applied_on = data.get("applied_on");
  if (data.get("response")) observations.response = data.get("response");
  const body = {
    url: data.get("url") || null, text: data.get("text") || null, title: data.get("title") || null,
    company: data.get("company") || null, location: data.get("location") || null,
    observations: Object.keys(observations).length ? observations : null, with_news: Boolean(data.get("with_news")),
  };
  if (!body.url && !body.text) { $("#check-status").textContent = "Enter a job link or paste the ad text."; return; }
  const out = $("#check-result");
  const button = form.querySelector("button[type=submit]");
  button.disabled = true;
  $("#check-status").textContent = "";
  try {
    const res = await runTask("/api/tasks/check", { body: JSON.stringify(body) }, out);
    const parts = [notesBlock(res.notes)];
    if (res.result) parts.push(renderScored(res.result));
    out.replaceChildren(...parts.filter(Boolean));
    if (res.result?.posting_id) history.replaceState(null, "", `#posting=${res.result.posting_id}`);
    OVERVIEW = null;
  } catch (err) {
    $("#check-status").textContent = `Check failed: ${err.message}`;
  } finally { button.disabled = false; }
});

async function openPosting(id) {
  showTab("check", { hash: false });
  history.replaceState(null, "", `#posting=${id}`);
  const out = $("#check-result");
  setBusy(out, $("#check-status"), "Loading the analysis…");
  try {
    out.replaceChildren(renderScored(await api(`/api/postings/${encodeURIComponent(id)}`)));
    setBusy(out, $("#check-status"), "");
  } catch (err) {
    setBusy(out, $("#check-status"), `Could not load posting ${id}: ${err.message}`);
    out.classList.remove("loading");
  }
}

// ------------------------------------------------------------------ company view

function renderCompanyIntro() {
  const out = $("#company-result");
  if (out.children.length) return;
  withOverview((data) => {
    const names = (data.top_employers || []).filter((e) => !e.agency && e.company !== "Unknown employer").slice(0, 10);
    if (out.children.length || !names.length) return;
    out.replaceChildren(section("Employers the radar knows", "Click one to analyse it.",
      el("div", { class: "panel" }, el("div", { class: "picks" }, names.map((e) => el("button", { class: "pick", type: "button", onclick: () => openCompany(e.company) },
        e.company, el("span", { class: "count", text: `${e.count} jobs` })))))));
  });
}

async function runCompany(name, careersUrl, news = true) {
  history.replaceState(null, "", `#company=${encodeURIComponent(name)}`);
  const out = $("#company-result");
  $("#company-status").textContent = "";
  try {
    const params = new URLSearchParams({ name, news: String(news) });
    if (careersUrl) params.set("careers_url", careersUrl);
    renderCompany(await runTask(`/api/tasks/company?${params}`, {}, out));
    OVERVIEW = null;
  } catch (err) {
    $("#company-status").textContent = `Analysis failed: ${err.message}`;
  }
}

async function rescoreCompany(name, message = "Company news arrived: scores updated.") {
  busy(1);
  try {
    renderCompany(await api(`/api/company?${new URLSearchParams({ name, news: "true" })}`));
    flash(message);
  } catch (_) { /* keep the current view */ } finally { busy(-1); }
}

/** Save what the user knows about the employer, then re-score every posting of it. */
async function saveCompany(res, fields, status) {
  try {
    await api(`/api/company/${res.company_id}`, { method: "PUT", body: JSON.stringify(fields) });
    status.textContent = "Saved. Re-scoring…";
    rescoreCompany(res.name, "Saved: the scores now include your entries.");
  } catch (err) { status.textContent = `Could not save: ${err.message}`; }
}

function field(label, control) {
  return el("label", { class: "field" }, el("span", { class: "field-label", text: label }), control);
}

function notesPanel(res) {
  const sig = res.signals || {};
  const status = el("span", { class: "small secondary", role: "status" });
  const choice = (value, text) => el("option", { value, text, selected: (sig.hiring_practice || "") === value ? true : null });
  const form = el("form", { class: "form-panel" },
    field("How this employer fills its jobs", el("select", { name: "hiring_practice" },
      choice("", "No note"), choice("internal_first", "Internal candidates usually get the jobs"),
      choice("external", "Usually hires from outside"))),
    field("Source or note", el("input", { name: "practice_note", maxlength: 300, value: sig.practice_note || "",
      placeholder: "e.g. own applications 2025, works agreement, insider" })),
    el("div", { class: "form-actions" }, status, el("button", { class: "btn btn-quiet", type: "submit", text: "Save note" })));
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const d = new FormData(form);
    saveCompany(res, { hiring_practice: d.get("hiring_practice"), practice_note: d.get("practice_note") }, status);
  });
  return panel("Your notes", "What you know from experience. It counts in every score of this employer.", form);
}

const OUTCOMES = [["none", "No reply"], ["auto_reject", "Automatic rejection"], ["reject", "Rejection"],
  ["internal", "Internal candidate chosen"], ["interview", "Interview"], ["offer", "Offer"]];

function outcomesPanel(res, items) {
  const r = res.signals?.reports || {};
  const counts = { none: r.no_response || 0, auto_reject: r.auto_reject || 0, reject: r.reject || 0, internal: r.internal || 0,
    interview: (r.interviews || 0) - (r.offers || 0), offer: r.offers || 0 };
  const decided = counts.auto_reject + counts.reject + counts.internal + counts.interview + counts.offer;
  const progressed = counts.interview + counts.offer;
  const summary = r.reports
    ? `${progressed} interview${progressed === 1 ? "" : "s"} or offer${progressed === 1 ? "" : "s"} from ${decided} answered application${decided === 1 ? "" : "s"}${counts.internal ? `, ${counts.internal} lost to internal candidates` : ""}; ${counts.none} without a reply.`
    : "No outcomes recorded yet.";
  const status = el("span", { class: "small secondary", role: "status" });
  const form = el("form", { class: "form-grid outcome-form" },
    field("Job (optional)", el("select", { name: "posting_id" }, el("option", { value: "", text: "Any job at this employer" }),
      items.slice(0, 100).map((sp) => el("option", { value: sp.posting_id, text: (sp.posting.title || "Untitled").slice(0, 70) })))),
    field("Applied on", el("input", { type: "date", name: "applied_on" })),
    field("Outcome", el("select", { name: "response" }, OUTCOMES.map(([k, label]) => el("option", { value: k, text: label })))),
    ...applicationFields(),
    el("div", { class: "form-actions" }, status, el("button", { class: "btn btn-quiet", type: "submit", text: "Add outcome" })));
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const d = new FormData(form);
    try {
      await api("/api/reports", { method: "POST", body: JSON.stringify({
        company: res.name, posting_id: d.get("posting_id") ? Number(d.get("posting_id")) : null,
        applied_on: d.get("applied_on") || null, response: d.get("response"), ...applicationValues(d) }) });
      status.textContent = "Added. Re-scoring…";
      rescoreCompany(res.name, "Outcome added: the scores now include it.");
    } catch (err) { status.textContent = `Could not save: ${err.message}`; }
  });
  const rows = OUTCOMES.map(([k, label]) => ({ key: k, label, value: counts[k] })).filter((x) => x.value > 0);
  const comm = res.signals?.communication;
  return panel("Application outcomes", "Your applications here and how they ended.",
    el("p", { class: "outcome-summary", text: summary }),
    comm && comm.level !== "unknown" ? el("div", { class: "comm-box" }, el("strong", { text: `Communication risk: ${comm.level}` }),
      el("span", { class: "small secondary", text: comm.text }), stageLines(comm.by_stage)) : null,
    rows.length ? barList(rows, { emphasis: new Set(["interview", "offer"]), unit: "applications" }) : null,
    rows.length ? el("p", { class: "panel-foot", text: "Blue: interviews and offers. Grey: everything else." }) : null,
    el("h4", { class: "subhead", text: "Add an outcome" }), form);
}

function sizePanel(res) {
  const sig = res.signals || {};
  const status = el("span", { class: "small secondary", role: "status" });
  const number = (name, value) => el("input", { type: "number", name, min: 0, value: value ?? "" });
  const form = el("form", { class: "form-grid" },
    field("Employees now", number("headcount", sig.headcount)),
    field("Employees a year ago", number("headcount_prev", sig.headcount_prev)),
    field("Last funding round", el("input", { type: "date", name: "funding_date",
      value: sig.funding_source === "your note" && sig.funding_date ? sig.funding_date : "" })),
    field("Amount and round", el("input", { name: "funding_amount", maxlength: 60, value: sig.funding_amount || "", placeholder: "e.g. €12M Series A" })),
    el("div", { class: "form-actions span-all" }, status, el("button", { class: "btn btn-quiet", type: "submit", text: "Save and re-score" })));
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const d = new FormData(form);
    const n = (k) => (d.get(k) ? Number(d.get(k)) : null);
    saveCompany(res, { headcount: n("headcount"), headcount_prev: n("headcount_prev"),
      funding_date: d.get("funding_date") || null, funding_amount: d.get("funding_amount") }, status);
  });
  const facts = [];
  if (sig.growth != null) facts.push(el("span", { class: "chip", text: `${sig.growth >= 0 ? "+" : "−"}${Math.abs(Math.round(sig.growth * 100))}% headcount in a year` }));
  if (sig.funding_months != null) {
    facts.push(el("span", { class: "chip", text: `Last funding ${sig.funding_months} month${sig.funding_months === 1 ? "" : "s"} ago (${sig.funding_source}${sig.funding_amount ? `, ${sig.funding_amount}` : ""})` }));
  }
  const capacity = sig.plausible_openings != null
    ? ratioBullet({ value: sig.open_jobs, norm: sig.plausible_openings, unit: "open jobs", normLabel: "the openings this size can plausibly fill",
        right: `${(sig.capacity_ratio ?? 0).toFixed(1)}× plausible`,
        aria: `${sig.open_jobs} open jobs against about ${sig.plausible_openings} plausible openings at a time` })
    : el("p", { class: "secondary small", text: "Add the number of employees to check whether the number of openings is plausible." });
  if (sig.fill_n) {
    facts.push(el("span", { class: "chip", text: `Likely filled: ${sig.fill_k} of ${sig.fill_n} closed jobs closed within the typical time` }));
  }
  return panel("Size, growth and funding", "Does the number of openings fit the company?",
  capacity, facts.length ? el("div", { class: "feed-chips" }, facts) : null, el("h4", { class: "subhead", text: "Your figures" }), form);
}

const handledTextTasks = new Set();

/** Background reading of missing ad texts (Bundesagentur, LinkedIn); `onDone(result)` runs once per task. */
function adTextLine(taskId, onDone) {
  const text = el("span", { text: "Reading the missing ad texts…" });
  const line = el("div", { class: "enrich-line" }, el("span", { class: "spinner", "aria-hidden": "true" }), text);
  const timer = setInterval(async () => {
    if (!line.isConnected) { clearInterval(timer); return; }
    try {
      const data = await api(`/api/tasks/${taskId}`);
      const steps = data.progress.steps;
      const finished = steps.filter((st) => ["done", "failed", "skipped"].includes(st.state)).length;
      text.textContent = `Reading the missing ad texts (${finished} of ${steps.length})…`;
      if (data.state === "running") return;
      clearInterval(timer);
      const filled = data.result?.filled || 0;
      const closed = data.result?.closed || 0;
      const summary = [filled ? `${filled} ad text${filled === 1 ? "" : "s"} read` : null,
        closed ? `${closed} job${closed === 1 ? "" : "s"} no longer online` : null].filter(Boolean).join(", ");
      if (handledTextTasks.has(taskId)) {
        line.replaceChildren(el("span", { class: "muted", text: summary ? `${summary}.` : "No further ad texts could be read." }));
        return;
      }
      handledTextTasks.add(taskId);
      if (filled || closed) {
        line.replaceChildren(el("span", { text: `${summary}: updating the scores…` }));
        onDone(summary);
      } else {
        line.replaceChildren(el("span", { class: "muted", text: "No ad texts could be read." }));
      }
    } catch (_) { clearInterval(timer); }
  }, 1500);
  return line;
}

function renderCompany(res) {
  const out = $("#company-result");
  const items = res.postings;
  const sig = res.signals || {};
  const links = makeLinks();
  const counts = gradeCounts(items);
  const flagged = (counts.elevated || 0) + (counts.high || 0);
  const onPlatforms = items.filter((s) => (s.copies || []).some((c) => c.channel !== "employer")).length;
  const gradeKey = { A: "low", B: "moderate", C: "elevated", D: "high" }[res.grade] || "unknown";
  const active = new Set(GRADE_ORDER);
  const tableHolder = el("div");
  const distHolder = el("div");
  const redraw = () => {
    distHolder.replaceChildren(gradeDistribution(items, { active, onToggle: (g) => { active.has(g) ? active.delete(g) : active.add(g); redraw(); } }));
    links.rows.clear();
    tableHolder.replaceChildren(postingsTable(items, { showCompany: false, filter: active, links }));
  };

  const feeds = res.feeds.length
    ? el("div", { class: "feed-chips" }, res.feeds.map((f) => el("span", { class: "chip" },
        `${sourceLabel(f.ats)} · ${f.slug} · ${f.error ? f.error : `${f.jobs} jobs${f.complete ? "" : " (partial)"}`}`)))
    : el("p", { class: "small muted", text: "No job feed found. Add the careers page URL to load all its jobs." });
  const depts = Object.entries(sig.departments || {}).map(([d, n]) => ({
    key: d, label: d, value: n,
    note: (sig.coherent_departments || []).includes(d) ? "Team build: 3+ distinct roles opened in the last 90 days" : null,
  })).sort((a, b) => b.value - a.value);
  const months = {};
  for (const s of items) {
    if (s.features.first_published) {
      const k = String(s.features.first_published).slice(0, 7);
      months[k] = (months[k] || 0) + 1;
    }
  }
  const medRatio = median(items.map((s) => s.features.excess_ratio));
  out.replaceChildren(...[
    res.text_task ? adTextLine(res.text_task, (summary) => rescoreCompany(res.name, `${summary}: wording checks and applicant counts now included.`)) : null,
    notesBlock(res.notes),
    el("div", { class: "panel company-head" },
      el("div", { class: `grade-plate ${GRADES[gradeKey].cls}`, title: `Employer grade ${res.grade}` }, res.grade || "?", gradeIcon(gradeKey, 26)),
      el("div", {}, el("p", { class: "eyebrow", text: "Employer grade" }), el("h2", { class: "company-name", text: res.name }),
        el("p", { class: "company-note", text: res.grade_note }), evidenceNote(items, res.grade), feeds,
        sig.hiring_practice ? el("div", { class: "feed-chips" }, el("span", { class: "chip note-chip", text: sig.hiring_practice === "internal_first"
          ? "Your note: internal candidates usually get the jobs" : "Your note: usually hires from outside" })) : null),
      el("div", { class: "verdict-actions" },
        el("button", { class: "btn btn-quiet", type: "button", onclick: () => addWatch("company", res.name) }, "Track employer"))),
    kpiBand(
      kpi("Open jobs", items.length, { note: onPlatforms ? `${onPlatforms} also seen on job platforms` : "from the employer's own feed",
        viz: shareBar(onPlatforms, items.length),
        help: "One entry per job: the employer's own listing plus its copies on LinkedIn, the Bundesagentur and Google for Jobs, merged. The bar shows the share also seen on platforms." }),
      kpi("Elevated or high", flagged, { unit: pct(flagged, items.length), note: "of open jobs", viz: miniGradeBar(counts),
        help: "Postings whose observable facts add up to an elevated or high ghost-risk indicator." }),
      kpi("Median age vs norm", medRatio != null ? `${medRatio.toFixed(1)}×` : "—", {
        note: `median ${median(items.map((s) => s.features.live_days)) ?? "—"} days online`, viz: medRatio != null ? miniBullet(medRatio) : null,
        help: "Time online divided by the typical advertising time for each job's occupation, counted from the first publication anywhere." }),
      kpi("Departments", depts.length, { note: sig.coherent_departments?.length ? `Team builds: ${sig.coherent_departments.join(", ")}` : "no team builds seen",
        help: "Departments with open roles. A team build is a department with 3+ distinct roles opened in the last 90 days." }),
      kpi("Tracked for", fmtDays(sig.tracked_days), { note: "reposts and removals need repeated checks",
        help: "How long the radar has been watching this employer. Add it to the watchlist for automatic re-checks." })),
    section("Postings at a glance", "Click a grade to filter.",
      row([
        panel("Ghost-risk grades", `${items.length} open jobs`, distHolder,
          items.length ? el("h4", { class: "subhead", text: "Highest ghost-risk" }) : null,
          items.length ? flagList([...items].sort((a, b) => b.score.risk - a.score.risk).slice(0, 4),
            { onSelect: links.select, onHover: (sp, on) => links.highlight(sp.posting_id, on) }) : null),
        panel("Time online against the norm", "One mark per job.",
          ageStrip(items, { onSelect: links.select, onHover: (sp, on) => links.highlight(sp.posting_id, on) })),
      ], "g-5-7")),
    section("Hiring activity", "When the open jobs were published, and in which teams.",
      row([
        panel("First published", "By month of first publication. Grey: over a year ago.", publicationMonths(months)),
        panel("Open roles by department", depts.length ? "Highlighted: team builds. Grey: other departments." : null,
          depts.length ? barList(depts.slice(0, 12), { emphasis: new Set(sig.coherent_departments || []), unit: "open roles" })
            : el("p", { class: "secondary", text: "The feed has no department data." })),
      ], "g-7-5")),
    section("What you know about this employer", "Saved on this computer. It counts in every score of this employer.",
      row([notesPanel(res), outcomesPanel(res, items)]), row([eventsPanel(res), contractsPanel(res)])),
    section("Size, growth, funding and news", "Whether the number of openings fits the company, and what the news says.",
      row([
        sizePanel(res),
        panel("Company news", "Layoffs, insolvency, freezes and funding in the last 6 months.",
          newsBlock(res.company_id, sig.news_status, sig.events || [], () => rescoreCompany(res.name))),
      ])),
    section("All postings", "Click a row for the full analysis.", el("div", { class: "panel panel-flush" }, tableHolder)),
  ].filter(Boolean));
  redraw();
}

/** How much evidence the employer grade rests on; warns when it is thin. */
function evidenceNote(items, grade) {
  if (!items.length) return null;
  const used = items.map((sp) => (sp.score.coverage || []).filter((c) => c.state === "used").length);
  const avg = used.reduce((a, b) => a + b, 0) / used.length;
  const total = items[0].score.coverage?.length || 7;
  const textless = items.filter((sp) => !(sp.posting.description || "").trim()).length;
  if (avg >= 3 && textless < items.length / 2) return null;
  return el("p", { class: "company-note thin", text: `Little evidence so far (${avg.toFixed(1)} of ${total} kinds per job), so this grade can change.` });
}

function openCompany(name) {
  showTab("company", { hash: false });
  $("#company-form").elements.name.value = name;
  runCompany(name, null, true);
}

$("#company-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const data = new FormData(e.currentTarget);
  runCompany(String(data.get("name")).trim(), data.get("careers_url") || null, Boolean(data.get("news")));
});

// ------------------------------------------------------------------ city view

let map = null;
let markerLayer = null;
let lastCityParams = null;
let cityHasResults = false;
let cityTextTask = null; // background reading of ad texts for the current city search

/** Live line for the background check of the top employers' own job sites; refreshes results when found. */
function enrichmentLine(taskId) {
  const text = el("span", { text: "Checking the top employers' own job sites for more evidence…" });
  const line = el("div", { class: "enrich-line" }, el("span", { class: "spinner", "aria-hidden": "true" }), text);
  const timer = setInterval(async () => {
    if (!line.isConnected) { clearInterval(timer); return; }
    try {
      const data = await api(`/api/tasks/${taskId}`);
      const steps = data.progress.steps;
      text.textContent = `Checking the top employers' own job sites (${steps.filter((s) => s.state === "done").length} of ${steps.length})…`;
      if (data.state === "running") return;
      clearInterval(timer);
      const found = data.result?.found || [];
      if (found.length && lastCityParams) {
        line.replaceChildren(el("span", { text: `Found the own job sites of ${found.join(", ")}: updating results…` }));
        renderCity(await api(`/api/city?${lastCityParams}&texts=false`));
        flash(`Employer sites found for ${found.join(", ")}: results now include the employer-site check.`);
      } else {
        line.replaceChildren(el("span", { class: "muted", text: "No public job feeds found for the top employers, so the employer-site check stays unavailable for them." }));
      }
    } catch (_) { clearInterval(timer); }
  }, 1500);
  return line;
}

function ensureMap() {
  if (typeof L === "undefined") return;
  if (map) { setTimeout(() => map.invalidateSize(), 60); return; }
  map = L.map("map", { scrollWheelZoom: false }).setView([51.16, 10.45], 6);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 18, attribution: "© OpenStreetMap contributors" }).addTo(map);
  markerLayer = L.layerGroup().addTo(map);
  const legend = L.control({ position: "bottomright" });
  legend.onAdd = () => el("div", { class: "map-legend" }, el("strong", { text: "Ghost-risk" }),
    GRADE_ORDER.map((g) => el("div", {}, gradeIcon(g, 16), GRADES[g].label)));
  legend.addTo(map);
}

function markerIcon(grade) {
  const wrap = el("div", { class: "mk", style: "width:28px;height:28px;display:grid;place-items:center" }, gradeIcon(grade, 22));
  return L.divIcon({ className: "mk-wrap", html: wrap, iconSize: [28, 28], iconAnchor: [14, 14] });
}

function sourceToggles() {
  const box = $("#city-sources");
  const defs = [["linkedin", "LinkedIn"], ["ba", "Bundesagentur"], ["jsearch", "Google for Jobs"], ["adzuna", "Adzuna"], ["arbeitnow", "Arbeitnow"], ["tracked", "Tracked employer feeds"]];
  const connected = { ...META.connectors, arbeitnow: true, tracked: true, ba: META.connectors.bundesagentur };
  box.replaceChildren(...defs.map(([key, label]) => {
    const on = Boolean(connected[key]);
    const lab = el("label", { class: `toggle-chip${on ? "" : " off"}` },
      el("input", { type: "checkbox", name: "src", value: key, checked: on ? true : null, disabled: on ? null : true }), label);
    if (!on) hoverable(lab, () => tip("Not connected", label));
    return lab;
  }));
}

function renderCityIntro() {
  const side = $("#city-side");
  if (cityHasResults || side.children.length) return;
  side.replaceChildren(panel("How to read the map", "Each marker is one job, marked by grade.",
    el("div", { class: "legend" }, GRADE_ORDER.map((g) => el("span", { class: "legend-item" }, gradeIcon(g, 16), GRADES[g].label))),
    el("p", { class: "panel-foot", text: "Search a city to see its jobs on the map." })));
  withOverview((data) => {
    const cities = (data.top_cities || []).filter((c) => c.company !== "Unknown").slice(0, 8);
    if (cityHasResults || !cities.length) return;
    side.append(panel("Cities the radar knows", "Click one to search it again.", el("div", { class: "picks" },
      cities.map((c) => el("button", { class: "pick", type: "button", onclick: () => openCity(c.company) }, c.company, el("span", { class: "count", text: `${c.count}` }))))));
  });
}

function renderCity(res) {
  ensureMap();
  cityHasResults = true;
  const items = res.postings;
  const links = makeLinks();
  const active = new Set(GRADE_ORDER);
  const distHolder = el("div");
  const tableHolder = el("div");
  const keyword = lastCityParams ? new URLSearchParams(lastCityParams).get("q") : null;

  const drawMarkers = () => {
    if (!map) return;
    markerLayer.clearLayers();
    links.markers.clear();
    const points = [];
    for (const sp of items) {
      const p = sp.posting;
      if (p.lat == null || p.lon == null || !active.has(sp.score.grade)) continue;
      const marker = L.marker([p.lat, p.lon], { icon: markerIcon(sp.score.grade), keyboard: true,
        title: `${GRADES[sp.score.grade]?.label || ""} ghost-risk: ${p.title}` });
      marker.on("mouseover", (e) => {
        showFloating(postingCard(sp), e.originalEvent.clientX, e.originalEvent.clientY);
        links.highlight(sp.posting_id, true);
      });
      marker.on("mouseout", () => { hideFloating(); links.highlight(sp.posting_id, false); });
      marker.on("click", () => links.select(sp));
      marker.addTo(markerLayer);
      links.markers.set(sp.posting_id, marker);
      points.push([p.lat, p.lon]);
    }
    if (points.length) map.fitBounds(points, { padding: [30, 30], maxZoom: 13 });
    else if (res.center) map.setView(res.center, 11);
  };
  const redraw = () => {
    distHolder.replaceChildren(gradeDistribution(items, { active, onToggle: (g) => { active.has(g) ? active.delete(g) : active.add(g); redraw(); } }));
    links.rows.clear();
    tableHolder.replaceChildren(postingsTable(items, { filter: active, links }));
    drawMarkers();
  };

  const s = res.summary || {};
  const counts = s.grades || gradeCounts(items);
  const flagged = (counts.elevated || 0) + (counts.high || 0);
  const sourceRows = Object.entries(s.sources || {}).sort((a, b) => b[1] - a[1]).map(([k, v]) => ({ key: k, label: k, value: v }));
  const ba = s.ba_facets;
  const approximate = items.some((sp) => sp.posting.extra?.approximate_position);
  const ratios = median(items.map((sp) => sp.features.excess_ratio));
  if (s.text_task) cityTextTask = s.text_task;
  $("#city-summary").replaceChildren(...[
    s.enrich_task ? enrichmentLine(s.enrich_task) : null,
    cityTextTask ? adTextLine(cityTextTask, async (summary) => {
      renderCity(await api(`/api/city?${lastCityParams}&texts=false`));
      flash(`${summary}: wording checks and applicant counts now included.`);
    }) : null,
    notesBlock(res.notes),
    el("div", { class: "view-head" },
      el("div", { class: "view-title" }, el("p", { class: "eyebrow", text: "Results" }),
        el("h2", { class: "sec-title", text: `${res.city}${keyword ? ` · ${keyword}` : ""}` })),
      el("button", { class: "btn btn-quiet", type: "button", onclick: () => addWatch("city", res.city, keyword ? { keyword } : {}) }, "Track this city")),
    kpiBand(
      kpi(`Jobs in ${res.city}`, s.total ?? items.length, { note: `from ${sourceRows.length} source${sourceRows.length === 1 ? "" : "s"}`,
        help: "One entry per job after filters; copies of the same job on several platforms are merged (see “Seen on”)." }),
      kpi("Elevated or high", flagged, { unit: pct(flagged, s.total || items.length), note: "of these jobs", viz: miniGradeBar(counts),
        help: "Postings whose observable facts add up to an elevated or high indicator." }),
      kpi("Median age vs norm", ratios != null ? `${ratios.toFixed(1)}×` : "—", { note: `median ${s.median_age_days ?? "—"} days online`,
        viz: ratios != null ? miniBullet(ratios) : null,
        help: "From the earliest publication date seen anywhere. Arbeitnow dates can be import dates, so they are minimums." }),
      kpi("Staffing agencies", s.agencies ?? 0, { unit: pct(s.agencies ?? 0, s.total || items.length), note: "postings by agencies",
        viz: shareBar(s.agencies ?? 0, s.total || items.length),
        help: "Detected from the Bundesagentur's Zeitarbeit and private-recruiter flags, agency names and placement wording." })),
  ].filter(Boolean));

  const raised = items.filter((sp) => sp.score.grade === "high" || sp.score.grade === "elevated");
  $("#city-side").replaceChildren(
    panel("Ghost-risk grades", "Click a grade to filter.", distHolder),
    panel("Needs a closer look", "Hover to find it on the map; click to open it in the table.",
      flagList((raised.length ? raised : items).slice(0, 5), { onSelect: links.select, onHover: (sp, on) => links.highlight(sp.posting_id, on) })));

  $("#city-result").replaceChildren(...[
    section("Time online against the norm", "One mark per job, by grade.",
      el("div", { class: "panel" }, ageStrip(items, { onSelect: links.select, onHover: (sp, on) => links.highlight(sp.posting_id, on) }))),
    section("Who advertises", null, row([
      panel("Employers with the most jobs", "Click a name to analyse the employer.", employerBars(s.top_employers || [], { onSelect: (name) => openCompany(name) })),
      panel("Where these postings come from", null, barList(sourceRows, { unit: "postings" }),
        ba ? el("div", { class: "stack", style: "margin-top:18px" }, el("h4", { class: "subhead", text: "Bundesagentur facts for this search" }),
          el("div", { class: "kpi-band compact" },
            kpi("In the area", ba.total ?? "—", { help: "All matching jobs on the Bundesagentur board." }),
            kpi("Partner boards", `${Math.round((ba.partner_board_share || 0) * 100)}%`, { help: "Copied in from other job boards." }),
            kpi("Private recruiters", `${Math.round((ba.private_recruiter_share || 0) * 100)}%`, { help: "Posted by placement agencies." }),
            kpi("New in 7 days", ba.published_last_7_days ?? "—", { help: "New in the last week." })),
          ba.top_employers?.length ? el("div", { class: "stack" }, el("p", { class: "small secondary", text: "Largest advertisers on the Bundesagentur board" }),
            barList(ba.top_employers.slice(0, 6).map((e) => ({ key: e.company, label: e.company, value: e.count })), { unit: "postings", onSelect: (r) => openCompany(r.label) })) : null)
          : null),
    ])),
    section("All postings", "Click a row for the full analysis.",
      el("div", { class: "panel panel-flush" }, tableHolder)),
    res.sources_used.length ? el("p", { class: "small muted", text: `Sources: ${res.sources_used.join(", ")}` }) : null,
  ].filter(Boolean));
  redraw();
}

function openCity(city, q = "") {
  showTab("city", { hash: false });
  const form = $("#city-form");
  form.elements.city.value = city;
  form.elements.q.value = q;
  form.requestSubmit();
}

$("#city-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.currentTarget;
  const data = new FormData(form);
  const out = $("#city-result");
  const params = new URLSearchParams({ city: String(data.get("city")).trim(), radius: String(data.get("radius")) });
  if (data.get("q")) params.set("q", String(data.get("q")).trim());
  if (data.get("posted_within")) params.set("posted_within", String(data.get("posted_within")));
  if (data.get("job_type")) params.set("job_type", String(data.get("job_type")));
  if (data.get("remote")) params.set("remote", "true");
  if (data.get("exclude_agencies")) params.set("exclude_agencies", "true");
  const chosen = data.getAll("src");
  if (chosen.length) params.set("sources", chosen.join(","));
  lastCityParams = params.toString();
  cityTextTask = null;
  history.replaceState(null, "", `#city=${encodeURIComponent(params.get("city"))}${params.get("q") ? `&q=${encodeURIComponent(params.get("q"))}` : ""}`);
  $("#city-status").textContent = "";
  try {
    renderCity(await runTask(`/api/tasks/city?${params}`, {}, out));
    OVERVIEW = null;
  } catch (err) {
    $("#city-status").textContent = `Search failed: ${err.message}`;
  }
});

// ------------------------------------------------------------------ watchlist

const ICONS = {
  company: "M4.5 21V4.5A1.5 1.5 0 0 1 6 3h7.5A1.5 1.5 0 0 1 15 4.5V21M15 9h3a1.5 1.5 0 0 1 1.5 1.5V21M3 21h18M8 7.5h3.5M8 11.5h3.5M8 15.5h3.5",
  city: "M12 21s-6.5-5.8-6.5-11a6.5 6.5 0 0 1 13 0c0 5.2-6.5 11-6.5 11zM14.4 10a2.4 2.4 0 1 1-4.8 0 2.4 2.4 0 0 1 4.8 0z",
};
const icon = (kind) => {
  const s = svgEl("svg", { viewBox: "0 0 24 24", "aria-hidden": "true" });
  s.append(svgEl("path", { d: ICONS[kind] || ICONS.company }));
  return s;
};

async function addWatch(kind, query, params = {}) {
  try {
    await api("/api/watchlist", { method: "POST", body: JSON.stringify({ kind, query, params }) });
    flash(`Added ${query} to the watchlist. It is re-checked automatically.`);
    api("/api/watchlist").then((items) => updateWatchCount(items.length)).catch(() => {});
  } catch (err) { flash(`Could not add to the watchlist: ${err.message}`); }
}

function watchItem(item) {
  const r = item.last_result;
  const meta = [el("span", { text: item.kind === "company" ? "Company" : "City" }),
    el("span", { text: item.last_run ? `checked ${fmtDate(item.last_run)}` : "not checked yet" })];
  if (item.params?.keyword) meta.push(el("span", { text: `keyword “${item.params.keyword}”` }));
  if (r && r.error) meta.push(el("span", { text: `Error: ${r.error}` }));
  else if (r) {
    meta.push(el("span", { text: item.kind === "company" ? `${r.postings} jobs · grade ${r.grade} · ${r.flagged} elevated or high` : `${r.postings} jobs` }));
    if (r.grades) meta.push(miniGradeBar(r.grades));
  }
  return el("li", { class: "watch-item" },
    el("span", { class: "watch-icon" }, icon(item.kind)),
    el("div", { class: "watch-main" }, el("span", { class: "watch-name", text: item.query }), el("div", { class: "watch-meta" }, meta)),
    el("div", { class: "watch-actions" },
      el("button", { class: "btn btn-small btn-quiet", type: "button", onclick: () => openWatch(item) }, "Open"),
      el("button", { class: "btn btn-small btn-ghost", type: "button", onclick: () => runWatch(item) }, "Check now"),
      el("button", { class: "btn btn-small btn-ghost", type: "button", onclick: async () => { await api(`/api/watchlist/${item.id}`, { method: "DELETE" }); loadWatchlist(); } }, "Remove")));
}

async function loadWatchlist() {
  const out = $("#watch-result");
  try {
    const items = await api("/api/watchlist");
    updateWatchCount(items.length);
    if (!items.length) {
      out.replaceChildren(el("div", { class: "panel empty" },
        el("h2", { text: "Nothing tracked yet" }),
        el("p", { text: "Add a company or a city above, or use “Track employer” on any result." })));
      try { out.append(await notesSection()); } catch (_) { /* the notes list is optional */ }
      return;
    }
    out.replaceChildren(section(`${items.length} watched`, "Re-checked automatically every 12 hours.",
      el("div", { class: "panel panel-flush" }, el("ul", { class: "watch-list" }, items.map(watchItem)))));
  } catch (err) { out.replaceChildren(el("div", { class: "panel" }, el("p", { text: `Could not load the watchlist: ${err.message}` }))); }
  try { out.append(await notesSection()); } catch (_) { /* the notes list is optional */ }
}

async function runWatch(item) {
  $("#watch-status").textContent = `Checking ${item.query}…`;
  busy(1);
  try { await api(`/api/watchlist/${item.id}/run`, { method: "POST" }); $("#watch-status").textContent = ""; }
  catch (err) { $("#watch-status").textContent = `Check failed: ${err.message}`; }
  finally { busy(-1); }
  loadWatchlist();
}

function openWatch(item) {
  if (item.kind === "company") { openCompany(item.query); return; }
  openCity(item.query, item.params?.keyword || "");
}

$("#watch-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.currentTarget;
  const data = new FormData(form);
  const kind = data.get("kind");
  const extra = String(data.get("extra") || "").trim();
  const params = extra ? (kind === "company" ? { careers_url: extra } : { keyword: extra }) : {};
  await addWatch(kind, String(data.get("query")).trim(), params);
  form.reset();
  loadWatchlist();
});

// ------------------------------------------------------------------ verdicts: chance, communication, evidence

const CHANCE_STEPS = [["good", "Good"], ["fair", "Fair"], ["low", "Low"], ["very_low", "Very low"]];
const COMM_STEPS = [["low", "Low"], ["medium", "Medium"], ["high", "High"]];
const EVENT_KINDS = [
  ["hiring_freeze", "Hiring freeze"], ["restructuring", "Restructuring or job cuts"], ["manager_left", "Hiring manager left"],
  ["recruiter_change", "Recruiter reassigned or recruiting team cut"], ["project_cancelled", "Project cancelled or financing delayed"],
  ["contract_won", "Contract or order won"], ["expansion", "New site, product or team expansion"], ["funding", "Funding round or grant"],
  ["new_starters", "Confirmed new starters in the team"],
];
const LOG_KINDS = { posting: "Posting", applicants: "Applicants", outcome: "Your application", audit: "Audit", distress: "Distress",
  funding: "Funding", growth: "Growth", contract: "Contract", other: "News" };

/** A row of steps with the current one marked (chance, communication); never status colours. */
function stepScale(steps, current, label) {
  const idx = steps.findIndex(([k]) => k === current);
  return el("div", { class: "effort", role: "img", "aria-label": `${label}: ${steps[idx]?.[1] || current}` },
    el("div", { class: "effort-steps", style: `grid-template-columns:repeat(${steps.length},1fr)` },
      steps.map((_, i) => el("span", { class: `effort-step${i === idx ? " current" : ""}` }))),
    el("div", { class: "effort-labels", style: `grid-template-columns:repeat(${steps.length},1fr)`, "aria-hidden": "true" },
      steps.map(([, l], i) => el("span", { class: i === idx ? "current" : null, text: l }))));
}

// reasons the chance text does not already say
const whyNotInText = (c) => (c?.why || []).filter((w) => !(c.text || "").includes(w));

function confidenceLine(level) {
  return el("p", { class: `conf conf-${level || "low"}` }, el("span", { class: "conf-dot", "aria-hidden": "true" }),
    `Confidence: ${level || "low"}`);
}

function chanceCard(c) {
  const known = c && c.chance && c.chance !== "unknown";
  const label = Object.fromEntries(CHANCE_STEPS)[c?.chance];
  const unit = c?.clicks ? "clicked apply" : c?.bound === "first" ? "applicants at most" : c?.bound === "over" ? "applicants or more" : "applicants";
  return el("div", { class: "panel advice" },
    el("p", { class: "eyebrow", text: "Your chance" }),
    el("div", { class: "advice-tier", text: known ? label : "Not known yet" }),
    c?.applicants != null ? ratioBullet({ value: c.applicants, norm: c.per_hire, unit,
      normLabel: "the applications per hire typical for the field",
      right: c.rate_per_day ? `${c.rate_per_day}/day` : "",
      aria: `${c.applicants} ${unit}, ${c.ratio} times the typical ${c.per_hire} per hire` }) : null,
    el("p", { class: "advice-text", text: c?.text || "" }),
    whyNotInText(c).length ? el("ul", { class: "plain small" }, whyNotInText(c).map((w) => el("li", { text: w }))) : null,
    known ? stepScale(CHANCE_STEPS, c.chance, "Your chance") : null,
    confidenceLine(c?.confidence));
}

function stageLines(byStage) {
  const names = { application: "After applying", screening: "After screening", interview: "After the interview" };
  const rows = Object.entries(byStage || {}).filter(([, v]) => v.replied + v.silent + v.unresolved > 0);
  if (!rows.length) return null;
  return el("ul", { class: "stage-lines" }, rows.map(([stage, v]) => el("li", {},
    el("span", { text: names[stage] || stage }),
    el("span", { class: "mono", text: `${v.replied} replied · ${v.silent} silent · ${v.unresolved} open` }))));
}

function communicationCard(m) {
  const known = m && m.level && m.level !== "unknown";
  const label = Object.fromEntries(COMM_STEPS)[m?.level];
  return el("div", { class: "panel advice" },
    el("p", { class: "eyebrow", text: "Communication risk" }),
    el("div", { class: "advice-tier", text: known ? `${label} risk of silence` : "No record yet" }),
    el("p", { class: "advice-text", text: m?.text || "No applications to this employer recorded yet." }),
    known ? stepScale(COMM_STEPS, m.level, "Communication risk") : null,
    stageLines(m?.by_stage),
    confidenceLine(m?.confidence));
}

function evidencePanel(sp) {
  const holder = el("div", { class: "evlog-wrap" }, el("p", { class: "secondary small", text: "Loading…" }));
  api(`/api/postings/${sp.posting_id}/evidence`).then((items) => {
    holder.replaceChildren(items.length ? el("ol", { class: "evlog" }, items.map((i) => el("li", {},
      el("span", { class: "evlog-date mono", text: fmtDate(i.at) }),
      el("span", { class: "chip", text: LOG_KINDS[i.kind] || i.kind }),
      el("span", { class: "evlog-text" }, safeUrl(i.url) ? el("a", { href: i.url, target: "_blank", rel: "noopener noreferrer", text: i.text }) : i.text,
        i.source ? el("span", { class: "muted", text: ` · ${sourceLabel(i.source)}` }) : null))))
      : el("p", { class: "secondary", text: "No dated observations yet." }));
  }).catch(() => holder.replaceChildren(el("p", { class: "secondary small", text: "Observations not available." })));
  return panel("Dated observations", "Newest first.", holder);
}

function employerNoteForm(sp) {
  const c = sp.features.company;
  if (!c?.company_id) return null;
  const status = el("span", { class: "small secondary", role: "status" });
  const choice = (value, text) => el("option", { value, text, selected: (c.hiring_practice || "") === value ? true : null });
  const form = el("form", { class: "form-inline" },
    field("How this employer fills its jobs", el("select", { name: "hiring_practice" }, choice("", "No note"),
      choice("internal_first", "Internal candidates usually get the jobs"), choice("external", "Usually hires from outside"))),
    el("label", { class: "field grow" }, el("span", { class: "field-label", text: "Source or note" }),
      el("input", { name: "practice_note", maxlength: 300, value: c.practice_note || "", placeholder: "e.g. own applications, insider" })),
    el("button", { class: "btn btn-quiet", type: "submit", text: "Save note" }), status);
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const d = new FormData(form);
    try {
      await api(`/api/company/${c.company_id}`, { method: "PUT", body: JSON.stringify({ hiring_practice: d.get("hiring_practice"), practice_note: d.get("practice_note") }) });
      status.textContent = "Saved. Updating…";
      refreshPosting(sp.posting_id, "Your note about the employer is now part of the score.");
    } catch (err) { status.textContent = `Could not save: ${err.message}`; }
  });
  return el("details", { class: "more note-form" },
    el("summary", {}, c.hiring_practice ? "Your note about this employer" : "Add your note about this employer",
      c.hiring_practice ? el("span", { class: "muted", text: c.hiring_practice === "internal_first" ? "internal candidates usually get the jobs" : "usually hires from outside" }) : null),
    form);
}

/** Stage, promised date, follow-ups and withdrawal: what the communication record needs. */
function applicationFields() {
  return [
    field("Stage reached", el("select", { name: "stage" }, el("option", { value: "application", text: "Application sent" }),
      el("option", { value: "screening", text: "Screening call" }), el("option", { value: "interview", text: "Interview" }))),
    field("Update promised by", el("input", { type: "date", name: "promised_by" })),
    field("Unanswered follow-ups", el("input", { type: "number", name: "followups", min: 0, max: 20 })),
    el("label", { class: "check" }, el("input", { type: "checkbox", name: "withdrawn" }), "I withdrew"),
  ];
}

function applicationValues(d) {
  return { stage: d.get("stage") || null, promised_by: d.get("promised_by") || null,
    followups: d.get("followups") ? Number(d.get("followups")) : null, withdrawn: d.get("withdrawn") ? true : null };
}

function applicantsCell(c) {
  if (!c || c.applicants == null) return el("span", { class: "muted", text: "—" });
  const n = c.bound === "first" ? `<${c.applicants}` : c.bound === "over" ? `${c.applicants}+` : String(c.applicants);
  const chance = Object.fromEntries(CHANCE_STEPS)[c.chance];
  return el("span", { class: "age-cell" }, el("span", { class: "mono", text: `${n}${c.clicks ? " clicks" : ""}` }),
    el("span", { class: "small muted", text: [c.rate_per_day ? `${c.rate_per_day}/day` : null, chance ? `chance ${chance.toLowerCase()}` : null].filter(Boolean).join(" · ") }));
}

function eventsPanel(res) {
  const sig = res.signals || {};
  const mine = (sig.events || []).filter((e) => e.source === "your note");
  const status = el("span", { class: "small secondary", role: "status" });
  const form = el("form", { class: "form-grid" },
    field("What happened", el("select", { name: "kind" }, EVENT_KINDS.map(([k, l]) => el("option", { value: k, text: l })))),
    field("When", el("input", { type: "date", name: "date", required: true })),
    field("Note or source", el("input", { name: "note", maxlength: 300, placeholder: "e.g. team lead left in September" })),
    el("div", { class: "form-actions" }, status, el("button", { class: "btn btn-quiet", type: "submit", text: "Add event" })));
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const d = new FormData(form);
    try {
      await api(`/api/company/${res.company_id}/events`, { method: "POST", body: JSON.stringify({ kind: d.get("kind"), date: d.get("date"), note: d.get("note") || null }) });
      status.textContent = "Added. Re-scoring…";
      rescoreCompany(res.name, "Event added: the scores now include it.");
    } catch (err) { status.textContent = `Could not save: ${err.message}`; }
  });
  const list = mine.length ? el("ul", { class: "event-list" }, mine.map((ev) => el("li", {},
    el("span", { class: "mono small", text: fmtDate(ev.published_at) }), el("span", { text: ev.title }),
    el("button", { class: "btn btn-small btn-ghost", type: "button", text: "Remove", onclick: async () => {
      await api(`/api/company/${res.company_id}/events/${ev.id}`, { method: "DELETE" });
      rescoreCompany(res.name, "Event removed.");
    } }))))
    : el("p", { class: "secondary small", text: "None yet." });
  return panel("Dated events you know of", "A freeze, a departure, a won contract: dated changes that affect the scores.", list,
    el("h4", { class: "subhead", text: "Add an event" }), form);
}

function contractsPanel(res) {
  const contracts = (res.signals?.events || []).filter((e) => e.kind === "contract" && e.source !== "your note");
  return panel(contracts.length ? `Public contracts won (${contracts.length})` : "Public contracts won", "Work that may need staff.",
    contracts.length ? el("ul", { class: "events" }, contracts.slice(0, 8).map((e) => el("li", {},
      safeUrl(e.url) ? el("a", { href: e.url, target: "_blank", rel: "noopener noreferrer", text: e.title }) : e.title,
      el("span", { class: "small muted", text: fmtDate(e.published_at) }))))
      : el("p", { class: "secondary small", text: "No public contracts found." }));
}

// ------------------------------------------------------------------ employer notes list (watchlist page)

async function notesSection() {
  const box = el("div", { class: "stack" });
  const render = async () => {
    const notes = await api("/api/notes");
    box.replaceChildren(notes.length
      ? el("div", { class: "panel panel-flush table-wrap" }, el("table", {},
          el("thead", {}, el("tr", {}, el("th", { text: "Employer" }), el("th", { text: "Your note" }), el("th", { class: "num", text: "Events" }),
            el("th", { class: "num", text: "Outcomes" }), el("th", { text: "" }))),
          el("tbody", {}, notes.map((n) => el("tr", {},
            el("td", { class: "title-cell", text: n.name }),
            el("td", { class: "secondary", text: [n.hiring_practice === "internal_first" ? "Internal candidates usually get the jobs" : n.hiring_practice === "external" ? "Usually hires from outside" : null, n.practice_note].filter(Boolean).join(" · ") || "figures only" }),
            el("td", { class: "num", text: n.events }), el("td", { class: "num", text: n.outcomes }),
            el("td", {}, el("button", { class: "btn btn-small btn-quiet", type: "button", text: "Open", onclick: () => openCompany(n.name) })))))))
      : el("p", { class: "secondary", text: "No notes yet." }));
  };
  await render();
  const status = el("span", { class: "small secondary", role: "status" });
  const area = el("textarea", { name: "csv", rows: 4, placeholder: "Example GmbH;internal;own applications 2026\nSample AG;external;" });
  const form = el("form", { class: "form-panel" }, area,
    el("div", { class: "form-actions" }, status, el("button", { class: "btn btn-quiet", type: "submit", text: "Import notes" })));
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const r = await api("/api/notes/import", { method: "POST", body: JSON.stringify({ csv: area.value }) });
      status.textContent = `Imported ${r.added}${r.skipped.length ? `, skipped ${r.skipped.length} (use internal or external)` : ""}.`;
      area.value = "";
      render();
    } catch (err) { status.textContent = `Could not import: ${err.message}`; }
  });
  return section("Employer notes", "What you know about employers, in one place.",
    box, panel("Import a list", "One per line: company; internal or external; note.", form));
}

// ------------------------------------------------------------------ your thresholds (method page)

async function thresholdsPanel() {
  const prefs = await api("/api/prefs");
  const status = el("span", { class: "small secondary", role: "status" });
  const option = (value, text, current) => el("option", { value, text, selected: String(current) === String(value) ? true : null });
  const form = el("form", { class: "form-grid" },
    field("Age starts to count at", el("select", { name: "age_start" }, option(1, "1× typical (default)", prefs.age_start),
      option(0.75, "0.75× (strict)", prefs.age_start))),
    field("Low chance from (applicants)", el("input", { type: "number", name: "chance_high", min: 5, value: prefs.chance_high })),
    field("Very low chance from (applicants)", el("input", { type: "number", name: "chance_very_high", min: 10, value: prefs.chance_very_high })),
    field("History window", el("select", { name: "window_days" }, prefs.windows.map((d) =>
      option(d, d === 7 ? "Past week" : d === 30 ? "Past month" : d === 90 ? "Past 3 months" : "Past year (maximum)", prefs.window_days)))),
    el("div", { class: "form-actions" }, status, el("button", { class: "btn btn-quiet", type: "submit", text: "Save settings" })));
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const d = new FormData(form);
    try {
      await api("/api/prefs", { method: "PUT", body: JSON.stringify({ age_start: Number(d.get("age_start")), chance_high: Number(d.get("chance_high")),
        chance_very_high: Number(d.get("chance_very_high")), window_days: Number(d.get("window_days")) }) });
      status.textContent = "Saved. New checks and views use them.";
      OVERVIEW = null;
    } catch (err) { status.textContent = `Could not save: ${err.message}`; }
  });
  return form;
}

// ------------------------------------------------------------------ model page

function estimateLine(est) {
  const line = el("p", { class: "estimate-line", tabindex: 0 },
    el("span", { class: "estimate-value", text: `Model: ${Math.round(est.p * 100)}%` }),
    ` likely not genuinely open (90% interval ${Math.round(est.low * 100)}–${Math.round(est.high * 100)}%), trained on ${est.labels} labels`);
  hoverable(line, () => el("div", { class: "tipbox" }, el("strong", { text: `${Math.round(est.p * 100)}% (${Math.round(est.low * 100)}–${Math.round(est.high * 100)}%)` }),
    el("span", { text: "Calibrated model: the expert score plus what audits and outcomes taught it." }),
    ...(est.corrections || []).map((c) => el("span", { class: "muted", text: `${c.logit > 0 ? "▲" : "▼"} ${c.label}` }))));
  return line;
}

function seriesLegend(items) {
  return el("div", { class: "legend" }, items.map(([label, slot]) => el("span", { class: "legend-item" },
    el("i", { class: `swatch cat-${slot}`, "aria-hidden": "true" }), label)));
}

async function loadModel() {
  const out = $("#model-result");
  if (!out.children.length) out.replaceChildren(el("div", { class: "kpi-band skeleton", style: "height:124px" }));
  busy(1);
  try {
    const [status, queue] = await Promise.all([api("/api/model"), api("/api/audit/queue")]);
    renderModel(status, queue);
  } catch (err) {
    out.replaceChildren(el("div", { class: "panel" }, el("p", { text: `Could not load the model page: ${err.message}` })));
  } finally { busy(-1); }
}

function renderModel(st, queue) {
  const g = st.gold;
  const m = st.model;
  const sv = st.survival;
  const pv = st.prevalence;
  $("#model-result").replaceChildren(
    kpiBand(
      kpi("Labels", g.total, { note: `${g.ghost} not genuinely open · ${g.genuine} genuine`, viz: shareBar(g.ghost, g.total),
        help: "From audits and application outcomes." }),
      kpi("Weak-label coverage", pct(st.weak.covered, st.jobs) || "0%", { note: `${st.weak.covered} of ${st.jobs} jobs have a vote`,
        viz: shareBar(st.weak.covered, st.jobs),
        help: "Strong patterns that point to jobs worth auditing." }),
      kpi("Observed closures", sv.events, { unit: `of ${sv.spells}`, note: `${sv.min_events} needed per group`, viz: shareBar(sv.events, sv.spells),
        help: "Jobs the radar saw close." }),
      kpi("Model", m.trained ? m.labels : "—", { unit: m.trained ? "labels" : null,
        note: m.trained ? `Brier ${m.metrics.model.brier} vs expert ${m.metrics.expert.brier}` : `needs ${m.min_labels} labels, ${m.min_per_class} per class`,
        help: "Lower Brier is better. Used only once it beats the expert score." }),
      kpi("Share not genuinely open", pv.estimate != null ? `${Math.round(pv.estimate * 100)}%` : "—", {
        note: pv.estimate != null ? `${Math.round(pv.low * 100)}–${Math.round(pv.high * 100)}% · ${pv.audited} audits` : pv.note,
        help: "Estimated from the audit sample." })),
    auditSection(queue),
    modelSection(st),
    survivalSection(sv),
    lfSection(st.labelling_functions),
  );
}

function auditItem(item, labelMap) {
  const sp = item.posting;
  const p = sp.posting;
  const url = safeUrl(p.url);
  const status = el("span", { class: "small secondary", role: "status" });
  const select = el("select", { name: "label", "aria-label": "What the audit found" },
    el("option", { value: "", text: "What did you find out?", selected: true, disabled: true }),
    Object.entries(labelMap).map(([k, v]) => el("option", { value: k, text: v })));
  const method = el("input", { name: "method", maxlength: 120, placeholder: "How you checked, e.g. e-mail to HR", "aria-label": "How you checked" });
  const job = el("div", { class: "audit-job" }, gradeBadge(sp.score.grade),
    el("div", { class: "flag-text" }, el("span", { class: "flag-title", text: p.title || "Untitled posting" }),
      el("span", { class: "flag-sub", text: [p.company, p.city || p.location, sp.features.live_days != null ? `${sp.features.live_days} days online` : null].filter(Boolean).join(" · ") })),
    url ? el("a", { href: url, target: "_blank", rel: "noopener noreferrer", text: "Open ↗" }) : null);
  hoverable(job, () => postingCard(sp), { delay: 250 });
  const form = el("form", { class: "audit-form" }, select, method, el("button", { class: "btn btn-quiet btn-small", type: "submit", text: "Save" }), status);
  const li = el("li", { class: "audit-item" }, job, form);
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!select.value) { status.textContent = "Choose what the employer said first."; return; }
    try {
      await api("/api/audit", { method: "POST", body: JSON.stringify({ posting_id: item.posting_id, label: select.value,
        method: method.value || null, inclusion_prob: item.inclusion_prob }) });
      status.textContent = "Saved";
      li.classList.add("done");
      setTimeout(loadModel, 700);
    } catch (err) { status.textContent = `Could not save: ${err.message}`; }
  });
  return li;
}

function auditSection(queue) {
  const list = el("ul", { class: "audit-list" });
  const count = el("p", { class: "panel-sub" });
  const render = (q) => {
    list.replaceChildren(...q.items.map((item) => auditItem(item, q.labels)));
    if (!q.items.length) list.append(el("li", { class: "table-empty", text: "No jobs to sample yet. Check a posting, analyse a company or map a city first." }));
    count.textContent = `${q.items.length} jobs to check, sampled across grades.`;
  };
  render(queue);
  const redraw = el("button", { class: "btn btn-quiet btn-small", type: "button", text: "Draw a new sample",
    onclick: async () => render(await api("/api/audit/queue?redraw=true")) });
  return section("Audit queue", "Ask the employer, then record the answer.",
    row([
      el("div", { class: "panel panel-flush" },
        el("div", { class: "panel-head" }, el("div", {}, el("h3", { class: "panel-title", text: "Sampled jobs" }), count), redraw), list),
      panel("What to ask", "In writing, to the named contact or HR.",
        el("blockquote", { class: "script", text: `„${queue.script_de}“` }),
        el("p", { class: "small secondary", text: queue.script_en })),
    ], "g-7-5"));
}

function metricsTable(m) {
  const rows = [["model", "Model"], ["expert", "Expert score"], ["base_rate", "Base rate"]];
  return el("div", { class: "table-wrap" }, el("table", { class: "metrics" },
    el("thead", {}, el("tr", {}, el("th", { text: "Out of fold" }), el("th", { class: "num", text: "Brier ↓" }),
      el("th", { class: "num", text: "Log loss ↓" }), el("th", { class: "num", text: "ROC AUC ↑" }),
      el("th", { class: "num", text: `Precision, top ${Math.round(m.review_budget * 100)}% ↑` }))),
    el("tbody", {}, rows.map(([k, label]) => {
      const r = m.metrics[k];
      return el("tr", {}, el("td", { text: label }), el("td", { class: "num", text: r.brier }), el("td", { class: "num", text: r.log_loss }),
        el("td", { class: "num", text: r.auc ?? "—" }), el("td", { class: "num", text: `${Math.round(r.precision_at_budget * 100)}%` }));
    }))));
}

function modelSection(st) {
  const m = st.model;
  const status = el("span", { class: "small secondary", role: "status" });
  const train = el("button", { class: "btn btn-primary", type: "button", text: m.trained ? "Retrain" : "Train model" });
  train.addEventListener("click", async () => {
    train.disabled = true;
    status.textContent = "Training…";
    try {
      const r = await api("/api/model/train", { method: "POST" });
      status.textContent = r.trained ? "Trained." : r.reason;
      if (r.trained) loadModel();
    } catch (err) { status.textContent = `Training failed: ${err.message}`; } finally { train.disabled = false; }
  });
  const info = m.trained
    ? `Trained ${fmtDate(m.trained_at)} on ${m.labels} labels (${m.ghost} not genuinely open, ${m.genuine} genuine), ${m.folds}-fold cross-validation.`
    : `Needs ${m.min_labels} labels with at least ${m.min_per_class} of each class; ${st.gold.total} recorded so far (${st.gold.audits} audits, ${st.gold.outcomes} outcomes).`;
  const head = panel("Calibrated model", "Starts from the expert score and adjusts only as far as the labels support.",
    el("div", { class: "form-actions" }, el("span", { class: "small secondary", text: info }), el("span", {}, status, " ", train)),
    m.trained ? metricsTable(m) : null);
  if (!m.trained) return section("Model", "Judged on cases it was not trained on.", head);
  const weights = m.names.map((n, i) => ({ name: n, label: m.labels_text[n] || n, beta: m.beta[i], prior: m.prior_mean[i], sd: m.prior_sd[i] }))
    .filter((r) => r.name !== "intercept");
  return section("Model", "Judged on cases it was not trained on.", head, row([
    panel("Calibration", "Predicted against observed. The diagonal is perfect.",
      calibrationChart(m.calibration, m.calibration_expert), seriesLegend([["Model", 1], ["Expert score", 2]])),
    panel("What the labels taught it", "Learned weight against its prior (black tick). Red raises the estimate, blue lowers it.", weightBars(weights)),
  ], "g-5-7"));
}

function survivalSection(sv) {
  const groups = sv.groups || [];
  const body = groups.length
    ? [survivalChart(groups), seriesLegend(groups.slice(0, 3).map((g, i) => [g.group, i + 1])),
      el("div", { class: "table-wrap" }, el("table", {},
        el("thead", {}, el("tr", {}, el("th", { text: "Group" }), el("th", { class: "num", text: "Jobs" }), el("th", { class: "num", text: "Closed" }), el("th", { class: "num", text: "Median days" }))),
        el("tbody", {}, groups.map((g) => el("tr", {}, el("td", { text: g.group }), el("td", { class: "num", text: g.spells }),
          el("td", { class: "num", text: g.events }), el("td", { class: "num", text: g.median_days != null ? Math.round(g.median_days) : "more than observed" }))))))]
    : [el("p", { class: "secondary", text: `No group has ${sv.min_events} closed jobs yet (${sv.events} so far). Until then, ages are compared with Bundesagentur statistics.` })];
  return section("Survival baselines", "How long comparable jobs stay online.",
    el("div", { class: "panel" }, ...body));
}

function lfSection(rows) {
  return section("Labelling functions", "Strong patterns that point to jobs worth auditing.",
    el("div", { class: "panel panel-flush table-wrap" }, el("table", {},
      el("thead", {}, el("tr", {}, el("th", { text: "Pattern" }), el("th", { class: "num", text: "Assumed accuracy" }), el("th", { class: "num", text: "Coverage" }),
        el("th", { class: "num", text: "Votes: not genuine / genuine" }), el("th", { class: "num", text: "Accuracy on labels" }))),
      el("tbody", {}, rows.map((r) => el("tr", {}, el("td", { text: r.label }), el("td", { class: "num", text: `${Math.round(r.prior_accuracy * 100)}%` }),
        el("td", { class: "num", text: `${Math.round(r.coverage * 100)}%` }), el("td", { class: "num", text: `${r.ghost_votes} / ${r.genuine_votes}` }),
        el("td", { class: "num", text: r.accuracy != null ? `${Math.round(r.accuracy * 100)}% (n=${r.checked})` : "no labels yet" })))))));
}

// ------------------------------------------------------------------ method page

$("#method-scale").replaceChildren(gradeScale());
thresholdsPanel().then((form) => $("#method-thresholds").replaceChildren(form)).catch(() => {});
for (const a of $$(".toc a")) {
  a.addEventListener("click", (e) => {
    e.preventDefault();
    document.getElementById(a.getAttribute("href").slice(1))?.scrollIntoView({ behavior: "smooth", block: "start" });
  });
}

// ------------------------------------------------------------------ deep links (#overview, #posting=…, #company=…, #city=…&q=…, #check=<url>)

function openFromHash() {
  const raw = location.hash.slice(1);
  if (VIEWS.includes(raw)) { showTab(raw); return; }
  const hash = new URLSearchParams(raw);
  if (hash.get("posting")) { openPosting(hash.get("posting")); return; }
  if (hash.get("company")) { openCompany(hash.get("company")); return; }
  if (hash.get("city")) { openCity(hash.get("city"), hash.get("q") || ""); return; }
  if (hash.get("check")) {
    showTab("check", { hash: false });
    const form = $("#check-form");
    form.elements.url.value = hash.get("check");
    form.requestSubmit();
    return;
  }
  showTab("overview");
}
window.addEventListener("hashchange", openFromHash);

// ------------------------------------------------------------------ start

(async () => {
  try {
    META = await api("/api/meta");
  } catch (_) { /* the dashboard still works without meta */ }
  sourceToggles();
  updateStation();
  api("/api/watchlist").then((items) => updateWatchCount(items.length)).catch(() => {});
  openFromHash();
})();
