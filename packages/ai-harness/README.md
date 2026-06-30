# AI Harness Engine

This package contains the Python harness engine and CLI. The installed command entrypoint is `harness`; source modules live directly under `src/` by harness layer.

## Contents

| Path | Role |
| --- | --- |
| `docs/ARCHITECTURE_DESIGN.md` | Detailed source architecture and runtime design |
| `src/interfaces/cli.py` | CLI entrypoint |
| `src/core/config.py` | Config contracts and YAML loading |
| `src/context/builder.py` | Context packet and manifest builder |
| `src/tool/agent_runner.py` | Provider dispatcher for Claude Code and Codex CLI |
| `src/evaluation/gates.py` | Deterministic gates |
| `src/security/secret_scanner.py` | Secret scan primitive |
| `src/governance/escalation.py` | Escalation policy |
| `src/agentops/storage.py` | Postgres persistence for state and artifacts |
| `src/agentops/state_store.py` | DB-backed run state facade |
| `src/agentops/db_logger.py` | Structured phase/gate logging |
| `src/orchestration/orchestrator.py` | Phase state machine, retry, resume |
| `harness.sdlc.yaml` | Generic SDLC pipeline template |
| `harness.yaml` | Spec-kit-oriented pipeline |
| `evals/` | Golden-case eval harness |

## Install For Local Development

```bash
pip install -e ./packages/ai-harness
```

## Persistence

Harness run state, context packets, manifests, logs, gate reports, and escalation artifacts are stored in Postgres. Set `DATABASE_URL` or `HARNESS_DB_URL` before running the CLI.

Or run without installing:

```bash
PYTHONPATH=packages/ai-harness/src python3 -m cli --help
```

## Run Against A Target Project

```bash
PYTHONPATH=packages/ai-harness/src python3 -m cli run \
  --feature "Add secure multi-agent review workflow" \
  --repo examples/todo-app \
  --config harness.codex.yaml
```

`--config` is resolved relative to the target repo.

## Providers

Claude Code:

```yaml
agent:
  provider: claude
  bin: claude
  model: sonnet
```

Codex CLI:

```yaml
agent:
  provider: codex
  bin: codex
  model: ""   # use Codex CLI configured default
```

Codex does not expand Claude Code slash commands directly. The harness inlines `.claude/commands/<command>.md` into a normal prompt before calling `codex exec`.

## Safety

`skip_permissions: true` is intended for sandboxed local demos or CI workers. For production use, route tool execution through a stronger H2 Tool Harness and require approvals for destructive or high-risk actions.

