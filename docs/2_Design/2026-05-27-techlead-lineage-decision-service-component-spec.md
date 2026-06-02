Title: TechLead Lineage Decision Service Component Spec
Doc-ID: paa-techlead-lineage-decision-service-component-spec
Doc-Type: component-spec
Status: active
Lifecycle-Stage: design
Created: 2026-05-27
Last-Edited: 2026-05-27
Author: Billy Weisberg
Repo: paa-platform
Component: TechLeadLineageDecisionService
Domain: techlead-runtime
Keywords: techlead, lineage, superseded, decision, runtime, component
Depends-On: 2026-05-27-techlead-final-extraction-sequence-plan.md, 2026-05-18-p0-techlead-runtime-extraction-plan.md, 2026-05-04-techlead-hub-state-and-routing-contract.md, 2026-05-05-phase-e-decision-lineage-query-helper.md, 2026-05-07-phase-h5-superseded-cleanup-plan.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-06-27
Summary: Defines the superseded-lineage decision application service extracted from the legacy TechLead runtime hub.

# TechLead Lineage Decision Service Component Spec

Date: 2026-05-27

## Purpose

Define the extracted application service that interprets superseded lineage or QA-escalation context and derives the next lineage decision recommendation.

This first slice exists to remove superseded decision logic from:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services`

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-27-techlead-final-extraction-sequence-plan.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-07-phase-h5-superseded-cleanup-plan.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-04-techlead-hub-state-and-routing-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-04-techlead-hub-packet-and-decision-vocabulary.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/6_Deploy/2026-05-07-techlead-superseded-cleanup.md`

## Architecture Placement

Layer:
- `Application Services`

Dependency stratum:
- `Stratum 3`

Primary upstream dependencies:
- superseded escalation context
- lineage view context resolved by the consumer runtime shell
- issue and PR context resolved by the consumer runtime shell

Primary downstream consumers:
- `TechLead Runtime Shell`
- superseded decision emission path
- later superseded cleanup lifecycle path

## Component Identity Table

| component_name | component_kind | alignment_state | system_layer | tier | status |
|---|---|---|---|---|---|
| TechLeadLineageDecisionService | service | aligned | application-services | runtime | active |

## 1. Role

`TechLeadLineageDecisionService` derives the next lineage-state decision for one active slice when the current lineage indicates superseded recovery instead of more active QA processing.

Authority boundary:
- owns superseded-lineage outcome classification
- owns supported `supersede_branch_lineage` recommendation derivation
- owns structured lineage decision outputs
- does not own packet transport
- does not own queue dispatch
- does not own workflow-state mutation
- does not own physical cleanup execution

## Ownership Boundary

Owned responsibilities:
- superseded-lineage outcome classification
- supported `supersede_branch_lineage` recommendation derivation
- structured lineage decision outputs for supported superseded states
- fail-closed rejected-result derivation for unsupported or unsafe superseded paths

## Non-Ownership Boundary

Excluded responsibilities:
- packet transport
- queue dispatch
- workflow-state mutation
- physical cleanup execution
- packet compilation
- assignment decision derivation
- worker-review routing derivation
- acceptance and closeout decision derivation
- reset-required decision derivation

## Collaborators

| collaborator | collaborator_kind | dependency_role |
|---|---|---|
| StructuredLogger | adapter | emit structured runtime diagnostics |
| TechLead Runtime Shell | runtime-shell | provide superseded escalation and lineage context and consume structured lineage decisions |
| Superseded Decision Emission Path | flow | consume supported superseded recommendations and materialize decision dispatch inputs |
| Superseded Cleanup Lifecycle Path | flow | later downstream consumer for physical cleanup after superseded decision publication |

## Component Elements Table

| element_name | element_kind | description | owned_by_component |
|---|---|---|---|
| lineage_decision_interface | interface | public service contract for superseded-lineage interpretation and next-decision recommendation over one active slice | TechLeadLineageDecisionService |
| lineage_decision_models | dto | request, summary, and result DTOs for superseded-lineage decision derivation | TechLeadLineageDecisionService |
| lineage_decision_coordination_logic | implementation | default service logic for supported superseded-lineage classification and recommendation derivation | TechLeadLineageDecisionService |
| lineage_decision_verification_surface | verification-surface | tests and governed proof surfaces for fail-closed lineage decision behavior | TechLeadLineageDecisionService |

## Realizations Table

| element_name | realization_kind | artifact_kind | artifact_target | verification_role |
|---|---|---|---|---|
| lineage_decision_interface | service_interface | python-module | `packages/paa-core/src/paa_core/services/techlead_lineage_decision/contracts.py` | interface contract validation |
| lineage_decision_models | dto | python-module | `packages/paa-core/src/paa_core/services/techlead_lineage_decision/models.py` | DTO and result-shape validation |
| lineage_decision_coordination_logic | service_implementation | python-module | `packages/paa-core/src/paa_core/services/techlead_lineage_decision/default.py` | behavioral and policy-integration validation |
| lineage_decision_verification_surface | test_module | python-module | `tests/unit/test_techlead_lineage_decision_service.py` | service-level validation and proof |
| lineage_decision_coordination_logic | package_export | python-module | `packages/paa-core/src/paa_core/services/techlead_lineage_decision/__init__.py` | export-surface validation |

## 2. Component State Model

The service is stateless between calls.

It consumes already-resolved runtime context and returns stable lineage decision DTOs.

### Persistent state
This component owns no primary persistent state.

It consumes already-derived runtime context from callers, but it does not persist rows directly.

### In-memory working state
During one call, the service may hold:
- workflow stage
- lineage state
- issue and PR identity
- superseded escalation summary
- source packet references
- lineage decision DTOs

### State rule
This service derives lineage recommendations from authoritative or already-resolved context.
It does not create new workflow truth.

## 3. Service Contract

The service provides superseded-lineage interpretation and next-decision recommendation derivation over one active slice.

### Inputs
- current workflow stage
- current lineage state
- current issue identity
- current PR identity when present
- optional superseded escalation type
- optional superseded escalation summary
- optional superseded escalation details
- optional source packet metadata
- optional metadata

### Outputs
- structured lineage decision DTOs
- supported next-action recommendation
- explicit blocked or unsupported reason codes when lineage supersession cannot proceed safely
- source packet references required by downstream decision emission or lifecycle cleanup flows

### Guarantees
- superseded-lineage decision logic is centralized outside `techlead.py`
- outputs are stable and structured
- unsupported or unsafe cases fail closed

### Non-guarantees
- this service does not send packets
- this service does not claim or acknowledge queue messages
- this service does not apply workflow transitions
- this service does not perform physical cleanup

## 4. Data Contract

The service operates on structured request and response DTOs.

### Primary consumed records or views
- current workflow stage summary from runtime shell inputs
- current lineage state summary from runtime shell inputs
- superseded escalation summary from runtime shell inputs
- issue summary
- PR summary

### `TechLeadLineageDecisionRequest`
Carries:
- `project_slug`
- `issue_number`
- optional `issue_url`
- optional `pr_number`
- optional `pr_url`
- `workflow_stage`
- `lineage_state`
- optional `superseded_escalation_type`
- optional `superseded_escalation_summary`
- optional `superseded_escalation_details`
- optional `source_packet_schema_type`
- optional `source_packet_message_id`
- optional `source_packet_path`
- optional `branch_name`
- optional `superseded_branch`
- optional `metadata`

### `TechLeadLineageDecisionSummary`
Carries:
- `decision_supported`
- `recommended_next_decision`
- `recommended_target_role`
- `supersede_allowed`
- `lineage_decision_summary`
- `blocking_reasons`
- `notes`

### `TechLeadLineageDecisionResult`
Carries:
- request echo identifiers
- workflow stage
- lineage state
- source packet references
- lineage decision summary
- `ok`
- optional `reason`
- optional `details`
- optional `recommended_actions`
- optional `unattended_safe`
- optional `metadata`

### Data contract rule
The service should return stable structured lineage decision objects suitable for packet materialization and runtime orchestration.
It should not return ad hoc dicts that require the runtime shell to reconstruct meaning.

## 5. Interfaces

### Provided interface
- `TechLeadLineageDecisionService`

## Plan Seed Table

| plan_name | consumer_context_key | primary_component_name | implementation_target_kind | plan_status |
|---|---|---|---|---|
| plan-materialize-techlead-lineage-decision-service-proof-python | governance-materialization-python-techlead-lineage-decision | TechLeadLineageDecisionService | python-runtime-service | draft_plan |

## Activity Seed Table

| activity_key | activity_name | sequence | activity_kind | element_name | realization_kind | done_definition |
|---|---|---:|---|---|---|---|
| lineage-decision-interface-contract | Author lineage decision interface contract | 10 | contract-authoring | lineage_decision_interface | service_interface | Interface exposes stable lineage-decision entrypoint and supported result contract. |
| lineage-decision-dto-models | Model lineage decision DTOs | 20 | dto-materialization | lineage_decision_models | dto | Request, summary, and result DTOs cover supported superseded-lineage decision cases. |
| lineage-decision-default-service | Implement default lineage decision service | 30 | service-implementation | lineage_decision_coordination_logic | service_implementation | Default service derives supported superseded outcomes and fails closed for unsupported states. |
| lineage-decision-validation-surface | Add lineage decision validation surface | 40 | verification | lineage_decision_verification_surface | test_module | Unit coverage proves supported outcomes and blocked-path behavior. |

## Activity Dependency Table

| activity_key | depends_on_activity_key | dependency_kind |
|---|---|---|
| lineage-decision-dto-models | lineage-decision-interface-contract | hard |
| lineage-decision-default-service | lineage-decision-dto-models | hard |
| lineage-decision-validation-surface | lineage-decision-default-service | hard |

## Verification Surface Table

| verification_surface | verification_kind | artifact_target | required_for_acceptance |
|---|---|---|---|
| techlead_lineage_decision_unit_tests | unit-test | `tests/unit/test_techlead_lineage_decision_service.py` | true |
| techlead_lineage_decision_model_code_consistency | governed-proof | `python scripts/governance/paa_model_code_consistency.py --component TechLeadLineageDecisionService` | true |
| techlead_lineage_decision_spec_model_consistency | governed-proof | `python scripts/governance/paa_component_spec_model_consistency.py --spec docs/2_Design/2026-05-27-techlead-lineage-decision-service-component-spec.md` | true |

## 6. Primary Supported Outcomes

- `lineage_state = superseded` -> recommend `supersede_branch_lineage`
- `superseded_escalation_type = qa_escalation_superseded` -> recommend `supersede_branch_lineage`
- `workflow_stage = qa_pending` with superseded escalation -> recommend `supersede_branch_lineage`

## 7. Non-Goals

This service must not become a second runtime hub.
It must not compile packets, mutate DB workflow truth, or perform physical cleanup.

## Constraints And Non-Goals

This service is constrained to superseded-lineage decision derivation only.

It must not:
- perform packet transport
- perform queue dispatch
- mutate workflow-state truth
- perform physical cleanup
- compile packets directly
- become a second runtime hub
