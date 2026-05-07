# Phase H2 Worktree Stale Detection Validation

## Goal

Validate the narrow stale-worktree detection slice on top of Phase H1 ownership reporting.

This slice should:
- make obvious stale conditions queryable
- remain conservative
- avoid cleanup mutation

## Commands used

Consumer repo:
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python`

### 1. Refresh installed consumer runtime

```bash
./.codex/paa/bin/paa-consumer update-consumer-runtime \
  --repo-root /Users/billyweisberg/Repos/billyweisberg/fractal-core-python
```

Observed result:
- `ok = true`

### 2. Query stale status for an unprepared deterministic role worktree

```bash
./.codex/paa/bin/paa-consumer techlead-worktree-stale \
  --repo-root /Users/billyweisberg/Repos/billyweisberg/fractal-core-python \
  --package-id-external fcore-stage1-2026-05-02-issue106-retirement-boundary-diagnostics \
  --brief-id-external fcore-coder-2026-05-02-issue106-retirement-boundary-diagnostics \
  --target-role qa
```

Observed result:
- `ok = true`
- `worktree_staleness.status = absent`
- `worktree_staleness.stale = false`
- `worktree_staleness.cleanup_candidate = false`
- `worktree_staleness.recommended_action = prepare_or_reuse_worktree_when_role_runs`

This is the correct conservative result for a role worktree that is defined deterministically but not currently prepared.

### 3. Validate TechLead status schema still passes

```bash
./.codex/paa/bin/paa-consumer techlead-status --validate-schema
```

Observed result:
- command succeeded
- lineage schema accepted the new `worktree_staleness` field

### 4. Verify command discovery

```bash
./.codex/paa/bin/paa-consumer help
```

Observed result:
- `techlead-worktree-stale` appears in the top-level command list

## Conclusion

The stale-worktree detection slice is working as intended:
- worktree stale state is queryable
- absence is not misclassified as stale
- the result is conservative and cleanup-free
