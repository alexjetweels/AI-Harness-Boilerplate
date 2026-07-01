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
    targets/okr-ghcp/     Active OKR expanded and boss-mode adapters

templates/
  generic-sdlc/           Copyable generic YAML adapter templates

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

The previous todo demo and reusable Claude SDLC template directories are not
present in this checkout, so the dashboard and docs should not present them as
active runnable assets.

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
| Target-specific harness config | Present |

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

The active harness/runtime adapter pieces are:

```text
packages/ai-harness/targets/okr-ghcp/
  harness.okr.yaml          expanded-mode dashboard adapter
  harness.okr.boss.yaml     boss-mode dashboard adapter
  commands/*                fallback command wrappers
```

The missing generated-app pieces are:

```text

target-project/
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
- Persist run state, events, gates, and artifacts to Postgres.
- Retry failed agent phases.
- Escalate after max attempts.
- Run deterministic gates: shell, glob, marker checks, DB artifact checks,
  secret scans, and agent-output marker checks.

The implementation is strongest in orchestration and deterministic gates. Context packets, tool audit, security scans, governance approvals, and detailed AgentOps metrics still need deeper implementation.

## Mapping Needed For The OKR Website

The OKR-specific harness config is package-owned:

```text
packages/ai-harness/targets/okr-ghcp/harness.okr.yaml
```

Start with one of these modes:

| Mode | Harness behavior | Use when |
| --- | --- | --- |
| Boss mode | Runs `/okr.bossbuiltin` as one main phase, then gates final outputs | First integration pass |
| Expanded mode | Maps each OKR step to a separate harness phase | Better dashboard visibility and repair control |

Dashboard runs currently default to Expanded mode because it exposes each OKR
step as a separate phase for retries, gates, and UI inspection. Boss mode is
kept as a compatibility adapter for one-shot `/okr.bossbuiltin` runs.

## Gap List

| Gap | Why it matters | Fix |
| --- | --- | --- |
| No target-owned OKR harness config | Intentional: target source should stay unchanged | Keep adapter under `packages/ai-harness/targets/okr-ghcp/` |
| No generated app code yet | Build/test gates have nothing to run | Scaffold the app in `backend/` and `frontend/` |
| No project scripts | Shell gates cannot verify implementation | Add npm scripts for build, typecheck, lint, test |
| No Docker stack | Target architecture requires local Docker runtime | Add `docker-compose.yml` and Dockerfiles |
| Some app gates cannot pass before app scaffold exists | Harness cannot verify generated source yet | Replace placeholder source assumptions as the generated app stabilizes |
| Boss flow hidden from harness | One command hides individual step status | Keep dashboard default on Expanded mode |
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

The next milestone should be generated-app onboarding for `AINative_OKR_Claude_GHCP/`:

1. Keep OKR adapters in `packages/ai-harness/targets/okr-ghcp/`.
2. Scaffold backend/frontend/Docker source inside the OKR folder.
3. Replace placeholder gates with real build, typecheck, lint, test, security, and acceptance commands.
4. Keep generic YAML examples under `templates/generic-sdlc/` until they are copied into a real target.

After these fixes, this repo can move from "harness plus imported source" to "harness-driven OKR app implementation."
