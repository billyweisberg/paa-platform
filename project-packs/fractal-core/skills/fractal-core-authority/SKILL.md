---
name: fractal-core-authority
description: Repo-local authority and packet compilation commands for producer or consumer repos using installed PAA runtime.
---

Branch policy for the full implementation cycle:
- Use one shared branch per issue: `issue-<issue_number>`.
- Do not invent role-specific or random branch names.
- Delivery Architect, Dev, and QA all work on the same issue branch for that issue.

Use repo-local authority inspection on any repo with installed PAA runtime:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-producer authority summary
{{REPO_ROOT}}/.codex/paa/bin/paa-producer authority current
```

Use repo-local producer tooling only in the canonical producer repo:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-producer authority task --issue-number 106
{{REPO_ROOT}}/.codex/paa/bin/paa-producer authority materialize-architect-packet \
  --package-id-external <package_id_external> \
  --repo <consumer_repo_root> \
  --accepted-pr-number <accepted_pr_number> \
  --accepted-pr-url <accepted_pr_url> \
  --closed-issue-number <closed_issue_number> \
  --closed-issue-url <closed_issue_url> \
  --next-issue-number <next_issue_number> \
  --next-issue-url <next_issue_url> \
  --baseline-file <baseline_json> \
  --persist-db
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

For legacy compatibility only, `materialize-slice-result-packet` still exists.
Do not treat it as the active Python bridge default.

Do not emit producer packets from a consumer repo. On consumer repos, use authority inspection plus `paa-consumer` queue and TechLead commands instead.

Use repo-local readiness tooling:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-producer materialize-readiness --db-package-id-external <package_id_external> --db-write
```
