# TechLead Physical Reset Cleanup

This command is the first narrow physical lifecycle cleanup path in the hub model.

Command:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-reset-cleanup \
  --repo-root {{REPO_ROOT}} \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  [--target-role python-team] \
  [--send-decision]
```

Current slice boundaries:
- `reset_required` only
- `python-team` only
- removes only the registered stale owned role worktree
- preserves the role branch
- does not recreate the worktree
- does not delete the role branch
- does not perform supersede or close cleanup

The command orchestrates:
1. `techlead-reset-required`
2. `techlead-worktree-ownership`
3. `techlead-worktree-stale`
4. `git worktree remove <worktree_path>`

Successful result fields include:
- `workflow_stage`
- `target_role`
- `canonical_branch`
- `role_branch`
- `worktree_path`
- `cleanup_performed`
- `cleanup_result`
- `prior_worktree_ownership`
- `prior_worktree_staleness`
- `decision_result`
- `next_step_hint`

Fail-closed behavior:
- if workflow is not `dev_reset_required`
- if the target role is not `python-team`
- if the worktree is not registered
- if stale detection does not mark the worktree as a cleanup candidate
- if the owned worktree path is not the deterministic default path

In those cases the command returns a structured refusal and performs no mutation.
