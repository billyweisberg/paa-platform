# Phase G Worker Result And Delivery Review Contracts

## Purpose

Define the first true Phase G packet contracts for:
- `worker_result_packet`
- `delivery_review_packet`

This note also locks the migration rule for the current Python lane so we do not blur:
- transitional reuse
- long-term generic contract
- Delivery Architect specialization

## Executive Summary

Phase F proved that the current bridge orchestration is reusable.
That means the next architectural question is packet semantics, not bridge shape.

The decisions are:
- introduce `worker_result_packet` as the generic execution-role result family
- introduce `delivery_review_packet` as the specialized Delivery Architect result family
- keep `qa_verification_packet` as the specialized QA result family
- keep `slice_result_packet` temporarily for the current Python lane only
- migrate `Python Dev` to `worker_result_packet` only after the generic worker contract is proven in runtime and reporting

## Contract Goals

The packet-family boundary should become:

- `techlead_assignment_packet`
  - one assignment family for all spoke roles
- `worker_result_packet`
  - one generic result family for implementation workers
- `delivery_review_packet`
  - one specialized result family for Delivery Architect
- `qa_verification_packet`
  - one specialized result family for QA
- `techlead_decision_packet`
  - one durable decision family for TechLead routing, reset, supersede, pause, merge, and close decisions

## 1. `worker_result_packet`

## Purpose

Represent a result produced by an implementation worker role and returned to `TechLead`.

This is the long-term replacement for using `slice_result_packet` as the default execution result family.

## Roles covered

Initial intended roles:
- `Python Dev`
- future `Frontend Dev`
- future `Backend Dev`
- future `Infra Dev`
- future `Docs Dev`

## Why it exists

`slice_result_packet` currently works, but it encodes a historical Python-specific lane.
That becomes a naming and evolution problem as soon as more worker-role families are added.

`worker_result_packet` fixes that by making role identity part of the payload data rather than the schema name.

## Required semantics

A valid `worker_result_packet` must answer:
- who did the work
- what assignment it answered
- what branch/worktree lineage it used
- what result type it reached
- what evidence and artifacts it produced
- what TechLead should consider next

## Top-level envelope expectations

Keep the current handoff envelope conventions:
- `message_id`
- `schema_type = worker_result_packet`
- `schema_version`
- `project`
- `from_role`
- `to_role = techlead`
- `created_at`
- `correlation_id`
- `github_context`
- `payload`
- `authority_context`

## Payload contract

Required payload sections:
- `issue`
- `branch`
- `pr`
- `worker_role`
- `worker_family`
- `result_type`
- `workflow_compliance`
- `implementation_summary`
- `validation_summary`
- `artifacts`
- `merge_status`
- `techlead_action_recommended`
- `coder_run_brief_ref`
- `coder_run_brief`
- `coder_brief_resolution`
- `source_assignment_ref`

### `worker_role`

Examples:
- `Python Dev`
- `Frontend Dev`
- `Backend Dev`
- `Infra Dev`
- `Docs Dev`

### `worker_family`

A stable grouping value for reporting and future policy.

Examples:
- `implementation`
- `docs`
- `infra`

Initial default:
- `implementation` for `Python Dev`

### `result_type`

Initial recommended values:
- `implemented_ready_for_qa`
- `blocked`
- `needs_clarification`
- `cannot_complete_without_scope_change`
- `superseded_by_branch_reset`

### `workflow_compliance`

Carries the existing execution-governance checks.

Examples:
- shared issue branch or authorized role branch used
- issue-side update recorded if required
- assignment artifact was the basis of work

### `implementation_summary`

Concise worker-oriented summary of what changed and why.
This replaces the Python-specific flavor of `result_summary` as the semantic center of the packet.

### `validation_summary`

Generic validation block.
Expected to hold:
- `status`
- `commands`
- `notes`
- `evidence_refs`

### `artifacts`

Preserve the existing artifact-list pattern.

### `merge_status`

Preserve the existing merge-readiness shape where useful.

### `techlead_action_recommended`

Explicit recommendation from the worker back to TechLead.

Initial values should remain constrained.
Examples:
- `assign_qa`
- `request_scope_clarification`
- `request_reset`
- `hold_for_human_review`

### `source_assignment_ref`

Required.
This must point back to the triggering `techlead_assignment_packet`.

Fields:
- `message_id`
- `assignment_type`
- `target_role`
- `path` if available

## What it intentionally does not include

It should not try to become:
- a QA verification packet
- a Delivery Architect review packet
- a TechLead decision packet

## 2. `delivery_review_packet`

## Purpose

Represent a scoped Delivery Architect review result returned to `TechLead`.

This is a specialized spoke-review family, not a worker implementation result.

## Why it exists

Delivery Architect performs architectural review and route-shaping, not implementation work and not QA verification.
Forcing it into either:
- `worker_result_packet`
- `qa_verification_packet`

would blur the meaning of the role.

## Required semantics

A valid `delivery_review_packet` must answer:
- what assignment it answered
- whether scope is acceptable
- whether authority clarification is needed
- whether branch/reset action is recommended
- what TechLead should do next

## Top-level envelope expectations

Keep the current handoff envelope conventions:
- `message_id`
- `schema_type = delivery_review_packet`
- `schema_version`
- `project`
- `from_role = delivery-architect`
- `to_role = techlead`
- `created_at`
- `correlation_id`
- `github_context`
- `payload`
- `authority_context`

## Payload contract

Required payload sections:
- `issue`
- `branch`
- `pr`
- `review_type`
- `result_type`
- `scope_recommendation`
- `authority_impact`
- `branch_recommendation`
- `techlead_action_recommended`
- `review_summary`
- `findings`
- `source_assignment_ref`
- `coder_run_brief_ref`
- `coder_run_brief`
- `coder_brief_resolution`

### `review_type`

Initial default:
- `delivery_architecture_review`

### `result_type`

Initial recommended values:
- `ready_for_dev`
- `narrow_scope`
- `reject_scope`
- `request_reset`
- `needs_authority_clarification`

### `scope_recommendation`

Explicit recommendation about implementation scope.
Examples:
- `proceed_as_assigned`
- `reduce_scope`
- `split_scope`
- `stop_and_reauthor`

### `authority_impact`

Signals whether the conclusion affects published authority.
Examples:
- `none`
- `clarification_needed`
- `reauthorization_needed`

### `branch_recommendation`

Delivery Architect may recommend lineage action, but does not perform it.
Examples:
- `keep_current_lineage`
- `reset_role_branch`
- `supersede_current_lineage`

### `techlead_action_recommended`

Initial values:
- `assign_worker`
- `return_to_delivery_architect`
- `escalate_to_authority_architect`
- `reset_branch`
- `hold_for_human_review`

## What it intentionally does not include

It should not pretend to be:
- QA verification
- implementation evidence
- final TechLead decision

## 3. Reuse vs Migration For The Current Python Lane

## Keep as transitional

Keep using:
- `slice_result_packet`

for the current Python lane during transition.

Why:
- the bridge is already proven
- current compilers, traceability, and reporting already understand it
- forcing an immediate rename would add churn before the generic contract is implemented

## Add in parallel

Add:
- `worker_result_packet`

as a new accepted schema family in the runtime.

Initial rule:
- `Python Dev` may still emit `slice_result_packet`
- future worker-role families should emit `worker_result_packet`
- later, `Python Dev` may migrate to `worker_result_packet` once the generic lane is proven

## Migration stages

### Stage G1

Definition only:
- define contracts
- do not change live compilers yet

### Stage G2

Runtime acceptance:
- add schema
- add example packet
- add validator/runtime acceptance
- add compiler path for `worker_result_packet`

### Stage G3

Dual-lane period:
- Python lane continues to allow `slice_result_packet`
- generic worker lanes use `worker_result_packet`

### Stage G4

Python migration decision:
- once TechLead reporting, traceability, and queue/runtime support are stable for `worker_result_packet`, decide whether `Python Dev` should move to the generic packet

## What should not migrate yet

Do not migrate now:
- historical `slice_result_packet` records
- the existing QA lane
- TechLead decision traffic

## Recommended implementation rule

The runtime should accept both during transition:
- `slice_result_packet`
- `worker_result_packet`

But the roadmap should treat:
- `slice_result_packet` as legacy-transitional
- `worker_result_packet` as target-state generic

## Acceptance criteria for this definition slice

This slice is complete when:
- `worker_result_packet` has a clear semantic contract
- `delivery_review_packet` has a clear semantic contract
- the Python-lane reuse vs migration rule is explicit
- the next implementation slice can add schemas without reopening the design question

## Recommended next slice

Implement the schema layer for:
- `worker_result_packet`
- `delivery_review_packet`

That should include:
- schema files
- example packets
- runtime validator acceptance
- no broad compiler migration yet
