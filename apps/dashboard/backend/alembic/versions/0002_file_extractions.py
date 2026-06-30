"""File extraction table for Excel, TXT, and PDF uploads

Stores uploaded files and their extracted Markdown content so downstream
harness phases can consume structured text without re-parsing on every run.

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-30
"""
from __future__ import annotations

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TYPE IF NOT EXISTS file_type_enum AS ENUM ('excel', 'txt', 'pdf')
    """)

    op.execute("""
        CREATE TYPE IF NOT EXISTS extraction_status_enum AS ENUM (
            'pending', 'processing', 'complete', 'failed'
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS file_extractions (
            id                  BIGSERIAL        PRIMARY KEY,

            -- Optional link to a harness run; NULL means the file was uploaded
            -- standalone and is not yet associated with a run.
            run_id              TEXT             REFERENCES harness_runs(run_id) ON DELETE SET NULL,

            original_filename   TEXT             NOT NULL,
            file_type           file_type_enum   NOT NULL,
            file_size_bytes     BIGINT           NOT NULL DEFAULT 0,

            -- Path on the server where the raw upload is stored.
            storage_path        TEXT             NOT NULL DEFAULT '',

            -- Extracted content rendered as Markdown.
            extracted_markdown  TEXT             NOT NULL DEFAULT '',

            -- For Excel: sheet names that were extracted (JSON array of strings).
            sheet_names         JSONB,

            -- For PDF: total page count.
            page_count          INTEGER,

            extraction_status   extraction_status_enum NOT NULL DEFAULT 'pending',
            error_message       TEXT,

            created_at          DOUBLE PRECISION NOT NULL,
            extracted_at        DOUBLE PRECISION
        )
    """)

    op.execute("CREATE INDEX IF NOT EXISTS idx_file_extractions_run_id ON file_extractions(run_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_file_extractions_status ON file_extractions(extraction_status)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_file_extractions_type   ON file_extractions(file_type)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_file_extractions_type")
    op.execute("DROP INDEX IF EXISTS idx_file_extractions_status")
    op.execute("DROP INDEX IF EXISTS idx_file_extractions_run_id")
    op.execute("DROP TABLE  IF EXISTS file_extractions")
    op.execute("DROP TYPE   IF EXISTS extraction_status_enum")
    op.execute("DROP TYPE   IF EXISTS file_type_enum")
