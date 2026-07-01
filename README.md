# AI Harness Boilerplate

This repository is a boilerplate for running AI coding agents through a gated
SDLC harness. The harness is the outer control plane: it builds context,
dispatches an AI provider, runs deterministic gates, stores run state, and
surfaces progress through a dashboard.

The current checked-in target is the OKR source package in
`AINative_OKR_Claude_GHCP/`.

## Current Repository Shape

```text
apps/
  dashboard/
    backend/              FastAPI API for starting and observing harness runs
    frontend/             React/Vite dashboard for run history and pipeline views

packages/
  ai-harness/             Python harness engine and CLI
    src/                  Layered harness source
    targets/okr-ghcp/     Package-owned OKR target adapters and fallback commands
    harness.yaml          Spec-Kit-oriented generic config
    harness.sdlc.yaml     Generic SDLC config with placeholder project commands

harness/
  layers/                 H1-H7 policy blueprints
  targets/okr-ghcp/       Target registry metadata

AINative_OKR_Claude_GHCP/
  .claude/                Imported Claude commands and agents
  .github/                GitHub Copilot prompt/agent mirror
  .specify/               Spec-Kit memory, scripts, and templates
  docs/input/             OKR requirements and change requests
  docs/technical_architecture.md

docs/
  architecture.md         Folder-by-folder architecture and current gap map
  template-overview.md    Practical overview of the harness and OKR target

docker-compose.yml        Postgres service for harness persistence
```

## What Is Implemented

- FastAPI backend for targets, harness runs, phases, gates, events, artifacts,
  token usage, and raw subprocess logs.
- React dashboard with run history, new run form, pipeline visualization,
  phase details, gate outcomes, events, artifacts, and system log tail.
- Python harness CLI with `run`, `resume`, and `status` commands.
- Provider dispatch for `codex` and `claude`.
- OKR target adapters:
  - expanded mode: `packages/ai-harness/targets/okr-ghcp/harness.okr.yaml`
  - boss mode: `packages/ai-harness/targets/okr-ghcp/harness.okr.boss.yaml`
- H1 context packet/manifest generation, H3 gates, H4 secret scan gate,
  H5 escalation, H6 Postgres-backed state/logging/artifacts, and H7 phase
  orchestration.

## Current Limitations

- `AINative_OKR_Claude_GHCP/` is currently a prompt/spec source package. It does
  not yet contain the generated OKR application source such as `backend/`,
  `frontend/`, app Dockerfiles, or target `docker-compose.yml`.
- The OKR target adapters already define build, typecheck, lint, test, security,
  and acceptance gates, but those gates depend on app source that has not been
  generated yet.
- `packages/ai-harness/harness.sdlc.yaml` is a generic template and intentionally
  contains placeholder commands that fail until configured for a real target.
- The frontend has an attachment UI, but the backend does not currently expose
  `/api/file-extractions`; uploads are attempted in the background and ignored
  if that endpoint is unavailable.

## Prerequisites

- Python 3.11+ for `packages/ai-harness`
- Python 3.12+ and Poetry for `apps/dashboard/backend`
- Node.js and npm for `apps/dashboard/frontend`
- Docker, if you want local Postgres via `docker-compose.yml`
- `codex` or `claude` available on `PATH` for real provider runs

## Run Postgres

The committed Compose file publishes Postgres on `localhost:5432`.

```bash
docker compose up -d postgres
```

Use this connection string with the committed Compose defaults:

```bash
DATABASE_URL=postgresql://harness:harness_dev@localhost:5432/harness
```

Set it in your shell or in the root `.env` file loaded by
`apps/dashboard/backend/start.sh`. If you change the Compose port, update
`DATABASE_URL` accordingly. The backend continues without persistence if the
database is unavailable, but real harness observability is designed around
Postgres.

## Run The Dashboard

Backend:

```bash
cd apps/dashboard/backend
./start.sh
```

Frontend, in a second terminal:

```bash
cd apps/dashboard/frontend
npm install
npm run dev
```

Open:

- Frontend: <http://localhost:5173>
- Backend API: <http://localhost:8000>
- Health check: <http://localhost:8000/health>


## Dashboard Flow

1. Open the dashboard.
2. Go to `New Run`.
3. Enter a task, for example:

   ```text
   Build the OKR web application from the imported requirements, change requests, and technical architecture
   ```

4. Choose `Codex` or `Claude Code`.
5. Start the run and inspect the pipeline page.

By default, the backend targets `AINative_OKR_Claude_GHCP/` with OKR expanded
mode. The backend also has conditional support for a `todo-app` target only if
`examples/todo-app/` exists locally.

## Run The Harness CLI

Without installing the package:

```bash
PYTHONPATH=packages/ai-harness/src python -m cli --help
```

PowerShell equivalent:

```powershell
$env:PYTHONPATH = "packages/ai-harness/src"
python -m cli --help
```

Run the OKR expanded adapter:

```bash
PYTHONPATH=packages/ai-harness/src python -m cli run \
  --repo AINative_OKR_Claude_GHCP \
  --config packages/ai-harness/targets/okr-ghcp/harness.okr.yaml \
  --provider codex \
  --feature "Build the OKR web application from the imported requirements"
```

Run the OKR boss adapter:

```bash
PYTHONPATH=packages/ai-harness/src python -m cli run \
  --repo AINative_OKR_Claude_GHCP \
  --config packages/ai-harness/targets/okr-ghcp/harness.okr.boss.yaml \
  --provider codex \
  --feature "Build the OKR web application from the imported requirements"
```

After installing the package, the script entrypoint is `harness`:

```bash
pip install -e ./packages/ai-harness
harness --help
```

For DB-backed CLI logging, set `HARNESS_DB_URL` or `DATABASE_URL` before running
the command.

## Dashboard API

Harness-run endpoints:

- `GET /api/harness-targets`
- `GET /api/harness-runs`
- `POST /api/harness-runs`
- `GET /api/harness-runs/latest`
- `GET /api/harness-runs/{run_id}`
- `POST /api/harness-runs/{run_id}/stop`
- `GET /api/harness-runs/{run_id}/events`
- `GET /api/harness-runs/{run_id}/gates`
- `GET /api/harness-runs/{run_id}/phases`
- `GET /api/harness-runs/{run_id}/token-usage`
- `GET /api/harness-runs/{run_id}/artifacts/{artifact_id}`
- `GET /api/harness-runs/{run_id}/log`

Legacy simulator endpoints are still present:

- `GET /api/runs`
- `POST /api/runs`
- `GET /api/runs/{run_id}`

## Architecture

Read [docs/architecture.md](docs/architecture.md) for the current
folder-by-folder architecture, H1-H7 placement, persistence model, runtime flow,
and hardening gaps.

Read [docs/template-overview.md](docs/template-overview.md) for the broader
template narrative around the OKR target.

Harness layers:

- H1 Context Harness
- H2 Tool Harness
- H3 Evaluation Harness
- H4 Security Harness
- H5 Governance Harness
- H6 AgentOps Harness
- H7 Orchestration Harness

## Useful Checks

Frontend build:

```bash
cd apps/dashboard/frontend
npm run build
```

Harness CLI smoke check:

```bash
PYTHONPATH=packages/ai-harness/src python -m cli --help
```

Backend import/startup checks require the backend dependencies from Poetry and,
for full persistence behavior, a reachable Postgres database.
