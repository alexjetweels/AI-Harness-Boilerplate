# AI SDLC Harness Architecture

This document describes the target architecture for a **7-component AI SDLC Harness**. The goal is to turn "send a prompt to Claude Code" into a controlled execution system with context management, policy, tool guardrails, evaluation, security, observability, state, and provider extensibility.

The harness should work with Claude Code today and later support direct integrations with providers such as OpenAI, Anthropic API, or other model/runtime providers.

## 1. Architecture Goals

The system should:

- Run a feature through the full SDLC from one command or API call.
- Let Claude Code use project prompts, commands, and subagents from `.claude/`, while still being controlled by an external harness.
- Separate orchestration, context, tools, evaluation, security, governance, and observability into explicit components.
- Persist state, logs, transcripts, reports, and artifacts for resume, audit, debugging, and dashboard visibility.
- Provide a provider abstraction so the same harness can route work to Claude Code, OpenAI, Anthropic API, or future providers.

## 2. Mental Model

The harness is a **control plane around the agent**, not just a large prompt.

```text
User / CI / Dashboard
        |
        v
H7 Orchestration Harness
        |
        v
Phase Execution Loop
        |
        +--> H1 Context Harness
        +--> H5 Governance Harness
        +--> H2 Tool Harness
        +--> Provider Adapter
        +--> H4 Security Harness
        +--> H3 Evaluation Harness
        +--> H6 AgentOps Harness
        |
        v
State / Logs / Reports / Dashboard
```

The provider can be Claude Code, OpenAI, Anthropic API, or another implementation. The important architectural rule is that all providers must pass through the same harness components.

## 3. Seven Harness Components

| ID | Component | Responsibility | Current State In This Repo |
| --- | --- | --- | --- |
| H1 | Context Harness | Builds a context packet from repo files, docs, specs, rules, memory, and previous run state | Project prompt pack and `CLAUDE.md` exist; real context builder is not implemented yet |
| H2 | Tool Harness | Controls tool calls, allow/deny policy, timeout, sandboxing, audit log, and idempotency | Basic `allowed_tools` and shell gates exist; full tool audit is not implemented yet |
| H3 | Evaluation Harness | Runs build, typecheck, lint, test, acceptance, golden evals, and optional LLM judge checks | `gates.py` has basic deterministic gates |
| H4 | Security Harness | Runs secret scan, prompt-injection scan, leakage detection, dependency scan, and risky-command detection | Rules and dashboard gaps exist; engine is not implemented yet |
| H5 | Governance Harness | Handles approvals, policy registry, risk register, escalation, and immutable audit | Basic escalation file exists |
| H6 | AgentOps Harness | Tracks cost, tokens, latency, trace, drift, hallucination risk, and per-agent metrics | Claude Code cost is captured; full metrics are not implemented yet |
| H7 | Orchestration Harness | Coordinates phase DAG, retry, repair, resume, provider routing, and escalation | `orchestrator.py` exists |

## 4. SDLC Phase Flow

The generic SDLC pipeline uses commands under the target project's `.claude/commands/sdlc.*.md`. Projects without those prompts can copy them from `templates/claude-sdlc/`.

```text
intake
  -> requirements
  -> architecture
  -> plan
  -> tasks
  -> implement
  -> review
  -> test
  -> security
  -> docs
  -> release
```

Each phase produces a stable artifact under `docs/sdlc/current/`:

| Phase | Command | Artifact |
| --- | --- | --- |
| intake | `/sdlc.intake` | `01-intake.md` |
| requirements | `/sdlc.requirements` | `02-requirements.md` |
| architecture | `/sdlc.architecture` | `03-architecture.md` |
| plan | `/sdlc.plan` | `04-plan.md` |
| tasks | `/sdlc.tasks` | `05-tasks.md` |
| implement | `/sdlc.implement` | `06-implementation.md` |
| review | `/sdlc.review` | `07-review.md` |
| test | `/sdlc.test` | `08-test-report.md` |
| security | `/sdlc.security` | `09-security.md` |
| docs | `/sdlc.docs` | `10-docs.md` |
| release | `/sdlc.release` | `11-release.md` |

The generic harness configuration is:

```text
packages/ai-harness/harness.sdlc.yaml
```

## 5. Runtime Flow For One Command

Example command:

```bash
harness run --feature "Add login with password reset" \
  --tech-stack "React + FastAPI" \
  --config packages/ai-harness/harness.sdlc.yaml
```

Runtime flow:

```text
1. H7 creates a run_id.
2. H7 loads the harness config.
3. H7 selects the first phase: intake.
4. H1 builds the context packet for intake.
5. H5 checks policy and risk.
6. H2 prepares the tool policy for the provider.
7. The provider runs `/sdlc.intake`.
8. H4 scans output/artifacts for security risk.
9. H3 runs the gates for the intake phase.
10. H6 records metrics: cost, latency, tokens, failures.
11. H7 decides:
    - pass: advance to the next phase
    - repairable failure: resume the same session and retry
    - exhausted retries: escalate
    - high risk: pause for approval
12. Repeat until release or escalation.
```

## 6. Why Every Phase Uses The Same Loop

Every phase uses the same harness loop because the **control requirements are the same**, even when the work being done is different.

For example:

- `requirements` mainly produces a document.
- `implement` changes code.
- `security` reviews risk.
- `release` decides whether the result can ship.

Those phases do different work, but each phase still needs:

- The right context.
- A policy and risk check.
- Controlled tools.
- Provider execution.
- Security checks.
- Evaluation gates.
- Metrics.
- A decision: continue, retry, pause, or escalate.

Using one shared loop gives the harness these properties:

| Reason | Why It Matters |
| --- | --- |
| Consistency | Every phase is auditable and controlled in the same way |
| Safety | Risk checks and tool policy are not skipped just because a phase "looks harmless" |
| Provider independence | Claude Code, OpenAI, and Anthropic API can all plug into the same execution contract |
| Retry and repair | Failures are handled uniformly across phases |
| Observability | Cost, latency, traces, and failures are comparable across phases |
| Governance | Approval and escalation rules apply everywhere |
| Extensibility | New phases can be added without inventing a new execution model |

The loop does not mean every phase runs the exact same checks. It means every phase passes through the same **control points**.

For example:

```text
requirements phase
  -> context includes intake and existing docs
  -> tools may be read/write only
  -> gates check requirements artifact and unresolved markers

implement phase
  -> context includes requirements, architecture, plan, and tasks
  -> tools may include shell/build/test
  -> gates run build, typecheck, lint, and tests

security phase
  -> context includes code changes and dependency files
  -> tools may include scanners
  -> gates check security report and security commands
```

Same loop. Different phase-specific context, tools, gates, risk policy, and output artifacts.

This is the core reason it becomes a harness instead of a prompt chain.

## 7. Per-Phase Execution Loop

Each phase runs through this loop:

```text
Phase N
  |
  v
H1 Context Harness
  - repo map
  - relevant files
  - CLAUDE.md
  - .claude/rules
  - previous artifacts
  - previous run state
  |
  v
H5 Governance Harness
  - classify risk
  - check policy
  - require approval if needed
  |
  v
H2 Tool Harness
  - allowed tools
  - denied tools
  - shell timeout
  - audit log
  - sandbox policy
  |
  v
Provider Adapter
  - Claude Code CLI today
  - OpenAI / Anthropic API later
  |
  v
Agent Output + File Changes + Tool Trace
  |
  v
H4 Security Harness
  - secret scan
  - prompt injection scan
  - leakage detection
  - dependency/risky command scan
  |
  v
H3 Evaluation Harness
  - artifact gates
  - build/typecheck/lint/test
  - acceptance
  - optional judge
  |
  v
H6 AgentOps Harness
  - cost
  - tokens
  - latency
  - retry count
  - risk score
  |
  v
H7 Decision
```

## 8. H7 Decision Model

The orchestrator does more than run phases sequentially. It decides what should happen next.

```text
Gate passed
  -> advance to next phase

Gate failed and attempts remain
  -> send gate report back to the same provider session
  -> retry phase

Gate failed and attempts are exhausted
  -> write ESCALATION.md
  -> mark run escalated

High-risk action detected
  -> pause
  -> require governance approval

Budget or timeout exceeded
  -> stop, downgrade model, or escalate depending on policy

Security issue detected
  -> block release
  -> require fix or explicit approval
```

## 9. Module Architecture

Target module layout:

```text
packages/ai-harness/src/spec_harness/
  cli.py                  # CLI entrypoint
  config.py               # harness YAML loader
  state.py                # state persistence

  orchestrator.py         # H7: phase state machine, retry, resume, escalation
  context.py              # H1: context packet builder
  tool_harness.py         # H2: tool registry, policy, audit, sandbox wrapper
  gates.py                # H3: deterministic evaluation gates
  security.py             # H4: security scans and risk checks
  governance.py           # H5: approval, policy, risk register
  agentops.py             # H6: usage, cost, latency, drift/risk metrics

  providers/
    base.py               # provider interface and normalized result types
    claude_code.py        # calls `claude -p`
    anthropic_api.py      # future direct Anthropic API adapter
    openai_api.py         # future OpenAI API adapter
```

Current repo already has:

```text
packages/ai-harness/src/spec_harness/
  cli.py
  config.py
  state.py
  orchestrator.py
  agent.py
  gates.py
```

`agent.py` currently dispatches to the Claude Code provider or Codex provider. In the target architecture, it should be split into `providers/claude_code.py`, `providers/codex_cli.py`, and future API adapters.

## 10. Provider Abstraction

The harness core should not care whether the agent is Claude Code, OpenAI, or Anthropic API.

Conceptual interface:

```text
Provider.run(
  phase,
  prompt,
  context_packet,
  allowed_tools,
  session_id,
  budget,
  metadata
) -> AgentResult
```

Normalized result:

```text
AgentResult
  ok: bool
  text: str
  session_id: str | null
  tool_calls: list
  files_changed: list
  cost_usd: float
  usage: object
  raw: object
```

Claude Code adapter today:

```text
claude -p "<prompt>"
  --output-format json
  --model <model>
  --max-turns <n>
  --allowedTools <tools>
  --resume <session_id>
```

Codex CLI adapter today:

```text
codex exec
  --json
  --output-last-message <temp-file>
  --cd <repo>
  --model <model, optional>
```

Codex does not natively execute `.claude/commands/*.md` slash commands the same way Claude Code does. The current harness handles this by inlining the matching `.claude/commands/<command>.md` file into a normal prompt before calling `codex exec`.

OpenAI or Anthropic API later:

```text
Provider Adapter
  -> call model API
  -> receive requested tool calls
  -> execute approved tools through H2 Tool Harness
  -> send tool results back to model
  -> return normalized AgentResult
```

Important rule: **tool execution must stay under H2 Tool Harness**, not inside each provider independently. Otherwise audit, security, policy, and governance become inconsistent.

## 11. Data And Artifact Layout

Target runtime output:

```text
.specify/
  state/
    <run-id>.json

  runs/
    <run-id>/
      context/
        intake.context.md
        requirements.context.md
        implement.context.md

      transcripts/
        intake.attempt1.json
        implement.attempt1.json
        implement.attempt2.json

      tools/
        tool-audit.jsonl

      gates/
        intake.gates.json
        implement.gates.json

      security/
        security-report.json

      governance/
        approvals.json
        risk-register.md

      agentops/
        metrics.json

      ESCALATION.md
```

Human-readable SDLC artifacts:

```text
docs/sdlc/current/
  01-intake.md
  02-requirements.md
  03-architecture.md
  04-plan.md
  05-tasks.md
  06-implementation.md
  07-review.md
  08-test-report.md
  09-security.md
  10-docs.md
  11-release.md
```

## 12. Dashboard Architecture

Current dashboard:

```text
React UI
  -> FastAPI /api/dashboard
  -> FastAPI /api/runs
  -> in-memory simulated run data
```

Target dashboard:

```text
React UI
  -> FastAPI run API
  -> run worker / subprocess manager
  -> packages/ai-harness CLI or in-process orchestrator
  -> .specify/state/<run-id>.json
  -> .specify/runs/<run-id>/*
  -> streamed phase status, logs, gates, cost, risk
```

API responsibilities:

- Create run.
- Resume run.
- Stop run.
- Read run state.
- Stream logs.
- Surface gates and failures.
- Surface approval requests.
- Surface cost and risk metrics.

Current dashboard runner endpoints:

```text
POST /api/harness-runs
  -> starts a background harness subprocess

GET /api/harness-runs/latest
  -> reads latest run state, artifacts, and log tail

GET /api/harness-runs/{run_id}
  -> reads one run

POST /api/harness-runs/{run_id}/stop
  -> terminates a running subprocess
```

The first implemented target is `examples/todo-app`. From the UI, a user can enter a task, select `Codex` or `Claude Code`, and start a real harness run without knowing the terminal command.

## 13. Config Model

Generic SDLC config:

```text
packages/ai-harness/harness.sdlc.yaml
```

Spec-kit config:

```text
packages/ai-harness/harness.yaml
```

The generic config intentionally fails project commands by default:

```yaml
project:
  build: "echo 'TODO: set project.build' && exit 1"
  typecheck: "echo 'TODO: set project.typecheck' && exit 1"
  lint: "echo 'TODO: set project.lint' && exit 1"
  test: "echo 'TODO: set project.test' && exit 1"
  security: "echo 'TODO: set project.security' && exit 1"
  acceptance: "echo 'TODO: set project.acceptance' && exit 1"
```

For a real project, replace them:

```yaml
project:
  build: "npm run build"
  typecheck: "npx tsc --noEmit"
  lint: "npm run lint"
  test: "npm test"
  security: "npm audit --audit-level=high"
  acceptance: "npm run test:e2e"
```

## 14. Security And Governance Model

The Security Harness handles technical checks:

- Secret exposure.
- Credential leakage.
- Prompt injection from external content.
- Unsafe subprocess usage.
- Dependency vulnerabilities.
- Data exfiltration risk.

The Governance Harness handles decision control:

- Whether a run may continue.
- Whether human approval is required.
- Whether a security finding blocks release.
- Whether a risky command is allowed.
- Whether an escalation should create an issue or approval request.

Example governance policy:

```text
Low risk
  -> auto-continue

Medium risk
  -> continue but record risk

High risk
  -> require approval before implementation or release

Critical risk
  -> block until fixed
```

## 15. Current Implementation vs Target

| Area | Current | Target |
| --- | --- | --- |
| Prompt pack | `templates/claude-sdlc/.claude` plus target-project `.claude` | Project-specific extensions and versioned prompt/eval baselines |
| Context | Static Claude memory and prompt artifacts | Generated per-phase context packet |
| Tooling | Claude `allowed_tools`, shell gates | Tool registry, audit log, sandbox wrapper, idempotency |
| Evaluation | Basic deterministic gates | Build/test/acceptance/golden eval/optional judge |
| Security | Rules and dashboard gap | Secret scan, injection scan, dependency scan, leakage checks |
| Governance | Escalation file | Approval workflow, risk register, policy engine |
| AgentOps | Cost from Claude output | Token/cost/latency/drift/failure metrics per agent |
| Orchestration | Sequential phases, retry, resume | DAG, parallel lanes, provider routing, worker queue |
| Dashboard | Simulated runs | Real run state and streaming logs |
| Providers | Claude Code wrapper | Provider abstraction for Claude Code, Anthropic API, OpenAI API |

## 16. Recommended Build Order

Implement the missing harness layers in this order:

1. **H1 Context Harness**
   Build per-phase `context_packet.md/json` from repo map, docs, rules, artifacts, and previous state.

2. **Provider Abstraction**
   Move the current Claude Code wrapper behind a provider interface.

3. **H2 Tool Harness**
   Add tool registry, allow/deny policy, command timeout, audit log, and risk tags.

4. **H3 Evaluation Expansion**
   Add structured gate output, real acceptance checks, and a golden eval baseline.

5. **H4 Security Harness**
   Add secret scan, prompt-injection scan, dependency scan, and leakage report.

6. **H5 Governance Harness**
   Add policy file, approval artifacts, and risk register.

7. **H6 AgentOps Harness**
   Add metrics JSON, token/cost/latency/failure tracking, and dashboard fields.

8. **Dashboard Integration**
   Replace simulated runs with real orchestrator runs and log streaming.

## 17. Final Target Flow

The intended end-state:

```text
harness run --feature "..."
  |
  v
H7 Orchestrator
  |
  v
for each SDLC phase:
  H1 build context
  H5 check governance
  H2 prepare tools
  Provider runs agent
  H4 scan security
  H3 evaluate gates
  H6 record metrics
  H7 decide next action
  |
  +--> pass: next phase
  +--> fail: repair retry
  +--> risk: approval
  +--> exhausted: escalation
  |
  v
release decision + audit trail + dashboard visibility
```

This architecture lets the same harness run with Claude Code today and evolve toward OpenAI, Anthropic API, or other providers later without rewriting the SDLC control plane.
