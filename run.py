"""
run.py — start local dev server
Usage: python run.py
Then open: http://localhost:8000
"""
import sys, os

# Make sure api/ folder is on the path so agent.py imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "api"))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "api.index:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
