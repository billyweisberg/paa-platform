# Canonical Branch Freshness Validation

Date:
- `2026-05-12`

## Purpose

Validate that role-branch preparation now prefers the remote canonical branch tip rather than a stale local canonical branch.

This hardening was added because the QA pilot leg had to manually fast-forward a stale local `issue-108` branch before verification.

## Validation

Command:

```bash
/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-consumer techlead-prepare-role-branch \
  --repo-root /Users/billyweisberg/Repos/billyweisberg/fractal-core-python \
  --package-id-external fcore-stagew7-2026-05-10-issue108-team-worker-automation-runtime-note \
  --brief-id-external fcore-coder-2026-05-10-issue108-team-worker-automation-runtime-note \
  --target-role qa \
  --action ensure
```

Observed result:

- `ok = true`
- `canonical_branch = issue-108`
- `canonical_source_ref = origin/issue-108`
- `canonical_source_commit = 7e2b98e0e56e8e38d41ba8032a006fb00bbd08f9`
- existing role branch:
  - `issue-108-qa`
- branch tip already aligned to the remote canonical source commit

## Conclusion

Role-branch preparation no longer prefers a stale local canonical branch when the remote canonical branch is available.

This addresses the low-severity QA finding from the pilot:

- future deterministic role worktrees should derive from the actual remote PR head by default
