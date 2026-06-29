# Steps 8–9: Detail Design Phase

> Boss MUST read this file before executing Steps 8–9.
> Protocols referenced: `protocols/auto-resolve-protocol.md`, `protocols/report-gate-protocol.md`

---

## [PARALLEL GROUP A] — Steps 8 + 9 (Dispatch Simultaneously After Step 7)

> Boss MUST dispatch STEP 8 and STEP 9 as a **single multi-agent call** immediately after Step 7 gate PASSES.
> Do NOT wait for Step 8 to finish before starting Step 9, or vice versa.
> See `protocols/parallel-execution-protocol.md` (inline in boss prompt) for rules.

---

## STEP 8 — DD Generation (Internal Design)

| Key | Value |
|-----|-------|
| Agent | `okr.dd` |
| Model | `gpt-5-3-codex` |
| Input | BD, SRS, spec, plan, technical architecture |
| Output | `docs/output/ipa-docs/dd/dd-<MOD-ID>-<short-name>.md` |
| Report | `reports/08-dd-report.md` |
| Gate | REPORT HARD GATE + Auto-Resolve |
| On fail | Log error, continue with empty DD stub |
| Parallel group | GROUP A — runs concurrently with STEP 9 |

**Delegation `$ARGUMENTS`:**
```yaml
feature-id: <feature-id>
module-id: <mod-id>
module-keyword: <keyword>
pipeline-context: docs/output/output_logs/<feature-id>/pipeline-context.yaml
```

**After completion:** Auto-resolve any `[NEEDS CLARIFICATION]` markers in DD.

> ⛔ **[REPORT GATE]** per `protocols/report-gate-protocol.md`

---

## STEP 9 — Task Generation

| Key | Value |
|-----|-------|
| Agent | `speckit.tasks` |
| Model | `gpt-5.4` |
| Input | `specs/<feature-id>/plan.md`, `specs/<feature-id>/spec.md`, `specs/<feature-id>/data-model.md` |
| Output | `specs/<feature-id>/tasks.md` |
| Report | `reports/09-tasks-report.md` |
| Gate | REPORT HARD GATE + Auto-Resolve |
| Parallel group | GROUP A — runs concurrently with STEP 8 |

**Delegation `$ARGUMENTS`:**
```yaml
feature-id: <feature-id>
pipeline-context: docs/output/output_logs/<feature-id>/pipeline-context.yaml
```

**After completion:** Auto-resolve any `[NEEDS CLARIFICATION]` markers in tasks.md.

> ⛔ **[REPORT GATE]** per `protocols/report-gate-protocol.md`

---

## [PARALLEL-SYNC] After Steps 8 + 9

> Boss writes a `[PARALLEL-SYNC]` log entry once BOTH Step 8 and Step 9 have returned
> and passed their individual REPORT HARD GATEs. Only then dispatch Step 8b.

---

## STEP 8b — Test Case Generation (Independent QA)

> **Prerequisite:** Step 8 (DD file) AND Step 9 (tasks.md) must both be complete.

| Key | Value |
|-----|-------|
| Agent | `okr.testkit` |
| Model | `claude-sonnet-4-6` |
| Mode | `gen-testcases` |
| Input | `docs/output/ipa-docs/srs/srs-<MOD-ID>-<short-name>.md`, `docs/output/ipa-docs/bd/bd-<MOD-ID>-<short-name>.md`, `docs/output/ipa-docs/dd/dd-<MOD-ID>-<short-name>.md`, `spec.md`, `plan.md` |
| Output | `docs/output/ipa-docs/testcase/testcase-<MOD-ID>-<short-name>.md` |
| Report | `reports/08b-testcases-report.md` |
| Gate | REPORT HARD GATE + Boss Validation |

**Delegation `$ARGUMENTS`:**
```
gen-testcases <feature-id>
```

Also pass `pipeline-context` path so testkit can discover all input document paths.

**Boss Validation (after completion):**
- Every FEA-xxx in SRS has ≥ 1 test case
- Every BR-xxx has ≥ 1 normal + 1 abnormal + 1 boundary test case
- Every SCR-MOD-xx-nn in BD has ≥ 1 layout + 1 functional E2E test case
- Test case count > 0 for each category (UT, AT, E2E, IT)

> ⛔ **[REPORT GATE]** per `protocols/report-gate-protocol.md`
