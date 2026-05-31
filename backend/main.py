"""
FastAPI Backend — Rock Paper Scissors RL
=========================================
Endpoints:
  POST /play          — human plays one round
  POST /train         — auto-train agent n episodes
  GET  /stats         — agent stats
  GET  /qtable        — full Q-table
  GET  /reward-history— episode reward data for chart
  POST /reset         — reset everything
  POST /save          — persist agent to disk
  POST /load          — load agent from disk
  GET  /health        — health check
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import os

try:
    from agent import QLearningAgent          # when run directly: uvicorn backend.main:app
except ImportError:
    from backend.agent import QLearningAgent  # when run as package

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Rock Paper Scissors RL API",
    description="Q-Learning agent — ML Lab Assignment 04",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Single shared agent instance ───────────────────────────────────────────────
agent = QLearningAgent()
SAVE_PATH = os.path.join(os.path.dirname(__file__), "agent_state.json")
agent.load(SAVE_PATH)   # load previous session if it exists

# ── Schemas ────────────────────────────────────────────────────────────────────
class PlayRequest(BaseModel):
    move: int = Field(..., ge=0, le=2, description="0=Rock 1=Paper 2=Scissors")
    exploit: bool = Field(True, description="True=greedy, False=ε-greedy")

class TrainRequest(BaseModel):
    episodes: int = Field(50, ge=1, le=5000)

# ── Endpoints ──────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "episodes_trained": agent.episodes}


@app.post("/play")
def play(req: PlayRequest):
    """Human plays one round. Returns round result + updated stats."""
    result = agent.play_round(req.move, exploit=req.exploit)
    agent.save(SAVE_PATH)
    return {
        "round":  result,
        "stats":  agent.get_stats(),
        "qtable": agent.get_q_table(),
    }


@app.post("/train")
def train(req: TrainRequest):
    """Auto-train agent against random opponent."""
    agent.auto_train(req.episodes)
    agent.save(SAVE_PATH)
    return {
        "trained": req.episodes,
        "stats":   agent.get_stats(),
        "qtable":  agent.get_q_table(),
        "history": agent.get_reward_history(),
    }


@app.get("/stats")
def stats():
    return agent.get_stats()


@app.get("/qtable")
def qtable():
    return {"qtable": agent.get_q_table()}


@app.get("/reward-history")
def reward_history():
    return agent.get_reward_history()


@app.post("/reset")
def reset():
    agent.reset()
    if os.path.exists(SAVE_PATH):
        os.remove(SAVE_PATH)
    return {"status": "reset", "stats": agent.get_stats()}


@app.post("/save")
def save():
    agent.save(SAVE_PATH)
    return {"status": "saved", "path": SAVE_PATH}


@app.post("/load")
def load():
    ok = agent.load(SAVE_PATH)
    return {"status": "loaded" if ok else "no_save_found", "stats": agent.get_stats()}


# ── Serve frontend ─────────────────────────────────────────────────────────────
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def root():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
