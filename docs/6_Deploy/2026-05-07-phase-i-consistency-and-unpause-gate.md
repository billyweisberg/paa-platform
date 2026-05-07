# Phase I Consistency Checklist And Unpause Gate

## Consistency checklist

Before unpausing real automations, verify:

### Prompt and skill consistency
- active TechLead guidance teaches:
  - `worker_result_packet` for Python
  - `delivery_review_packet` for Delivery Architect
  - `qa_verification_packet` for QA
- no active guidance teaches `slice_result_packet` as the default Python lane
- lifecycle cleanup guidance matches implemented commands:
  - `reset`
  - `superseded`
  - `closed`

### Wrapper and runtime consistency
- installed consumer wrapper exposes the current command surface
- installed TechLead skill matches the current runtime
- queue validate/send helpers are available from the top-level CLI

### Routing consistency
- `TechLead` is the only routing hub for consumer-side roles
- no active flow depends on direct:
  - `Python Dev -> QA`
  - `QA -> Architect`
- Delivery Architect follow-up behavior matches the current implemented cases

### Branch and worktree consistency
- lineage is queryable
- worktree ownership is queryable
- stale-worktree state is queryable
- lifecycle cleanup commands fail closed when state is ineligible

### Legacy compatibility boundaries
- `slice_result_packet` still validates for legacy overlap
- but is not taught as an active default

## Automation unpause gate

Real automations should remain paused until all of the following are true:

1. one canonical end-to-end slice passes through the current role set
2. no queue-state drift appears during that run
3. no branch/worktree ownership ambiguity appears during that run
4. no prompt/runtime mismatch is found on an active path
5. no active path requires hidden manual queue reasoning
6. lifecycle cleanup commands remain consistent with lineage state during the run

## Still-blocking conditions even after a mostly successful E2E run

Do not unpause real automations yet if:
- the E2E pass depends on ad hoc manual intervention outside documented runtime surfaces
- the installed wrappers and project-pack guidance are out of sync
- Delivery Architect routing still needs unplanned manual reinterpretation
- repeated runs produce inconsistent queue or worktree observations

## Exit condition for this gate

The gate is satisfied only when the current role set is:
- coherent
- repeatable
- documented
- and safe enough to unpause deliberately rather than experimentally
