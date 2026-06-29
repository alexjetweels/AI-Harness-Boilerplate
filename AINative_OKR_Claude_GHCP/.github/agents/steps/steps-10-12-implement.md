# Steps 10–12: Implementation & QA Phase

> Boss MUST read this file before executing Steps 10–12.
> Protocols referenced: `protocols/gate-retry-protocol.md`, `protocols/report-gate-protocol.md`, `protocols/implement-delegation.md`

---

## STEP 10 — Implementation + Build & Fix (Auto-Retry)

| Key | Value |
|-----|-------|
| Agent | `speckit.implement` |
| Model | `gpt-5-3-codex` |
| Input | `tasks.md`, `plan.md`, `data-model.md`, `contracts/`, `docs/output/ipa-docs/testcase/testcase-<mod-id>-<short-name>.md` |
| Report | `reports/10-implement-report.md` (NN=10, phase=implement) |
| Gate | BUILD GATE (Auto-Retry) + REPORT HARD GATE (+ "Test Results" + "Screen Verification" sections required) |
| Max retries | 5 |

**Delegation:** Per `protocols/implement-delegation.md` § STEP 10.

**Additional context:**
```yaml
feature-id: <feature-id>
module-id: <mod-id>
report-nn: 10
report-phase: implement
pipeline-context: docs/output/output_logs/<feature-id>/pipeline-context.yaml
```

**Phase 1 — Gen test:**
- Every source file under `src/` must have a dedicated test file under `test/` or co-located (following standard TypeScript/Jest testing conventions)
- All checklist items in `specs/<feature-id>/checklists/` must be resolved before proceeding
- Auto-resolve any checklist ambiguities per `protocols/auto-resolve-protocol.md`

**⛔ Test Quality Mandate (Post-Mortem P-08):**
- Integration tests MUST use real database (SQLite for local, Docker DB for CI) — **in-memory mocks are PROHIBITED**
- Every endpoint test MUST verify: HTTP status, response shape, actual DB state change (read-back after write)
- Authorization tests MUST verify: unauthenticated → 401, wrong role → 403, ownership violation → 403
- Pseudo-tests (tests that always pass, mock everything, or have no assertions) are treated as CRITICAL review failure

**Phase 2 — Implement:**
- Execute all tasks in `specs/<feature-id>/tasks.md` phase by phase
- All checklist items in `specs/<feature-id>/checklists/` must be resolved before proceeding
- Auto-resolve any checklist ambiguities per `protocols/auto-resolve-protocol.md`

**Phase 3 — Build & Fix:**
1. Fix all compile/lint errors (`get_errors` → fix → repeat until zero)
2. Build frontend: `cd frontend && npm install && npm run build`
3. Start Docker (if `docker-compose.dev.yml` exists): `docker compose -f docker/docker-compose.dev.yml up -d`
4. Build backend: `cd backend && npm install && npm run build`
5. Verify startup (if Docker available): `cd backend && npm run start:dev`

**Gate logic:**
- ✅ Build succeeds + app starts → proceed to Step 11
- ❌ Build/startup fails → **Auto-Retry Loop:**
  1. Capture error log
  2. Write `[ISSUE]` in boss log
  3. Invoke `speckit.implement`: *"Fix build/startup errors: <error log>. Minimal fix."*
  4. Retry build sequence
  5. If retry > 5: `[ESCALATION]`, mark PARTIAL COMPLETE

> ⛔ **[REPORT GATE]** per `protocols/report-gate-protocol.md`

---

## STEP 11 — Code Review (Auto-Retry)

| Key | Value |
|-----|-------|
| Agent | `okr.reviewcode` |
| Model | `claude-sonnet-4-6` |
| Input | Implemented source code, spec, tasks, constitution |
| Report | `reports/11-review-code-report.md` |
| Gate | REVIEW GATE (Auto-Retry) + REPORT HARD GATE |
| Fix agent | `speckit.implement` |
| Max retries | 5 |

**Gate logic:**
- ✅/⚠️ → proceed to Step 12
- ❌ REJECTED → invoke `speckit.implement` to fix CRITICAL issues → re-invoke `okr.reviewcode`
- Escalation after 5 retries → continue to Step 12

**Additional DB Data Check:**
Code review MUST also verify:
- All screen data is fetched from the database (via Prisma Client / API endpoints), NOT from mock/hardcoded data
- Prisma seed script (`backend/prisma/seed.ts`) includes necessary seed data for the screens to display real content
- Frontend components call real API endpoints (not mock adapters or static JSON)
- If mock data is detected, mark as ❌ CRITICAL and instruct fix agent to replace with DB-backed data

> ⛔ **[REPORT GATE]** per `protocols/report-gate-protocol.md`

---

## STEP 12 — Final QA Audit: Test Execution (Independent QA)

| Key | Value |
|-----|-------|
| Agent | `okr.testkit` |
| Model | `claude-sonnet-4-6` |
| Mode | `run-tests` |
| Prerequisite | Step 10 PASSED |
| Report (Phase C) | `reports/12-testkit-report.md` |
| Report (Phase D) | `docs/output/ipa-docs/testreport/testreport-<MOD-ID>-<short-name>.md` |
| Gate | TEST GATE (BACK-TO-PLAN on FAIL) |

> ⚠ This is the **FINAL quality gate** before launch. No screen shown until ALL tests pass.

**Delegation `$ARGUMENTS`:**
```
run-tests <feature-id>
```

**Additional delegation context (mandatory):**

Pipeline report (Phase C) MUST include:
1. `## Test Execution Summary` — Category | Total | Passed | Failed | Skipped | Pass Rate
2. `## Failed Test Details` — every failed test with TC-ID, failure reason, design reference
3. `## Retry Log` — Retry Count | Target | Fix Applied | Result
4. `## Screen Verification Results (E2E)` — per-screen accessibility
5. `## Coverage` — Istanbul/c8 metrics
6. `## Overall Verdict` — PASS / FAIL

IPA detail report (Phase D) generation rules:
- Take `docs/output/ipa-docs/testcase/testcase-<MOD-ID>-<short-name>.md` as BASE
- Rename title to `Test Execution Result Report`
- Keep ALL test case rows intact — fill `Execution Result`, `Verdict`, `Notes` columns only
- Add `## Test Execution Summary`, `## Coverage Results` at top
- Append `## Screen Verification Results`, `## SRS/BD/DD Compliance Check`, `## Overall Verdict` at bottom

**GATE — FAIL ← BACK TO PLAN (Full Fix Cycle):**

Per `protocols/gate-retry-protocol.md` § BACK-TO-PLAN Fix Cycle:
- ✅ ALL tests PASS + coverage ≥ 80% → proceed to Step 13
- ❌ Tests FAIL → re-invoke pipeline from STEP 6 (max 3 full cycles)
- If 3 cycles exhausted → `[ESCALATION]`, proceed to Step 13 with failure report

> ⛔ **[REPORT GATE]** — **Both files required:**
> 1. `reports/12-testkit-report.md` (Phase C)
> 2. `docs/output/ipa-docs/testreport/testreport-<MOD-ID>-<short-name>.md` (Phase D)
