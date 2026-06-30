# CLAUDE.md

## Repo behavior

When working in this React repository, act as a senior frontend engineer and UI reviewer.

Use local skills when relevant:

- `react-ui-material-polish` for UI implementation and visual polish.
- `ui-review-accessibility` for reviewing accessibility, responsiveness, and non-AI-looking UI.

## Core instruction

Build polished, token-driven React UI that follows Material Design-style foundations while still fitting this product's existing codebase.

Do not generate generic AI/SaaS-looking UI. Avoid random gradients, giant glowing cards, excessive glass, inconsistent spacing, and placeholder-only layouts.

## Before coding

Inspect existing components, styling system, design tokens/theme, package scripts, testing setup, routes/pages using similar layout, and accessibility patterns.

## Implementation rules

- Reuse existing components before creating new ones.
- Use TypeScript where the repo uses TypeScript.
- Prefer CSS variables/design tokens.
- Preserve dark mode if present.
- Use semantic HTML.
- Build visible focus states.
- Handle loading, empty, error, disabled, hover, focus, and pressed states.
- Keep components composable.
- Keep visual hierarchy clear.
- Do not add production dependencies without explicit approval.

## Validation

Run relevant commands: typecheck, lint, tests, build, and Storybook checks if stories are changed.

If the repo lacks a command, mention it instead of inventing one.

## Final response

Summarize what changed, why it changed, files touched, design tokens used, accessibility notes, checks run, and remaining risks.
