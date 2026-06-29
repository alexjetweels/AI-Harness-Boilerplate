# Steps 1–4: Design Phase

> Boss MUST read this file before executing Steps 1–4.
> Protocols referenced: `protocols/auto-resolve-protocol.md`, `protocols/report-gate-protocol.md`

---

## STEP 0 — Existing Spec Detection (MANDATORY BEFORE ALL STEPS)

**Agent**: Boss (self)

Scan `specs/` directory for existing feature/module match before creating anything.

```
Run: Get-ChildItem specs/ -Directory | Select-Object -ExpandProperty Name
```

1. Extract module keyword from `$ARGUMENTS` (e.g., "MOD-01", "Objective ")
2. Look for matching folder in `specs/`
3. If match found:
   - Set `<feature-id>` = existing folder name
   - Set pipeline mode = **UPDATE** (do NOT create new branch/folder)
   - Propagate `<feature-id>` to ALL subsequent steps
4. If no match:
   - Set pipeline mode = **CREATE**

**Update Mode Rules:**
- **PROHIBITED:** Creating a new numbered folder when one already exists for this module.
- SRS/BD re-generation (Steps 1 & 2): Run normally — overwrite existing files.
- Spec update (Step 3): Invoke `speckit.specify` with: *"Update existing spec at `specs/<feature-id>/spec.md` in-place. DO NOT create new branch or folder."*

> Write `[STEP 0]` entry in boss log per `protocols/log-formats.md`.

---

## STEP 1 — SRS Generation

| Key | Value |
|-----|-------|
| Agent | `okr.srs` |
| Model | `gpt-5.4` |
| Input | Module keyword from `$ARGUMENTS` |
| Output | `docs/output/ipa-docs/srs/srs-<MOD-ID>-<short-name>.md` |
| Report | `reports/01-srs-report.md` |
| Gate | REPORT HARD GATE |
| On fail | Log error, continue with empty SRS stub |

**Delegation `$ARGUMENTS`:**
```yaml
feature-id: <feature-id>
module-id: <mod-id>
module-keyword: <keyword>
pipeline-context: docs/output/output_logs/<feature-id>/pipeline-context.yaml
```

**After completion:** Parse `<!-- STEP-RESULT -->` block, update `pipeline-context.yaml`.

> ⛔ **[REPORT GATE]** per `protocols/report-gate-protocol.md`

---

## STEP 2 — BD Generation (External Design)

| Key | Value |
|-----|-------|
| Agent | `okr.bd` |
| Model | `gpt-5.4` |
| Input | `docs/output/ipa-docs/srs/srs-<MOD-ID>-<short-name>.md`, `docs/output/srs-systems/srs-overview-system.md`, `docs/technical_architecture.md` |
| Output | `docs/output/ipa-docs/bd/bd-<MOD-ID>-<short-name>.md` |
| Report | `reports/02-bd-report.md` |
| Gate | REPORT HARD GATE + Auto-Resolve |
| On fail | Log error, continue with empty BD stub |

**Delegation `$ARGUMENTS`:**
```yaml
feature-id: <feature-id>
module-id: <mod-id>
module-keyword: <keyword>
pipeline-context: docs/output/output_logs/<feature-id>/pipeline-context.yaml
```

**After completion:** Auto-resolve any `[NEEDS CLARIFICATION]` markers in BD per `protocols/auto-resolve-protocol.md`.

> ⛔ **[REPORT GATE]** per `protocols/report-gate-protocol.md`

---

## STEP 3 — Spec Creation

| Key | Value |
|-----|-------|
| Agent | `speckit.specify` |
| Model | `gpt-5.4` |
| Input | Feature description, `docs/output/ipa-docs/srs/srs-<MOD-ID>-<short-name>.md`, `docs/output/ipa-docs/bd/bd-<MOD-ID>-<short-name>.md` |
| Output | `specs/<feature-id>/spec.md` |
| Report | `reports/03-specify-report.md` |
| Gate | REPORT HARD GATE + Post-Check Auto-Resolve |

**Delegation `$ARGUMENTS`:**
```yaml
feature-id: <feature-id>
module-id: <mod-id>
srs-path: <from pipeline-context>
bd-path: <from pipeline-context>
pipeline-context: docs/output/output_logs/<feature-id>/pipeline-context.yaml
```

**POST-CHECK (boss does after agent returns):**
1. Read generated spec file
2. Collect all `[NEEDS CLARIFICATION]` markers
3. For each: apply Auto-Resolve Protocol — replace marker in spec
4. Write `[AUTO-RESOLVE]` entry in boss log

> ⛔ **[REPORT GATE]** per `protocols/report-gate-protocol.md`

---

## STEP 4 — Consolidated Spec Clarification (Autonomous Mode)

| Key | Value |
|-----|-------|
| Agent | `speckit.clarify` |
| Model | `gpt-5.4` |
| Input | `specs/<feature-id>/spec.md` |
| Output | Updated spec + `reports/04-clarify-qa.md` |
| Report | `reports/04-clarify-report.md` |
| Gate | REPORT HARD GATE (+ QA Summary section required) |

**Autonomous behavior (NO PAUSE):**
1. `speckit.clarify` identifies ambiguities → produces QA list
2. Boss applies Auto-Resolve Protocol to every question
3. Boss encodes all answers back into spec
4. Boss writes QA list with answers to `reports/04-clarify-qa.md`
5. Confirms no `[NEEDS CLARIFICATION]` markers remain

**Output format for `04-clarify-qa.md`:**
```markdown
# Clarification Q&A — Auto-Resolved

| # | ID | Question | Auto-Answer | Rationale | Confidence |
|---|----|----------|-------------|-----------|------------|
| 1 | TBC-01 | ... | ... | ... | High |

## Summary
- Total questions: N
- Auto-resolved: N (High: X, Med: Y, Low: Z)
- Pending user confirmation: 0 (pipeline continues)
```

> ⛔ **[REPORT GATE]** per `protocols/report-gate-protocol.md`
