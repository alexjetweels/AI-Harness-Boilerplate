---
description: Execute the implementation plan by processing and executing all tasks defined in tasks.md
model: claude-sonnet-4-6
tools: [Read, Write, Edit, Bash, Glob, Grep, TodoWrite]
---

## Execution Logging & Phase Report (Constitution Art. XI & XII)

### ⛔ MANDATORY — Two Output Files Required

This agent **MUST** create one output file during execution. The pipeline CANNOT advance to the next step without it.

| # | File | Path | When |
|---|------|------|------|
| 1 | **Phase Report** | `docs/output/output_logs/<feature-id>/reports/<NN>-<phase>-report.md` | **LAST** — after all other work |

Where `<NN>` is determined by the Boss orchestrator's delegation instruction:
- STEP 10 (implementation): `NN=10`, `phase=implement`



**When the Boss passes an explicit NN value** (e.g., "Use NN=10"), use that value exactly.
**When no NN is specified**, determine from context: check the Boss instruction for "STEP 10/12/13" keywords.

### Step 0 — Setup

**Before doing ANY other work**, you MUST:

1. Determine `<feature-id>` and `<NN>` from the context
2. Create directories: `docs/output/output_logs/<feature-id>/` and `docs/output/output_logs/<feature-id>/reports/`

### Step FINAL — Write Phase Report (⚠️ DO THIS LAST — NON-NEGOTIABLE)

Write to: `docs/output/output_logs/<feature-id>/reports/<NN>-<phase>-report.md`

> 📄 Follow **Universal Report Structure** from `templates/report-templates.md` (STEP 10/12/13 — depends on current phase).

**Step-specific overrides:**
- **Title:** `# STEP <NN>: <Implementation Report / Build Verification Report / Launch Report>`
- **Agent:** `speckit.implement (gpt-5-3-codex)`
- **Input:** tasks (`tasks.md`), implementation plan (`plan.md`), data model (`data-model.md`), contracts (`contracts/*.md`)
- **Quality evaluation categories:** compile success, test pass, coverage threshold met, checklist completion
- **Metrics:** completed task count, created file count, changed file count, test count (pass/fail), coverage
- **Additional section (STEP 10):** `## Screen Verification`
- **Next phase:** STEP 10→`okr.reviewcode` (STEP 11)

### ⛔ COMPLETION HARD GATE

Report file `docs/output/output_logs/<feature-id>/reports/<NN>-<phase>-report.md` MUST exist with ALL sections before returning.

---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. Run `.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Check checklists status** (if FEATURE_DIR/checklists/ exists):
   - Scan all checklist files in the checklists/ directory
   - For each checklist, count:
     - Total items: All lines matching `- [ ]` or `- [X]` or `- [x]`
     - Completed items: Lines matching `- [X]` or `- [x]`
     - Incomplete items: Lines matching `- [ ]`
   - Create a status table:

     ```text
     | Checklist | Total | Completed | Incomplete | Status |
     |-----------|-------|-----------|------------|--------|
     | ux.md     | 12    | 12        | 0          | ✓ PASS |
     | test.md   | 8     | 5         | 3          | ✗ FAIL |
     | security.md | 6   | 6         | 0          | ✓ PASS |
     ```

   - Calculate overall status:
     - **PASS**: All checklists have 0 incomplete items
     - **FAIL**: One or more checklists have incomplete items

   - **If any checklist is incomplete**:
     - Display the table with incomplete item counts
     - **STOP** and ask: "Some checklists are incomplete. Do you want to proceed with implementation anyway? (yes/no)"
     - Wait for user response before continuing
     - If user says "no" or "wait" or "stop", halt execution
     - If user says "yes" or "proceed" or "continue", proceed to step 3

   - **If all checklists are complete**:
     - Display the table showing all checklists passed
     - Automatically proceed to step 3

3. Load and analyze the implementation context:
   - **REQUIRED**: Read tasks.md for the complete task list and execution plan
   - **REQUIRED**: Read plan.md for tech stack, architecture, and file structure
   - **IF EXISTS (BINDING)**: Read data-model.md for entities and relationships.
     When this file exists **and** plan.md specifies a database (Storage ≠ N/A),
     ALL entities in data-model.md **MUST** be created as Prisma models in `schema.prisma`
     with Prisma migrations and a seed script.
     **In-memory substitutes (HashMap, ConcurrentHashMap, static demo data) are
     PROHIBITED** for any entity defined in data-model.md.
   - **IF EXISTS**: Read contracts/ for API specifications and test requirements
   - **IF EXISTS**: Read research.md for technical decisions and constraints
   - **IF EXISTS**: Read quickstart.md for integration scenarios

4. **Project Setup Verification**:
   - **REQUIRED**: Create/verify ignore files based on actual project setup:

   **Detection & Creation Logic**:
   - Check if the following command succeeds to determine if the repository is a git repo (create/verify .gitignore if so):

     ```sh
     git rev-parse --git-dir 2>/dev/null
     ```

   - Check if Dockerfile* exists or Docker in plan.md → create/verify .dockerignore
   - Check if .eslintrc* exists → create/verify .eslintignore
   - Check if eslint.config.* exists → ensure the config's `ignores` entries cover required patterns
   - Check if .prettierrc* exists → create/verify .prettierignore
   - Check if .npmrc or package.json exists → create/verify .npmignore (if publishing)
   - Check if terraform files (*.tf) exist → create/verify .terraformignore
   - Check if .helmignore needed (helm charts present) → create/verify .helmignore

   **If ignore file already exists**: Verify it contains essential patterns, append missing critical patterns only
   **If ignore file missing**: Create with full pattern set for detected technology

   **Common Patterns by Technology** (from plan.md tech stack):
   - **Node.js/JavaScript/TypeScript**: `node_modules/`, `dist/`, `build/`, `*.log`, `.env*`
   - **Python**: `__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `dist/`, `*.egg-info/`
   - **Java**: `target/`, `*.class`, `*.jar`, `.gradle/`, `build/`
   - **C#/.NET**: `bin/`, `obj/`, `*.user`, `*.suo`, `packages/`
   - **Go**: `*.exe`, `*.test`, `vendor/`, `*.out`
   - **Ruby**: `.bundle/`, `log/`, `tmp/`, `*.gem`, `vendor/bundle/`
   - **PHP**: `vendor/`, `*.log`, `*.cache`, `*.env`
   - **Rust**: `target/`, `debug/`, `release/`, `*.rs.bk`, `*.rlib`, `*.prof*`, `.idea/`, `*.log`, `.env*`
   - **Kotlin**: `build/`, `out/`, `.gradle/`, `.idea/`, `*.class`, `*.jar`, `*.iml`, `*.log`, `.env*`
   - **C++**: `build/`, `bin/`, `obj/`, `out/`, `*.o`, `*.so`, `*.a`, `*.exe`, `*.dll`, `.idea/`, `*.log`, `.env*`
   - **C**: `build/`, `bin/`, `obj/`, `out/`, `*.o`, `*.a`, `*.so`, `*.exe`, `autom4te.cache/`, `config.status`, `config.log`, `.idea/`, `*.log`, `.env*`
   - **Swift**: `.build/`, `DerivedData/`, `*.swiftpm/`, `Packages/`
   - **R**: `.Rproj.user/`, `.Rhistory`, `.RData`, `.Ruserdata`, `*.Rproj`, `packrat/`, `renv/`
   - **Universal**: `.DS_Store`, `Thumbs.db`, `*.tmp`, `*.swp`, `.vscode/`, `.idea/`

   **Tool-Specific Patterns**:
   - **Docker**: `node_modules/`, `.git/`, `Dockerfile*`, `.dockerignore`, `*.log*`, `.env*`, `coverage/`
   - **ESLint**: `node_modules/`, `dist/`, `build/`, `coverage/`, `*.min.js`
   - **Prettier**: `node_modules/`, `dist/`, `build/`, `coverage/`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`
   - **Terraform**: `.terraform/`, `*.tfstate*`, `*.tfvars`, `.terraform.lock.hcl`
   - **Kubernetes/k8s**: `*.secret.yaml`, `secrets/`, `.kube/`, `kubeconfig*`, `*.key`, `*.crt`

5. Parse tasks.md structure and extract:
   - **Task phases**: Setup, Tests, Core, Integration, Polish
   - **Task dependencies**: Sequential vs parallel execution rules
   - **Task details**: ID, description, file paths, parallel markers [P]
   - **Execution flow**: Order and dependency requirements

6. Execute implementation following the task plan:
   - **⛔ PATH VALIDATION (runs before first file creation)**:
     Scan all file paths in `tasks.md` and `plan.md`. Reject any path that does NOT follow
     the canonical layout:
     - TypeScript backend source → `backend/src/<feature>/` or `backend/src/auth/` or `backend/src/common/`
     - React pages → `frontend/src/pages/<FeaturePage>.tsx`
     - Layout components → `frontend/src/components/layout/`
     - UI components → `frontend/src/components/ui/`
     - Prisma schema & migrations → `backend/prisma/`
     - Jest tests → `backend/test/`
     - Controller tests → co-located in `backend/src/<feature>/`
     - Playwright E2E → `e2e/`
     - `okr-workshop/modXX-lib/` — ❌ INVALID (wrong legacy path)
     - `okr-workshop-web/src/features/` — ❌ INVALID (wrong React path)
     If invalid paths are found, **correct them to canonical paths** and write a
     `[PROCESSING] path corrected` log entry for each correction before proceeding.
   - **⛔ SHARED UI LAYOUT (runs before creating any frontend page)**:
     Before creating any page component, check if the shared layout exists:
     ```
     frontend/src/components/layout/AppLayout.tsx
     frontend/src/components/layout/Header.tsx
     frontend/src/components/layout/Sidebar.tsx
     ```
     If these files do NOT exist, create them first following the Tailwind CSS design system:
     - **Header**: Fixed top bar with `bg-white border-b border-gray-200`, height 64px.
     - **Sidebar**: Fixed left nav with `bg-white border-r border-gray-200`, width 256px.
     - **AppLayout**: Wraps `Sidebar` + `Header` + `{children}` in a
       consistent layout using Tailwind utility classes.
     ALL page components MUST use `<AppLayout>` instead of ad-hoc inline navigation.

   - **⛔ BD LAYOUT COMPLIANCE (runs before creating any frontend page)**:
    Before creating page components, MUST read the BD (Basic Design document) wireframe:
     ```
     docs/output/ipa-docs/bd/bd-modXX-*.md
     ```
     Extract and follow:
     - **Sidebar**: If BD shows left sidebar → create `Sidebar.tsx` in `frontend/src/components/layout/` with matching width, nav items, and Tailwind classes
     - **Header**: Use exact brand color from BD/constitution
     - **Navigation**: Tab-based, sidebar-based, or breadcrumb per BD specification
     - **Content layout**: Column grid, card placement, table structure per wireframe
     - **Screen components**: One `.tsx` file per screen defined in BD at `frontend/src/pages/`
     If this file does not exist, proceed with constitution Layout-01~06 defaults.

   - **⛔ REACT FRONTEND QUALITY RULES (Post-Mortem P-06, P-07, P-10):**
     1. **React Router future flags:** When using React Router DOM v6, ALWAYS add:
        ```tsx
        <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        ```
     2. **NEVER call `navigate()` during render.** For conditional redirects in render body, use:
        ```tsx
        if (isAuthenticated) return <Navigate to="/dashboard" replace />;
        ```
     3. **ADMIN role query logic:** List/dashboard endpoints MUST handle ADMIN role seeing ALL records:
        ```ts
        const where = user.role === 'ADMIN' ? {} : { ownerId: user.id };
        ```
     4. **Error boundaries:** Wrap router root in `<AppErrorBoundary>`.
     5. **Axios interceptor:** Configure base URL and auth token refresh in a single `api.ts` client file.

   - **⛔ DEV DATA SEED (runs after creating Prisma schema/migrations)**:
     After updating `schema.prisma` and running `prisma migrate dev`, MUST also:
     1. Update `backend/prisma/seed.ts` with ≥3 realistic rows per entity table using `upsert` for idempotency
     2. If the module depends on external integrations defined by the project plan:
        create a NestJS service `Dev<Feature>Simulator.ts` conditionally registered for dev environment
        that injects realistic values into the DB at regular intervals (using `@Cron` or `setInterval`)
     3. For trend/chart screens: seed ≥30 days of historical data at the module's collection interval
     4. In NestJS guards config: ensure all GET endpoints accessible in dev (adjust guard logic — do NOT use per-method `@UseGuards` overrides)
   - **Phase-by-phase execution**: Complete each phase before moving to the next
   - **Respect dependencies**: Run sequential tasks in order, parallel tasks [P] can run together  
   - **Follow TDD approach**: Execute test tasks before their corresponding implementation tasks
   - **File-based coordination**: Tasks affecting the same files must run sequentially
   - **Validation checkpoints**: Verify each phase completion before proceeding

7. Implementation execution rules:
   - **Setup first**: Initialize project structure, dependencies, configuration
   - **Tests before code**: If you need to write tests for contracts, entities, and integration scenarios
   - **Core development**: Implement models, services, CLI commands, endpoints
   - **Integration work**: Database connections, middleware, logging, external services
   - **Polish and validation**: Unit tests, performance optimization, documentation

7b. **Persistence enforcement** (when data-model.md exists and Storage ≠ N/A):
   - Create Prisma migration scripts for ALL tables, indexes, constraints defined in data-model.md (`npx prisma migrate dev`)
   - Update `backend/prisma/schema.prisma` with models matching every entity in data-model.md (field names, types, relationships)
   - **⛔ Prisma Portable Schema (Post-Mortem):**
     - Do NOT use `enum` blocks in schema.prisma — use `String` type with `@default("VALUE")` instead
     - Do NOT use `@db.VarChar()`, `@db.Text`, or any provider-specific annotations
     - Default provider MUST be `sqlite` for local dev portability
     - Create `backend/src/common/types/domain-enums.ts` with `const` arrays + derived types for all enumerations
     - Import enum types from `domain-enums.ts`, NEVER from `@prisma/client` enum types
   - Use Prisma Client (`PrismaService`) for all DB operations — no raw SQL, no TypeORM
   - Database connection is configured via `DATABASE_URL` in environment:
     - **Docker mode:** `DATABASE_URL` set in `docker-compose.yml` (MySQL/PostgreSQL)
     - **Local mode (no Docker):** Create `backend/.env` with `DATABASE_URL="file:./dev.db"` (SQLite)
   - **MUST create `backend/.env.example`** with all required env vars (placeholder values)
   - **MUST create `backend/.env`** with working defaults for local development
   - **NEVER hardcode secrets (JWT_SECRET, DB passwords) in source code** — always use `process.env` or `ConfigService`
   - Application must **fail-fast** at startup if the database is unreachable — never silently fall back to in-memory data
   - **NEVER** create demo / in-memory services that bypass the persistence layer
   - If the database is not available during development, STOP and instruct the user to start the database (`docker-compose up`) rather than substituting in-memory data

8. Progress tracking and error handling:
   - Report progress after each completed task
   - Halt execution if any non-parallel task fails
   - For parallel tasks [P], continue with successful tasks, report failed ones
   - Provide clear error messages with context for debugging
   - Suggest next steps if implementation cannot proceed
   - **IMPORTANT** For completed tasks, make sure to mark the task off as [X] in the tasks file.

9. Completion validation:
   - Verify all required tasks are completed
   - Check that implemented features match the original specification
   - Validate that tests pass and coverage meets requirements
   - Confirm the implementation follows the technical plan
   - **If data-model.md exists**: verify ALL entities have corresponding Prisma models in `schema.prisma`,
     Prisma migrations, and `DATABASE_URL` configured in `docker-compose.yml`.
     **FAIL** the implementation if any are missing or if any in-memory demo service remains.
   - Report final status with summary of completed work

Note: This command assumes a complete task breakdown exists in tasks.md. If tasks are incomplete or missing, suggest running `/speckit.tasks` first to regenerate the task list.

---

## STEP 10 Mode: Build, Start & Verify on Screen

When invoked by `okr.bossbuiltin` for **STEP 10** (the instruction will contain "Build, run, and verify"), execute the following concrete sequence using the `run` tool. Do NOT skip to simulated log output — run actual commands.

> **⚠️ CRITICAL EXECUTION RULES (applies to ALL steps)**:
> 1. **USE the `run` tool** for every terminal command. DO NOT document commands without executing them.
> 2. **USE `get_errors`** after editing code to verify no compile/lint errors remain.
> 3. **Capture REAL output** from the `run` tool. DO NOT write simulated/mock output.
> 4. **If a command fails**: read the error, fix the source code, re-run the command.
> 5. **Track retries**: record each fix attempt and re-run in the execution log.
> 6. **For frontend**: Always `npm install` first if `node_modules/` does not exist.

### 10-A: Start Infrastructure

```bash
# 0. Detect Docker availability
docker --version
```

**If Docker is available:**
```bash
# 1. Start all services via Docker Compose (docker-compose.yml at project root)
docker-compose up -d

# 2. Wait for health checks (poll until ready, max 60s)
docker-compose ps
```

**If Docker is NOT available (fallback to local SQLite):**
```bash
# 1. Ensure backend/.env exists with SQLite config
# DATABASE_URL="file:./dev.db"
# JWT_SECRET=<generated>
# JWT_REFRESH_SECRET=<generated>

# 2. Ensure schema.prisma uses provider = "sqlite" (no enums, no @db annotations)

# 3. Run Prisma migrations + seed
cd backend && npx prisma migrate dev --name init && npx prisma db seed
```

> **⚠️ When falling back to SQLite:** Verify schema.prisma has NO `enum` blocks and NO `@db.*` annotations. If found, fix schema first.

The project uses `docker-compose.yml` at the workspace root, which provides:
- `mysql:8.0` — port 3306, credentials hardcoded (`okr_user`/`okr_password`, db `okr_db`)
- `backend` (NestJS) — port 3000, auto-runs `prisma migrate deploy` + seed on start
- `frontend` (Vite) — port 5173 with HMR
- `adminer` — port 8080 (DB GUI)

### 10-B: Build

```bash
# Build backend from its directory
cd backend && npm install && npm run build
```

Expected: `dist/main.js` present in `backend/dist/`.

### 10-C: Start Application

```bash
cd backend && npm run start:dev &
```

Wait for log line: `NestJS application listening on port 3000` (poll for max 30s).

### 10-D: Verify Screens

For each screen ID defined in `spec.md` (e.g., SCR-mod01-01, SCR-mod01-02, SCR-mod01-03):

```bash
# Check main SPA entry point
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/
# Expected: 200

# Check API endpoints (example)
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $TEST_JWT" \
  http://localhost:3000/api/v1/<feature>/<endpoint>
# Expected: 200
```

Log each result. Any non-200 is a FAIL → trigger auto-retry loop.

### 10-D2: Data Presence Verification

For each primary GET endpoint, verify the response contains **actual data**:

```bash
# Check that API returns non-empty data
RESPONSE=$(curl -s http://localhost:3000/api/v1/<feature>/<primary-endpoint>)
# Verify: $RESPONSE is NOT "[]", NOT "{}", NOT "0", NOT empty
# If empty/zero → diagnose:
#   (a) DB tables seeded? → check `backend/prisma/seed.ts` ran (via `npx prisma db seed` or container entrypoint)
#   (b) Guard config permits the endpoint? → check dev guard logic
```

Log each endpoint's data presence status. Any empty-data endpoint is a FAIL → fix seed/simulator/auth and retry.

### 10-E: Run Full Test Suite

```bash
cd backend && npm test -- --coverage
# Istanbul/c8 ≥ 80% enforced here
```

### 10-F: Write STEP 10 log + report

After all commands complete:
2. Write `docs/output/output_logs/<feature-id>/reports/12-verify-report.md` with per-screen HTTP status table and Istanbul/c8 results

---

## Pipeline Context Integration

If `$ARGUMENTS` contains a `pipeline-context:` key, read that YAML file at startup to discover:
- `feature-id`, `module-id`, all artifact paths from prior steps
- Tech stack summary (no need to re-read `docs/technical_architecture.md` for basics)

## Step Result Block — MANDATORY

As your **absolute last output**, include (adjust `step` and `report` path per NN value):

```yaml
<!-- STEP-RESULT
step: <NN>
agent: speckit.implement
status: SUCCESS | FAILED
feature-id: <feature-id>
module-id: <mod-id>
artifacts:
  report: docs/output/output_logs/<feature-id>/reports/<NN>-<phase>-report.md
metrics:
  files-created: <N>
  files-modified: <N>
  errors-fixed: <N>
verdict: N/A
critical-issues: []
next-inputs: {}
/STEP-RESULT -->
```
