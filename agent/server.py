"""Minimal FastAPI server for the pipeline monitor.

Serves pipeline-explorer.html and provides API endpoints for launching
pipeline runs and polling their status via the audit_log table.

Usage:
    cd /Users/oliviagao/project/starbridge
    python -m agent.server
    # or: uvicorn agent.server:app --port 8111
"""

import json
import os
import threading
import time

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import uvicorn

from . import db
from .pipeline import run_pipeline

app = FastAPI()

# ── State ────────────────────────────────────────────────────────────────────

_active_run = {"thread": None, "run_id": None, "error": None}
_lock = threading.Lock()

AGENT_DIR = os.path.dirname(__file__)
HTML_PATH = os.path.join(AGENT_DIR, "pipeline-explorer.html")
LOGO_PATH = os.path.join(AGENT_DIR, "starbridge-logo-white.svg")


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/")
def serve_html():
    return FileResponse(HTML_PATH, media_type="text/html")


@app.get("/starbridge-logo-white.svg")
def serve_logo():
    return FileResponse(LOGO_PATH, media_type="image/svg+xml")


@app.post("/api/run")
def start_run(webhook: dict):
    """Launch a pipeline run in a background thread. Returns run_id."""
    with _lock:
        if _active_run["thread"] and _active_run["thread"].is_alive():
            raise HTTPException(409, "Pipeline already running")

    # Validate: at least one of target_company or target_domain
    if not webhook.get("target_company") and not webhook.get("target_domain"):
        raise HTTPException(422, "At least one of target_company or target_domain required")

    _active_run["error"] = None
    _active_run["run_id"] = None

    def _run():
        try:
            result = run_pipeline(webhook)
            with _lock:
                _active_run["run_id"] = result.get("runId")
        except Exception as e:
            with _lock:
                _active_run["error"] = str(e)

    t = threading.Thread(target=_run, daemon=True)
    _active_run["thread"] = t
    t.start()

    # Wait briefly for s1 to create the run stub so we can return run_id
    for _ in range(20):  # up to 2s
        time.sleep(0.1)
        runs = db.get_recent_runs(1)
        if runs and runs[0]["status"] == "processing":
            _active_run["run_id"] = runs[0]["id"]
            return {"run_id": runs[0]["id"]}

    # If we still don't have a run_id, return what we have
    if _active_run["error"]:
        raise HTTPException(500, _active_run["error"])
    return {"run_id": None, "message": "Pipeline started, run_id not yet available"}


@app.get("/api/status/{run_id}")
def get_status(run_id: int):
    """Poll target — returns run metadata + audit_log entries."""
    run = db.get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")

    audit = db.get_audit_log(run_id)

    # Strip large JSON fields from the run row for lightweight polling
    light_run = {
        "id": run["id"],
        "target_domain": run["target_domain"],
        "target_company": run["target_company"],
        "status": run["status"],
        "created_at": run["created_at"],
        "completed_at": run["completed_at"],
        "featured_buyer_id": run["featured_buyer_id"],
        "featured_buyer_name": run["featured_buyer_name"],
        "notion_url": run["notion_url"],
    }

    # Check if pipeline thread is still alive
    pipeline_active = _active_run["thread"] and _active_run["thread"].is_alive()

    return {
        "run": light_run,
        "audit_log": audit,
        "pipeline_active": pipeline_active,
        "error": _active_run["error"],
    }


@app.get("/api/runs")
def list_runs():
    """List recent runs for the run selector dropdown."""
    return db.get_recent_runs(20)


@app.get("/api/data/{run_id}/{table}")
def get_data(run_id: int, table: str):
    """Fetch detailed data for a specific run + table."""
    if table not in ("discoveries", "contacts", "audit_log", "run"):
        raise HTTPException(400, f"Unknown table: {table}")

    if table == "run":
        run = db.get_run(run_id)
        if not run:
            raise HTTPException(404, "Run not found")
        # Parse JSON fields for the full view
        for key in ("search_strategy", "discovery_signals_a", "discovery_signals_b",
                     "discovery_buyers", "secondary_buyers", "feat_profile",
                     "feat_contacts", "sec_profiles", "sec_contacts"):
            if run.get(key):
                try:
                    run[key] = json.loads(run[key])
                except (json.JSONDecodeError, TypeError):
                    pass
        return run

    conn = db.get_connection()
    rows = conn.execute(
        f"SELECT * FROM {table} WHERE run_id = ? ORDER BY id", (run_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    db.init_db()
    uvicorn.run(app, host="127.0.0.1", port=8111)
