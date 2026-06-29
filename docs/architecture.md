# AI SDLC Harness Architecture

This repository is now a harness workspace for building the real OKR web application from the imported source package:

```text
AINative_OKR_Claude_GHCP/
```

The imported folder is not yet the OKR app implementation. It is the real OKR agent, prompt, Spec-Kit, requirements, and architecture source that should drive the future app build inside that folder.

## Current Workspace Shape

```text
apps/
  dashboard/
    backend/              FastAPI API for launching and observing harness runs
    frontend/             React dashboard for non-terminal harness users

packages/
  ai-harness/             Python harness engine, CLI, phase configs, gates

AINative_OKR_Claude_GHCP/
  .claude/
    agents/               Claude Code agent definitions
    commands/             Claude Code slash command wrappers
  .github/
    agents/               GitHub Copilot agent mirror
    prompts/              GitHub Copilot prompt wrappers
  .specify/
    memory/               Spec-Kit constitution
    scripts/              Spec-Kit helper scripts
    templates/            Spec, plan, tasks, SRS, BD, DD templates
  docs/
    input/                OKR requirements and change requests
    technical_architecture.md

docs/
  architecture.md         This architecture and gap map
  template-overview.md    Practical template overview
```

The old `templates/claude-sdlc/` and `examples/todo-app/` paths are no longer present in the working tree. The docs should treat `AINative_OKR_Claude_GHCP/` as the primary target project source.

## Mental Model

There are two orchestration layers:

```text
User / Dashboard / CLI
        |
        v
AI Harness control plane
  - run state
  - provider execution
  - deterministic gates
  - logs and escalation
        |
        v
Target project agent flow
  - AINative_OKR_Claude_GHCP/.claude/commands/*
  - AINative_OKR_Claude_GHCP/.claude/agents/*
  - AINative_OKR_Claude_GHCP/.specify/*
        |
        v
Generated OKR application code and artifacts
```

The harness should remain the outer control plane. The imported OKR `okr.bossbuiltin` agent can remain the inner domain-specific flow, but the harness needs a configuration that understands its phases and output artifacts.

## Imported OKR Source

The imported source contains a complete AI-SDLC prompt system:

| Area | Source | Purpose |
| --- | --- | --- |
| Claude commands | `AINative_OKR_Claude_GHCP/.claude/commands/` | Slash command entrypoints such as `/okr.bossbuiltin`, `/speckit.specify`, `/speckit.plan`, `/speckit.implement` |
| Claude agents | `AINative_OKR_Claude_GHCP/.claude/agents/` | Full agent definitions for OKR, review, test, and Spec-Kit flow |
| Shared protocols | `AINative_OKR_Claude_GHCP/.claude/agents/protocols/` | Retry, report gate, timestamp, logging, context, and delegation protocols |
| Step definitions | `AINative_OKR_Claude_GHCP/.claude/agents/steps/` | Grouped orchestration instructions for steps 01-13 |
| Output templates | `AINative_OKR_Claude_GHCP/.claude/agents/templates/` | Pipeline completion and report templates |
| GitHub Copilot mirror | `AINative_OKR_Claude_GHCP/.github/agents/` and `.github/prompts/` | Agent/prompt equivalents for GHCP workflows |
| Spec-Kit runtime | `AINative_OKR_Claude_GHCP/.specify/` | Constitution, feature scripts, and artifact templates |
| OKR requirements | `AINative_OKR_Claude_GHCP/docs/input/okr-requirement.md` | Main functional source input |
| Change requests | `AINative_OKR_Claude_GHCP/docs/input/change-request/` | Incremental scope changes |
| App architecture | `AINative_OKR_Claude_GHCP/docs/technical_architecture.md` | Target OKR web app architecture |

The OKR app architecture currently targets:

| Layer | Target |
| --- | --- |
| Frontend | React 18, Vite 5, React Router, TanStack Query, Axios, React Hook Form, Zod, Tailwind CSS |
| Backend | Node.js 20, NestJS 10, Prisma 5, JWT auth, bcrypt, Swagger |
| Database | MySQL 8 with Prisma migrations and seed data |
| Runtime | Docker Compose with MySQL, backend, frontend, and Adminer |

## Imported OKR Flow

The OKR source defines a 13-step AI-SDLC flow orchestrated by `okr.bossbuiltin`:

| Step | Agent | Main output |
| --- | --- | --- |
| 1 | `okr.srs` | IPA SRS documents |
| 2 | `okr.bd` | Basic Design documents |
| 3 | `speckit.specify` | `spec.md` |
| 4 | `speckit.clarify` | Ambiguity resolution |
| 5 | `okr.reviewspec` | Spec review and retry feedback |
| 6 | `speckit.plan` | `plan.md`, data model, contracts |
| 7 | `okr.reviewplan` | Plan review and retry feedback |
| 8 | `okr.dd` | Detail Design documents |
| 8b | `okr.testkit` | Generated test cases |
| 9 | `speckit.tasks` | `tasks.md` |
| 10 | `speckit.implement` | Application code with build/fix loop |
| 11 | `okr.reviewcode` | Code review and DB data check |
| 12 | `okr.testkit` | Test execution with back-to-plan behavior |
| 13 | Boss direct step | Build backend, connect DB, build frontend, launch UI |

This flow is richer than the generic SDLC flow previously documented in this repo.

## Harness Standard

The current harness standard is implemented in:

```text
packages/ai-harness/src/spec_harness/
  cli.py
  config.py
  state.py
  orchestrator.py
  agent.py
  gates.py
  db_logger.py
```

The current harness expects:

```text
target-project/
  CLAUDE.md
  .claude/commands/*.md
  .specify/state/
  .specify/runs/
  harness.yaml or another selected harness config
  project build/typecheck/lint/test/security/acceptance commands
```

Current supported providers:

| Provider | Implementation |
| --- | --- |
| Claude Code | `claude -p --output-format json` |
| Codex CLI | `codex exec --json`; slash commands are inlined from `.claude/commands/*.md` |

Current gates:

| Gate type | Purpose |
| --- | --- |
| `shell` | Run a command and pass on exit code `0` |
| `glob_nonempty` | Require matching artifact files |
| `no_markers` | Fail if generated artifacts still contain markers such as `TBD` |
| `agent_output` | Fail if agent output contains configured blocking markers |

Current state and run outputs:

```text
.specify/state/<run-id>.json
.specify/runs/<run-id>/*.log
.specify/runs/<run-id>/ESCALATION.md
```

## Harness Fit Check For `AINative_OKR_Claude_GHCP`

| Standard item | OKR source status | Fit |
| --- | --- | --- |
| `CLAUDE.md` | Present | Good |
| `.claude/commands/*.md` | Present, OKR/Spec-Kit commands | Good |
| `.claude/agents/*.md` | Present, much richer than generic template | Good |
| `.specify/memory/constitution.md` | Present | Good |
| `.specify/scripts/*` | Present for Bash and PowerShell | Good |
| `.specify/templates/*` | Present | Good |
| App source code | Not present yet | Gap |
| Target `harness.yaml` inside OKR folder | Not present | Gap |
| Project build/typecheck/lint/test commands | Documented in target architecture, not implemented | Gap |
| Harness phase mapping to OKR 13-step flow | Not present | Gap |
| Deterministic artifact gates for OKR outputs | Not present | Gap |
| Dashboard target registration for OKR folder | Not confirmed | Gap |
| Real Docker Compose app stack | Described in docs, not implemented | Gap |

Conclusion: `AINative_OKR_Claude_GHCP/` is close to the harness target-project standard for prompts and agent flow, but it is not yet runnable as a harness target because it lacks a project-level harness config, app code, package files, Docker stack, and concrete verification commands.

## Required Mapping

The generic harness phases should be replaced or extended with an OKR-specific mapping.

| Harness phase | OKR command | Expected gate |
| --- | --- | --- |
| `system-srs` | `/okr.srs.getsrsall` or direct `/okr.srsallsystem` command if added | `docs/output/srs-systems/**` exists |
| `srs` | `/okr.srs` | `docs/output/ipa-docs/srs/**` exists |
| `basic-design` | `/okr.bd` | `docs/output/ipa-docs/bd/**` exists |
| `specify` | `/speckit.specify {feature}` | `specs/*/spec.md` exists |
| `clarify` | `/speckit.clarify` | no `[NEEDS CLARIFICATION]` markers in `spec.md` |
| `review-spec` | `/okr.reviewspec` | no blocking review markers |
| `plan` | `/speckit.plan {tech_stack}` | `specs/*/plan.md` exists |
| `review-plan` | `/okr.reviewplan` | no blocking plan markers |
| `detail-design` | `/okr.dd` | `docs/output/ipa-docs/dd/**` exists |
| `generate-tests` | `/okr.testkit gen-testcases` | `docs/output/ipa-docs/testcase/**` exists |
| `tasks` | `/speckit.tasks` | `specs/*/tasks.md` exists |
| `implement` | `/speckit.implement` | app build/typecheck/lint/test pass |
| `review-code` | `/okr.reviewcode` | no blocking code-review markers |
| `run-tests` | `/okr.testkit run-tests` | test report exists and automated tests pass |
| `launch` | `/okr.bossbuiltin` step 13 or a dedicated command | Docker services build and app is reachable |

There are two viable integration modes:

| Mode | Description | Recommendation |
| --- | --- | --- |
| Boss mode | Harness runs one phase: `/okr.bossbuiltin`, then gates final artifacts | Fastest path to use the imported flow |
| Expanded mode | Harness owns each OKR step as a separate phase | Better observability, retry control, dashboard visibility |

Use Boss mode first to preserve the imported flow, then evolve to Expanded mode when the dashboard needs per-step visibility.

## Seven Harness Components

| ID | Component | Current implementation | OKR integration need |
| --- | --- | --- | --- |
| H1 | Context Harness | Static prompt/context via commands and project files | Build an OKR context packet from `docs/input`, change requests, `technical_architecture.md`, `.specify/memory`, prior outputs |
| H2 | Tool Harness | Provider CLI flags and shell gates | Add tool policy/audit around Docker, npm, Prisma, and browser launch commands |
| H3 | Evaluation Harness | Shell, glob, marker, agent-output gates | Add OKR artifact gates and app gates for NestJS, React, Prisma, Docker, and Playwright |
| H4 | Security Harness | Not separately implemented | Add secret scan, dependency audit, auth/RBAC checks, prompt injection checks for imported docs |
| H5 | Governance Harness | Escalation artifact only | Add approval/risk policy for DB resets, migrations, destructive commands, and release launch |
| H6 | AgentOps Harness | Basic cost aggregation from provider output | Track per-agent cost/latency/retries for OKR steps |
| H7 | Orchestration Harness | Sequential phases, retry, resume, escalation | Add OKR-specific phase config and dashboard target support |

## Immediate Gaps To Fix Before Coding The OKR Website

1. Add an OKR harness config, likely `AINative_OKR_Claude_GHCP/harness.okr.yaml`, that points phases to OKR commands and gates.
2. Decide whether first run uses Boss mode or Expanded mode.
3. Add or normalize command wrappers for any commands referenced by the flow but not directly present as slash commands.
4. Define the application source layout inside `AINative_OKR_Claude_GHCP/`:

```text
AINative_OKR_Claude_GHCP/
  backend/
  frontend/
  docker/
  docker-compose.yml
  docker-compose.test.yml
```

5. Add project verification commands once app scaffolding exists:

```yaml
project:
  build: "docker compose build"
  typecheck: "docker compose run --rm backend npm run typecheck && docker compose run --rm frontend npm run typecheck"
  lint: "docker compose run --rm backend npm run lint && docker compose run --rm frontend npm run lint"
  test: "docker compose run --rm backend npm test && docker compose run --rm frontend npm test"
  security: "docker compose run --rm backend npm audit --audit-level=high && docker compose run --rm frontend npm audit --audit-level=high"
  acceptance: "docker compose -f docker-compose.yml -f docker-compose.test.yml up --abort-on-container-exit"
```

6. Register `AINative_OKR_Claude_GHCP/` as a dashboard target so runs can be launched from the UI.
7. Add deterministic gates for generated IPA documents, Spec-Kit artifacts, Docker health, seeded data, Swagger, and frontend reachability.
8. Preserve imported agent files as source-of-truth until an intentional migration is made.

## Recommended Build Order

1. **OKR harness config**
   Create the minimum Boss-mode config and confirm the harness can invoke `/okr.bossbuiltin` from `AINative_OKR_Claude_GHCP/`.

2. **Dashboard target**
   Point the dashboard target selector at `AINative_OKR_Claude_GHCP/`.

3. **App scaffold**
   Create `backend/`, `frontend/`, Docker files, Prisma schema, seed script, and package scripts inside the OKR folder.

4. **Verification commands**
   Wire build, typecheck, lint, test, security, and acceptance commands into the OKR harness config.

5. **Expanded phase mode**
   Split `okr.bossbuiltin` into harness-visible phases for better run logs and retry behavior.

6. **Security and governance**
   Add DB reset policy, secret checks, dependency audit, auth/RBAC verification, and approval artifacts.

7. **AgentOps**
   Record per-agent metrics and expose them in the dashboard.

## Target End State

```text
Dashboard or CLI
  -> selected target: AINative_OKR_Claude_GHCP
  -> selected provider: Claude Code or Codex
  -> selected mode: boss or expanded
  -> harness creates run state
  -> harness invokes OKR agent flow
  -> OKR app code is generated/changed in backend + frontend
  -> Docker/MySQL/NestJS/React gates run
  -> docs, logs, cost, gates, and app status appear in dashboard
```

At that point, the imported source becomes a real harness target rather than only a Claude/GHCP prompt package.
