---
name: fractal-core-qa-review
description: Compile and hand off a QA verification packet using repo-local PAA tooling.
---

Compile via repo-local producer runtime installed in the repo:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-producer authority materialize-qa-verification-packet --persist-db ...
```
