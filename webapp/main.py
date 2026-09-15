import sys
from pathlib import Path

# Make project root importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import json

from src.graph.queries import ConstraintQueries
from src.memory.experience import ExperienceMemory

app = FastAPI(title="CINT‑70 Dashboard")

# Mount static files (from project root, the folder is webapp/static)
app.mount("/static", StaticFiles(directory="webapp/static"), name="static")

graph = ConstraintQueries()
memory = ExperienceMemory()

EVIDENCE_DIR = Path("logs/evidence")


@app.get("/")
def index():
    return FileResponse("webapp/static/index.html")


@app.get("/api/obstacles")
def get_obstacles():
    obstacles = []
    try:
        result = graph.conn.execute(
            "MATCH (o:Obstacle) RETURN o.name, o.x, o.y, o.z, o.radius, o.clearance"
        )
        while result.has_next():
            row = result.get_next()
            obstacles.append({
                "name": row[0],
                "x": row[1], "y": row[2], "z": row[3],
                "radius": row[4], "clearance": row[5]
            })
    except:
        pass
    return obstacles


@app.get("/api/joints")
def get_joints():
    joints = []
    try:
        result = graph.conn.execute(
            "MATCH (j:Joint) RETURN j.name, j.min_angle, j.max_angle, j.max_velocity"
        )
        while result.has_next():
            row = result.get_next()
            joints.append({
                "name": row[0],
                "min": row[1], "max": row[2],
                "max_velocity": row[3]
            })
    except:
        pass
    return joints


@app.get("/api/benchmark/latest")
def latest_benchmark():
    bench_dir = Path("logs/benchmarks")
    if not bench_dir.exists():
        return {"error": "No benchmarks"}
    files = sorted(bench_dir.glob("*.json"), reverse=True)
    if not files:
        return {"error": "No benchmarks"}
    with open(files[0]) as f:
        return json.load(f)


@app.get("/api/evidence/recent")
def recent_evidence(limit: int = 5):
    if not EVIDENCE_DIR.exists():
        return []
    files = sorted(EVIDENCE_DIR.glob("*.json"), reverse=True)[:limit]
    trails = []
    for f in files:
        with open(f) as fp:
            trails.append(json.load(fp))
    return trails


# ---------------------------------------------------------------------------
# NEW — Evidence Trail search & filter (dashboard feature 5)
# Must be declared before /api/evidence/{filename} so "recent" above still
# resolves correctly and this doesn't collide with the filename route below.
# ---------------------------------------------------------------------------
@app.get("/api/evidence")
def get_filtered_evidence(task: str = "", search: str = "", limit: int = 20):
    if not EVIDENCE_DIR.exists():
        return []
    files = sorted(EVIDENCE_DIR.glob("*.json"), reverse=True)
    results = []
    for f in files:
        try:
            with open(f) as fp:
                data = json.load(fp)
        except (json.JSONDecodeError, OSError):
            continue
        if task and data.get("task_type", "").lower() != task.lower():
            continue
        if search and search.lower() not in data.get("command", "").lower():
            continue
        data["filename"] = f.name  # lets the frontend/future rows link back to this exact run
        results.append(data)
        if len(results) >= limit:
            break
    return results


# ---------------------------------------------------------------------------
# NEW — fetch a single evidence record by filename (dashboard feature 3,
# for wiring true per-row "Test Details" once benchmark results carry it)
# ---------------------------------------------------------------------------
@app.get("/api/evidence/{filename}")
def get_evidence_file(filename: str):
    file_path = EVIDENCE_DIR / filename
    if file_path.exists():
        with open(file_path) as f:
            return json.load(f)
    return {"error": "File not found"}


@app.get("/api/stats")
def get_stats():
    return memory.get_stats()


# ---------------------------------------------------------------------------
# NEW — Live Pipeline Trigger (dashboard feature 4)
#
# ASSUMPTION I can't verify without seeing it: an orchestrator class living at
# src/agent/orchestrator.py with a CINT70Orchestrator().execute(command) method
# that returns a dict containing at least all_checks_passed, trust_score,
# plan, violations, recovery_count — matching the shape your /api/evidence
# files already use. Adjust the import path and the result.get(...) keys
# below to whatever your orchestrator actually returns.
# ---------------------------------------------------------------------------
class CommandRequest(BaseModel):
    command: str


@app.post("/api/run")
def run_pipeline(req: CommandRequest):
    from src.agent.orchestrator import CINT70Orchestrator

    orch = CINT70Orchestrator()
    result = orch.execute(req.command)

    return {
        "approved": result.get("all_checks_passed", False),
        "trust_score": result.get("trust_score", 0),
        "steps": len(result.get("plan", [])),
        "violations": result.get("violations", []),
        "recovery_count": result.get("recovery_count", 0),
        "plan": result.get("plan", []),
    }