# Phase H3 Mini Plan: Reset-Required Lifecycle Mutation

## Summary

Implement the first cleanup-safe lifecycle mutation slice on top of:
- `techlead-lineage`
- `techlead-worktree-ownership`
- `techlead-worktree-stale`
- existing `reset_required` TechLead decision support

Chosen scope:
- `reset_required` only
- no broad supersede handling
- no broad close handling
- no automatic worktree deletion
- no branch deletion

The goal is to make the system capable of marking a role execution surface as reset-required and preparing a clean next-lineage branch target without immediately destroying any worktree state.

## Why this is the first mutation slice

`reset_required` is the best first lifecycle mutation because:
- the system already detects reset-required conditions
- the system already records `reset_required` as a TechLead decision
- reset-required is safer to implement first than `superseded` or `closed`
- it lets us separate:
  - authoritative mutation of lineage state
  - later physical cleanup of stale worktrees

That keeps the first mutation slice conservative.

## Ownership model carried forward

This slice preserves the Phase H1 ownership contract:
- `TechLead` owns lineage and mutation authority
- role automation owns its own worktree instance
- this slice may mark a role worktree stale / reset-required
- this slice does **not** delete the role worktree

## Implementation scope

### 1. Add one reset-required lifecycle command

Add one new consumer-side command:

```bash
<consumer_repo>/.codex/paa/bin/paa-consumer techlead-reset-required \
  --repo-root <consumer_repo> \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  [--target-role <delivery-architect|python-team|qa>] \
  [--send-decision]
```

Initial supported role target:
- `python-team` only

Optional later extension in a future slice:
- `qa`
- `delivery-architect`

### 2. What the command does

The new command should orchestrate existing surfaces in order:
1. query lineage
2. query worktree ownership
3. query stale status
4. derive `reset_required` TechLead decision context
5. optionally emit/send the `techlead_decision_packet`
6. return a normalized mutation plan

The command should not:
- delete a branch
- delete a worktree
- recreate a worktree automatically
- force-reset a branch automatically in this slice

### 3. Supported reset-required behavior in this slice

For the supported path:
- current lineage/workflow must support `reset_required`
- role target must be `python-team`
- output should explicitly identify:
  - canonical branch
  - affected role branch
  - affected worktree path
  - stale assessment
  - decision packet result if emitted
  - recommended next manual or future-automation action

Expected effect:
- the system records that the current role execution surface is no longer safe to continue in place
- the worktree becomes a cleanup candidate
- the next branch/worktree preparation can be done on a clean lineage in a later slice

### 4. Fail-closed rules

Return `ok = false` if:
- lineage is ambiguous
- no reset-required state is actually present
- target role is unsupported in this slice
- worktree ownership cannot be resolved
- stale assessment is inconsistent with the reset-required mutation intent

Important constraint:
- do not guess
- do not quietly reset or recreate branches/worktrees

## Expected outputs

The command should return a JSON result containing:
- `workflow_stage`
- `target_role`
- `canonical_branch`
- `role_branch`
- `worktree_path`
- `worktree_ownership`
- `worktree_staleness`
- `decision_result`
- `cleanup_candidate = true`
- `next_step_hint`

The important point is:
- this slice makes reset-required lifecycle state actionable and queryable
- without performing irreversible cleanup actions yet

## Explicit non-goals

Do not include in this slice:
- supersede cleanup
- close cleanup
- branch deletion
- worktree deletion
- automatic worktree recreation
- multi-role reset mutation support
- physical cleanup execution

## Test plan

### Static checks
- command is listed in `paa-consumer help`
- command compiles/returns structured output
- `techlead-status --validate-schema` still passes

### Runtime checks
- supported reset-required context returns a valid mutation plan
- if `--send-decision` is used, the existing `reset_required` decision path is reused
- unsupported or non-reset contexts fail closed

### Safety checks
- command does not mutate branches or worktrees directly in this slice
- command does not delete anything
- command only marks cleanup candidacy and returns the next action

## Acceptance criteria

This slice is done when:
- `reset_required` has one narrow lifecycle mutation surface
- the affected role worktree can be marked as stale/cleanup-candidate in a queryable way
- no physical cleanup is performed yet
- the next reset cleanup slice can build on this result without re-deriving ownership and staleness from scratch
