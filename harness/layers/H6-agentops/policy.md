# H6 AgentOps Harness Policy

Purpose: observe provider behavior and cost.

Baseline:

- record provider result
- record session id when available
- aggregate `cost_usd`
- write phase attempt logs
- write gate logs
- optionally mirror events to PostgreSQL

Future hardening:

- per-agent latency and token metrics
- drift and retry analytics
- context size metrics
- dashboard charts for H1-H7 health
