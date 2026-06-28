"""Per-run state manifest: durable, resumable, auditable."""
import json
import os
import time


def _path(state_dir: str, run_id: str) -> str:
    return os.path.join(state_dir, f"{run_id}.json")


def new_run(state_dir: str, run_id: str, feature: str, ctx: dict) -> dict:
    os.makedirs(state_dir, exist_ok=True)
    state = {
        "run_id": run_id,
        "feature": feature,
        "ctx": ctx,                 # template vars for slash commands (tech_stack, constitution, ...)
        "status": "running",        # running | complete | escalated
        "current_phase": None,
        "feature_dir": None,        # specs/NNN-* discovered after /speckit.specify
        "phases": {},               # name -> {status, gate, attempts, failed_gates}
        "cost_usd": 0.0,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    save(state_dir, state)
    return state


def load(state_dir: str, run_id: str) -> dict:
    with open(_path(state_dir, run_id)) as f:
        return json.load(f)


def save(state_dir: str, state: dict) -> None:
    os.makedirs(state_dir, exist_ok=True)
    tmp = _path(state_dir, state["run_id"]) + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, _path(state_dir, state["run_id"]))
