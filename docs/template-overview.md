# AI Harness Template Overview

This is the consolidated design note for the repository after restructuring it into a reusable AI harness template.

## Purpose

This repository is meant to be a reusable **AI SDLC harness template**. It should help users run AI coding agents against any target project through a controlled flow instead of manually operating terminal commands, provider CLIs, prompts, and gates.

The target use case is:

```text
User opens dashboard
  -> enters a task
  -> selects target project
  -> selects provider: Codex or Claude Code
  -> clicks Start
  -> harness executes SDLC phases
  -> target project code is changed
  -> gates run
  -> artifacts/logs/status appear in UI
```

## Repository Structure

```text
apps/
  dashboard/
    backend/              FastAPI API for UI and harness process execution
    frontend/             React UI for non-terminal users

packages/
  ai-harness/             Python harness engine and CLI

templates/
  claude-sdlc/            Reusable prompt pack for target projects

examples/
  todo-app/               Demo target project

docs/
  architecture.md         Detailed H1-H7 architecture
  template-overview.md    This consolidated overview
```

## Core Concept

The harness is not just a prompt pack. It is a control plane around AI agents.

```text
Dashboard / CLI / CI
  -> AI Harness Engine
  -> target project prompts and context
  -> provider adapter
       -> Codex CLI
       -> Claude Code
       -> future OpenAI / Anthropic API
  -> gates
  -> logs, state, artifacts
  -> dashboard status
```

## Seven Harness Components

| ID | Component | Role |
| --- | --- | --- |
| H1 | Context Harness | Build the right context for each phase |
| H2 | Tool Harness | Control tool calls, commands, policies, timeouts, and audit logs |
| H3 | Evaluation Harness | Run build, typecheck, lint, tests, acceptance, and evals |
| H4 | Security Harness | Detect secrets, injection, leakage, dependency risk, and risky commands |
| H5 | Governance Harness | Handle approvals, risk policy, escalation, and audit |
| H6 | AgentOps Harness | Track cost, tokens, latency, failures, drift, and traces |
| H7 | Orchestration Harness | Coordinate phases, retries, repair loop, resume, and provider routing |

Current implementation is strongest in H7 and H3. H1, H2, H4, H5, and H6 still need deeper implementation to guarantee robust use across arbitrary projects.

## Target Project Contract

To run well against any project, the target repo should provide or be adapted into this contract:

```text
target-project/
  CLAUDE.md or equivalent project guidance
  .claude/commands/* or another prompt mapping
  harness.yaml
  build/typecheck/lint/test/security/acceptance commands
  docs/sdlc/current/ for generated artifacts
```

If a target project already has strong prompts, the harness should discover and use them. If it does not, copy the fallback prompt pack from:

```text
templates/claude-sdlc/
```

Example:

```bash
cp -R templates/claude-sdlc/.claude /path/to/target-project/.claude
cp templates/claude-sdlc/CLAUDE.md /path/to/target-project/CLAUDE.md
```

## Dashboard Flow

The intended user flow is dashboard-first:

```text
1. User enters task.
2. User selects provider.
3. User clicks Start task.
4. Backend starts harness subprocess.
5. Harness runs inside target project.
6. UI polls status, logs, phases, cost, and artifacts.
7. User reviews output and generated project changes.
```

Implemented backend endpoints:

```text
POST /api/harness-runs
GET  /api/harness-runs/latest
GET  /api/harness-runs/{run_id}
POST /api/harness-runs/{run_id}/stop
GET  /api/harness-targets
```

## Demo Target

The first demo target is:

```text
examples/todo-app/
```

It includes:

- Node.js dependency-free Todo CLI.
- Unit tests.
- Acceptance script.
- Security check script.
- Claude-compatible `.claude/commands/sdlc.*.md`.
- `harness.yaml` for Claude Code.
- `harness.codex.yaml` for Codex.

Run directly:

```bash
cd examples/todo-app
npm run build
npm run typecheck
npm run lint
npm test
npm run acceptance
npm run security
```

Run through harness:

```bash
PYTHONPATH=packages/ai-harness/src python3 -m spec_harness run \
  --feature "Add priority support to todo tasks" \
  --repo examples/todo-app \
  --config harness.codex.yaml
```

## Provider Support

Current provider support:

| Provider | Status | Notes |
| --- | --- | --- |
| Claude Code | Supported | Uses `claude -p --output-format json` |
| Codex CLI | Supported | Uses `codex exec --json` |
| OpenAI API | Not implemented | Planned provider adapter |
| Anthropic API | Not implemented | Planned provider adapter |

Codex does not expand Claude Code slash commands directly. The harness currently reads `.claude/commands/<command>.md` and inlines it into a normal prompt before calling `codex exec`.

## What Is Guaranteed Today

The current repo can:

- Start harness runs from UI.
- Run against `examples/todo-app`.
- Use Claude Code or Codex provider configs.
- Persist state under `.specify/state`.
- Persist run logs under `.specify/runs` and `.run/harness-runs`.
- Run deterministic gates from `harness.yaml`.
- Show phases, logs, artifacts, provider, status, and cost in the dashboard.

## What Is Not Yet Guaranteed

The current repo does not yet guarantee robust operation for any arbitrary project without adaptation.

Missing pieces:

- Automatic prompt discovery for arbitrary projects.
- Automatic stack and command detection.
- Generated `harness.project.yaml`.
- Full context packet builder.
- Strong tool-call audit and policy enforcement.
- Approval workflow and governance UI.
- Built-in secret/dependency/prompt-injection scanners.
- Preview hosting for generated frontend apps.
- OpenAI and Anthropic API provider adapters.

## Recommended Next Milestone

Add onboarding for arbitrary target projects:

```bash
harness init --repo /path/to/target-project
```

Expected behavior:

```text
scan target repo
  -> detect stack
  -> discover prompts
  -> detect build/test commands
  -> detect existing CI
  -> generate harness.project.yaml
  -> show readiness report in UI
```

Dashboard should then show:

```text
Project readiness
  - prompts found / missing
  - build command found / missing
  - tests found / missing
  - security command found / missing
  - provider compatibility
  - ready to run: yes/no
```

This is the step that turns the current demo-capable template into a stronger harness for arbitrary real-world projects.

