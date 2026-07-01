from __future__ import annotations

import asyncio
import difflib
import json
import os
import re
import signal
import ssl
import sys
import time
from pathlib import Path
from typing import Literal
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from . import db
from . import db_logger

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional in local shells
    load_dotenv = None

try:
    import certifi
except Exception:  # pragma: no cover - falls back to system CA store
    certifi = None


DocType = Literal["requirement", "change-request", "architecture"]


class CreateHarnessRunRequest(BaseModel):
    feature: str = Field(..., min_length=3, max_length=500)
    provider: Literal["claude", "codex"] = "codex"
    tech_stack: str = Field(default="", max_length=240)
    target: Literal["okr-ghcp"] = "okr-ghcp"
    mode: Literal["expanded", "boss"] = "expanded"
    # IDs returned by POST /api/file-extractions for files uploaded before
    # this run existed — their content gets written into the target repo
    # synchronously before the harness subprocess starts (see create_harness_run).
    extraction_ids: list[int] = Field(default_factory=list, max_length=20)


class RetryHarnessRunRequest(BaseModel):
    provider: Literal["claude", "codex"] | None = None


class RequestedFileSpec(BaseModel):
    path: str = Field(..., min_length=3, max_length=240)
    action: Literal["create", "update"] = "create"
    instructions: str = Field(default="", max_length=2000)
    content: str = Field(default="", max_length=20000)


class CreateCopilotSessionRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=4000)
    target: Literal["okr-ghcp"] = "okr-ghcp"
    model: str = Field(default="deepseek-v4-flash", max_length=80)
    requested_files: list[RequestedFileSpec] = Field(default_factory=list, max_length=10)
    auto_apply: bool = True
    max_repair_attempts: int = Field(default=1, ge=0, le=3)


class CopilotApprovalRequest(BaseModel):
    stage: Literal["plan", "changes"]
    approved: bool = True


class CopilotRejectRequest(BaseModel):
    reason: str = Field(default="", max_length=500)


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
    if load_dotenv:
        load_dotenv(ROOT_DIR / ".env")
        load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    try:
        db.init_db()
        _restore_harness_runs_from_db()
    except Exception as exc:
        print(f"⚠️  DB unavailable on startup (continuing without persistence): {exc}")


def _find_root_dir() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "packages" / "ai-harness").exists() and (parent / "AINative_OKR_Claude_GHCP").exists():
            return parent
    return Path(__file__).resolve().parents[4]


ROOT_DIR = _find_root_dir()
HARNESS_PACKAGE_DIR = ROOT_DIR / "packages" / "ai-harness"
TARGETS = {
    "okr-ghcp": ROOT_DIR / "AINative_OKR_Claude_GHCP",
}
TARGET_CONFIGS = {
    ("okr-ghcp", "expanded"): str(HARNESS_PACKAGE_DIR / "targets" / "okr-ghcp" / "harness.okr.yaml"),
    ("okr-ghcp", "boss"): str(HARNESS_PACKAGE_DIR / "targets" / "okr-ghcp" / "harness.okr.boss.yaml"),
}
HARNESS_LOG_DIR = ROOT_DIR / ".run" / "harness-runs"
HARNESS_RUNS: dict[str, dict] = {}
HARNESS_PROCESSES: dict[str, asyncio.subprocess.Process] = {}
COPILOT_SESSIONS: dict[str, dict] = {}
COPILOT_TERMINAL_STATUSES = {
    "clarification_needed",
    "verified",
    "applied",
    "needs_fix",
    "failed",
    "rejected",
}
COPILOT_ALLOWED_PREFIXES = (
    "frontend/",
    "backend/",
    "apps/frontend/",
    "apps/backend/",
)


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
                "model": row.get("model", ""),
                "input_tokens": row.get("input_tokens", 0),
                "output_tokens": row.get("output_tokens", 0),
                "total_tokens": row.get("total_tokens", 0),
                "tech_stack": "",
                "target": row.get("target", "okr-ghcp"),
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



def _tail(path: Path, limit: int = 120) -> list[str]:
    try:
        lines = path.read_text(errors="ignore").splitlines()
    except OSError:
        return []
    return lines[-limit:]


def _now() -> float:
    return time.time()


def _mark_copilot_session(session: dict, **updates) -> dict:
    session.update(updates)
    session["updated_at"] = _now()
    return session


def _target_root(target: str) -> Path:
    target_repo = TARGETS.get(target)
    if not target_repo:
        raise HTTPException(status_code=404, detail="Target project not registered")
    if not target_repo.exists():
        raise HTTPException(status_code=404, detail="Target project not found")
    return target_repo


def _safe_target_path(target_repo: Path, rel_path: str) -> Path:
    normalized = rel_path.replace("\\", "/").lstrip("/")
    if not normalized or normalized.endswith("/"):
        raise HTTPException(status_code=400, detail=f"Invalid file path: {rel_path}")
    if ".." in Path(normalized).parts:
        raise HTTPException(status_code=400, detail=f"Path traversal is not allowed: {rel_path}")
    if not any(normalized.startswith(prefix) for prefix in COPILOT_ALLOWED_PREFIXES):
        raise HTTPException(
            status_code=400,
            detail=f"Path must be under frontend/backend folders: {rel_path}",
        )
    absolute = (target_repo / normalized).resolve()
    try:
        absolute.relative_to(target_repo.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Path escapes target project: {rel_path}")
    return absolute


def _normalize_requested_files(target_repo: Path, files: list[RequestedFileSpec]) -> list[dict]:
    normalized: list[dict] = []
    for file in files:
        path = file.path.replace("\\", "/").lstrip("/")
        _safe_target_path(target_repo, path)
        normalized.append({
            "path": path,
            "action": file.action,
            "instructions": file.instructions.strip(),
            "content": file.content,
        })
    return normalized


def _list_allowed_tree(target_repo: Path, limit: int = 120) -> list[str]:
    paths: list[str] = []
    for prefix in COPILOT_ALLOWED_PREFIXES:
        base = target_repo / prefix
        if not base.exists():
            paths.append(f"{prefix.rstrip('/')}/ (missing)")
            continue
        for path in sorted(base.rglob("*")):
            if len(paths) >= limit:
                paths.append("... truncated")
                return paths
            if path.is_file():
                paths.append(str(path.relative_to(target_repo)))
    return paths


def _extract_json_object(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("DeepSeek response did not include a JSON object")
        return json.loads(text[start:end + 1])


def _deepseek_api_key() -> str:
    if load_dotenv:
        load_dotenv(ROOT_DIR / ".env", override=False)
        load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    return os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""


async def _call_deepseek(messages: list[dict], model: str = "deepseek-v4-flash") -> dict:
    api_key = _deepseek_api_key()
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="Missing DEEPSEEK_API_KEY in .env or process environment",
        )

    payload = json.dumps({
        "model": model or "deepseek-v4-flash",
        "messages": messages,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")
    req = urlrequest.Request(
        "https://api.deepseek.com/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    def send() -> dict:
        try:
            context = (
                ssl.create_default_context(cafile=certifi.where())
                if certifi
                else ssl.create_default_context()
            )
            with urlrequest.urlopen(req, timeout=90, context=context) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")[:800]
            raise RuntimeError(f"DeepSeek API {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"DeepSeek API unavailable: {exc.reason}") from exc
        data = json.loads(raw)
        content = data["choices"][0]["message"]["content"]
        return _extract_json_object(content)

    try:
        return await asyncio.to_thread(send)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=502, detail=f"Invalid DeepSeek response: {exc}")


def _copilot_system_prompt(target_repo: Path) -> str:
    return (
        "You are a coding agent for a demo Copilot-like dashboard. "
        "Return only valid JSON. Do not include markdown. "
        "You may only propose source changes inside these target project folders: "
        f"{', '.join(COPILOT_ALLOWED_PREFIXES)}. "
        "The frontend/backend folders may not exist yet; create them when needed. "
        "Generated source should be runnable. If a requested frontend/backend project lacks "
        "package.json, pyproject.toml, or minimal entry/config files required by the generated code, "
        "include those files in the changes so validation commands can run. "
        "For React frontend work, prefer a minimal Vite React project shape: package.json with "
        "a build script, index.html, src/main.jsx, src/App.jsx, and src/styles.css. "
        "Do not create isolated React component files unless the existing tree already has a React app "
        "that imports them, or unless the user explicitly asks only for a component. "
        "If the product type, framework, routes, data model, styling preference, or run command is unclear, "
        "ask concise clarification questions before generating code. "
        f"Target project root: {target_repo.name}."
    )


async def _create_copilot_intake(
    prompt: str,
    target_repo: Path,
    model: str,
    requested_files: list[dict],
) -> dict:
    tree = "\n".join(_list_allowed_tree(target_repo))
    messages = [
        {"role": "system", "content": _copilot_system_prompt(target_repo)},
        {
            "role": "user",
            "content": (
                "Analyze whether this request has enough information to generate runnable code. "
                "Respond as JSON with keys: needs_clarification (boolean), reasoning_summary (string), "
                "assumptions (array of strings), questions (array of strings), project_type (string), "
                "recommended_stack (string). "
                "Ask questions when requirements are vague, when a whole app is requested without target "
                "pages/features, or when the framework/project shape is unclear. "
                "Do not ask questions for a simple uploaded file apply unless the destination is ambiguous."
                f"\n\nAllowed tree:\n{tree or '(no allowed folders yet)'}"
                f"\n\nExplicit file requests:\n{json.dumps(requested_files, ensure_ascii=False)}"
                f"\n\nUser request:\n{prompt}"
            ),
        },
    ]
    raw = await _call_deepseek(messages, model=model)
    questions = [str(item) for item in raw.get("questions", [])][:5]
    return {
        "needs_clarification": bool(raw.get("needs_clarification")) and bool(questions),
        "reasoning_summary": str(raw.get("reasoning_summary") or ""),
        "assumptions": [str(item) for item in raw.get("assumptions", [])][:8],
        "questions": questions,
        "project_type": str(raw.get("project_type") or ""),
        "recommended_stack": str(raw.get("recommended_stack") or ""),
    }


async def _create_copilot_plan(
    prompt: str,
    target_repo: Path,
    model: str,
    requested_files: list[dict],
    intake: dict | None = None,
) -> dict:
    tree = "\n".join(_list_allowed_tree(target_repo))
    messages = [
        {"role": "system", "content": _copilot_system_prompt(target_repo)},
        {
            "role": "user",
            "content": (
                "Create an implementation plan for this user request. "
                "Respond as JSON with keys: summary (string), steps (array of strings), "
                "files (array of relative paths you expect to create or edit). "
                f"\n\nAllowed tree:\n{tree or '(no allowed folders yet)'}"
                f"\n\nExplicit file requests:\n{json.dumps(requested_files, ensure_ascii=False)}"
                f"\n\nIntake analysis:\n{json.dumps(intake or {}, ensure_ascii=False)}"
                f"\n\nUser request:\n{prompt}"
            ),
        },
    ]
    plan = await _call_deepseek(messages, model=model)
    return {
        "summary": str(plan.get("summary") or "Prepare source changes"),
        "steps": [str(item) for item in plan.get("steps", [])][:8],
        "files": [str(item).replace("\\", "/").lstrip("/") for item in plan.get("files", [])][:20],
    }


async def _create_copilot_changes(session: dict, target_repo: Path) -> list[dict]:
    tree = "\n".join(_list_allowed_tree(target_repo))
    requested_files = session.get("requested_files", [])
    messages = [
        {"role": "system", "content": _copilot_system_prompt(target_repo)},
        {
            "role": "user",
            "content": (
                "Generate the file changes for the approved plan. "
                "Respond as JSON with key changes. changes must be an array of objects: "
                "{path: relative file path, action: create|update|delete, content: full file content for create/update}. "
                "Use complete file contents, not patches. Keep the change small and demo-ready. "
                "Every explicit file request must appear in changes using the exact requested path."
                "For new React frontend apps, generate a complete Vite React skeleton with package.json, "
                "index.html, src/main.jsx, src/App.jsx, and src/styles.css so npm run build can pass."
                f"\n\nAllowed tree:\n{tree or '(no allowed folders yet)'}"
                f"\n\nExplicit file requests:\n{json.dumps(requested_files, ensure_ascii=False)}"
                f"\n\nIntake analysis:\n{json.dumps(session.get('intake', {}), ensure_ascii=False)}"
                f"\n\nApproved plan:\n{json.dumps(session.get('plan', {}), ensure_ascii=False)}"
                f"\n\nUser request:\n{session['prompt']}"
            ),
        },
    ]
    raw = await _call_deepseek(messages, model=session.get("model", "deepseek-v4-flash"))
    changes = raw.get("changes", [])
    if not isinstance(changes, list) or not changes:
        raise HTTPException(status_code=502, detail="DeepSeek did not return any file changes")

    normalized = []
    for item in changes:
        path = str(item.get("path") or "").replace("\\", "/").lstrip("/")
        action = str(item.get("action") or "update").lower()
        if action not in {"create", "update", "delete"}:
            raise HTTPException(status_code=400, detail=f"Unsupported file action: {action}")
        _safe_target_path(target_repo, path)
        content = "" if action == "delete" else str(item.get("content") or "")
        if action != "delete" and not content:
            raise HTTPException(status_code=400, detail=f"Missing content for {path}")
        normalized.append({"path": path, "action": action, "content": content})
    for requested in requested_files:
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

    expected_paths = {item["path"] for item in requested_files}
    actual_paths = {item["path"] for item in normalized}
    missing = sorted(expected_paths - actual_paths)
    if missing:
        raise HTTPException(
            status_code=502,
            detail=f"DeepSeek missed explicit file request(s): {', '.join(missing)}",
        )
    return normalized


def _build_changes_diff(target_repo: Path, changes: list[dict]) -> str:
    chunks: list[str] = []
    for change in changes:
        path = _safe_target_path(target_repo, change["path"])
        before = path.read_text(encoding="utf-8", errors="ignore").splitlines() if path.exists() else []
        after = [] if change["action"] == "delete" else str(change["content"]).splitlines()
        diff_lines = difflib.unified_diff(
            before,
            after,
            fromfile=f"a/{change['path']}",
            tofile=f"b/{change['path']}",
            lineterm="",
        )
        chunks.append("\n".join(diff_lines))
    return "\n\n".join(chunk for chunk in chunks if chunk).strip()


def _apply_copilot_changes(target_repo: Path, changes: list[dict]) -> list[str]:
    applied: list[str] = []
    for change in changes:
        path = _safe_target_path(target_repo, change["path"])
        if change["action"] == "delete":
            if path.exists():
                path.unlink()
                applied.append(change["path"])
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(change["content"]), encoding="utf-8")
        applied.append(change["path"])
    return applied


async def _run_copilot_command(cmd: list[str], cwd: Path, timeout: int = 45) -> dict:
    started_at = _now()
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(cwd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return_code = proc.returncode
        except asyncio.TimeoutError:
            proc.kill()
            stdout, _ = await proc.communicate()
            return_code = 124
    except FileNotFoundError as exc:
        return {
            "command": " ".join(cmd),
            "cwd": str(cwd),
            "return_code": 127,
            "duration_sec": round(_now() - started_at, 2),
            "output": str(exc),
        }

    output = stdout.decode("utf-8", errors="ignore")
    return {
        "command": " ".join(cmd),
        "cwd": str(cwd),
        "return_code": return_code,
        "duration_sec": round(_now() - started_at, 2),
        "output": output[-8000:],
    }


def _package_build_command(project_dir: Path) -> list[str] | None:
    package_json = project_dir / "package.json"
    if not package_json.exists():
        return None
    try:
        raw = json.loads(package_json.read_text(encoding="utf-8"))
    except Exception:
        return ["npm", "run", "build"]
    scripts = raw.get("scripts") or {}
    if "build" in scripts:
        return ["npm", "run", "build"]
    if "test" in scripts:
        return ["npm", "test", "--", "--runInBand"]
    return None


def _validation_commands(target_repo: Path, applied_files: list[str]) -> list[tuple[list[str], Path, str]]:
    commands: list[tuple[list[str], Path, str]] = []
    seen: set[tuple[str, str]] = set()

    for rel_path in applied_files:
        path = _safe_target_path(target_repo, rel_path)
        parts = Path(rel_path).parts

        if len(parts) >= 1 and parts[0] in {"frontend", "backend"}:
            project_dir = target_repo / parts[0]
        elif len(parts) >= 2 and parts[0] == "apps" and parts[1] in {"frontend", "backend"}:
            project_dir = target_repo / "apps" / parts[1]
        else:
            project_dir = path.parent

        suffix = path.suffix.lower()
        command: list[str] | None = None
        label = "syntax"

        if suffix == ".py":
            command = [sys.executable, "-m", "py_compile", str(path)]
            label = "python compile"
        elif suffix in {".js", ".jsx", ".ts", ".tsx", ".json", ".css", ".html"}:
            command = _package_build_command(project_dir)
            label = "npm build" if command and command[:3] == ["npm", "run", "build"] else "npm check"

        if command:
            if command[0] == "npm" and (project_dir / "package.json").exists() and not (project_dir / "node_modules").exists():
                install_key = ("npm install --ignore-scripts", str(project_dir))
                if install_key not in seen:
                    seen.add(install_key)
                    commands.append((["npm", "install", "--ignore-scripts"], project_dir, "npm install"))
            key = (" ".join(command), str(project_dir))
            if key not in seen:
                seen.add(key)
                commands.append((command, project_dir, label))

    return commands


async def _validate_copilot_changes(target_repo: Path, applied_files: list[str]) -> dict:
    commands = _validation_commands(target_repo, applied_files)
    if not commands:
        return {
            "status": "skipped",
            "summary": "No runnable project check was found for the changed files.",
            "checks": [],
        }

    checks = []
    for command, cwd, label in commands:
        timeout = 120 if label == "npm install" else 60 if command[:2] == ["npm", "run"] else 45
        result = await _run_copilot_command(command, cwd, timeout=timeout)
        checks.append({**result, "label": label})

    failed = [check for check in checks if check["return_code"] != 0]
    return {
        "status": "fail" if failed else "pass",
        "summary": (
            f"{len(failed)} of {len(checks)} check(s) failed."
            if failed
            else f"{len(checks)} check(s) passed."
        ),
        "checks": checks,
    }


async def _repair_copilot_changes(session: dict, target_repo: Path, validation: dict) -> list[dict]:
    failed_logs = "\n\n".join(
        f"$ {check['command']}\n{check.get('output', '')}"
        for check in validation.get("checks", [])
        if check.get("return_code") != 0
    )
    messages = [
        {"role": "system", "content": _copilot_system_prompt(target_repo)},
        {
            "role": "user",
            "content": (
                "The generated code did not pass validation. "
                "Generate a repair changes JSON only. "
                "Respond with {\"changes\":[{path, action, content}]}. "
                "Use full file contents for create/update. Keep paths within allowed folders."
                f"\n\nOriginal user request:\n{session['prompt']}"
                f"\n\nCurrent plan:\n{json.dumps(session.get('plan', {}), ensure_ascii=False)}"
                f"\n\nCurrent changed files:\n{json.dumps(session.get('changes', []), ensure_ascii=False)[:12000]}"
                f"\n\nValidation failure logs:\n{failed_logs[-8000:]}"
            ),
        },
    ]
    raw = await _call_deepseek(messages, model=session.get("model", "deepseek-v4-flash"))
    changes = raw.get("changes", [])
    if not isinstance(changes, list) or not changes:
        raise HTTPException(status_code=502, detail="DeepSeek did not return repair changes")

    normalized = []
    for item in changes:
        path = str(item.get("path") or "").replace("\\", "/").lstrip("/")
        action = str(item.get("action") or "update").lower()
        if action not in {"create", "update", "delete"}:
            raise HTTPException(status_code=400, detail=f"Unsupported repair action: {action}")
        _safe_target_path(target_repo, path)
        content = "" if action == "delete" else str(item.get("content") or "")
        if action != "delete" and not content:
            raise HTTPException(status_code=400, detail=f"Missing repair content for {path}")
        normalized.append({"path": path, "action": action, "content": content})
    return normalized


def _config_agent_model(target_repo: Path, config_name: str) -> str:
    config_path = Path(config_name)
    if not config_path.is_absolute():
        config_path = target_repo / config_name
    try:
        import yaml
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return ""
    return str((raw.get("agent") or {}).get("model") or "")


def _phase_names(record: dict, state: dict) -> list[str]:
    # YAML config is authoritative for ordering — JSONB key order is not reliable
    # (PostgreSQL sorts JSONB keys by length then alpha, not insertion order).
    yaml_names: list[str] = []
    target_repo = Path(record["target_repo"])
    config_name = record.get("config") or TARGET_CONFIGS.get((record.get("target"), record.get("mode", "expanded")), "")
    config_path = Path(config_name)
    if not config_path.is_absolute():
        config_path = target_repo / config_name
    try:
        import yaml
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        yaml_names = [phase["name"] for phase in raw.get("phases", []) if "name" in phase]
    except Exception:
        pass
    # Start with YAML order, then append any state phases not in YAML (e.g. dynamic phases).
    names = list(yaml_names)
    for name in state.get("phases", {}).keys():
        if name not in set(names):
            names.append(name)
    return names


def _serialize_harness_run(run_id: str) -> dict:
    record = HARNESS_RUNS.get(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="Harness run not found")

    db_record = db_logger.fetch_run(run_id) or {}
    target_repo = Path(record["target_repo"])
    state = db_logger.fetch_run_state(run_id) or {}
    phases_raw = state.get("phases", {})
    phases = []
    for name in _phase_names(record, state):
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
        "model": db_record.get("model", record.get("model", state.get("model", ""))),
        "cost_usd": state.get("cost_usd", db_record.get("cost_usd", 0.0)),
        "input_tokens": state.get("input_tokens", db_record.get("input_tokens", record.get("input_tokens", 0))),
        "output_tokens": state.get("output_tokens", db_record.get("output_tokens", record.get("output_tokens", 0))),
        "total_tokens": state.get("total_tokens", db_record.get("total_tokens", record.get("total_tokens", 0))),
        "phases": phases,
        "artifacts": db_logger.fetch_artifacts(run_id),
        "log_tail": db_logger.fetch_artifact_log_tail(run_id),
    }


async def _run_harness_process(run_id: str, resume: bool = False) -> None:
    record = HARNESS_RUNS[run_id]
    target_repo = Path(record["target_repo"])
    config = record.get("config") or TARGET_CONFIGS.get((record["target"], record.get("mode", "expanded")))
    if not config:
        record["status"] = "failed"
        record["finished_at"] = time.time()
        db_logger.log_run_updated(
            run_id,
            status="failed",
            finished_at=record["finished_at"],
            command="missing target harness config",
        )
        return
    log_path = Path(record["log_path"])
    HARNESS_LOG_DIR.mkdir(parents=True, exist_ok=True)

    if resume:
        cmd = [
            sys.executable,
            "-m",
            "cli",
            "resume",
            run_id,
            "--repo",
            str(target_repo),
            "--config",
            config,
        ]
        if record.get("provider"):
            cmd += ["--provider", record["provider"]]
    else:
        cmd = [
            sys.executable,
            "-m",
            "cli",
            "run",
            "--feature",
            record["feature"],
            "--tech-stack",
            record["tech_stack"],
            "--repo",
            str(target_repo),
            "--config",
            config,
            "--provider",
            record["provider"],
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


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/harness-targets")
def harness_targets() -> dict:
    return {
        "targets": [
            {
                "id": target_id,
                "name": "AINative OKR Claude/GHCP",
                "path": str(path.relative_to(ROOT_DIR)),
                "providers": ["codex", "claude"],
                "modes": ["expanded", "boss"],
            }
            for target_id, path in TARGETS.items()
        ]
    }


@app.get("/api/copilot/status")
def copilot_status() -> dict:
    target_repo = _target_root("okr-ghcp")
    return {
        "provider": "deepseek",
        "model": "deepseek-v4-flash",
        "configured": bool(_deepseek_api_key()),
        "target": "okr-ghcp",
        "target_repo": str(target_repo.relative_to(ROOT_DIR)),
        "allowed_prefixes": list(COPILOT_ALLOWED_PREFIXES),
    }


@app.get("/api/copilot/sessions")
def list_copilot_sessions() -> dict:
    ordered = sorted(
        COPILOT_SESSIONS.values(),
        key=lambda item: item["created_at"],
        reverse=True,
    )
    return {"sessions": ordered[:20]}


async def _run_harness_code_chat(target_repo: Path, payload: dict) -> dict:
    env = os.environ.copy()
    harness_src = str(ROOT_DIR / "packages" / "ai-harness" / "src")
    env["PYTHONPATH"] = harness_src + os.pathsep + env.get("PYTHONPATH", "")
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "cli",
        "code-chat",
        "--repo",
        str(target_repo),
        cwd=str(ROOT_DIR),
        env=env,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate(json.dumps(payload).encode("utf-8"))
    text = stdout.decode("utf-8", errors="ignore").strip()
    if not text:
        raise HTTPException(
            status_code=502,
            detail=(stderr.decode("utf-8", errors="ignore") or "Harness code-chat returned no output")[-1200:],
        )
    try:
        result = json.loads(text.splitlines()[-1])
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"Invalid harness code-chat response: {text[-1200:]}") from exc
    if proc.returncode != 0 and result.get("status") != "failed":
        result["status"] = "failed"
        result["error"] = (stderr.decode("utf-8", errors="ignore") or text)[-1200:]
    return result


async def _run_harness_code_chat_background(session_id: str, target_repo: Path, payload: dict) -> None:
    env = os.environ.copy()
    harness_src = str(ROOT_DIR / "packages" / "ai-harness" / "src")
    env["PYTHONPATH"] = harness_src + os.pathsep + env.get("PYTHONPATH", "")
    payload = {**payload, "session_id": session_id}

    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "cli",
        "code-chat",
        "--stream",
        "--repo",
        str(target_repo),
        cwd=str(ROOT_DIR),
        env=env,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    assert proc.stdin is not None
    proc.stdin.write(json.dumps(payload).encode("utf-8"))
    await proc.stdin.drain()
    proc.stdin.close()

    try:
        assert proc.stdout is not None
        async for raw_line in proc.stdout:
            line = raw_line.decode("utf-8", errors="ignore").strip()
            if not line:
                continue
            try:
                snapshot = json.loads(line)
            except json.JSONDecodeError:
                continue
            snapshot.setdefault("id", session_id)
            snapshot["updated_at"] = snapshot.get("updated_at") or _now()
            COPILOT_SESSIONS[session_id] = snapshot

        stderr = ""
        if proc.stderr:
            stderr = (await proc.stderr.read()).decode("utf-8", errors="ignore")
        return_code = await proc.wait()
        current = COPILOT_SESSIONS.get(session_id, {})
        if return_code != 0 and current.get("status") not in COPILOT_TERMINAL_STATUSES:
            current.update({
                "id": session_id,
                "status": "failed",
                "error": (stderr or "Harness code-chat failed")[-1200:],
                "updated_at": _now(),
            })
            COPILOT_SESSIONS[session_id] = current
    except Exception as exc:
        current = COPILOT_SESSIONS.get(session_id, {})
        current.update({"id": session_id, "status": "failed", "error": str(exc), "updated_at": _now()})
        COPILOT_SESSIONS[session_id] = current


@app.post("/api/copilot/sessions", status_code=201)
async def create_copilot_session(payload: CreateCopilotSessionRequest) -> dict:
    target_repo = _target_root(payload.target)
    session_id = f"chat-{uuid4().hex[:10]}"
    now = _now()
    session = {
        "id": session_id,
        "target": payload.target,
        "target_repo": str(target_repo),
        "prompt": payload.prompt,
        "model": payload.model,
        "requested_files": [item.model_dump() for item in payload.requested_files],
        "auto_apply": payload.auto_apply,
        "status": "queued",
        "plan": None,
        "changes": [],
        "diff": "",
        "applied_files": [],
        "validation": None,
        "repair_attempts": [],
        "error": "",
        "created_at": now,
        "updated_at": now,
    }
    COPILOT_SESSIONS[session_id] = session
    asyncio.create_task(_run_harness_code_chat_background(session_id, target_repo, payload.model_dump()))
    return session


@app.get("/api/copilot/sessions/{session_id}")
def get_copilot_session(session_id: str) -> dict:
    session = COPILOT_SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Copilot session not found")
    return session


@app.get("/api/copilot/sessions/{session_id}/events")
async def stream_copilot_session(session_id: str) -> StreamingResponse:
    if session_id not in COPILOT_SESSIONS:
        raise HTTPException(status_code=404, detail="Copilot session not found")

    async def events():
        last_updated = None
        while True:
            session = COPILOT_SESSIONS.get(session_id)
            if not session:
                yield "event: error\ndata: {\"error\":\"session not found\"}\n\n"
                return
            updated = session.get("updated_at")
            if updated != last_updated:
                last_updated = updated
                yield f"event: session\ndata: {json.dumps(session, ensure_ascii=False)}\n\n"
            if session.get("status") in COPILOT_TERMINAL_STATUSES:
                yield f"event: done\ndata: {json.dumps(session, ensure_ascii=False)}\n\n"
                return
            await asyncio.sleep(0.5)

    return StreamingResponse(events(), media_type="text/event-stream")


@app.post("/api/copilot/sessions/{session_id}/approve")
async def approve_copilot_stage(session_id: str, payload: CopilotApprovalRequest) -> dict:
    session = COPILOT_SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Copilot session not found")
    target_repo = _target_root(session["target"])

    if not payload.approved:
        session["approvals"].append({"stage": payload.stage, "approved": False, "at": _now()})
        return _mark_copilot_session(session, status="rejected")

    if payload.stage == "plan":
        if session["status"] != "plan_pending":
            raise HTTPException(status_code=409, detail="Plan is not pending approval")
        session["approvals"].append({"stage": "plan", "approved": True, "at": _now()})
        _mark_copilot_session(session, status="generating_changes")
        try:
            changes = await _create_copilot_changes(session, target_repo)
            diff = _build_changes_diff(target_repo, changes)
            return _mark_copilot_session(
                session,
                status="changes_pending",
                changes=changes,
                diff=diff,
            )
        except HTTPException as exc:
            _mark_copilot_session(session, status="failed", error=str(exc.detail))
            raise

    if session["status"] != "changes_pending":
        raise HTTPException(status_code=409, detail="Changes are not pending approval")
    session["approvals"].append({"stage": "changes", "approved": True, "at": _now()})
    applied = _apply_copilot_changes(target_repo, session.get("changes", []))
    return _mark_copilot_session(session, status="applied", applied_files=applied)


@app.post("/api/copilot/sessions/{session_id}/reject")
def reject_copilot_session(session_id: str, payload: CopilotRejectRequest) -> dict:
    session = COPILOT_SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Copilot session not found")
    session["approvals"].append({
        "stage": session.get("status", "unknown"),
        "approved": False,
        "reason": payload.reason,
        "at": _now(),
    })
    return _mark_copilot_session(session, status="rejected")


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


MAX_MD_UPLOAD_BYTES = 2_000_000  # 2 MB — plain requirement/change-request text, not a binary dump


def _slugify(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return base[:60] or "upload"


def _apply_extraction_to_target(extraction: dict, target_repo: Path) -> str:
    """Write an uploaded doc's content into the target repo so the existing
    harness context sources (docs/input/**/*.md, docs/technical_architecture.md)
    pick it up. Returns the path written, relative to target_repo."""
    content = extraction["extracted_markdown"]
    doc_type = extraction.get("doc_type") or "requirement"
    slug = _slugify(Path(extraction["original_filename"]).stem)

    if doc_type == "architecture":
        dest = target_repo / "docs" / "technical_architecture.md"
    elif doc_type == "change-request":
        dest = target_repo / "docs" / "input" / "change-request" / f"{slug}.md"
    else:
        dest = target_repo / "docs" / "input" / "uploads" / f"{slug}.md"

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")
    return str(dest.relative_to(target_repo))


@app.post("/api/file-extractions", status_code=201)
async def create_file_extraction(
    files: list[UploadFile] = File(...),
    doc_type: DocType = Form(default="requirement"),
    run_id: str | None = Form(default=None),
) -> dict:
    """Upload one or more Markdown files as harness input context.

    Only `.md` is supported today — pdf/xlsx/txt extraction is not wired up
    yet even though the upload UI lists them as accepted types. Files are
    stored standalone (run_id=None) unless `run_id` refers to an existing
    run; otherwise pass the returned `id`s as `extraction_ids` when creating
    a harness run so the content lands in the target repo before it starts.
    """
    if run_id is not None and run_id not in HARNESS_RUNS:
        raise HTTPException(status_code=404, detail="Harness run not found")

    created = []
    for upload in files:
        filename = upload.filename or "upload.md"
        if not filename.lower().endswith(".md"):
            raise HTTPException(
                status_code=400,
                detail=f"Only .md uploads are supported right now: {filename}",
            )
        raw = await upload.read()
        if len(raw) > MAX_MD_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail=f"{filename} exceeds the 2MB limit")
        content = raw.decode("utf-8", errors="ignore")

        extraction_id = db_logger.insert_file_extraction(
            original_filename=filename,
            file_type="md",
            file_size_bytes=len(raw),
            extracted_markdown=content,
            doc_type=doc_type,
            run_id=run_id,
        )

        storage_path = None
        if run_id is not None:
            target_repo = TARGETS.get(HARNESS_RUNS[run_id]["target"])
            extraction = db_logger.fetch_file_extraction(extraction_id)
            storage_path = _apply_extraction_to_target(extraction, target_repo)
            db_logger.attach_file_extraction_to_run(extraction_id, run_id, storage_path)

        created.append({
            "id": extraction_id,
            "original_filename": filename,
            "doc_type": doc_type,
            "size_bytes": len(raw),
            "storage_path": storage_path,
        })

    return {"files": created}


@app.post("/api/harness-runs", status_code=201)
async def create_harness_run(payload: CreateHarnessRunRequest) -> dict:
    target_repo = TARGETS.get(payload.target)
    if not target_repo:
        raise HTTPException(status_code=404, detail="Harness target not registered")
    if not target_repo.exists():
        raise HTTPException(status_code=404, detail="Target project not found")

    run_id = f"ui-{uuid4().hex[:10]}"
    log_path = HARNESS_LOG_DIR / f"{run_id}.log"
    config = (
        TARGET_CONFIGS.get((payload.target, payload.mode))
        or TARGET_CONFIGS.get((payload.target, "expanded"))
    )
    if not config:
        raise HTTPException(status_code=400, detail="Harness config not registered for target/mode")
    record = {
        "id": run_id,
        "feature": payload.feature,
        "provider": payload.provider,
        "model": _config_agent_model(target_repo, config),
        "tech_stack": payload.tech_stack,
        "target": payload.target,
        "mode": payload.mode,
        "config": config,
        "target_repo": str(target_repo),
        "status": "queued",
        "created_at": time.time(),
        "started_at": None,
        "finished_at": None,
        "pid": None,
        "return_code": None,
        "command": None,
        "log_path": str(log_path),
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
    }
    HARNESS_RUNS[run_id] = record
    db_logger.log_run_created(record)

    # Write any pre-uploaded docs into the target repo *before* the harness
    # subprocess is scheduled, so H1-context always sees them — the harness
    # process is launched via asyncio.create_task below and there is no other
    # synchronization point once it starts.
    for extraction_id in payload.extraction_ids:
        extraction = db_logger.fetch_file_extraction(extraction_id)
        if not extraction:
            raise HTTPException(status_code=404, detail=f"file_extraction {extraction_id} not found")
        storage_path = _apply_extraction_to_target(extraction, target_repo)
        db_logger.attach_file_extraction_to_run(extraction_id, run_id, storage_path)
        db_logger.log_event(run_id, "upload_applied", None,
                            f"Applied uploaded doc '{extraction['original_filename']}' -> {storage_path}")

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


@app.post("/api/harness-runs/{run_id}/retry")
async def retry_harness_run(run_id: str, payload: RetryHarnessRunRequest) -> dict:
    if run_id not in HARNESS_RUNS:
        raise HTTPException(status_code=404, detail="Harness run not found")
    record = HARNESS_RUNS[run_id]
    if record["status"] in ("running", "queued"):
        raise HTTPException(status_code=409, detail="Run is already active")

    if payload.provider:
        record["provider"] = payload.provider
        db_logger.log_run_updated(run_id, provider=payload.provider)

    record["status"] = "queued"
    record["finished_at"] = None
    db_logger.log_run_updated(run_id, status="queued", finished_at=None)

    asyncio.create_task(_run_harness_process(run_id, resume=True))
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


@app.get("/api/harness-runs/{run_id}/token-usage")
def get_run_token_usage(run_id: str) -> dict:
    """Return model/token usage grouped by phase, highest token usage first."""
    if run_id not in HARNESS_RUNS:
        raise HTTPException(status_code=404, detail="Harness run not found")
    rows = db_logger.fetch_phase_token_usage(run_id)
    return {"run_id": run_id, "phases": rows}


@app.get("/api/harness-runs/{run_id}/artifacts/{artifact_id}")
def get_artifact_content(run_id: str, artifact_id: str) -> dict:
    """Return a single artifact's full content."""
    if run_id not in HARNESS_RUNS:
        raise HTTPException(status_code=404, detail="Harness run not found")
    row = db_logger.fetch_artifact_content(artifact_id)
    if not row or str(row.get("run_id")) != run_id:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return {
        "id": row["id"],
        "artifact_type": row["artifact_type"],
        "name": row["name"],
        "content": row["content"] or "",
        "payload": row["payload"],
        "created_at": row["created_at"],
    }


@app.get("/api/harness-runs/{run_id}/log")
def get_run_log(
    run_id: str,
    lines: int = Query(default=200, ge=1, le=2000),
) -> dict:
    """Return the tail of the raw harness subprocess log file."""
    if run_id not in HARNESS_RUNS:
        raise HTTPException(status_code=404, detail="Harness run not found")
    record = HARNESS_RUNS[run_id]
    log_path = Path(record.get("log_path", ""))
    if not log_path.exists():
        return {"run_id": run_id, "lines": [], "available": False}
    tail = _tail(log_path, limit=lines)
    return {"run_id": run_id, "lines": tail, "available": True, "total": len(tail)}
