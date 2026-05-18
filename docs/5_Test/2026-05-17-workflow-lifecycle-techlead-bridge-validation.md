# Workflow Lifecycle TechLead Bridge Validation

Date: 2026-05-17
Status: pass

## Purpose

Validate the first downstream consumer integration of `WorkflowLifecycleService` for the
`worker_result_returned` transition family.

The intent of this validation is narrow:
- confirm the TechLead consumer path no longer relies only on inline packet-stage inference
- confirm it can resolve authoritative workflow identity from the local PAA database
- confirm it delegates worker-result transition evaluation to `WorkflowLifecycleService`
- confirm the resulting workflow decision is surfaced back into the TechLead runtime path

## Integrated Consumer Path

Consumer:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-consumer/src/paa_consumer/techlead.py`

Bridge helper:
- `workflow_lifecycle_worker_result_evaluation(...)`

Integration point:
- `derive_workflow(...)`
- branch:
  - pending `worker_result_packet` addressed to `techlead`

## Bridge Shape

For a pending worker-result packet, the consumer path now:

1. resolves `work_item_id` from:
   - `project_slug`
   - `issue_number`
2. constructs:
   - `PostgresWorkflowStateRepository`
   - `PostgresRuntimeEventRepository`
   - `DefaultExecutionPackageResolutionService`
   - `DefaultWorkflowLifecycleService`
3. evaluates:
   - `requested_transition_type = worker_result_returned`
   - `requested_from_stage = worker_execution_in_progress`
   - `source_message_id_external`
   - `source_packet_schema_type = worker_result_packet`
4. receives back:
   - transition allowed / denied
   - blocking reasons
   - notes
   - recommended next action
   - resolved target stage
5. injects that lifecycle output into the TechLead escalation details for the worker-result review path

## What Is Proven

### 1. Real DB identity resolution is used

The consumer path does not guess a workflow UUID.

It resolves the DB-primary `work_item_id` via:
- `resolve_work_item_id(...)`

That means the workflow service is called with authoritative workflow identity, not only queue-preview context.

### 2. Worker-result evaluation is delegated to the service

The consumer now asks `WorkflowLifecycleService` to interpret the worker-result transition family.

That closes the gap between:
- packet preview
- workflow truth
- policy-backed transition evaluation

### 3. The service output is carried back into consumer behavior

The worker-result escalation details now include:
- `workflow_transition_allowed`
- `workflow_blocking_reasons`
- `workflow_notes`
- `workflow_recommended_next_action`
- `workflow_target_stage`

So the consumer path is now informed by real workflow evaluation rather than only local packet heuristics.

## What Was Not Broadened

This integration intentionally does **not**:
- apply workflow-state mutations from `techlead.py`
- rewrite QA or delivery-review transition handling
- replace all workflow heuristics in the consumer runtime
- claim the TechLead runtime is fully lifecycle-service-driven

This is a first consumer bridge, not a full workflow-runtime rewrite.

## Validation Performed

Focused tests:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/tests/unit/test_techlead_self_hosted.py`

Key test coverage added:
- the bridge helper resolves `work_item_id` and builds the expected lifecycle request
- `derive_workflow(...)` uses the lifecycle result on the worker-result path

Suite results:
- focused TechLead tests: pass
- full unit suite: pass
- total unit tests passing at validation time: `100`

## Decision

Decision: `GO`

For the first workflow consumer bridge, the current slice is valid.

The system now has:
- one authoritative workflow service
- one real transition family
- one real downstream consumer integration

## Next Recommended Step

Choose one of:

1. extend the workflow service with:
   - `qa_result_returned`
2. add a mutation/apply bridge from one real runtime action path
3. continue replacing inline workflow heuristics in `techlead.py` incrementally
