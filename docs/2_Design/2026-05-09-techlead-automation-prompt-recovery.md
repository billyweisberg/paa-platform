# TechLead Automation Prompt Recovery

## Purpose

Recover the best historically-developed prompt intent for the `Fractal Core TechLead Automation` so it can be reviewed as a stable artifact instead of rediscovered from scattered runtime files.

## Recovery Sources Reviewed

### Current authoritative sources
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/project-packs/fractal-core/automations/fractal-core-techlead-automation/automation.toml`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/project-packs/fractal-core/skills/fractal-core-techlead/SKILL.md`

### Installed consumer copies
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/automations/fractal-core-techlead-automation/automation.toml`
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/skills/fractal-core-techlead/SKILL.md`

### Historical committed prompt surfaces
- commit `0f1ddcb`
- commit `e9a5885`
- commit `31a93dd`
- commit `6e0d090`
- commit `409173d`
- commit `e7f0426` for the earlier richer TechLead skill text

### Home-level UI registration surface
- `/Users/billyweisberg/.codex/automations/fractal-core-techlead-automation/automation.toml`
- `/Users/billyweisberg/.codex/automations/fractal-core-techlead-automation-probe/automation.toml`

## What Was Recovered

The best TechLead prompt work was split across two layers:

1. wrapper intent in `automation.toml`
2. operational workflow contract in `fractal-core-techlead/SKILL.md`

The wrapper alone was never the full valuable prompt.
The skill carried most of the important behavioral guidance.

## Earliest Durable Wrapper Intent

This was the durable high-level wrapper shape recovered from early committed automation definitions:

```text
Use repo-local consumer runtime only.
Generate the TechLead report from installed authority, queue runtime, GitHub state, and PAA traceability.
Flag any issue work that is not using the shared branch pattern `issue-<issue_number>`.
```

This was useful, but too thin to serve as the whole operating prompt.

## Earliest Rich Skill Intent

The richest early TechLead operational skill text recovered from git history was the pre-hub status/reconciliation version:

- reconcile authority version and local mirrors
- reconcile GitHub issue / PR state
- reconcile queue state for Python, QA, and Architect
- reconcile automation visibility and runtime mode
- reconcile unresolved QA escalations
- use one report to determine current owner role and whether unattended continuation is safe

That was the strongest early expression of TechLead as a system-state reconciler.

## Current High-Value Prompt Intent

The later hub-phase work added the valuable routing and lineage responsibilities:

- TechLead owns routing decisions
- TechLead owns canonical branch lineage
- TechLead owns role-branch authorization
- TechLead receives all spoke-role results
- TechLead emits assignment and decision packets
- TechLead uses lineage, worktree ownership, and staleness before mutation or cleanup
- TechLead owns lifecycle decisions such as reset, supersede, close, merge-prep, and pause

## Recovered Canonical TechLead Prompt Intent

This is the best recovered canonical prompt intent for TechLead:

```text
Act as TechLead only.
Use repo-local consumer runtime only.
Use the canonical consumer repo root as the runtime launch surface.

First reconcile the current system state from:
- installed authority
- queue runtime
- GitHub issue / PR state
- PAA traceability
- current lineage / worktree state

Treat all consumer-side routing as TechLead-owned.
Treat all worker, QA, and Delivery Architect result packets as inputs to a TechLead routing or lifecycle decision.
Do not allow spoke roles to route directly to each other.

TechLead owns:
- canonical issue branch lineage
- role-branch authorization
- assignment emission
- decision emission
- lifecycle mutation and cleanup decisions

Use:
- `techlead-lineage` before branch or worktree mutation
- `techlead-worktree-ownership` before ownership-sensitive cleanup reasoning
- `techlead-worktree-stale` before cleanup or reset behavior
- `techlead-emit-next-assignment` for supported next assignments
- `techlead-emit-decision` for durable reset, supersede, close, merge-prep, pause, or escalation decisions
- role-bridge helper commands only as bounded handoff/inspection/return surfaces

Use `issue-<issue_number>` as the canonical issue branch.
Use authorized deterministic role branches only when isolated role execution is explicitly needed.
Flag lineage violations, stale branch assumptions, unapproved branch invention, or any attempt to route around TechLead.
```

## Prompt Elements Worth Preserving

These are the most valuable TechLead prompt elements recovered from history:

- TechLead as reconciler of system truth, not just a router
- TechLead as the sole consumer-side routing hub
- explicit repo-local runtime discipline
- traceability through authority, queue, GitHub, and PAA state together
- explicit lineage and lifecycle ownership
- fail-closed posture around branch, worktree, and routing violations

## Regressions To Avoid

Do not regress TechLead back to:
- status-report-only observer
- thin wrapper text with no routing/lifecycle contract
- shared-branch-only assumptions
- hidden operator knowledge for queue, branch, or lineage decisions
- home-folder skill dependencies as active runtime truth

## Recovery Conclusion

The original value was not one perfect wrapper prompt.
The value was the combination of:
- system reconciliation discipline
- explicit routing ownership
- repo-local runtime discipline
- lineage-aware execution control

Future TechLead prompt work should preserve those four properties together.
