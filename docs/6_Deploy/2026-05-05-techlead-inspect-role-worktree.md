## Purpose

Add the first narrow receive-side companion flow for a prepared role worktree.

This slice intentionally does only three things:
- inspect the prepared worktree context
- confirm the expected role branch is checked out there
- point the role at the emitted assignment artifact

It does **not**:
- run implementation work
- run QA work
- mutate branches or worktrees
- infer broader workflow transitions

## Command

```bash
<consumer_repo>/.codex/paa/bin/paa-consumer techlead-inspect-role-worktree \
  --repo-root <consumer_repo> \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role <python-team|qa>
```

Optional overrides:
- `--role-branch`
- `--worktree-path`
- `--assignment-path`
- `--review-output`

## Behavior

The command:
1. derives lineage from `techlead-lineage`
2. resolves the expected role branch
3. verifies a registered worktree exists for that role branch
4. loads the emitted assignment artifact
5. returns a normalized receive-side context for the role

## Output highlights

The response includes:
- `worktree_path`
- `current_branch`
- `assignment_artifact.path`
- `assignment_artifact.review_output_path`
- `assignment_type`
- `assignment_summary`
- `allowed_result_types`

## Current non-goals

This slice does not attempt to:
- auto-claim queue messages
- execute role work
- rewrite branches
- create worktrees if they do not already exist
