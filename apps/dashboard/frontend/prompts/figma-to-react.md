# Prompt: Figma/Design Brief to React

```text
Convert this design brief/Figma description into React UI.

Inputs:
- Design brief: [PASTE]
- Target route/component: [TARGET]
- Existing design tokens: use `design-tokens/tokens.css` or repo theme.

Instructions:
- Inspect existing components first.
- Map design decisions to tokens.
- Do not hardcode visual values unless no token exists.
- Keep UI responsive.
- Include accessible labels and keyboard behavior.
- Include real product states: loading, empty, error, disabled.
- Avoid generic AI SaaS styling.
- If the design is vague, make conservative choices aligned with Material Design-style foundations.

Output:
- Implementation plan.
- Code changes.
- Tests/stories if applicable.
- Summary of token usage and accessibility.
```
