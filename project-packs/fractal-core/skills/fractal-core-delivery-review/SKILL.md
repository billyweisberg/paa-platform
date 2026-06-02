---
name: fractal-core-delivery-review
description: Deprecated legacy role-worktree skill. Use the unified PAA runtime/queue CLI instead.
---

Deprecated:
- the old `techlead.py` role-worktree commands referenced by this skill were removed from the user-facing CLI
- do not use historical `paa-consumer techlead-*` examples

Current supported operator path:

```bash
{{REPO_ROOT}}/.codex/paa/scripts/runtime/run_automation_preflight_with_logging.sh \
  --repo-root {{REPO_ROOT}} \
  --automation-id fractal-core-delivery-architect-automation \
  --role-key delivery-architect \
  --role-display-name "Delivery Architect" \
  --target-role delivery-architect \
  --phase preflight

{{REPO_ROOT}}/.codex/paa/bin/paa queue check --repo-root {{REPO_ROOT}} --queue fractal-core-architecture
{{REPO_ROOT}}/.codex/paa/bin/paa queue claim-next --repo-root {{REPO_ROOT}} --queue fractal-core-architecture
{{REPO_ROOT}}/.codex/paa/bin/paa queue ack --repo-root {{REPO_ROOT}} --claim-id <claim_id>
```
