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

Operator-facing dispatch path:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-validate-packet --message-file <packet.json>
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-send-packet --repo-root {{REPO_ROOT}} --message-file <packet.json>
```

Supported Phase C emission path:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-emit-next-assignment \
  --repo-root {{REPO_ROOT}} \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  [--send]
```

Initial supported cases:
- `techlead_dev_review_pending` -> emit assignment to `QA`
- explicit `--target-role python-team` invocation -> emit assignment to `Python Dev`

Supported branch-aware decision path:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-emit-decision \
  --repo-root {{REPO_ROOT}} \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --decision-type <reset_required|superseded|closed> \
  [--send]
```

Initial supported decision cases:
- `reset_required`
- `superseded`
- `closed`

Dedicated lineage query path:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-lineage \
  --repo-root {{REPO_ROOT}} \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external>
```

Narrow branch mutation path:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-prepare-role-branch \
  --repo-root {{REPO_ROOT}} \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role <python-team|qa> \
  --action <ensure|reset>
```

Use `techlead-lineage` as the required precursor to `techlead-prepare-role-branch`.
This slice is limited to role-branch creation/reset only. Do not assume worktree creation or cleanup is automatic yet.

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-status --validate-schema --output {{REPO_ROOT}}/.project/data/paa/reports/techlead-status-report.json
```
