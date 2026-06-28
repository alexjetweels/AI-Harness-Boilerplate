---
description: Run the project's build, typecheck, lint and tests, then report failures with file:line and fix them. Use before declaring an implementation done.
allowed-tools: Bash, Read, Edit
---

## Build
!`npm run build 2>&1 | tail -40 || true`

## Typecheck
!`npx tsc --noEmit 2>&1 | tail -40 || true`

## Lint
!`npm run lint 2>&1 | tail -40 || true`

## Tests
!`npm test 2>&1 | tail -60 || true`

## Instructions
Review the command output above (edit the commands to match this project's stack).
- If everything passed, reply exactly: `VERIFY: PASS`.
- Otherwise list each failure as `file:line — problem`, fix the code, and re-run the
  failing command. Do not stop until all checks pass or you have made 3 fix attempts.
