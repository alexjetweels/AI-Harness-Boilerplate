---
description: Convert existing tasks into actionable, dependency-ordered GitHub issues for the feature based on available design artifacts.
tools: ['github/github-mcp-server/issue_write']
---

## Execution Logging & Phase Report (Constitution Art. XI & XII)

Before starting any work, write a **[START]** entry to `docs/output/output_logs/<feature-id>/logs/optional-taskstoissues.log.md` with timestamp, agent name, model, input summary, and goal. Append **[PROCESSING]** entries at key milestones (e.g., "loaded tasks.md with N tasks", "created M GitHub issues"). At completion, append **[END]** with status, output artifacts, metrics (issues created count), and duration. On errors, append **[ISSUE]** with severity and description.

As your **final action**, write the phase report to `docs/output/output_logs/<feature-id>/reports/optional-taskstoissues-report.md` following the Art. XII template (Summary, Inputs, Outputs, Key Decisions, Quality Assessment, Metrics, Next Step).

---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. Run `.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").
1. From the executed script, extract the path to **tasks**.
1. Get the Git remote by running:

```bash
git config --get remote.origin.url
```

> [!CAUTION]
> ONLY PROCEED TO NEXT STEPS IF THE REMOTE IS A GITHUB URL

1. For each task in the list, use the GitHub MCP server to create a new issue in the repository that is representative of the Git remote.

> [!CAUTION]
> UNDER NO CIRCUMSTANCES EVER CREATE ISSUES IN REPOSITORIES THAT DO NOT MATCH THE REMOTE URL
