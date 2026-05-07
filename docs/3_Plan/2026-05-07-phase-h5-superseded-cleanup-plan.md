# Phase H5 Mini Plan: Superseded Worktree Cleanup

## Summary

Implement the next narrow lifecycle cleanup slice after Phase H4 by handling the `superseded` lineage state.

Chosen scope:
- `superseded` only
- `python-team` only
- operate only on the superseded role execution surface
- no `closed` cleanup yet
- no branch deletion
- no broad retirement policy

The goal is to safely retire a superseded Python role worktree after TechLead has already recorded the supersession decision, while preserving the superseded role branch for audit and recovery.

## Why this slice is next

Phase H4 already proved the first physical cleanup action:
- remove a stale registered role worktree
- preserve the role branch
- fail closed when lifecycle state is not eligible

`superseded` is the closest safe extension of that model because it still deals with:
- a stale execution surface
- a non-terminal lineage state
- evidence-preserving retirement

It avoids the extra policy weight of `closed`, which is closer to terminal acceptance and broader retirement semantics.

## Why `superseded` before `closed`

`closed` cleanup raises harder questions that are better deferred:
- whether the final role branch should be preserved or retired
- whether the canonical issue branch should be retained, merged, archived, or deleted
- how close-state cleanup aligns with acceptance history and PR merge state

`superseded` is narrower:
- the worktree is obsolete because lineage has moved on
- the branch can stay for audit
- the execution surface can be retired without deciding final branch-retention policy

That makes `superseded` the right next lifecycle slice.

## Scope boundaries

### Included
- remove a stale registered `python-team` role worktree when lineage state is `superseded`
- preserve the superseded role branch
- return a structured cleanup record

### Not included
- deleting the role branch
- deleting the canonical branch
- recreating a replacement worktree automatically
- `closed` cleanup
- multi-role cleanup
- broad branch retirement policy

## Safety model

This slice must fail closed unless all of the following are true:
- lifecycle state is `superseded`
- target role is `python-team`
- worktree ownership resolves successfully
- stale-worktree assessment returns:
  - `stale = true`
  - `cleanup_candidate = true`
- the worktree is currently registered
- the worktree path matches the expected owned worktree path
- the lineage view identifies a `superseded_branch`

If any of those are false:
- do not mutate anything
- return a structured refusal

## Implementation shape

### 1. Add one cleanup command

```bash
<consumer_repo>/.codex/paa/bin/paa-consumer techlead-superseded-cleanup \
  --repo-root <consumer_repo> \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  [--target-role python-team] \
  [--send-decision]
```

### 2. What the command does

The command should orchestrate these existing surfaces:
1. `techlead-emit-decision --decision-type superseded` or equivalent lifecycle decision helper
2. `techlead-worktree-ownership`
3. `techlead-worktree-stale`

Then, if the mutation state is valid:
4. remove the registered stale superseded role worktree
5. confirm the worktree is no longer registered
6. confirm the superseded role branch remains present
7. return a structured cleanup result

### 3. Physical action in this slice

The physical action should be limited to:
- `git worktree remove <worktree_path>`

Do not:
- delete the superseded role branch
- force-delete an occupied or ambiguous worktree
- mutate the canonical branch

### 4. Evidence preservation

This slice should preserve enough evidence to explain what happened:
- canonical branch
- affected role branch
- superseded branch
- removed worktree path
- prior ownership view
- prior stale assessment
- source superseded decision record

Structured JSON command output is enough for this slice.

## Expected outputs

The command should return:
- `workflow_stage`
- `target_role`
- `canonical_branch`
- `role_branch`
- `superseded_branch`
- `worktree_path`
- `cleanup_performed`
- `cleanup_result`
- `prior_worktree_ownership`
- `prior_worktree_staleness`
- `decision_result`
- `next_step_hint`

Successful cleanup should indicate:
- worktree removed
- superseded branch preserved
- superseded execution surface retired

## Explicit non-goals

Do not include in this slice:
- branch deletion
- automatic replacement worktree preparation
- automatic replacement role branch preparation
- `closed` cleanup
- cross-role cleanup
- broad stale-branch retirement

## Test plan

### Static checks
- command appears in `paa-consumer help`
- runtime compiles
- `techlead-status --validate-schema` still passes

### Positive-path validation
Use a disposable synthetic `superseded` fixture and a disposable registered role worktree.

Prove that:
- the command removes the registered role worktree
- the superseded branch remains present
- the result is structured and auditable

### Fail-closed validation
Prove that cleanup is refused when:
- workflow is not `superseded`
- no registered worktree exists
- target role is unsupported
- stale assessment is not cleanup-candidate
- no `superseded_branch` is present in lineage

## Acceptance criteria

This slice is done when:
- a superseded role worktree can be physically retired in one narrow command
- the superseded role branch is preserved
- cleanup is fail-closed and evidence-preserving
- no `closed` cleanup logic leaks into the implementation
