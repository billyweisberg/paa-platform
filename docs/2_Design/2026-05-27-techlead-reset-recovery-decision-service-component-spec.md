Title: TechLead Reset Recovery Decision Service Component Spec
Doc-ID: paa-techlead-reset-recovery-decision-service-component-spec
Doc-Type: component-spec
Status: active
Lifecycle-Stage: design
Created: 2026-05-27
Last-Edited: 2026-05-27
Author: Billy Weisberg
Repo: paa-platform
Component: TechLeadResetRecoveryDecisionService
Domain: techlead-runtime
Keywords: techlead, reset, recovery, lineage, decision, runtime, component
Depends-On: 2026-05-27-techlead-final-extraction-sequence-plan.md, 2026-05-18-p0-techlead-runtime-extraction-plan.md, 2026-05-04-techlead-hub-state-and-routing-contract.md, 2026-05-05-phase-g-worker-result-and-delivery-review-contracts.md, 2026-05-07-phase-h3-reset-required-mutation-plan.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-06-27
Summary: Defines the reset-required recovery decision application service extracted from the legacy TechLead runtime hub.

# TechLead Reset Recovery Decision Service Component Spec

Date: 2026-05-27

## Purpose

Define the extracted application service that interprets reset-required lineage or escalation context and derives the next reset-recovery routing recommendation.

This service exists to remove reset-required decision logic from:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services`

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-27-techlead-final-extraction-sequence-plan.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-18-p0-techlead-runtime-extraction-plan.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-07-phase-h3-reset-required-mutation-plan.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-04-techlead-hub-state-and-routing-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-04-techlead-hub-packet-and-decision-vocabulary.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/6_Deploy/2026-05-07-techlead-reset-required.md`

## Architecture Placement

Layer:
- `Application Services`

Dependency stratum:
- `Stratum 3`

Primary upstream dependencies:
- reset-required escalation context
- lineage view context resolved by the consumer runtime shell
- issue and PR context resolved by the consumer runtime shell

Primary downstream consumers:
- `TechLead Runtime Shell`
- reset-required decision emission path
- later reset cleanup and lifecycle mutation paths

## Component Identity Table

| component_name | component_kind | alignment_state | system_layer | tier | status |
|---|---|---|---|---|---|
| TechLeadResetRecoveryDecisionService | service | aligned | application-services | runtime | active |

## 1. Role

`TechLeadResetRecoveryDecisionService` derives the next reset-recovery decision for one active slice when the current lineage indicates reset-required recovery instead of more in-place cleanup.

Authority boundary:
- owns reset-required outcome classification
- owns supported `reset_branch` recommendation derivation
- owns structured reset-recovery decision outputs
- does not own packet transport
- does not own queue dispatch
- does not own workflow-state mutation
- does not own branch cleanup execution

## Ownership Boundary

Owned responsibilities:
- reset-required outcome classification
- supported `reset_branch` recommendation derivation
- structured reset-recovery decision outputs for supported lineage states
- fail-closed rejected-result derivation for unsupported or unsafe reset paths

## Non-Ownership Boundary

Excluded responsibilities:
- packet transport
- queue dispatch
- workflow-state mutation
- branch cleanup execution
- packet compilation
- worker-review routing derivation
- acceptance and closeout decision derivation
- supersede lineage decision derivation

## Collaborators

| collaborator | collaborator_kind | dependency_role |
|---|---|---|
| StructuredLogger | adapter | emit structured runtime diagnostics |
| TechLead Runtime Shell | runtime-shell | provide reset-related escalation and lineage context and consume structured reset decisions |
| Reset-Required Decision Emission Path | flow | consume supported reset recommendations and materialize decision dispatch inputs |
| Reset Cleanup Lifecycle Path | flow | later downstream consumer for physical cleanup after reset-required decision publication |

## Component Elements Table

| element_name | element_kind | description | owned_by_component |
|---|---|---|---|
| reset_recovery_decision_interface | interface | public service contract for reset-required interpretation and next-routing recommendation over one active slice | TechLeadResetRecoveryDecisionService |
| reset_recovery_decision_models | dto | request, summary, and result DTOs for reset-recovery decision derivation | TechLeadResetRecoveryDecisionService |
| reset_recovery_decision_coordination_logic | implementation | default service logic for supported reset-required classification and routing recommendation derivation | TechLeadResetRecoveryDecisionService |
| reset_recovery_decision_verification_surface | verification-surface | tests and governed proof surfaces for fail-closed reset-recovery decision behavior | TechLeadResetRecoveryDecisionService |

## Realizations Table

| element_name | realization_kind | artifact_kind | artifact_target | verification_role |
|---|---|---|---|---|
| reset_recovery_decision_interface | service_interface | python-module | `packages/paa-core/src/paa_core/services/techlead_reset_recovery_decision/contracts.py` | interface contract validation |
| reset_recovery_decision_models | dto | python-module | `packages/paa-core/src/paa_core/services/techlead_reset_recovery_decision/models.py` | DTO and result-shape validation |
| reset_recovery_decision_coordination_logic | service_implementation | python-module | `packages/paa-core/src/paa_core/services/techlead_reset_recovery_decision/default.py` | behavioral and policy-integration validation |
| reset_recovery_decision_verification_surface | test_module | python-module | `tests/unit/test_techlead_reset_recovery_decision_service.py` | service-level validation and proof |
| reset_recovery_decision_coordination_logic | package_export | python-module | `packages/paa-core/src/paa_core/services/techlead_reset_recovery_decision/__init__.py` | export-surface validation |

## 2. Component State Model

The service is stateless between calls.

It consumes already-resolved runtime context and returns stable reset-recovery decision DTOs.

### Persistent state
This component owns no primary persistent state.

It consumes already-derived runtime context from callers, but it does not persist rows directly.

### In-memory working state
During one call, the service may hold:
- workflow stage
- lineage state
- issue and PR identity
- reset escalation summary
- source packet references
- reset-recovery decision DTOs

### State rule
This service derives routing recommendations from authoritative or already-resolved context.
It does not create new workflow truth.

## 3. Service Contract

The service provides reset-required interpretation and next-routing recommendation derivation over one active slice.

### Inputs
- current workflow stage
- current lineage state
- current issue identity
- current PR identity when present
- optional reset escalation type
- optional reset escalation summary
- optional source packet metadata
- optional metadata

### Outputs
- structured reset-recovery decision DTOs
- supported next-action recommendation
- explicit blocked or unsupported reason codes when reset recovery cannot proceed safely
- source packet references required by downstream decision emission or lifecycle mutation flows

### Guarantees
- reset-required decision logic is centralized outside `techlead.py`
- outputs are stable and structured
- unsupported or unsafe cases fail closed

### Non-guarantees
- this service does not send packets
- this service does not claim or acknowledge queue messages
- this service does not apply workflow transitions
- this service does not perform branch cleanup

## 4. Data Contract

The service operates on structured request and response DTOs.

### Primary consumed records or views
- current workflow stage summary from runtime shell inputs
- current lineage state summary from runtime shell inputs
- reset escalation summary from runtime shell inputs
- issue summary
- PR summary

### `TechLeadResetRecoveryDecisionRequest`
Carries:
- `project_slug`
- `issue_number`
- optional `issue_url`
- optional `pr_number`
- optional `pr_url`
- `workflow_stage`
- `lineage_state`
- optional `reset_escalation_type`
- optional `reset_escalation_summary`
- optional `reset_escalation_details`
- optional `source_packet_schema_type`
- optional `source_packet_message_id`
- optional `source_packet_path`
- optional `branch_name`
- optional `metadata`

### `TechLeadResetRecoveryDecisionSummary`
Carries:
- `decision_supported`
- `recommended_next_decision`
- `recommended_target_role`
- `reset_allowed`
- `reset_recovery_summary`
- `blocking_reasons`
- `notes`

### `TechLeadResetRecoveryDecisionResult`
Carries:
- request echo identifiers
- workflow stage
- lineage state
- source packet references
- reset-recovery decision summary
- `ok`
- optional `reason`
- optional `details`
- optional `recommended_actions`
- optional `unattended_safe`
- optional `metadata`

### Data contract rule
The service should return stable structured reset-recovery decision objects suitable for packet materialization and runtime orchestration.
It should not return ad hoc dicts that require the runtime shell to reconstruct meaning.

## 5. Interfaces

### Provided interface
- `TechLeadResetRecoveryDecisionService`

## Plan Seed Table

| plan_name | consumer_context_key | primary_component_name | implementation_target_kind | plan_status |
|---|---|---|---|---|
| plan-materialize-techlead-reset-recovery-decision-service-proof-python | governance-materialization-python-techlead-reset-recovery-decision | TechLeadResetRecoveryDecisionService | python-runtime-service | draft_plan |

## Activity Seed Table

| activity_key | activity_name | sequence | activity_kind | element_name | realization_kind | done_definition |
|---|---|---:|---|---|---|---|
| reset-recovery-interface-contract | Author reset-recovery interface contract | 10 | contract-authoring | reset_recovery_decision_interface | service_interface | Interface exposes stable reset-recovery decision entrypoint and supported result contract. |
| reset-recovery-dto-models | Model reset-recovery decision DTOs | 20 | dto-materialization | reset_recovery_decision_models | dto | Request, summary, and result DTOs cover supported reset-recovery decision cases. |
| reset-recovery-default-service | Implement default reset-recovery decision service | 30 | service-implementation | reset_recovery_decision_coordination_logic | service_implementation | Default service derives supported reset outcomes and fails closed for unsupported states. |
| reset-recovery-validation-surface | Add reset-recovery decision validation surface | 40 | verification | reset_recovery_decision_verification_surface | test_module | Unit coverage proves supported outcomes and blocked-path behavior. |

## Activity Dependency Table

| activity_key | depends_on_activity_key | dependency_kind |
|---|---|---|
| reset-recovery-dto-models | reset-recovery-interface-contract | hard |
| reset-recovery-default-service | reset-recovery-dto-models | hard |
| reset-recovery-validation-surface | reset-recovery-default-service | hard |

## Verification Surface Table

| verification_surface | verification_kind | artifact_target | required_for_acceptance |
|---|---|---|---|
| techlead_reset_recovery_decision_unit_tests | unit-test | `tests/unit/test_techlead_reset_recovery_decision_service.py` | true |
| techlead_reset_recovery_decision_model_code_consistency | governed-proof | `python scripts/governance/paa_model_code_consistency.py --component TechLeadResetRecoveryDecisionService` | true |
| techlead_reset_recovery_decision_spec_model_consistency | governed-proof | `python scripts/governance/paa_component_spec_model_consistency.py --spec docs/2_Design/2026-05-27-techlead-reset-recovery-decision-service-component-spec.md` | true |

## 6. Primary Supported Outcomes

- `lineage_state = reset_required` -> recommend `reset_branch`
- `workflow_stage = dev_reset_required` -> recommend `reset_branch`
- `reset_branch_required` escalation -> recommend `reset_branch`
- `reset_branch_recommended` escalation -> recommend `reset_branch`

## 7. Non-Goals

This service must not become a second runtime hub.
It must not compile packets, mutate DB workflow truth, or perform branch cleanup.

## Constraints And Non-Goals

This service is constrained to reset-recovery decision derivation only.

It must not:
- perform packet transport
- perform queue dispatch
- mutate workflow-state truth
- perform branch cleanup
- compile packets directly
- become a second runtime hub
