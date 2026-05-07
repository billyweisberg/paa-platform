---
name: fractal-core-dev-result
description: Compile and hand off a Python worker result packet using repo-local PAA tooling.
---

Branch policy:
- Use the shared full-cycle issue branch: `issue-<issue_number>`.
- Do not create role-specific branch names for Dev work.

Routing policy:
- Dev returns the result packet to TechLead.
- Dev does not route directly to QA.
- The active Python lane now uses `worker_result_packet`.
- `slice_result_packet` remains legacy-compatible only.

Compile via repo-local producer runtime installed in the repo:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-producer authority materialize-worker-result-packet \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --worker-role python-team \
  --worker-family implementation \
  --result-type <worker_result_type> \
  --repo {{REPO_ROOT}} \
  --issue-number <issue_number> \
  --issue-url <issue_url> \
  --pr-number <pr_number> \
  --pr-url <pr_url> \
  --branch issue-<issue_number> \
  --worker-input-file <worker_input_json> \
  --source-assignment-path <techlead_assignment_packet_json> \
  --source-assignment-type implement_authorized_slice \
  --persist-db
```
