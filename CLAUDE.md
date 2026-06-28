# AI Harness Boilerplate

This repository is a boilerplate for running a gated SDLC workflow around Claude Code.

## Repository Shape

- `frontend/`: React dashboard for observing harness runs.
- `backend/`: FastAPI API for dashboard data. The current API simulates runs unless wired to the CLI.
- `spec-harness/`: Python CLI that drives Claude Code in headless mode through SDLC phases and deterministic gates.
- `.claude/`: Reusable Claude Code SDLC prompt pack for any project.
- `docs/`: Architecture and operating documentation.

## Default Working Rules

- Prefer small, reviewable changes that preserve the existing architecture.
- Read local docs, configs, and package files before making implementation assumptions.
- Keep generated SDLC artifacts under `docs/sdlc/current/` unless a project-specific location already exists.
- Run the narrowest meaningful checks before declaring work complete.
- Do not claim build, lint, typecheck, tests, or security checks passed unless you actually ran them.
- If a required check is unavailable, record the reason and the residual risk.

## Quality Bar

Every SDLC run should leave behind:

- A requirements or intake artifact.
- A design or architecture decision when behavior crosses module boundaries.
- A task plan with verification mapped to each task.
- Implementation notes with changed files and commands run.
- Review, test, and security findings.
- Release notes or an explicit "not releasable yet" decision.

## Project Commands

When available, use these commands:

```bash
cd backend && ./start.sh
cd frontend && npm run dev
cd frontend && npm run build
```

For the generic harness, configure real commands in `spec-harness/harness.sdlc.yaml` before relying on gates.

