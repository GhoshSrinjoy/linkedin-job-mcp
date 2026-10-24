// DOM and formatting helpers. Data from the API is always inserted as text, never as HTML.

export const $ = (sel, root = document) => root.querySelector(sel);
export const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

export function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value === null || value === undefined || value === false) continue;
    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = value;
    else if (key === "style") node.setAttribute("style", value);
    else if (key.startsWith("on") && typeof value === "function") node.addEventListener(key.slice(2), value);
    else node.setAttribute(key, value === true ? "" : String(value));
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

export function svgEl(tag, attrs = {}, text) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [k, v] of Object.entries(attrs)) if (v !== null && v !== undefined) node.setAttribute(k, String(v));
  if (text !== undefined) node.textContent = text;
  return node;
}

export const fmtDate = (value) => {
  if (!value) return "—";
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? "—" : d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
};
export const fmtShortDate = (value) => {
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? "" : d.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
};
export const fmtDays = (n) => (n === null || n === undefined ? "—" : `${n} day${n === 1 ? "" : "s"}`);
export const safeUrl = (url) => (typeof url === "string" && /^https?:\/\//i.test(url) ? url : null);
export const median = (values) => {
  const v = values.filter((x) => typeof x === "number").sort((a, b) => a - b);
  return v.length ? v[Math.floor(v.length / 2)] : null;
};
export const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

// deterministic pseudo-random in [0, 1) from a string (stable jitter across renders)
export function hash01(text) {
  let h = 2166136261;
  for (let i = 0; i < text.length; i += 1) {
    h ^= text.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return ((h >>> 0) % 10000) / 10000;
}

export async function api(path, options = {}) {
  const res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  if (!res.ok) {
    let message = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (body.detail) message = typeof body.detail === "string" ? body.detail : body.detail.map((d) => d.msg).join("; ");
    } catch (_) { /* keep status text */ }
    throw new Error(message);
  }
  return res.json();
}

export const SOURCE_LABELS = {
  personio: "Personio", greenhouse: "Greenhouse", lever: "Lever", smartrecruiters: "SmartRecruiters", ashby: "Ashby",
  recruitee: "Recruitee", workday: "Workday", jsonld: "Careers page", page: "Web page", arbeitnow: "Arbeitnow",
  adzuna: "Adzuna", manual: "Pasted text", linkedin: "LinkedIn", ba: "Bundesagentur", jsearch: "Google for Jobs",
  indeed: "Indeed", stepstone: "StepStone", xing: "XING", glassdoor: "Glassdoor", web: "Web page",
};
export const sourceLabel = (s) => SOURCE_LABELS[s] || s;
