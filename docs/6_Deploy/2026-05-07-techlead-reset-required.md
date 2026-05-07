# TechLead Reset-Required Lifecycle Mutation

## Purpose

Add the first cleanup-safe lifecycle mutation surface in Phase H3.

This command:
- reuses lineage
- reuses worktree ownership
- reuses stale-worktree detection
- reuses the existing `reset_required` TechLead decision path

It does **not**:
- delete branches
- delete worktrees
- recreate worktrees
- perform physical cleanup

## Command

```bash
<consumer_repo>/.codex/paa/bin/paa-consumer techlead-reset-required \
  --repo-root <consumer_repo> \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  [--target-role python-team] \
  [--send-decision]
```

Optional overrides:
- `--role-branch`
- `--worktree-path`
- `--source-packet-path`
- `--canonical-branch`
- `--superseded-branch`
- `--worktree-hint`
- `--reset-reason`
- `--output`
- `--review-output`

## Scope in this slice

Supported role target:
- `python-team` only

Supported lifecycle state:
- `dev_reset_required` only

## Output

The command returns:
- `workflow_stage`
- `target_role`
- `canonical_branch`
- `role_branch`
- `worktree_path`
- `worktree_ownership`
- `worktree_staleness`
- `decision_result`
- `cleanup_candidate`
- `next_step_hint`

## Contract

This is a lifecycle mutation planning and recording surface.

It is intentionally narrow:
- if reset-required is not actually supported by the current runtime state, it fails closed
- if ownership/staleness cannot be resolved, it fails closed
- if the target role is not `python-team`, it fails closed

## Why this boundary matters

This slice gives the system one explicit way to say:
- this role execution surface is no longer safe to continue in place
- the stale/cleanup-candidate status is now queryable
- later cleanup automation can act on that state without rediscovering it
