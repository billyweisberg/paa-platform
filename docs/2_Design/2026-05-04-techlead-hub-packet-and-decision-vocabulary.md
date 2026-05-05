# TechLead Hub Packet and Decision Vocabulary

## Purpose

Define the exact packet and result vocabulary for the TechLead-centered consumer workflow, grounded in the current PAA control spine and packet runtime.

This note goes one level deeper than the mesh-vs-hub comparison.
It answers:

1. which packets each role may receive
2. which result packets each role may return
3. which decisions TechLead may emit
4. which packet schema types can be reused
5. which packet schema types should be introduced for the hub-and-spoke model
6. how to keep the model extensible for future worker roles such as frontend and backend

## Design Goal

The goal is not to create a packet type for every conversational nuance.
The goal is to create a small, explicit workflow vocabulary that:

- keeps routing authority centralized in `TechLead`
- keeps worker roles bounded
- preserves the existing DB spine where it already works
- allows new worker roles to fit the same pattern without inventing a new workflow each time

## Current packet vocabulary

The live runtime currently supports three packet schema types:

- `architect_cycle_packet`
- `slice_result_packet`
- `qa_verification_packet`

The live route pattern is:

- `Architect -> Python Dev` via `architect_cycle_packet`
- `Python Dev -> QA` via `slice_result_packet`
- `QA -> Architect` via `qa_verification_packet`

That means the current packet contracts are role-specific and route-specific.
They are not yet a clean general assignment/result language.

## Target packet model

The hub-and-spoke model should separate packet meaning into three families:

1. assignment packets
2. worker result packets
3. TechLead decision packets

That is the reusable pattern.

## Packet families

### 1. Assignment packet family

Purpose:
- sent only by `TechLead`
- tells one role what bounded work to perform next
- anchors the assignment to the canonical issue lineage and branch strategy

Required semantics:
- target role
- issue identity
- canonical branch identity
- optional role worktree branch identity
- source brief/design package context
- explicit assignment objective
- allowed output/result types
- escalation rules

### 2. Worker result packet family

Purpose:
- returned by a worker role to `TechLead`
- describes what happened in a bounded way
- does not itself route to the next worker

Required semantics:
- source role
- issue identity
- branch lineage used
- result type
- evidence or review outcome
- explicit blocker/escalation markers
- recommendation to TechLead, not a self-executing route

### 3. TechLead decision packet family

Purpose:
- emitted by `TechLead` after evaluating a worker result
- records the next routing or governance decision
- provides durable workflow intent beyond ephemeral queue action

Required semantics:
- decision type
- why the decision was made
- source packet/result that triggered the decision
- next assignment target if any
- branch/worktree action if any
- merge/reset/close state if terminal

## Role vocabulary

## Delivery Architect

### Assignment packet accepted

Preferred schema family:
- `techlead_assignment_packet`

Assignment type values:
- `architecture_review`
- `scope_narrowing`
- `acceptance_readiness_review`
- `branch_reset_review`
- `authority_clarification_review`

### Allowed result packet schema

Preferred schema family:
- `delivery_review_packet`

Allowed result types:
- `ready_for_dev`
- `narrow_scope`
- `reject_scope`
- `request_reset`
- `needs_authority_clarification`
- `needs_human_architect_review`

Notes:
- Delivery Architect does not assign Dev directly
- Delivery Architect does not assign QA directly
- Delivery Architect returns recommendation and rationale to `TechLead`

## Worker role pattern

This pattern covers `Python Dev` now and should cover future worker roles such as `Frontend Dev`, `Backend Dev`, or `Docs Dev`.

### Assignment packet accepted

Preferred schema family:
- `techlead_assignment_packet`

Assignment type values:
- `implement_slice`
- `rework_slice`
- `investigate_blocker`
- `prepare_pr_delta`

Required worker-role fields:
- `worker_role`
- `worker_family`
- `assignment_scope`

Examples:
- `worker_role = Python Dev`
- `worker_role = Frontend Dev`
- `worker_role = Backend Dev`

### Allowed result packet schema

Preferred schema family:
- `worker_result_packet`

Allowed result types:
- `implemented_ready_for_qa`
- `blocked`
- `needs_clarification`
- `cannot_complete_without_scope_change`
- `superseded_by_branch_reset`

Optional future-safe result types:
- `implemented_ready_for_peer_review`
- `implemented_ready_for_multi_role_qa`

Notes:
- This is where we should generalize instead of hardcoding `slice_result_packet` forever
- the worker role should be a field, not a schema fork per language/team

## QA

### Assignment packet accepted

Preferred schema family:
- `techlead_assignment_packet`

Assignment type values:
- `verify_slice`
- `reverify_after_fix`
- `scope_integrity_review`
- `merge_readiness_review`

### Allowed result packet schema

Preferred schema family:
- `qa_verification_packet`

Allowed result types:
- `pass`
- `fail_fixable`
- `fail_scope`
- `needs_human_review`
- `blocked`

Notes:
- existing `qa_verification_packet` is already close to the needed shape
- it should be retained and routed back to `TechLead` instead of to `Architect`

## TechLead

TechLead is not just another role emitting a peer packet.
TechLead owns workflow control.
So its vocabulary should be split between:

- assignment issuance
- workflow decision recording
- terminal acceptance preparation

### Assignment packet schema

Preferred schema family:
- `techlead_assignment_packet`

Assignment target values:
- `Delivery Architect`
- `Python Dev`
- `QA`
- future worker roles

Assignment type values:
- `architecture_review`
- `scope_narrowing`
- `acceptance_readiness_review`
- `implement_slice`
- `rework_slice`
- `investigate_blocker`
- `verify_slice`
- `reverify_after_fix`
- `merge_readiness_review`

### Decision packet schema

Preferred schema family:
- `techlead_decision_packet`

Decision type values:
- `assign_delivery_architect`
- `assign_worker`
- `assign_qa`
- `return_to_delivery_architect`
- `return_to_worker`
- `return_to_qa`
- `escalate_to_authority_architect`
- `reset_branch`
- `supersede_branch_lineage`
- `prepare_merge`
- `close_slice`
- `pause_slice`
- `cancel_slice`

### Merge and closure decisions

Terminal TechLead decision values:
- `prepare_merge`
- `close_slice`

Non-terminal control values:
- `assign_worker`
- `assign_qa`
- `return_to_worker`
- `reset_branch`
- `pause_slice`

## Schema reuse vs new schema introduction

## Reuse with stricter routing

### `architect_cycle_packet`

Recommendation:
- do not use as the long-term hub packet
- keep temporarily during transition only

Why:
- its payload is specifically shaped around the old `Architect -> Python Dev` next-cycle model
- it includes planning and baseline narrative that is useful, but the semantic name is wrong for a TechLead-issued hub assignment

Transitional use:
- may be reused short-term as the first `TechLead -> Python Dev` assignment packet if routing is changed and branch fields are added externally

Long-term status:
- replace with `techlead_assignment_packet`

### `slice_result_packet`

Recommendation:
- reuse temporarily, but evolve away from the name

Why:
- it already carries worker execution evidence well
- but the schema name is too Python/Dev-specific and not future-friendly for worker-role generalization

Transitional use:
- allow `Python Dev -> TechLead` to keep using `slice_result_packet`

Long-term status:
- replace with `worker_result_packet`

### `qa_verification_packet`

Recommendation:
- keep and reuse

Why:
- it already represents a strong verification outcome packet
- its semantics remain valid in the hub model
- only the route changes from `QA -> Architect` to `QA -> TechLead`

Long-term status:
- retained

## New schema types to introduce

### `techlead_assignment_packet`

Why needed:
- we need one reusable assignment contract for all spoke roles
- it must carry branch/worktree lineage and allowed result vocabulary explicitly
- it should not be named after `Architect`

Core fields to add:
- `assignment_type`
- `target_role`
- `canonical_branch`
- `role_branch`
- `worker_role` if applicable
- `allowed_result_types`
- `assignment_scope`
- `source_context`
- `decision_context`

### `worker_result_packet`

Why needed:
- future worker roles should not force packet schema forks
- `Python Dev`, `Frontend Dev`, `Backend Dev`, and similar roles can all follow the same result contract shape

Core fields to add:
- `worker_role`
- `worker_family`
- `result_type`
- `branch_lineage`
- `implementation_summary`
- `validation_summary`
- `artifacts`
- `techlead_action_recommended`

### `delivery_review_packet`

Why needed:
- Delivery Architect is not an implementation worker and not QA
- its output is a scoped architectural review/route recommendation
- forcing it into `qa_verification_packet` or `worker_result_packet` would blur meaning

Core fields to add:
- `review_type`
- `result_type`
- `scope_recommendation`
- `authority_impact`
- `branch_recommendation`
- `techlead_action_recommended`

### `techlead_decision_packet`

Why needed:
- TechLead routing decisions should become durable first-class artifacts, not only implied by the next queue send
- this is especially important for resets, superseding branch lineage, pausing, escalation, and merge preparation

Core fields to add:
- `decision_type`
- `decision_reason`
- `source_packet_ref`
- `next_target_role`
- `next_assignment_type`
- `branch_action`
- `canonical_branch`
- `role_branch`
- `work_item_status_update`

## Extensibility pattern for more worker roles

The important pattern is:
- one assignment schema for spoke roles
- one worker-result schema for execution roles
- role identity carried as data, not encoded into the schema name

That lets future roles fit without redesigning the control plane:

- `Python Dev`
- `Frontend Dev`
- `Backend Dev`
- `Infra Dev`
- `Docs Dev`

They can all accept:
- `techlead_assignment_packet`

They can all return:
- `worker_result_packet`

Only `QA` and `Delivery Architect` remain specialized result families because their review semantics are meaningfully different.

## DB/control-spine adaptation

## What can stay as-is initially

The following tables already support the new model with route-policy changes rather than schema surgery:

- `paa.handoffs`
- `paa.queue_messages`
- `paa.automation_runs`
- `paa.work_items`
- `paa.coder_run_briefs`
- `paa.design_packages`
- `paa.coder_brief_sequence_states`
- `paa.verification_obligations`
- `paa.acceptance_events`

Initial adaptation is mostly data/policy:
- new `handoff_type` values
- new `schema_type` values
- new allowed route rules
- new packet compilers

## What should likely be added later

### Branch lineage persistence

We should eventually persist, at minimum:
- canonical branch name
- role branch name
- branch owner role
- superseded branch lineage
- reset reason

That may belong in:
- `paa.handoffs.metadata_json`
- `paa.queue_messages.metadata_json`
- or a new dedicated branch-lineage table if we want strong reporting/query semantics

### Decision persistence clarity

`techlead_decision_packet` may be persisted through existing `handoffs` and `queue_messages`, but we may later want a clearer decision table if workflow analytics become important.

Do not start there.
Start with packet persistence and prove the model first.

## Recommended rollout

### Phase 1
- route `slice_result_packet` back to `TechLead` instead of directly to `QA`
- route `qa_verification_packet` back to `TechLead` instead of directly to `Architect`
- let `TechLead` issue the next packet every time
- keep existing packet schemas where possible during transition

### Phase 2
- introduce `techlead_assignment_packet`
- introduce `techlead_decision_packet`
- keep `qa_verification_packet`
- keep `slice_result_packet` temporarily

### Phase 3
- replace `slice_result_packet` with `worker_result_packet`
- introduce `delivery_review_packet`
- generalize worker roles beyond `Python Dev`

## Recommended initial contract

If we want the smallest viable hub-and-spoke shift:

Keep:
- `qa_verification_packet`

Temporarily reuse:
- `architect_cycle_packet`
- `slice_result_packet`

Add new:
- `techlead_assignment_packet`
- `techlead_decision_packet`
- later `worker_result_packet`
- later `delivery_review_packet`

That gives us a pragmatic transition instead of a rewrite.

## Bottom line

The hub-and-spoke model should standardize around:

- one TechLead-issued assignment family
- one generalized worker-result family
- one specialized QA verification family
- one TechLead decision family

That is the right pattern for:
- current `Python Dev`
- future `Frontend Dev` and `Backend Dev`
- explicit branch/worktree governance
- centralized workflow routing
- better recovery and auditability
