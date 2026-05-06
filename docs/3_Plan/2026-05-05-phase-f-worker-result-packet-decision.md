# Phase F Decision: Keep The Current Return Bridge, Defer `worker_result_packet` To Phase G

## Decision

The current return-bridge orchestration is generic enough to keep.

Do **not** introduce `worker_result_packet` yet.

Instead:
- keep the existing return bridge shape
- keep `slice_result_packet` as the transitional worker result for the current Python lane
- defer `worker_result_packet` to Phase G, where multi-worker expansion becomes real rather than hypothetical

## Why

Phase F has now validated the same narrow return bridge for both:
- `Python Dev`
- `QA`

That proves the orchestration layer is already reusable:
- TechLead handoff
- role worktree preparation
- role entry
- role result assist
- role return compile/validate/send

The remaining limitation is not the bridge flow.
The limitation is the semantic contract of the worker result packet name:
- `slice_result_packet` still encodes a Python-specific historical lane

That is a naming and future-generalization concern, not a reason to block the current bridge.

## Interpretation

This means:

### Good enough now
- command shape
- branch/worktree bridge shape
- validate/send flow
- result-return transport path

### Not good enough for later
- treating `slice_result_packet` as the final long-term result family for multiple worker-role types

## Consequence for the plan

Phase F can continue without a packet-family rewrite.

Phase G should own the decision boundary for:
- whether `slice_result_packet` becomes `worker_result_packet`
- whether `delivery_review_packet` is introduced at the same time
- how future worker-role families map onto the result contract cleanly
