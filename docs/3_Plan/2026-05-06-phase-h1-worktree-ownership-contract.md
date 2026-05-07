# Phase H1: Worktree Ownership Contract

## Purpose

Define who creates, reuses, and cleans up role worktrees in the first MVP automation model.

This slice exists because worktree creation is now possible from two directions:
- `TechLead`-side helper commands already exist
- Codex Automations can also create worktrees directly

Without an explicit ownership rule, we will drift into:
- duplicate worktree creation paths
- unclear cleanup responsibility
- cross-role worktree mutation
- hidden branch/worktree state

## Decision

For the first MVP automation model:
- `TechLead` owns **lineage and authorization**
- each role automation owns **its own role worktree instance**

That means:
- `TechLead` decides the canonical issue lineage and the allowed role branch
- `TechLead` emits the assignment packet
- the role automation, when it starts work, is responsible for creating or reusing its own worktree from the approved role branch
- the role automation must not create arbitrary branches or arbitrary worktree paths
- one role automation must not mutate another role's worktree

## Ownership Model

### TechLead owns

`TechLead` is the control-plane owner of:
- canonical branch choice
- role branch authorization
- lineage state
- assignment routing
- close/reset/supersede decisions

`TechLead` does **not** own the long-lived runtime responsibility for each role worktree instance.

### Role automation owns

The automation for a specific role owns:
- create-or-reuse of its own approved worktree
- local execution inside that worktree
- result return from that worktree context
- marking that worktree ready for cleanup when the role completes or is superseded

Examples:
- `Python Dev` automation owns the `issue-<n>-dev` worktree instance
- `QA` automation owns the `issue-<n>-qa` worktree instance
- `Delivery Architect` automation owns the `issue-<n>-delivery` worktree instance

## MVP operational rule

The existing `TechLead` worktree helpers should now be treated as:
- reference implementation
- validation/admin utilities
- fallback/manual recovery tools

They should **not** be the normal steady-state owner of role worktree lifecycle.

For MVP automations, the preferred path is:
1. `TechLead` emits assignment with lineage context
2. role automation claims or receives assignment
3. role automation calls the shared repo-local worktree-prep helper for its own role
4. role automation runs in that worktree
5. role automation returns its result

So the helper is still used, but by the role automation, not by `TechLead` as the long-term runtime owner.

## Why this is the right MVP model

This keeps the responsibilities clean:
- `TechLead` remains the hub and authority
- role automations remain bounded workers
- worktree lifecycle stays closest to the code actually running inside that worktree

It also avoids a bad pattern where:
- `TechLead` creates worktrees for everyone
- but another agent is actually using them
- and no one clearly owns cleanup, reuse, or stale-state detection

## Constraints

### Allowed
- role automation may create or reuse only its own deterministic role worktree
- role automation may do so only from lineage/assignment context emitted by `TechLead`
- `TechLead` may still invoke helper commands for validation, bootstrap testing, or recovery

### Not allowed
- role automation inventing random branch names
- role automation creating a worktree for a different role
- `TechLead` mutating a role worktree ad hoc without a lineage-driven reason
- one automation cleaning another automation's worktree in the MVP model

## Deterministic paths

The deterministic model remains:
- canonical branch: `issue-<issue_number>`
- role branch: `issue-<issue_number>-<role>`
- default worktree path: `~/.codex/worktrees/paa/<repo_name>/<role_branch>`

This is still the contract. The only thing changing is the declared owner of create/reuse/cleanup responsibility.

## First Phase H slice

The first Phase H implementation slice should be:
- formalize role automation self-service worktree preparation as the default runtime path
- keep `TechLead` worktree commands as admin/recovery surfaces
- add explicit worktree ownership metadata/reporting so the owning role is queryable
- do **not** automate cleanup yet

## Acceptance criteria

This slice is done when:
- the plan clearly says who owns worktree creation and reuse
- the normal runtime path is role automation self-service, not `TechLead`-managed worktree creation
- `TechLead` retains authority over lineage and branch authorization
- no cleanup automation is introduced yet

## Follow-on slices

After this ownership contract is accepted, the next lifecycle slices should be:
1. worktree ownership metadata/reporting
2. stale worktree detection
3. close/reset/supersede cleanup actions
4. only then automated retirement/deletion
