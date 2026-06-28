# Architecture Rules

- Preserve module boundaries unless the task explicitly changes them.
- Introduce a new dependency only when it removes clear complexity or matches the existing stack.
- For cross-cutting changes, update `docs/architecture.md` or add an ADR under `docs/sdlc/current/`.
- Capture data flow, control flow, and failure modes for new orchestration behavior.
- Prefer deterministic gates over LLM-only judgment for final acceptance.

