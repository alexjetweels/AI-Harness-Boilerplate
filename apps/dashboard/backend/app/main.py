from __future__ import annotations

import asyncio
import os
import signal
import sys
import time
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import db
from . import db_logger


class CreateHarnessRunRequest(BaseModel):
    feature: str = Field(..., min_length=3, max_length=500)
    provider: Literal["claude", "codex"] = "codex"
    tech_stack: str = Field(default="React 18 + NestJS 10 + Prisma 5 + MySQL 8 + Docker", max_length=240)
    target: Literal["okr-ghcp"] = "okr-ghcp"
    mode: Literal["expanded", "boss"] = "expanded"


app = FastAPI(title="AI Harness Dashboard API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    """Initialise PostgreSQL schema on startup. Warn but don't crash if DB is unavailable."""
    try:
        db.init_db()
        _restore_harness_runs_from_db()
    except Exception as exc:
        print(f"⚠️  DB unavailable on startup (continuing without persistence): {exc}")


def _find_root_dir() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "packages" / "ai-harness").exists() and (parent / "AINative_OKR_Claude_GHCP").exists():
            return parent
    return Path(__file__).resolve().parents[4]


ROOT_DIR = _find_root_dir()
HARNESS_PACKAGE_DIR = ROOT_DIR / "packages" / "ai-harness"
TARGETS = {
    "okr-ghcp": ROOT_DIR / "AINative_OKR_Claude_GHCP",
}
TARGET_CONFIGS = {
    ("okr-ghcp", "expanded"): str(HARNESS_PACKAGE_DIR / "targets" / "okr-ghcp" / "harness.okr.yaml"),
    ("okr-ghcp", "boss"): str(HARNESS_PACKAGE_DIR / "targets" / "okr-ghcp" / "harness.okr.boss.yaml"),
}
HARNESS_LOG_DIR = ROOT_DIR / ".run" / "harness-runs"
HARNESS_RUNS: dict[str, dict] = {}
HARNESS_PROCESSES: dict[str, asyncio.subprocess.Process] = {}


def _restore_harness_runs_from_db() -> None:
    """Re-populate in-memory HARNESS_RUNS from DB on server restart."""
    rows = db_logger.fetch_all_runs()
    for row in rows:
        run_id = row["run_id"]
        if run_id not in HARNESS_RUNS:
            HARNESS_RUNS[run_id] = {
                "id": run_id,
                "feature": row["feature"],
                "provider": row.get("provider", "codex"),
                "model": row.get("model", ""),
                "input_tokens": row.get("input_tokens", 0),
                "output_tokens": row.get("output_tokens", 0),
                "total_tokens": row.get("total_tokens", 0),
                "tech_stack": "",
                "target": row.get("target", "okr-ghcp"),
                "target_repo": row.get("target_repo", ""),
                "status": row.get("status", "unknown"),
                "created_at": row.get("created_at", 0.0),
                "started_at": row.get("started_at"),
                "finished_at": row.get("finished_at"),
                "pid": row.get("pid"),
                "return_code": row.get("return_code"),
                "command": row.get("command"),
                "log_path": row.get("log_path", ""),
            }
    if rows:
        print(f"✅ Restored {len(rows)} harness run(s) from database")



def _tail(path: Path, limit: int = 120) -> list[str]:
    try:
        lines = path.read_text(errors="ignore").splitlines()
    except OSError:
        return []
    return lines[-limit:]


def _config_agent_model(target_repo: Path, config_name: str) -> str:
    config_path = Path(config_name)
    if not config_path.is_absolute():
        config_path = target_repo / config_name
    try:
        import yaml
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return ""
    return str((raw.get("agent") or {}).get("model") or "")


def _phase_names(record: dict, state: dict) -> list[str]:
    # YAML config is authoritative for ordering — JSONB key order is not reliable
    # (PostgreSQL sorts JSONB keys by length then alpha, not insertion order).
    yaml_names: list[str] = []
    target_repo = Path(record["target_repo"])
    config_name = record.get("config") or TARGET_CONFIGS.get((record.get("target"), record.get("mode", "expanded")), "")
    config_path = Path(config_name)
    if not config_path.is_absolute():
        config_path = target_repo / config_name
    try:
        import yaml
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        yaml_names = [phase["name"] for phase in raw.get("phases", []) if "name" in phase]
    except Exception:
        pass
    # Start with YAML order, then append any state phases not in YAML (e.g. dynamic phases).
    names = list(yaml_names)
    for name in state.get("phases", {}).keys():
        if name not in set(names):
            names.append(name)
    return names


def _serialize_harness_run(run_id: str) -> dict:
    record = HARNESS_RUNS.get(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="Harness run not found")

    db_record = db_logger.fetch_run(run_id) or {}
    target_repo = Path(record["target_repo"])
    state = db_logger.fetch_run_state(run_id) or {}
    phases_raw = state.get("phases", {})
    phases = []
    for name in _phase_names(record, state):
        phase = phases_raw.get(name, {})
        phases.append({
            "name": name,
            "status": phase.get("status", "pending"),
            "gate": phase.get("gate"),
            "attempts": phase.get("attempts", 0),
            "failed_gates": phase.get("failed_gates", []),
        })

    status = record["status"]
    if state.get("status") == "complete":
        status = "complete"
    elif state.get("status") == "escalated":
        status = "escalated"

    return {
        **record,
        "status": status,
        "current_phase": state.get("current_phase"),
        "model": db_record.get("model", record.get("model", state.get("model", ""))),
        "cost_usd": state.get("cost_usd", db_record.get("cost_usd", 0.0)),
        "input_tokens": state.get("input_tokens", db_record.get("input_tokens", record.get("input_tokens", 0))),
        "output_tokens": state.get("output_tokens", db_record.get("output_tokens", record.get("output_tokens", 0))),
        "total_tokens": state.get("total_tokens", db_record.get("total_tokens", record.get("total_tokens", 0))),
        "phases": phases,
        "artifacts": db_logger.fetch_artifacts(run_id),
        "log_tail": db_logger.fetch_artifact_log_tail(run_id),
    }


async def _run_harness_process(run_id: str) -> None:
    record = HARNESS_RUNS[run_id]
    target_repo = Path(record["target_repo"])
    config = record.get("config") or TARGET_CONFIGS.get((record["target"], record.get("mode", "expanded")))
    if not config:
        record["status"] = "failed"
        record["finished_at"] = time.time()
        db_logger.log_run_updated(
            run_id,
            status="failed",
            finished_at=record["finished_at"],
            command="missing target harness config",
        )
        return
    log_path = Path(record["log_path"])
    HARNESS_LOG_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "cli",
        "run",
        "--feature",
        record["feature"],
        "--tech-stack",
        record["tech_stack"],
        "--repo",
        str(target_repo),
        "--config",
        config,
        "--provider",
        record["provider"],
        "--run-id",
        run_id,
    ]

    env = os.environ.copy()
    harness_src = str(ROOT_DIR / "packages" / "ai-harness" / "src")
    env["PYTHONPATH"] = harness_src + os.pathsep + env.get("PYTHONPATH", "")
    # Pass DB URL so harness subprocess can write events directly to PostgreSQL
    db_url = os.environ.get("DATABASE_URL", "")
    if db_url:
        env["HARNESS_DB_URL"] = db_url

    record["status"] = "running"
    record["command"] = " ".join(cmd)
    record["started_at"] = time.time()
    db_logger.log_run_updated(run_id,
                              status="running",
                              started_at=record["started_at"],
                              command=record["command"])

    with log_path.open("w", encoding="utf-8") as log:
        log.write(f"$ {' '.join(cmd)}\n\n")
        log.flush()
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(ROOT_DIR),
            env=env,
            stdout=log,
            stderr=asyncio.subprocess.STDOUT,
        )
        HARNESS_PROCESSES[run_id] = proc
        record["pid"] = proc.pid
        db_logger.log_run_updated(run_id, pid=proc.pid)
        return_code = await proc.wait()

    HARNESS_PROCESSES.pop(run_id, None)
    record["return_code"] = return_code
    record["finished_at"] = time.time()
    if record.get("status") != "stopped":
        record["status"] = "complete" if return_code == 0 else "failed"
    db_logger.log_run_updated(run_id,
                              return_code=return_code,
                              finished_at=record["finished_at"],
                              status=record["status"])


async def _stop_harness_process(run_id: str) -> None:
    proc = HARNESS_PROCESSES.get(run_id)
    if not proc or proc.returncode is not None:
        return
    proc.send_signal(signal.SIGTERM)
    try:
        await asyncio.wait_for(proc.wait(), timeout=8)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/harness-targets")
def harness_targets() -> dict:
    return {
        "targets": [
            {
                "id": target_id,
                "name": "AINative OKR Claude/GHCP",
                "path": str(path.relative_to(ROOT_DIR)),
                "providers": ["codex", "claude"],
                "modes": ["expanded", "boss"],
            }
            for target_id, path in TARGETS.items()
        ]
    }


@app.get("/api/harness-runs")
def list_harness_runs() -> dict:
    ordered = sorted(HARNESS_RUNS, key=lambda item: HARNESS_RUNS[item]["created_at"], reverse=True)
    return {"runs": [_serialize_harness_run(run_id) for run_id in ordered]}


@app.get("/api/harness-runs/latest")
def latest_harness_run() -> dict:
    if not HARNESS_RUNS:
        return {"run": None}
    run_id = max(HARNESS_RUNS, key=lambda item: HARNESS_RUNS[item]["created_at"])
    return {"run": _serialize_harness_run(run_id)}


@app.post("/api/harness-runs", status_code=201)
async def create_harness_run(payload: CreateHarnessRunRequest) -> dict:
    target_repo = TARGETS.get(payload.target)
    if not target_repo:
        raise HTTPException(status_code=404, detail="Harness target not registered")
    if not target_repo.exists():
        raise HTTPException(status_code=404, detail="Target project not found")

    run_id = f"ui-{uuid4().hex[:10]}"
    log_path = HARNESS_LOG_DIR / f"{run_id}.log"
    config = (
        TARGET_CONFIGS.get((payload.target, payload.mode))
        or TARGET_CONFIGS.get((payload.target, "expanded"))
    )
    if not config:
        raise HTTPException(status_code=400, detail="Harness config not registered for target/mode")
    record = {
        "id": run_id,
        "feature": payload.feature,
        "provider": payload.provider,
        "model": _config_agent_model(target_repo, config),
        "tech_stack": payload.tech_stack,
        "target": payload.target,
        "mode": payload.mode,
        "config": config,
        "target_repo": str(target_repo),
        "status": "queued",
        "created_at": time.time(),
        "started_at": None,
        "finished_at": None,
        "pid": None,
        "return_code": None,
        "command": None,
        "log_path": str(log_path),
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
    }
    HARNESS_RUNS[run_id] = record
    db_logger.log_run_created(record)
    asyncio.create_task(_run_harness_process(run_id))
    return _serialize_harness_run(run_id)


@app.get("/api/harness-runs/{run_id}")
def get_harness_run(run_id: str) -> dict:
    return _serialize_harness_run(run_id)


@app.post("/api/harness-runs/{run_id}/stop")
async def stop_harness_run(run_id: str) -> dict:
    if run_id not in HARNESS_RUNS:
        raise HTTPException(status_code=404, detail="Harness run not found")
    HARNESS_RUNS[run_id]["status"] = "stopped"
    await _stop_harness_process(run_id)
    HARNESS_RUNS[run_id]["finished_at"] = time.time()
    db_logger.log_run_updated(run_id, status="stopped",
                              finished_at=HARNESS_RUNS[run_id]["finished_at"])
    return _serialize_harness_run(run_id)


# ── New logging / observability endpoints ─────────────────────────────────────

@app.get("/api/harness-runs/{run_id}/events")
def get_run_events(
    run_id: str,
    limit: int = Query(default=200, ge=1, le=1000),
    after_id: int = Query(default=0, ge=0),
) -> dict:
    """Return structured audit-log events for a run, paginated by row id."""
    if run_id not in HARNESS_RUNS:
        raise HTTPException(status_code=404, detail="Harness run not found")
    events = db_logger.fetch_run_events(run_id, limit=limit, after_id=after_id)
    return {"run_id": run_id, "events": events, "count": len(events)}


@app.get("/api/harness-runs/{run_id}/gates")
def get_run_gates(run_id: str) -> dict:
    """Return all gate outcomes grouped by phase for a run."""
    if run_id not in HARNESS_RUNS:
        raise HTTPException(status_code=404, detail="Harness run not found")
    rows = db_logger.fetch_gate_outcomes(run_id)
    # Group by phase_name → attempt → list of gates
    grouped: dict = {}
    for row in rows:
        phase = row["phase_name"]
        attempt = row["attempt"]
        grouped.setdefault(phase, {}).setdefault(attempt, []).append(row)
    return {"run_id": run_id, "phases": grouped, "total": len(rows)}


@app.get("/api/harness-runs/{run_id}/phases")
def get_run_phases(run_id: str) -> dict:
    """Return phase event timeline with cost and latency per phase."""
    if run_id not in HARNESS_RUNS:
        raise HTTPException(status_code=404, detail="Harness run not found")
    rows = db_logger.fetch_phase_timeline(run_id)
    # Attach duration_sec for convenience
    for row in rows:
        if row.get("started_at") and row.get("finished_at"):
            row["duration_sec"] = round(row["finished_at"] - row["started_at"], 2)
        else:
            row["duration_sec"] = None
    return {"run_id": run_id, "phases": rows}


@app.get("/api/harness-runs/{run_id}/token-usage")
def get_run_token_usage(run_id: str) -> dict:
    """Return model/token usage grouped by phase, highest token usage first."""
    if run_id not in HARNESS_RUNS:
        raise HTTPException(status_code=404, detail="Harness run not found")
    rows = db_logger.fetch_phase_token_usage(run_id)
    return {"run_id": run_id, "phases": rows}


@app.get("/api/harness-runs/{run_id}/artifacts/{artifact_id}")
def get_artifact_content(run_id: str, artifact_id: str) -> dict:
    """Return a single artifact's full content."""
    if run_id not in HARNESS_RUNS:
        raise HTTPException(status_code=404, detail="Harness run not found")
    row = db_logger.fetch_artifact_content(artifact_id)
    if not row or str(row.get("run_id")) != run_id:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return {
        "id": row["id"],
        "artifact_type": row["artifact_type"],
        "name": row["name"],
        "content": row["content"] or "",
        "payload": row["payload"],
        "created_at": row["created_at"],
    }


@app.get("/api/harness-runs/{run_id}/log")
def get_run_log(
    run_id: str,
    lines: int = Query(default=200, ge=1, le=2000),
) -> dict:
    """Return the tail of the raw harness subprocess log file."""
    if run_id not in HARNESS_RUNS:
        raise HTTPException(status_code=404, detail="Harness run not found")
    record = HARNESS_RUNS[run_id]
    log_path = Path(record.get("log_path", ""))
    if not log_path.exists():
        return {"run_id": run_id, "lines": [], "available": False}
    tail = _tail(log_path, limit=lines)
    return {"run_id": run_id, "lines": tail, "available": True, "total": len(tail)}
