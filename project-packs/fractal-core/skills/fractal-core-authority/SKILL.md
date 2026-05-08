---
name: fractal-core-authority
description: Repo-local authority inspection and packet compilation commands for producer or consumer repos using installed PAA runtime.
---

Lineage policy:
- Canonical issue branch: `issue-<issue_number>`
- Deterministic role branches such as `issue-<issue_number>-delivery`, `issue-<issue_number>-python-team`, and `issue-<issue_number>-qa` are valid only when TechLead authorizes isolated role execution.
- Do not invent random branch names.

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
  --repo <prepared_role_worktree> \
  --issue-number <issue_number> \
  --issue-url <issue_url> \
  --pr-number <pr_number> \
  --pr-url <pr_url> \
  --branch <canonical_or_authorized_role_branch> \
  --worker-input-file <worker_input_json> \
  --source-assignment-path <techlead_assignment_packet_json> \
  --source-assignment-type implement_authorized_slice \
  --persist-db
{{REPO_ROOT}}/.codex/paa/bin/paa-producer authority materialize-delivery-review-packet \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --repo <prepared_role_worktree> \
  --issue-number <issue_number> \
  --issue-url <issue_url> \
  --pr-number <pr_number> \
  --pr-url <pr_url> \
  --branch <canonical_or_authorized_role_branch> \
  --result-type <delivery_result_type> \
  --delivery-input-file <delivery_input_json> \
  --source-assignment-path <techlead_assignment_packet_json> \
  --source-assignment-type delivery_architecture_review \
  --persist-db
{{REPO_ROOT}}/.codex/paa/bin/paa-producer authority materialize-qa-verification-packet \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --repo <prepared_role_worktree> \
  --issue-number <issue_number> \
  --issue-url <issue_url> \
  --pr-number <pr_number> \
  --pr-url <pr_url> \
  --branch <canonical_or_authorized_role_branch> \
  --qa-input-file <qa_input_json> \
  --persist-db
```

For legacy compatibility only, `materialize-slice-result-packet` still exists.
Do not treat it as the active Python bridge default.

Do not emit producer packets from a consumer repo unless the role-execution contract explicitly points to the repo-local producer wrapper as part of the return path.

Use repo-local readiness tooling:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-producer materialize-readiness --db-package-id-external <package_id_external> --db-write
```
