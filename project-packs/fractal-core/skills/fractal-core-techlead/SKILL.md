---
name: fractal-core-techlead
description: Generate and validate a repo-local TechLead report from installed authority and queue/runtime state.
---

TechLead owns the consumer-side routing decision in Phase A:
- review Dev result packets routed to TechLead
- review QA verification packets routed to TechLead
- determine the next recommended route without emitting a new assignment packet yet

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-status --validate-schema --output {{REPO_ROOT}}/.project/data/paa/reports/techlead-status-report.json
```
