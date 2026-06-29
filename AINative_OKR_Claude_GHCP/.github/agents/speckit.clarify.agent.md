---
description: Identify underspecified areas in the current feature spec by asking up to 5 highly targeted clarification questions and encoding answers back into the spec.
model: GPT-5.4
tools: [read, search, edit, todo]
handoffs: 
  - label: Build Technical Plan
    agent: speckit.plan
    prompt: Create a plan for the spec. I am building with...
---

## Execution Logging & Phase Report (Constitution Art. XI & XII)

### ⛔ MANDATORY — Two Output Files Required

This agent **MUST** create one output file during execution. The pipeline CANNOT advance to the next step without it.

| # | File | Path | When |
|---|------|------|------|
| 1 | **Phase Report** | `docs/output/output_logs/<feature-id>/reports/04-clarify-report.md` | **LAST** — after all other work |

### Step 0 — Setup

**Before doing ANY other work**, you MUST:

1. Determine `<feature-id>` from the context
2. Create directories: `docs/output/output_logs/<feature-id>/` and `docs/output/output_logs/<feature-id>/reports/`
### Step FINAL — Write Phase Report (⚠️ DO THIS LAST — NON-NEGOTIABLE)

Write to: `docs/output/output_logs/<feature-id>/reports/04-clarify-report.md`

> 📄 Follow **Universal Report Structure** from `templates/report-templates.md` (STEP 04).

**Step-specific overrides:**
- **Title:** `# STEP 3: Specification Clarification Report`
- **Agent:** `speckit.clarify (gpt-5.4)`
- **Input:** specification (`specs/<feature-id>/spec.md`)
- **Output:** Q&A document (`04-clarify-qa.md`), updated specification (`spec.md`)
- **Quality evaluation categories:** ambiguity detection, Q&A quality, completeness of spec updates
- **Metrics:** ambiguity count, resolved count, unresolved count
- **Additional section:** `## QA Summary` — full question + answer table
- **Next phase:** `okr.reviewspec` (STEP 4) — specification quality review

### ⛔ COMPLETION HARD GATE

Report file `docs/output/output_logs/<feature-id>/reports/04-clarify-report.md` MUST exist with ALL sections before returning.

---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

Goal: Detect and reduce ambiguity or missing decision points in the active feature specification and record the clarifications directly in the spec file.

Note: This clarification workflow is expected to run (and be completed) BEFORE invoking `/speckit.plan`. If the user explicitly states they are skipping clarification (e.g., exploratory spike), you may proceed, but must warn that downstream rework risk increases.

Execution steps:

1. Run `.specify/scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly` from repo root **once** (combined `--json --paths-only` mode / `-Json -PathsOnly`). Parse minimal JSON payload fields:
   - `FEATURE_DIR`
   - `FEATURE_SPEC`
   - (Optionally capture `IMPL_PLAN`, `TASKS` for future chained flows.)
   - If JSON parsing fails, abort and instruct user to re-run `/speckit.specify` or verify feature branch environment.
   - For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. Load the current spec file.

   **2a. Collect carry-forward markers**: Scan the spec for all `[NEEDS CLARIFICATION: ...]` markers left by `speckit.specify`. Extract each into a structured list: `{ id: "TBC-XX", description: "...", related: "FR-XXX" }`. These are **Part A** of the consolidated QA list.

   **2b. Structured ambiguity scan**: Perform a structured ambiguity & coverage scan using this taxonomy. For each category, mark status: Clear / Partial / Missing. Produce an internal coverage map used for prioritization (do not output raw map unless no questions will be asked).

   Functional Scope & Behavior:
   - Core user goals & success criteria
   - Explicit out-of-scope declarations
   - User roles / personas differentiation

   Domain & Data Model:
   - Entities, attributes, relationships
   - Identity & uniqueness rules
   - Lifecycle/state transitions
   - Data volume / scale assumptions

   Interaction & UX Flow:
   - Critical user journeys / sequences
   - Error/empty/loading states
   - Accessibility or localization notes

   Non-Functional Quality Attributes:
   - Performance (latency, throughput targets)
   - Scalability (horizontal/vertical, limits)
   - Reliability & availability (uptime, recovery expectations)
   - Observability (logging, metrics, tracing signals)
   - Security & privacy (authN/Z, data protection, threat assumptions)
   - Compliance / regulatory constraints (if any)

   Integration & External Dependencies:
   - External services/APIs and failure modes
   - Data import/export formats
   - Protocol/versioning assumptions

   Edge Cases & Failure Handling:
   - Negative scenarios
   - Rate limiting / throttling
   - Conflict resolution (e.g., concurrent edits)

   Constraints & Tradeoffs:
   - Technical constraints (language, storage, hosting)
   - Explicit tradeoffs or rejected alternatives

   Terminology & Consistency:
   - Canonical glossary terms
   - Avoided synonyms / deprecated terms

   Completion Signals:
   - Acceptance criteria testability
   - Measurable Definition of Done style indicators

   Misc / Placeholders:
   - TODO markers / unresolved decisions
   - Ambiguous adjectives ("robust", "intuitive") lacking quantification

   For each category with Partial or Missing status, add a candidate question opportunity unless:
   - Clarification would not materially change implementation or validation strategy
   - Information is better deferred to planning phase (note internally)

3. Generate (internally) a prioritized queue of candidate clarification questions. These are **Part B** of the consolidated QA list. Do NOT output them yet. Apply these constraints:
    - Maximum of 5 NEW clarify questions (Part B) + all carry-forward markers (Part A, uncapped).
    - Combined total (Part A + Part B) should not exceed 8 questions. If Part A already has 3+ items, reduce Part B accordingly.
    - Each question must be answerable with EITHER:
       - A short multiple‑choice selection (2–5 distinct, mutually exclusive options), OR
       - A one-word / short‑phrase answer (explicitly constrain: "Answer in <=5 words").
    - Only include questions whose answers materially impact architecture, data modeling, task decomposition, test design, UX behavior, operational readiness, or compliance validation.
    - Ensure category coverage balance: attempt to cover the highest impact unresolved categories first; avoid asking two low-impact questions when a single high-impact area (e.g., security posture) is unresolved.
    - Exclude questions already answered, trivial stylistic preferences, or plan-level execution details (unless blocking correctness).
    - Favor clarifications that reduce downstream rework risk or prevent misaligned acceptance tests.
    - If more than 5 categories remain unresolved, select the top 5 by (Impact * Uncertainty) heuristic.

4. Consolidated QA output (batch mode):
    - Merge Part A (carry-forward markers from `speckit.specify`) and Part B (new clarify questions) into a **single numbered list**.
    - Part A questions come first (prefixed `[from specify]`), then Part B (prefixed `[from clarify]`).
    - Output the full consolidated QA list to `docs/output/output_logs/<feature-id>/reports/04-clarify-qa.md` (Vietnamese).
    - **Present ALL questions at once** to the user in a single message. Do NOT ask one-by-one.
    - For each multiple‑choice question:
       - **Analyze all options** and determine the **most suitable option** based on:
          - Best practices for the project type
          - Common patterns in similar implementations
          - Risk reduction (security, performance, maintainability)
          - Alignment with any explicit project goals or constraints visible in the spec
       - Present your **recommended option prominently**: `**Recommended:** Option [X] - <reasoning>`
       - Then render all options as a Markdown table:

       | Option | Description |
       |--------|-------------|
       | A | <Option A description> |
       | B | <Option B description> |
       | C | <Option C description> (add D/E as needed up to 5) |
       | Short | Provide a different short answer (<=5 words) (Include only if free-form alternative is appropriate) |

    - For short‑answer style (no meaningful discrete options):
       - Provide your **suggested answer**: `**Suggested:** <your proposed answer> - <brief reasoning>`
    - At the end of the full list, add a summary table and instructions:
       ```
       | # | Question | Your Answer |
       |---|----------|-------------|
       | Q1 | ... | ___ |
       | Q2 | ... | ___ |
       ...

       Reply with: `Q1=A Q2=B Q3=yes ...` (use "yes" to accept the recommendation)
       ```
    - Wait for the user to answer ALL questions in a single response.
    - After the user answers:
       - If the user replies "yes" or "recommended" for a specific question, use the recommendation.
       - Validate each answer maps to a valid option or fits the <=5 word constraint.
       - If any answer is ambiguous, ask for disambiguation only for that specific question.
       - Once all answers are satisfactory, proceed to integration (step 5).
    - If no valid questions exist (no markers + full coverage), immediately report no critical ambiguities.

5. Integration after ALL answers received (batch update approach):
    - After receiving and validating all user answers, apply them to the spec in a single pass.
    - For **Part A answers** (carry-forward `[NEEDS CLARIFICATION]` markers):
       - Replace each `[NEEDS CLARIFICATION: TBC-XX ...]` marker in the spec with the confirmed answer text.
       - Remove the marker entirely — the answer becomes part of the requirement prose.
    - For **Part B answers** (new clarify questions):
       - Ensure a `## Clarifications` section exists (create it just after the highest-level contextual/overview section per the spec template if missing).
       - Under it, create (if not present) a `### Session YYYY-MM-DD` subheading for today.
       - Append a bullet line for each: `- Q: <question> → A: <final answer>`.
    - For ALL answers, apply the clarification to the most appropriate section(s):
       - Functional ambiguity → Update or add a bullet in Functional Requirements.
       - User interaction / actor distinction → Update User Stories or Actors subsection (if present) with clarified role, constraint, or scenario.
       - Data shape / entities → Update Data Model (add fields, types, relationships) preserving ordering; note added constraints succinctly.
       - Non-functional constraint → Add/modify measurable criteria in Non-Functional / Quality Attributes section (convert vague adjective to metric or explicit target).
       - Edge case / negative flow → Add a new bullet under Edge Cases / Error Handling (or create such subsection if template provides placeholder for it).
       - Terminology conflict → Normalize term across spec; retain original only if necessary by adding `(formerly referred to as "X")` once.
    - If the clarification invalidates an earlier ambiguous statement, replace that statement instead of duplicating; leave no obsolete contradictory text.
    - Save the spec file AFTER each integration to minimize risk of context loss (atomic overwrite).
    - Preserve formatting: do not reorder unrelated sections; keep heading hierarchy intact.
    - Keep each inserted clarification minimal and testable (avoid narrative drift).

6. Validation (performed once after batch write + final pass):
   - All Part A `[NEEDS CLARIFICATION]` markers have been removed from the spec.
   - Clarifications session contains exactly one bullet per Part B accepted answer (no duplicates).
   - Total questions ≤ 8 (Part A + Part B combined).
   - Updated sections contain no lingering vague placeholders the new answer was meant to resolve.
   - No contradictory earlier statement remains (scan for now-invalid alternative choices removed).
   - Markdown structure valid; only allowed new headings: `## Clarifications`, `### Session YYYY-MM-DD`.
   - Terminology consistency: same canonical term used across all updated sections.

7. Write the updated spec back to `FEATURE_SPEC`.

8. Report completion (after questioning loop ends or early termination):
   - Number of questions asked & answered.
   - Path to updated spec.
   - Sections touched (list names).
   - Coverage summary table listing each taxonomy category with Status: Resolved (was Partial/Missing and addressed), Deferred (exceeds question quota or better suited for planning), Clear (already sufficient), Outstanding (still Partial/Missing but low impact).
   - If any Outstanding or Deferred remain, recommend whether to proceed to `/speckit.plan` or run `/speckit.clarify` again later post-plan.
   - Suggested next command.

Behavior rules:

- If no meaningful ambiguities found (or all potential questions would be low-impact), respond: "No critical ambiguities detected worth formal clarification." and suggest proceeding.
- If spec file missing, instruct user to run `/speckit.specify` first (do not create a new spec here).
- Never exceed 8 total questions (Part A carry-forward + Part B new clarify combined).
- Avoid speculative tech stack questions unless the absence blocks functional clarity.
- Respect user early termination signals ("stop", "done", "proceed").
- If no questions asked due to full coverage, output a compact coverage summary (all categories Clear) then suggest advancing.
- If quota reached with unresolved high-impact categories remaining, explicitly flag them under Deferred with rationale.

Context for prioritization: $ARGUMENTS

---

## Pipeline Context Integration

If `$ARGUMENTS` contains a `pipeline-context:` key, read that YAML file at startup to discover:
- `feature-id`, spec path from Step 3

## Step Result Block — MANDATORY

As your **absolute last output**, include:

```yaml
<!-- STEP-RESULT
step: 4
agent: speckit.clarify
status: SUCCESS | FAILED
feature-id: <feature-id>
module-id: <mod-id>
artifacts:
  qa: docs/output/output_logs/<feature-id>/reports/04-clarify-qa.md
  report: docs/output/output_logs/<feature-id>/reports/04-clarify-report.md
metrics:
  ambiguities-found: <N>
  resolved: <N>
  unresolved: <N>
verdict: N/A
critical-issues: []
next-inputs:
  spec-path: specs/<feature-id>/spec.md
/STEP-RESULT -->
```
