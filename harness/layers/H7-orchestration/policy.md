# H7 Orchestration Harness Policy

Purpose: drive the SDLC flow with resumable phase orchestration.

Modes:

- Expanded mode: harness owns every OKR phase and gate.
- Boss mode: harness delegates the full inner flow to `okr.bossbuiltin` and gates final artifacts.

Recommended default:

- Use expanded mode for production visibility.
- Use boss mode for initial compatibility or exploratory runs.

Implementation hooks:

- `packages/ai-harness/src/orchestration/orchestrator.py`
- `packages/ai-harness/targets/okr-ghcp/harness.okr.yaml`
- `packages/ai-harness/targets/okr-ghcp/harness.okr.boss.yaml`
