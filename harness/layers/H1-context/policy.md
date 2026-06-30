# H1 Context Harness Policy

Purpose: build a deterministic context packet before any agent call.

Required behavior:

- Read target guidance, requirements, architecture, constitution, protocols, and step definitions.
- Store context packet and manifest as Postgres `harness_artifacts`.
- Record file path, role, required flag, byte size, and SHA-256 for every context source.
- Fail the run if required context sources are missing.

Implementation hook:

- `packages/ai-harness/src/context/builder.py`
- `context:` block in target harness config
