# Frontend Guidance

The frontend is a Vite React dashboard.

## Conventions

- Keep dashboard views dense, operational, and easy to scan.
- Use existing React component style in `src/main.jsx` unless a larger refactor is explicitly needed.
- Use icons from `lucide-react` for toolbar and status actions.
- Avoid marketing-page layout patterns; this is an operations surface.

## Checks

Prefer these commands when frontend behavior changes:

```bash
cd frontend
npm run build
```

If lint or tests are added later, update this file and `spec-harness/harness.sdlc.yaml`.

