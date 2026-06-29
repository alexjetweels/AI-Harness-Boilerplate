<!--
Sync Impact Report
Version change: template -> 1.0.0
Modified principles: placeholder principle 1 -> I. Requirement-First Definition; placeholder principle 2 -> II. Workflow and Role Traceability; placeholder principle 3 -> III. Test-First Delivery (Non-Negotiable); placeholder principle 4 -> IV. Reviewable Independent Increments; placeholder principle 5 -> V. Minimal Technical Commitment and Simplicity
Added sections: Product Scope Constraints; Delivery Workflow and Quality Gates
Removed sections: none
Templates requiring updates:
- ✅ .specify/templates/spec-template.md
- ✅ .specify/templates/plan-template.md
- ✅ .specify/templates/tasks-template.md
- ⚠ pending none in .specify/templates/commands because that directory does not exist in this repository
- ✅ README.md
Follow-up TODOs: none
-->

# OKR Web AI-SDLC Constitution

## Core Principles

### I. Requirement-First Definition
Every feature artifact MUST begin from validated business intent, user outcomes, and workflow purpose.
Specifications MUST describe what the system does and why the behavior matters before any implementation
approach is chosen. If the input does not mandate a technical decision, the specification MUST leave that
decision open and record the unresolved point explicitly instead of inventing detail.

Rationale: This project exists to transform customer requirements into reviewable delivery artifacts. Early
technical commitments create rework and hide requirement gaps.

### II. Workflow and Role Traceability
Each feature MUST trace back to a user role, a business workflow step, and an observable business outcome.
Specifications, plans, and tasks MUST preserve that traceability so reviewers can verify why each unit of work
exists. Scope that appears in mockups or examples but lacks defined behavior MUST be marked as excluded or
clarification-needed until the requirement defines it.

Rationale: The OKR system depends on role-driven behavior across employee, manager, and admin workflows.
Traceability prevents hidden assumptions and keeps delivery aligned with the stated process.

### III. Test-First Delivery (Non-Negotiable)
Strict TDD is mandatory. For every behavior being implemented, tests MUST be written first, MUST be observed
failing for the intended reason, and only then may production code be changed. Red-green-refactor is the
required delivery cycle. No feature, fix, or refactor is complete unless automated tests prove the behavior.

Rationale: This repository uses AI-assisted delivery. Test-first execution is the control mechanism that keeps
generated or assisted code aligned with the requirement and safe to evolve.

### IV. Reviewable Independent Increments
User stories MUST be written and planned as independently testable slices that deliver visible value on their
own. Each story MUST have acceptance scenarios, explicit success criteria, and a clear independent test path.
Plans and tasks MUST allow reviewers to validate one increment without requiring the entire product to be done.

Rationale: Small, reviewable increments reduce ambiguity, surface defects earlier, and fit the project's staged
AI-SDLC workflow.

### V. Minimal Technical Commitment and Simplicity
Artifacts created before planning MUST avoid unnecessary architecture, tooling, or implementation detail.
Technical choices MAY be documented only when the input explicitly mandates them or when deferring the choice
would block requirement understanding. When a decision is necessary, the simplest option that satisfies the
requirement and preserves future change MUST be preferred.

Rationale: Simplicity keeps the specification readable and keeps later planning honest about what is known
versus what is still design work.

## Product Scope Constraints

This constitution governs an internal web-based OKR management system used in a workshop context. Current
requirement scope includes authentication, objective creation, key result definition, manager approval,
progress tracking, end-of-cycle evaluation, and dashboard visibility. The system MUST support company,
department, and individual OKR management concepts where they are defined by the requirement. Production-scale
operational concerns MUST not be assumed unless they are explicitly mandated by the input artifact for the
feature being specified or planned.

## Delivery Workflow and Quality Gates

Work MUST proceed in the following order: requirement input, specification, clarification of gaps, plan,
design artifacts, tasks, implementation, review, and test execution. A specification is not ready for planning
unless it is clear, reviewable, technology-agnostic except for mandated constraints, and contains explicit
clarification items for unresolved business rules. A plan is not ready for implementation unless its
constitution check confirms strict TDD, independent story delivery, and traceability back to the specification.
Tasks MUST list test work before implementation work for every user story. Reviews MUST reject artifacts that
replace missing requirements with undocumented assumptions.

## Governance

This constitution overrides conflicting local habits and template defaults. Amendments MUST document the reason
for change, the affected principles or sections, the semantic version bump rationale, and any downstream
template updates required to keep the workflow aligned. Versioning follows semantic rules: MAJOR for breaking
governance changes or removal of principles, MINOR for new principles or materially expanded obligations, and
PATCH for clarifications that do not change expected behavior. Compliance review is mandatory during spec,
plan, task, and implementation review. Any exception MUST be documented in the relevant artifact with explicit
justification and reviewer acknowledgement.

**Version**: 1.0.0 | **Ratified**: 2026-04-05 | **Last Amended**: 2026-04-05
