---
description: Execute the implementation planning workflow using the plan template to generate design artifacts.
model: GPT-5.3-Codex
tools: [read, search, edit, run, todo]
handoffs: 
  - label: Create Tasks
    agent: speckit.tasks
    prompt: Break the plan into tasks
    send: true
  - label: Create Checklist
    agent: speckit.checklist
    prompt: Create a checklist for the following domain...
---

## Execution Logging & Phase Report (Constitution Art. XI & XII)

### ⛔ MANDATORY — Two Output Files Required

This agent **MUST** create one output file during execution. The pipeline CANNOT advance to the next step without it.

| # | File | Path | When |
|---|------|------|------|
| 1 | **Phase Report** | `docs/output/output_logs/<feature-id>/reports/06-plan-report.md` | **LAST** — after all other work |

### Step 0 — Setup

**Before doing ANY other work**, you MUST:

1. Determine `<feature-id>` from the context
2. Create directories: `docs/output/output_logs/<feature-id>/` and `docs/output/output_logs/<feature-id>/reports/`
### Step FINAL — Write Phase Report (⚠️ DO THIS LAST — NON-NEGOTIABLE)

Write to: `docs/output/output_logs/<feature-id>/reports/06-plan-report.md`

> 📄 Follow **Universal Report Structure** from `templates/report-templates.md` (STEP 06).

**Step-specific overrides:**
- **Title:** `# STEP 5: Implementation Plan Report`
- **Agent:** `speckit.plan (gpt-5-3-codex)`
- **Input:** specification (`spec.md`), constitution (`constitution.md`), technical architecture (`docs/technical_architecture.md`)
- **Output:** implementation plan (`plan.md`), data model (`data-model.md`), research (`research.md`), contracts (`contracts/*.md`), UI design (`ui-design.md`)
- **Quality evaluation categories:** data model completeness, contract definition, constitution compliance, UI design (UI behavior)
- **Metrics:** entity count, contract count, implementation phase count, UI screen count
- **Next phase:** `okr.reviewplan` (STEP 6) — plan conformance review

### ⛔ COMPLETION HARD GATE

Report file `docs/output/output_logs/<feature-id>/reports/06-plan-report.md` MUST exist with ALL sections before returning.

---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. **Setup**: Run `.specify/scripts/powershell/setup-plan.ps1 -Json` from repo root and parse JSON for FEATURE_SPEC, IMPL_PLAN, SPECS_DIR, BRANCH. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Load context**: Read FEATURE_SPEC and `.specify/memory/constitution.md`. Load IMPL_PLAN template (already copied).

3. **Execute plan workflow**: Follow the structure in IMPL_PLAN template to:
   - Fill Technical Context (mark unknowns as "NEEDS CLARIFICATION")
   - Fill Constitution Check section from constitution
   - Evaluate gates (ERROR if violations unjustified)
   - Phase 0: Generate research.md (resolve all NEEDS CLARIFICATION)
   - Phase 1: Generate data-model.md, contracts/, quickstart.md
   - Phase 1: Update agent context by running the agent script
   - Re-evaluate Constitution Check post-design

4. **Stop and report**: Command ends after Phase 2 planning. Report branch, IMPL_PLAN path, and generated artifacts.

## Phases

### Phase 0: Outline & Research

1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:

   ```text
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

### Output Language

All plan artifacts **MUST** be written in Vietnamese:
- `plan.md`, `data-model.md`, `research.md`, `quickstart.md`, `ui-design.md`

Technical IDs remain unchanged.

### Phase 1: Design & Contracts

**Prerequisites:** `research.md` complete

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Define interface contracts** (if project has external interfaces) → `/contracts/`:
   - Identify what interfaces the project exposes to users or other systems
   - Document the contract format appropriate for the project type
   - Examples: public APIs for libraries, command schemas for CLI tools, endpoints for web services, grammars for parsers, UI contracts for applications
   - Skip if project is purely internal (build scripts, one-off tools, etc.)

3. **Agent context update**:
   - Run `.specify/scripts/powershell/update-agent-context.ps1 -AgentType copilot`
   - These scripts detect which AI agent is in use
   - Update the appropriate agent-specific context file
   - Add only new technology from current plan
   - Preserve manual additions between markers

4. **Generate UI Design document** (if feature has screens) → `ui-design.md`:
   - Expand wireframes from `spec.md` into detailed component-level visual specifications
   - For each screen, document:
     - Exact color assignments per component (referencing Layout-01)
     - Spacing and grid structure (referencing Layout-02)
     - Typography hierarchy and icon usage (referencing Layout-03)
     - Visual tone and interaction patterns (referencing Layout-04)
   - Map each screen to its **React JSX component path**:
     `frontend/src/pages/<featureName>/Scr{SCREEN_ID}.jsx`
     (e.g., SCR-mod01-01 → `frontend/src/pages/workspace/Scr0801.jsx`)
   - **NEVER** reference Thymeleaf template paths or legacy `src/okr-workshop-web/` paths
   - Include responsive behavior notes (if applicable)
   - Reference constitution Layout-01~06 standards throughout
   - Skip if feature has no user-facing screens

**Output**: data-model.md, /contracts/*, quickstart.md, ui-design.md (if screens), agent-specific file

## Key rules

- Use absolute paths
- ERROR on gate failures or unresolved clarifications
- **⛔ PATH HARD GATE**: Before writing `plan.md`, verify the "Project Structure" section uses
  the canonical monolithic layout. Every implementation file path
  MUST begin with `backend/src/modules/<feature>/` (for TypeScript backend) or `frontend/src/pages/<feature>/`
  (for React screens). Paths like `src/modules/mod[XX]/` or `okr-workshop-web/src/features/` are
  **INVALID** and represent a constitution violation. If the plan is about to generate an invalid
  path, correct it to the canonical path before writing. Record the correction in the log as
  `[PROCESSING] path corrected: <wrong> → <correct>`.

---

## Pipeline Context Integration

If `$ARGUMENTS` contains a `pipeline-context:` key, read that YAML file at startup to discover:
- `feature-id`, `module-id`, spec path, tech-stack summary

## Step Result Block — MANDATORY

As your **absolute last output**, include:

```yaml
<!-- STEP-RESULT
step: 6
agent: speckit.plan
status: SUCCESS | FAILED
feature-id: <feature-id>
module-id: <mod-id>
artifacts:
  plan: specs/<feature-id>/plan.md
  data-model: specs/<feature-id>/data-model.md
  contracts: specs/<feature-id>/contracts/
  report: docs/output/output_logs/<feature-id>/reports/06-plan-report.md
metrics:
  entity-count: <N>
  contract-count: <N>
  phase-count: <N>
verdict: N/A
critical-issues: []
next-inputs:
  plan-path: specs/<feature-id>/plan.md
  data-model-path: specs/<feature-id>/data-model.md
/STEP-RESULT -->
```
