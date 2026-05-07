# TechLead Worktree Ownership Query

## Purpose

Add one narrow query surface for Phase H1 so worktree ownership is explicit and machine-readable before any cleanup automation begins.

## Command

```bash
<consumer_repo>/.codex/paa/bin/paa-consumer techlead-worktree-ownership \
  --repo-root <consumer_repo> \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role <delivery-architect|python-team|qa>
```

Optional overrides:
- `--role-branch`
- `--worktree-path`

## What it returns

The command returns one normalized `worktree_ownership` object with:
- ownership model
- lineage owner role
- runtime owner role
- runtime owner role CLI id
- admin surface role
- ownership source
- role branch
- worktree path
- default worktree path
- whether the default deterministic path is in use
- whether the worktree is currently registered
- checked-out branch
- whether the checked-out branch is aligned
- worktree head commit

It also returns the linked lineage view so the ownership record stays attached to the issue/branch context that authorized it.

## Contract

This reflects the Phase H1 ownership rule:
- `TechLead` owns lineage and branch authorization
- the role automation owns create-or-reuse of its own deterministic role worktree
- `TechLead` worktree commands remain admin/recovery surfaces

## Why this exists

This keeps cleanup automation from guessing.

Before reset/supersede/close automation mutates any worktree, the system should be able to answer:
- which role owns this worktree?
- is it the deterministic path for that role branch?
- is the expected branch actually checked out there?

This command provides that narrow answer without introducing cleanup behavior yet.
