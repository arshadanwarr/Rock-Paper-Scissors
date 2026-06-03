"""
api/index.py  ←  Vercel REQUIRES this exact path and filename.
FastAPI app entry point for Vercel serverless deployment.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field
import os, pathlib

from agent import QLearningAgent   # agent.py lives next to this file

# ── App ────────────────────────────────────────────────────────
app = FastAPI(title="RPS RL API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Agent ──────────────────────────────────────────────────────
# /tmp is the only writable directory on Vercel lambdas.
SAVE_PATH = "/tmp/agent_state.json"
agent = QLearningAgent()
agent.load(SAVE_PATH)   # loads previous state if lambda is warm

# ── Schemas ────────────────────────────────────────────────────
class PlayRequest(BaseModel):
    move: int  = Field(..., ge=0, le=2)
    exploit: bool = Field(True)

class TrainRequest(BaseModel):
    episodes: int = Field(50, ge=1, le=5000)

# ── Endpoints ──────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok", "episodes_trained": agent.episodes}

@app.post("/api/play")
def play(req: PlayRequest):
    result = agent.play_round(req.move, exploit=req.exploit)
    agent.save(SAVE_PATH)
    return {
        "round":  result,
        "stats":  agent.get_stats(),
        "qtable": agent.get_q_table(),
    }

@app.post("/api/train")
def train(req: TrainRequest):
    agent.auto_train(req.episodes)
    agent.save(SAVE_PATH)
    return {
        "trained": req.episodes,
        "stats":   agent.get_stats(),
        "qtable":  agent.get_q_table(),
        "history": agent.get_reward_history(),
    }

@app.get("/api/stats")
def stats():
    return agent.get_stats()

@app.get("/api/qtable")
def qtable():
    return {"qtable": agent.get_q_table()}

@app.get("/api/reward-history")
def reward_history():
    return agent.get_reward_history()

@app.post("/api/reset")
def reset():
    agent.reset()
    if os.path.exists(SAVE_PATH):
        os.remove(SAVE_PATH)
    return {"status": "reset", "stats": agent.get_stats()}

@app.post("/api/save")
def save():
    agent.save(SAVE_PATH)
    return {"status": "saved"}

@app.post("/api/load")
def load():
    ok = agent.load(SAVE_PATH)
    return {"status": "loaded" if ok else "no_save_found", "stats": agent.get_stats()}
