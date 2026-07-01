"""Add 'md' file type and a doc_type category to file_extractions

Raw Markdown uploads need no extraction step — their text content is used
as-is. doc_type records which part of the harness context the uploaded
document should feed (requirement, change-request, architecture) so the
API layer knows where to place it in the target repo.

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-02
"""
from __future__ import annotations

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_enum e
                JOIN pg_type t ON e.enumtypid = t.oid
                WHERE t.typname = 'file_type_enum' AND e.enumlabel = 'md'
            ) THEN
                ALTER TYPE file_type_enum ADD VALUE 'md';
            END IF;
        END
        $$;
    """)
    op.execute(
        "ALTER TABLE file_extractions "
        "ADD COLUMN IF NOT EXISTS doc_type TEXT NOT NULL DEFAULT 'requirement'"
    )


def downgrade() -> None:
    # Postgres does not support removing a value from an enum type; the 'md'
    # label is left in place on downgrade.
    op.execute("ALTER TABLE file_extractions DROP COLUMN IF EXISTS doc_type")
