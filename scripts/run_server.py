"""Launch ORBIT FastAPI backend and live discovery dashboard."""

import sys
from pathlib import Path
import uvicorn

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.api.app import app

if __name__ == "__main__":
    print(f"Launching ORBIT Intelligence Engine on http://localhost:8000 ...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
