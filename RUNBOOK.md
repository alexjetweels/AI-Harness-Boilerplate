# Runbook — Restart The Dashboard

First time only:

```bash
cp .env.example .env   # if .env doesn't exist yet
```

## Start (3 commands, 2 terminals)

```bash
docker compose up -d
```

```bash
cd apps/dashboard/backend && ./start.sh
```

```bash
cd apps/dashboard/frontend && npm install && npm run dev
```

`start.sh` installs deps, runs `alembic upgrade head` against Postgres, then
starts the API — no separate migrate step needed.

## Verify

- Frontend: http://localhost:5173
- Backend health: http://localhost:8000/health

## Stop

```bash
docker compose down       # keeps DB data (named volume)
```
