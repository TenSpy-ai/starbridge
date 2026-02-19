"""FastAPI server for the pipeline monitor.

Serves pipeline-explorer.html and provides API endpoints for launching
pipeline runs (single + batch), polling status, and managing active runs.

Usage:
    cd /Users/oliviagao/project/starbridge
    python -m agent.server
    # or: uvicorn agent.server:app --port 8111
"""

import json
import os
import threading
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
import uvicorn

from . import db
from .config import (
    MAX_CONCURRENT_RUNS, CONFIG_METADATA,
    get_config_snapshot, set_config_value, reset_config, apply_config_to_modules,
)
from .pipeline import run_pipeline

app = FastAPI()

# ── State ────────────────────────────────────────────────────────────────────

# Multi-run tracking: run_id → {"thread", "stop_event", "error", "batch_id"}
_active_runs: dict[int, dict] = {}
_lock = threading.Lock()
_run_semaphore = threading.Semaphore(MAX_CONCURRENT_RUNS)
_batch_counter = 0

AGENT_DIR = os.path.dirname(__file__)
HTML_PATH = os.path.join(AGENT_DIR, "pipeline-explorer.html")
LOGO_PATH = os.path.join(AGENT_DIR, "starbridge-logo-white.svg")


def _prune_dead_runs():
    """Remove entries for threads that have finished. Call under _lock."""
    dead = [rid for rid, entry in _active_runs.items()
            if not entry["thread"].is_alive()]
    for rid in dead:
        del _active_runs[rid]


def _active_count():
    """Count currently alive run threads. Call under _lock."""
    return sum(1 for entry in _active_runs.values() if entry["thread"].is_alive())


def _run_pipeline_managed(webhook, run_entry, run_id, semaphore=None):
    """Wrapper: acquire semaphore slot, apply config snapshot, run pipeline, release."""
    sem = semaphore or _run_semaphore
    sem.acquire()
    try:
        # Mark as actually running now that we have a semaphore slot
        conn = db.get_connection()
        conn.execute("UPDATE runs SET status='processing' WHERE id=?", (run_id,))
        conn.commit()
        conn.close()

        # Apply the config snapshot captured at submission time so this run
        # uses the config that was active when it was started, not whatever
        # the user may have changed in the UI since then.
        snapshot = run_entry.get("config_snapshot")
        if snapshot:
            apply_config_to_modules(snapshot)
        run_pipeline(webhook, stop_event=run_entry["stop_event"], run_id=run_id)
    except Exception as e:
        with _lock:
            run_entry["error"] = str(e)
    finally:
        sem.release()


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/")
def serve_html():
    return FileResponse(HTML_PATH, media_type="text/html")


@app.get("/starbridge-logo-white.svg")
def serve_logo():
    return FileResponse(LOGO_PATH, media_type="image/svg+xml")


@app.get("/test-batch.csv")
def serve_test_csv():
    csv_path = os.path.join(os.path.dirname(__file__), "tmp", "test-batch-5.csv")
    return FileResponse(csv_path, media_type="text/csv", filename="test-batch-5.csv")


@app.post("/api/run")
def start_run(webhook: dict):
    """Launch a single pipeline run in a background thread. Returns run_id."""
    # Validate: at least one of target_company or target_domain
    if not webhook.get("target_company") and not webhook.get("target_domain"):
        raise HTTPException(422, "At least one of target_company or target_domain required")

    with _lock:
        _prune_dead_runs()
        if _active_count() >= MAX_CONCURRENT_RUNS:
            raise HTTPException(409, f"Max concurrent runs ({MAX_CONCURRENT_RUNS}) reached")

    # Pre-create run stub so we can return run_id immediately
    db.init_db()
    run_id = db.insert_run_stub(webhook)

    # Snapshot config at submission time — this run will use these values
    # even if the user changes config in the UI before the run finishes.
    config_snapshot = get_config_snapshot()

    stop_event = threading.Event()
    entry = {"thread": None, "stop_event": stop_event, "error": None,
             "batch_id": None, "config_snapshot": config_snapshot}
    t = threading.Thread(target=_run_pipeline_managed, args=(webhook, entry, run_id), daemon=True)
    entry["thread"] = t

    with _lock:
        _active_runs[run_id] = entry
    t.start()

    return {"run_id": run_id}


@app.post("/api/batch")
def start_batch(webhooks: list[dict]):
    """Launch multiple pipeline runs. Returns batch_id + run_ids.

    Runs are throttled by MAX_CONCURRENT_RUNS semaphore — excess runs
    queue until a slot opens.
    """
    global _batch_counter

    if not webhooks:
        raise HTTPException(422, "Empty webhook list")

    # Validate all rows first
    invalid = []
    for i, wh in enumerate(webhooks):
        if not wh.get("target_company") and not wh.get("target_domain"):
            invalid.append(f"Row {i+1}: missing target_company and target_domain")
    if invalid:
        raise HTTPException(422, f"Validation failed:\n" + "\n".join(invalid))

    with _lock:
        _prune_dead_runs()
        _batch_counter += 1
        batch_id = _batch_counter

    # Pre-create all run stubs so we can return run_ids immediately
    db.init_db()
    run_ids = []
    for wh in webhooks:
        rid = db.insert_run_stub(wh, batch_id=batch_id)
        run_ids.append(rid)

    # Snapshot config once for the entire batch — all runs use the same config.
    config_snapshot = get_config_snapshot()

    # Create a per-batch semaphore from the current MAX_CONCURRENT_RUNS config
    batch_semaphore = threading.Semaphore(config_snapshot.get("MAX_CONCURRENT_RUNS", MAX_CONCURRENT_RUNS))

    # Spawn threads (semaphore gates actual execution)
    for rid, wh in zip(run_ids, webhooks):
        stop_event = threading.Event()
        entry = {"thread": None, "stop_event": stop_event, "error": None,
                 "batch_id": batch_id, "config_snapshot": config_snapshot}
        t = threading.Thread(target=_run_pipeline_managed, args=(wh, entry, rid, batch_semaphore), daemon=True)
        entry["thread"] = t
        with _lock:
            _active_runs[rid] = entry
        t.start()

    return {"batch_id": batch_id, "run_ids": run_ids, "total": len(run_ids)}


@app.get("/api/batch-status/{batch_id}")
def get_batch_status(batch_id: int):
    """Returns status summary for all runs in a batch."""
    runs = db.get_batch_runs(batch_id)
    if not runs:
        raise HTTPException(404, "Batch not found")

    counts = {"completed": 0, "failed": 0, "processing": 0, "pending": 0, "cancelled": 0}
    for r in runs:
        status = r["status"]
        if status in counts:
            counts[status] += 1
        else:
            counts[status] = counts.get(status, 0) + 1

    return {
        "batch_id": batch_id,
        "total": len(runs),
        **counts,
        "runs": runs,
    }


@app.post("/api/batch-kill/{batch_id}")
def kill_batch(batch_id: int):
    """Kill all active runs in a batch."""
    killed = 0
    with _lock:
        entries = [(rid, e) for rid, e in _active_runs.items()
                   if e.get("batch_id") == batch_id and e["thread"].is_alive()]

    for rid, entry in entries:
        entry["stop_event"].set()

    # Brief wait for graceful exit
    for rid, entry in entries:
        entry["thread"].join(timeout=2)

    # Mark any still-processing runs as cancelled
    for rid, entry in entries:
        run = db.get_run(rid)
        if run and run["status"] in ("processing", "pending"):
            db.update_run_cancelled(rid)
            db.log_step(rid, "pipeline_killed", "failure", "Killed via batch kill")
        killed += 1

    return {"status": "cancelled", "batch_id": batch_id, "killed": killed}


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
        "product_description": run["product_description"],
        "status": run["status"],
        "created_at": run["created_at"],
        "completed_at": run["completed_at"],
        "featured_buyer_id": run["featured_buyer_id"],
        "featured_buyer_name": run["featured_buyer_name"],
        "featured_buyer_type": run.get("featured_buyer_type"),
        "selection_rationale": run.get("selection_rationale"),
        "secondary_buyers": run.get("secondary_buyers"),
        "validation_result": run.get("validation_result"),
        "notion_url": run["notion_url"],
        "batch_id": run.get("batch_id"),
        "search_strategy": run.get("search_strategy"),
    }

    # Parse JSON string fields for the frontend
    for key in ("secondary_buyers", "validation_result"):
        if light_run.get(key) and isinstance(light_run[key], str):
            try:
                light_run[key] = json.loads(light_run[key])
            except (json.JSONDecodeError, TypeError):
                pass

    # Prior run count — how many completed runs exist for this domain
    prior_count = 0
    if run["target_domain"]:
        conn = db.get_connection()
        row = conn.execute(
            "SELECT COUNT(*) FROM runs WHERE target_domain = ? AND status = 'completed' AND id < ?",
            (run["target_domain"], run["id"]),
        ).fetchone()
        conn.close()
        prior_count = row[0] if row else 0
    light_run["prior_run_count"] = prior_count

    # Check dedup status from s1 audit log for this run
    dedup_enabled = None
    for entry in audit:
        if entry.get("step") == "s1_validate_and_load" and entry.get("metadata"):
            try:
                meta = json.loads(entry["metadata"]) if isinstance(entry["metadata"], str) else entry["metadata"]
                dedup_enabled = meta.get("dedup_enabled")
            except (json.JSONDecodeError, TypeError):
                pass
            break
    light_run["dedup_enabled"] = dedup_enabled

    # Check if this specific run's thread is still alive
    with _lock:
        entry = _active_runs.get(run_id)
    pipeline_active = entry and entry["thread"].is_alive() if entry else False
    error = entry["error"] if entry else None

    return {
        "run": light_run,
        "audit_log": audit,
        "pipeline_active": pipeline_active,
        "error": error,
    }


@app.post("/api/kill/{run_id}")
def kill_run(run_id: int):
    """Signal an active pipeline to stop and mark the run as cancelled."""
    with _lock:
        entry = _active_runs.get(run_id)

    if not entry or not entry["thread"].is_alive():
        raise HTTPException(409, "No active pipeline for this run_id")

    entry["stop_event"].set()
    entry["thread"].join(timeout=5)

    # If the pipeline thread handled it, status is already 'cancelled'.
    # If thread is still alive or didn't update DB, mark it ourselves.
    run = db.get_run(run_id)
    if run and run["status"] in ("processing", "pending"):
        db.update_run_cancelled(run_id)
        db.log_step(run_id, "pipeline_killed", "failure", "Killed by user via monitor UI")

    return {"status": "cancelled", "run_id": run_id}


@app.get("/api/config")
def get_config():
    """Return all tunable config values + metadata for the explorer UI."""
    return {"values": get_config_snapshot(), "metadata": CONFIG_METADATA}


@app.patch("/api/config")
async def update_config(request: Request):
    """Update one or more config values at runtime.

    Body: {"KEY": value, ...}. Changes are in-memory only — lost on restart.
    """
    updates = await request.json()
    errors = []
    changed = []
    for key, value in updates.items():
        ok, err = set_config_value(key, value)
        if ok:
            changed.append(key)
        else:
            errors.append(err)
    if errors and not changed:
        raise HTTPException(400, "; ".join(errors))
    return {"changed": changed, "errors": errors, "values": get_config_snapshot()}


@app.post("/api/config/reset")
def reset_config_endpoint():
    """Reset all config values to factory defaults (as defined in config.py source).

    Only affects the next pipeline run — already-running pipelines keep their
    snapshot. Changes are in-memory; restarting the server has the same effect.
    """
    values = reset_config()
    return {"status": "reset", "values": values}


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
                     "feat_contacts", "sec_profiles", "sec_contacts",
                     "validation_result"):
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


# ── Startup ──────────────────────────────────────────────────────────────────

@app.on_event("startup")
def _init_batch_counter():
    """Seed _batch_counter from DB so it doesn't collide after restart."""
    global _batch_counter
    db.init_db()
    conn = db.get_connection()
    row = conn.execute("SELECT MAX(batch_id) FROM runs").fetchone()
    conn.close()
    _batch_counter = (row[0] or 0)


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    db.init_db()
    uvicorn.run(app, host="127.0.0.1", port=8111)
