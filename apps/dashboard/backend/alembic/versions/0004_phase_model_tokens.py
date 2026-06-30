"""Track model and token usage per phase attempt

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-30
"""
from __future__ import annotations

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE phase_events ADD COLUMN IF NOT EXISTS model TEXT NOT NULL DEFAULT ''")
    op.execute("ALTER TABLE phase_events ADD COLUMN IF NOT EXISTS input_tokens BIGINT NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE phase_events ADD COLUMN IF NOT EXISTS output_tokens BIGINT NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE phase_events ADD COLUMN IF NOT EXISTS total_tokens BIGINT NOT NULL DEFAULT 0")
    op.execute("CREATE INDEX IF NOT EXISTS idx_phase_events_tokens ON phase_events(run_id, total_tokens DESC)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_phase_events_tokens")
    op.execute("ALTER TABLE phase_events DROP COLUMN IF EXISTS total_tokens")
    op.execute("ALTER TABLE phase_events DROP COLUMN IF EXISTS output_tokens")
    op.execute("ALTER TABLE phase_events DROP COLUMN IF EXISTS input_tokens")
    op.execute("ALTER TABLE phase_events DROP COLUMN IF EXISTS model")
