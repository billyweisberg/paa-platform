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

Narrow role-worktree path:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-prepare-role-worktree \
  --repo-root {{REPO_ROOT}} \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role <python-team|qa> \
  [--branch-action <ensure|reset>]
```

Use `techlead-lineage` first, then `techlead-prepare-role-branch`, then `techlead-prepare-role-worktree`.
This slice only creates or reuses a role worktree from a prepared role branch. Do not assume lifecycle cleanup is automatic yet.

Narrow TechLead handoff path:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-handoff-to-role-worktree \
  --repo-root {{REPO_ROOT}} \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  [--target-role <python-team|qa>] \
  [--send]
```

This path is intentionally narrow:
- emit the assignment packet
- prepare the role branch
- prepare the role worktree
- stop before role execution

Receive-side role-worktree inspection:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-inspect-role-worktree \
  --repo-root {{REPO_ROOT}} \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role <python-team|qa>
```

This path is intentionally narrow:
- inspect the prepared worktree context
- point the role at the emitted assignment artifact
- stop before role execution

Role-side entry helper:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-role-entry \
  --repo-root {{REPO_ROOT}} \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role <python-team|qa>
```

This path is intentionally narrow:
- read the inspected worktree context
- verify branch and assignment artifact alignment
- print the exact next manual execution surfaces
- stop before compiling Dev or QA result packets

Role-side result assist helper:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-role-result-assist \
  --repo-root {{REPO_ROOT}} \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role <python-team|qa>
```

This path is intentionally narrow:
- consume the role-entry context
- validate the required result-packet context
- print the exact result compile surfaces
- stop before compiling or sending the result packet

Role-side return bridge:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-role-return \
  --repo-root {{REPO_ROOT}} \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role <python-team|qa> \
  [--send]
```

This path is intentionally narrow:
- consume the role-result-assist context
- compile the role result packet
- validate the compiled packet and resolve the queue
- optionally send it back toward `TechLead`

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-status --validate-schema --output {{REPO_ROOT}}/.project/data/paa/reports/techlead-status-report.json
```
