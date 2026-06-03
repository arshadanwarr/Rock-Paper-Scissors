/**
 * api.js — backend fetch wrapper
 * All API routes are prefixed with /api/ (required by Vercel).
 * Works identically for local dev (python run.py) and Vercel.
 */

const API_BASE = window.location.protocol === "file:"
  ? "http://localhost:8000"   // opened index.html directly as a file
  : "";                       // served by FastAPI or Vercel — same origin

async function apiCall(method, path, body = null) {
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body !== null) opts.body = JSON.stringify(body);
  const res = await fetch(API_BASE + path, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

const API = {
  health:        ()         => apiCall("GET",  "/api/health"),
  play:          (move, ex) => apiCall("POST", "/api/play",           { move, exploit: ex }),
  train:         (n)        => apiCall("POST", "/api/train",          { episodes: n }),
  stats:         ()         => apiCall("GET",  "/api/stats"),
  qtable:        ()         => apiCall("GET",  "/api/qtable"),
  rewardHistory: ()         => apiCall("GET",  "/api/reward-history"),
  reset:         ()         => apiCall("POST", "/api/reset"),
  save:          ()         => apiCall("POST", "/api/save"),
  load:          ()         => apiCall("POST", "/api/load"),
};
