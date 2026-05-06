## Purpose

Add one narrow worktree-aware companion command on top of `techlead-lineage` and `techlead-prepare-role-branch`.

This slice is intentionally limited to:
- create a role worktree from a prepared role branch
- reuse an existing role worktree for that role branch

It does **not** automate:
- worktree cleanup
- worktree deletion
- branch deletion
- full lifecycle reset or supersede cleanup

## Command

```bash
<consumer_repo>/.codex/paa/bin/paa-consumer techlead-prepare-role-worktree \
  --repo-root <consumer_repo> \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role <python-team|qa> \
  [--branch-action <ensure|reset>]
```

Optional overrides:
- `--canonical-branch`
- `--role-branch`
- `--worktree-path`

## Required precursor

`techlead-prepare-role-worktree` must derive its context from `techlead-lineage`.

It then uses `techlead-prepare-role-branch` semantics internally before any worktree action happens.

If the lineage view is ambiguous, branch preparation fails, or the worktree path is already occupied by something incompatible, the command fails closed.

## Default path

By default, worktrees are created under:

- `~/.codex/worktrees/paa/<repo_name>/<role_branch>`

This keeps the worktree location deterministic and avoids inventing ad hoc sibling clones.

## Behavior

### Reuse

If the role branch is already checked out in an active worktree:
- reuse that existing worktree
- do not create another one for the same branch

### Create

If the role branch is not checked out anywhere:
- prepare the role branch first
- create a worktree at the requested or default path
- check out the prepared role branch there

## Current scope

Supported target roles:
- `python-team`
- `qa`

The output reports:
- the prepared role-branch result
- worktree path
- whether the worktree was created or reused
- the branch checked out in that worktree
