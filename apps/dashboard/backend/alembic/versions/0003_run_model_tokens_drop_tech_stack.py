"""Track run model and token usage

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-30
"""
from __future__ import annotations

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE harness_runs ADD COLUMN IF NOT EXISTS model TEXT NOT NULL DEFAULT ''")
    op.execute("ALTER TABLE harness_runs ADD COLUMN IF NOT EXISTS input_tokens BIGINT NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE harness_runs ADD COLUMN IF NOT EXISTS output_tokens BIGINT NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE harness_runs ADD COLUMN IF NOT EXISTS total_tokens BIGINT NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE harness_runs DROP COLUMN IF EXISTS tech_stack")


def downgrade() -> None:
    op.execute("ALTER TABLE harness_runs ADD COLUMN IF NOT EXISTS tech_stack TEXT NOT NULL DEFAULT ''")
    op.execute("ALTER TABLE harness_runs DROP COLUMN IF EXISTS total_tokens")
    op.execute("ALTER TABLE harness_runs DROP COLUMN IF EXISTS output_tokens")
    op.execute("ALTER TABLE harness_runs DROP COLUMN IF EXISTS input_tokens")
    op.execute("ALTER TABLE harness_runs DROP COLUMN IF EXISTS model")
