"""PostgreSQL database connection and schema initialisation.

Uses psycopg2 (sync) so it works inside FastAPI startup events and
also inside the harness subprocess without requiring an asyncio loop.

Environment:
    DATABASE_URL  – full libpq DSN, e.g.
                    postgresql://harness:harness_dev@localhost:5432/harness
"""
from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from typing import Generator

import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool

_pool: ThreadedConnectionPool | None = None
_lock = threading.Lock()


# ── DDL ───────────────────────────────────────────────────────────────────────

_DDL = """
CREATE TABLE IF NOT EXISTS harness_runs (
    run_id          TEXT        PRIMARY KEY,
    feature         TEXT        NOT NULL,
    provider        TEXT        NOT NULL DEFAULT 'codex',
    tech_stack      TEXT        NOT NULL DEFAULT '',
    target          TEXT        NOT NULL DEFAULT 'todo-app',
    target_repo     TEXT        NOT NULL DEFAULT '',
    status          TEXT        NOT NULL DEFAULT 'queued',
    created_at      DOUBLE PRECISION NOT NULL,
    started_at      DOUBLE PRECISION,
    finished_at     DOUBLE PRECISION,
    cost_usd        DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    current_phase   TEXT,
    feature_dir     TEXT,
    log_path        TEXT        NOT NULL DEFAULT '',
    pid             INTEGER,
    return_code     INTEGER,
    command         TEXT
);

CREATE TABLE IF NOT EXISTS phase_events (
    id              BIGSERIAL   PRIMARY KEY,
    run_id          TEXT        NOT NULL REFERENCES harness_runs(run_id) ON DELETE CASCADE,
    phase_name      TEXT        NOT NULL,
    attempt         INTEGER     NOT NULL DEFAULT 1,
    status          TEXT        NOT NULL DEFAULT 'running',
    started_at      DOUBLE PRECISION NOT NULL,
    finished_at     DOUBLE PRECISION,
    gate_result     TEXT,
    prompt_snippet  TEXT,
    agent_ok        BOOLEAN,
    cost_usd        DOUBLE PRECISION NOT NULL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS gate_outcomes (
    id              BIGSERIAL   PRIMARY KEY,
    run_id          TEXT        NOT NULL REFERENCES harness_runs(run_id) ON DELETE CASCADE,
    phase_name      TEXT        NOT NULL,
    attempt         INTEGER     NOT NULL DEFAULT 1,
    gate_name       TEXT        NOT NULL,
    gate_type       TEXT        NOT NULL DEFAULT '',
    passed          BOOLEAN     NOT NULL,
    report          TEXT        NOT NULL DEFAULT '',
    checked_at      DOUBLE PRECISION NOT NULL
);

CREATE TABLE IF NOT EXISTS run_events (
    id              BIGSERIAL   PRIMARY KEY,
    run_id          TEXT        NOT NULL REFERENCES harness_runs(run_id) ON DELETE CASCADE,
    event_type      TEXT        NOT NULL,
    phase           TEXT,
    message         TEXT        NOT NULL DEFAULT '',
    payload         JSONB,
    occurred_at     DOUBLE PRECISION NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_phase_events_run_id    ON phase_events(run_id);
CREATE INDEX IF NOT EXISTS idx_gate_outcomes_run_id   ON gate_outcomes(run_id);
CREATE INDEX IF NOT EXISTS idx_run_events_run_id      ON run_events(run_id);
CREATE INDEX IF NOT EXISTS idx_run_events_occurred_at ON run_events(run_id, occurred_at);
"""


# ── Pool management ───────────────────────────────────────────────────────────

def _get_dsn() -> str:
    dsn = os.environ.get("DATABASE_URL") or os.environ.get("HARNESS_DB_URL")
    if not dsn:
        raise RuntimeError(
            "DATABASE_URL is not set. "
            "Copy .env.example to .env and set DATABASE_URL, "
            "or start the PostgreSQL container with: docker compose up -d postgres"
        )
    return dsn


def get_pool() -> ThreadedConnectionPool:
    global _pool
    if _pool is None:
        with _lock:
            if _pool is None:
                _pool = ThreadedConnectionPool(minconn=1, maxconn=10, dsn=_get_dsn())
    return _pool


@contextmanager
def get_conn() -> Generator[psycopg2.extensions.connection, None, None]:
    """Yield a connection from the pool; auto-commit on success, rollback on error."""
    pool = get_pool()
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


# ── Schema bootstrap ──────────────────────────────────────────────────────────

def init_db() -> None:
    """Create tables if they do not exist. Idempotent — safe to call on every startup."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_DDL)
    print("✅ Database schema initialised (PostgreSQL)")
