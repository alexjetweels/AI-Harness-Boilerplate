"""Postgres-first persistence for harness state and artifacts."""
from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from typing import Generator

_DDL = """
CREATE TABLE IF NOT EXISTS harness_runs (
    run_id          TEXT        PRIMARY KEY,
    feature         TEXT        NOT NULL,
    provider        TEXT        NOT NULL DEFAULT 'codex',
    model           TEXT        NOT NULL DEFAULT '',
    target          TEXT        NOT NULL DEFAULT '',
    mode            TEXT        NOT NULL DEFAULT 'expanded',
    config          TEXT        NOT NULL DEFAULT '',
    target_repo     TEXT        NOT NULL DEFAULT '',
    status          TEXT        NOT NULL DEFAULT 'running',
    created_at      DOUBLE PRECISION NOT NULL,
    started_at      DOUBLE PRECISION,
    finished_at     DOUBLE PRECISION,
    cost_usd        DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    input_tokens    BIGINT      NOT NULL DEFAULT 0,
    output_tokens   BIGINT      NOT NULL DEFAULT 0,
    total_tokens    BIGINT      NOT NULL DEFAULT 0,
    current_phase   TEXT,
    feature_dir     TEXT,
    log_path        TEXT        NOT NULL DEFAULT '',
    pid             INTEGER,
    return_code     INTEGER,
    command         TEXT
);

CREATE TABLE IF NOT EXISTS harness_run_state (
    run_id          TEXT        PRIMARY KEY REFERENCES harness_runs(run_id) ON DELETE CASCADE,
    state           JSONB       NOT NULL,
    updated_at      DOUBLE PRECISION NOT NULL
);

CREATE TABLE IF NOT EXISTS harness_artifacts (
    id              BIGSERIAL   PRIMARY KEY,
    run_id          TEXT        NOT NULL REFERENCES harness_runs(run_id) ON DELETE CASCADE,
    artifact_type   TEXT        NOT NULL,
    name            TEXT        NOT NULL,
    content         TEXT        NOT NULL DEFAULT '',
    payload         JSONB,
    created_at      DOUBLE PRECISION NOT NULL
);

ALTER TABLE harness_runs ADD COLUMN IF NOT EXISTS mode TEXT NOT NULL DEFAULT 'expanded';
ALTER TABLE harness_runs ADD COLUMN IF NOT EXISTS config TEXT NOT NULL DEFAULT '';
ALTER TABLE harness_runs ADD COLUMN IF NOT EXISTS model TEXT NOT NULL DEFAULT '';
ALTER TABLE harness_runs ADD COLUMN IF NOT EXISTS input_tokens BIGINT NOT NULL DEFAULT 0;
ALTER TABLE harness_runs ADD COLUMN IF NOT EXISTS output_tokens BIGINT NOT NULL DEFAULT 0;
ALTER TABLE harness_runs ADD COLUMN IF NOT EXISTS total_tokens BIGINT NOT NULL DEFAULT 0;
ALTER TABLE harness_runs DROP COLUMN IF EXISTS tech_stack;

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
    cost_usd        DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    model           TEXT        NOT NULL DEFAULT '',
    input_tokens    BIGINT      NOT NULL DEFAULT 0,
    output_tokens   BIGINT      NOT NULL DEFAULT 0,
    total_tokens    BIGINT      NOT NULL DEFAULT 0
);

ALTER TABLE phase_events ADD COLUMN IF NOT EXISTS model TEXT NOT NULL DEFAULT '';
ALTER TABLE phase_events ADD COLUMN IF NOT EXISTS input_tokens BIGINT NOT NULL DEFAULT 0;
ALTER TABLE phase_events ADD COLUMN IF NOT EXISTS output_tokens BIGINT NOT NULL DEFAULT 0;
ALTER TABLE phase_events ADD COLUMN IF NOT EXISTS total_tokens BIGINT NOT NULL DEFAULT 0;

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

CREATE INDEX IF NOT EXISTS idx_harness_artifacts_run_id
    ON harness_artifacts(run_id);
CREATE INDEX IF NOT EXISTS idx_harness_artifacts_type
    ON harness_artifacts(run_id, artifact_type);
CREATE INDEX IF NOT EXISTS idx_phase_events_run_id
    ON phase_events(run_id);
CREATE INDEX IF NOT EXISTS idx_phase_events_tokens
    ON phase_events(run_id, total_tokens DESC);
CREATE INDEX IF NOT EXISTS idx_gate_outcomes_run_id
    ON gate_outcomes(run_id);
CREATE INDEX IF NOT EXISTS idx_run_events_run_id
    ON run_events(run_id);
"""


def _dsn() -> str:
    dsn = os.environ.get("HARNESS_DB_URL") or os.environ.get("DATABASE_URL")
    if not dsn:
        raise RuntimeError(
            "Postgres is required for harness persistence. "
            "Set HARNESS_DB_URL or DATABASE_URL before running the harness."
        )
    return dsn


@contextmanager
def connect() -> Generator:
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


def init() -> None:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(_DDL)


def save_state(state: dict) -> None:
    init()
    now = time.time()
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO harness_runs
                    (run_id, feature, provider, model, status, created_at, started_at,
                     cost_usd, input_tokens, output_tokens, total_tokens,
                     current_phase, feature_dir)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (run_id) DO UPDATE
                   SET status = EXCLUDED.status,
                       model = EXCLUDED.model,
                       cost_usd = EXCLUDED.cost_usd,
                       input_tokens = EXCLUDED.input_tokens,
                       output_tokens = EXCLUDED.output_tokens,
                       total_tokens = EXCLUDED.total_tokens,
                       current_phase = EXCLUDED.current_phase,
                       feature_dir = EXCLUDED.feature_dir
                """,
                (
                    state["run_id"],
                    state["feature"],
                    state.get("provider", "codex"),
                    state.get("model", ""),
                    state.get("status", "running"),
                    now,
                    now,
                    float(state.get("cost_usd", 0.0) or 0.0),
                    int(state.get("input_tokens", 0) or 0),
                    int(state.get("output_tokens", 0) or 0),
                    int(state.get("total_tokens", 0) or 0),
                    state.get("current_phase"),
                    state.get("feature_dir"),
                ),
            )
            cur.execute(
                """
                INSERT INTO harness_run_state (run_id, state, updated_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (run_id) DO UPDATE
                   SET state = EXCLUDED.state,
                       updated_at = EXCLUDED.updated_at
                """,
                (state["run_id"], json.dumps(state), now),
            )


def load_state(run_id: str) -> dict:
    init()
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT state FROM harness_run_state WHERE run_id = %s",
                (run_id,),
            )
            row = cur.fetchone()
    if not row:
        raise FileNotFoundError(f"Harness run state not found in Postgres: {run_id}")
    state = row[0]
    if isinstance(state, str):
        return json.loads(state)
    return state


def save_artifact(run_id: str, artifact_type: str, name: str,
                  content: str = "", payload: dict | None = None) -> str:
    init()
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO harness_artifacts
                    (run_id, artifact_type, name, content, payload, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    run_id,
                    artifact_type,
                    name,
                    content or "",
                    json.dumps(payload) if payload is not None else None,
                    time.time(),
                ),
            )
            artifact_id = cur.fetchone()[0]
    return str(artifact_id)


def artifact_exists(artifact_id: str) -> bool:
    if not artifact_id:
        return False
    init()
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM harness_artifacts WHERE id = %s",
                (artifact_id,),
            )
            return cur.fetchone() is not None


def artifact_content(artifact_id: str) -> str:
    if not artifact_id:
        return ""
    init()
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT content FROM harness_artifacts WHERE id = %s",
                (artifact_id,),
            )
            row = cur.fetchone()
    return row[0] if row else ""


def list_artifacts(run_id: str, limit: int = 100) -> list[dict]:
    init()
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, artifact_type, name, content, payload, created_at
                  FROM harness_artifacts
                 WHERE run_id = %s
                 ORDER BY id DESC
                 LIMIT %s
                """,
                (run_id, limit),
            )
            rows = cur.fetchall()
    items = []
    for row in rows:
        payload = row[4]
        if isinstance(payload, str):
            payload = json.loads(payload)
        items.append({
            "id": row[0],
            "artifact_type": row[1],
            "name": row[2],
            "content": row[3],
            "payload": payload,
            "created_at": row[5],
        })
    return items
