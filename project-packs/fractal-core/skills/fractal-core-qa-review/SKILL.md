---
name: fractal-core-qa-review
description: Compile and hand off a QA verification packet using repo-local PAA tooling.
---

Compile via repo-local producer runtime installed in the repo:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-producer authority materialize-qa-verification-packet \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --repo {{REPO_ROOT}} \
  --issue-number <issue_number> \
  --issue-url <issue_url> \
  --pr-number <pr_number> \
  --pr-url <pr_url> \
  --branch <branch_name> \
  --qa-input-file <qa_input_json> \
  --persist-db
```
