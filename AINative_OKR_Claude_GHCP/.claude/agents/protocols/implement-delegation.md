# Common Delegation Block for speckit.implement

This delegation block is used by the Boss when invoking `speckit.implement` in Step 10.
Sub-agent already knows its own workflow — Boss only passes **step-specific context**.

## Standard Context (always included)

```yaml
feature-id: <feature-id>
module-id: <mod-id>
report-nn: <NN>
report-phase: <phase-name>
pipeline-context: docs/output/output_logs/<feature-id>/pipeline-context.yaml
mode: autonomous
language: Vietnamese
```

## Empty Workspace Handling (Mandatory)

`backend/` and `frontend/` not existing yet is the **expected state** before Step 10 runs — no
earlier pipeline step creates application source code (Steps 1-9 only produce design/spec
documents). Finding no source tree is a signal to scaffold the application from
`plan.md` + `data-model.md` + `tasks.md`, not a blocker.

- Do NOT stop to ask the user for an existing codebase or repo pointer.
- Do NOT produce a phase report whose conclusion is "cannot implement without an existing
  frontend/backend" — write the code instead.
- If something is genuinely ambiguous (e.g. a task references a library not in
  `technical_architecture.md`), follow `protocols/auto-resolve-protocol.md` and document the
  assumption in the report — do not use ambiguity as a reason to skip code generation entirely.

## Real Execution Mandate

ALL terminal commands MUST be executed via the `run` tool with real output captured.

- **PROHIBITED:** Documenting commands without executing, mock output, skipping npm commands.
- **REQUIRED:** Use `get_errors` after every code edit to verify compile/lint errors are resolved.
- **REQUIRED:** For frontend under `frontend/`, run `npm install` if `node_modules/` does not exist.

## ⛔ Portable Database Schema Rules (Post-Mortem P-02, P-05)

When generating Prisma schema:

1. **Do NOT use `enum` in schema.prisma** — SQLite does not support enums. Use `String` type with `@default("VALUE")` instead.
2. **Do NOT use `@db.VarChar()`, `@db.Text`, or any provider-specific annotations** — these break when switching providers.
3. **Create `backend/src/common/types/domain-enums.ts`** with TypeScript `const` arrays + derived types for all domain enumerations:
   ```ts
   export const ROLES = ['ADMIN', 'MANAGER', 'EMPLOYEE'] as const;
   export type Role = (typeof ROLES)[number];
   ```
4. **Import enums from `domain-enums.ts`**, NEVER from `@prisma/client` enum types.
5. **Use `provider = "sqlite"` as default** for local dev. Only switch to MySQL/PostgreSQL when Docker is confirmed available.

## ⛔ Mandatory .env File Creation (Post-Mortem P-03)

During Step 10 implementation, the agent MUST:

1. **Create `backend/.env`** with at minimum:
   ```
   DATABASE_URL="file:./dev.db"
   JWT_SECRET=<random-generated-secret>
   JWT_REFRESH_SECRET=<random-generated-secret>
   PORT=3000
   ```
2. **Create `backend/.env.example`** (same keys, placeholder values) for documentation.
3. **NEVER hardcode JWT secrets, database URLs, or API keys in source code.** All secrets MUST be read from `process.env`.
4. Add `.env` to `.gitignore` (but NOT `.env.example`).

## ⛔ Security: Secrets Management (Post-Mortem P-09)

- JWT_SECRET, JWT_REFRESH_SECRET, DATABASE_URL → **env-only, NEVER in source files**
- Use `@nestjs/config` `ConfigService` or `process.env` to read secrets at runtime
- If `technical_architecture.md` says "hardcoded (workshop)" → OVERRIDE: still use env vars. Security trumps convenience.

## ⛔ React Frontend Quality Rules (Post-Mortem P-06, P-07)

1. **React Router future flags:** When using React Router DOM v6, ALWAYS add future flags to `<BrowserRouter>`:
   ```tsx
   <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
   ```
2. **NEVER call `navigate()` during render.** Use `<Navigate to="..." replace />` component for conditional redirects in render body.
3. **ADMIN role queries:** When implementing list/dashboard endpoints, ADMIN role MUST see ALL records (not filtered by `ownerId`). Add role-based query logic:
   ```ts
   const where = user.role === 'ADMIN' ? {} : { ownerId: user.id };
   ```

## Step-Specific Additional Instructions

### STEP 10 — Implementation + Build & Fix
```
Phase 1 — Implement:
Execute all tasks in docs/output/specs/<feature-id>/tasks.md phase by phase.
Track every file created/modified in the report's Artifacts section.

Phase 2 — Build & Fix:
Build the application and fix all compile/runtime errors. Do NOT launch the screen.
Execute in order:
1. Fix all compile/lint errors (get_errors → fix → repeat until zero)
2. Build frontend: cd frontend && npm install && npm run build
3. Start Docker (if docker-compose.dev.yml exists): docker compose -f docker/docker-compose.dev.yml up -d
4. Build backend: cd backend && npm install && npm run build
5. Verify startup (if Docker available): cd backend && npm run start:dev
```

## UI Layout Convention (for frontend work)

> Read `docs/technical_architecture.md §IV` for all UI layout rules.
> Shared components: `AppLayout.jsx`, `SystemHeader.jsx`, `ModuleNav.jsx` under `frontend/src/components/shared/`
> Create if not exist, reuse if they do. Wrap ALL page components in `<AppLayout>`.
