---
name: fractal-core-dev-result
description: Compile and hand off a Dev slice result packet using repo-local PAA tooling.
---

Branch policy:
- Use the shared full-cycle issue branch: `issue-<issue_number>`.
- Do not create role-specific branch names for Dev work.

Compile via repo-local producer runtime installed in the repo:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-producer authority materialize-slice-result-packet \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --repo {{REPO_ROOT}} \
  --issue-number <issue_number> \
  --issue-url <issue_url> \
  --pr-number <pr_number> \
  --pr-url <pr_url> \
  --branch issue-<issue_number> \
  --dev-input-file <dev_input_json> \
  --persist-db
```
