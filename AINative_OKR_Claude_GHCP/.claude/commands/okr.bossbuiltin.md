---
description: Run the full AI-SDLC pipeline end-to-end (fully autonomous, no pauses)
allowed-tools: Agent, Read, Write, Edit, Bash, Glob, Grep, TodoWrite, WebFetch, WebSearch
---

⚠️ **MANDATORY**: You MUST spawn the `okr.bossbuiltin` sub-agent via the **Agent tool**.
**DO NOT implement anything yourself. DO NOT skip to coding. DO NOT generate docs directly.**
Your ONLY job in this turn: prepare structured arguments → call Agent tool → wait for completion.

---

## Step 1 — Derive feature-id

Read `docs/output/output_logs/` to list existing feature folders:

```
Get-ChildItem docs/output/output_logs/ -Directory | Select-Object Name
```

- If directory is empty or does not exist → use `okr-feat-001`
- If folders exist → increment the highest number (e.g., `okr-feat-003` → `okr-feat-004`)

Do NOT reuse an existing feature-id unless the user explicitly says "resume" or "continue".

---

## Step 2 — Spawn the Boss Agent via Agent tool

Call the **Agent tool** with:
- `subagent_type`: `"okr.bossbuiltin"`
- `prompt`: the structured YAML block below followed by the feature description

```yaml
feature-id: <derived-feature-id>
module-id: mod01
module-keyword: OKR
pipeline-context: docs/output/output_logs/<feature-id>/pipeline-context.yaml
mode: autonomous
language: Vietnamese
```

Feature description:
$ARGUMENTS

---

## Step 3 — Do nothing else

Wait for the Agent tool to return. The boss agent runs the full 13-step pipeline:
SRS → BD → Spec → Clarify → Review → Plan → Review → DD → Test Cases → Tasks → Implement → Code Review → QA → Launch

Do not intervene, generate code, or produce documents yourself.
If Agent tool is unavailable, inform the user: "The okr.bossbuiltin agent is required. Please ensure it is registered in .claude/agents/okr.bossbuiltin.md."
