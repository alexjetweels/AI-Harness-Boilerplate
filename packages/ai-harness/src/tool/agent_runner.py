"""Provider wrapper for headless coding agents.

Supported providers:
- claude: calls `claude -p --output-format json`
- codex: calls `codex exec --json`
"""
import json
import os
import re
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


def run(agent_cfg, prompt: str, resume_session: str | None = None, cwd: str = ".",
        run_id: str | None = None, phase_name: str | None = None) -> AgentResult:
    provider = (getattr(agent_cfg, "provider", "claude") or "claude").lower()
    if provider == "claude":
        return _run_claude(agent_cfg, prompt, resume_session=resume_session, cwd=cwd,
                           run_id=run_id, phase_name=phase_name)
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


def _run_claude(agent_cfg, prompt: str, resume_session: str | None = None, cwd: str = ".",
                run_id: str | None = None, phase_name: str | None = None) -> AgentResult:
    argv = [
        _agent_bin(agent_cfg, "claude"), "-p", prompt,
        "--output-format", "stream-json",
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

    try:
        proc = subprocess.Popen(
            argv, cwd=cwd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1,
        )
    except FileNotFoundError:
        return AgentResult(False, f"claude binary not found: {argv[0]}", None, 0.0, {})

    lines: list[str] = []
    session_id: str | None = None
    result_text = ""
    cost = 0.0
    is_error = False

    # Import db_logger lazily so pure-CLI mode (no DB) still works.
    _db: object = None
    if run_id:
        try:
            from agentops import db_logger as _db_mod  # type: ignore
            _db = _db_mod
        except ImportError:
            pass

    for raw_line in proc.stdout:  # type: ignore[union-attr]
        line = raw_line.rstrip("\n\r")
        if not line:
            continue
        lines.append(line)
        # Echo to harness stdout so it lands in the backend log file.
        print(line, flush=True)

        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            if _db and run_id:
                try:
                    _db._emit(run_id, "claude_raw", phase_name, line[:500])  # type: ignore[union-attr]
                except Exception:
                    pass
            continue

        etype = event.get("type", "")
        if not session_id:
            session_id = event.get("session_id")

        if etype == "result":
            is_error = bool(event.get("is_error", False))
            result_text = event.get("result", "")
            cost = float(event.get("total_cost_usd", 0.0) or 0.0)

        if _db and run_id:
            try:
                _db.log_stream_event(run_id, phase_name, event)  # type: ignore[union-attr]
            except Exception:
                pass

    proc.wait()
    stderr_text = (proc.stderr.read() if proc.stderr else "").strip()  # type: ignore[union-attr]

    # Fallback: if stream-json gave no result event, try to parse stdout as plain JSON.
    if not result_text and lines:
        try:
            fallback = json.loads(lines[-1])
            if "result" in fallback:
                is_error = bool(fallback.get("is_error", False))
                result_text = fallback.get("result", "")
                cost = float(fallback.get("total_cost_usd", 0.0) or 0.0)
                session_id = session_id or fallback.get("session_id")
        except json.JSONDecodeError:
            pass

    if proc.returncode != 0 and not result_text:
        is_error = True
        result_text = stderr_text or "\n".join(lines[-20:])

    return AgentResult(
        ok=not is_error and proc.returncode == 0,
        text=result_text,
        session_id=session_id,
        cost=cost,
        raw={"lines_count": len(lines), "returncode": proc.returncode},
    )


def _run_codex(agent_cfg, prompt: str, resume_session: str | None = None, cwd: str = ".") -> AgentResult:
    cwd_abs = os.path.abspath(cwd)
    expanded_prompt = _inline_project_command(prompt, cwd_abs, agent_cfg)

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


def _inline_project_command(prompt: str, cwd: str, agent_cfg=None) -> str:
    """Inline command and agent prompts for providers without native slash commands."""
    stripped = prompt.strip()
    if not stripped.startswith("/"):
        return prompt

    match = re.match(r"^/(\S+)(?:\s+([\s\S]*))?$", stripped)
    if not match:
        return prompt
    command_name = match.group(1)
    first = f"/{command_name}"
    arguments = match.group(2) or ""
    command_path = _find_prompt_file(
        command_name,
        cwd,
        agent_cfg,
        key="command_dirs",
        default_dirs=[".claude/commands"],
        suffixes=[".md"],
    )
    if not command_path:
        return prompt

    body = command_path.read_text(encoding="utf-8", errors="ignore")
    body = _strip_frontmatter(body).replace("$ARGUMENTS", arguments.strip())
    agent_name = _extract_agent_name(body)
    agent_definition = _agent_definition(agent_name, cwd, agent_cfg) if agent_name else ""
    agent_block = (
        "\n\n# Resolved Agent Definition\n\n"
        f"Use this agent definition as the role and operating protocol for `{agent_name}`.\n\n"
        f"{agent_definition.strip()}\n"
        if agent_definition else ""
    )
    return (
        f"Run the project command `{first}` using the instructions below.\n\n"
        f"Command arguments:\n{arguments.strip() or '(none)'}\n\n"
        f"{body.strip()}\n"
        f"{agent_block}"
    )


def _configured_dirs(agent_cfg, key: str, cwd: str, default_dirs: list[str]) -> list[Path]:
    dirs = [Path(cwd) / item for item in default_dirs]
    prompt_pack = getattr(agent_cfg, "prompt_pack", {}) or {}
    config_dir = Path(getattr(agent_cfg, "config_dir", "") or cwd)
    for item in prompt_pack.get(key, []) or []:
        if isinstance(item, str) and item.startswith("target:"):
            dirs.append(Path(cwd) / item[len("target:"):])
            continue
        path = Path(item)
        dirs.append(path if path.is_absolute() else config_dir / path)
    return dirs


def _find_prompt_file(name: str, cwd: str, agent_cfg, key: str,
                      default_dirs: list[str], suffixes: list[str]) -> Path | None:
    for directory in _configured_dirs(agent_cfg, key, cwd, default_dirs):
        for suffix in suffixes:
            candidate = directory / f"{name}{suffix}"
            if candidate.exists():
                return candidate
    return None


def _extract_agent_name(command_body: str) -> str | None:
    patterns = [
        r"Use the \*\*([^*]+)\*\* agent",
        r"`subagent_type`:\s*\"([^\"]+)\"",
        r"subagent_type[\"']?\s*:\s*[\"']([^\"']+)[\"']",
    ]
    for pattern in patterns:
        match = re.search(pattern, command_body)
        if match:
            return match.group(1).strip()
    return None


def _agent_definition(agent_name: str, cwd: str, agent_cfg) -> str:
    path = _find_prompt_file(
        agent_name,
        cwd,
        agent_cfg,
        key="agent_dirs",
        default_dirs=[".claude/agents", ".github/agents"],
        suffixes=[".md", ".agent.md"],
    )
    if not path:
        return ""
    return _strip_frontmatter(path.read_text(encoding="utf-8", errors="ignore"))


def _strip_frontmatter(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return text
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "\n".join(lines[index + 1:]).lstrip()
    return text
