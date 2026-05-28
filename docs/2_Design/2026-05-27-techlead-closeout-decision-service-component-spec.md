Title: TechLead Closeout Decision Service Component Spec
Doc-ID: paa-techlead-closeout-decision-service-component-spec
Doc-Type: component-spec
Status: active
Lifecycle-Stage: design
Created: 2026-05-27
Last-Edited: 2026-05-27
Author: Billy Weisberg
Repo: paa-platform
Component: TechLeadCloseoutDecisionService
Domain: techlead-runtime
Keywords: techlead, closeout, proof-only, decision, runtime, component
Depends-On: 2026-05-27-techlead-final-extraction-sequence-plan.md, 2026-05-18-p0-techlead-runtime-extraction-plan.md, 2026-05-04-techlead-hub-state-and-routing-contract.md, 2026-05-17-proof-only-closeout-validation.md, 2026-05-17-live-github-closeout-validation.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-06-27
Summary: Defines the closeout decision application service extracted from the legacy TechLead runtime hub.

# TechLead Closeout Decision Service Component Spec

Date: 2026-05-27

## Purpose

Define the extracted application service that derives pure closeout decision and context outputs from terminal QA-pass lineage context.

This first slice exists to remove proof-only closeout decision logic from:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-consumer/src/paa_consumer/techlead.py`

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-27-techlead-final-extraction-sequence-plan.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/5_Test/2026-05-17-proof-only-closeout-validation.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/5_Test/2026-05-17-live-github-closeout-validation.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-04-techlead-hub-state-and-routing-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-04-techlead-hub-packet-and-decision-vocabulary.md`

## Architecture Placement

Layer:
- `Application Services`

Dependency stratum:
- `Stratum 3`

Primary upstream dependencies:
- QA pass acceptance context resolved by the consumer runtime shell
- issue and PR identity resolved by the consumer runtime shell
- proof-only execution mode resolved by the consumer runtime shell

Primary downstream consumers:
- `TechLead Runtime Shell`
- closeout decision emission path
- later closeout lifecycle and GitHub merge orchestration paths

## Component Identity Table

| component_name | component_kind | alignment_state | system_layer | tier | status |
|---|---|---|---|---|---|
| TechLeadCloseoutDecisionService | service | aligned | application-services | runtime | active |

## 1. Role

`TechLeadCloseoutDecisionService` derives closeout decision and terminal context for one active slice when QA has already passed and the runtime needs a stable closeout recommendation.

Authority boundary:
- owns proof-only closeout outcome classification
- owns supported `proof_only_close_slice` recommendation derivation
- owns structured closeout decision outputs
- does not own packet transport
- does not own queue dispatch
- does not own workflow-state mutation
- does not own merge execution or GitHub mutation

## Ownership Boundary

Owned responsibilities:
- proof-only closeout outcome classification
- supported `proof_only_close_slice` recommendation derivation
- structured closeout decision outputs for supported proof-only terminal states
- fail-closed rejected-result derivation for unsupported or unsafe closeout paths

## Non-Ownership Boundary

Excluded responsibilities:
- packet transport
- queue dispatch
- workflow-state mutation
- merge execution
- GitHub issue close
- packet compilation
- assignment decision derivation
- worker-review routing derivation
- acceptance and reroute decision derivation outside this terminal proof-only slice
- physical cleanup execution

## Collaborators

| collaborator | collaborator_kind | dependency_role |
|---|---|---|
| StructuredLogger | adapter | emit structured runtime diagnostics |
| TechLead Runtime Shell | runtime-shell | provide QA-pass closeout context and consume structured closeout decisions |
| Closeout Decision Emission Path | flow | consume supported closeout recommendations and materialize decision dispatch inputs |
| Closeout Lifecycle Path | flow | later downstream consumer for merge, issue-close, and queue-closeout side effects |

## Component Elements Table

| element_name | element_kind | description | owned_by_component |
|---|---|---|---|
| closeout_decision_interface | interface | public service contract for proof-only closeout interpretation and next-decision recommendation over one active slice | TechLeadCloseoutDecisionService |
| closeout_decision_models | dto | request, summary, and result DTOs for closeout decision derivation | TechLeadCloseoutDecisionService |
| closeout_decision_coordination_logic | implementation | default service logic for supported proof-only closeout classification and recommendation derivation | TechLeadCloseoutDecisionService |
| closeout_decision_verification_surface | verification-surface | tests and governed proof surfaces for fail-closed closeout behavior | TechLeadCloseoutDecisionService |

## Realizations Table

| element_name | realization_kind | artifact_kind | artifact_target | verification_role |
|---|---|---|---|---|
| closeout_decision_interface | service_interface | python-module | `packages/paa-core/src/paa_core/services/techlead_closeout_decision/contracts.py` | interface contract validation |
| closeout_decision_models | dto | python-module | `packages/paa-core/src/paa_core/services/techlead_closeout_decision/models.py` | DTO and result-shape validation |
| closeout_decision_coordination_logic | service_implementation | python-module | `packages/paa-core/src/paa_core/services/techlead_closeout_decision/default.py` | behavioral and policy-integration validation |
| closeout_decision_verification_surface | test_module | python-module | `tests/unit/test_techlead_closeout_decision_service.py` | service-level validation and proof |
| closeout_decision_coordination_logic | package_export | python-module | `packages/paa-core/src/paa_core/services/techlead_closeout_decision/__init__.py` | export-surface validation |

## 2. Component State Model

The service is stateless between calls.

It consumes already-resolved runtime context and returns stable closeout decision DTOs.

### Persistent state
This component owns no primary persistent state.

It consumes already-derived runtime context from callers, but it does not persist rows directly.

### In-memory working state
During one call, the service may hold:
- workflow stage
- decision type intent
- issue and PR identity
- proof-only execution-mode context
- source packet references
- closeout decision DTOs

### State rule
This service derives terminal closeout recommendations from authoritative or already-resolved context.
It does not create new workflow truth.

## 3. Service Contract

The service provides proof-only closeout interpretation and next-decision recommendation derivation over one active slice.

### Inputs
- current workflow stage
- current decision type intent
- current issue identity
- current PR identity when present
- current proof-only execution mode indicator
- optional source packet metadata
- optional metadata

### Outputs
- structured closeout decision DTOs
- supported next-action recommendation
- explicit blocked or unsupported reason codes when proof-only closeout cannot proceed safely
- source packet references required by downstream decision emission or lifecycle flows

### Guarantees
- proof-only closeout decision logic is centralized outside `techlead.py`
- outputs are stable and structured
- unsupported or unsafe cases fail closed

### Non-guarantees
- this service does not send packets
- this service does not claim or acknowledge queue messages
- this service does not apply workflow transitions
- this service does not perform merge or issue-close side effects

## 4. Data Contract

The service operates on structured request and response DTOs.

### Primary consumed records or views
- current workflow stage summary from runtime shell inputs
- current issue summary
- current PR summary when present
- proof-only execution-mode summary from runtime shell inputs

### `TechLeadCloseoutDecisionRequest`
Carries:
- `project_slug`
- `issue_number`
- optional `issue_url`
- optional `pr_number`
- optional `pr_url`
- `workflow_stage`
- `decision_type`
- `proof_only_mode`
- optional `source_packet_schema_type`
- optional `source_packet_message_id`
- optional `source_packet_path`
- optional `branch_name`
- optional `canonical_branch`
- optional `metadata`

### `TechLeadCloseoutDecisionSummary`
Carries:
- `decision_supported`
- `recommended_next_decision`
- `recommended_target_role`
- `closeout_allowed`
- `closeout_decision_summary`
- `blocking_reasons`
- `notes`

### `TechLeadCloseoutDecisionResult`
Carries:
- request echo identifiers
- workflow stage
- decision type
- source packet references
- closeout decision summary
- `ok`
- optional `reason`
- optional `details`
- optional `recommended_actions`
- optional `unattended_safe`
- optional `metadata`

### Data contract rule
The service should return stable structured closeout decision objects suitable for packet materialization and runtime orchestration.
It should not return ad hoc dicts that require the runtime shell to reconstruct meaning.

## 5. Interfaces

### Provided interface
- `TechLeadCloseoutDecisionService`

## Plan Seed Table

| plan_name | consumer_context_key | primary_component_name | implementation_target_kind | plan_status |
|---|---|---|---|---|
| plan-materialize-techlead-closeout-decision-service-proof-python | governance-materialization-python-techlead-closeout-decision | TechLeadCloseoutDecisionService | python-runtime-service | draft_plan |

## Activity Seed Table

| activity_key | activity_name | sequence | activity_kind | element_name | realization_kind | done_definition |
|---|---|---:|---|---|---|---|
| closeout-decision-interface-contract | Author closeout decision interface contract | 10 | contract-authoring | closeout_decision_interface | service_interface | Interface exposes stable closeout-decision entrypoint and supported result contract. |
| closeout-decision-dto-models | Model closeout decision DTOs | 20 | dto-materialization | closeout_decision_models | dto | Request, summary, and result DTOs cover supported proof-only closeout decision cases. |
| closeout-decision-default-service | Implement default closeout decision service | 30 | service-implementation | closeout_decision_coordination_logic | service_implementation | Default service derives supported proof-only closeout outcomes and fails closed for unsupported states. |
| closeout-decision-validation-surface | Add closeout decision validation surface | 40 | verification | closeout_decision_verification_surface | test_module | Unit coverage proves supported proof-only closeout outcomes and blocked-path behavior. |

## Activity Dependency Table

| activity_key | depends_on_activity_key | dependency_kind |
|---|---|---|
| closeout-decision-dto-models | closeout-decision-interface-contract | hard |
| closeout-decision-default-service | closeout-decision-dto-models | hard |
| closeout-decision-validation-surface | closeout-decision-default-service | hard |

## Verification Surface Table

| verification_surface | verification_kind | artifact_target | required_for_acceptance |
|---|---|---|---|
| techlead_closeout_decision_unit_tests | unit-test | `tests/unit/test_techlead_closeout_decision_service.py` | true |
| techlead_closeout_decision_model_code_consistency | governed-proof | `python scripts/governance/paa_model_code_consistency.py --component TechLeadCloseoutDecisionService` | true |
| techlead_closeout_decision_spec_model_consistency | governed-proof | `python scripts/governance/paa_component_spec_model_consistency.py --spec docs/2_Design/2026-05-27-techlead-closeout-decision-service-component-spec.md` | true |

## 6. Primary Supported Outcomes

- `decision_type = proof_only_closed` with `proof_only_mode = true` -> recommend `proof_only_close_slice`
- `workflow_stage = proof_only_closed` with proof-only execution mode -> recommend `proof_only_close_slice`

## 7. Non-Goals

This service must not become a second runtime hub.
It must not compile packets, mutate DB workflow truth, or perform merge / issue-close side effects.

## Constraints And Non-Goals

This service is constrained to proof-only closeout decision derivation only.

It must not:
- perform packet transport
- perform queue dispatch
- mutate workflow-state truth
- perform merge execution
- close GitHub issues
- compile packets directly
- become a second runtime hub
