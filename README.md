# AI Harness Boilerplate

Harness dashboard with:

- React frontend dashboard
- FastAPI harness API
- Existing `spec-harness` Python CLI preserved under `spec-harness/`
- Coverage for Context, Tool, Evaluation, Security, Governance, AgentOps, and Orchestration harnesses
- Reusable Claude Code SDLC prompt pack under `.claude/`
- Architecture documentation in `docs/architecture.md`

## Run Directly

Backend:

```bash
cd backend
./start.sh
```

Frontend, in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Health check: http://localhost:8000/health

From the dashboard, use the task launcher to run the harness against the Todo demo target without typing the CLI command manually:

1. Enter a task, for example `Build a browser Todo UI for the demo app with add, complete, delete, and persistent tasks`.
2. Choose `Codex` or `Claude Code`.
3. Click `Start task`.
4. Watch SDLC phases, logs, and generated artifacts in the dashboard.

If backend port `8000` is already in use, run the backend on another port and set the frontend API base:

```bash
cd backend
PORT=8010 ./start.sh
```

```bash
cd frontend
VITE_API_BASE=http://localhost:8010 npm run dev -- --port 5174
```

## API

- `GET /health` - backend health check
- `GET /api/dashboard` - readiness, harness components, workflow stages, and latest run
- `GET /api/runs` - all in-memory runs
- `POST /api/runs` - create a simulated harness run
- `GET /api/runs/{run_id}` - inspect one run

Example:

```bash
curl -X POST http://localhost:8000/api/runs \
  -H "Content-Type: application/json" \
  -d '{"feature":"Add secure multi-agent review workflow"}'
```

## Harness Components

The dashboard models the seven requested harness layers:

- H1 Context Harness: context packets, spec layering, run memory
- H2 Tool Harness: registry, schemas, Docker command chains, rate limits
- H3 Evaluation Harness: deterministic gates, golden cases, judge checks
- H4 Security Harness: prompt-injection scan, credential audit, leakage detection
- H5 Governance Harness: approvals, immutable audit log, risk registry
- H6 AgentOps Harness: cost, drift, hallucination risk, trace metrics
- H7 Orchestration Harness: DAG lanes, retry loop, repair loop, dispatch

The current API uses an in-memory simulator so the UI visibly progresses. To connect a real agent run, wire `POST /api/runs` to call the existing `spec-harness` CLI in `spec-harness/src/spec_harness/orchestrator.py` and stream its state files from `.specify/state`.

## Claude Code SDLC Prompt Pack

This repo includes a generic Claude Code prompt pack:

- `CLAUDE.md` and nested guidance files for persistent project memory
- `.claude/rules/` for engineering, architecture, testing, and security rules
- `.claude/commands/sdlc.*.md` for intake through release
- `.claude/agents/` for specialist roles
- `spec-harness/harness.sdlc.yaml` for a non-spec-kit SDLC pipeline

Read `docs/architecture.md` for the component model, runtime flow, and extension points.

## Demo Target Project

`examples/todo-app/` is a small dependency-free Node.js CLI app used to test the harness against a real target repository.

Validate the app directly:

```bash
cd examples/todo-app
npm run build
npm run typecheck
npm run lint
npm test
npm run acceptance
npm run security
```

Run the SDLC harness against the demo target:

```bash
PYTHONPATH=spec-harness/src python3 -m spec_harness run \
  --feature "Add priority support to todo tasks" \
  --repo examples/todo-app \
  --config harness.yaml
```

Run the same target through the Codex provider:

```bash
PYTHONPATH=spec-harness/src python3 -m spec_harness run \
  --feature "Add due date support to todo tasks" \
  --repo examples/todo-app \
  --config harness.codex.yaml
```

The harness runs inside `examples/todo-app`, so Claude Code edits the demo app source and writes SDLC artifacts under `examples/todo-app/docs/sdlc/current/`.

The dashboard calls the same runner through:

- `POST /api/harness-runs`
- `GET /api/harness-runs/latest`
- `GET /api/harness-runs/{run_id}`
- `POST /api/harness-runs/{run_id}/stop`
