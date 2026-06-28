# Claude SDLC Prompt Pack

This template contains reusable Claude Code project prompts for SDLC-oriented agent work.

## Contents

```text
.claude/
  commands/sdlc.*.md
  agents/*.md
  rules/*.md
  settings.example.json
CLAUDE.md
```

## Install Into A Target Project

```bash
cp -R templates/claude-sdlc/.claude /path/to/target-project/.claude
cp templates/claude-sdlc/CLAUDE.md /path/to/target-project/CLAUDE.md
```

Then configure that target project's `harness.yaml` to call the commands you want, such as:

```yaml
phases:
  - name: intake
    command: "/sdlc.intake {feature}"
```

