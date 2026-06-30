---
name: ui-review-accessibility
description: Use when reviewing React UI for accessibility, responsive behavior, visual polish, design-token consistency, and anti-AI-looking quality.
allowed-tools: Read, Glob, Grep, Bash
---

# UI Review Accessibility Skill

Use this skill to review UI code, PR diffs, components, pages, or screenshots.

## Review dimensions

Score each area from 1 to 5:

1. Visual hierarchy
2. Token consistency
3. Layout and spacing
4. Responsive behavior
5. Accessibility
6. Interaction states
7. Content realism
8. Maintainability
9. Test coverage
10. Product fit

## Accessibility checklist

Check semantic HTML, keyboard accessibility, focus visible, input labels, button/link semantics, ARIA usage, disabled state clarity, error text association, contrast issues, and motion reduction.

## Anti-AI-look checklist

Flag generic gradients, excessive glass effects, decorative cards with no purpose, huge whitespace without information hierarchy, repetitive icon-card grids, inconsistent radius/shadows, placeholder copy, unrealistic data, overuse of emojis, center-aligned everything, and lack of edge states.

## Output format

```text
UI Review Summary

Overall score: X/10

High priority issues:
1.
2.
3.

Recommended fixes:
1.
2.
3.

Accessibility notes:
-

Token/design-system notes:
-

Tests or stories to add:
-
```
