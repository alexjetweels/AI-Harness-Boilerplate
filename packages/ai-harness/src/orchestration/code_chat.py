"""Copilot-style code chat workflow managed by the harness.

Flow:
intake/clarify -> plan -> generate full-file changes -> apply -> validate -> repair.
"""
from __future__ import annotations

import asyncio
import difflib
import json
import os
import ssl
import sys
import time
from pathlib import Path
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError
from uuid import uuid4

try:
    import certifi
except Exception:  # pragma: no cover
    certifi = None


ALLOWED_PREFIXES = (
    "frontend/",
    "backend/",
    "apps/frontend/",
    "apps/backend/",
)


class CodeChatError(Exception):
    pass


def _now() -> float:
    return time.time()


def _load_dotenv(repo: Path) -> None:
    env_path = repo.parent / ".env"
    if not env_path.exists():
        env_path = repo / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def _safe_path(repo: Path, rel_path: str) -> Path:
    normalized = rel_path.replace("\\", "/").lstrip("/")
    if not normalized or normalized.endswith("/"):
        raise CodeChatError(f"Invalid file path: {rel_path}")
    if ".." in Path(normalized).parts:
        raise CodeChatError(f"Path traversal is not allowed: {rel_path}")
    if not any(normalized.startswith(prefix) for prefix in ALLOWED_PREFIXES):
        raise CodeChatError(f"Path must be under frontend/backend folders: {rel_path}")
    absolute = (repo / normalized).resolve()
    try:
        absolute.relative_to(repo.resolve())
    except ValueError as exc:
        raise CodeChatError(f"Path escapes target project: {rel_path}") from exc
    return absolute


def _normalize_requested_files(repo: Path, files: list[dict]) -> list[dict]:
    normalized = []
    for file in files or []:
        path = str(file.get("path", "")).replace("\\", "/").lstrip("/")
        _safe_path(repo, path)
        normalized.append({
            "path": path,
            "action": file.get("action") or "create",
            "instructions": str(file.get("instructions") or "").strip(),
            "content": str(file.get("content") or ""),
        })
    return normalized


def _tree(repo: Path, limit: int = 120) -> list[str]:
    paths = []
    for prefix in ALLOWED_PREFIXES:
        base = repo / prefix
        if not base.exists():
            paths.append(f"{prefix.rstrip('/')}/ (missing)")
            continue
        for path in sorted(base.rglob("*")):
            if len(paths) >= limit:
                paths.append("... truncated")
                return paths
            if path.is_file():
                paths.append(str(path.relative_to(repo)))
    return paths


def _extract_json_object(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise CodeChatError("DeepSeek response did not include a JSON object")
        return json.loads(text[start:end + 1])


def _api_key(repo: Path) -> str:
    _load_dotenv(repo)
    return os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""


async def _call_deepseek(repo: Path, messages: list[dict], model: str) -> dict:
    api_key = _api_key(repo)
    if not api_key:
        raise CodeChatError("Missing DEEPSEEK_API_KEY in environment")

    payload = json.dumps({
        "model": model or "deepseek-v4-flash",
        "messages": messages,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")
    req = urlrequest.Request(
        "https://api.deepseek.com/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )

    def send() -> dict:
        try:
            context = ssl.create_default_context(cafile=certifi.where()) if certifi else ssl.create_default_context()
            with urlrequest.urlopen(req, timeout=90, context=context) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")[:800]
            raise CodeChatError(f"DeepSeek API {exc.code}: {detail}") from exc
        except URLError as exc:
            raise CodeChatError(f"DeepSeek API unavailable: {exc.reason}") from exc
        data = json.loads(raw)
        return _extract_json_object(data["choices"][0]["message"]["content"])

    return await asyncio.to_thread(send)


def _system_prompt(repo: Path) -> str:
    return (
        "You are a coding agent managed by an SDLC harness. Return only JSON. "
        f"You may only change files inside: {', '.join(ALLOWED_PREFIXES)}. "
        "Generated source must be runnable. For new React frontend apps, use a minimal "
        "Vite React shape: package.json with build script, index.html, src/main.jsx, "
        "src/App.jsx, and src/styles.css. Do not create isolated components unless the "
        "existing app imports them or the user explicitly asks for a standalone component. "
        "If product type, framework, routes, data model, styling, or run command is unclear, "
        "ask concise clarification questions before generating code. "
        f"Target project root: {repo.name}."
    )


async def _intake(repo: Path, prompt: str, model: str, requested_files: list[dict]) -> dict:
    raw = await _call_deepseek(repo, [
        {"role": "system", "content": _system_prompt(repo)},
        {"role": "user", "content": (
            "Analyze whether this request has enough information to generate runnable code. "
            "Respond as JSON with: needs_clarification boolean, reasoning_summary string, "
            "assumptions array, questions array, project_type string, recommended_stack string."
            f"\n\nAllowed tree:\n{chr(10).join(_tree(repo)) or '(empty)'}"
            f"\n\nExplicit file requests:\n{json.dumps(requested_files, ensure_ascii=False)}"
            f"\n\nUser request:\n{prompt}"
        )},
    ], model)
    questions = [str(item) for item in raw.get("questions", [])][:5]
    return {
        "needs_clarification": bool(raw.get("needs_clarification")) and bool(questions),
        "reasoning_summary": str(raw.get("reasoning_summary") or ""),
        "assumptions": [str(item) for item in raw.get("assumptions", [])][:8],
        "questions": questions,
        "project_type": str(raw.get("project_type") or ""),
        "recommended_stack": str(raw.get("recommended_stack") or ""),
    }


async def _plan(repo: Path, prompt: str, model: str, requested_files: list[dict], intake: dict) -> dict:
    raw = await _call_deepseek(repo, [
        {"role": "system", "content": _system_prompt(repo)},
        {"role": "user", "content": (
            "Create an implementation plan. Respond as JSON with summary string, "
            "steps array, files array. The plan must result in runnable code."
            f"\n\nAllowed tree:\n{chr(10).join(_tree(repo)) or '(empty)'}"
            f"\n\nExplicit file requests:\n{json.dumps(requested_files, ensure_ascii=False)}"
            f"\n\nIntake:\n{json.dumps(intake, ensure_ascii=False)}"
            f"\n\nUser request:\n{prompt}"
        )},
    ], model)
    return {
        "summary": str(raw.get("summary") or "Prepare source changes"),
        "steps": [str(item) for item in raw.get("steps", [])][:8],
        "files": [str(item).replace("\\", "/").lstrip("/") for item in raw.get("files", [])][:30],
    }


def _normalize_changes(repo: Path, changes: list[dict], requested_files: list[dict] | None = None) -> list[dict]:
    normalized = []
    for item in changes:
        path = str(item.get("path") or "").replace("\\", "/").lstrip("/")
        action = str(item.get("action") or "update").lower()
        if action not in {"create", "update", "delete"}:
            raise CodeChatError(f"Unsupported file action: {action}")
        _safe_path(repo, path)
        content = "" if action == "delete" else str(item.get("content") or "")
        if action != "delete" and not content:
            raise CodeChatError(f"Missing content for {path}")
        normalized.append({"path": path, "action": action, "content": content})

    for requested in requested_files or []:
        if not requested.get("content"):
            continue
        matching = next((item for item in normalized if item["path"] == requested["path"]), None)
        if matching:
            matching["action"] = requested.get("action") or "create"
            matching["content"] = requested["content"]
        else:
            normalized.append({
                "path": requested["path"],
                "action": requested.get("action") or "create",
                "content": requested["content"],
            })

    expected = {item["path"] for item in requested_files or []}
    actual = {item["path"] for item in normalized}
    missing = sorted(expected - actual)
    if missing:
        raise CodeChatError(f"DeepSeek missed explicit file request(s): {', '.join(missing)}")
    return normalized


async def _changes(repo: Path, session: dict) -> list[dict]:
    raw = await _call_deepseek(repo, [
        {"role": "system", "content": _system_prompt(repo)},
        {"role": "user", "content": (
            "Generate full-file source changes. Respond as JSON with key changes, where "
            "changes is [{path, action:create|update|delete, content}]. Every explicit file "
            "request must appear exactly. For new React apps include runnable Vite skeleton."
            f"\n\nAllowed tree:\n{chr(10).join(_tree(repo)) or '(empty)'}"
            f"\n\nExplicit file requests:\n{json.dumps(session.get('requested_files', []), ensure_ascii=False)}"
            f"\n\nIntake:\n{json.dumps(session.get('intake', {}), ensure_ascii=False)}"
            f"\n\nPlan:\n{json.dumps(session.get('plan', {}), ensure_ascii=False)}"
            f"\n\nUser request:\n{session['prompt']}"
        )},
    ], session.get("model", "deepseek-v4-flash"))
    raw_changes = raw.get("changes", [])
    if not isinstance(raw_changes, list) or not raw_changes:
        raise CodeChatError("DeepSeek did not return any file changes")
    return _normalize_changes(repo, raw_changes, session.get("requested_files", []))


def _diff(repo: Path, changes: list[dict]) -> str:
    chunks = []
    for change in changes:
        path = _safe_path(repo, change["path"])
        before = path.read_text(encoding="utf-8", errors="ignore").splitlines() if path.exists() else []
        after = [] if change["action"] == "delete" else str(change["content"]).splitlines()
        chunks.append("\n".join(difflib.unified_diff(
            before, after, fromfile=f"a/{change['path']}", tofile=f"b/{change['path']}", lineterm="")))
    return "\n\n".join(chunk for chunk in chunks if chunk).strip()


def _apply(repo: Path, changes: list[dict]) -> list[str]:
    applied = []
    for change in changes:
        path = _safe_path(repo, change["path"])
        if change["action"] == "delete":
            if path.exists():
                path.unlink()
                applied.append(change["path"])
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(change["content"]), encoding="utf-8")
        applied.append(change["path"])
    return applied


async def _run_command(cmd: list[str], cwd: Path, timeout: int = 45) -> dict:
    started = _now()
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, cwd=str(cwd), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return_code = proc.returncode
        except asyncio.TimeoutError:
            proc.kill()
            stdout, _ = await proc.communicate()
            return_code = 124
    except FileNotFoundError as exc:
        return {"command": " ".join(cmd), "cwd": str(cwd), "return_code": 127,
                "duration_sec": round(_now() - started, 2), "output": str(exc)}
    return {"command": " ".join(cmd), "cwd": str(cwd), "return_code": return_code,
            "duration_sec": round(_now() - started, 2),
            "output": stdout.decode("utf-8", errors="ignore")[-8000:]}


def _package_command(project_dir: Path) -> list[str] | None:
    package_json = project_dir / "package.json"
    if not package_json.exists():
        return None
    try:
        scripts = (json.loads(package_json.read_text(encoding="utf-8")).get("scripts") or {})
    except Exception:
        scripts = {}
    if "build" in scripts:
        return ["npm", "run", "build"]
    if "test" in scripts:
        return ["npm", "test", "--", "--runInBand"]
    return None


def _validation_commands(repo: Path, applied_files: list[str]) -> list[tuple[list[str], Path, str]]:
    commands = []
    seen = set()
    for rel_path in applied_files:
        path = _safe_path(repo, rel_path)
        parts = Path(rel_path).parts
        if len(parts) >= 1 and parts[0] in {"frontend", "backend"}:
            project_dir = repo / parts[0]
        elif len(parts) >= 2 and parts[0] == "apps" and parts[1] in {"frontend", "backend"}:
            project_dir = repo / "apps" / parts[1]
        else:
            project_dir = path.parent
        suffix = path.suffix.lower()
        command = None
        label = "syntax"
        if suffix == ".py":
            command = [sys.executable, "-m", "py_compile", str(path)]
            label = "python compile"
        elif suffix in {".js", ".jsx", ".ts", ".tsx", ".json", ".css", ".html"}:
            command = _package_command(project_dir)
            label = "npm build" if command and command[:3] == ["npm", "run", "build"] else "npm check"
        if command:
            if command[0] == "npm" and (project_dir / "package.json").exists() and not (project_dir / "node_modules").exists():
                key = ("npm install --ignore-scripts", str(project_dir))
                if key not in seen:
                    seen.add(key)
                    commands.append((["npm", "install", "--ignore-scripts"], project_dir, "npm install"))
            key = (" ".join(command), str(project_dir))
            if key not in seen:
                seen.add(key)
                commands.append((command, project_dir, label))
    return commands


async def _validate(repo: Path, applied_files: list[str]) -> dict:
    commands = _validation_commands(repo, applied_files)
    if not commands:
        return {"status": "skipped", "summary": "No runnable project check was found.", "checks": []}
    checks = []
    for command, cwd, label in commands:
        timeout = 120 if label == "npm install" else 60 if command[:2] == ["npm", "run"] else 45
        checks.append({**await _run_command(command, cwd, timeout=timeout), "label": label})
    failed = [check for check in checks if check["return_code"] != 0]
    return {"status": "fail" if failed else "pass",
            "summary": f"{len(failed)} of {len(checks)} check(s) failed." if failed else f"{len(checks)} check(s) passed.",
            "checks": checks}


async def _repair(repo: Path, session: dict, validation: dict) -> list[dict]:
    failed_logs = "\n\n".join(
        f"$ {check['command']}\n{check.get('output', '')}"
        for check in validation.get("checks", []) if check.get("return_code") != 0)
    raw = await _call_deepseek(repo, [
        {"role": "system", "content": _system_prompt(repo)},
        {"role": "user", "content": (
            "The generated code failed validation. Return repair JSON only: "
            "{\"changes\":[{\"path\":\"...\",\"action\":\"update\",\"content\":\"full file\"}]}."
            f"\n\nOriginal request:\n{session['prompt']}"
            f"\n\nPlan:\n{json.dumps(session.get('plan', {}), ensure_ascii=False)}"
            f"\n\nCurrent changes:\n{json.dumps(session.get('changes', []), ensure_ascii=False)[:12000]}"
            f"\n\nValidation logs:\n{failed_logs[-8000:]}"
        )},
    ], session.get("model", "deepseek-v4-flash"))
    changes = raw.get("changes", [])
    if not isinstance(changes, list) or not changes:
        raise CodeChatError("DeepSeek did not return repair changes")
    return _normalize_changes(repo, changes, [])


def _emit(emit, session: dict) -> None:
    if emit:
        emit(json.loads(json.dumps(session, ensure_ascii=False)))


async def run(payload: dict, repo: str, emit=None) -> dict:
    target_repo = Path(repo).resolve()
    model = payload.get("model") or "deepseek-v4-flash"
    requested_files = _normalize_requested_files(target_repo, payload.get("requested_files") or [])
    session = {
        "id": payload.get("session_id") or f"chat-{uuid4().hex[:10]}",
        "target": payload.get("target", "okr-ghcp"),
        "target_repo": str(target_repo),
        "prompt": str(payload["prompt"]),
        "model": model,
        "requested_files": requested_files,
        "auto_apply": bool(payload.get("auto_apply", True)),
        "status": "planning",
        "intake": None,
        "reasoning_summary": "",
        "assumptions": [],
        "clarification": None,
        "plan": None,
        "changes": [],
        "diff": "",
        "applied_files": [],
        "validation": None,
        "repair_attempts": [],
        "approvals": [],
        "error": "",
        "created_at": _now(),
        "updated_at": _now(),
    }
    try:
        _emit(emit, session)
        intake = await _intake(target_repo, session["prompt"], model, requested_files)
        session.update({
            "intake": intake,
            "reasoning_summary": intake.get("reasoning_summary", ""),
            "assumptions": intake.get("assumptions", []),
            "updated_at": _now(),
        })
        _emit(emit, session)
        if intake.get("needs_clarification") and not any(file.get("content") for file in requested_files):
            session.update({"status": "clarification_needed",
                            "clarification": {"questions": intake.get("questions", []),
                                              "project_type": intake.get("project_type", ""),
                                              "recommended_stack": intake.get("recommended_stack", "")},
                            "updated_at": _now()})
            _emit(emit, session)
            return session

        plan = await _plan(target_repo, session["prompt"], model, requested_files, intake)
        session.update({"plan": plan, "status": "generating_changes", "updated_at": _now()})
        _emit(emit, session)
        if not session["auto_apply"]:
            session["status"] = "plan_pending"
            session["updated_at"] = _now()
            _emit(emit, session)
            return session

        changes = await _changes(target_repo, session)
        diff = _diff(target_repo, changes)
        applied = _apply(target_repo, changes)
        session.update({"changes": changes, "diff": diff, "applied_files": applied,
                        "status": "validating", "updated_at": _now(),
                        "approvals": [{"stage": "plan", "approved": True, "by": "harness", "at": _now()},
                                      {"stage": "changes", "approved": True, "by": "harness", "at": _now()}]})
        _emit(emit, session)

        validation = await _validate(target_repo, applied)
        all_changes = list(changes)
        all_applied = list(applied)
        combined_diff = diff
        repairs = []
        for attempt in range(int(payload.get("max_repair_attempts", 1))):
            if validation["status"] != "fail":
                break
            session.update({"status": "repairing", "validation": validation, "updated_at": _now()})
            _emit(emit, session)
            repair_changes = await _repair(target_repo, session, validation)
            repair_diff = _diff(target_repo, repair_changes)
            repair_applied = _apply(target_repo, repair_changes)
            repair_validation = await _validate(target_repo, repair_applied)
            repairs.append({"attempt": attempt + 1, "changes": repair_changes,
                            "applied_files": repair_applied, "diff": repair_diff,
                            "validation": repair_validation})
            all_changes.extend(repair_changes)
            all_applied.extend(file for file in repair_applied if file not in all_applied)
            combined_diff = "\n\n".join(
                part for part in [combined_diff, f"--- repair attempt {attempt + 1} ---\n{repair_diff}"] if part)
            validation = repair_validation
            session.update({"changes": all_changes, "diff": combined_diff,
                            "applied_files": all_applied, "repair_attempts": repairs,
                            "validation": validation, "updated_at": _now()})
            _emit(emit, session)

        session.update({
            "status": "verified" if validation["status"] == "pass" else "applied" if validation["status"] == "skipped" else "needs_fix",
            "changes": all_changes,
            "diff": combined_diff,
            "applied_files": all_applied,
            "validation": validation,
            "repair_attempts": repairs,
            "updated_at": _now(),
        })
        _emit(emit, session)
        return session
    except Exception as exc:
        session.update({"status": "failed", "error": str(exc), "updated_at": _now()})
        _emit(emit, session)
        return session


def run_sync(payload: dict, repo: str) -> dict:
    return asyncio.run(run(payload, repo))
