# AI Harness Boilerplate

This repository contains a dashboard-driven AI SDLC harness for running a target
project through controlled context, provider execution, deterministic gates,
Postgres-backed state, and observable phase logs.

The active target in this checkout is `AINative_OKR_Claude_GHCP/`. Generic SDLC
configs are kept under `templates/` as starter material, not as dashboard
runtime config.

## Folder Structure

```text
apps/
  dashboard/
    backend/              FastAPI API for starting and observing harness runs
    frontend/             React dashboard for non-terminal users

packages/
  ai-harness/             Python harness engine, CLI, and package-owned adapters
    targets/okr-ghcp/     OKR expanded and boss-mode adapters

harness/
  layers/                 H1-H7 blueprint and policies
  targets/okr-ghcp/       Target registry metadata

templates/
  generic-sdlc/           Copyable generic YAML adapter templates

AINative_OKR_Claude_GHCP/
  .claude/                Imported OKR command and agent pack
  .github/                GitHub Copilot prompt/agent mirror
  .specify/               Spec-Kit scripts, memory, and templates
  docs/input/             OKR requirements and change requests
```

## Dashboard Runtime Flow

The dashboard does not use `templates/generic-sdlc/harness.sdlc.yaml`.

Current run path:

```text
Frontend POST /api/harness-runs
  -> backend selects packages/ai-harness/targets/okr-ghcp/harness.okr.yaml
  -> backend spawns python -m cli run
  -> packages/ai-harness/src/orchestration/orchestrator.py executes phases
  -> gates/state/artifacts/events are written to Postgres
  -> frontend polls /api/harness-runs/* endpoints
```

The boss-mode adapter is available at:

```text
packages/ai-harness/targets/okr-ghcp/harness.okr.boss.yaml
```

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

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Health check: http://localhost:8000/health

If backend port `8000` is already in use:

```bash
cd apps/dashboard/backend
PORT=8010 ./start.sh
```

```bash
cd apps/dashboard/frontend
VITE_API_BASE=http://localhost:8010 npm run dev -- --port 5174
```

## Run The Harness CLI Directly

```bash
PYTHONPATH=packages/ai-harness/src python3 -m cli run \
  --feature "Build the OKR web application" \
  --repo AINative_OKR_Claude_GHCP \
  --config packages/ai-harness/targets/okr-ghcp/harness.okr.yaml \
  --provider codex
```

## Generic Templates

`templates/generic-sdlc/` contains copyable starter YAML configs:

- `harness.yaml`: Spec-Kit-style generic adapter template.
- `harness.sdlc.yaml`: plain SDLC command-pack adapter template.

Copy one into a target project and replace its placeholder `project` commands
before relying on gates. These files are intentionally outside
`packages/ai-harness/` because they are templates, not runtime package config.

## Dashboard API

Real harness runner endpoints:

- `POST /api/harness-runs`
- `GET /api/harness-runs/latest`
- `GET /api/harness-runs/{run_id}`
- `POST /api/harness-runs/{run_id}/stop`
- `GET /api/harness-targets`

## Architecture

Read [docs/template-overview.md](docs/template-overview.md) for the practical
overview and [docs/architecture.md](docs/architecture.md) for the H1-H7 model.
