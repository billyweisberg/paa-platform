# TechLead Closed Cleanup

This command is the first terminal-state physical lifecycle cleanup path.

Command:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-closed-cleanup \
  --repo-root {{REPO_ROOT}} \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  [--target-role python-team] \
  [--send-decision]
```

Current slice boundaries:
- `closed` only
- `python-team` only
- removes only the registered stale owned role worktree
- preserves the role branch
- preserves the canonical branch
- does not recreate the worktree
- does not delete branches

The command orchestrates:
1. lineage query
2. `techlead-worktree-ownership`
3. `techlead-worktree-stale`
4. `techlead-emit-decision --decision-type closed`
5. `git worktree remove <worktree_path>`

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
- if lineage state is not `closed`
- if the target role is not `python-team`
- if the worktree is not registered
- if stale detection does not mark the worktree as a cleanup candidate
- if the owned worktree path is not the deterministic default path

In those cases the command returns a structured refusal and performs no mutation.
