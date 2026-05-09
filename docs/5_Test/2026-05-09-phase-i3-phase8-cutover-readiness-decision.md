# Phase I3 Phase 8 Cutover Readiness Decision

## Verdict

- `Phase 8: pass`
- readiness decision: `ready only for additional supervised pilot`

## Pass/fail summary of prior phases

- Phase 0 baseline and installation sanity:
  - `pass`
- Phase 1 prompt and skill contract alignment:
  - `pass`
- Phase 2 non-model preflight gate:
  - `pass`
- Phase 3 execution environment contract adherence:
  - `pass`
- Phase 4 packet and queue transport validation:
  - `pass`
- Phase 5 role bridge surface validation:
  - `pass`
- Phase 6 canonical supervised end-to-end slice:
  - `pass`
- Phase 7 lifecycle safety validation:
  - `pass`

## Blocker review

### Hard blockers for deliberate unpause

1. actual app/UI automation visibility and launch behavior is still not proven end to end
- we verified:
  - home-level UI registration files exist and parse
  - installed/project-pack prompts and runtime contracts align
  - CLI/runtime execution works
- we did not yet verify, in the actual app UI, that:
  - `Delivery Architect`
  - `Python Dev`
  - `QA`
  show up reliably and launch with the expected runtime context
- because deliberate unpause depends on the real automation launcher, this remains a hard blocker for full unpause

2. actual automation-triggered execution has not yet been observed from the app boundary
- we proved the current role set through supervised CLI/runtime surfaces
- we have not yet observed the real automation runner:
  - polling via the preflight gate
  - deciding not to invoke the model when no work exists
  - invoking the model when work exists
  - using the expected cwd / wrapper / worktree contract under the app launcher
- this is the last meaningful gap between runtime proof and real cutover

### Operational notes, not blockers

1. `queue-check` preview depth on `fractal-core-architecture` remains shallow
- routing and top-level TechLead status now tolerate this correctly
- this is a real observability defect
- it is not a blocker for the current proven role set
- it should be hardened before broader scale-out

2. raw broker `messages_ready` can lag briefly after cleanup
- reconciled queue state and follow-up checks returned to zero
- treated as known runtime behavior, not an active blocker

## Why the verdict is not `ready for deliberate unpause`

The current proven role set is now good enough that the remaining gap is no longer packet/routing/lifecycle correctness.

The remaining gap is launch-surface proof:
- actual UI visibility
- actual app-triggered automation startup
- actual app-triggered preflight/no-work behavior
- actual app-triggered runtime environment adherence

That means we are beyond:
- architecture proof
- runtime proof
- lifecycle proof

But we are not yet beyond:
- automation launcher proof

So calling this `ready for deliberate unpause` today would be too optimistic.

## Why the verdict is still positive

This is not a `not ready` result.

The proven system now has:
- coherent packet families
- coherent routing
- coherent role bridges
- coherent lifecycle safety
- coherent top-level TechLead state transitions
- deterministic worktree and queue behavior for the current proven role set

So the right next step is not more core-system design.
The right next step is one supervised pilot from the actual automation/UI boundary.

## Decision

- `ready only for additional supervised pilot`

## Explicit next action

Run one supervised app/UI-launched automation pilot for the current proven role set, in this order:
1. verify `Delivery Architect`, `Python Dev`, and `QA` appear in the UI alongside `TechLead`
2. trigger one no-work poll cycle and verify no model invocation occurs
3. trigger one real supervised work cycle and verify:
   - correct cwd
   - correct wrapper usage
   - correct worktree transition
   - correct return packet family
4. only after that, make the final deliberate unpause decision
