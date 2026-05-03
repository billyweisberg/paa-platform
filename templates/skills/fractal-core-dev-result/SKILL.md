---
name: fractal-core-dev-result
description: Compile and hand off a Dev slice result packet using repo-local PAA tooling.
---

Compile via repo-local producer runtime installed in the repo:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-producer authority materialize-slice-result-packet --persist-db ...
```
