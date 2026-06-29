# Pipeline Completion Report Template

Use this template when all steps complete (with or without escalations).

```markdown
## ✅ Pipeline Complete (Autonomous Mode) — <feature-name>

**Feature Branch**: <branch>
**Date Completed**: <YYYY-MM-DD>
**Mode**: Built-in Autonomous (no human pauses)

| # | Step | Agent | Model | Status | Retries | Assumptions |
|---|------|-------|-------|--------|---------|-------------|
| 1 | SRS Generation | okr.srs | gpt-5.4 | ✅ | 0 | N |
| 2 | BD Generation (External Design) | okr.bd | gpt-5.4 | ✅ | 0 | N |
| 3 | Spec Creation | speckit.specify | gpt-5.4 | ✅ | 0 | N |
| 4 | Spec Clarification | speckit.clarify | gpt-5.4 | ✅ | 0 | N |
| 5 | Thorough Spec Review | okr.reviewspec | claude-sonnet-4-6 | ✅ | R | - |
| 6 | Implementation Planning | speckit.plan | gpt-5-3-codex | ✅ | 0 | N |
| 7 | Plan Conformance Review | okr.reviewplan | claude-sonnet-4-6 | ✅ | R | - |
| 8 | DD Generation (Internal Design) | okr.dd | gpt-5-3-codex | ✅ | 0 | N |
| 8b | Test Case Generation | okr.testkit | claude-sonnet-4-6 | ✅ | 0 | N |
| 9 | Task Generation | speckit.tasks | gpt-5.4 | ✅ | 0 | N |
| 10 | Implementation + Build & Fix | speckit.implement | gpt-5-3-codex | ✅ | R | N |
| 11 | Code Review | okr.reviewcode | claude-sonnet-4-6 | ✅ | R | - |
| 12 | Final QA Audit | okr.testkit | claude-sonnet-4-6 | ✅ | R | - |
| 13 | Launch | Boss (direct) | claude-sonnet-4-6 | ✅ | R | - |

**Total auto-resolved assumptions:** N (High: X, Med: Y, Low: Z)
**Total gate retries:** N
**Escalated gates:** <list or "None">

> ⚠  Items requiring user review (Low-confidence assumptions):
> - <TBC-ID>: <question> ← Assumed: <answer>
> - (or "None — all assumptions were High/Med confidence")

**Artifacts**:
- SRS: `docs/output/ipa-docs/srs/srs-<MOD-ID>-<module-short-name>.md`
- BD: `docs/output/ipa-docs/bd/bd-<MOD-ID>-<module-short-name>.md`
- Spec: `specs/<feature-id>/spec.md`
- Clarification Q&A: `docs/output/output_logs/<feature-id>/reports/04-clarify-qa.md`
- Plan: `specs/<feature-id>/plan.md`
- DD: `docs/output/ipa-docs/dd/dd-<MOD-ID>-<module-short-name>.md`
- Tasks: `specs/<feature-id>/tasks.md`
- Implementation: `src/modules/<module>/`
- Verified: Feature accessible on screen ✅

**Execution Logs & Reports**: `docs/output/output_logs/<feature-id>/`

| # | Report File |
|---|-------------|
| 0 | `00-boss.log.md` |
| 1 | `reports/01-srs-report.md` |
| 2 | `reports/02-bd-report.md` |
| 3 | `reports/03-specify-report.md` |
| 4 | `reports/04-clarify-report.md` |
| 5 | `reports/05-review-spec-report.md` |
| 6 | `reports/06-plan-report.md` |
| 7 | `reports/07-review-plan-report.md` |
| 8 | `reports/08-dd-report.md` |
| 8b | `reports/08b-testcases-report.md` |
| 9 | `reports/09-tasks-report.md` |
| 10 | `reports/10-implement-report.md` |
| 11 | `reports/11-review-code-report.md` |
| 12 | `reports/12-testkit-report.md` + `docs/output/ipa-docs/testreport/testreport-<MOD-ID>-*.md` |
| 13 | `reports/13-launch-report.md` |
```
