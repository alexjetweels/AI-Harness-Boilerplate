---
description: Perform a security and risk pass for the current change.
allowed-tools: Read, Write, Edit, Bash
argument-hint: "<optional security focus>"
---

Review the current change for security risk.

Create or update `docs/sdlc/current/09-security.md` with:

- Secret exposure risk.
- Dependency or supply-chain risk.
- Input validation and injection risk.
- Auth, authorization, and data access impact.
- Subprocess, filesystem, network, or deployment risk.
- Required approvals before release.

Use available local tools only. Do not expose secrets in the report.

