---
name: fractal-core-qa-review
description: Deprecated legacy role-worktree skill. Use the unified PAA runtime/queue CLI instead.
---

Deprecated:
- the old `techlead.py` role-worktree commands referenced by this skill were removed from the user-facing CLI
- do not use historical `paa-consumer techlead-*` examples

Current supported operator path:

```bash
{{REPO_ROOT}}/.codex/paa/scripts/runtime/run_automation_preflight_with_logging.sh \
  --repo-root {{REPO_ROOT}} \
  --automation-id fractal-core-qa-automation \
  --role-key qa \
  --role-display-name "QA" \
  --target-role qa \
  --phase preflight

{{REPO_ROOT}}/.codex/paa/bin/paa runtime qa --repo-root {{REPO_ROOT}} --intake-mode claim_next --emit-verification
{{REPO_ROOT}}/.codex/paa/bin/paa queue check --repo-root {{REPO_ROOT}} --queue fractal-core-qa
{{REPO_ROOT}}/.codex/paa/bin/paa queue claim-next --repo-root {{REPO_ROOT}} --queue fractal-core-qa
{{REPO_ROOT}}/.codex/paa/bin/paa queue ack --repo-root {{REPO_ROOT}} --claim-id <claim_id>
```
