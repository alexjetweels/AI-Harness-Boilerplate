# spec-harness

A closed-loop SDLC **harness** wrapped around your existing [spec-kit](https://github.com/github/spec-kit) project, driving **Claude Code** in headless mode.

It turns the manual `/speckit.*` slash-command flow into one automated loop:

```
generate (claude -p)  ->  verify (gates)  ->  feedback  ->  gate  ->  advance | retry | escalate
```

## What's inside

| Path | Role |
|------|------|
| `src/spec_harness/orchestrator.py` | Control loop / state machine over the spec-kit phases |
| `src/spec_harness/agent.py` | `claude -p --output-format json` wrapper (parses cost + session_id) |
| `src/spec_harness/gates.py` | Deterministic gates: `shell`, `glob_nonempty`, `no_markers`, `agent_output` |
| `src/spec_harness/state.py` | Resumable, auditable run manifest (`.specify/state/<run>.json`) |
| `harness.yaml` | The pipeline: each phase = a slash command + its gates. **Edit `project:` commands.** |
| `harness.sdlc.yaml` | Generic SDLC pipeline using root `.claude/commands/sdlc.*.md`; no spec-kit dependency. |
| `.claude/commands/speckit.verify.md` | Bonus self-check command the agent can run during repair |
| `.github/workflows/spec-harness.yml` | Run the whole thing unattended on a dispatch or issue label |
| `evals/` | Golden-case eval harness — gates prompt/template changes against regression |

## Install

From the **root of your spec-kit project** (drop this folder in as `spec-harness/`):

```bash
npm install -g @anthropic-ai/claude-code        # the agent
pip install -e ./spec-harness                   # the `harness` CLI
# project must already be spec-kit-initialized:
#   specify init --here --integration claude
```

## Configure (the only required step)

Open `harness.yaml` and set the `project:` commands to your stack:

```yaml
project:
  build:      "npm run build"
  typecheck:  "npx tsc --noEmit"
  lint:       "npm run lint"
  test:       "npm test"
  acceptance: "npm run test:e2e"
```

These feed the `shell` gates after `/speckit.implement` and the final `verify` phase.
Also edit the commands inside `.claude/commands/speckit.verify.md` to match.

## Use

```bash
# Full pipeline for one feature
harness run --feature "Photo album organizer with drag-and-drop" \
            --tech-stack "Vite + vanilla JS + local SQLite" \
            --config spec-harness/harness.yaml

# Inspect / resume
harness status <run-id> --config spec-harness/harness.yaml
harness resume <run-id> --config spec-harness/harness.yaml
```

For a non-spec-kit project that uses the root `.claude/` SDLC prompt pack:

```bash
harness run --feature "Add secure multi-agent review workflow" \
            --tech-stack "React + FastAPI" \
            --config spec-harness/harness.sdlc.yaml
```

Before relying on this in CI, replace every `TODO` command under `project:` in
`harness.sdlc.yaml` with real build, typecheck, lint, test, security, and acceptance commands.

To use Codex instead of Claude Code, set:

```yaml
agent:
  provider: codex
  bin: codex
  model: ""   # use Codex CLI configured default
```

Codex does not expand Claude Code slash commands directly, so the harness inlines
`.claude/commands/<command>.md` into a normal prompt before calling `codex exec`.

The run advances `constitution -> specify -> clarify -> plan -> tasks -> analyze -> implement -> verify`.
At each phase it runs the slash command headless, then the gates. On a gate failure it
**resumes the same Claude session** with the failure report and retries up to `max_attempts`.
Exhausting attempts writes `.specify/runs/<run>/ESCALATION.md` (and opens a GitHub issue if
`HARNESS_OPEN_ISSUE=1`). Per-phase transcripts and gate logs land under `.specify/runs/<run>/`.

## Automate (CI)

`.github/workflows/spec-harness.yml` runs the harness on `workflow_dispatch` or when an
issue is labeled `harness:build`, then pushes the branch and opens a PR. Set the repo
secret `ANTHROPIC_API_KEY`.

## Eval (what makes it a real harness)

```bash
EVAL_TEMPLATE=/path/to/initialized-repo python spec-harness/evals/run_evals.py
```

Runs every case in `evals/cases/`, scores `acceptance.yaml`, and **fails on regression**
versus `baseline.json`. Run it in CI before merging any change to your prompts, templates,
or presets.

## Safety

`skip_permissions: true` lets the agent run tools without prompting — necessary for
unattended runs, dangerous outside a sandbox. **Always run in a container / CI runner**
(spec-kit ships a `.devcontainer/` you can reuse), with `allowed_tools` scoped and
`max_budget_usd` / `max_turns` set as circuit breakers.

## Extending

- New gate type → add a branch in `gates.py`.
- New phase → add an entry in `harness.yaml` (and a slash command if it generates).
- Org-wide template/format changes → use spec-kit **presets**; new commands → **extensions**.
  Keep gate-relevant structure stable so the deterministic gates keep working.

## Note on slash commands in headless mode

The orchestrator invokes commands as `claude -p "/speckit.specify ..."`. If your Claude
Code version doesn't expand project slash commands in `-p` mode, install spec-kit in
skills mode (`specify init --integration claude --integration-options="--skills"`) and
invoke as a skill, or inline the command file's body — adjust `phase.command` in
`harness.yaml` accordingly.
