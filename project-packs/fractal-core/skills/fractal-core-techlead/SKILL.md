---
name: fractal-core-techlead
description: Generate and validate a repo-local TechLead report from installed authority and queue/runtime state.
---

TechLead owns the consumer-side routing decision in Phase A:
- review Dev result packets routed to TechLead
- review QA verification packets routed to TechLead
- determine the next recommended route without emitting a new assignment packet yet

Phase B adds first-class TechLead packet artifacts:
- `techlead_assignment_packet` records the issued next assignment and target role
- `techlead_decision_packet` records the durable routing, pause, reset, merge-prep, or escalation decision
- keep assignment sending operator-invoked in this phase; do not assume auto-dispatch

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-status --validate-schema --output {{REPO_ROOT}}/.project/data/paa/reports/techlead-status-report.json
```
