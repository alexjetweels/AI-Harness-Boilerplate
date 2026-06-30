# Prompt: Build React UI

```text
You are working in my React application.

Goal:
Build [COMPONENT_OR_PAGE] for [USER_OR_USE_CASE].

Use the repo's existing patterns and the design tokens in `design-tokens/tokens.css` if available.

Requirements:
- Make it look like a real production UI, not a generic AI-generated mockup.
- Use Material Design-style foundations: color roles, type scale, spacing, shape, elevation, motion, and state layers.
- Do not copy Google branding or proprietary Google product UI.
- Reuse existing components before creating new ones.
- Include responsive behavior.
- Include loading, empty, error, disabled, hover, focus, and active states where relevant.
- Ensure semantic HTML and keyboard accessibility.
- Add or update tests and Storybook stories if the repo supports them.
- Run typecheck, lint, tests, and build when relevant.

Before coding:
1. Inspect package.json.
2. Inspect existing components.
3. Inspect styling and theme files.
4. Identify similar screens/components.
5. Explain the implementation plan briefly.

After coding:
Summarize files changed, tokens used, states covered, accessibility notes, and checks run.
```
