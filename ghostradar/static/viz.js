// Interactive visuals: floating hover windows, grade icons, charts, the radar scope and the lifecycle timeline.
// Colour roles follow the dataviz reference palette: status colours for grades (always with shape + glyph + label),
// one accent hue for magnitude, de-emphasis grey for context, a blue/red diverging pair for score contributions.
// Every chart has a table or list twin, and every mark opens a floating window on hover or keyboard focus.
import { clamp, el, fmtDate, fmtDays, fmtShortDate, hash01, sourceLabel, svgEl } from "./dom.js";

export const GRADES = {
  low: { label: "Low", glyph: "✓", shape: "circle", cls: "g-low" },
  moderate: { label: "Moderate", glyph: "!", shape: "square", cls: "g-moderate" },
  elevated: { label: "Elevated", glyph: "!!", shape: "diamond", cls: "g-elevated" },
  high: { label: "High", glyph: "✕", shape: "triangle", cls: "g-high" },
  unknown: { label: "Not enough data", glyph: "?", shape: "circle", cls: "g-unknown" },
  closed: { label: "No longer online", glyph: "–", shape: "circle", cls: "g-unknown" },
};
export const GRADE_ORDER = ["low", "moderate", "elevated", "high"];
export const GRADE_BANDS = [["low", 0, 25], ["moderate", 25, 45], ["elevated", 45, 65], ["high", 65, 100]];

export const TYPE_LABELS = {
  stale: "Possibly filled or abandoned",
  pool: "Candidate pool",
  pre_decided: "Internal favourite",
  frozen: "Hiring frozen",
  fictitious: "CV collection",
};
const TYPE_HELP = {
  stale: "The role may already be filled or abandoned while the ad keeps running.",
  pool: "Collects candidates for expected demand rather than one open position (agencies, talent pools).",
  pre_decided: "A real vacancy, but advertised for formal reasons while an internal candidate is favoured.",
  frozen: "Hiring at the employer may be on hold (layoffs, insolvency, freeze) while ads stay up.",
  fictitious: "The pattern fits signalling growth or collecting CVs without a role behind it.",
};

// ------------------------------------------------------------------ shapes and badges

function shapeNode(shape, cx, cy, r) {
  if (shape === "circle") return svgEl("circle", { cx, cy, r });
  if (shape === "square") return svgEl("rect", { x: cx - r * 0.9, y: cy - r * 0.9, width: r * 1.8, height: r * 1.8, rx: r * 0.3 });
  if (shape === "diamond") return svgEl("polygon", { points: `${cx},${cy - r * 1.1} ${cx + r * 1.1},${cy} ${cx},${cy + r * 1.1} ${cx - r * 1.1},${cy}` });
  return svgEl("polygon", { points: `${cx},${cy - r * 1.1} ${cx + r * 1.1},${cy + r * 0.9} ${cx - r * 1.1},${cy + r * 0.9}` });
}

export function gradeIcon(grade, size = 18) {
  const g = GRADES[grade] || GRADES.unknown;
  const s = svgEl("svg", { viewBox: "0 0 26 26", width: size, height: size, class: `gicon ${g.cls}`, "aria-hidden": "true" });
  const shape = shapeNode(g.shape, 13, g.shape === "triangle" ? 14 : 13, 10.5);
  shape.setAttribute("class", "shape");
  s.append(shape, svgEl("text", { x: 13, y: g.shape === "triangle" ? 16.5 : 13.5, "font-size": g.glyph.length > 1 ? 10 : 12 }, g.glyph));
  return s;
}

export function gradeBadge(grade, label) {
  const g = GRADES[grade] || GRADES.unknown;
  return el("span", { class: `badge ${g.cls}` }, gradeIcon(grade, 18), label || g.label);
}

/** The brand radar, small; spins while work is running. */
export function radarMark(cls = "progress-mark") {
  const s = svgEl("svg", { viewBox: "0 0 40 40", class: cls, "aria-hidden": "true" });
  s.append(svgEl("rect", { width: 40, height: 40, rx: 11, class: "bm-bg" }),
    svgEl("circle", { cx: 20, cy: 20, r: 14, class: "bm-ring" }), svgEl("circle", { cx: 20, cy: 20, r: 7, class: "bm-ring" }),
    svgEl("path", { d: "M20 20 L20 6 A14 14 0 0 1 32.1 13 Z", class: "bm-sweep" }),
    svgEl("circle", { cx: 27, cy: 13.5, r: 2.4, class: "bm-blip" }));
  return s;
}

// ------------------------------------------------------------------ floating window

const layer = el("div", { class: "floating", role: "tooltip", hidden: true });
document.body.append(layer);
let showTimer = null;

function place(x, y) {
  const pad = 14;
  const w = layer.offsetWidth;
  const h = layer.offsetHeight;
  let left = x + pad;
  let top = y + pad;
  if (left + w > window.innerWidth - 8) left = Math.max(8, x - w - pad);
  if (top + h > window.innerHeight - 8) top = Math.max(8, y - h - pad);
  layer.style.left = `${left}px`;
  layer.style.top = `${top}px`;
}

export function showFloating(content, x, y) {
  layer.replaceChildren(content);
  layer.hidden = false;
  place(x, y);
}

export function hideFloating() {
  clearTimeout(showTimer);
  layer.hidden = true;
}

/** Show `build()` in a floating window while the pointer or keyboard focus is on `target`. */
export function hoverable(target, build, { delay = 90 } = {}) {
  let inside = false;
  const schedule = (x, y) => {
    clearTimeout(showTimer);
    showTimer = setTimeout(() => { if (inside) showFloating(build(), x, y); }, delay);
  };
  target.addEventListener("pointerenter", (e) => { inside = true; schedule(e.clientX, e.clientY); });
  target.addEventListener("pointermove", (e) => {
    inside = true;
    // after a scroll closed the window, moving over the same target opens it again
    if (layer.hidden) schedule(e.clientX, e.clientY);
    else place(e.clientX, e.clientY);
  });
  target.addEventListener("pointerleave", () => { inside = false; hideFloating(); });
  target.addEventListener("focus", () => {
    const r = target.getBoundingClientRect();
    showFloating(build(), r.left + r.width / 2, r.bottom);
  });
  target.addEventListener("blur", hideFloating);
  return target;
}
window.addEventListener("scroll", hideFloating, { passive: true });

/** Small value-first tooltip: the value is the strong element, the label follows. */
export function tip(value, label, extra) {
  return el("div", { class: "tipbox" }, el("strong", { text: value }), label ? el("span", { text: label }) : null,
    extra ? el("span", { class: "muted", text: extra }) : null);
}

// ------------------------------------------------------------------ progress panel

const STEP_ICON = { done: "✓", failed: "✕", skipped: "–", running: "", pending: "" };

/** Live progress of a background task: a determinate bar plus one line per step. */
export function progressPanel(snapshot) {
  const pct = Math.round((snapshot?.fraction || 0) * 100);
  const steps = snapshot?.steps || [];
  return el("div", { class: "progress-panel", role: "status", "aria-live": "polite" },
    el("div", { class: "progress-head" }, radarMark(),
      el("span", { class: "progress-title", text: snapshot?.title || "Working…" }),
      el("span", { class: "progress-meta", text: `${pct}% · ${snapshot?.elapsed ?? 0} s` })),
    el("div", { class: "progress-track", role: "progressbar", "aria-valuemin": 0, "aria-valuemax": 100, "aria-valuenow": pct },
      el("div", { class: "progress-fill", style: `width:${Math.max(3, pct)}%` })),
    steps.length ? el("ul", { class: "progress-steps" }, steps.map((s) => el("li", { class: `step ${s.state}` },
      el("span", { class: "step-icon", "aria-hidden": "true", text: STEP_ICON[s.state] ?? "" }),
      el("span", { class: "step-label", text: s.label }),
      s.detail ? el("span", { class: "step-detail", text: s.detail }) : null))) : null);
}

// ------------------------------------------------------------------ verdict pieces

/** The 0–100 score as a needle over the four grade bands. */
export function scoreMeter(risk, grade) {
  const label = (GRADES[grade] || GRADES.unknown).label;
  const track = el("div", { class: "meter-track" },
    GRADE_BANDS.map(([g, a, b]) => el("div", { class: `meter-band ${GRADES[g].cls}${g === grade ? " current" : ""}`, style: `left:${a}%;width:${b - a}%` })),
    el("div", { class: "meter-needle", style: `left:${clamp(risk, 0, 100)}%` }, el("span", { class: "meter-value", text: `${risk}` })));
  const scale = el("div", { class: "meter-scale", "aria-hidden": "true" },
    GRADE_BANDS.map(([g, a, b]) => el("span", { class: g === grade ? "current" : null, style: `left:${a}%;width:${b - a}%`, text: GRADES[g].label })));
  const wrap = el("div", { class: "meter", role: "img", "aria-label": `Score ${risk} of 100: ${label} ghost-risk. Bands: low below 25, moderate 25 to 44, elevated 45 to 64, high 65 and above.` }, track, scale);
  hoverable(wrap, () => tip(`${risk} of 100`, `${label} ghost-risk`, "Low < 25 · Moderate 25–44 · Elevated 45–64 · High ≥ 65"));
  return wrap;
}

const EFFORT = [["full", "Tailored"], ["standard", "Standard"], ["light", "Short"], ["verify", "Verify first"], ["skip", "Skip"]];

/** Where the suggested application effort sits between "tailored" and "skip". */
export function effortScale(tier) {
  const idx = EFFORT.findIndex(([k]) => k === tier);
  return el("div", { class: "effort", role: "img", "aria-label": `Suggested effort: ${EFFORT[idx]?.[1] || tier}, step ${idx + 1} of 5 from tailored to skip` },
    el("div", { class: "effort-steps" }, EFFORT.map((_, i) => el("span", { class: `effort-step${i === idx ? " current" : ""}` }))),
    el("div", { class: "effort-labels", "aria-hidden": "true" }, EFFORT.map(([, l], i) => el("span", { class: i === idx ? "current" : null, text: l }))));
}

/** Evidence the score could use: seven cells plus a chip per kind; hovering explains each item. */
export function coverageStrip(coverage = []) {
  if (!coverage.length) return null;
  const used = coverage.filter((c) => c.state === "used").length;
  const marks = { used: "✓", partial: "◐", missing: "○", pending: "…" };
  const states = { used: "Used", partial: "Partly used", missing: "Not available yet", pending: "Loading" };
  return el("div", { class: "evidence" },
    el("div", { class: "ev-head" }, el("span", { class: "ev-title", text: "Evidence used" }),
      el("span", { class: "ev-count", text: `${used} of ${coverage.length}` })),
    el("div", { class: "ev-cells", role: "img", "aria-label": `${used} of ${coverage.length} kinds of evidence used` },
      coverage.map((c) => el("span", { class: `ev-cell ${c.state}` }))),
    el("div", { class: "ev-chips" }, coverage.map((c) => hoverable(
      el("span", { class: `cov-chip ${c.state}`, tabindex: 0 }, el("span", { "aria-hidden": "true", text: marks[c.state] }), c.label),
      () => tip(states[c.state], c.label, c.note)))),
    used <= 2 ? el("p", { class: "ev-note", text: "Little evidence so far, so the grade can change." }) : null);
}

/** Days online against the occupation's typical advertising time, with ticks at each multiple. */
export function ageBullet(f) {
  const days = f.live_days;
  const exp = f.baseline?.expected_days;
  if (days == null) return el("p", { class: "secondary", text: "The first publication date is unknown, so the age cannot be compared with the norm." });
  if (!exp) return el("div", { class: "bullet" }, el("div", { class: "bullet-head" }, el("span", { class: "bullet-value", text: String(days) }), el("span", { text: "days online" })),
    el("p", { class: "secondary small", text: "No occupation baseline to compare with." }));
  const ratio = f.excess_ratio ?? days / exp;
  const top = Math.max(4, Math.ceil(Math.min(ratio, 8) + 0.2));
  const pct = (d) => clamp((100 * d) / (exp * top), 0, 100);
  const ticks = Array.from({ length: top }, (_, i) => i + 1);
  const track = el("div", { class: "bullet-track", role: "img", "aria-label": `${days} days online, ${ratio.toFixed(1)} times the typical ${exp} days` },
    el("div", { class: "bullet-norm", style: `width:${pct(exp)}%` }),
    el("div", { class: "bullet-fill", style: `width:${Math.max(1, pct(days))}%` }),
    ticks.map((k) => el("span", { class: `bullet-tick${k === 1 ? " norm" : ""}`, style: `left:${pct(k * exp)}%` })));
  hoverable(track, () => tip(`${days} days online`, `${ratio.toFixed(1)}× the typical ${exp} days`, ratio > top ? `Bar capped at ${top}×` : null));
  const every = top <= 5 ? 1 : Math.ceil(top / 4);
  const labelled = ticks.filter((k) => k === 1 || k === top || (k % every === 0 && top - k >= every / 2 && k > 1 + every / 2));
  const scale = el("div", { class: "bullet-scale", "aria-hidden": "true" }, el("span", { style: "left:0", text: "0" }),
    labelled.map((k) => el("span", { class: k === 1 ? "norm" : null, style: `left:${pct(k * exp)}%`, text: k === 1 ? `1× = ${exp} d` : `${k}×` })));
  return el("div", { class: "bullet" },
    el("div", { class: "bullet-head" }, el("span", { class: "bullet-value", text: String(days) }), el("span", { text: "days online" }),
      el("span", { class: "bullet-ratio", text: `${ratio.toFixed(1)}× typical` })),
    track, scale);
}

/** A count against a norm (applicants per hire, open jobs per plausible opening), with a tick at each multiple. */
export function ratioBullet({ value, norm, unit, normLabel, right, aria }) {
  const ratio = value / Math.max(norm, 0.01);
  const top = Math.max(4, Math.ceil(Math.min(ratio, 8) + 0.2));
  const pct = (v) => clamp((100 * v) / (norm * top), 0, 100);
  const ticks = Array.from({ length: top }, (_, i) => i + 1);
  const every = top <= 5 ? 1 : Math.ceil(top / 4);
  const labelled = ticks.filter((k) => k === 1 || k === top || (k % every === 0 && top - k >= every / 2 && k > 1 + every / 2));
  const normText = norm >= 10 ? Math.round(norm) : Math.round(norm * 10) / 10;
  const track = el("div", { class: "bullet-track", role: "img", "aria-label": aria },
    el("div", { class: "bullet-norm", style: `width:${pct(norm)}%` }),
    el("div", { class: "bullet-fill", style: `width:${Math.max(1, pct(value))}%` }),
    ticks.map((k) => el("span", { class: `bullet-tick${k === 1 ? " norm" : ""}`, style: `left:${pct(k * norm)}%` })));
  hoverable(track, () => tip(`${value} ${unit}`, `${ratio.toFixed(1)}× ${normLabel}`, ratio > top ? `Bar capped at ${top}×` : null));
  const scale = el("div", { class: "bullet-scale", "aria-hidden": "true" }, el("span", { style: "left:0", text: "0" }),
    labelled.map((k) => el("span", { class: k === 1 ? "norm" : null, style: `left:${pct(k * norm)}%`, text: k === 1 ? `1× = ${normText}` : `${k}×` })));
  return el("div", { class: "bullet" },
    el("div", { class: "bullet-head" }, el("span", { class: "bullet-value", text: String(value) }), el("span", { text: unit }),
      el("span", { class: "bullet-ratio", text: right })),
    track, scale);
}

// ------------------------------------------------------------------ tiny visuals for KPI tiles and table cells

export function miniGradeBar(counts) {
  const total = GRADE_ORDER.reduce((s, g) => s + (counts[g] || 0), 0);
  const label = GRADE_ORDER.map((g) => `${GRADES[g].label} ${counts[g] || 0}`).join(", ");
  return el("div", { class: "mini-dist", role: "img", "aria-label": `Grades: ${label}` },
    total ? GRADE_ORDER.filter((g) => counts[g]).map((g) => el("span", { class: GRADES[g].cls, style: `flex-grow:${counts[g]}` })) : null);
}

export function miniBullet(ratio, max = 4) {
  return el("div", { class: "mini-bullet", role: "img", "aria-label": `${ratio.toFixed(1)} times the typical time` },
    el("span", { class: "fill", style: `width:${clamp((ratio / max) * 100, 2, 100)}%` }),
    el("span", { class: "tick", style: `left:${100 / max}%` }));
}

export function miniCells(value, total = 7) {
  const on = Math.round(value);
  return el("div", { class: "mini-cells", role: "img", "aria-label": `${value} of ${total}` },
    Array.from({ length: total }, (_, i) => el("span", { class: i < on ? "on" : null })));
}

/** Days online plus a tiny age-vs-norm bar (table cells). */
export function ageMini(f) {
  if (f.live_days == null) return el("span", { class: "muted", text: "—" });
  return el("span", { class: "age-cell" }, el("span", { class: "mono", text: `${f.live_days} d` }),
    f.excess_ratio != null ? miniBullet(f.excess_ratio) : null);
}

// ------------------------------------------------------------------ posting preview card

function ageMeter(f) {
  const ratio = f.excess_ratio;
  const expected = f.baseline?.expected_days;
  const pct = clamp((ratio / 4) * 100, 0, 100);
  return el("div", { class: "agemeter" },
    el("div", { class: "agemeter-track", "aria-hidden": "true" },
      el("div", { class: "agemeter-fill", style: `width:${pct}%` }),
      el("div", { class: "agemeter-tick", style: "left:25%" })),
    el("div", { class: "agemeter-text" },
      el("strong", { text: `${f.live_days} days online` }),
      ` · typical ≈ ${expected} days (${ratio.toFixed(1)}×)`));
}

/** One chip per source (grouped, e.g. "Bundesagentur ×2"); hovering lists every copy with its dates. */
export function copyChips(copies = []) {
  const wrap = el("span", { class: "copies" });
  const groups = new Map();
  for (const c of copies) {
    const key = `${c.source}|${c.channel}|${c.status}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(c);
  }
  for (const group of groups.values()) {
    const c = group[0];
    const chip = el("span", {
      class: `copy-chip${c.channel === "employer" ? " employer" : ""}${c.status === "removed" ? " removed" : ""}`,
      tabindex: 0,
    }, sourceLabel(c.source), group.length > 1 ? ` ×${group.length}` : null);
    hoverable(chip, () => el("div", { class: "tipbox" },
      el("strong", { text: c.status === "removed" ? "Removed" : `Still online${group.length > 1 ? ` (${group.length} copies)` : ""}` }),
      el("span", { text: `${sourceLabel(c.source)}${c.channel === "employer" ? " (employer's own channel)" : ""}` }),
      ...group.map((g) => el("span", { class: "muted", text: `posted ${fmtDate(g.posted_at)} · first seen ${fmtDate(g.first_seen)}`
        + (g.status === "removed" ? ` · removed ${fmtDate(g.removed_at)}` : ` · last seen ${fmtDate(g.last_seen)}`) }))));
    wrap.append(chip);
  }
  return wrap;
}

export function postingCard(sp) {
  const { score: s, posting: p, features: f } = sp;
  const raising = s.reasons.filter((r) => r.points > 0).slice(0, 3);
  const used = (s.coverage || []).filter((c) => c.state === "used");
  return el("div", { class: "pcard" },
    el("div", { class: "pcard-head" }, gradeBadge(s.grade, s.grade_label),
      s.grade === "closed" ? null : el("span", { class: "pcard-score", text: `score ${s.risk}/100` })),
    el("div", { class: "pcard-title", text: p.title || "Untitled posting" }),
    el("div", { class: "pcard-sub", text: [p.company, p.city || p.location].filter(Boolean).join(" · ") }),
    f.excess_ratio != null && f.live_days != null ? ageMeter(f) : null,
    raising.length
      ? el("ul", { class: "pcard-list" }, raising.map((r) => el("li", {}, el("span", { class: "pts", text: `+${r.points}` }), ` ${r.label}`)))
      : el("div", { class: "pcard-line muted", text: "No raising signals." }),
    sp.copies && sp.copies.length ? el("div", { class: "pcard-line" }, el("span", { class: "muted", text: "Seen on " }), copyChips(sp.copies)) : null,
    s.competition && s.competition.level !== "unknown" ? el("div", { class: "pcard-line", text: s.competition.text }) : null,
    s.coverage && s.coverage.length
      ? el("div", { class: "pcard-line muted", text: `Evidence used: ${used.length} of ${s.coverage.length}${used.length ? ` (${used.map((c) => c.label.toLowerCase()).join(", ")})` : ""}` })
      : null,
    el("div", { class: "pcard-foot", text: "Click for the full analysis" }));
}

// ------------------------------------------------------------------ grade distribution (stacked bar)

export function gradeDistribution(items, { active, onToggle, counts: given } = {}) {
  const counts = Object.fromEntries(GRADE_ORDER.map((g) => [g, 0]));
  if (given) for (const g of GRADE_ORDER) counts[g] = given[g] || 0;
  else for (const item of items) if (item.score.grade in counts) counts[item.score.grade] += 1;
  const total = GRADE_ORDER.reduce((s, g) => s + counts[g], 0);
  const wrap = el("div", { class: "dist" });
  if (!total) return wrap;
  const summary = GRADE_ORDER.map((g) => `${GRADES[g].label} ${counts[g]}`).join(", ");
  const bar = el("div", { class: "dist-bar", role: "img", "aria-label": `Ghost-risk grades: ${summary}` });
  for (const g of GRADE_ORDER) {
    if (!counts[g]) continue;
    const pct = Math.round((100 * counts[g]) / total);
    const seg = el("div", {
      class: `dist-seg ${GRADES[g].cls}`, style: `flex-grow:${counts[g]}`, tabindex: 0,
      "aria-label": `${GRADES[g].label}: ${counts[g]} postings (${pct}%)`,
    });
    seg.dataset.count = String(counts[g]);
    hoverable(seg, () => tip(`${counts[g]} job${counts[g] === 1 ? "" : "s"}`, `${GRADES[g].label} ghost-risk · ${pct}% of this view`));
    if (onToggle) seg.addEventListener("click", () => onToggle(g));
    bar.append(seg);
  }
  const legend = el("div", { class: "legend" });
  for (const g of GRADE_ORDER) {
    const pressed = !active || active.has(g);
    const pct = total ? Math.round((100 * counts[g]) / total) : 0;
    legend.append(el("button", {
      type: "button", "aria-pressed": String(pressed), title: onToggle ? "Show or hide this grade" : null,
      onclick: onToggle ? () => onToggle(g) : null, disabled: onToggle ? null : true,
    }, gradeIcon(g, 16), GRADES[g].label, el("span", { class: "count", text: `${counts[g]} · ${pct}%` })));
  }
  wrap.append(bar, legend);
  requestAnimationFrame(() => {
    for (const seg of bar.children) if (seg.offsetWidth >= 34) seg.textContent = seg.dataset.count;
  });
  return wrap;
}

// ------------------------------------------------------------------ ghost-type bars

export function typeBars(types) {
  const rows = [...types].sort((a, b) => b.score - a.score).map((t) => {
    const pct = clamp(t.score, 0, 1) * 100;
    const row = el("div", { class: "bar-row", tabindex: 0 },
      el("div", { class: "name", text: t.label }),
      el("div", { class: "val", text: t.score.toFixed(2) }),
      el("div", { class: "bar-track", role: "img", "aria-label": `${t.label}: indicator strength ${t.score.toFixed(2)} of 1` },
        pct > 0 ? el("div", { class: "bar-fill", style: `width:${pct}%` }) : null),
      t.score > 0 ? el("div", { class: "why", text: t.explanation }) : null);
    hoverable(row, () => tip(`${t.score.toFixed(2)} of 1`, t.label, TYPE_HELP[t.key]));
    return row;
  });
  return el("div", { class: "bars" }, rows);
}

// ------------------------------------------------------------------ responsive chart shell

/** Redraws `draw(width, visible)` whenever the container width changes. */
function responsive(draw, minWidth = 320) {
  const wrap = el("div", { class: "chart" });
  let last = 0;
  const render = () => {
    const measured = Math.floor(wrap.clientWidth);
    const width = Math.max(minWidth, measured || 720);
    if (width === last) return;
    last = width;
    wrap.replaceChildren(draw(width, measured > 0));
  };
  wrap.append(draw(720, false));
  const ro = new ResizeObserver(() => requestAnimationFrame(render));
  ro.observe(wrap);
  return wrap;
}

function niceStep(max, count = 3) {
  const raw = Math.max(1, max) / count;
  const pow = 10 ** Math.floor(Math.log10(raw));
  const unit = [1, 2, 2.5, 5, 10].find((m) => m * pow >= raw) || 10;
  return unit * pow;
}

// ------------------------------------------------------------------ the radar scope

export const SECTORS = ["Employer sites", "LinkedIn", "Bundesagentur", "Other boards"];

export function sectorOf(p) {
  if (p.channel === "employer" && !["manual", "page"].includes(p.source)) return "Employer sites";
  if (p.source === "linkedin") return "LinkedIn";
  if (p.source === "ba") return "Bundesagentur";
  return "Other boards";
}

/**
 * Every job as a blip. Distance from the centre = time online ÷ typical advertising time for the occupation
 * (square-root scale, rings at 1×–4×, an outer band for 4× and more); sector = where the job was found (width
 * proportional to its jobs, labels on the bezel); colour + shape + glyph = ghost-risk grade. The range labels
 * sit in a clear lane at twelve o'clock. A single sweep runs once when the scope first appears.
 */
let scopeSerial = 0;
export function radarScope(jobs, { onSelect, onHover } = {}) {
  const usable = jobs.filter((sp) => sp.features.excess_ratio != null && GRADE_ORDER.includes(sp.score.grade));
  const wrap = el("div", { class: "scope-wrap" });
  if (!usable.length) {
    wrap.append(el("p", { class: "scope-empty", text: "No jobs with an occupation baseline yet. Check a posting or map a city to fill the radar." }));
    return wrap;
  }
  const counts = new Map(SECTORS.map((s) => [s, 0]));
  for (const sp of usable) counts.set(sectorOf(sp.posting), counts.get(sectorOf(sp.posting)) + 1);
  const present = SECTORS.filter((s) => counts.get(s));
  const LANE = 18; // degrees kept free at twelve o'clock for the range labels
  const span = 360 - LANE;
  const minWidth = present.length > 1 ? 46 : span;
  let widths = present.map((s) => Math.max(minWidth, (span * counts.get(s)) / usable.length));
  const k = span / widths.reduce((a, b) => a + b, 0);
  widths = widths.map((w) => w * k);
  const starts = [];
  widths.reduce((acc, w) => { starts.push(acc); return acc + w; }, LANE / 2);
  const order = { low: 0, moderate: 1, elevated: 2, high: 3 };
  const sorted = [...usable].sort((a, b) => order[a.score.grade] - order[b.score.grade]);
  const beyond2 = usable.filter((sp) => sp.features.excess_ratio >= 2).length;
  const id = `scope${(scopeSerial += 1)}`;
  let animated = false;

  const chart = responsive((width, visible) => {
    const height = Math.round(Math.min(width, 580));
    const narrow = width < 420;
    const cx = width / 2;
    const cy = height / 2;
    const R = Math.min(width, height) / 2 - (narrow ? 24 : 30);
    const R4 = R * 0.86; // 4× ring; beyond it, the band for 4× and more
    const rad = (ratio) => (ratio >= 4 ? R4 : R4 * Math.sqrt(Math.max(ratio, 0) / 4));
    const polar = (deg, r) => [cx + r * Math.sin((deg * Math.PI) / 180), cy - r * Math.cos((deg * Math.PI) / 180)];
    const arc = (r, a1, a2, sweep) => {
      const [x1, y1] = polar(a1, r);
      const [x2, y2] = polar(a2, r);
      return `M${x1},${y1} A${r},${r} 0 0 ${sweep} ${x2},${y2}`;
    };
    const run = visible && !animated && !matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (visible) animated = true;
    const svg = svgEl("svg", {
      viewBox: `0 0 ${width} ${height}`, width, height, class: `scope${run ? " run" : ""}${narrow ? " narrow" : ""}`, role: "img",
      "aria-label": `Radar of ${usable.length} jobs. Distance from the centre shows time online compared with the typical time for the occupation; ${beyond2} jobs are online at least twice as long as typical. The table below lists the jobs.`,
    });
    const defs = svgEl("defs");
    const grad = svgEl("linearGradient", { id: `${id}-sweep`, gradientUnits: "userSpaceOnUse" });
    const [tx, ty] = polar(-55, R);
    grad.setAttribute("x1", tx); grad.setAttribute("y1", ty); grad.setAttribute("x2", cx); grad.setAttribute("y2", cy - R);
    grad.append(svgEl("stop", { offset: "0", style: "stop-color:var(--scope-sweep);stop-opacity:0" }),
      svgEl("stop", { offset: "1", style: "stop-color:var(--scope-sweep);stop-opacity:0.45" }));
    defs.append(grad);
    svg.append(defs);
    // within the typical time, the band for 4× and more, then the rings
    svg.append(svgEl("circle", { cx, cy, r: (R + R4) / 2, class: "band", "stroke-width": R - R4 }));
    svg.append(svgEl("circle", { cx, cy, r: rad(1), class: "zone" }));
    for (const r of [1, 2, 3, 4]) svg.append(svgEl("circle", { cx, cy, r: rad(r), class: `ring${r === 1 ? " norm" : ""}` }));
    svg.append(svgEl("circle", { cx, cy, r: R, class: "ring edge" }));
    // sector spokes, and each sector's name on the bezel (read left to right, top and bottom)
    present.forEach((s, i) => {
      for (const a of i === present.length - 1 ? [starts[i], starts[i] + widths[i]] : [starts[i]]) {
        const [x2, y2] = polar(a, R);
        svg.append(svgEl("line", { x1: cx, y1: cy, x2, y2, class: "spoke" }));
      }
      const mid = starts[i] + widths[i] / 2;
      const top = Math.cos((mid * Math.PI) / 180) >= 0;
      const pathId = `${id}-s${i}`;
      defs.append(svgEl("path", { id: pathId, d: top ? arc(R + 9, mid - 80, mid + 80, 1) : arc(R + 19, mid + 80, mid - 80, 0) }));
      const label = svgEl("text", { class: "sector-label" });
      const onPath = svgEl("textPath", { href: `#${pathId}`, startOffset: "50%", "text-anchor": "middle" });
      onPath.append(document.createTextNode(s), svgEl("tspan", { class: "sector-count", dx: 6 }, String(counts.get(s))));
      label.append(onPath);
      svg.append(label);
    });
    // range labels in the clear lane at twelve o'clock
    for (const r of [1, 2, 3]) {
      svg.append(svgEl("text", { x: cx, y: cy - rad(r) + 3.5, class: "ring-label", "text-anchor": "middle" }, `${r}×`));
    }
    svg.append(svgEl("text", { x: cx, y: cy - (R + R4) / 2 + 3.5, class: "ring-label", "text-anchor": "middle" }, "4×+"));
    svg.append(svgEl("circle", { cx, cy, r: 2.5, class: "centre" }));
    // one sweep
    const [sx, sy] = polar(-55, R);
    const sweep = svgEl("g", { class: "sweep", style: `transform-origin:${cx}px ${cy}px` });
    sweep.append(svgEl("path", { d: `M${cx},${cy} L${sx},${sy} A${R},${R} 0 0 1 ${cx},${cy - R} Z`, fill: `url(#${id}-sweep)` }),
      svgEl("line", { x1: cx, y1: cy, x2: cx, y2: cy - R, class: "sweep-line" }));
    svg.append(sweep);
    // blips: jobs at 4× and more spread across the outer band
    for (const sp of sorted) {
      const i = present.indexOf(sectorOf(sp.posting));
      const pad = Math.min(4, widths[i] * 0.06);
      const deg = starts[i] + pad + hash01(`${sp.posting_id}:a`) * (widths[i] - 2 * pad);
      const ratio = sp.features.excess_ratio;
      const jitter = hash01(`${sp.posting_id}:r`);
      const r = ratio >= 4 ? R4 + (R - R4) * (0.22 + 0.56 * jitter) : clamp(rad(ratio) + (jitter - 0.5) * 4, 5, R4 - 2);
      const [x, y] = polar(deg, r);
      const g = GRADES[sp.score.grade];
      const dot = svgEl("g", { class: `dot ${g.cls}`, "data-pid": sp.posting_id, style: `--d:${((deg / 360) * 2.4).toFixed(2)}s` });
      dot.append(svgEl("circle", { cx: x, cy: y, r: 10, class: "hit" }));
      const shape = shapeNode(g.shape, x, y, narrow ? 3.8 : 4.4);
      shape.setAttribute("class", "shape");
      dot.append(shape);
      hoverable(dot, () => postingCard(sp), { delay: 30 });
      dot.addEventListener("pointerenter", () => onHover?.(sp, true));
      dot.addEventListener("pointerleave", () => onHover?.(sp, false));
      if (onSelect) dot.addEventListener("click", () => onSelect(sp));
      svg.append(dot);
    }
    return svg;
  }, 300);

  const legend = el("div", { class: "scope-legend" }, GRADE_ORDER.map((g) => el("span", {}, gradeIcon(g, 15), GRADES[g].label)));
  const skipped = jobs.length - usable.length;
  const caption = el("p", { class: "scope-caption", text:
    "Distance from the centre: time online ÷ the Bundesagentur's typical advertising time for the occupation "
    + "(square-root scale; the dashed ring is 1×, as long as typical). The outer band holds jobs at 4× and more. "
    + "Sectors: where the job was found."
    + (skipped ? ` ${skipped} job${skipped === 1 ? "" : "s"} without an occupation baseline or grade are not plotted.` : "") });
  const top = [...usable].sort((a, b) => b.features.excess_ratio - a.features.excess_ratio).slice(0, 40);
  const twin = el("details", { class: "twin" }, el("summary", { text: "Show as table" }),
    el("div", { class: "table-wrap" }, el("table", {},
      el("thead", {}, el("tr", {}, el("th", { text: "Grade" }), el("th", { text: "Job" }), el("th", { text: "Found on" }), el("th", { class: "num", text: "× typical" }), el("th", { class: "num", text: "Days" }))),
      el("tbody", {}, top.map((sp) => el("tr", {},
        el("td", { text: GRADES[sp.score.grade].label }),
        el("td", { text: [sp.posting.title, sp.posting.company].filter(Boolean).join(" · ") }),
        el("td", { text: sectorOf(sp.posting) }),
        el("td", { class: "num", text: sp.features.excess_ratio.toFixed(1) }),
        el("td", { class: "num", text: sp.features.live_days ?? "—" })))))));
  wrap.append(chart, legend, caption, twin);
  return wrap;
}

// ------------------------------------------------------------------ age vs. norm strip chart

/** One dot per posting: time online divided by the occupation's typical advertising time, by grade lane. */
export function ageStrip(items, { onSelect, onHover } = {}) {
  const usable = items.filter((sp) => sp.features.excess_ratio != null && GRADE_ORDER.includes(sp.score.grade));
  if (!usable.length) return el("p", { class: "secondary", text: "No postings with an occupation baseline to plot." });
  const lanes = ["high", "elevated", "moderate", "low"];
  const MAX = 5;
  return responsive((width) => {
    const left = 92;
    const right = 16;
    const top = 22;
    const laneH = 48;
    const plotH = lanes.length * laneH;
    const height = top + plotH + 44;
    const x = (r) => left + (Math.min(r, MAX) / MAX) * (width - left - right);
    const svg = svgEl("svg", {
      viewBox: `0 0 ${width} ${height}`, width, height, class: "strip", role: "img",
      "aria-label": `Time online compared with the typical time for each occupation, ${usable.length} postings. The table below lists every posting.`,
    });
    svg.append(svgEl("rect", { x: x(3), y: top, width: x(MAX) - x(3), height: plotH, class: "zone" }));
    svg.append(svgEl("text", { x: x(3) + 6, y: top - 6, class: "zone-label" }, "more than 3× typical"));
    lanes.forEach((g, i) => {
      const y0 = top + i * laneH;
      svg.append(svgEl("line", { x1: left, x2: width - right, y1: y0 + laneH, y2: y0 + laneH, class: "lane" }));
      svg.append(svgEl("text", { x: left - 10, y: y0 + laneH / 2 + 4, class: "lane-label", "text-anchor": "end" }, GRADES[g].label));
    });
    for (const t of [0, 1, 2, 3, 4, 5]) {
      svg.append(svgEl("line", { x1: x(t), x2: x(t), y1: top, y2: top + plotH, class: t === 1 ? "ref" : "grid" }));
      svg.append(svgEl("text", { x: x(t), y: top + plotH + 16, class: "tick", "text-anchor": "middle" }, t === 0 ? "0" : t === MAX ? "5×+" : `${t}×`));
    }
    svg.append(svgEl("text", { x: x(1) + 4, y: top - 6, class: "ref-label" }, "typical"));
    svg.append(svgEl("text", { x: left, y: height - 6, class: "axis-title" },
      "Time online ÷ usual time for the occupation"));
    for (const sp of usable) {
      const lane = lanes.indexOf(sp.score.grade);
      const g = GRADES[sp.score.grade];
      const cx = x(sp.features.excess_ratio);
      const cy = top + lane * laneH + laneH / 2 + (hash01(`${sp.posting_id}:${sp.posting.source_id}`) - 0.5) * (laneH - 20);
      const dot = svgEl("g", { class: `dot ${g.cls}`, "data-pid": sp.posting_id });
      dot.append(svgEl("circle", { cx, cy, r: 12, class: "hit" }));
      const shape = shapeNode(g.shape, cx, cy, 5.5);
      shape.setAttribute("class", "shape");
      dot.append(shape);
      hoverable(dot, () => postingCard(sp), { delay: 40 });
      dot.addEventListener("pointerenter", () => onHover?.(sp, true));
      dot.addEventListener("pointerleave", () => onHover?.(sp, false));
      if (onSelect) dot.addEventListener("click", () => { onSelect(sp); });
      svg.append(dot);
    }
    return svg;
  });
}

// ------------------------------------------------------------------ column chart (counts over months)

/** Single-hue columns anchored to the baseline; `muted` keys (e.g. "earlier") are drawn in de-emphasis grey. */
export function columnChart(rows, { unit = "jobs", height = 210, muted = new Set(), ariaLabel } = {}) {
  if (!rows.length) return el("p", { class: "secondary", text: "Nothing to show yet." });
  const max = Math.max(...rows.map((r) => r.value)) || 1;
  const step = niceStep(max, 3);
  const top = Math.ceil(max / step) * step;
  return responsive((width) => {
    const left = 36;
    const right = 6;
    const padTop = 12;
    const bottom = 26;
    const plotW = width - left - right;
    const plotH = height - padTop - bottom;
    const gap = rows.length > 24 ? 2 : 4;
    const bw = Math.max(3, (plotW - gap * (rows.length - 1)) / rows.length);
    const y = (v) => padTop + plotH - (v / top) * plotH;
    const svg = svgEl("svg", { viewBox: `0 0 ${width} ${height}`, width, height, class: "cols", role: "img",
      "aria-label": ariaLabel || `${rows.length} columns: ${rows.map((r) => `${r.label} ${r.value}`).join(", ")}` });
    for (let v = 0; v <= top; v += step) {
      svg.append(svgEl("line", { x1: left, x2: width - right, y1: y(v), y2: y(v), class: v === 0 ? "baseline" : "grid" }));
      svg.append(svgEl("text", { x: left - 6, y: y(v) + 3.5, class: "tick", "text-anchor": "end" }, String(v)));
    }
    const every = Math.max(1, Math.ceil((rows.length * 46) / plotW));
    rows.forEach((r, i) => {
      const x = left + i * (bw + gap);
      const h = Math.max(0, y(0) - y(r.value));
      const base = y(0);
      const rr = Math.min(4, bw / 2, h);
      const hit = svgEl("rect", { x: x - gap / 2, y: padTop, width: bw + gap, height: plotH, class: "hit col-hit" });
      hoverable(hit, () => tip(`${r.value} ${unit}`, r.label, r.note));
      svg.append(hit);
      if (h > 0) {
        svg.append(svgEl("path", {
          class: `col${muted.has(r.key) ? " muted-col" : ""}`,
          d: `M${x},${base} L${x},${base - h + rr} Q${x},${base - h} ${x + rr},${base - h} L${x + bw - rr},${base - h} Q${x + bw},${base - h} ${x + bw},${base - h + rr} L${x + bw},${base} Z`,
        }));
      }
      if (i % every === 0 || i === rows.length - 1) {
        svg.append(svgEl("text", { x: x + bw / 2, y: height - 8, class: "col-label", "text-anchor": "middle" }, r.short || r.label));
      }
    });
    return svg;
  }, 280);
}

/** Months of first publication: the last `months` calendar months plus one grey "earlier" column. */
export function publicationMonths(counts, { months = 12, now = new Date() } = {}) {
  const keys = [];
  const d = new Date(now.getFullYear(), now.getMonth(), 1);
  for (let i = months - 1; i >= 0; i -= 1) {
    const m = new Date(d.getFullYear(), d.getMonth() - i, 1);
    keys.push(`${m.getFullYear()}-${String(m.getMonth() + 1).padStart(2, "0")}`);
  }
  const earlier = Object.entries(counts).filter(([k]) => k < keys[0]).reduce((s, [, v]) => s + v, 0);
  const rows = [];
  if (earlier) rows.push({ key: "earlier", label: `Before ${fmtMonth(keys[0])}`, short: "earlier", value: earlier, note: "Published more than a year ago" });
  for (const k of keys) {
    rows.push({ key: k, label: fmtMonth(k), short: fmtMonth(k, true), value: counts[k] || 0 });
  }
  return columnChart(rows, { unit: "jobs first published", muted: new Set(["earlier"]),
    ariaLabel: `Jobs by month of first publication: ${rows.map((r) => `${r.label} ${r.value}`).join(", ")}` });
}

function fmtMonth(key, short = false) {
  const [y, m] = key.split("-").map(Number);
  const d = new Date(y, m - 1, 1);
  return short
    ? d.toLocaleDateString("en-GB", { month: "short" }) + (m === 1 ? ` ${String(y).slice(2)}` : "")
    : d.toLocaleDateString("en-GB", { month: "long", year: "numeric" });
}

// ------------------------------------------------------------------ horizontal bars

/** Single-series bars (one hue); `emphasis` keys are drawn in the accent, the rest in de-emphasis grey. */
export function barList(rows, { emphasis = null, unit = "postings", onSelect, stacked = false } = {}) {
  if (!rows.length) return el("p", { class: "secondary", text: "Nothing to show." });
  const max = Math.max(...rows.map((r) => r.value)) || 1;
  return el("div", { class: `hbars${stacked ? " stacked" : ""}` }, rows.map((r) => {
    const accent = !emphasis || emphasis.has(r.key);
    const row = el("div", { class: `hbar-row${onSelect ? " clickable" : ""}`, tabindex: 0 },
      el("div", { class: "hbar-label", title: r.label, text: r.label }),
      el("div", { class: "hbar-bar" },
        el("div", { class: `hbar-fill ${accent ? "accent" : "muted-fill"}`, style: `width:${Math.max(2, (100 * r.value) / max)}%` }),
        el("span", { class: "hbar-value", text: String(r.value) })));
    hoverable(row, () => tip(`${r.value} ${unit}`, r.label, r.note));
    if (onSelect) {
      row.addEventListener("click", () => onSelect(r));
      row.addEventListener("keydown", (e) => { if (e.key === "Enter") onSelect(r); });
    }
    return row;
  }));
}

/** Employers (or cities) by open jobs, each bar split by ghost-risk grade (status colours + legend). */
export function employerBars(rows, { onSelect, actionLabel = "Analyse" } = {}) {
  if (!rows.length) return el("p", { class: "secondary", text: "Nothing to show." });
  const max = Math.max(...rows.map((r) => r.count)) || 1;
  const list = el("div", { class: "hbars" }, rows.map((r) => {
    const name = r.company || r.name;
    const stack = el("div", { class: "hbar-stack", style: `width:${Math.max(3, (100 * r.count) / max)}%` });
    for (const g of GRADE_ORDER) {
      const n = (r.grades || {})[g] || 0;
      if (!n) continue;
      const seg = el("div", { class: `hbar-seg ${GRADES[g].cls}`, style: `flex-grow:${n}`, tabindex: 0,
        "aria-label": `${name}: ${n} ${GRADES[g].label}` });
      hoverable(seg, () => tip(`${n} job${n === 1 ? "" : "s"}`, `${GRADES[g].label} ghost-risk`, name));
      stack.append(seg);
    }
    const label = el("button", { class: "hbar-label as-link", type: "button", title: `${actionLabel} ${name}`,
      onclick: () => onSelect?.(name) }, name, r.agency ? el("span", { class: "muted", text: " · agency" }) : null);
    return el("div", { class: "hbar-row" }, label,
      el("div", { class: "hbar-bar" }, stack, el("span", { class: "hbar-value", text: String(r.count) })));
  }));
  const legend = el("div", { class: "legend" }, GRADE_ORDER.map((g) => el("span", { class: "legend-item" }, gradeIcon(g, 14), GRADES[g].label)));
  return el("div", { class: "dist" }, list, legend);
}

// ------------------------------------------------------------------ model page charts

/** Kaplan–Meier step curves for up to three groups: share of jobs still online against days since publication. */
export function survivalChart(groups) {
  const series = groups.filter((g) => g.curve?.length).slice(0, 3);
  if (!series.length) return el("p", { class: "secondary", text: "No survival curves yet." });
  const maxT = Math.max(30, ...series.flatMap((g) => g.curve.map(([t]) => t)));
  const step = niceStep(maxT, 5);
  const top = Math.ceil(maxT / step) * step;
  return responsive((width) => {
    const left = 46;
    const right = width < 560 ? 16 : 150;
    const padTop = 14;
    const bottom = 40;
    const height = 280;
    const x = (t) => left + (t / top) * (width - left - right);
    const y = (s) => padTop + (1 - s) * (height - padTop - bottom);
    const svg = svgEl("svg", { viewBox: `0 0 ${width} ${height}`, width, height, class: "km-chart", role: "img",
      "aria-label": `Share of jobs still online by days since publication, for ${series.map((g) => g.group).join("; ")}. The table below lists the medians.` });
    for (const s of [0, 0.25, 0.5, 0.75, 1]) {
      svg.append(svgEl("line", { x1: left, x2: width - right, y1: y(s), y2: y(s), class: s === 0.5 ? "ref" : s === 0 ? "baseline" : "grid" }));
      svg.append(svgEl("text", { x: left - 6, y: y(s) + 3.5, class: "tick", "text-anchor": "end" }, `${s * 100}%`));
    }
    for (let t = 0; t <= top; t += step) {
      svg.append(svgEl("text", { x: x(t), y: height - 22, class: "tick", "text-anchor": "middle" }, String(t)));
    }
    svg.append(svgEl("text", { x: left, y: height - 4, class: "axis-title" }, "Days since first publication"));
    series.forEach((g, i) => {
      let d = `M${x(0)},${y(1)}`;
      let prev = 1;
      for (const [t, s] of g.curve) {
        d += ` H${x(t)} V${y(s)}`;
        prev = s;
      }
      svg.append(svgEl("path", { d, class: `km-line cat-${i + 1}` }));
      const [lastT] = g.curve[g.curve.length - 1];
      if (right > 40) {
        svg.append(svgEl("text", { x: x(lastT) + 6, y: y(prev) + 4, class: "km-label" }, g.group.length > 22 ? `${g.group.slice(0, 21)}…` : g.group));
      }
      for (const [t, s] of g.curve.filter((_, k) => k % Math.max(1, Math.floor(g.curve.length / 30)) === 0)) {
        const hit = svgEl("circle", { cx: x(t), cy: y(s), r: 9, class: "hit" });
        hoverable(hit, () => tip(`${Math.round(s * 100)}% still online`, `after ${Math.round(t)} days`, `${g.group} · ${g.events} closed of ${g.spells}`));
        svg.append(hit);
      }
    });
    return svg;
  }, 320);
}

/** Reliability diagram: predicted against observed share per bin, for the model and for the expert score. */
export function calibrationChart(model, expert) {
  const sets = [["Model", model, 1], ["Expert score", expert, 2]].filter(([, pts]) => pts && pts.length);
  if (!sets.length) return el("p", { class: "secondary", text: "No calibration data yet." });
  return responsive((width) => {
    const height = 270;
    const left = 46;
    const bottom = 40;
    const padTop = 12;
    const side = Math.min(width - left - 16, height - padTop - bottom);
    const x = (v) => left + v * side;
    const y = (v) => padTop + (1 - v) * side;
    const svg = svgEl("svg", { viewBox: `0 0 ${width} ${height}`, width, height, class: "calib-chart", role: "img",
      "aria-label": "Predicted against observed share of postings that were not genuinely open, per bin. The diagonal is perfect calibration." });
    for (const v of [0, 0.25, 0.5, 0.75, 1]) {
      svg.append(svgEl("line", { x1: x(0), x2: x(1), y1: y(v), y2: y(v), class: v === 0 ? "baseline" : "grid" }));
      svg.append(svgEl("text", { x: left - 6, y: y(v) + 3.5, class: "tick", "text-anchor": "end" }, `${v * 100}%`));
      svg.append(svgEl("text", { x: x(v), y: y(0) + 16, class: "tick", "text-anchor": "middle" }, `${v * 100}%`));
    }
    svg.append(svgEl("line", { x1: x(0), y1: y(0), x2: x(1), y2: y(1), class: "ref" }));
    svg.append(svgEl("text", { x: left, y: height - 4, class: "axis-title" }, "Predicted (x) against observed (y)"));
    for (const [name, pts, slot] of sets) {
      svg.append(svgEl("path", { d: pts.map((b, k) => `${k ? "L" : "M"}${x(b.predicted)},${y(b.observed)}`).join(" "), class: `calib-line cat-${slot}` }));
      for (const b of pts) {
        const r = Math.min(9, 3.5 + Math.sqrt(b.n));
        svg.append(svgEl("circle", { cx: x(b.predicted), cy: y(b.observed), r, class: `calib-dot cat-${slot}` }));
        const hit = svgEl("circle", { cx: x(b.predicted), cy: y(b.observed), r: Math.max(r, 12), class: "hit" });
        hoverable(hit, () => tip(`${Math.round(b.observed * 100)}% observed`, `${name}: predicted ${Math.round(b.predicted * 100)}%`, `${b.n} labelled postings`));
        svg.append(hit);
      }
    }
    return svg;
  }, 300);
}

/** Learned weights next to their prior: bars from zero (red raises, blue lowers the estimate), a tick at the prior. */
export function weightBars(rows) {
  const max = Math.max(0.5, ...rows.flatMap((r) => [Math.abs(r.beta), Math.abs(r.prior)]));
  const pct = (v) => 50 + (v / max) * 50;
  return el("ul", { class: "reasons weights" }, rows.map((r) => {
    const item = el("li", { class: "reason", tabindex: 0 },
      el("span", { class: "reason-dir", text: r.beta > 0 ? "▲" : r.beta < 0 ? "▼" : "•" }),
      el("span", { class: "reason-text" }, el("span", { class: "reason-label", text: r.label })),
      el("span", { class: "contrib", "aria-hidden": "true" },
        r.beta ? el("span", { class: `contrib-bar ${r.beta > 0 ? "pos" : "neg"}`, style: `width:${(Math.abs(r.beta) / max) * 50}%` }) : null,
        el("span", { class: "prior-tick", style: `left:${pct(r.prior)}%` })),
      el("span", { class: "reason-pts", text: `${r.beta >= 0 ? "+" : "−"}${Math.abs(r.beta).toFixed(2)}` }));
    hoverable(item, () => tip(`${r.beta >= 0 ? "+" : "−"}${Math.abs(r.beta).toFixed(2)} log-odds`, r.label, `Prior ${r.prior >= 0 ? "+" : "−"}${Math.abs(r.prior).toFixed(2)} ± ${r.sd}`));
    return item;
  }));
}

/** "Needs a closer look": the highest-risk jobs, each with its age against the norm. */
export function flagList(items, { onSelect, onHover } = {}) {
  if (!items.length) return el("p", { class: "secondary", text: "Nothing stands out right now." });
  return el("ol", { class: "flag-list" }, items.map((sp) => {
    const p = sp.posting;
    const f = sp.features;
    const button = el("button", { class: "flag-item", type: "button", "data-pid": sp.posting_id },
      gradeIcon(sp.score.grade, 22),
      el("span", { class: "flag-text" },
        el("span", { class: "flag-title", text: p.title || "Untitled posting" }),
        el("span", { class: "flag-sub", text: [p.company, p.city || p.location].filter(Boolean).join(" · ") })),
      el("span", { class: "flag-ratio" },
        el("span", { text: f.excess_ratio != null ? `${f.excess_ratio.toFixed(1)}×` : `${sp.score.risk}` }),
        el("span", { class: "muted", text: f.live_days != null ? `${f.live_days} d online` : "score" })));
    hoverable(button, () => postingCard(sp), { delay: 160 });
    button.addEventListener("click", () => { hideFloating(); onSelect?.(sp); });
    button.addEventListener("pointerenter", () => onHover?.(sp, true));
    button.addEventListener("pointerleave", () => onHover?.(sp, false));
    return el("li", {}, button);
  }));
}

/** The grade bands of the 0–100 scale with what each grade means (method page). */
export function gradeScale() {
  const meaning = {
    low: "Facts point to a live, fillable role or there is little against it.",
    moderate: "Some observable facts raise questions; verify before investing much time.",
    elevated: "Several facts fit a ghost pattern; apply briefly or verify first.",
    high: "At least two independent strong signals; usually not worth a tailored application.",
  };
  return el("div", { class: "scale-demo" },
    el("div", { class: "meter", role: "img", "aria-label": "Grade bands: low below 25, moderate 25 to 44, elevated 45 to 64, high 65 and above" },
      el("div", { class: "meter-track" }, GRADE_BANDS.map(([g, a, b]) => el("div", { class: `meter-band current ${GRADES[g].cls}`, style: `left:${a}%;width:${b - a}%` }))),
      el("div", { class: "meter-scale" }, GRADE_BANDS.map(([g, a, b]) => el("span", { style: `left:${a}%;width:${b - a}%`, text: `${a}–${b === 100 ? 100 : b - 1}` })))),
    el("div", { class: "scale-legend" }, GRADE_BANDS.map(([g]) => el("div", {}, gradeIcon(g, 20),
      el("span", {}, el("strong", { text: GRADES[g].label }), meaning[g])))));
}

// ------------------------------------------------------------------ lifecycle timeline

export function timeline(data) {
  const now = new Date(data.now).getTime();
  const instances = data.instances || [];
  if (!instances.length) return el("p", { class: "secondary", text: "No lifecycle data yet." });
  const markers = [
    ["first_published", "first published"], ["expected_end", "end of typical window"], ["start_date", "stated start date"],
    ["valid_through", "expiry date"], ["deadline", "application deadline"],
  ].filter(([k]) => data[k]).map(([k, label]) => ({ t: new Date(data[k]).getTime(), label, key: k }));
  const times = [now, ...markers.map((m) => m.t), ...instances.flatMap((i) => [i.start, i.end].filter(Boolean).map((d) => new Date(d).getTime()))];
  let t0 = Math.min(...times);
  let t1 = Math.max(...times);
  const span = Math.max(t1 - t0, 14 * 864e5);
  t0 -= span * 0.04;
  t1 += span * 0.04;
  return responsive((width) => {
    const left = 150;
    const right = 20;
    const laneH = 34;
    const top = 40;
    const plotH = instances.length * laneH;
    const height = top + plotH + 36;
    const x = (t) => left + ((t - t0) / (t1 - t0)) * (width - left - right);
    const svg = svgEl("svg", { viewBox: `0 0 ${width} ${height}`, width, height, class: "timeline", role: "img",
      "aria-label": "Lifecycle of this job across every place it was seen. The list below the chart gives the same dates." });
    // time grid: about six ticks; long spans show month and year
    const step = (t1 - t0) / 6;
    const long = t1 - t0 > 300 * 864e5;
    const tickLabel = (t) => (long
      ? new Date(t).toLocaleDateString("en-GB", { month: "short", year: "numeric" })
      : fmtShortDate(t));
    for (let i = 0; i <= 6; i += 1) {
      const t = t0 + i * step;
      svg.append(svgEl("line", { x1: x(t), x2: x(t), y1: top - 4, y2: top + plotH, class: "grid" }));
      if (i < 6) svg.append(svgEl("text", { x: x(t), y: top + plotH + 16, class: "tick", "text-anchor": "middle" }, tickLabel(t)));
    }
    // typical advertising window for the occupation
    if (data.first_published && data.expected_end) {
      const a = x(new Date(data.first_published).getTime());
      const b = x(new Date(data.expected_end).getTime());
      const band = svgEl("rect", { x: a, y: top - 4, width: Math.max(1, b - a), height: plotH + 4, class: "expected" });
      svg.append(band);
      hoverable(band, () => tip(`${data.expected_days} days`, "Typical advertising time for this occupation",
        `${fmtDate(data.first_published)} → ${fmtDate(data.expected_end)}`));
    }
    // copies (duplicates from one source are numbered)
    const seen = {};
    const totals = {};
    for (const inst of instances) totals[inst.source] = (totals[inst.source] || 0) + 1;
    instances.forEach((inst, i) => {
      const y = top + i * laneH + laneH / 2;
      const start = new Date(inst.start).getTime();
      const end = inst.end ? new Date(inst.end).getTime() : now;
      const employer = inst.channel === "employer";
      seen[inst.source] = (seen[inst.source] || 0) + 1;
      const number = totals[inst.source] > 1 ? ` #${seen[inst.source]}` : "";
      svg.append(svgEl("text", { x: left - 10, y: y + 4, class: "lane-label", "text-anchor": "end" },
        `${sourceLabel(inst.source)}${number}${employer ? " (employer)" : ""}`));
      const bar = svgEl("rect", { x: x(start), y: y - 6, width: Math.max(3, x(end) - x(start)), height: 12, rx: 3,
        class: `tl-bar ${employer ? "employer" : "copy"}` });
      svg.append(bar);
      if (inst.end) svg.append(svgEl("text", { x: x(end) + 4, y: y + 4, class: "tl-end" }, "✕ removed"));
      const hit = svgEl("rect", { x: x(start), y: y - 12, width: Math.max(24, x(end) - x(start)), height: 24, class: "hit" });
      const days = Math.round((end - start) / 864e5);
      hoverable(hit, () => tip(`${days} days`, `${sourceLabel(inst.source)}${employer ? " (employer's own channel)" : ""}`,
        `${fmtDate(inst.start)} → ${inst.end ? `removed ${fmtDate(inst.end)}` : "still online"} · ${inst.sightings} check${inst.sightings === 1 ? "" : "s"}`));
      svg.append(hit);
    });
    // dated markers, labels staggered so they never collide
    const placed = [];
    for (const m of [...markers.filter((mk) => mk.key !== "first_published"), { t: now, label: "today", key: "now" }]) {
      const mx = x(m.t);
      const row = placed.filter((p) => Math.abs(p - mx) < 110).length % 2;
      placed.push(mx);
      svg.append(svgEl("line", { x1: mx, x2: mx, y1: top - 8, y2: top + plotH, class: `marker ${m.key}` }));
      svg.append(svgEl("text", { x: mx, y: top - 12 - row * 12, class: "marker-label", "text-anchor": "middle" }, m.label));
      const hit = svgEl("rect", { x: mx - 8, y: top - 24, width: 16, height: plotH + 24, class: "hit" });
      hoverable(hit, () => tip(fmtDate(m.t), m.label));
      svg.append(hit);
    }
    // applicant observations captured by the extension
    for (const o of data.observations || []) {
      if (o.applicants == null) continue;
      const lane = Math.max(0, instances.findIndex((i) => i.source === o.platform));
      const ox = x(new Date(o.at).getTime());
      const oy = top + lane * laneH + laneH / 2 - 11;
      const label = `${o.bound === "over" ? "over " : o.bound === "first" ? "first " : ""}${o.applicants} applicants`;
      svg.append(svgEl("circle", { cx: ox, cy: oy, r: 4, class: "obs" }));
      const hit = svgEl("circle", { cx: ox, cy: oy, r: 12, class: "hit" });
      hoverable(hit, () => tip(label, `seen on ${sourceLabel(o.platform)}`, fmtDate(o.at) + (o.reposted ? " · marked as reposted" : "")));
      svg.append(hit);
    }
    const lastObs = (data.observations || []).filter((o) => o.applicants != null).slice(-1)[0];
    if (lastObs) {
      const lane = Math.max(0, instances.findIndex((i) => i.source === lastObs.platform));
      svg.append(svgEl("text", { x: x(new Date(lastObs.at).getTime()) - 6, y: top + lane * laneH + laneH / 2 - 16,
        class: "obs-label", "text-anchor": "end" }, `${lastObs.bound === "over" ? "over " : ""}${lastObs.applicants} applicants`));
    }
    return svg;
  }, 420);
}

export function timelineList(data) {
  return el("ul", { class: "plain small" }, (data.instances || []).map((i) => el("li", {},
    `${sourceLabel(i.source)}${i.channel === "employer" ? " (employer)" : ""}: ${fmtDate(i.start)} → `,
    i.end ? `removed ${fmtDate(i.end)}` : "still online",
    ` (${fmtDays(Math.round(((i.end ? new Date(i.end) : new Date(data.now)) - new Date(i.start)) / 864e5))})`)));
}
