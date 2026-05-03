---
name: fractal-core-inbox
description: Repo-local consumer queue and claim commands for PAA handoffs.
---

Use repo-local consumer tooling:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer queue-check --repo-root {{REPO_ROOT}} --queue fractal-core-python
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer queue-claim-next --repo-root {{REPO_ROOT}} --queue fractal-core-python
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer queue-ack --repo-root {{REPO_ROOT}} --claim-id <claim_id>
```
