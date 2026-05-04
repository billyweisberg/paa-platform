# Worktree Branch Strategy

## Purpose

Define how PAA automations should use Git worktrees without reintroducing branch drift.

## Core Constraint

Git does not allow the same local branch to be checked out in multiple worktrees at the same time.

That means this is not valid for concurrent automation worktrees:
- Delivery Architect on `issue-123`
- Dev on `issue-123`
- QA on `issue-123`

all at once as separate checked-out worktrees.

## Correct Model

Use one shared issue lineage, not one literally shared checked-out branch identity.

### Canonical issue branch

For each active issue, keep one canonical issue branch:

- `issue-<issue_number>`

Example:
- `issue-106`

### Worktree branches

If multiple automations need concurrent worktrees for the same issue, use deterministic role-specific branches derived from the canonical issue branch:

- `issue-<issue_number>-delivery`
- `issue-<issue_number>-dev`
- `issue-<issue_number>-qa`
- `issue-<issue_number>-techlead`

Examples:
- `issue-106-delivery`
- `issue-106-dev`
- `issue-106-qa`
- `issue-106-techlead`

## Rules

- All role worktree branches must be created from the current tip of `issue-<issue_number>`.
- All role worktree branches belong to the same issue lineage.
- Do not invent random branch names.
- Do not use historical `codex/...` branch naming for automation issue execution branches.
- Delivery Architect, Dev, QA, and TechLead must all recognize the same issue lineage even when using different worktree branches.

## Recommended Usage

### Single active worker

If only one automation or one human session is active for the issue:
- use `issue-<issue_number>`

### Concurrent worktrees

If multiple worktree-based automations are active concurrently:
- keep `issue-<issue_number>` as the canonical issue branch
- allow each concurrent worktree to use a role-specific branch derived from it

## Why This Exists

This strategy prevents:
- branch checkout conflicts across worktrees
- random role branch names
- QA and Dev operating on unrelated code lines
- confusion between issue identity and worktree identity

## Current Operational Note

At the time of writing, Codex UI automation visibility appears to prefer global automation registration under:
- `/Users/billyweisberg/.codex/automations/`

and worktree execution creates runtime worktrees under:
- `/Users/billyweisberg/.codex/worktrees/`

So this branch strategy should be treated as part of the automation execution contract, not only a Git convention.
