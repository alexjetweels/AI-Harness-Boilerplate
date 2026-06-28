# Testing Rules

- Map every implemented requirement to at least one verification step.
- Prefer deterministic tests, typechecks, linters, builds, or shell gates over subjective review.
- If a test cannot be run locally, document the exact blocker and residual risk.
- Add regression coverage when fixing a bug with a clear reproduction path.
- Keep acceptance checks executable from the repository root when possible.

