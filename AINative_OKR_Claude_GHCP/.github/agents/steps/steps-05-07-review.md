# Steps 5–7: Review Phase

> Boss MUST read this file before executing Steps 5–7.
> Protocols referenced: `protocols/gate-retry-protocol.md`, `protocols/report-gate-protocol.md`

---

## STEP 5 — Thorough Spec Review (Auto-Retry)

| Key | Value |
|-----|-------|
| Agent | `okr.reviewspec` |
| Model | `claude-sonnet-4-6` |
| Input | `spec.md`, `docs/output/ipa-docs/srs/srs-<MOD-ID>-<short-name>.md`, `constitution.md` |
| Report | `reports/05-review-spec-report.md` |
| Gate | REVIEW GATE (Auto-Retry) + REPORT HARD GATE |
| Fix agent | `speckit.specify` |
| Max retries | 5 |

**Gate logic:**
- ✅/⚠️ → proceed to Step 6
- ❌ REJECTED → invoke `speckit.specify` to fix CRITICAL issues → re-invoke `okr.reviewspec` → repeat until pass or retry > 5
- Escalation after 5 retries → continue to Step 6

> ⛔ **[REPORT GATE]** per `protocols/report-gate-protocol.md`

---

## STEP 6 — Implementation Planning

| Key | Value |
|-----|-------|
| Agent | `speckit.plan` |
| Model | `gpt-5-3-codex` |
| Input | `spec.md`, `constitution.md`, `docs/technical_architecture.md` |
| Output | `plan.md`, `data-model.md`, `contracts/` |
| Report | `reports/06-plan-report.md` |
| Gate | REPORT HARD GATE + Auto-Resolve |

**Delegation `$ARGUMENTS`:**
```yaml
feature-id: <feature-id>
module-id: <mod-id>
pipeline-context: docs/output/output_logs/<feature-id>/pipeline-context.yaml
```

**After completion:** Auto-resolve any `[NEEDS CLARIFICATION]` markers in plan artifacts.

> ⛔ **[REPORT GATE]** per `protocols/report-gate-protocol.md`

---

## STEP 7 — Plan Conformance Review (Auto-Retry)

| Key | Value |
|-----|-------|
| Agent | `okr.reviewplan` |
| Model | `claude-sonnet-4-6` |
| Input | `plan.md`, `spec.md`, `data-model.md`, `docs/technical_architecture.md` |
| Report | `reports/07-review-plan-report.md` |
| Gate | REVIEW GATE (Auto-Retry) + REPORT HARD GATE |
| Fix agent | `speckit.plan` |
| Max retries | 5 |

**Gate logic:**
- ✅/⚠️ → proceed to Step 8
- ❌ REJECTED → invoke `speckit.plan` to fix → re-invoke `okr.reviewplan` → repeat
- Escalation after 5 retries → continue to Step 8

> ⛔ **[REPORT GATE]** per `protocols/report-gate-protocol.md`
