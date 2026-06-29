# AI Harness Template Overview

This repository is now a reusable AI harness template plus a real OKR source package:

```text
AINative_OKR_Claude_GHCP/
```

The next major task is to build the OKR website inside that folder using its imported agents, requirements, change requests, Spec-Kit templates, and technical architecture.

## Purpose

The template should let a user run an AI coding flow against a target project through a controlled harness instead of manually driving many prompts and terminal commands.

Target workflow:

```text
User opens dashboard or CLI
  -> selects AINative_OKR_Claude_GHCP as target
  -> enters the OKR website task
  -> selects provider: Claude Code or Codex
  -> starts a harness run
  -> imported OKR agents generate docs, specs, plans, tasks, code, reviews, and tests
  -> gates verify the app
  -> logs, artifacts, status, and costs appear in the dashboard
```

## Repository Structure

```text
apps/
  dashboard/
    backend/              FastAPI API for UI and harness process execution
    frontend/             React dashboard

packages/
  ai-harness/             Python harness engine and CLI
    harness.yaml          Existing Spec-Kit-style config
    harness.sdlc.yaml     Existing generic SDLC config

AINative_OKR_Claude_GHCP/
  .claude/
    agents/               Real Claude Code agents for the OKR flow
    commands/             Slash command wrappers
  .github/
    agents/               GitHub Copilot agent mirror
    prompts/              GitHub Copilot prompt wrappers
  .specify/
    memory/               Constitution
    scripts/              Spec-Kit helper scripts
    templates/            Spec, plan, task, SRS, BD, DD templates
  docs/
    input/                OKR requirements and change requests
    technical_architecture.md
  CLAUDE.md               OKR app build instructions and coding rules
  README.md               Imported AI-SDLC flow documentation

docs/
  architecture.md         Detailed architecture and gap map
  template-overview.md    This practical overview
```

The previous todo demo and reusable Claude SDLC template directories are currently deleted from the working tree, so the docs should no longer present them as active runnable assets.

## What The OKR Source Contains

`AINative_OKR_Claude_GHCP/` contains the real process source for the OKR web application:

| Item | Status |
| --- | --- |
| Claude Code command pack | Present |
| Claude Code agent pack | Present |
| GitHub Copilot agent/prompt mirror | Present |
| Spec-Kit memory, scripts, templates | Present |
| OKR requirements | Present |
| Change requests | Present |
| Technical app architecture | Present |
| Actual backend/frontend code | Not present yet |
| Docker Compose app stack | Not present yet |
| Target-specific harness config | Not present yet |

## OKR Agent Flow

The imported flow is orchestrated by `okr.bossbuiltin` and includes:

| Stage | Agents |
| --- | --- |
| Requirements/design | `okr.srs`, `okr.bd`, `okr.dd`, `okr.srsallsystem` |
| Spec-Kit | `speckit.specify`, `speckit.clarify`, `speckit.plan`, `speckit.tasks`, `speckit.implement`, `speckit.analyze`, `speckit.checklist`, `speckit.taskstoissues` |
| Review | `okr.reviewspec`, `okr.reviewplan`, `okr.reviewcode` |
| Test | `okr.testkit` |
| Orchestration | `okr.bossbuiltin`, plus shared protocols and step files |

The flow produces IPA documents, Spec-Kit artifacts, generated code, review reports, test cases, test reports, and finally a launched local OKR app.

## Harness Standard Fit

The imported OKR source mostly satisfies the prompt-side target project contract:

```text
target-project/
  CLAUDE.md                 present
  .claude/commands/*        present
  .claude/agents/*          present
  .specify/*                present
  docs/input/*              present
```

The missing harness/runtime pieces are:

```text
target-project/
  harness.okr.yaml          missing
  backend/                  missing
  frontend/                 missing
  docker-compose.yml        missing
  package scripts           missing
  build/test/security gates missing
```

This means the source is harness-compatible in shape, but not yet harness-runnable as a real app target.

## Current Harness Capabilities

The Python harness can currently:

- Load YAML phase configs.
- Run Claude Code or Codex CLI.
- Inline `.claude/commands/*.md` for Codex.
- Persist state under `.specify/state`.
- Persist run logs under `.specify/runs`.
- Retry failed agent phases.
- Escalate after max attempts.
- Run deterministic gates: shell, glob, marker checks, and agent-output marker checks.

The implementation is strongest in orchestration and deterministic gates. Context packets, tool audit, security scans, governance approvals, and detailed AgentOps metrics still need deeper implementation.

## Mapping Needed For The OKR Website

Add an OKR-specific harness config in the imported folder:

```text
AINative_OKR_Claude_GHCP/harness.okr.yaml
```

Start with one of these modes:

| Mode | Harness behavior | Use when |
| --- | --- | --- |
| Boss mode | Runs `/okr.bossbuiltin` as one main phase, then gates final outputs | First integration pass |
| Expanded mode | Maps each OKR step to a separate harness phase | Better dashboard visibility and repair control |

Recommended first pass: Boss mode. It keeps the imported flow intact while proving that the folder works as a harness target.

## Gap List

| Gap | Why it matters | Fix |
| --- | --- | --- |
| No OKR harness config | Harness cannot run the imported flow directly | Add `harness.okr.yaml` |
| No generated app code yet | Build/test gates have nothing to run | Scaffold the app in `backend/` and `frontend/` |
| No project scripts | Shell gates cannot verify implementation | Add npm scripts for build, typecheck, lint, test |
| No Docker stack | Target architecture requires local Docker runtime | Add `docker-compose.yml` and Dockerfiles |
| No deterministic OKR artifact gates | Harness cannot prove SRS/BD/DD/spec/plan/tasks were produced | Add glob gates for expected outputs |
| No dashboard target registration | UI may not list the OKR folder | Add target discovery/config for `AINative_OKR_Claude_GHCP/` |
| Boss flow hidden from harness | One command hides individual step status | Use Expanded mode after first pass |
| Security/governance still light | DB resets, secrets, auth, and Docker commands need guardrails | Add security and approval policies |

## Target OKR App Stack

The imported technical architecture specifies:

| Layer | Stack |
| --- | --- |
| Frontend | React 18, Vite 5, React Router, TanStack Query, Axios, React Hook Form, Zod, Tailwind CSS |
| Backend | Node.js 20, NestJS 10, Prisma 5, JWT, bcrypt, Swagger |
| Database | MySQL 8 |
| Local runtime | Docker Compose |
| Test direction | Jest, Vitest/React Testing Library, Playwright |

Planned app layout:

```text
AINative_OKR_Claude_GHCP/
  backend/
    src/
    prisma/
    test/
    Dockerfile
    package.json
  frontend/
    src/
    public/
    Dockerfile
    package.json
  docker/
    wait-for-db.sh
  docker-compose.yml
  docker-compose.test.yml
```

## Next Milestone

The next milestone should be target onboarding for `AINative_OKR_Claude_GHCP/`:

1. Create `harness.okr.yaml`.
2. Register the OKR folder as a dashboard target.
3. Add initial Boss-mode gates for generated docs and final app health.
4. Scaffold backend/frontend/Docker source inside the OKR folder.
5. Replace placeholder gates with real build, typecheck, lint, test, security, and acceptance commands.
6. Split Boss mode into Expanded mode after the first successful end-to-end run.

After these fixes, this repo can move from "harness plus imported source" to "harness-driven OKR app implementation."
