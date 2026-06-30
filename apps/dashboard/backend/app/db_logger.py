"""Thin event-logging helpers that write structured rows to PostgreSQL.

All functions are fire-and-forget (they swallow DB errors so a logging
failure never crashes the harness or the API).
"""
from __future__ import annotations

import json
import time

from . import db


# ── Run lifecycle ─────────────────────────────────────────────────────────────

def log_run_created(record: dict) -> None:
    """Insert a new harness run row."""
    try:
        with db.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                   INSERT INTO harness_runs
                        (run_id, feature, provider, model, target,
                         mode, config, target_repo, status, created_at, log_path,
                         input_tokens, output_tokens, total_tokens)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (run_id) DO NOTHING
                    """,
                    (
                        record["id"],
                        record["feature"],
                        record.get("provider", "codex"),
                        record.get("model", ""),
                        record.get("target", "okr-ghcp"),
                        record.get("mode", "expanded"),
                        record.get("config", ""),
                        record.get("target_repo", ""),
                        record.get("status", "queued"),
                        record["created_at"],
                        record.get("log_path", ""),
                        int(record.get("input_tokens", 0) or 0),
                        int(record.get("output_tokens", 0) or 0),
                        int(record.get("total_tokens", 0) or 0),
                    ),
                )
        _emit_event(record["id"], "run_created", None,
                    f"Run {record['id']} created for feature: {record['feature'][:120]}")
    except Exception as exc:
        print(f"[db_logger] log_run_created failed: {exc}")


def log_run_updated(run_id: str, **fields) -> None:
    """Patch one or more columns on an existing run row."""
    if not fields:
        return
    allowed = {
        "status", "started_at", "finished_at", "cost_usd", "model",
        "input_tokens", "output_tokens", "total_tokens",
        "current_phase", "feature_dir", "pid", "return_code", "command",
    }
    safe = {k: v for k, v in fields.items() if k in allowed}
    if not safe:
        return
    set_clause = ", ".join(f"{k} = %s" for k in safe)
    values = list(safe.values()) + [run_id]
    try:
        with db.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE harness_runs SET {set_clause} WHERE run_id = %s",
                    values,
                )
    except Exception as exc:
        print(f"[db_logger] log_run_updated failed: {exc}")


# ── Phase events ──────────────────────────────────────────────────────────────

def log_phase_started(run_id: str, phase_name: str, attempt: int,
                      prompt_snippet: str = "") -> None:
    try:
        with db.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO phase_events
                        (run_id, phase_name, attempt, status, started_at, prompt_snippet)
                    VALUES (%s, %s, %s, 'running', %s, %s)
                    """,
                    (run_id, phase_name, attempt, time.time(),
                     (prompt_snippet or "")[:500]),
                )
        _emit_event(run_id, "phase_started", phase_name,
                    f"Phase '{phase_name}' attempt {attempt} started")
    except Exception as exc:
        print(f"[db_logger] log_phase_started failed: {exc}")


def log_phase_done(run_id: str, phase_name: str, attempt: int,
                   status: str, gate_result: str,
                   agent_ok: bool | None = None, cost_usd: float = 0.0,
                   model: str = "", input_tokens: int = 0,
                   output_tokens: int = 0, total_tokens: int = 0) -> None:
    try:
        with db.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE phase_events
                       SET status = %s,
                           gate_result = %s,
                           agent_ok = %s,
                           cost_usd = %s,
                           model = %s,
                           input_tokens = %s,
                           output_tokens = %s,
                           total_tokens = %s,
                           finished_at = %s
                     WHERE run_id = %s AND phase_name = %s AND attempt = %s
                    """,
                    (status, gate_result, agent_ok, cost_usd,
                     model, input_tokens, output_tokens, total_tokens,
                     time.time(), run_id, phase_name, attempt),
                )
        _emit_event(run_id, "phase_done", phase_name,
                    f"Phase '{phase_name}' attempt {attempt} → {status} (gate: {gate_result})",
                    {
                        "cost_usd": cost_usd,
                        "agent_ok": agent_ok,
                        "model": model,
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": total_tokens,
                    })
    except Exception as exc:
        print(f"[db_logger] log_phase_done failed: {exc}")


# ── Gate outcomes ─────────────────────────────────────────────────────────────

def log_gate_outcome(run_id: str, phase_name: str, attempt: int,
                     gate_name: str, gate_type: str,
                     passed: bool, report: str = "") -> None:
    try:
        with db.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO gate_outcomes
                        (run_id, phase_name, attempt, gate_name, gate_type,
                         passed, report, checked_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (run_id, phase_name, attempt, gate_name, gate_type,
                     passed, (report or "")[:4000], time.time()),
                )
        icon = "✅" if passed else "❌"
        _emit_event(run_id, "gate_checked", phase_name,
                    f"{icon} Gate '{gate_name}' ({gate_type}): {'pass' if passed else 'fail'}",
                    {"gate_name": gate_name, "gate_type": gate_type, "passed": passed})
    except Exception as exc:
        print(f"[db_logger] log_gate_outcome failed: {exc}")


# ── Generic event emitter ─────────────────────────────────────────────────────

def log_event(run_id: str, event_type: str, phase: str | None,
              message: str, payload: dict | None = None) -> None:
    _emit_event(run_id, event_type, phase, message, payload)


def _emit_event(run_id: str, event_type: str, phase: str | None,
                message: str, payload: dict | None = None) -> None:
    try:
        with db.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO run_events
                        (run_id, event_type, phase, message, payload, occurred_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (run_id, event_type, phase, message,
                     json.dumps(payload) if payload else None,
                     time.time()),
                )
    except Exception as exc:
        print(f"[db_logger] _emit_event failed: {exc}")


# ── Query helpers (used by API endpoints) ────────────────────────────────────

def fetch_all_runs() -> list[dict]:
    try:
        with db.get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM harness_runs ORDER BY created_at DESC"
                )
                return [dict(row) for row in cur.fetchall()]
    except Exception as exc:
        print(f"[db_logger] fetch_all_runs failed: {exc}")
        return []


def fetch_run(run_id: str) -> dict | None:
    try:
        with db.get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM harness_runs WHERE run_id = %s", (run_id,)
                )
                row = cur.fetchone()
                return dict(row) if row else None
    except Exception as exc:
        print(f"[db_logger] fetch_run failed: {exc}")
        return None


def fetch_artifact_content(artifact_id: str) -> dict | None:
    """Return a single artifact row including its full content."""
    try:
        with db.get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, run_id, artifact_type, name, content, payload, created_at
                      FROM harness_artifacts
                     WHERE id = %s
                    """,
                    (artifact_id,),
                )
                row = cur.fetchone()
                return dict(row) if row else None
    except Exception as exc:
        print(f"[db_logger] fetch_artifact_content failed: {exc}")
        return None


def fetch_run_state(run_id: str) -> dict | None:
    try:
        with db.get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT state FROM harness_run_state WHERE run_id = %s",
                    (run_id,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                state = row["state"]
                return json.loads(state) if isinstance(state, str) else dict(state)
    except Exception as exc:
        print(f"[db_logger] fetch_run_state failed: {exc}")
        return None


def fetch_artifacts(run_id: str, limit: int = 80) -> list[dict]:
    try:
        with db.get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, artifact_type, name, payload,
                           length(content) AS size,
                           created_at
                      FROM harness_artifacts
                     WHERE run_id = %s
                     ORDER BY id DESC
                     LIMIT %s
                    """,
                    (run_id, limit),
                )
                rows = []
                for row in cur.fetchall():
                    item = dict(row)
                    item["path"] = f"db://harness_artifacts/{item['id']}"
                    rows.append(item)
                return rows
    except Exception as exc:
        print(f"[db_logger] fetch_artifacts failed: {exc}")
        return []


def fetch_artifact_log_tail(run_id: str, limit: int = 120) -> list[str]:
    try:
        with db.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT artifact_type, name, content
                      FROM harness_artifacts
                     WHERE run_id = %s
                       AND artifact_type IN ('phase_log', 'gate_log', 'escalation')
                     ORDER BY id DESC
                     LIMIT 6
                    """,
                    (run_id,),
                )
                chunks = []
                for artifact_type, name, content in cur.fetchall():
                    chunks.append(f"## {artifact_type}: {name}")
                    chunks.extend((content or "").splitlines()[-40:])
                return chunks[-limit:]
    except Exception as exc:
        print(f"[db_logger] fetch_artifact_log_tail failed: {exc}")
        return []


def fetch_run_events(run_id: str, limit: int = 200, after_id: int = 0) -> list[dict]:
    try:
        with db.get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, event_type, phase, message, payload, occurred_at
                      FROM run_events
                     WHERE run_id = %s AND id > %s
                     ORDER BY id ASC
                     LIMIT %s
                    """,
                    (run_id, after_id, limit),
                )
                return [dict(row) for row in cur.fetchall()]
    except Exception as exc:
        print(f"[db_logger] fetch_run_events failed: {exc}")
        return []


def fetch_gate_outcomes(run_id: str) -> list[dict]:
    try:
        with db.get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT phase_name, attempt, gate_name, gate_type,
                           passed, report, checked_at
                      FROM gate_outcomes
                     WHERE run_id = %s
                     ORDER BY checked_at ASC
                    """,
                    (run_id,),
                )
                return [dict(row) for row in cur.fetchall()]
    except Exception as exc:
        print(f"[db_logger] fetch_gate_outcomes failed: {exc}")
        return []


def fetch_phase_timeline(run_id: str) -> list[dict]:
    try:
        with db.get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT phase_name, attempt, status, gate_result,
                           agent_ok, cost_usd, model,
                           input_tokens, output_tokens, total_tokens,
                           started_at, finished_at
                      FROM phase_events
                     WHERE run_id = %s
                     ORDER BY started_at ASC
                    """,
                    (run_id,),
                )
                return [dict(row) for row in cur.fetchall()]
    except Exception as exc:
        print(f"[db_logger] fetch_phase_timeline failed: {exc}")
        return []


def fetch_phase_token_usage(run_id: str) -> list[dict]:
    try:
        with db.get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT phase_name,
                           COALESCE(NULLIF(model, ''), '') AS model,
                           SUM(input_tokens) AS input_tokens,
                           SUM(output_tokens) AS output_tokens,
                           SUM(total_tokens) AS total_tokens,
                           SUM(cost_usd) AS cost_usd,
                           COUNT(*) AS attempts
                      FROM phase_events
                     WHERE run_id = %s
                     GROUP BY phase_name, COALESCE(NULLIF(model, ''), '')
                     ORDER BY SUM(total_tokens) DESC, SUM(cost_usd) DESC, phase_name ASC
                    """,
                    (run_id,),
                )
                return [dict(row) for row in cur.fetchall()]
    except Exception as exc:
        print(f"[db_logger] fetch_phase_token_usage failed: {exc}")
        return []


# Need this for fetch_all_runs cursor factory
import psycopg2.extras  # noqa: E402 — placed here to keep top-level imports clean
