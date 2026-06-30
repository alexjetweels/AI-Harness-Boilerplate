# H5 Governance Harness Policy

Purpose: make risk and escalation explicit.

Baseline:

- Each phase has `max_attempts`.
- Failed final attempts create an `escalation` artifact in Postgres.
- State is persisted in Postgres table `harness_run_state`.

Approval boundaries:

- destructive database commands
- production secret changes
- schema reset with data loss
- release or external deployment

Future hardening:

- require approval artifacts for high-risk phases
- maintain a target risk register
- attach escalation to GitHub issues when enabled
