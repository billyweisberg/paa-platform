## Purpose

Add the first narrow role-side entry helper on top of the receive-side worktree inspection flow.

This slice intentionally does only four things:
- read the inspected worktree context
- verify branch and assignment artifact alignment
- print the exact next manual execution surfaces
- stop before compiling Dev or QA result packets

## Command

```bash
<consumer_repo>/.codex/paa/bin/paa-consumer techlead-role-entry \
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

The command builds on `techlead-inspect-role-worktree`.

If the inspection is valid, it returns:
- worktree path
- branch alignment
- assignment artifact paths
- exact manual next commands

## Exact manual execution surfaces

The output includes:
- `enter_worktree_command`
- `assignment_json_command`
- `assignment_review_command`
- `result_compile_command`

Important:
- role work still happens in the prepared worktree
- packet compilation still uses the installed repo-root runtime wrappers
- this slice does not execute those commands automatically
