# Auto-Resolve Protocol (No-Pause Mode)

When any `[NEEDS CLARIFICATION]` marker or ambiguity is encountered at any step:

## Rule: Auto-Resolve with Optimal Assumption

1. **Identify** every `[NEEDS CLARIFICATION]` marker or ambiguous item.
2. **Evaluate** the best answer based on:
   - Context from the SRS document
   - Common engineering best practices for domain
   - Conservative, safe defaults (prefer explicit over implicit, standard over custom)
   - Existing patterns in the codebase (`src/modules/`)
3. **Choose** the optimal assumption and record it with rationale.
4. **Encode** the assumption directly into the document (replace marker with the resolved value).
5. **Report** every resolved item in the `## [AUTO-RESOLVED] Assumptions` section of the phase report.

## Auto-Resolved Assumptions Report Format

Every phase report MUST include:

```markdown
## [AUTO-RESOLVED] Assumptions

| # | ID | Original Question | Auto-Answer | Rationale | Confidence |
|---|----|-------------------|-------------|-----------|------------|
| 1 | TBC-01 | <original question text> | <chosen answer> | <why this was chosen> | High/Med/Low |

> ⚠  User Review Recommended: Items with Confidence=Low should be verified by the user at their convenience.
```

## Confidence Levels

- **High** — answer derived directly from SRS or existing codebase pattern, highly certain
- **Med** — answer based on best practice and domain knowledge, likely correct
- **Low** — answer is a reasonable guess; user should verify when convenient (pipeline continues)
