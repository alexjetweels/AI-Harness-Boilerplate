# Report Hard Gate Protocol

## ⛔ MANDATORY BEFORE NEXT STEP

After each step completes, the boss MUST enforce this gate before proceeding:

```
STEP N completes
    │
    ▼
[GATE A] CHECK: Are all primary artifact files physically present on disk?
    │            Use Glob tool for each path listed in artifacts: of STEP-RESULT block.
    │
    ├─ ANY MISSING → BLOCKED. Do NOT mark step COMPLETE.
    │                Re-invoke the sub-agent with explicit instruction:
    │                  "File <path> was not written. Re-generate and write it now."
    │                Write boss log: [ARTIFACT GATE] STEP N — missing: <path>. Re-invoking.
    │                (Counts against gate-retry-protocol max retries)
    │
    └─ ALL PRESENT → GATE A PASSED
                        │
                        ▼
[GATE B] CHECK: Does the phase report file EXIST?
    │
    ├─ NO → BLOCKED. Generate the report NOW using data already produced.
    │        Write boss log: [REPORT GATE] STEP N — report generated (late).
    │
    └─ YES → CHECK: Does report contain ALL required sections?
                │
                ├─ NO → ADD missing section inline. Re-write file.
                │        Write boss log: [REPORT GATE] STEP N — patched missing section: <name>.
                │
                └─ YES → CHECK: Any unresolved [NEEDS CLARIFICATION] markers?
                            │
                            ├─ YES → Auto-resolve every item. Patch report.
                            │        Write boss log: [REPORT GATE] STEP N — auto-resolved N TBC items.
                            │
                            └─ NO → ✅ BOTH GATES PASSED → Advance to STEP N+1
```

> **Rule:** `pipeline-context.yaml` step status may only be set to `COMPLETE` after GATE A and GATE B both pass. Setting it earlier — based solely on the sub-agent's STEP-RESULT claim — is forbidden.

## Required Report Sections (all steps)

1. `## Summary` — brief phase outcome
2. `## Artifacts Produced` — list of all files written (with paths)
3. `## [AUTO-RESOLVED] Assumptions` — auto-resolved clarifications
4. `## [NEEDS CLARIFICATION] Items` — remaining unresolved items (should be empty in built-in mode)
5. `## Issues & Retries` — record of rejected verdicts and retry attempts
6. `## Next Step` — what step follows and what inputs it will receive

## Step-Specific Additional Sections

| Step | Additional Required Section |
|------|-----------------------------|
| STEP 4 | `## QA Summary` — full table of questions + auto-resolved answers |
| STEP 10 | `## Test Results` — pass/fail table per test class, Istanbul/c8 coverage % | `## Screen Verification` — per-screen: ID, HTTP status, render OK/FAIL |
| STEP 13 | `## Launch Status` — FE/BE startup, DB seed count, screen accessibility |

---

## ⛔ Implementation Gate (Step 10 — CANNOT be bypassed or auto-resolved)

Before dispatching `speckit.implement` (Step 10), boss MUST read `pipeline-context.yaml` and verify:

```
REQUIRED statuses in pipeline-context.yaml:
  step-6-plan.status    == "COMPLETE"   → plan.md, data-model.md, contracts/ exist
  step-8-dd.status      == "COMPLETE"   → DD document exists
  step-9-tasks.status   == "COMPLETE"   → tasks.md exists
  step-8b-testcases.status == "COMPLETE" → testcase document exists

REQUIRED files on disk (verify with Glob/Read):
  docs/output/specs/<feature-id>/plan.md
  docs/output/specs/<feature-id>/data-model.md
  docs/output/specs/<feature-id>/tasks.md
  docs/output/ipa-docs/dd/dd-<mod-id>-<short-name>.md
  docs/output/ipa-docs/testcase/testcase-<mod-id>-<short-name>.md
  docs/output/ipa-docs/srs/srs-<mod-id>-<short-name>.md
  docs/output/ipa-docs/bd/bd-<mod-id>-<short-name>.md
  docs/output/specs/<feature-id>/spec.md
```

**On failure (any check fails):**
1. Log `[IMPLEMENTATION GATE BLOCKED]` in boss log with list of missing items
2. **Do NOT dispatch Step 10** — no exceptions
3. Identify the earliest incomplete step in `pipeline-context.yaml`
4. Re-execute from that step forward
5. Re-run this gate after remediation

**Why this gate cannot be auto-resolved:**
Missing design documents mean the implementation has no spec to be traced to. Code written without SRS/BD/Plan/DD cannot be reviewed for correctness — it is untraceable and unverifiable. The entire purpose of the pipeline is this traceability chain. Auto-resolving this gate would mean shipping code with no design rationale, which defeats the pipeline entirely.

> This gate applies even in `mode: autonomous`. "Autonomous" means no human pauses — it does NOT mean skipping required pipeline steps.
