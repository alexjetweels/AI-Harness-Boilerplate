# Timestamp Protocol — MANDATORY

Every `Timestamp:` field in the boss log MUST use the real system clock.

## How to get the real timestamp

**ALWAYS** run via the `run` tool immediately before writing any boss log entry:

```powershell
Get-Date -Format "yyyy-MM-dd HH:mm:ss"
```

Use the exact output as the `Timestamp:` value. **Never hardcode, estimate, or pre-calculate.**

## Incremental Writing Rule — ⛔ STRICTLY ENFORCED

```
BEFORE delegating to agent N:
    1. Run: Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    2. Append [PROCESSING] STEP N entry to boss log
    3. Delegate to agent N

AFTER agent N returns:
    4. Run: Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    5. Append [PROCESSING] STEP N — COMPLETE entry
    6. Proceed to gate check
```

**⛔ PROHIBITED:** Pre-writing multiple future step entries or writing the full boss log in one batch.
