"""Quality gates run after each phase. Mostly deterministic (no LLM)."""
import glob
import os
import subprocess
from dataclasses import dataclass


@dataclass
class GateOutcome:
    name: str
    passed: bool
    report: str          # human/agent-readable failure detail; "" when passed


def _expand(s: str, ctx: dict) -> str:
    """Replace {feature_dir}, {feature}, {repo} runtime placeholders."""
    for k, v in ctx.items():
        s = s.replace("{" + k + "}", str(v))
    return s


def _shell(cmd: str, cwd: str):
    p = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    out = ((p.stdout or "") + (p.stderr or "")).strip()
    return p.returncode == 0, out


def run_gates(phase, ctx: dict, repo: str, agent_text: str = "") -> list[GateOutcome]:
    outcomes: list[GateOutcome] = []

    for g in phase.gates:
        if g.type == "shell":
            cmd = _expand(g.params["cmd"], ctx)
            ok, out = _shell(cmd, repo)
            outcomes.append(GateOutcome(
                g.name, ok,
                "" if ok else f"[{g.name}] command failed: {cmd}\n{out[-4000:]}"))

        elif g.type == "glob_nonempty":
            pat = _expand(g.params["glob"], ctx)
            matches = glob.glob(os.path.join(repo, pat), recursive=True)
            ok = len(matches) > 0
            outcomes.append(GateOutcome(
                g.name, ok,
                "" if ok else f"[{g.name}] expected at least one file matching: {pat}"))

        elif g.type == "no_markers":
            pat = _expand(g.params["glob"], ctx)
            markers = g.params["markers"]
            hits = []
            for f in glob.glob(os.path.join(repo, pat), recursive=True):
                try:
                    with open(f, encoding="utf-8", errors="ignore") as fh:
                        for i, line in enumerate(fh, 1):
                            for m in markers:
                                if m in line:
                                    hits.append(f"{os.path.relpath(f, repo)}:{i}: {m}")
                except OSError:
                    pass
            ok = not hits
            outcomes.append(GateOutcome(
                g.name, ok,
                "" if ok else f"[{g.name}] forbidden markers still present:\n" + "\n".join(hits[:50])))

        elif g.type == "agent_output":
            markers = g.params.get("fail_markers", [])
            text = (agent_text or "").lower()
            found = [m for m in markers if m.lower() in text]
            ok = not found
            outcomes.append(GateOutcome(
                g.name, ok,
                "" if ok else (f"[{g.name}] analysis flagged: {', '.join(found)}\n"
                               f"Report:\n{(agent_text or '')[-4000:]}")))

        else:
            outcomes.append(GateOutcome(g.name, False, f"[{g.name}] unknown gate type: {g.type}"))

    return outcomes
