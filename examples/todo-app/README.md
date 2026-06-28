# Todo App Demo Target

This is a small dependency-free Node.js CLI app used as a target repository for the AI SDLC Harness.

## Commands

```bash
npm run build
npm run typecheck
npm run lint
npm test
npm run acceptance
npm run security
```

## CLI Usage

```bash
node src/cli.js add "Write architecture doc"
node src/cli.js list
node src/cli.js done 1
node src/cli.js delete 1
```

By default tasks are stored in `.todo.json`. For tests or isolated runs, set:

```bash
TODO_FILE=/tmp/todo.json node src/cli.js add "Task title"
```

## Harness Usage

From the repository root:

```bash
PYTHONPATH=packages/ai-harness/src python3 -m spec_harness run \
  --feature "Add priority support to todo tasks" \
  --repo examples/todo-app \
  --config harness.yaml
```

Use Codex instead of Claude Code:

```bash
PYTHONPATH=packages/ai-harness/src python3 -m spec_harness run \
  --feature "Add due date support to todo tasks" \
  --repo examples/todo-app \
  --config harness.codex.yaml
```

The harness will run inside this demo target project and write SDLC artifacts under `docs/sdlc/current/`.
