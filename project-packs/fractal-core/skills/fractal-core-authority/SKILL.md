---
name: fractal-core-authority
description: Repo-local authority and packet compilation commands for producer or consumer repos using installed PAA runtime.
---

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
{{REPO_ROOT}}/.codex/paa/bin/paa-producer authority materialize-slice-result-packet \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --repo {{REPO_ROOT}} \
  --issue-number <issue_number> \
  --issue-url <issue_url> \
  --pr-number <pr_number> \
  --pr-url <pr_url> \
  --branch <branch_name> \
  --dev-input-file <dev_input_json> \
  --persist-db
```

Do not emit producer packets from a consumer repo. On consumer repos, use authority inspection plus `paa-consumer` queue and TechLead commands instead.

Use repo-local readiness tooling:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-producer materialize-readiness --db-package-id-external <package_id_external> --db-write
```
