# H4 Security Harness Policy

Purpose: catch unsafe context and generated artifacts before launch.

Baseline gates:

- `secret_scan` over context packet and requirement inputs
- `secret_scan` over generated backend/frontend/docs
- dependency audit via project security command

Future hardening:

- prompt-injection classifier for imported requirements
- auth/RBAC acceptance tests
- dependency lockfile policy
- Docker image scan
