"""The control loop: drive phases, run gates, repair-with-feedback, gate or escalate."""
import glob
import os
import subprocess

from agentops import db_logger
from agentops import state_store
from agentops import storage
from context import builder as context_builder
from evaluation import gates as gates_mod
from governance.escalation import escalate
from tool import agent_runner


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


def _write_artifact(run_id: str, artifact_type: str, name: str, content: str) -> None:
    storage.save_artifact(run_id, artifact_type, name, content=content)


def _inject_context(prompt: str, state: dict, attempt: int) -> str:
    if attempt != 1:
        # Repair retries resume the same agent session, which already saw
        # the context packet on attempt 1 — re-pasting it here would just
        # duplicate that content in every repair prompt for no benefit.
        return prompt

    ctx = state.get("ctx", {})
    packet_path = ctx.get("context_packet")
    if packet_path and not str(packet_path).startswith("db://"):
        return (
            "The harness context packet for this run is available at "
            f"`{packet_path}`. Read that file with your Read tool first and use it "
            "as the authoritative run context. Do not read unrelated files unless "
            "the phase instructions require it.\n\n"
            "# Phase Prompt\n\n"
            f"{prompt}"
        )

    content = ctx.get("context_packet_content")
    if not content:
        return prompt
    return (
        "Use the controlled harness context below as the authoritative run context. "
        "Do not read unrelated files unless the phase instructions require it.\n\n"
        f"{content}\n\n"
        "# Phase Prompt\n\n"
        f"{prompt}"
    )


def run(cfg, feature: str, run_id: str, repo: str = ".",
        resume: bool = False, ctx_extra: dict | None = None) -> int:  # noqa: C901
    state_dir = os.path.join(repo, cfg.state_dir)

    if resume:
        state = state_store.load(state_dir, run_id)
    else:
        ctx = {"feature": feature}
        if ctx_extra:
            ctx.update(ctx_extra)
        ctx.update(context_builder.build(repo, run_id, feature, getattr(cfg, "context", {})))
        state = state_store.new_run(state_dir, run_id, feature, ctx)

    state["provider"] = getattr(cfg.agent, "provider", "")
    state["model"] = getattr(cfg.agent, "model", "") or state.get("model", "")
    state.setdefault("input_tokens", 0)
    state.setdefault("output_tokens", 0)
    state.setdefault("total_tokens", 0)

    if resume:
        # A resume (e.g. a dashboard retry) is re-entering after a failed/
        # escalated attempt — reflect that immediately so status readers
        # don't keep showing the stale terminal status while it runs.
        state["status"] = "running"
        state_store.save(state_dir, state)

    for phase in cfg.phases:
        if state["phases"].get(phase.name, {}).get("status") == "done":
            continue

        # Skip phases whose artifact already exists (e.g. constitution).
        if phase.skip_if_exists and glob.glob(os.path.join(repo, phase.skip_if_exists)):
            state["phases"][phase.name] = {"status": "done", "gate": "skipped", "attempts": 0}
            state_store.save(state_dir, state)
            continue

        state["current_phase"] = phase.name
        feedback = None
        session = None
        passed = False

        for attempt in range(1, phase.max_attempts + 1):
            db_logger.phase_started(run_id, phase.name, attempt)
            agent_text = ""

            if phase.command:
                if attempt == 1:
                    prompt = _expand(phase.command, _ctx_for(state))
                    res = agent_runner.run(cfg.agent, _inject_context(prompt, state, attempt), cwd=repo,
                                          run_id=run_id, phase_name=phase.name)
                else:
                    # Repair: resume the same session, hand back the failure report.
                    prompt = ("The previous attempt did not pass verification. "
                              "Fix the following issues, then stop:\n\n" + (feedback or ""))
                    res = agent_runner.run(cfg.agent, _inject_context(prompt, state, attempt),
                                          resume_session=session, cwd=repo,
                                          run_id=run_id, phase_name=phase.name)

                session = res.session_id or session
                state["cost_usd"] = round(state["cost_usd"] + res.cost, 4)
                state["model"] = res.model or state.get("model", "")
                state["input_tokens"] = int(state.get("input_tokens", 0) or 0) + res.input_tokens
                state["output_tokens"] = int(state.get("output_tokens", 0) or 0) + res.output_tokens
                state["total_tokens"] = int(state.get("total_tokens", 0) or 0) + res.total_tokens
                agent_text = res.text
                _write_artifact(
                    run_id,
                    "phase_log",
                    f"{phase.name}.attempt{attempt}",
                    f"PROMPT:\n{prompt}\n\nOK={res.ok} COST=${res.cost}\n\nRESULT:\n{res.text}",
                )

                if not res.ok:
                    feedback = f"Agent reported an error:\n{(res.text or '')[-3000:]}"
                    state["phases"][phase.name] = {
                        "status": "failed", "gate": "agent_error", "attempts": attempt}
                    state_store.save(state_dir, state)
                    db_logger.phase_done(run_id, phase.name, attempt,
                                        "failed", "agent_error",
                                        agent_ok=False, cost_usd=res.cost,
                                        model=res.model or state.get("model", ""),
                                        input_tokens=res.input_tokens,
                                        output_tokens=res.output_tokens,
                                        total_tokens=res.total_tokens)
                    continue

            # The /speckit.specify run creates specs/<branch>/ — discover it now.
            if not state.get("feature_dir"):
                fd = _discover_feature_dir(repo, cfg.specs_glob)
                if fd:
                    state["feature_dir"] = fd

            outcomes = gates_mod.run_gates(phase, _ctx_for(state), repo, agent_text=agent_text)
            failed = [o for o in outcomes if not o.passed]
            report = "\n\n".join(o.report for o in failed if o.report)
            _write_artifact(
                run_id,
                "gate_log",
                f"{phase.name}.attempt{attempt}.gates",
                report or "ALL GATES PASSED",
            )

            # ── Log each gate outcome to DB ──────────────────────────────────
            for o in outcomes:
                db_logger.gate_outcome(
                    run_id, phase.name, attempt,
                    o.name, getattr(o, "type", ""),
                    o.passed, o.report,
                )

            gate_result = "pass" if not failed else "fail"
            state["phases"][phase.name] = {
                "status": "done" if not failed else "failed",
                "gate": gate_result,
                "attempts": attempt,
                "failed_gates": [o.name for o in failed],
            }
            state_store.save(state_dir, state)

            # Determine agent_ok from last agent call (None if gate-only phase)
            _agent_ok = res.ok if phase.command else None  # type: ignore[name-defined]
            db_logger.phase_done(run_id, phase.name, attempt,
                                 "done" if not failed else "failed",
                                 gate_result,
                                 agent_ok=_agent_ok,
                                 cost_usd=res.cost if phase.command else 0.0,  # type: ignore[name-defined]
                                 model=(res.model or state.get("model", "")) if phase.command else state.get("model", ""),  # type: ignore[name-defined]
                                 input_tokens=res.input_tokens if phase.command else 0,  # type: ignore[name-defined]
                                 output_tokens=res.output_tokens if phase.command else 0,  # type: ignore[name-defined]
                                 total_tokens=res.total_tokens if phase.command else 0)  # type: ignore[name-defined]

            if not failed:
                passed = True
                break

            feedback = report
            if not phase.command:
                break  # gate-only phase has no agent to self-repair

        if not passed:
            return escalate(repo, run_id, state, phase.name, feedback, state_dir)

    state["status"] = "complete"
    state["current_phase"] = None
    state_store.save(state_dir, state)
    db_logger.run_complete(run_id, state["cost_usd"])
    print(f"\u2705 Run {run_id} complete. Cost ~${state['cost_usd']}. "
          f"Feature dir: {state.get('feature_dir')}")
    return 0
