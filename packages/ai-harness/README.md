# AI Harness Engine

This package contains the Python harness engine and CLI. The command entrypoint is still `harness`, and the Python module is still `spec_harness` for compatibility with the existing implementation.

## Contents

| Path | Role |
| --- | --- |
| `src/spec_harness/cli.py` | CLI entrypoint |
| `src/spec_harness/orchestrator.py` | H7 phase state machine, retry, resume, escalation |
| `src/spec_harness/agent.py` | Provider dispatcher for Claude Code and Codex CLI |
| `src/spec_harness/gates.py` | H3 deterministic gates |
| `src/spec_harness/state.py` | Run state persistence |
| `harness.sdlc.yaml` | Generic SDLC pipeline template |
| `harness.yaml` | Spec-kit-oriented pipeline |
| `evals/` | Golden-case eval harness |

## Install For Local Development

```bash
pip install -e ./packages/ai-harness
```

Or run without installing:

```bash
PYTHONPATH=packages/ai-harness/src python3 -m spec_harness --help
```

## Run Against A Target Project

```bash
PYTHONPATH=packages/ai-harness/src python3 -m spec_harness run \
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

