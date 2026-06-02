---
name: fractal-core-techlead
description: Use the unified PAA queue and runtime CLI for TechLead-side packet validation, dispatch, and host execution.
---

Supported operator path:

```bash
{{REPO_ROOT}}/.codex/paa/scripts/runtime/run_automation_preflight_with_logging.sh \
  --repo-root {{REPO_ROOT}} \
  --automation-id fractal-core-techlead-automation \
  --role-key techlead \
  --role-display-name "TechLead" \
  --target-role techlead \
  --phase preflight

{{REPO_ROOT}}/.codex/paa/bin/paa queue validate-packet --repo-root {{REPO_ROOT}} --message-file <packet.json>
{{REPO_ROOT}}/.codex/paa/bin/paa queue send-packet --repo-root {{REPO_ROOT}} --message-file <packet.json>
{{REPO_ROOT}}/.codex/paa/bin/paa runtime techlead --repo-root {{REPO_ROOT}} --intake-mode claim_next --emit-next-assignment
{{REPO_ROOT}}/.codex/paa/bin/paa report techlead-service-map
```

Notes:
- the old `paa-consumer techlead-*` shell commands are removed
- use `paa runtime techlead` for host execution
- use `paa queue *` for packet validation, sending, and claim lifecycle
