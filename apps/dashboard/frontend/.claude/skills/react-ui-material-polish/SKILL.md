---
name: react-ui-material-polish
description: Use when creating, modifying, or polishing React UI components/pages with Material Design-style tokens, responsive layout, accessibility, and non-generic visual quality.
allowed-tools: Read, Glob, Grep, Bash, Edit, Write
---

# React UI Material Polish Skill

Use this skill for React UI work that must look polished, product-ready, accessible, and not AI-generated.

## Goal

Create frontend UI that is token-driven, accessible, responsive, visually restrained, consistent with existing code, and suitable for a real product.

Use Material Design 3-style foundations: color roles, typography scale, spacing scale, shape scale, elevation, motion, state layers, and dark mode support.

Do not copy Google branding or proprietary product UI.

## Discovery workflow

Before editing:

1. Inspect `package.json`.
2. Detect framework: Vite, Next.js, Remix, CRA, etc.
3. Detect styling: Tailwind, CSS Modules, CSS variables, styled-components, vanilla-extract, MUI, Chakra, Radix, shadcn/ui, etc.
4. Search for existing tokens: `tokens.css`, `theme.ts`, `tailwind.config`, `styles/`, `packages/ui/`.
5. Search for similar components.
6. Read tests/stories for similar components.
7. Determine whether dark mode exists.

## Implementation rules

### Structure

- Reuse existing components first.
- Keep component props typed.
- Avoid over-abstracting.
- Keep layout logic separate from data/business logic.
- Use composition instead of duplication.
- Avoid adding dependencies unless explicitly approved.

### Visual quality

Use clear hierarchy, predictable spacing, consistent radius, subtle elevation, restrained color, readable labels, meaningful density, and real UI states.

Avoid random gradient backgrounds, excessive glassmorphism, giant soft shadows, arbitrary one-off colors, inconsistent border radius, generic AI dashboard cards, placeholder copy as final content, and decorative icons with no purpose.

### Accessibility

Every UI change must consider semantic HTML, keyboard navigation, focus visible states, form labels, error messaging, disabled states, color contrast, and ARIA only when semantic HTML is not enough.

### Required states

When relevant, include default, hover, focus, active/pressed, disabled, loading, empty, error, selected/current, mobile/tablet/desktop layouts.

## Token usage

Prefer these CSS custom properties when available:

```css
--md-sys-color-primary
--md-sys-color-on-primary
--md-sys-color-surface
--md-sys-color-on-surface
--md-sys-color-surface-container
--md-sys-color-outline
--md-sys-shape-corner-md
--md-sys-elevation-level1
--md-sys-motion-duration-medium2
--app-space-4
```

If the repo uses Tailwind, map tokens through Tailwind config instead of hardcoding values.

## Validation workflow

Run relevant checks: typecheck, lint, unit/component tests, build, Storybook checks when stories are modified, and E2E tests for critical flows.

If visual changes are substantial, create or update Storybook stories when the repo supports Storybook.

## Final report

When done, report files changed, components/pages affected, design tokens used, states covered, accessibility notes, responsive behavior, commands run, and known limitations.
