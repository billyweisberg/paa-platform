---
name: fractal-core-qa-review
description: Compile and hand off a QA verification packet using repo-local PAA tooling.
---

Branch policy:
- Use the same shared full-cycle issue branch used by Delivery Architect and Dev: `issue-<issue_number>`.
- Do not invent a separate QA branch.

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
  --branch issue-<issue_number> \
  --qa-input-file <qa_input_json> \
  --persist-db
```
