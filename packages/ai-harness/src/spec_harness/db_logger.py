"""Harness-side database logger.

Writes phase events and gate outcomes directly to PostgreSQL from inside
the harness subprocess.  The backend sets HARNESS_DB_URL when it spawns
the subprocess so both processes share the same database.

If HARNESS_DB_URL is not set (pure CLI mode), every function is a no-op —
the harness keeps running normally and just skips structured DB logging.
"""
from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from typing import Generator

_pool = None
_psycopg2 = None


def _available() -> bool:
    """Return True if psycopg2 is importable and HARNESS_DB_URL is set."""
    global _psycopg2
    dsn = os.environ.get("HARNESS_DB_URL") or os.environ.get("DATABASE_URL")
    if not dsn:
        return False
    if _psycopg2 is None:
        try:
            import psycopg2  # noqa: F401
            import psycopg2.extras  # noqa: F401
            _psycopg2 = True
        except ImportError:
            _psycopg2 = False
    return bool(_psycopg2)


def _dsn() -> str:
    return os.environ.get("HARNESS_DB_URL") or os.environ.get("DATABASE_URL", "")


@contextmanager
def _conn() -> Generator:
    import psycopg2  # type: ignore
    conn = psycopg2.connect(_dsn())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Phase events ──────────────────────────────────────────────────────────────

def phase_started(run_id: str, phase_name: str, attempt: int,
                  prompt_snippet: str = "") -> None:
    if not _available():
        return
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO phase_events
                        (run_id, phase_name, attempt, status, started_at, prompt_snippet)
                    VALUES (%s, %s, %s, 'running', %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (run_id, phase_name, attempt, time.time(),
                     (prompt_snippet or "")[:500]),
                )
        _emit(run_id, "phase_started", phase_name,
              f"Phase '{phase_name}' attempt {attempt} started")
    except Exception as exc:
        print(f"[harness db_logger] phase_started: {exc}")


def phase_done(run_id: str, phase_name: str, attempt: int,
               status: str, gate_result: str,
               agent_ok: bool | None = None, cost_usd: float = 0.0) -> None:
    if not _available():
        return
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE phase_events
                       SET status = %s, gate_result = %s,
                           agent_ok = %s, cost_usd = %s, finished_at = %s
                     WHERE run_id = %s AND phase_name = %s AND attempt = %s
                    """,
                    (status, gate_result, agent_ok, cost_usd,
                     time.time(), run_id, phase_name, attempt),
                )
        _emit(run_id, "phase_done", phase_name,
              f"Phase '{phase_name}' attempt {attempt} → {status} (gate: {gate_result})",
              {"cost_usd": cost_usd, "agent_ok": agent_ok})
    except Exception as exc:
        print(f"[harness db_logger] phase_done: {exc}")


def gate_outcome(run_id: str, phase_name: str, attempt: int,
                 gate_name: str, gate_type: str,
                 passed: bool, report: str = "") -> None:
    if not _available():
        return
    try:
        with _conn() as conn:
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
        _emit(run_id, "gate_checked", phase_name,
              f"{icon} Gate '{gate_name}' ({gate_type}): {'pass' if passed else 'fail'}",
              {"gate_name": gate_name, "passed": passed})
    except Exception as exc:
        print(f"[harness db_logger] gate_outcome: {exc}")


def run_escalated(run_id: str, phase_name: str, reason: str) -> None:
    if not _available():
        return
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE harness_runs SET status = 'escalated', "
                    "current_phase = %s WHERE run_id = %s",
                    (phase_name, run_id),
                )
        _emit(run_id, "escalated", phase_name,
              f"⛔ Run escalated at phase '{phase_name}'",
              {"reason": reason[:1000]})
    except Exception as exc:
        print(f"[harness db_logger] run_escalated: {exc}")


def run_complete(run_id: str, cost_usd: float) -> None:
    if not _available():
        return
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE harness_runs SET status = 'complete', "
                    "cost_usd = %s, current_phase = NULL, finished_at = %s "
                    "WHERE run_id = %s",
                    (cost_usd, time.time(), run_id),
                )
        _emit(run_id, "run_complete", None,
              f"✅ Run complete. Total cost ~${cost_usd}",
              {"cost_usd": cost_usd})
    except Exception as exc:
        print(f"[harness db_logger] run_complete: {exc}")


# ── Internal event emitter ────────────────────────────────────────────────────

def _emit(run_id: str, event_type: str, phase: str | None,
          message: str, payload: dict | None = None) -> None:
    try:
        with _conn() as conn:
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
        print(f"[harness db_logger] _emit: {exc}")
