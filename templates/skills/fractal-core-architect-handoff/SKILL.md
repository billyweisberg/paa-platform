---
name: fractal-core-architect-handoff
description: Send the next architect cycle packet using repo-local PAA tooling.
---

```bash
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
```

This command now performs producer-side source-to-PAA sync for the target next issue before resolving the design package and coder brief. Use `--skip-source-sync` only for debugging or controlled recovery work.
