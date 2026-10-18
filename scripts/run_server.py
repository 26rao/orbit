"""Launch ORBIT FastAPI backend and live discovery dashboard."""

import uvicorn

if __name__ == "__main__":
    print("Launching ORBIT Intelligence Engine on http://localhost:8000 ...")
    uvicorn.run("src.api.app:app", host="0.0.0.0", port=8000, reload=True)
