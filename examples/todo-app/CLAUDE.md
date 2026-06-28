# Todo App Demo Target

This project is a dependency-free Node.js CLI todo app used to test the AI SDLC Harness.

## Project Shape

- `src/store.js`: task persistence and domain operations.
- `src/cli.js`: command-line interface.
- `test/todo.test.js`: unit tests.
- `scripts/acceptance.js`: end-to-end CLI acceptance test.
- `scripts/lint.js`: lightweight repository lint.
- `scripts/security-check.js`: lightweight security scan.
- `.claude/commands/`: local SDLC slash commands used by the harness.

## Working Rules

- Keep the app dependency-free unless a task explicitly requires a dependency.
- Preserve JSON-file persistence.
- Add or update tests for behavior changes.
- Run `npm run build`, `npm run lint`, `npm test`, `npm run acceptance`, and `npm run security` before marking implementation complete.
- Put SDLC artifacts under `docs/sdlc/current/`.

