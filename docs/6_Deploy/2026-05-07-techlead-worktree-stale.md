# TechLead Worktree Stale Detection

## Purpose

Add one narrow stale-worktree detection surface on top of the Phase H1 ownership model.

This slice does **not** clean up or mutate worktrees.
It only makes obvious stale conditions queryable before later lifecycle automation begins.

## Command

```bash
<consumer_repo>/.codex/paa/bin/paa-consumer techlead-worktree-stale \
  --repo-root <consumer_repo> \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role <delivery-architect|python-team|qa>
```

Optional overrides:
- `--role-branch`
- `--worktree-path`

## Conservative stale rules in this slice

A role worktree is marked stale only when one of these is true:
- the worktree is registered but checked out on the wrong branch
- the lineage state is:
  - `reset_required`
  - `superseded`
  - `closed`

A role worktree is **not** marked stale just because:
- it exists while another role is currently active
- it uses the deterministic role branch while the slice is still active
- it is absent and has not been prepared yet

## Output

The command returns:
- `worktree_ownership`
- `worktree_staleness`
- linked `lineage_view`

The `worktree_staleness` object contains:
- `status`
- `stale`
- `cleanup_candidate`
- `reasons`
- `warnings`
- `recommended_action`

## Why this is the right boundary

This keeps stale detection explainable and safe.

It does not guess from soft signals like “wrong current owner role” or “this worktree exists longer than expected.”
Those may matter later, but they are not strong enough for cleanup automation yet.
