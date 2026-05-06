## Purpose

Add the first narrow handoff from TechLead assignment emission to a prepared role worktree.

This slice intentionally does only four things:
- emit the assignment packet
- prepare the role branch
- prepare the role worktree
- stop before role execution

## Command

```bash
<consumer_repo>/.codex/paa/bin/paa-consumer techlead-handoff-to-role-worktree \
  --repo-root <consumer_repo> \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  [--target-role <python-team|qa>] \
  [--send]
```

Optional overrides:
- `--output`
- `--review-output`
- `--branch-action`
- `--canonical-branch`
- `--role-branch`
- `--worktree-path`

## Required sequencing

The command is an orchestration layer over existing primitives:

1. `techlead-emit-next-assignment`
2. `techlead-prepare-role-branch`
3. `techlead-prepare-role-worktree`

It does not introduce a new queue transport or a new branch/worktree mutation model.

## Supported scope

Supported roles:
- `python-team`
- `qa`

Supported behavior:
- explicit Python Dev handoff
- derived QA handoff when TechLead sees `techlead_dev_review_pending`

## Current non-goals

This slice does **not**:
- execute role work automatically
- clean up prior worktrees
- clean up stale branches
- supersede or close branch lineages
