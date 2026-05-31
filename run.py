"""
run.py — Start the RPS RL Game server
Usage: python run.py
Then open: http://localhost:8000
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,       # auto-reload on code changes
        log_level="info",
    )
