---
description: Review the current change for defects, regressions, and missing verification.
allowed-tools: Read, Write, Edit, Bash
argument-hint: "<optional review focus>"
---

Review the current working tree against the SDLC artifacts.

Create or update `docs/sdlc/current/07-review.md` with:

- Findings ordered by severity.
- File and line references when possible.
- Missing tests or weak verification.
- Requirement traceability gaps.
- Recommendation: approve, approve with follow-up, or block.

Use `git diff` and local files. Do not rewrite the implementation unless explicitly asked.

