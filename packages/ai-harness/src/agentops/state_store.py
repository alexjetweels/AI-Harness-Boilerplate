"""Per-run state manifest backed by Postgres."""
import time

from agentops import storage


def new_run(state_dir: str, run_id: str, feature: str, ctx: dict) -> dict:
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
    return storage.load_state(run_id)


def save(state_dir: str, state: dict) -> None:
    storage.save_state(state)
