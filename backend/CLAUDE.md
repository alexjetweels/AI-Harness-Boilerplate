# Backend Guidance

The backend is a FastAPI service.

## Conventions

- Keep request and response shapes explicit with Pydantic models.
- Avoid hidden global state for production behavior. The current in-memory run store is acceptable for dashboard simulation only.
- When wiring real harness execution, isolate subprocess execution, stream logs, and persist state instead of relying only on memory.
- Return stable status values that the frontend can render without guessing.

## Checks

Prefer these commands when backend behavior changes:

```bash
cd backend
python -m compileall app
```

If new test tooling is added, update this file and `spec-harness/harness.sdlc.yaml`.

