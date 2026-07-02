#!/usr/bin/env sh
set -eu

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"

# Load .env from repo root if it exists
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
if [ -f "$ROOT/.env" ]; then
  # shellcheck disable=SC1090
  set -a && . "$ROOT/.env" && set +a
  echo "Loaded .env from $ROOT/.env"
fi

echo "DATABASE_URL=${DATABASE_URL:-'(not set — DB logging disabled)'}"

if command -v poetry >/dev/null 2>&1; then
  POETRY="poetry"
elif python -m poetry --version >/dev/null 2>&1; then
  POETRY="python -m poetry"
elif [ -x "$HOME/Library/Python/3.13/bin/poetry" ]; then
  POETRY="$HOME/Library/Python/3.13/bin/poetry"
else
  echo "Poetry is required. Install it first: python -m pip install --user poetry" >&2
  exit 1
fi

$POETRY install
$POETRY run alembic upgrade head
exec $POETRY run uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
