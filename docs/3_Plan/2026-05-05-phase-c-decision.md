# Phase C Decision

## Summary

Recommended Phase C:
- **real TechLead assignment emission flow**

Deferred to the following phase:
- branch/worktree lineage persistence

## Why this is the right next move

The system goal is autonomous agent-driven routing, not a permanently human-operated packet loop.

After Phase B, we now have:
- first-class `techlead_assignment_packet`
- first-class `techlead_decision_packet`
- explicit validate/send dispatch helpers
- TechLead reporting that recognizes:
  - `techlead_assignment_issued`
  - `techlead_decision_recorded`

That means the missing capability is no longer packet structure.
It is **emission orchestration**.

Right now the biggest remaining gap between the current system and the intended PAA model is:
- TechLead can determine the next route
- but TechLead does not yet emit the next assignment as part of a stable flow

That is the most important autonomy gap.

## Why not branch/worktree lineage persistence first

Branch/worktree lineage persistence is still important, but it is not the next bottleneck.

We already have enough to operate with:
- canonical branch naming
- optional role-branch conventions
- branch fields carried in packet payloads
- a documented worktree strategy

What we do **not** yet have is the ability for TechLead to move the workflow forward end to end without a manual compile/send boundary.

If we choose lineage persistence first, we improve auditability before we improve autonomy.
That is the wrong order for the current system need.

## What Phase C should accomplish

Phase C should make TechLead capable of issuing the next assignment artifact through a controlled runtime path.

Target outcomes:
1. TechLead can emit `techlead_assignment_packet` as the next step after evaluating:
   - a Dev result packet
   - a QA verification packet
   - a previously recorded TechLead decision
2. emission uses the same deterministic dispatch primitives already added in Phase B
3. emission remains policy-driven and explicit
4. reporting reflects emitted assignments as durable workflow state
5. humans are no longer required to bridge the compile -> validate -> send gap for ordinary next-step routing

## Scope recommendation for Phase C

Keep Phase C narrow.

Include:
- TechLead runtime command or subflow to prepare the next assignment packet
- explicit emission path using the existing dispatch helper
- clear mapping from TechLead decision types to assignment packet outputs
- minimal prompt updates needed to reflect that TechLead can now emit the next assignment in supported cases

Do not include yet:
- full branch/worktree metadata persistence in new DB fields
- queue renaming
- DB role split for `Delivery Architect` / `Authority Architect`
- replacement of `slice_result_packet` with `worker_result_packet`
- full future-worker generalization beyond what current schemas already allow

## Why this ordering is safer

This ordering lets us prove:
- the hub can actually drive the workflow
- the dispatch primitive is sufficient
- the TechLead runtime can move from recommendation to action

Only after that is proven do we need to deepen lineage persistence.

If Phase C succeeds, then the next phase can focus on:
- branch/worktree lineage persistence
- richer audit/history
- clearer role separation in the control spine

## Decision

Phase C should be:
- **real TechLead assignment emission flow**

Branch/worktree lineage persistence should follow as the next hardening phase after TechLead emission is working.
