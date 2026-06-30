"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-30
"""
from __future__ import annotations

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS harness_runs (
            run_id          TEXT             PRIMARY KEY,
            feature         TEXT             NOT NULL,
            provider        TEXT             NOT NULL DEFAULT 'codex',
            tech_stack      TEXT             NOT NULL DEFAULT '',
            target          TEXT             NOT NULL DEFAULT 'todo-app',
            mode            TEXT             NOT NULL DEFAULT 'expanded',
            config          TEXT             NOT NULL DEFAULT '',
            target_repo     TEXT             NOT NULL DEFAULT '',
            status          TEXT             NOT NULL DEFAULT 'queued',
            created_at      DOUBLE PRECISION NOT NULL,
            started_at      DOUBLE PRECISION,
            finished_at     DOUBLE PRECISION,
            cost_usd        DOUBLE PRECISION NOT NULL DEFAULT 0.0,
            current_phase   TEXT,
            feature_dir     TEXT,
            log_path        TEXT             NOT NULL DEFAULT '',
            pid             INTEGER,
            return_code     INTEGER,
            command         TEXT
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS phase_events (
            id              BIGSERIAL        PRIMARY KEY,
            run_id          TEXT             NOT NULL REFERENCES harness_runs(run_id) ON DELETE CASCADE,
            phase_name      TEXT             NOT NULL,
            attempt         INTEGER          NOT NULL DEFAULT 1,
            status          TEXT             NOT NULL DEFAULT 'running',
            started_at      DOUBLE PRECISION NOT NULL,
            finished_at     DOUBLE PRECISION,
            gate_result     TEXT,
            prompt_snippet  TEXT,
            agent_ok        BOOLEAN,
            cost_usd        DOUBLE PRECISION NOT NULL DEFAULT 0.0
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS gate_outcomes (
            id              BIGSERIAL        PRIMARY KEY,
            run_id          TEXT             NOT NULL REFERENCES harness_runs(run_id) ON DELETE CASCADE,
            phase_name      TEXT             NOT NULL,
            attempt         INTEGER          NOT NULL DEFAULT 1,
            gate_name       TEXT             NOT NULL,
            gate_type       TEXT             NOT NULL DEFAULT '',
            passed          BOOLEAN          NOT NULL,
            report          TEXT             NOT NULL DEFAULT '',
            checked_at      DOUBLE PRECISION NOT NULL
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS run_events (
            id              BIGSERIAL        PRIMARY KEY,
            run_id          TEXT             NOT NULL REFERENCES harness_runs(run_id) ON DELETE CASCADE,
            event_type      TEXT             NOT NULL,
            phase           TEXT,
            message         TEXT             NOT NULL DEFAULT '',
            payload         JSONB,
            occurred_at     DOUBLE PRECISION NOT NULL
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS harness_run_state (
            run_id          TEXT             PRIMARY KEY REFERENCES harness_runs(run_id) ON DELETE CASCADE,
            state           JSONB            NOT NULL,
            updated_at      DOUBLE PRECISION NOT NULL
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS harness_artifacts (
            id              BIGSERIAL        PRIMARY KEY,
            run_id          TEXT             NOT NULL REFERENCES harness_runs(run_id) ON DELETE CASCADE,
            artifact_type   TEXT             NOT NULL,
            name            TEXT             NOT NULL,
            content         TEXT             NOT NULL DEFAULT '',
            payload         JSONB,
            created_at      DOUBLE PRECISION NOT NULL
        )
    """)

    op.execute("CREATE INDEX IF NOT EXISTS idx_phase_events_run_id    ON phase_events(run_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_gate_outcomes_run_id   ON gate_outcomes(run_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_run_events_run_id      ON run_events(run_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_run_events_occurred_at ON run_events(run_id, occurred_at)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_harness_artifacts_run_id ON harness_artifacts(run_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_harness_artifacts_type   ON harness_artifacts(run_id, artifact_type)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_harness_artifacts_type")
    op.execute("DROP INDEX IF EXISTS idx_harness_artifacts_run_id")
    op.execute("DROP INDEX IF EXISTS idx_run_events_occurred_at")
    op.execute("DROP INDEX IF EXISTS idx_run_events_run_id")
    op.execute("DROP INDEX IF EXISTS idx_gate_outcomes_run_id")
    op.execute("DROP INDEX IF EXISTS idx_phase_events_run_id")
    op.execute("DROP TABLE IF EXISTS harness_artifacts")
    op.execute("DROP TABLE IF EXISTS harness_run_state")
    op.execute("DROP TABLE IF EXISTS run_events")
    op.execute("DROP TABLE IF EXISTS gate_outcomes")
    op.execute("DROP TABLE IF EXISTS phase_events")
    op.execute("DROP TABLE IF EXISTS harness_runs")
