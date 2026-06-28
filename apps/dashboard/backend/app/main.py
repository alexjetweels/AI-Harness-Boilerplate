from __future__ import annotations

import asyncio
import json
import os
import random
import signal
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import db
from . import db_logger


HarnessKind = Literal[
    "context",
    "tool",
    "evaluation",
    "security",
    "governance",
    "agentops",
    "orchestration",
]


@dataclass
class HarnessComponent:
    id: str
    code: str
    kind: HarnessKind
    name: str
    coverage: int
    status: Literal["strong", "good", "gap", "critical"]
    summary: str
    gaps: list[str]
    color: str


@dataclass
class Stage:
    id: str
    label: str
    state: Literal["done", "current", "pending", "failed", "blocked", "warning"]
    owner: HarnessKind


@dataclass
class Lane:
    id: str
    title: str
    harness: HarnessKind
    status: Literal["running", "complete", "needs_you", "idle", "blocked"]
    progress: int
    current_stage: str
    branch: str
    checks: list[str]
    cost_usd: float
    hallucination_risk: Literal["low", "medium", "high"]
    updated_at: float
    log: list[str] = field(default_factory=list)


@dataclass
class Run:
    id: str
    feature: str
    status: Literal["running", "complete", "blocked"]
    created_at: float
    lanes: list[Lane]


class CreateRunRequest(BaseModel):
    feature: str = Field(..., min_length=3, max_length=240)
    tech_stack: str = Field(default="React + FastAPI + Docker", max_length=240)


class CreateHarnessRunRequest(BaseModel):
    feature: str = Field(..., min_length=3, max_length=500)
    provider: Literal["claude", "codex"] = "codex"
    tech_stack: str = Field(default="Node.js CLI demo target", max_length=240)
    target: Literal["todo-app"] = "todo-app"


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


RUNS: dict[str, Run] = {}


def _find_root_dir() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "packages" / "ai-harness").exists() and (parent / "examples").exists():
            return parent
    return Path(__file__).resolve().parents[4]


ROOT_DIR = _find_root_dir()
TARGETS = {
    "todo-app": ROOT_DIR / "examples" / "todo-app",
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
                "tech_stack": row.get("tech_stack", ""),
                "target": row.get("target", "todo-app"),
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



def _lane(
    index: int,
    title: str,
    harness: HarnessKind,
    status: Literal["running", "complete", "needs_you", "idle", "blocked"],
    progress: int,
) -> Lane:
    branch_slug = title.lower().replace(" ", "-").replace("/", "-")[:36]
    now = time.time()
    return Lane(
        id=f"lane-{index}",
        title=title,
        harness=harness,
        status=status,
        progress=progress,
        current_stage="gates" if status == "running" else "review",
        branch=f"feat/{branch_slug}",
        checks=["api", "fe", "docker", "eval"],
        cost_usd=round(random.uniform(0.04, 0.8), 2),
        hallucination_risk=random.choice(["low", "low", "medium"]),
        updated_at=now,
        log=[
            "context packet assembled",
            "tool schema validation passed",
            "evaluation gate waiting for latest agent output",
        ],
    )


def _default_lanes(feature: str) -> list[Lane]:
    return [
        _lane(1, feature, "context", "running", 48),
        _lane(2, "Tool registry and Docker command chain", "tool", "running", 32),
        _lane(3, "Golden-case evaluation and judge gates", "evaluation", "complete", 100),
        _lane(4, "Prompt injection and credential audit", "security", "needs_you", 18),
        _lane(5, "Approval workflow and risk registry", "governance", "idle", 10),
        _lane(6, "Per-agent cost, drift, and trace metrics", "agentops", "running", 44),
        _lane(7, "DAG orchestration and repair loop", "orchestration", "complete", 100),
    ]


def _serialize_run(run: Run) -> dict:
    return {
        **asdict(run),
        "lane_count": len(run.lanes),
        "running_count": sum(1 for lane in run.lanes if lane.status == "running"),
        "needs_you_count": sum(1 for lane in run.lanes if lane.status in {"needs_you", "blocked"}),
    }


def _phase_names() -> list[str]:
    return [
        "intake",
        "requirements",
        "architecture",
        "plan",
        "tasks",
        "implement",
        "review",
        "test",
        "security",
        "docs",
        "release",
    ]


def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _tail(path: Path, limit: int = 120) -> list[str]:
    try:
        lines = path.read_text(errors="ignore").splitlines()
    except OSError:
        return []
    return lines[-limit:]


def _artifact_summary(target_repo: Path) -> list[dict]:
    artifact_dir = target_repo / "docs" / "sdlc" / "current"
    if not artifact_dir.exists():
        return []
    items = []
    for path in sorted(artifact_dir.glob("*.md")):
        try:
            stat = path.stat()
        except OSError:
            continue
        items.append({
            "name": path.name,
            "path": str(path.relative_to(target_repo)),
            "size": stat.st_size,
            "updated_at": stat.st_mtime,
        })
    return items


def _serialize_harness_run(run_id: str) -> dict:
    record = HARNESS_RUNS.get(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="Harness run not found")

    target_repo = Path(record["target_repo"])
    state = _read_json(target_repo / ".specify" / "state" / f"{run_id}.json") or {}
    phases_raw = state.get("phases", {})
    phases = []
    for name in _phase_names():
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
        "cost_usd": state.get("cost_usd", 0.0),
        "phases": phases,
        "artifacts": _artifact_summary(target_repo),
        "log_tail": _tail(Path(record["log_path"])),
    }


async def _run_harness_process(run_id: str) -> None:
    record = HARNESS_RUNS[run_id]
    target_repo = Path(record["target_repo"])
    provider = record["provider"]
    config = "harness.codex.yaml" if provider == "codex" else "harness.yaml"
    log_path = Path(record["log_path"])
    HARNESS_LOG_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "spec_harness",
        "run",
        "--feature",
        record["feature"],
        "--tech-stack",
        record["tech_stack"],
        "--repo",
        str(target_repo),
        "--config",
        config,
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


def _latest_run() -> Run:
    if not RUNS:
        run_id = f"demo-{uuid4().hex[:8]}"
        RUNS[run_id] = Run(
            id=run_id,
            feature="Predefined criteria: free-text and protocol-ref rules",
            status="running",
            created_at=time.time(),
            lanes=_default_lanes("Predefined criteria: free-text and protocol-ref rules"),
        )
    return max(RUNS.values(), key=lambda item: item.created_at)


async def _simulate_run(run_id: str) -> None:
    while run_id in RUNS:
        run = RUNS[run_id]
        if run.status != "running":
            return

        active_lanes = [lane for lane in run.lanes if lane.status == "running"]
        if not active_lanes:
            run.status = "complete"
            return

        for lane in active_lanes:
            lane.progress = min(100, lane.progress + random.randint(3, 9))
            lane.cost_usd = round(lane.cost_usd + random.uniform(0.01, 0.06), 2)
            lane.updated_at = time.time()
            lane.log.append(f"{lane.current_stage} advanced to {lane.progress}%")
            if len(lane.log) > 8:
                lane.log = lane.log[-8:]
            if lane.progress >= 100:
                lane.status = "complete"
                lane.current_stage = "ship"
                lane.log.append("lane complete: gates green")

        await asyncio.sleep(3)


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/runs")
def runs() -> dict:
    _latest_run()
    ordered = sorted(RUNS.values(), key=lambda item: item.created_at, reverse=True)
    return {"runs": [_serialize_run(run) for run in ordered]}


@app.post("/api/runs", status_code=201)
async def create_run(payload: CreateRunRequest) -> dict:
    run_id = f"run-{uuid4().hex[:10]}"
    run = Run(
        id=run_id,
        feature=payload.feature,
        status="running",
        created_at=time.time(),
        lanes=_default_lanes(payload.feature),
    )
    RUNS[run_id] = run
    asyncio.create_task(_simulate_run(run_id))
    return _serialize_run(run)


@app.get("/api/runs/{run_id}")
def get_run(run_id: str) -> dict:
    run = RUNS.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return _serialize_run(run)


@app.get("/api/harness-targets")
def harness_targets() -> dict:
    return {
        "targets": [
            {
                "id": "todo-app",
                "name": "Todo App Demo",
                "path": str(TARGETS["todo-app"].relative_to(ROOT_DIR)),
                "providers": ["codex", "claude"],
            }
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
    target_repo = TARGETS[payload.target]
    if not target_repo.exists():
        raise HTTPException(status_code=404, detail="Target project not found")

    run_id = f"ui-{uuid4().hex[:10]}"
    log_path = HARNESS_LOG_DIR / f"{run_id}.log"
    record = {
        "id": run_id,
        "feature": payload.feature,
        "provider": payload.provider,
        "tech_stack": payload.tech_stack,
        "target": payload.target,
        "target_repo": str(target_repo),
        "status": "queued",
        "created_at": time.time(),
        "started_at": None,
        "finished_at": None,
        "pid": None,
        "return_code": None,
        "command": None,
        "log_path": str(log_path),
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
