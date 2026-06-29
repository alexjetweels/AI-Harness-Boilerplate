# Pipeline Context File

The Boss maintains a running context file updated after each step.
Sub-agents read this file instead of re-reading large source files.

## Path

```
docs/output/output_logs/<feature-id>/pipeline-context.yaml
```

## Schema

```yaml
# --- Immutable (set at STEP 0) ---
feature-id: <feature-id>
module-id: <mod-id>              # e.g. mod01
module-keyword: <keyword>        # e.g. OKR
module-short-name: <short-name>  # e.g. xxx
mode: autonomous
language: Vietnamese

# --- Tech stack summary (extracted once from docs/technical_architecture.md) ---
tech-stack:
  backend: "NestJS 10, Node.js 22, TypeScript 5"
  frontend: "React 18.3, Vite 6.0"
  db: "PostgreSQL 17"
  cache: "Redis 7.4"
  css: "Bootstrap 5 (utility classes only)"

# --- Updated after each step ---
steps:
  step-0:
    status: COMPLETE
    pipeline-mode: UPDATE | CREATE
  step-1-srs:
    status: COMPLETE | SKIPPED | FAILED
    path: docs/output/ipa-docs/srs/srs-<mod-id>-<short-name>.md
    report: docs/output/output_logs/<feature-id>/reports/01-srs-report.md
    fea-count: <N>
    tbc-count: <N>
  step-2-bd:
    status: COMPLETE
    path: docs/output/ipa-docs/bd/bd-<mod-id>-<short-name>.md
    report: docs/output/output_logs/<feature-id>/reports/02-bd-report.md
    screen-count: <N>
  step-3-spec:
    status: COMPLETE
    path: specs/<feature-id>/spec.md
    report: docs/output/output_logs/<feature-id>/reports/03-specify-report.md
    branch: <branch-name>
  step-4-clarify:
    status: COMPLETE
    qa-path: docs/output/output_logs/<feature-id>/reports/04-clarify-qa.md
    report: docs/output/output_logs/<feature-id>/reports/04-clarify-report.md
    tbc-resolved: <N>
  step-5-review-spec:
    status: COMPLETE
    verdict: APPROVED | APPROVED_WITH_CONDITIONS | REJECTED
    report: docs/output/output_logs/<feature-id>/reports/05-review-spec-report.md
    retries: <N>
  step-6-plan:
    status: COMPLETE
    path: specs/<feature-id>/plan.md
    data-model: specs/<feature-id>/data-model.md
    contracts: specs/<feature-id>/contracts/
    report: docs/output/output_logs/<feature-id>/reports/06-plan-report.md
  step-7-review-plan:
    status: COMPLETE
    verdict: APPROVED
    report: docs/output/output_logs/<feature-id>/reports/07-review-plan-report.md
    retries: <N>
  step-8-dd:
    status: COMPLETE
    path: docs/output/ipa-docs/dd/dd-<mod-id>-<short-name>.md
    report: docs/output/output_logs/<feature-id>/reports/08-dd-report.md
  step-8b-testcases:
    status: COMPLETE
    path: docs/output/ipa-docs/testcase/testcase-<mod-id>-<short-name>.md
    report: docs/output/output_logs/<feature-id>/reports/08b-testcases-report.md
  step-9-tasks:
    status: COMPLETE
    path: specs/<feature-id>/tasks.md
    report: docs/output/output_logs/<feature-id>/reports/09-tasks-report.md
  step-10-implement:
    status: COMPLETE
    report: docs/output/output_logs/<feature-id>/reports/10-implement-report.md
    retries: <N>
  step-11-review-code:
    status: COMPLETE
    verdict: APPROVED
    report: docs/output/output_logs/<feature-id>/reports/11-review-code-report.md
    retries: <N>
  step-12-testkit:
    status: COMPLETE
    verdict: PASS | FAIL
    report: docs/output/output_logs/<feature-id>/reports/12-testkit-report.md
    ipa-report: docs/output/ipa-docs/testreport/testreport-<mod-id>-<short-name>.md
    back-to-plan-cycles: <N>
  step-13-launch:
    status: COMPLETE
    fe-url: "http://localhost:5173"
    be-url: "http://localhost:8081"
    report: docs/output/output_logs/<feature-id>/reports/13-launch-report.md
```

## Boss Update Rules

1. **After STEP 0**: Create file with immutable section + tech-stack (read from `docs/technical_architecture.md` once)
2. **After each step**: Parse the sub-agent's `<!-- STEP-RESULT -->` block and update the corresponding `steps.step-N` section
3. **Before delegating**: Sub-agents receive the pipeline-context path in `$ARGUMENTS` and can read it for all prior step outputs

## Sub-Agent Read Rules

Sub-agents SHOULD read `pipeline-context.yaml` at startup to discover:
- `feature-id`, `module-id`, `module-keyword` (no need to re-detect)
- Artifact paths from prior steps (no need to guess)
- Tech stack (no need to re-read `docs/technical_architecture.md` for basics)
