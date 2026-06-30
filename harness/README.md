# AI SDLC Harness Wrapper Blueprint

This folder is the reusable outer-harness blueprint. Target projects keep their
own prompts, agents, source code, and product documents. The harness adds a
control plane around them.

## Pattern

**Outer Control Plane / Inner Agent System**

```text
User or dashboard
  -> packages/ai-harness CLI and API
  -> harness target adapter
  -> H1-H7 policies and gates
  -> target project prompt/agent system
  -> generated code, docs, logs, metrics
```

## Reusable Folder Structure

```text
harness/
  README.md
  layers/
    H1-context/policy.md
    H2-tool/policy.md
    H3-evaluation/policy.md
    H4-security/policy.md
    H5-governance/policy.md
    H6-agentops/policy.md
    H7-orchestration/policy.md
  targets/
    okr-ghcp/target.yaml
```

Package-owned adapters live inside `packages/ai-harness/targets/` so target
repositories can stay unchanged. The CLI can run with:

```powershell
python -m cli run `
  --repo .\AINative_OKR_Claude_GHCP `
  --config .\packages\ai-harness\targets\okr-ghcp\harness.okr.yaml `
  --feature "Build the OKR web application"
```

## Adapter Pattern

Each target adapter should provide:

- `target` metadata: id, name, inner system, default mode
- `context` sources for H1 context packet creation
- `agent` provider defaults
- `project` commands for build, lint, test, security, acceptance
- `phases` mapping target commands to deterministic gates

## Current Target

`AINative_OKR_Claude_GHCP/` is an inner AI-SDLC prompt system. It remains
source-only; OKR wrapper assets now live in `packages/ai-harness/targets/okr-ghcp/`:

- `harness.okr.yaml` for expanded phase-by-phase orchestration
- `harness.okr.boss.yaml` for one-shot boss orchestration
- fallback command wrappers for `okr.bd`, `okr.dd`, `okr.reviewplan`, and `okr.testkit`
