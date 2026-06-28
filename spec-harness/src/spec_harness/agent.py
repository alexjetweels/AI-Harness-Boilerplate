"""Provider wrapper for headless coding agents.

Supported providers:
- claude: calls `claude -p --output-format json`
- codex: calls `codex exec --json`
"""
import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AgentResult:
    ok: bool
    text: str
    session_id: str | None
    cost: float
    raw: object


def run(agent_cfg, prompt: str, resume_session: str | None = None, cwd: str = ".") -> AgentResult:
    provider = (getattr(agent_cfg, "provider", "claude") or "claude").lower()
    if provider == "claude":
        return _run_claude(agent_cfg, prompt, resume_session=resume_session, cwd=cwd)
    if provider == "codex":
        return _run_codex(agent_cfg, prompt, resume_session=resume_session, cwd=cwd)
    return AgentResult(False, f"Unsupported agent provider: {provider}", None, 0.0, {})


def _agent_bin(agent_cfg, default: str) -> str:
    configured = getattr(agent_cfg, "bin", "") or ""
    # Existing configs default to `bin: claude`; do not force Codex users to
    # override it when they set `provider: codex`.
    if default == "codex" and configured == "claude":
        return "codex"
    return configured or default


def _run_claude(agent_cfg, prompt: str, resume_session: str | None = None, cwd: str = ".") -> AgentResult:
    argv = [
        _agent_bin(agent_cfg, "claude"), "-p", prompt,
        "--output-format", "json",
        "--max-turns", str(agent_cfg.max_turns),
        "--allowedTools", agent_cfg.allowed_tools,
    ]
    if getattr(agent_cfg, "model", ""):
        argv += ["--model", agent_cfg.model]
    if agent_cfg.max_budget_usd and agent_cfg.max_budget_usd > 0:
        argv += ["--max-budget-usd", str(agent_cfg.max_budget_usd)]
    if agent_cfg.skip_permissions:
        argv += ["--dangerously-skip-permissions"]
    if resume_session:
        argv += ["--resume", resume_session]
    argv += list(agent_cfg.extra_args)

    proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True)
    raw = (proc.stdout or "").strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Non-JSON output usually means the CLI errored before producing a result.
        return AgentResult(False, (proc.stdout or "") + "\n" + (proc.stderr or ""),
                           None, 0.0, raw)

    is_error = bool(data.get("is_error")) or proc.returncode != 0
    return AgentResult(
        ok=not is_error,
        text=data.get("result", ""),
        session_id=data.get("session_id"),
        cost=float(data.get("total_cost_usd", 0.0) or 0.0),
        raw=data,
    )


def _run_codex(agent_cfg, prompt: str, resume_session: str | None = None, cwd: str = ".") -> AgentResult:
    cwd_abs = os.path.abspath(cwd)
    expanded_prompt = _inline_project_command(prompt, cwd_abs)

    with tempfile.NamedTemporaryFile(prefix="codex-last-message-", suffix=".txt", delete=False) as fh:
        last_message_path = fh.name

    try:
        is_resume = bool(resume_session)
        if resume_session:
            argv = [
                _agent_bin(agent_cfg, "codex"), "exec", "resume",
                "--json",
                "--output-last-message", last_message_path,
                "--skip-git-repo-check",
            ]
            positional = [resume_session, expanded_prompt]
        else:
            argv = [
                _agent_bin(agent_cfg, "codex"), "exec",
                "--json",
                "--output-last-message", last_message_path,
                "--skip-git-repo-check",
                "--cd", cwd_abs,
            ]
            positional = [expanded_prompt]

        if getattr(agent_cfg, "model", "") and agent_cfg.model != "sonnet":
            argv += ["--model", agent_cfg.model]

        if getattr(agent_cfg, "skip_permissions", False):
            argv += ["--dangerously-bypass-approvals-and-sandbox"]
        elif not is_resume:
            argv += ["--ask-for-approval", "never", "--sandbox", "workspace-write"]

        argv += list(getattr(agent_cfg, "extra_args", []) or [])
        argv += positional

        proc = subprocess.run(argv, cwd=cwd_abs, capture_output=True, text=True)
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        last_message = _read_text(last_message_path)
        events = _parse_jsonl(stdout)
        session_id = _extract_session_id(events)
        cost = _extract_cost(events)

        ok = proc.returncode == 0
        text = last_message.strip() or _extract_final_text(events).strip() or stdout.strip()
        if not ok:
            text = (text + "\n" + stderr).strip()

        return AgentResult(ok, text, session_id, cost, {"events": events, "stderr": stderr})
    finally:
        try:
            os.unlink(last_message_path)
        except OSError:
            pass


def _read_text(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _parse_jsonl(text: str) -> list:
    events = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            events.append({"type": "raw", "text": line})
    return events


def _find_key(obj, keys: set[str]):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in keys and isinstance(value, (str, int, float)):
                return str(value)
        for value in obj.values():
            found = _find_key(value, keys)
            if found:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = _find_key(item, keys)
            if found:
                return found
    return None


def _extract_session_id(events: list) -> str | None:
    return _find_key(events, {"session_id", "sessionId", "conversation_id", "conversationId", "thread_id", "threadId"})


def _extract_cost(events: list) -> float:
    found = _find_key(events, {"total_cost_usd", "cost_usd", "costUsd"})
    try:
        return float(found or 0.0)
    except ValueError:
        return 0.0


def _extract_final_text(events: list) -> str:
    text_parts = []
    for event in events:
        found = _find_key(event, {"message", "text", "content", "final_output", "last_message"})
        if found:
            text_parts.append(found)
    return "\n".join(text_parts[-3:])


def _inline_project_command(prompt: str, cwd: str) -> str:
    """Inline `.claude/commands/*.md` for providers without Claude slash commands."""
    stripped = prompt.strip()
    if not stripped.startswith("/"):
        return prompt

    first, _, arguments = stripped.partition(" ")
    command_name = first[1:]
    command_path = Path(cwd) / ".claude" / "commands" / f"{command_name}.md"
    if not command_path.exists():
        return prompt

    body = command_path.read_text(encoding="utf-8", errors="ignore")
    body = _strip_frontmatter(body).replace("$ARGUMENTS", arguments.strip())
    return (
        f"Run the project command `{first}` using the instructions below.\n\n"
        f"Command arguments:\n{arguments.strip() or '(none)'}\n\n"
        f"{body.strip()}\n"
    )


def _strip_frontmatter(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return text
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "\n".join(lines[index + 1:]).lstrip()
    return text
