# Boss Log Entry Formats

All entries are written to `docs/output/output_logs/<feature-id>/00-boss.log.md`.

## [START] Pipeline Initialized

```markdown
## [START] Pipeline Initialized

- **Timestamp:** <real timestamp>
- **Mode:** BUILT-IN AUTONOMOUS (no pauses, no human gates)
- **Feature:** <feature description>
- **Feature ID:** <feature-id>
- **Auto-resolve policy:** All [NEEDS CLARIFICATION] items resolved with optimal assumptions
- **Retry policy:** REJECTED gates trigger automatic fix-and-retry loops (max 5 per gate)
```

## [PROCESSING] STEP N — Before Delegation

```markdown
## [PROCESSING] STEP N — <agent-name>

- **Timestamp:** <real timestamp>
- **Delegating to:** `<agent-name>`
- **Model:** `<model>`
- **Purpose:** <purpose>
- **Inputs:** <key inputs>
```

## [PROCESSING] STEP N — COMPLETE

```markdown
## [PROCESSING] STEP N — COMPLETE

- **Timestamp:** <real timestamp>
- **Status:** ✅ SUCCESS / ❌ FAILED
- **Artifacts:** <list paths>
- **Key metrics:** <step-specific metrics>
```

## [AUTO-RESOLVE] Entry

```markdown
## [AUTO-RESOLVE] STEP N — <N> items resolved

- **Timestamp:** <real timestamp>
- **Items resolved:** <count>
- **Confidence breakdown:** High: X, Med: Y, Low: Z
- **Details:** See `reports/<NN>-<phase>-report.md` § AUTO-RESOLVED Assumptions
- **Low-confidence items for user review:** <list IDs or "None">
```

## [ISSUE] Gate Rejection

```markdown
## [ISSUE] STEP N — REJECTED (Retry <R>/5)

- **Timestamp:** <real timestamp>
- **Gate:** <step name>
- **Verdict:** REJECTED
- **Retry:** <R> of 5
- **CRITICAL Issues:** <list>
- **Fix Action:** Invoking `<fix-agent>` to resolve
- **Next:** Re-invoking `<review-agent>` after fix
```

## [REPORT GATE] Entry

```markdown
## [REPORT GATE] STEP N — ✅ PASSED / ⚠️ GENERATED LATE

- **Timestamp:** <real timestamp>
- **Report path:** <path>
- **Status:** EXISTS / GENERATED NOW
- **Sections verified:** Summary ✅ | Artifacts ✅ | AUTO-RESOLVED ✅ | NEEDS CLARIFICATION ✅ | Issues & Retries ✅ | Next Step ✅
- **TBC items auto-resolved:** <N>
- **Gate result:** PASSED
```

## [ESCALATION] Max Retries Exceeded

```markdown
## [ESCALATION] STEP N — Max retries exceeded

- **Timestamp:** <real timestamp>
- **Gate:** <step name>
- **Retries attempted:** 5
- **Final verdict:** ESCALATED
- **Unresolved CRITICAL issues:** <list>
- **Decision:** Pipeline continues with limitations.
- **Risk level:** <High/Med>
```

## [PARALLEL-SYNC] Parallel Group Complete

```markdown
## [PARALLEL-SYNC] <group-name> — All agents returned

- **Timestamp:** <real timestamp>
- **Group:** <e.g., "GROUP A: Steps 8 + 9">
- **Agents:** <list of agent names>
- **Status:** ALL-PASSED | PARTIAL | ALL-FAILED
- **Step 8 verdict:** ✅ PASSED / ❌ FAILED
- **Step 9 verdict:** ✅ PASSED / ❌ FAILED
- **Next:** <next step to dispatch>
```

## [BACK-TO-PLAN] Entry (Step 12 only)

```markdown
## [BACK-TO-PLAN] STEP 12 — Test Failures (Fix Cycle <N>/3)

- **Timestamp:** <real timestamp>
- **Fix Cycle:** <N> of 3
- **Failed Tests:** <count>
- **Failed Test Details:**
  | TC-ID | Test Name | Failure Reason | Design Reference |
  |-------|-----------|----------------|------------------|
- **Action:** Re-invoking pipeline from STEP 6 (plan) with failure context
```

## [STEP 0] Existing Spec Detection

```markdown
## [STEP 0] Existing Spec Detection

- **Timestamp:** <real timestamp>
- **Feature argument:** <$ARGUMENTS>
- **Module keyword extracted:** <keyword>
- **docs/output/specs/ folders scanned:** <list>
- **Match found:** YES — `docs/output/specs/<feature-id>/` | NO
- **Pipeline mode:** UPDATE | CREATE
- **Resolved feature-id:** `<feature-id>`
```

## [END] Pipeline Complete

```markdown
## [END] Pipeline Complete

- **Timestamp:** <real timestamp>
- **Overall verdict:** ✅ COMPLETE / ⚠️ PARTIAL COMPLETE
- **Total steps executed:** <N>
- **Total gate retries:** <N>
- **Total assumptions made:** <N> (High: X, Med: Y, Low: Z)
- **Escalated gates:** <list or "None">
- **Browser URL:** <final URL opened>
```
