# Flow Agent — Pipeline

> Describes the operational flow of the multi-agent system for the Feature Development Pipeline.

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                  okr.bossbuiltin (Boss)                         │
│               claude-sonnet-4-6 — Orchestrator                  │
│                                                                 │
│  📋 protocols/    📝 steps/    📄 templates/    📊 logs/       │
└──────────┬──────────────────────────────────────────────────────┘
           │ delegates to 12 specialist sub-agents
           ▼
┌──────────────────────────────────────────────────────────────────┐
│  okr.srs                │  okr.bd                │  okr.dd       │
│  speckit.specify        │  speckit.clarify       │  speckit.plan │
│  speckit.tasks          │  speckit.implement     │               │
│  okr.reviewspec         │  okr.reviewplan        │               │
│  okr.reviewcode         │  okr.testkit           │               │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. Pipeline Flow — 5 Phases, 16 Steps

```
USER INPUT ($ARGUMENTS: feature description)
    │
    ▼
╔══════════════════════════════════════════════════════════════════╗
║  PHASE 1: DESIGN (Steps 0–4)                                   ║
║  📄 steps/steps-01-04-design.md                                 ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  STEP 0 ─ Boss (self)                                           ║
║  │  Detect existing spec in specs/ directory                    ║
║  │  → mode = CREATE or UPDATE                                   ║
║  ▼                                                               ║
║  STEP 1 ─ okr.srs (gpt-5.4)                                    ║
║  │  Input:  srs-systems/ (overview + module detail + wireframe) ║
║  │  Output: docs/output/ipa-docs/srs/srs-<MOD>-<name>.md            ║
║  │  Report: 01-srs-report.md                                   ║
║  ▼                                                               ║
║  STEP 2 ─ okr.bd (gpt-5.4)                                     ║
║  │  Input:  SRS + system overview + technical architecture      ║
║  │  Output: docs/output/ipa-docs/bd/bd-<MOD>-<name>.md              ║
║  │  Report: 02-bd-report.md                                    ║
║  │  🔧 Auto-Resolve: [NEEDS CLARIFICATION] markers             ║
║  ▼                                                               ║
║  STEP 3 ─ speckit.specify (gpt-5.4)                            ║
║  │  Input:  Feature desc + SRS + BD                             ║
║  │  Output: specs/<feature-id>/spec.md                          ║
║  │  Report: 03-specify-report.md                                ║
║  │  🔧 Post-check: Boss auto-resolves [NEEDS CLARIFICATION]    ║
║  ▼                                                               ║
║  STEP 4 ─ speckit.clarify (gpt-5.4)                            ║
║     Input:  spec.md                                              ║
║     Output: spec.md (updated) + 04-clarify-qa.md               ║
║     Report: 04-clarify-report.md                                ║
║     ⚠️  NO HUMAN PAUSE — auto-resolve all questions             ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    │
    ▼
╔══════════════════════════════════════════════════════════════════╗
║  PHASE 2: REVIEW (Steps 5–7)                                    ║
║  📄 steps/steps-05-07-review.md                                  ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  STEP 5 ─ okr.reviewspec (claude-sonnet-4-6)   🔄 GATE         ║
║  │  Input:  spec.md + SRS + constitution                        ║
║  │  Verdict: ✅ APPROVED / ⚠️ CONDITIONS / ❌ REJECTED          ║
║  │  Report: 05-review-spec-report.md                            ║
║  │                                                               ║
║  │  ❌ REJECTED → speckit.specify fixes → re-review (max 5x)   ║
║  │  ✅/⚠️ → continue                                            ║
║  ▼                                                               ║
║  STEP 6 ─ speckit.plan (gpt-5-3-codex)                         ║
║  │  Input:  spec.md + constitution + docs/technical_architecture.md     ║
║  │  Output: plan.md + data-model.md + contracts/ + research.md  ║
║  │  Report: 06-plan-report.md                                   ║
║  │  🔧 Auto-Resolve: [NEEDS CLARIFICATION] in plan artifacts   ║
║  ▼                                                               ║

║  STEP 7 ─ okr.reviewplan (claude-sonnet-4-6)   🔄 GATE         ║
║     Input:  plan.md + spec.md + data-model.md + tech arch       ║
║     Verdict: ✅ APPROVED / ⚠️ CONDITIONS / ❌ REJECTED          ║
║     Report: 07-review-plan-report.md                            ║
║                                                                  ║
║     ❌ REJECTED → speckit.plan fixes → re-review (max 5x)      ║
║     ✅/⚠️ → continue                                            ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    │
    ▼
╔══════════════════════════════════════════════════════════════════╗
║  PHASE 3: DETAIL DESIGN (Steps 8–9)                             ║
║  📄 steps/steps-08-09-detail.md                                  ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  STEP 8 ─ okr.dd (gpt-5-3-codex)                               ║
║  │  Input:  BD + SRS + spec + plan + tech arch                  ║
║  │  Output: docs/output/ipa-docs/dd/dd-<MOD>-<name>.md              ║
║  │  Report: 08-dd-report.md                                     ║
║  │  🔧 Auto-Resolve: [NEEDS CLARIFICATION] in DD               ║
║  ▼                                                               ║
║  STEP 8b ─ okr.testkit (claude-sonnet-4-6)                      ║
║  │  Mode:   gen-testcases                                       ║
║  │  Input:  SRS + BD + DD + spec + plan                         ║
║  │  Output: docs/output/ipa-docs/testcase/testcase-<MOD>-<name>.md  ║
║  │  Report: 08b-testcases-report.md                             ║
║  │  Boss validates: FEA/BR/SCR coverage ≥ 1 TC each            ║
║  ▼                                                               ║
║  STEP 9 ─ speckit.tasks (gpt-5.4)                              ║
║     Input:  plan.md + spec.md + data-model.md                   ║
║     Output: specs/<feature-id>/tasks.md                         ║
║     Report: 09-tasks-report.md                                  ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    │
    ▼
╔══════════════════════════════════════════════════════════════════╗
║  PHASE 4: IMPLEMENTATION & QA (Steps 10–12)                     ║
║  📄 steps/steps-10-12-implement.md                               ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  STEP 10 ─ speckit.implement (gpt-5-3-codex)        🔄 GATE   ║
║  │  Input:  tasks.md + plan.md + data-model.md + contracts/     ║
║  │  Output: src/modules/<module>/ (source code)                 ║
║  │  Phase 1: implement all tasks                                 ║
║  │  Phase 2: build & fix all errors                              ║
║  │  Report: 10-implement-report.md (incl. Screen Verification) ║
║  │  ⚡ REAL EXECUTION — npm build, docker up, npm start          ║
║  │                                                               ║
║  │  ❌ Build fails → auto-fix → re-build (max 5x)              ║
║  │  ✅ Build success + app starts → continue                    ║
║  ▼                                                               ║
║  STEP 11 ─ okr.reviewcode (claude-sonnet-4-6)  🔄 GATE         ║
║  │  Input:  source code + spec + tasks + constitution           ║
║  │  Check:  code quality + DB data usage (no mock data)         ║
║  │  Verdict: ✅ APPROVED / ⚠️ CONDITIONS / ❌ REJECTED          ║
║  │  Report: 11-review-code-report.md                            ║
║  │                                                               ║
║  │  ❌ REJECTED → speckit.implement fixes → re-review (max 5x) ║
║  │  ✅/⚠️ → continue                                            ║
║  ▼                                                               ║
║  STEP 12 ─ okr.testkit (claude-sonnet-4-6)     🔄 GATE         ║
║     Mode:   run-tests                                            ║
║     Input:  testcases + running app                              ║
║     Output: testreport-<MOD>-<name>.md                          ║
║     Report: 12-testkit-report.md                                 ║
║     ⚡ REAL EXECUTION — Jest + Playwright                      ║
║                                                                  ║
║     ❌ FAIL → 🔙 BACK-TO-PLAN (speckit.plan → ... → re-test)  ║
║     ✅ PASS → continue                                          ║
║     Max 3 BACK-TO-PLAN cycles → force continue with defects    ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    │
    ▼
╔══════════════════════════════════════════════════════════════════╗
║  PHASE 5: LAUNCH (Step 13)                                       ║
║  📄 steps/step-13-launch.md                                      ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  STEP 13 ─ Boss (direct: build + DB + launch)                  ║
║  │  Build BE + connect DB + build FE + start services           ║
║  │  Report: 13-launch-report.md (incl. Launch Status)           ║
║  │  ⚡ REAL EXECUTION — npm build, docker up, npm build+start   ║
║  │  open_browser_page → user sees working UI                    ║
║  ▼                                                               ║
║  ✅ PIPELINE COMPLETE                                            ║
║  │  Write final pipeline-completion report                      ║
║  │  Write [END] boss log entry                                   ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## 3. Agent Roster

### 3.1 Generation Agents (artifact creation)

| Agent | Model | Steps | Role | Primary Output |
|-------|-------|-------|------|----------------|
| `okr.srs` | gpt-5.4 | 1 | Requirements analysis → SRS | `srs-<MOD>-<name>.md` |
| `okr.bd` | gpt-5.4 | 2 | External design (BD / External Design) | `bd-<MOD>-<name>.md` |
| `speckit.specify` | gpt-5.4 | 3 | Create feature spec | `spec.md` |
| `speckit.clarify` | gpt-5.4 | 4 | Detect & resolve ambiguities | `spec.md` (updated) |
| `speckit.plan` | gpt-5-3-codex | 6 | Implementation planning | `plan.md`, `data-model.md`, `contracts/` |
| `okr.dd` | gpt-5-3-codex | 8 | Detailed design (DD / Internal Design) | `dd-<MOD>-<name>.md` |
| `speckit.tasks` | gpt-5.4 | 9 | Task decomposition | `tasks.md` |
| `speckit.implement` | gpt-5-3-codex | 10,12,13 | Code implementation + build + launch | `src/modules/<mod>/` |

### 3.2 Review Agents (quality assurance)

| Agent | Model | Steps | Role | Gate |
|-------|-------|-------|------|------|
| `okr.reviewspec` | claude-sonnet-4-6 | 5 | Review spec vs SRS | 🔄 Auto-Retry (max 5) |
| `okr.reviewplan` | claude-sonnet-4-6 | 7 | Review plan vs spec | 🔄 Auto-Retry (max 5) |
| `okr.reviewcode` | claude-sonnet-4-6 | 11 | Review code vs spec/constitution | 🔄 Auto-Retry (max 5) |

### 3.3 QA Agent (independent testing)

| Agent | Model | Steps | Mode | Role |
|-------|-------|-------|------|------|
| `okr.testkit` | claude-sonnet-4-6 | 8b | `gen-testcases` | Generate test cases from SRS+BD+DD |
| `okr.testkit` | claude-sonnet-4-6 | 12 | `run-tests` | Execute tests (Jest + Playwright) |

### 3.4 Boss Orchestrator

| Agent | Model | Steps | Role |
|-------|-------|-------|------|
| `okr.bossbuiltin` | claude-sonnet-4-6 | ALL | Coordinate the entire pipeline, auto-resolve all issues |

### 3.5 Model Selection Rationale by Group

| Group | Agents | Main Task | Preferred Model | Technical Reason |
|-------|--------|-----------|-----------------|------------------|
| Requirements and specification synthesis | `okr.srs`, `okr.bd`, `speckit.specify` | Convert large upstream inputs into formal, internally consistent specification documents | `gpt-5.4` | `gpt-5.4` is a good fit because it handles long-context document synthesis well and keeps structure and terminology stable while writing. That makes it suitable for turning large upstream inputs into long-form specifications with consistent organization and wording. |
| Planning and implementation design | `speckit.plan`, `okr.dd`, `speckit.implement` | Translate approved requirements into implementable technical design and executable code changes | `gpt-5-3-codex` | `gpt-5-3-codex` is a good fit because it is stronger at code-centric reasoning, including code-adjacent design, patch creation and editing, interface- and typing-aware implementation, and build/test-fix loops. That makes it suitable for translating requirements into implementable technical design and executable source changes. |
| Review and orchestration | `okr.reviewspec`, `okr.reviewplan`, `okr.reviewcode`, `okr.testkit`, `okr.bossbuiltin` | Evaluate artifacts, control pipeline progression, and decide pass/fail or retry actions across steps | `claude-sonnet-4-6` | `claude-sonnet-4-6` is a good fit because it is stronger at review and critique, long-context comparison across artifacts, inconsistency and coverage-gap detection, and consistent decision-making. That makes it suitable for gate pass/fail decisions and multi-step pipeline orchestration. |

---

## 4. Communication Mechanisms (Context Exchange)

### 4.1 Boss → Sub-Agent: Structured $ARGUMENTS

```yaml
feature-id: 001-xxx
module-id: mod01
module-keyword: OKR
pipeline-context: docs/output/output_logs/001-xxx/pipeline-context.yaml
mode: autonomous
language: Vietnamese
```

### 4.2 Sub-Agent → Boss: Step Result Block

```yaml
<!-- STEP-RESULT
step: 1
agent: okr.srs
status: SUCCESS
feature-id: 001-xxx
module-id: mod01
artifacts:
  srs-path: docs/output/ipa-docs/srs/srs-mod01-xxx.md
  report: docs/output/output_logs/001-xxx/reports/01-srs-report.md
metrics:
  fea-count: 12
  tbc-count: 3
verdict: APPROVED
next-inputs:
  srs-path: docs/output/ipa-docs/srs/srs-mod01-xxx.md
/STEP-RESULT -->
```

### 4.3 Pipeline Context File (shared state)

```
docs/output/output_logs/<feature-id>/pipeline-context.yaml
```

- Created at Step 0 (immutable fields: feature-id, module-id, tech-stack)
- Updated after each step with artifact paths + metrics from STEP-RESULT
- Sub-agents read this file to discover outputs from prior steps → **no need to re-read large files**

---

## 5. Gate Mechanisms

### 5.1 Report Hard Gate ⛔
- Applies to: **EVERY step** (after completion)
- Requirement: Report file MUST exist with all required sections
- Protocol: `protocols/report-gate-protocol.md`

### 5.2 Review Gate 🔄
- Applies to: Steps 5, 7, 11 (review agents)
- Logic: REJECTED → fix agent corrects → re-review (maximum 5 times)
- Protocol: `protocols/gate-retry-protocol.md`

### 5.3 Build Gate 🔄
- Applies to: Step 10 (implementation + build & fix)
- Logic: Build fail → auto-fix → re-build (maximum 5 times)

### 5.4 Test Gate 🔙
- Applies to: Step 12 (test execution)
- Logic: Test FAIL → **BACK-TO-PLAN** (return to Step 6 → re-plan → re-implement → re-test)
- Maximum 3 BACK-TO-PLAN cycles → force continue

### 5.5 Auto-Resolve 🔧
- Applies to: When encountering `[NEEDS CLARIFICATION]` markers
- Logic: Boss automatically resolves using optimal assumption, logs to report
- Protocol: `protocols/auto-resolve-protocol.md`

---

## 6. File Structure

```
.github/agents/
├── okr.bossbuiltin.agent.md          ← Boss orchestrator (~163 lines)
├── okr.srs.agent.md                  ← Step 1
├── okr.bd.agent.md                   ← Step 2
├── speckit.specify.agent.md          ← Step 3
├── speckit.clarify.agent.md          ← Step 4
├── okr.reviewspec.agent.md           ← Step 5
├── speckit.plan.agent.md             ← Step 6
├── okr.reviewplan.agent.md           ← Step 7
├── okr.dd.agent.md                   ← Step 8
├── okr.testkit.agent.md              ← Steps 8b, 12
├── speckit.tasks.agent.md            ← Step 9
├── speckit.implement.agent.md        ← Step 10
├── okr.reviewcode.agent.md           ← Step 11
│
├── protocols/                        ← Protocols (read on-demand)
│   ├── auto-resolve-protocol.md
│   ├── gate-retry-protocol.md
│   ├── report-gate-protocol.md
│   ├── timestamp-protocol.md
│   ├── log-formats.md
│   ├── implement-delegation.md
│   ├── step-result-block.md
│   └── pipeline-context.md
│
├── steps/                            ← Step definitions (read on-demand)
│   ├── steps-01-04-design.md
│   ├── steps-05-07-review.md
│   ├── steps-08-09-detail.md
│   ├── steps-10-12-implement.md
│   └── step-13-launch.md
│
└── templates/                        ← Shared templates
    ├── report-templates.md           ← Universal report structure
    └── pipeline-completion.md        ← Pipeline completion template
```

---

## 7. Output Structure (Runtime)

```
docs/output/
├── ipa-docs/
│   ├── srs/srs-mod01-xxx.md        ← Step 1
│   ├── bd/bd-mod01-xxx.md           ← Step 2
│   ├── dd/dd-mod01-xxx.md           ← Step 8
│   ├── testcase/testcase-mod01-xxx.md  ← Step 8b
│   └── testreport/testreport-mod01-xxx.md  ← Step 12
│
└── output_logs/<feature-id>/
    ├── 00-boss.log.md                           ← Boss log (all steps)
    ├── pipeline-context.yaml                    ← Shared state
    └── reports/
        ├── 01-srs-report.md
        ├── 02-bd-report.md
        ├── 03-specify-report.md
        ├── 04-clarify-report.md
        ├── 05-review-spec-report.md
        ├── 06-plan-report.md
        ├── 07-review-plan-report.md
        ├── 08-dd-report.md
        ├── 08b-testcases-report.md
        ├── 09-tasks-report.md
        ├── 10-implement-report.md
        ├── 11-review-code-report.md
        ├── 12-testkit-report.md
        └── 13-launch-report.md

specs/<feature-id>/
├── spec.md                                      ← Step 3
├── plan.md                                      ← Step 6
├── data-model.md                                ← Step 6
├── research.md                                  ← Step 6
├── tasks.md                                     ← Step 9
├── contracts/*.md                               ← Step 6
└── checklists/requirements.md                   ← Step 3
```

---

## 8. BACK-TO-PLAN Cycle (Special Flow)

When Step 12 (test execution) FAILS:

```
STEP 12 FAIL
    │
    ▼
Boss logs [BACK-TO-PLAN]
    │
    ▼
STEP 6  speckit.plan       ← re-plan with failure context
    │
    ▼
STEP 7  okr.reviewplan        ← re-review plan
    │
    ▼
STEP 8  okr.dd              ← re-generate DD
    │
    ▼
STEP 9  speckit.tasks      ← re-generate tasks
    │
    ▼
STEP 10 speckit.implement  ← re-implement + build
    │
    ▼
STEP 11 okr.reviewcode      ← re-review code
    │
    ▼
STEP 12 okr.testkit         ← re-test
    │
    ├─ ✅ PASS → STEP 13 (fix & launch)
    └─ ❌ FAIL → repeat cycle (max 3 total)
              └─ After 3 cycles → force STEP 13 with known defects
```
