---
name: fractal-core-architect-handoff
description: Send the next architect cycle packet using repo-local PAA tooling.
---

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-producer authority materialize-architect-packet --persist-db ...
```

This command now performs producer-side source-to-PAA sync for the target next issue before resolving the design package and coder brief. Use `--skip-source-sync` only for debugging or controlled recovery work.
