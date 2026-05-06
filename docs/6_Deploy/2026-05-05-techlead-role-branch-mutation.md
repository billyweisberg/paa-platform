## Purpose

Add one narrow branch-mutation surface on top of `techlead-lineage` without jumping ahead to full worktree or lifecycle cleanup automation.

This slice is intentionally limited to:
- role-branch creation
- role-branch reset back to the canonical issue branch

It does **not** automate:
- worktree creation
- worktree cleanup
- branch deletion
- supersede/close cleanup

## Command

```bash
<consumer_repo>/.codex/paa/bin/paa-consumer techlead-prepare-role-branch \
  --repo-root <consumer_repo> \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role <python-team|qa> \
  --action <ensure|reset>
```

Optional overrides:
- `--canonical-branch`
- `--role-branch`

## Required precursor

`techlead-prepare-role-branch` must derive its context from `techlead-lineage`.

If the lineage view is ambiguous, the command fails closed instead of guessing branch state.

## Behavior

### `--action ensure`

- create the role branch if it does not exist
- source it from the resolved canonical branch
- do not rewrite an existing role branch that points somewhere else
- if the role branch already exists at a different tip, fail closed and require `--action reset`

### `--action reset`

- force the role branch back to the resolved canonical branch tip
- fail closed if the role branch is checked out in an active worktree

## Canonical branch resolution

For mutation purposes, the runtime prefers:
1. explicit `--canonical-branch`
2. local or remote `issue-<issue_number>` if present
3. canonical branch from the lineage helper

This lets the mutation path align to the declared issue-branch policy even when historical PR context still exposes older branch names.

## Current scope

Supported target roles:
- `python-team`
- `qa`

The output reports:
- canonical branch
- canonical source ref and commit
- role branch
- whether the branch was created or reset
- whether any worktree currently has the role branch checked out
