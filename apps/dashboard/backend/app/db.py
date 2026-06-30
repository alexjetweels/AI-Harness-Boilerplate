"""PostgreSQL database connection and Alembic-managed schema migrations.

Uses psycopg2 (sync) for runtime queries and SQLAlchemy+Alembic for schema
versioning. Schema changes must go through a versioned migration in
alembic/versions/ — never alter the database directly in application code.

Environment:
    DATABASE_URL  – full libpq DSN, e.g.
                    postgresql://harness:harness_dev@localhost:5432/harness
"""
from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool

_pool: ThreadedConnectionPool | None = None
_lock = threading.Lock()


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


# ── Alembic migration runner ──────────────────────────────────────────────────

def run_migrations() -> None:
    """Apply all pending Alembic migrations. Safe to call on every startup."""
    from alembic.config import Config
    from alembic import command

    ini_path = Path(__file__).resolve().parents[1] / "alembic.ini"
    alembic_cfg = Config(str(ini_path))
    command.upgrade(alembic_cfg, "head")
    print("✅ Database migrations applied (Alembic)")


# ── Back-compat alias so any code still calling init_db() keeps working ───────

def init_db() -> None:
    run_migrations()
