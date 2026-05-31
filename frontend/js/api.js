/**
 * api.js — thin client for the FastAPI backend
 * All fetch calls go through here so the base URL is configured once.
 */

// ── Config ────────────────────────────────────────────────────────────────────
// In production (served from FastAPI) the API is on the same origin.
// In local dev the backend is on port 8000.
const API_BASE =
  window.location.port === "8000" || window.location.port === ""
    ? ""                    // same origin — FastAPI serves everything
    : "http://localhost:8000"; // dev: frontend opened directly in browser

// ── Helpers ───────────────────────────────────────────────────────────────────
async function apiCall(method, path, body = null) {
  const opts = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  if (body !== null) opts.body = JSON.stringify(body);
  const res = await fetch(API_BASE + path, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// ── Public API ────────────────────────────────────────────────────────────────
const API = {
  health:        ()         => apiCall("GET",  "/health"),
  play:          (move, ex) => apiCall("POST", "/play",  { move, exploit: ex }),
  train:         (n)        => apiCall("POST", "/train", { episodes: n }),
  stats:         ()         => apiCall("GET",  "/stats"),
  qtable:        ()         => apiCall("GET",  "/qtable"),
  rewardHistory: ()         => apiCall("GET",  "/reward-history"),
  reset:         ()         => apiCall("POST", "/reset"),
  save:          ()         => apiCall("POST", "/save"),
  load:          ()         => apiCall("POST", "/load"),
};
