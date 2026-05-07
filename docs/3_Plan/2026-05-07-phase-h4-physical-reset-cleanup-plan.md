# Phase H4 Mini Plan: Physical Reset Cleanup

## Summary

Implement the first physical cleanup slice on top of the proven Phase H3 `reset_required` lifecycle mutation.

Chosen scope:
- `reset_required` only
- `python-team` only
- operate only on the affected role execution surface
- no supersede cleanup
- no close cleanup
- no broad retirement policy

The goal is to safely retire the stale Python role execution surface after `reset_required` has already been recorded, while preserving evidence and avoiding destructive branch deletion.

## Why this slice is next

Phase H3 proved that we can:
- detect reset-required state
- record the lifecycle mutation
- mark the execution surface as a cleanup candidate

What is still missing is the first physical action that follows from that state.

This slice should be the minimum physical cleanup needed to move from:
- "the worktree is known-bad"

to:
- "the worktree is retired and a clean next execution surface can be prepared later"

## Scope boundaries

### Included
- remove a stale registered role worktree for `python-team`
- preserve the role branch ref for audit/recovery in this slice
- return a structured cleanup record

### Not included
- deleting the role branch
- recreating the role worktree automatically
- superseded cleanup
- closed cleanup
- multi-role cleanup
- broad stale-branch retirement policy

## Safety model

This slice must fail closed unless all of the following are true:
- lifecycle state is `reset_required`
- target role is `python-team`
- worktree ownership resolves successfully
- stale-worktree assessment returns:
  - `stale = true`
  - `cleanup_candidate = true`
- the worktree is currently registered
- the worktree path matches the expected owned worktree path

If any of those are false:
- do not mutate anything
- return a structured refusal

## Implementation shape

### 1. Add one cleanup command

```bash
<consumer_repo>/.codex/paa/bin/paa-consumer techlead-reset-cleanup \
  --repo-root <consumer_repo> \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  [--target-role python-team]
```

### 2. What the command does

The command should orchestrate these existing surfaces:
1. `techlead-reset-required`
2. `techlead-worktree-ownership`
3. `techlead-worktree-stale`

Then, if the mutation state is valid:
4. remove the registered stale role worktree
5. confirm the worktree is no longer registered
6. return a structured cleanup result

### 3. Physical action in this slice

The physical action should be limited to:
- `git worktree remove <worktree_path>`

Do not:
- delete the role branch
- force-delete an occupied or ambiguous worktree
- mutate the canonical branch

### 4. Evidence preservation

This slice should preserve enough evidence to explain what happened:
- canonical branch
- affected role branch
- removed worktree path
- prior ownership view
- prior stale assessment
- source reset-required decision record

This can be returned as structured JSON in the command result for now.
A later slice can decide whether additional durable cleanup artifacts are needed.

## Expected outputs

The command should return:
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

Successful cleanup should indicate:
- worktree removed
- branch preserved
- role execution surface retired

## Explicit non-goals

Do not include in this slice:
- branch deletion
- automatic fresh worktree preparation
- automatic fresh role branch preparation
- cross-role cleanup
- supersede handling
- close handling

## Test plan

### Static checks
- command appears in `paa-consumer help`
- runtime compiles
- `techlead-status --validate-schema` still passes

### Positive-path validation
Use a disposable synthetic `dev_reset_required` fixture and a disposable registered role worktree.

Prove that:
- the command removes the registered role worktree
- the branch remains present
- the result is structured and auditable

### Fail-closed validation
Prove that cleanup is refused when:
- workflow is not `dev_reset_required`
- no registered worktree exists
- target role is unsupported
- stale assessment is not cleanup-candidate

## Acceptance criteria

This slice is done when:
- a reset-required role worktree can be physically retired in one narrow command
- the role branch is preserved
- cleanup is fail-closed and evidence-preserving
- no supersede/close logic leaks into the implementation
