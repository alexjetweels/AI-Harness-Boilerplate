# H2 Tool Harness Policy

Purpose: constrain and audit tool/runtime access.

Baseline:

- Provider tools are declared in `agent.allowed_tools`.
- Shell execution is only allowed through configured gate commands and provider tool policy.
- High-risk commands belong in project commands so they are visible and reviewable.

OKR high-risk commands:

- `docker compose down -v`
- database reset or migration commands
- dependency installation
- browser launch / public port exposure

Future hardening:

- Add command allow/deny enforcement before shell gates.
- Emit a tool-audit event for every provider and gate command.
