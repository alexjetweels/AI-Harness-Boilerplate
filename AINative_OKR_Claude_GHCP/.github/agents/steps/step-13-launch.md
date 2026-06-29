# Step 13: Launch

> Boss MUST read this file before executing Step 13.
> Protocols referenced: `protocols/report-gate-protocol.md`

---

## STEP 13 — Build, Connect DB & Launch Screen

> ✅ Step 12 verdict = ALL TESTS PASS → launch with confidence.
> ⚠ Step 12 verdict = FAIL (after 3 cycles) → still launch, but notify user of known defects.
> ⚠ All code errors MUST have been resolved in Steps 10–12. STEP 13 does NOT fix code.

| Key | Value |
|-----|-------|
| Agent | Boss (self — direct execution) |
| Report | `reports/13-launch-report.md` |
| Gate | REPORT HARD GATE (+ "Launch Status" section required) |
| Max retries | 5 |

### ⛔ PRE-LAUNCH: Environment Detection (MANDATORY — run FIRST)

Before ANY build/start command, Boss MUST detect the runtime environment:

```
1. Check Docker availability:
   - Run: `docker --version` (or `docker info`)
   - If SUCCEEDS → Docker mode (use docker-compose)
   - If FAILS → Local mode (fallback to SQLite + local Node)

2. Check database availability (Local mode only):
   - If MySQL/PostgreSQL configured in docker-compose.yml but Docker unavailable:
     → Switch Prisma schema to SQLite provider
     → Create .env with DATABASE_URL="file:./dev.db"
     → Remove enum definitions (SQLite does not support enums)
     → Create local TypeScript type definitions to replace Prisma enums
     → Run: npx prisma migrate dev --name init && npx prisma db seed

3. Check port availability:
   - Run: `netstat -ano | findstr :<PORT>` (Windows) or `lsof -i :<PORT>` (Unix)
   - If port in use → kill existing process BEFORE starting new one
   - Log [ISSUE] entry with killed PID

4. Verify .env file exists:
   - backend/.env MUST exist with at minimum: DATABASE_URL, JWT_SECRET
   - If missing → CREATE it with sensible defaults for local dev
   - JWT_SECRET MUST be read from env, NEVER hardcoded in source
```

### Execution — Boss builds & launches directly (no delegation)

Boss MUST directly:

1. **Build Backend:**
   - `cd backend && npm install && npm run build`
   - If build fails, log `[ISSUE]` and retry (do NOT fix code — code must be clean from Steps 10–12)
2. **Connect DB (if the chosen stack uses a database):**
   - **Docker mode:** Start Docker infrastructure: `docker-compose up -d` (or `docker compose -f docker/docker-compose.dev.yml up -d`)
   - **Local mode (Docker unavailable):**
     - Verify `backend/.env` has `DATABASE_URL` pointing to SQLite file
     - Run `cd backend && npx prisma migrate dev --name init` if no migrations exist
     - Run `cd backend && npx prisma db seed` to populate data
   - Verify the application can connect to the configured database
3. **Build Frontend:**
   - `cd frontend && npm install && npm run build`
   - (Output is bundled to `backend/src/static/`)
4. **Start Backend (background):**
   - **FIRST:** Kill any existing process on the backend port (default 3000):
     - Windows: `Get-Process -Id (Get-NetTCPConnection -LocalPort 3000).OwningProcess -ErrorAction SilentlyContinue | Stop-Process -Force`
     - Unix: `lsof -ti:3000 | xargs kill -9`
   - `cd backend && node dist/main.js &`
   - Wait for startup confirmation in logs
5. **Start Frontend dev server (background, for screen verification only):**
   - **FIRST:** Kill any existing process on port 5173 (same pattern as above)
   - `cd frontend && npm run dev`
   - Confirm dev server is listening on `http://localhost:5173`
6. **Verify screens:**
   - Read `specs/<feature-id>/spec.md` → find first screen route (`SCR-MOD[XX]-01` URL path)
   - Confirm screens are accessible and data is visible from DB (not mock)
7. **Open browser:**
   - **Call `open_browser_page`** with URL: `http://localhost:5173/<first-screen-route>`
   - This is the **final mandatory deliverable** of the pipeline
   - The user MUST see the running UI without manual action
8. **Write `[END]`** entry in boss log with the exact URL

### Auto-Retry Gate

- All screens accessible + data visible → write `[END]` pipeline complete
- Startup errors → Auto-Retry Loop (max 5 retries):
  1. Write `[ISSUE]` in boss log
  2. Retry startup sequence
  3. If retry > 5: `[ESCALATION]`, mark PARTIAL COMPLETE

> ⛔ **[REPORT GATE]** per `protocols/report-gate-protocol.md`
