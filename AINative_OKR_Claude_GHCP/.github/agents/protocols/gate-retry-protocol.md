# Gate Retry Protocol (No-Halt Mode)

When any review gate returns **REJECTED**, the pipeline does NOT stop.

## Gate Retry Loop

```
REJECTED verdict received
    │
    ├─ Extract CRITICAL issues list from review report
    ├─ Write [ISSUE] entry in boss log
    ├─ Increment retry counter for this gate
    │
    ├─ If retry counter ≤ 5:
    │      Invoke fix agent with CRITICAL issues list
    │      Re-invoke review agent
    │      Evaluate new verdict → repeat if still REJECTED
    │
    └─ If retry counter > 5:
           Write [ESCALATION] entry in boss log
           Mark step as "ESCALATED — Partial Pass"
           Continue pipeline with known limitations documented
```

## Fix Agent Selection per Gate

| Gate Step | Review Agent | Fix Agent | Fix Instruction |
|-----------|-------------|-----------|-----------------|
| Step 5  | `okr.reviewspec` | `speckit.specify` | "Fix CRITICAL spec issues: <list>. Re-generate affected sections of spec.md." |
| Step 7  | `okr.reviewplan` | `speckit.plan` | "Fix CRITICAL plan conformance issues: <list>. Update plan.md." |
| Step 11 | `okr.reviewcode` | `speckit.implement` | "Fix CRITICAL code review issues: <list>. Apply minimal targeted fixes." |
| Step 12 | `okr.testkit` | `speckit.implement` | "Fix CRITICAL test failures tracing to SRS/BD/DD: <failed test list>." |

## BACK-TO-PLAN Fix Cycle (Step 12 only)

When Step 12 tests FAIL, unlike other gates, this triggers a **full fix cycle** from STEP 6:

1. Extract ALL failed test cases with design document references
2. Write `[BACK-TO-PLAN]` entry in boss log
3. Re-invoke pipeline from STEP 6 → 7 → 8 → 8b → 9 → 10 → 11 → 12
4. Max **3 full cycles**. After 3 cycles: write `[ESCALATION]`, proceed to Step 13 anyway.
