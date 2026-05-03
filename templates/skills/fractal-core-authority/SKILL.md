---
name: fractal-core-authority
description: Repo-local authority and packet compilation commands for producer or consumer repos using installed PAA runtime.
---

Use repo-local producer tooling:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-producer authority summary
{{REPO_ROOT}}/.codex/paa/bin/paa-producer authority current
{{REPO_ROOT}}/.codex/paa/bin/paa-producer authority task --issue-number 106
{{REPO_ROOT}}/.codex/paa/bin/paa-producer authority materialize-slice-result-packet --persist-db ...
```

Use repo-local readiness tooling:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-producer materialize-readiness --db-package-id-external <package_id_external> --db-write
```
