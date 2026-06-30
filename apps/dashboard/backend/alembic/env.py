from __future__ import annotations

import os
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import create_engine, pool

config = context.config

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parents[2]

load_dotenv(REPO_ROOT / ".env", override=False)
load_dotenv(BACKEND_DIR / ".env", override=False)


def _get_url() -> str:
    url = os.environ.get("DATABASE_URL") or os.environ.get("HARNESS_DB_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. "
            "Copy .env.example to .env and set DATABASE_URL."
        )
    # Ensure the driver dialect is explicit so SQLAlchemy doesn't warn.
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://") and "+psycopg2" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def run_migrations_online() -> None:
    connectable = create_engine(_get_url(), poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=None,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
