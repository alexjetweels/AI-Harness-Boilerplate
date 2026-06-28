"""The control loop: drive phases, run gates, repair-with-feedback, gate or escalate."""
import glob
import os
import subprocess

from . import agent as agent_mod
from . import gates as gates_mod
from . import state as state_mod


def _git_branch(repo: str) -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo, capture_output=True, text=True).stdout.strip()
    except Exception:
        return ""


def _discover_feature_dir(repo: str, specs_glob: str) -> str | None:
    """spec-kit creates specs/<branch>/ during /speckit.specify. Find it."""
    branch = _git_branch(repo)
    if branch:
        cand = os.path.join(repo, "specs", branch)
        if os.path.isdir(cand):
            return os.path.relpath(cand, repo)
    dirs = [d for d in glob.glob(os.path.join(repo, specs_glob)) if os.path.isdir(d)]
    if not dirs:
        return None
    return os.path.relpath(max(dirs, key=os.path.getmtime), repo)


def _expand(s: str, ctx: dict) -> str:
    for k, v in ctx.items():
        s = s.replace("{" + k + "}", str(v))
    return s


def _ctx_for(state: dict) -> dict:
    ctx = dict(state.get("ctx", {}))
    ctx["feature"] = state["feature"]
    ctx["repo"] = "."
    if state.get("feature_dir"):
        ctx["feature_dir"] = state["feature_dir"]
    return ctx


def _write_log(runs_dir: str, run_id: str, fname: str, content: str) -> None:
    d = os.path.join(runs_dir, run_id)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, fname), "w") as f:
        f.write(content)


def run(cfg, feature: str, run_id: str, repo: str = ".",
        resume: bool = False, ctx_extra: dict | None = None) -> int:
    state_dir = os.path.join(repo, cfg.state_dir)
    runs_dir = os.path.join(repo, cfg.runs_dir)

    if resume:
        state = state_mod.load(state_dir, run_id)
    else:
        ctx = {"feature": feature}
        if ctx_extra:
            ctx.update(ctx_extra)
        state = state_mod.new_run(state_dir, run_id, feature, ctx)

    for phase in cfg.phases:
        if state["phases"].get(phase.name, {}).get("status") == "done":
            continue

        # Skip phases whose artifact already exists (e.g. constitution).
        if phase.skip_if_exists and glob.glob(os.path.join(repo, phase.skip_if_exists)):
            state["phases"][phase.name] = {"status": "done", "gate": "skipped", "attempts": 0}
            state_mod.save(state_dir, state)
            continue

        state["current_phase"] = phase.name
        feedback = None
        session = None
        passed = False

        for attempt in range(1, phase.max_attempts + 1):
            agent_text = ""

            if phase.command:
                if attempt == 1:
                    prompt = _expand(phase.command, _ctx_for(state))
                    res = agent_mod.run(cfg.agent, prompt, cwd=repo)
                else:
                    # Repair: resume the same session, hand back the failure report.
                    prompt = ("The previous attempt did not pass verification. "
                              "Fix the following issues, then stop:\n\n" + (feedback or ""))
                    res = agent_mod.run(cfg.agent, prompt, resume_session=session, cwd=repo)

                session = res.session_id or session
                state["cost_usd"] = round(state["cost_usd"] + res.cost, 4)
                agent_text = res.text
                _write_log(runs_dir, run_id, f"{phase.name}.attempt{attempt}.log",
                           f"PROMPT:\n{prompt}\n\nOK={res.ok} COST=${res.cost}\n\nRESULT:\n{res.text}")

                if not res.ok:
                    feedback = f"Agent reported an error:\n{(res.text or '')[-3000:]}"
                    state["phases"][phase.name] = {
                        "status": "failed", "gate": "agent_error", "attempts": attempt}
                    state_mod.save(state_dir, state)
                    continue

            # The /speckit.specify run creates specs/<branch>/ — discover it now.
            if not state.get("feature_dir"):
                fd = _discover_feature_dir(repo, cfg.specs_glob)
                if fd:
                    state["feature_dir"] = fd

            outcomes = gates_mod.run_gates(phase, _ctx_for(state), repo, agent_text=agent_text)
            failed = [o for o in outcomes if not o.passed]
            report = "\n\n".join(o.report for o in failed if o.report)
            _write_log(runs_dir, run_id, f"{phase.name}.attempt{attempt}.gates.log",
                       report or "ALL GATES PASSED")

            state["phases"][phase.name] = {
                "status": "done" if not failed else "failed",
                "gate": "pass" if not failed else "fail",
                "attempts": attempt,
                "failed_gates": [o.name for o in failed],
            }
            state_mod.save(state_dir, state)

            if not failed:
                passed = True
                break

            feedback = report
            if not phase.command:
                break  # gate-only phase has no agent to self-repair

        if not passed:
            return _escalate(repo, runs_dir, run_id, state, phase.name, feedback, state_dir)

    state["status"] = "complete"
    state["current_phase"] = None
    state_mod.save(state_dir, state)
    print(f"\u2705 Run {run_id} complete. Cost ~${state['cost_usd']}. "
          f"Feature dir: {state.get('feature_dir')}")
    return 0


def _escalate(repo, runs_dir, run_id, state, phase, feedback, state_dir) -> int:
    state["status"] = "escalated"
    state_mod.save(state_dir, state)
    body = (f"# Escalation: {run_id}\n\n"
            f"Phase **{phase}** failed after the maximum number of attempts.\n\n"
            f"## Feature\n{state['feature']}\n\n"
            f"## Last gate report\n\n```\n{feedback or '(none)'}\n```\n")
    _write_log(runs_dir, run_id, "ESCALATION.md", body)
    print(f"\u26d4 Run {run_id} escalated at phase '{phase}'. "
          f"See {os.path.join(runs_dir, run_id, 'ESCALATION.md')}")

    if os.environ.get("HARNESS_OPEN_ISSUE") == "1":
        try:
            subprocess.run(
                ["gh", "issue", "create",
                 "--title", f"[harness] {run_id} stuck at {phase}",
                 "--body-file", os.path.join(runs_dir, run_id, "ESCALATION.md")],
                cwd=repo, check=False)
        except Exception:
            pass
    return 2
