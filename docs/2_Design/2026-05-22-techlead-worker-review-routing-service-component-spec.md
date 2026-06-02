Title: TechLead Worker Review Routing Service Component Spec
Doc-ID: paa-techlead-worker-review-routing-service-component-spec
Doc-Type: component-spec
Status: active
Lifecycle-Stage: design
Created: 2026-05-22
Last-Edited: 2026-05-23
Author: Billy Weisberg
Repo: paa-platform
Component: TechLeadWorkerReviewRoutingService
Domain: techlead-runtime
Keywords: techlead, worker-review, qa-routing, runtime, component
Depends-On: 2026-05-18-p0-techlead-runtime-extraction-plan.md, 2026-05-04-techlead-hub-state-and-routing-contract.md, 2026-05-05-phase-g-worker-result-and-delivery-review-contracts.md, 2026-05-17-workflow-lifecycle-service-component-spec.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-06-22
Summary: Defines the worker-result review and QA-routing application service extracted from the legacy TechLead runtime hub.

# TechLead Worker Review Routing Service Component Spec

Date: 2026-05-22

## Purpose

Define the extracted application service that reviews worker-result context and derives the next routing recommendation for:
- QA assignment
- return to worker
- return to Delivery Architect
- escalation or pause

This service exists to remove worker-review and QA-routing logic from:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services`

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-18-p0-techlead-runtime-extraction-plan.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-18-paa-operational-remediation-backlog.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-18-techlead-assignment-decision-service-component-spec.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-22-techlead-acceptance-decision-service-component-spec.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-workflow-lifecycle-service-component-spec.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-05-phase-g-worker-result-and-delivery-review-contracts.md`

## Architecture Placement

Layer:
- `Application Services`

Dependency stratum:
- `Stratum 3`

Primary upstream dependencies:
- `WorkflowLifecycleService`
- worker-result packet context
- issue / PR context resolved by the consumer runtime shell

Primary downstream consumers:
- `TechLead Runtime Shell`
- `QA assignment emission path`
- later `TechLeadAcceptanceDecisionService`

## Component Identity Table

| component_name | component_kind | alignment_state | system_layer | tier | status |
|---|---|---|---|---|---|
| TechLeadWorkerReviewRoutingService | service | aligned | application-services | runtime | active |

## 1. Role

`TechLeadWorkerReviewRoutingService` derives the next review-routing decision for one active slice after a worker result is returned.

Authority boundary:
- owns worker-result review outcome classification
- owns QA-routing recommendation derivation
- owns return-to-worker and return-to-delivery recommendation derivation
- owns allowed next-decision outputs for supported worker result types
- does not own packet transport
- does not own queue dispatch
- does not own workflow-state mutation
- does not own merge or closeout

## Ownership Boundary

Owned responsibilities:
- worker-result review outcome classification
- QA-routing recommendation derivation
- return-to-worker recommendation derivation
- return-to-delivery recommendation derivation
- allowed next-decision outputs for supported worker result types
- fail-closed rejected-result derivation for unsupported or unsafe review paths

## Non-Ownership Boundary

Excluded responsibilities:
- packet transport
- queue dispatch
- workflow-state mutation
- merge or closeout
- packet compilation
- acceptance and closeout decision derivation
- initial assignment decision derivation

## Collaborators

| collaborator | collaborator_kind | dependency_role |
|---|---|---|
| WorkflowLifecycleService | service | provide authoritative workflow-stage and lifecycle evaluation context |
| StructuredLogger | adapter | emit structured runtime diagnostics |
| TechLead Runtime Shell | runtime-shell | provide worker-result packet context and issue or PR context and consume structured review-routing decisions |
| QA Assignment Emission Path | flow | consume supported QA-routing recommendations and materialize QA assignment dispatch inputs |
| TechLeadAcceptanceDecisionService | service | later downstream companion service for post-QA acceptance and closeout decisions |

## Component Elements Table

| element_name | element_kind | description | owned_by_component |
|---|---|---|---|
| worker_review_routing_interface | interface | public service contract for worker-result review and next-routing recommendation over one active slice | TechLeadWorkerReviewRoutingService |
| worker_review_routing_models | dto | request, summary, and result DTOs for worker-review routing derivation | TechLeadWorkerReviewRoutingService |
| worker_review_routing_coordination_logic | implementation | default service logic for supported worker-result review classification and routing recommendation derivation | TechLeadWorkerReviewRoutingService |
| worker_review_routing_verification_surface | verification-surface | tests and governed proof surfaces for fail-closed worker-review routing behavior | TechLeadWorkerReviewRoutingService |

## Realizations Table

| element_name | realization_kind | artifact_kind | artifact_target | verification_role |
|---|---|---|---|---|
| worker_review_routing_interface | service_interface | python-module | `packages/paa-core/src/paa_core/services/techlead_worker_review_routing/contracts.py` | interface contract validation |
| worker_review_routing_models | dto | python-module | `packages/paa-core/src/paa_core/services/techlead_worker_review_routing/models.py` | DTO and result-shape validation |
| worker_review_routing_coordination_logic | service_implementation | python-module | `packages/paa-core/src/paa_core/services/techlead_worker_review_routing/default.py` | behavioral and policy-integration validation |
| worker_review_routing_verification_surface | test_module | python-module | `tests/unit/test_techlead_worker_review_routing_service.py` | service-level validation and proof |
| worker_review_routing_coordination_logic | package_export | python-module | `packages/paa-core/src/paa_core/services/techlead_worker_review_routing/__init__.py` | export-surface validation |

## 2. Component State Model

The service is stateless between calls.

It consumes already-resolved runtime context and returns stable review-routing DTOs.

### Persistent state
This component owns no primary persistent state.

It consumes already-derived runtime context from callers and may depend on evaluation outputs from `WorkflowLifecycleService`, but it does not persist rows directly.

### In-memory working state
During one call, the service may hold:
- worker result packet summary
- current workflow stage
- issue and PR identity
- optional workflow-lifecycle evaluation summary
- supported-next-action candidates
- review-routing DTOs

### State rule
This service derives routing recommendations from authoritative or already-resolved context.
It does not create new workflow truth.

## 3. Service Contract

The service provides worker-result review and next-routing recommendation derivation over one active slice.

### Inputs
- worker result packet summary
- current workflow stage
- current issue identity
- current PR identity when present
- optional workflow-lifecycle evaluation result
- optional metadata

### Outputs
- structured review-routing decision DTOs
- supported next-action recommendation
- explicit blocked or unsupported reason codes when the review cannot proceed safely
- source packet references required by downstream assignment or escalation materialization flows

### Guarantees
- worker-review routing logic is centralized outside `techlead.py`
- outputs are stable and structured
- unsupported or unsafe cases fail closed

### Non-guarantees
- this service does not send packets
- this service does not claim or acknowledge queue messages
- this service does not apply workflow transitions
- this service does not determine acceptance or closeout

## 4. Data Contract

The service operates on structured request and response DTOs.

### Primary consumed records or views
- worker-result packet summary from runtime shell inputs
- current workflow stage summary from runtime shell inputs
- optional `WorkflowLifecycleResult`
- issue summary
- PR summary

### `TechLeadWorkerReviewRoutingRequest`
Carries:
- `project_slug`
- `issue_number`
- optional `pr_number`
- `workflow_stage`
- `worker_role`
- `worker_result_type`
- optional `source_packet_schema_type`
- optional `source_packet_message_id`
- optional `workflow_lifecycle_result`
- optional `metadata`

### `TechLeadWorkerReviewRoutingSummary`
Carries:
- `decision_supported`
- `recommended_next_decision`
- `recommended_target_role`
- `qa_assignment_allowed`
- `review_summary`
- `blocking_reasons`
- `notes`

### `TechLeadWorkerReviewRoutingResult`
Carries:
- request echo identifiers
- workflow stage
- source packet references
- review-routing summary
- `ok`
- optional `reason`
- optional `details`
- optional `recommended_actions`
- optional `unattended_safe`
- optional `metadata`

### Data contract rule
The service should return stable structured review-routing objects suitable for packet materialization and runtime orchestration.
It should not return ad hoc dicts that require the runtime shell to reconstruct meaning.

## 5. Interfaces

### Provided interface
- `TechLeadWorkerReviewRoutingService`

## Plan Seed Table

| plan_name | consumer_context_key | primary_component_name | implementation_target_kind | plan_status |
|---|---|---|---|---|
| plan-materialize-techlead-worker-review-routing-service-proof-python | governance-materialization-python-techlead-worker-review-routing | TechLeadWorkerReviewRoutingService | python-runtime-service | draft_plan |

## Activity Seed Table

| activity_key | activity_name | sequence | activity_kind | element_name | realization_kind | done_definition |
|---|---|---:|---|---|---|---|
| worker-review-routing-interface-contract | Author worker-review routing interface contract | 10 | contract-authoring | worker_review_routing_interface | service_interface | Interface exposes stable review-routing entrypoint and supported result contract. |
| worker-review-routing-dto-models | Model worker-review routing DTOs | 20 | dto-materialization | worker_review_routing_models | dto | Request, summary, and result DTOs cover supported worker-result routing cases. |
| worker-review-routing-default-service | Implement default worker-review routing service | 30 | service-implementation | worker_review_routing_coordination_logic | service_implementation | Default service derives supported routing outcomes and fails closed for unsupported states. |
| worker-review-routing-validation-surface | Add worker-review routing validation surface | 40 | verification | worker_review_routing_verification_surface | test_module | Unit coverage proves supported outcomes and blocked-path behavior. |

## Activity Dependency Table

| activity_key | depends_on_activity_key | dependency_kind |
|---|---|---|
| worker-review-routing-dto-models | worker-review-routing-interface-contract | hard |
| worker-review-routing-default-service | worker-review-routing-dto-models | hard |
| worker-review-routing-validation-surface | worker-review-routing-default-service | hard |

## Verification Surface Table

| verification_surface | verification_kind | artifact_target | required_for_acceptance |
|---|---|---|---|
| techlead_worker_review_routing_unit_tests | unit-test | `tests/unit/test_techlead_worker_review_routing_service.py` | true |
| techlead_worker_review_routing_model_code_consistency | governed-proof | `python scripts/governance/paa_model_code_consistency.py --component TechLeadWorkerReviewRoutingService` | true |
| techlead_worker_review_routing_spec_model_consistency | governed-proof | `python scripts/governance/paa_component_spec_model_consistency.py --spec docs/2_Design/2026-05-22-techlead-worker-review-routing-service-component-spec.md` | true |

## 6. Primary Supported Outcomes

- `implemented_ready_for_qa` -> recommend `assign_qa`
- `blocked` -> recommend `return_to_delivery_architect`, `assign_worker`, or `pause_slice`
- `needs_clarification` -> recommend `return_to_delivery_architect` or `assign_worker`
- `cannot_complete_without_scope_change` -> recommend `return_to_delivery_architect` or `escalate_to_authority_architect`
- `superseded_by_branch_reset` -> recommend `reset_branch` or `assign_worker`

## 7. Non-Goals

This service must not become a second runtime hub.
It must not compile packets, mutate DB workflow truth, or perform queue sends.

## Constraints And Non-Goals

This service is constrained to review-routing decision derivation only.

It must not:
- perform packet transport
- perform queue dispatch
- mutate workflow-state truth
- own merge or closeout decisions
- compile packets directly
- become a second runtime hub
