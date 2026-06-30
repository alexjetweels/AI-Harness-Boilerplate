"""Escalation policy for failed harness phases."""
import os
import subprocess

from agentops import db_logger
from agentops import state_store
from agentops import storage


def escalate(repo: str, run_id: str, state: dict, phase: str,
             feedback: str | None, state_dir: str) -> int:
    state["status"] = "escalated"
    state_store.save(state_dir, state)
    body = (f"# Escalation: {run_id}\n\n"
            f"Phase **{phase}** failed after the maximum number of attempts.\n\n"
            f"## Feature\n{state['feature']}\n\n"
            f"## Last gate report\n\n```\n{feedback or '(none)'}\n```\n")
    storage.save_artifact(run_id, "escalation", "ESCALATION.md", content=body)
    db_logger.run_escalated(run_id, phase, feedback or "(none)")
    print(f"\u26d4 Run {run_id} escalated at phase '{phase}'. Escalation saved in Postgres.")

    if os.environ.get("HARNESS_OPEN_ISSUE") == "1":
        try:
            subprocess.run(
                ["gh", "issue", "create",
                 "--title", f"[harness] {run_id} stuck at {phase}",
                 "--body", body],
                cwd=repo, check=False)
        except Exception:
            pass
    return 2
