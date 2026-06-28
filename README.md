# AI Harness Template

This repository is a template for running AI coding agents through a controlled SDLC harness. It is intended to work as a reusable control plane for arbitrary target projects, whether they already have their own prompts or need fallback SDLC prompts from this repo.

## Folder Structure

```text
apps/
  dashboard/
    backend/              FastAPI API for starting and observing harness runs
    frontend/             React dashboard for non-terminal users

packages/
  ai-harness/             Python harness engine and CLI

templates/
  claude-sdlc/            Reusable Claude Code prompt pack

examples/
  todo-app/               Demo target project used for end-to-end testing

docs/
  architecture.md         7-component harness architecture
```

## What This Template Provides

- A dashboard-first flow: enter a task, choose provider, click `Start task`.
- A Python harness engine with phase orchestration, retry, state, logs, and gates.
- Provider support for Claude Code and Codex CLI.
- A reusable `.claude` SDLC prompt pack under `templates/claude-sdlc/`.
- A Todo demo target project to validate the full flow.
- Architecture documentation for H1-H7 harness components.

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

From the dashboard:

1. Enter a task, for example `Build a browser Todo UI for the demo app with add, complete, delete, and persistent tasks`.
2. Choose `Codex` or `Claude Code`.
3. Click `Start task`.
4. Watch SDLC phases, logs, and generated artifacts.

If backend port `8000` is already in use:

```bash
cd apps/dashboard/backend
PORT=8010 ./start.sh
```

```bash
cd apps/dashboard/frontend
VITE_API_BASE=http://localhost:8010 npm run dev -- --port 5174
```

## Demo Target Project

`examples/todo-app/` is a dependency-free Node.js CLI app used as a target repository. It has its own local `.claude/commands`, harness configs, tests, acceptance checks, and security check.

Validate it directly:

```bash
cd examples/todo-app
npm run build
npm run typecheck
npm run lint
npm test
npm run acceptance
npm run security
```

Run the harness from the repo root:

```bash
PYTHONPATH=packages/ai-harness/src python3 -m spec_harness run \
  --feature "Add priority support to todo tasks" \
  --repo examples/todo-app \
  --config harness.yaml
```

Run with Codex:

```bash
PYTHONPATH=packages/ai-harness/src python3 -m spec_harness run \
  --feature "Add due date support to todo tasks" \
  --repo examples/todo-app \
  --config harness.codex.yaml
```

## Using This With Another Project

The target project should provide or be adapted into a harness contract:

```text
target-project/
  CLAUDE.md or equivalent project guidance
  .claude/commands/* or custom prompt mapping
  harness.yaml
  build/typecheck/lint/test/security/acceptance commands
```

For a project that does not already have prompts, copy the template prompt pack:

```bash
cp -R templates/claude-sdlc/.claude /path/to/target-project/.claude
cp templates/claude-sdlc/CLAUDE.md /path/to/target-project/CLAUDE.md
```

Then create or adapt a `harness.yaml` in the target project and run:

```bash
PYTHONPATH=packages/ai-harness/src python3 -m spec_harness run \
  --feature "Your feature request" \
  --repo /path/to/target-project \
  --config harness.yaml
```

## Dashboard API

Real harness runner endpoints:

- `POST /api/harness-runs`
- `GET /api/harness-runs/latest`
- `GET /api/harness-runs/{run_id}`
- `POST /api/harness-runs/{run_id}/stop`
- `GET /api/harness-targets`

Legacy simulator endpoints are still present for comparison:

- `GET /api/dashboard`
- `GET /api/runs`
- `POST /api/runs`
- `GET /api/runs/{run_id}`

## Architecture

Read [docs/architecture.md](docs/architecture.md) for the full H1-H7 model:

- H1 Context Harness
- H2 Tool Harness
- H3 Evaluation Harness
- H4 Security Harness
- H5 Governance Harness
- H6 AgentOps Harness
- H7 Orchestration Harness

