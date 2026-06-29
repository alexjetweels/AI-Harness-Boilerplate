---
description: Create or update the feature specification from a natural language feature description.
model: GPT-5.4
tools: [read, search, edit, todo]
handoffs: 
  - label: Build Technical Plan
    agent: speckit.plan
    prompt: Create a plan for the spec. I am building with...
  - label: Clarify Spec Requirements
    agent: speckit.clarify
    prompt: Clarify specification requirements
    send: true
---

## Execution Logging & Phase Report (Constitution Art. XI & XII)

### ⛔ MANDATORY — Two Output Files Required

This agent **MUST** create one output file during execution. The pipeline CANNOT advance to the next step without it.

| # | File | Path | When |
|---|------|------|------|
| 1 | **Phase Report** | `docs/output/output_logs/<feature-id>/reports/03-specify-report.md` | **LAST** — after all other work |

### Step 0 — Setup

**Before doing ANY other work** (before branch creation, before reading templates), you MUST:

1. Determine `<feature-id>` from the context (branch name, specs directory, or generate from feature description)
2. Create directories: `docs/output/output_logs/<feature-id>/` and `docs/output/output_logs/<feature-id>/reports/`
### Step FINAL — Write Phase Report (⚠️ DO THIS LAST — NON-NEGOTIABLE)

As your **absolute last action** before returning to the user or boss orchestrator, write the phase report. This file MUST exist or the pipeline is blocked.

Write to: `docs/output/output_logs/<feature-id>/reports/03-specify-report.md`

Use this **exact template** (in Vietnamese):

> 📄 Follow **Universal Report Structure** from `templates/report-templates.md` (STEP 03).

**Step-specific overrides:**
- **Title:** `# STEP 2: Specification Creation Report`
- **Agent:** `speckit.specify (gpt-5.4)`
- **Input:** feature description, SRS (`srs-<mod-id>-<name>.md`), BD (`bd-<mod-id>-<name>.md`), template, constitution
- **Output:** specification (`specs/<feature-id>/spec.md`), quality checklist (`specs/<feature-id>/checklists/requirements.md`)
- **Quality evaluation categories:** content quality, requirement completeness, feature readiness, screen layout (UI), wireframe (UI), visual design specification (UI)
- **Metrics:** user story count, functional requirement count, screen layout count, wireframe count, visual design specification count, success criteria count, [NEEDS CLARIFICATION] marker count, quality checklist pass rate
- **Next phase:** `speckit.clarify` (STEP 3) — ambiguity detection and resolution for the specification

### ⛔ COMPLETION HARD GATE

**You MUST NOT return SUCCESS or declare completion** until the following file exists with complete content:

1. ✅ `docs/output/output_logs/<feature-id>/reports/03-specify-report.md` — with ALL sections listed above

**If either file is missing or incomplete when you finish your main spec work, CREATE/COMPLETE IT NOW before returning.**

---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/speckit.specify` in the triggering message **is** the feature description. Assume you always have it available in this conversation even if `$ARGUMENTS` appears literally below. Do not ask the user to repeat it unless they provided an empty command.

Given that feature description, do this:

1. **Generate a concise short name** (2-4 words) for the branch:
   - Analyze the feature description and extract the most meaningful keywords
   - Create a 2-4 word short name that captures the essence of the feature
   - Use action-noun format when possible (e.g., "add-user-auth", "fix-payment-bug")
   - Preserve technical terms and acronyms (OAuth2, API, JWT, etc.)
   - Keep it concise but descriptive enough to understand the feature at a glance
   - Examples:
     - "I want to add user authentication" → "user-auth"
     - "Implement OAuth2 integration for the API" → "oauth2-api-integration"
     - "Create a dashboard for analytics" → "analytics-dashboard"
     - "Fix payment processing timeout bug" → "fix-payment-timeout"

2. **Check for existing spec folder FIRST — prevents duplicate creation**:

   ⚠️ **CRITICAL: Before ANY git operations or new folder creation, run this check:**

   a. Derive the short-name from the feature description (same logic as step 1 above).

   b. Scan the `specs/` directory for an existing folder matching the short-name:
      ```powershell
      Get-ChildItem specs/ -Directory | Where-Object { $_.Name -match '<short-name>' }
      ```

   c. **If a matching folder is found** (e.g., `specs/001-xxx/spec.md` exists):
      - **Do NOT create a new branch or a new numbered folder.**
      - Set `<feature-id>` = the existing folder name (e.g., `001-xxx`)
      - Set `FEATURE_DIR` = `specs/<feature-id>`
      - Set `SPEC_FILE` = `specs/<feature-id>/spec.md`
      - **Skip steps 2d (the create-new-feature.ps1 script) entirely** — the folder already exists
      - Log in the phase report: "Detected existing spec folder: `specs/<feature-id>/` — skip new creation and update the existing spec instead"
      - Proceed directly to step 3 (load spec template), then **UPDATE the existing spec.md in-place** with new content

   d. **If NO matching folder is found**: proceed to the original creation flow below.

   e. Find the highest feature number across all sources for the short-name:
      - Remote branches: `git ls-remote --heads origin | grep -E 'refs/heads/[0-9]+-<short-name>$'`
      - Local branches: `git branch | grep -E '^[* ]*[0-9]+-<short-name>$'`
      - Specs directories: Check for directories matching `specs/[0-9]+-<short-name>`

   f. Determine the next available number:
      - Extract all numbers from all three sources
      - Find the highest number N
      - Use N+1 for the new branch number

   g. Run the script `.specify/scripts/powershell/create-new-feature.ps1 -Json "$ARGUMENTS"` with the calculated number and short-name:
      - Pass `--number N+1` and `--short-name "your-short-name"` along with the feature description
      - Bash example: `.specify/scripts/powershell/create-new-feature.ps1 -Json "$ARGUMENTS" --json --number 5 --short-name "user-auth" "Add user authentication"`
      - PowerShell example: `.specify/scripts/powershell/create-new-feature.ps1 -Json "$ARGUMENTS" -Json -Number 5 -ShortName "user-auth" "Add user authentication"`

   **IMPORTANT**:
   - Check all three sources (remote branches, local branches, specs directories) to find the highest number
   - Only match branches/directories with the exact short-name pattern
   - If no existing branches/directories found with this short-name, start with number 1
   - You must only ever run this script once per feature
   - The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for
   - The JSON output will contain BRANCH_NAME and SPEC_FILE paths
   - For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot")

3. Load `.specify/templates/spec-template.md` to understand required sections.

4. Follow this execution flow:

    1. Parse user description from Input
       If empty: ERROR "No feature description provided"
    2. Extract key concepts from description
       Identify: actors, actions, data, constraints
    3. For unclear aspects:
       - Make informed guesses based on context and industry standards
       - Only mark with [NEEDS CLARIFICATION: specific question] if:
         - The choice significantly impacts feature scope or user experience
         - Multiple reasonable interpretations exist with different implications
         - No reasonable default exists
       - **LIMIT: Maximum 3 [NEEDS CLARIFICATION] markers total**
       - Prioritize clarifications by impact: scope > security/privacy > user experience > technical details
    4. Fill User Scenarios & Testing section
       If no clear user flow: ERROR "Cannot determine user scenarios"
    4b. **Derive Screen Layouts** (if feature has UI):
       - Scan user stories for screen references (explicit IDs or implied UI interactions)
       - For each distinct screen, fill the Screen Layouts section per the template
       - Cross-check: every screen ID in user stories must appear in Screen Layouts
       - Cross-check: every action in Screen Layouts must trace to at least one FR
    4c. **Generate Wireframes** (mandatory if feature has UI — Layout-05):
       - For each screen in Screen Layouts, create an ASCII wireframe showing spatial arrangement
       - Wireframe MUST reflect: Layout Regions, Displayed Information, Available Actions, State Variations
       - Label each region clearly; show key data items and action buttons in their spatial positions
       - Populate the `### Wireframes` section in the spec with one wireframe per screen
    4d. **Generate Visual Design Specs** (mandatory if feature has UI — Layout-06):
       - For each screen, create a component-level visual mapping table
       - Map every visible UI element to constitution Layout-01~10 standards (`docs/technical_architecture.md §IV`):
         - Colors (Layout-01): reference Bootstrap class tokens only (`bg-primary`, `text-danger`, etc.) — NO custom hex values
         - Layout (Layout-02): 2-tier header model per §IV.1, Bootstrap 5 grid
         - Typography & icons (Layout-03): Bootstrap Icons 1.x, WCAG AA ≥4.5:1 contrast
         - Visual tone (Layout-04): no decorative animations
       - Column format: Component | Bootstrap class pattern | Constitution / technical_architecture.md Ref
       - Populate the `### Visual Design Specs` section in the spec
    5. Generate Functional Requirements
       Each requirement must be testable
       Use reasonable defaults for unspecified details (document assumptions in Assumptions section)
    6. Define Success Criteria
       Create measurable, technology-agnostic outcomes
       Include both quantitative metrics (time, performance, volume) and qualitative measures (user satisfaction, task completion)
       Each criterion must be verifiable without implementation details
    7. Identify Key Entities (if data involved)
    8. Return: SUCCESS (spec ready for planning)

5. Write the specification to SPEC_FILE using the template structure, replacing placeholders with concrete details derived from the feature description (arguments) while preserving section order and headings.

6. **Specification Quality Validation**: After writing the initial spec, validate it against quality criteria:

   a. **Create Spec Quality Checklist**: Generate a checklist file at `FEATURE_DIR/checklists/requirements.md` using the checklist template structure with these validation items:

      ```markdown
      # Specification Quality Checklist: [FEATURE NAME]
      
      **Purpose**: Validate specification completeness and quality before proceeding to planning
      **Created**: [DATE]
      **Feature**: [Link to spec.md]
      
      ## Content Quality
      
      - [ ] No implementation details (languages, frameworks, APIs)
      - [ ] Focused on user value and business needs
      - [ ] Written for non-technical stakeholders
      - [ ] All mandatory sections completed
      
      ## Requirement Completeness
      
      - [ ] No [NEEDS CLARIFICATION] markers remain
      - [ ] Requirements are testable and unambiguous
      - [ ] Success criteria are measurable
      - [ ] Success criteria are technology-agnostic (no implementation details)
      - [ ] All acceptance scenarios are defined
      - [ ] Edge cases are identified
      - [ ] Scope is clearly bounded
      - [ ] Dependencies and assumptions identified
      
      ## Feature Readiness
      
      - [ ] All functional requirements have clear acceptance criteria
      - [ ] User scenarios cover primary flows
      - [ ] Feature meets measurable outcomes defined in Success Criteria
      - [ ] No implementation details leak into specification
      
      ## UI Screen Layouts *(required if feature has UI)*
      
      - [ ] Screen Layouts section exists (FAIL if feature has user-facing screens and section is missing)
      - [ ] Every screen ID referenced in User Stories has a corresponding Screen Layout entry
      - [ ] Each screen layout includes: Layout Regions, Displayed Information, Available Actions, State Variations
      - [ ] Screen layout descriptions are technology-agnostic (no CSS, component names, framework terms)
      
      ## Wireframes *(required if feature has UI — Layout-05)*
      
      - [ ] Wireframes section exists (FAIL if feature has user-facing screens and section is missing)
      - [ ] Every screen in Screen Layouts has a corresponding wireframe
      - [ ] Each wireframe shows spatial arrangement of all Layout Regions defined in the screen layout
      - [ ] Key data items and action buttons are labeled in their spatial positions
      - [ ] Wireframes are technology-agnostic (no CSS classes, component names, or framework terms)
      
      ## Visual Design Specs *(required if feature has UI — Layout-06)*
      
      - [ ] Visual Design Specs section exists (FAIL if feature has user-facing screens and section is missing)
      - [ ] Every screen in Screen Layouts has a corresponding visual design mapping table
      - [ ] Each component maps to a specific Layout-01~04 constitution reference
      - [ ] Color values match constitution palette (#1D4ED8, #FFFFFF, #1E293B)
      - [ ] No CSS classes, component names, or framework terms in visual specs
      
      ## Notes
      
      - Items marked incomplete require spec updates before `/speckit.clarify` or `/speckit.plan`
      ```

   b. **Run Validation Check**: Review the spec against each checklist item:
      - For each item, determine if it passes or fails
      - Document specific issues found (quote relevant spec sections)

   c. **Handle Validation Results**:

      - **If all items pass**: Mark checklist complete and proceed to step 6

      - **If items fail (excluding [NEEDS CLARIFICATION])**:
        1. List the failing items and specific issues
        2. Update the spec to address each issue
        3. Re-run validation until all items pass (max 3 iterations)
        4. If still failing after 3 iterations, document remaining issues in checklist notes and warn user

      - **If [NEEDS CLARIFICATION] markers remain**:
        1. Extract all [NEEDS CLARIFICATION: ...] markers from the spec
        2. **LIMIT CHECK**: If more than 3 markers exist, keep only the 3 most critical (by scope/security/UX impact) and make informed guesses for the rest
        3. For each clarification needed (max 3), present options to user in this format:

           ```markdown
           ## Question [N]: [Topic]
           
           **Context**: [Quote relevant spec section]
           
           **What we need to know**: [Specific question from NEEDS CLARIFICATION marker]
           
           **Suggested Answers**:
           
           | Option | Answer | Implications |
           |--------|--------|--------------|
           | A      | [First suggested answer] | [What this means for the feature] |
           | B      | [Second suggested answer] | [What this means for the feature] |
           | C      | [Third suggested answer] | [What this means for the feature] |
           | Custom | Provide your own answer | [Explain how to provide custom input] |
           
           **Your choice**: _[Wait for user response]_
           ```

        4. **CRITICAL - Table Formatting**: Ensure markdown tables are properly formatted:
           - Use consistent spacing with pipes aligned
           - Each cell should have spaces around content: `| Content |` not `|Content|`
           - Header separator must have at least 3 dashes: `|--------|`
           - Test that the table renders correctly in markdown preview
        5. Number questions sequentially (Q1, Q2, Q3 - max 3 total)
        6. Present all questions together before waiting for responses
        7. Wait for user to respond with their choices for all questions (e.g., "Q1: A, Q2: Custom - [details], Q3: B")
        8. Update the spec by replacing each [NEEDS CLARIFICATION] marker with the user's selected or provided answer
        9. Re-run validation after all clarifications are resolved

   d. **Update Checklist**: After each validation iteration, update the checklist file with current pass/fail status

7. Report completion with branch name, spec file path (`spec.md`), checklist results, and readiness for the next phase (`/speckit.clarify` or `/speckit.plan`).

**NOTE:** The script creates and checks out the new branch and initializes the spec file before writing.

## General Guidelines

## Quick Guidelines

- Focus on **WHAT** users need and **WHY**.
- Avoid HOW to implement (no tech stack, APIs, code structure), **but always describe WHAT users see on screen** — layout regions, displayed information, and available actions are part of the specification, not implementation.
- Written for business stakeholders, not developers.
- DO NOT create any checklists that are embedded in the spec. That will be a separate command.

### UI / Screen Layout Requirements

If the feature includes **any user-facing screens** (web pages, dashboards, forms, dialogs), you **MUST** include a `## Screen Layouts` section in the spec. This section describes **what the user sees and can do**, not how it is coded.

For each screen:

| Item | Description |
|------|-------------|
| **Screen ID** | Unique ID matching user stories (e.g., SCR-mod01-01) |
| **Screen Name** | Human-readable name |
| **Purpose** | What the user accomplishes on this screen |
| **Primary User** | Which actor uses this screen |
| **Entry Point** | How the user navigates here |
| **Layout Regions** | Named areas of the screen (header, sidebar, main panel, footer, etc.) with a brief description of what each region contains |
| **Displayed Information** | Data items shown, grouped by region |
| **Available Actions** | Buttons, links, controls the user can interact with, and what each action does |
| **State Variations** | How the screen changes based on conditions (e.g., alarm active vs. normal, loading vs. loaded, empty state) |
| **Wireframe** *(mandatory — Layout-05)* | ASCII or Mermaid diagram showing spatial arrangement of regions. Must match Layout Regions, Displayed Information, and Available Actions above. |
| **Visual Design Mapping** *(mandatory — Layout-06)* | Component-level visual specs table mapping each UI element to constitution Layout-01~04 standards (colors, spacing, typography, tone). No CSS classes or framework terms. |

Rules:
- Screen IDs referenced in User Stories **MUST** each have a corresponding entry in Screen Layouts.
- Layout descriptions are **technology-agnostic** — no CSS classes, component names, or framework terms.
- Focus on **information architecture** and **user interaction**, not visual styling.

### Section Requirements

- **Mandatory sections**: Must be completed for every feature
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation

When creating this spec from a user prompt:

1. **Make informed guesses**: Use context, industry standards, and common patterns to fill gaps
2. **Document assumptions**: Record reasonable defaults in the Assumptions section
3. **Limit clarifications**: Maximum 3 [NEEDS CLARIFICATION] markers - use only for critical decisions that:
   - Significantly impact feature scope or user experience
   - Have multiple reasonable interpretations with different implications
   - Lack any reasonable default
4. **Prioritize clarifications**: scope > security/privacy > user experience > technical details
5. **Think like a tester**: Every vague requirement should fail the "testable and unambiguous" checklist item
6. **Common areas needing clarification** (only if no reasonable default exists):
   - Feature scope and boundaries (include/exclude specific use cases)
   - User types and permissions (if multiple conflicting interpretations possible)
   - Security/compliance requirements (when legally/financially significant)

**Examples of reasonable defaults** (don't ask about these):

- Data retention: Industry-standard practices for the domain
- Performance targets: Standard web/mobile app expectations unless specified
- Error handling: User-friendly messages with appropriate fallbacks
- Authentication method: Read from `docs/technical_architecture.md` — JWT (Passport.js + jsonwebtoken) for this project; OAuth2 when integrating external identity providers
- Integration patterns: Use project-appropriate patterns (REST/GraphQL for web services, function calls for libraries, CLI args for tools, etc.)

### Success Criteria Guidelines

Success criteria must be:

1. **Measurable**: Include specific metrics (time, percentage, count, rate)
2. **Technology-agnostic**: No mention of frameworks, languages, databases, or tools
3. **User-focused**: Describe outcomes from user/business perspective, not system internals
4. **Verifiable**: Can be tested/validated without knowing implementation details

**Good examples**:

- "Users can complete checkout in under 3 minutes"
- "System supports 10,000 concurrent users"
- "95% of searches return results in under 1 second"
- "Task completion rate improves by 40%"

**Bad examples** (implementation-focused):

- "API response time is under 200ms" (too technical, use "Users see results instantly")
- "Database can handle 1000 TPS" (implementation detail, use user-facing metric)
- "React components render efficiently" (framework-specific)
- "Redis cache hit rate above 80%" (technology-specific)

---

## Pipeline Context Integration

If `$ARGUMENTS` contains a `pipeline-context:` key, read that YAML file at startup to discover:
- `feature-id`, `module-id` (use existing feature-id, do NOT generate new one)
- SRS and BD paths from prior steps

## Step Result Block — MANDATORY

As your **absolute last output**, include:

```yaml
<!-- STEP-RESULT
step: 3
agent: speckit.specify
status: SUCCESS | FAILED
feature-id: <feature-id>
module-id: <mod-id>
artifacts:
  spec: specs/<feature-id>/spec.md
  report: docs/output/output_logs/<feature-id>/reports/03-specify-report.md
metrics:
  user-story-count: <N>
  fr-count: <N>
  tbc-count: <N>
verdict: N/A
critical-issues: []
next-inputs:
  spec-path: specs/<feature-id>/spec.md
/STEP-RESULT -->
```
