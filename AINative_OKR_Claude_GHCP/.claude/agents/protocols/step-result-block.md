# Step Result Block — Handoff Contract

Every sub-agent MUST include a structured result block at the end of their response.
The Boss parses this block to extract status, artifacts, and metrics without reading the full report.

## Format

```yaml
<!-- STEP-RESULT
step: <step-number>
agent: <agent-name>
status: SUCCESS | FAILED
feature-id: <feature-id>
module-id: <mod-id>
artifacts:
  <key>: <file-path>
metrics:
  <key>: <value>
verdict: APPROVED | APPROVED_WITH_CONDITIONS | REJECTED | N/A
critical-issues: []
next-inputs:
  <key>: <file-path>
/STEP-RESULT -->
```

## Examples

### STEP 1 — okr.srs
```yaml
<!-- STEP-RESULT
step: 1
agent: okr.srs
status: SUCCESS
feature-id: 001-xxx
module-id: mod01
artifacts:
  srs: docs/output/ipa-docs/srs/srs-mod01-xxx.md
  report: docs/output/output_logs/001-xxx/reports/01-srs-report.md
metrics:
  fea-count: 12
  tbc-count: 3
verdict: N/A
critical-issues: []
next-inputs:
  srs-path: docs/output/ipa-docs/srs/srs-mod01-xxx.md
/STEP-RESULT -->
```

### STEP 5 — okr.reviewspec (with rejection)
```yaml
<!-- STEP-RESULT
step: 5
agent: okr.reviewspec
status: SUCCESS
feature-id: 001-xxx
module-id: mod01
artifacts:
  report: docs/output/output_logs/001-xxx/reports/05-review-spec-report.md
metrics:
  critical-count: 2
  minor-count: 3
verdict: REJECTED
critical-issues:
  - "Missing BR-KR-002 boundary validation in spec §5"
  - "SCR-mod01-02 wireframe missing target field"
next-inputs: {}
/STEP-RESULT -->
```

## Boss Parsing Rule

After each sub-agent returns, the Boss:
1. Extracts `<!-- STEP-RESULT ... /STEP-RESULT -->` block
2. Parses YAML content
3. **ARTIFACT VERIFICATION (mandatory before step-3):** For every path listed under `artifacts:`, use the `Glob` tool to confirm the file exists on disk.
   - If ANY artifact file is missing → treat the step as **FAILED**, do NOT update pipeline-context.yaml with status: COMPLETE, and re-invoke the sub-agent with an explicit instruction to write the missing file(s).
   - Log: `[ARTIFACT GATE] STEP N — missing: <path>. Re-invoking agent.`
4. Updates `pipeline-context.yaml` with artifacts and metrics — **only after step-3 passes**
5. Checks `verdict` for gate decisions — no need to read the full report file
6. If `critical-issues` is non-empty and verdict is REJECTED → invoke gate retry protocol

## Artifact Verification Table

Steps with primary artifacts that MUST be verified on disk:

| Step | Agent | Artifact key | Expected path pattern |
|------|-------|--------------|-----------------------|
| 1 | okr.srs | `srs` | `docs/output/ipa-docs/srs/srs-*.md` |
| 2 | okr.bd | `bd` | `docs/output/ipa-docs/bd/bd-*.md` |
| 3 | speckit.specify | `spec` | `docs/output/specs/*/spec.md` |
| 6 | speckit.plan | `plan` | `docs/output/specs/*/plan.md` |
| 8 | okr.dd | `dd` | `docs/output/ipa-docs/dd/dd-*.md` |
| 8b | okr.testkit | `testcases` | `docs/output/ipa-docs/testcase/testcase-*.md` |
| 9 | speckit.tasks | `tasks` | `docs/output/specs/*/tasks.md` |

Review steps (5, 7, 11) and the launch step (13) produce reports only — no primary artifact to verify beyond the report file itself.
