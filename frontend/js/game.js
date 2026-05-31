/**
 * game.js — UI logic, chart rendering, Q-table display
 * Depends on: api.js (loaded first), Chart.js (CDN)
 */

// ── Constants ─────────────────────────────────────────────────────────────────
const MOVES  = ["Rock", "Paper", "Scissors"];
const EMOJIS = ["🪨",  "📄",    "✂️"];

// ── State ─────────────────────────────────────────────────────────────────────
let history   = [];   // local copy of match history
let exploitMode = true;
let busy      = false;
let rewardChart = null;

// ── DOM refs ──────────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", async () => {
  showResult("Connecting to AI backend…", "info");
  try {
    const h = await API.health();
    setConn(true);
    showResult(`Backend online · ${h.episodes_trained} episodes loaded`, "info");
    // Refresh full UI from server
    const [stats, qt, hist] = await Promise.all([
      API.stats(), API.qtable(), API.rewardHistory()
    ]);
    renderStats(stats);
    renderQTable(qt.qtable);
    renderChart(hist);
  } catch (e) {
    setConn(false);
    showResult("Cannot reach backend — start uvicorn first", "lose");
  }
});

// ── Connection indicator ──────────────────────────────────────────────────────
function setConn(ok) {
  const dot = $("connDot");
  const lbl = $("connLabel");
  dot.className  = "conn-dot " + (ok ? "ok" : "err");
  lbl.textContent = ok ? "Backend connected" : "Backend offline";
}

// ── Move buttons ──────────────────────────────────────────────────────────────
async function humanPlay(moveIdx) {
  if (busy) return;
  busy = true;
  setBtns(true);

  // Animate question marks
  $("humanDisplay").textContent = "❓";
  $("humanDisplay").className   = "choice-display";
  $("aiDisplay").textContent    = "🤔";
  $("aiDisplay").className      = "choice-display";
  showResult("", "");

  try {
    const data = await API.play(moveIdx, exploitMode);
    const { round, stats, qtable } = data;

    // Animate result after short delay
    setTimeout(() => {
      $("humanDisplay").textContent = EMOJIS[round.hum_move];
      $("aiDisplay").textContent    = EMOJIS[round.ai_move];

      const humanCls = round.outcome === "human" ? "flash-win"
                     : round.outcome === "ai"    ? "flash-lose"
                     : "flash-draw";
      const aiCls    = round.outcome === "ai"    ? "flash-win"
                     : round.outcome === "human" ? "flash-lose"
                     : "flash-draw";
      $("humanDisplay").className = "choice-display " + humanCls;
      $("aiDisplay").className    = "choice-display " + aiCls;

      // Result text
      if (round.outcome === "human") {
        showResult(`🎉 You Win!  ${MOVES[round.hum_move]} beats ${MOVES[round.ai_move]}`, "win");
      } else if (round.outcome === "ai") {
        showResult(`🤖 AI Wins!  ${MOVES[round.ai_move]} beats ${MOVES[round.hum_move]}`, "lose");
      } else {
        showResult(`🤝 Draw!  Both chose ${MOVES[round.hum_move]}`, "draw");
      }

      // Push to local history
      history.push(round);
      renderHistory();
      renderStats(stats);
      renderQTable(qtable);
      renderEpsilon(stats.epsilon);

      busy = false;
      setBtns(false);
    }, 380);
  } catch (e) {
    showResult("Error: " + e.message, "lose");
    busy = false;
    setBtns(false);
  }
}

// ── Train ─────────────────────────────────────────────────────────────────────
async function doTrain(n) {
  if (busy) return;
  busy = true;
  setBtns(true);
  showResult(`<span class="spinner"></span>Training ${n} episodes…`, "info");

  try {
    const data = await API.train(n);
    renderStats(data.stats);
    renderQTable(data.qtable);
    renderChart(data.history);
    renderEpsilon(data.stats.epsilon);
    showResult(`✅ Trained ${n} episodes — ε=${data.stats.epsilon}`, "info");
  } catch (e) {
    showResult("Training error: " + e.message, "lose");
  } finally {
    busy = false;
    setBtns(false);
  }
}

// ── Reset ─────────────────────────────────────────────────────────────────────
async function doReset() {
  if (!confirm("Reset the agent? All training will be lost.")) return;
  try {
    const data = await API.reset();
    history = [];
    renderStats(data.stats);
    renderQTable([]);
    renderChart({ episode_rewards:[], cumulative_rewards:[], episodes:[] });
    renderHistory();
    renderEpsilon(1.0);
    $("humanDisplay").textContent = "🤔";
    $("humanDisplay").className   = "choice-display";
    $("aiDisplay").textContent    = "🤖";
    $("aiDisplay").className      = "choice-display";
    showResult("Game reset. Choose your move!", "info");
  } catch (e) {
    showResult("Reset error: " + e.message, "lose");
  }
}

// ── Mode toggle ───────────────────────────────────────────────────────────────
function setMode(m) {
  exploitMode = (m === "exploit");
  $("modeExploit").className  = "mode-btn" + (exploitMode  ? " active" : "");
  $("modeExplore").className  = "mode-btn" + (!exploitMode ? " active" : "");
}

// ── UI helpers ────────────────────────────────────────────────────────────────
function setBtns(disabled) {
  ["btnRock","btnPaper","btnScissors"].forEach(id => {
    $(id).disabled = disabled;
  });
  ["train10","train50","train200","btnReset"].forEach(id => {
    $(id).disabled = disabled;
  });
}

function showResult(msg, cls) {
  const el = $("resultText");
  el.innerHTML  = msg;
  el.className  = "result-text" + (msg ? " show" : "") + (cls ? " " + cls : "");
}

// ── Render stats ──────────────────────────────────────────────────────────────
function renderStats(s) {
  $("scoreHuman").textContent   = s.losses ?? 0;
  $("scoreDraw").textContent    = s.draws  ?? 0;
  $("scoreAI").textContent      = s.wins   ?? 0;
  $("scoreEpisodes").textContent= s.episodes ?? 0;

  $("statAlpha").textContent    = s.alpha      ?? "0.30";
  $("statGamma").textContent    = s.gamma      ?? "0.90";
  $("statWinRate").textContent  = s.win_rate != null ? s.win_rate + "%" : "—";
  $("statAvgReward").textContent= s.avg_reward ?? "—";
  $("statTotalReward").textContent = (s.total_reward ?? 0).toFixed(2);
  $("statEpisodes2").textContent   = s.episodes ?? 0;

  renderEpsilon(s.epsilon ?? 1.0);
}

function renderEpsilon(eps) {
  const pct = Math.max(0, ((eps - 0.05) / 0.95) * 100);
  $("epsFill").style.width = pct + "%";
  $("epsVal").textContent  = (+eps).toFixed(3);
}

// ── Render Q-table ────────────────────────────────────────────────────────────
function qColor(v) {
  if (v >  0.3)  return { bg: "rgba(92,252,188,.22)", color: "#5cfcbc" };
  if (v >  0.05) return { bg: "rgba(92,252,188,.08)", color: "#5cfcbc99" };
  if (v < -0.3)  return { bg: "rgba(252,92,124,.22)", color: "#fc5c7c" };
  if (v < -0.05) return { bg: "rgba(252,92,124,.08)", color: "#fc5c7c99" };
  return { bg: "rgba(255,255,255,.04)", color: "#6a6a8a" };
}

function renderQTable(rows) {
  const grid = $("qtableGrid");
  if (!rows || rows.length === 0) {
    grid.innerHTML = `<div style="grid-column:1/-1;color:var(--muted);font-family:var(--font-mono);font-size:.6rem;padding:.5rem;">No Q-values yet — train or play first.</div>`;
    return;
  }
  let html = `
    <div class="qt-h">State (AI→Hum)</div>
    <div class="qt-h">🪨 Rock</div>
    <div class="qt-h">📄 Paper</div>
    <div class="qt-h">✂️ Scissors</div>
    <div class="qt-h">Best Action</div>
  `;
  rows.forEach(r => {
    const cR = qColor(r.rock), cP = qColor(r.paper), cS = qColor(r.scissors);
    html += `
      <div class="qt-state">${r.state}</div>
      <div class="qt-cell" style="background:${cR.bg};color:${cR.color}">${(+r.rock).toFixed(3)}</div>
      <div class="qt-cell" style="background:${cP.bg};color:${cP.color}">${(+r.paper).toFixed(3)}</div>
      <div class="qt-cell" style="background:${cS.bg};color:${cS.color}">${(+r.scissors).toFixed(3)}</div>
      <div class="qt-best">${r.best_action}</div>
    `;
  });
  grid.innerHTML = html;
}

// ── Render chart ──────────────────────────────────────────────────────────────
function renderChart(data) {
  const ctx = $("rewardChart").getContext("2d");
  const labels  = data.episodes         || [];
  const cumData = data.cumulative_rewards || [];

  if (rewardChart) {
    rewardChart.data.labels            = labels;
    rewardChart.data.datasets[0].data  = cumData;
    rewardChart.update("none");
    return;
  }

  rewardChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Avg Reward / Episode",
        data: cumData,
        borderColor: "#7c5cfc",
        backgroundColor: "rgba(124,92,252,.08)",
        borderWidth: 1.5,
        pointRadius: 0,
        fill: true,
        tension: 0.35,
      }],
    },
    options: {
      responsive: true,
      animation: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#12121a",
          borderColor: "#7c5cfc",
          borderWidth: 1,
          titleColor: "#7c5cfc",
          bodyColor: "#e8e8f0",
          titleFont: { family: "Space Mono", size: 10 },
          bodyFont:  { family: "Space Mono", size: 10 },
          callbacks: { label: c => "Avg reward: " + c.parsed.y.toFixed(4) },
        },
      },
      scales: {
        x: {
          grid:   { color: "rgba(255,255,255,.04)" },
          ticks:  { color: "#6a6a8a", font: { family: "Space Mono", size: 9 }, maxTicksLimit: 8 },
          border: { color: "rgba(255,255,255,.06)" },
        },
        y: {
          grid:   { color: "rgba(255,255,255,.04)" },
          ticks:  { color: "#6a6a8a", font: { family: "Space Mono", size: 9 } },
          border: { color: "rgba(255,255,255,.06)" },
        },
      },
    },
  });
}

// ── Render history ────────────────────────────────────────────────────────────
function renderHistory() {
  const list = $("historyList");
  if (history.length === 0) {
    list.innerHTML = `<div class="hist-item" style="justify-content:center;">No rounds yet</div>`;
    return;
  }
  const recent = history.slice(-40);
  list.innerHTML = recent.map(h => {
    const out = h.outcome === "human" ? "You Win"
              : h.outcome === "ai"   ? "AI Wins" : "Draw";
    const cls = h.outcome === "human" ? "win"
              : h.outcome === "ai"   ? "lose"   : "draw";
    const rew = h.reward > 0 ? `<span style="color:var(--win)">+1.0</span>`
              : h.reward < 0 ? `<span style="color:var(--lose)">-1.0</span>`
              : `<span style="color:var(--muted)">0.0</span>`;
    return `<div class="hist-item">
      <span class="hist-ep">#${h.episode}</span>
      <span class="hist-move">${EMOJIS[h.hum_move]}${MOVES[h.hum_move]} vs ${EMOJIS[h.ai_move]}${MOVES[h.ai_move]}</span>
      <span class="hist-out ${cls}">${out}</span>
      <span class="hist-rew">${rew}</span>
    </div>`;
  }).join("");
}
