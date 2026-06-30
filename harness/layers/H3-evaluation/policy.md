# H3 Evaluation Harness Policy

Purpose: verify each SDLC phase with deterministic gates.

Gate classes:

- `glob_nonempty`: required artifact exists
- `no_markers`: unresolved markers are absent
- `agent_output`: review output contains no blocking markers
- `shell`: build, lint, test, security, and acceptance commands pass
- `json_no_missing_required`: required context sources are present

OKR required artifact families:

- SRS documents
- Basic Design documents
- Spec-Kit spec, plan, data model, and tasks
- Detail Design documents
- Test cases and reports
- Backend, frontend, Docker runtime files
