Title: Methodology Execution Projection Service Component Spec
Doc-ID: methodology-execution-projection-service-component-spec
Doc-Type: component-spec
Status: active
Lifecycle-Stage: design
Created: 2026-05-31
Last-Edited: 2026-05-31
Author: Billy Weisberg
Repo: paa-platform
Component: MethodologyExecutionProjectionService
Domain: methodology-execution
Keywords: paa, methodology, execution, projection, status, next, explain, service, component
Depends-On: 2026-05-30-paa-methodology-execution-state-model.md, 2026-05-30-paa-methodology-execution-object-model.md, 2026-05-30-paa-methodology-execution-transition-state-machine-table.md, 2026-05-30-methodology-execution-repository-contract-and-persistence-mapping.md, 2026-05-30-methodology-execution-repository-component-spec.md, 2026-05-30-methodology-execution-state-service-component-spec.md, 2026-05-30-paa-methodology-execution-preflight-rule-table.md, 2026-05-20-component-spec-template-materialization-bridge.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-06-30
Summary: Defines the governed application service that projects persisted methodology-execution truth into stable operator-facing status, next-action, and explain surfaces without owning mutation, rendering, or preflight enforcement.

# Methodology Execution Projection Service Component Spec

Date: 2026-05-31

## Purpose

Define the governed application service that projects persisted methodology-execution truth into stable operator-facing status, next-action, and explain surfaces without owning mutation, rendering, or preflight enforcement.

This component exists to make the methodology pointer legible and reusable across:
- pointer-facing CLI reads such as `paa status`, `paa next`, and `paa explain`
- runtime and operator diagnostics that need one stable current-state summary
- future preflight enforcement that should consume a clear projection instead of reconstructing state locally

This first slice is intentionally projection-service first so the CLI can read one coherent methodology pointer view before stronger lane-aware preflight is wired into command enforcement.

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-30-paa-methodology-execution-state-model.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-30-paa-methodology-execution-object-model.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-30-paa-methodology-execution-transition-state-machine-table.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-30-paa-methodology-execution-preflight-rule-table.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-30-methodology-execution-repository-contract-and-persistence-mapping.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-30-methodology-execution-repository-component-spec.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-30-methodology-execution-state-service-component-spec.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-30-paa-methodology-execution-component-family.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/current/policy/component-spec-template-materialization-bridge.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/4_Build/2026-05-27-component-realization-loop.md`

## Architecture Placement

Layer:
- `Application Services`

Dependency stratum:
- `Stratum 3`

Primary upstream dependencies:
- `MethodologyExecutionRepository`
- `MethodologyExecutionStateService`
- methodology-execution controlled vocabulary values for lane, stage, step, status, owner role, and transition kind
- methodology-execution transition/state-machine authority
- current project/work item/component/design-package/implementation-plan identity truth supplied through bindings

Primary downstream consumers:
- `PAAOperatorCLI`
- future `paa status`, `paa next`, and `paa explain` command surfaces
- `MethodologyExecutionPreflightService`
- future runtime controllers that need a stable current-pointer summary before deciding operator guidance or redirects

## Component Identity Table

| component_name | component_kind | alignment_state | system_layer | tier | status |
|---|---|---|---|---|---|
| MethodologyExecutionProjectionService | service | aligned | application-services | runtime | active |

## 1. Role

`MethodologyExecutionProjectionService` loads persisted methodology-execution truth, stitches the current root and bindings into stable operator-facing projection objects, and derives readable status, next-action, and explain summaries.

Authority boundary:
- owns current methodology pointer projection through one explicit service contract
- owns translation from persisted root and binding truth into stable operator-facing summary DTOs
- owns derived next-action and explanation summaries for the supported first slice
- owns fail-closed outcomes for missing or ambiguous pointer truth in the supported first slice
- does not own current-state mutation
- does not own repository SQL
- does not own CLI rendering
- does not own preflight command classification or redirect decisions
- does not own implementation-plan, workflow, packet, or acceptance mutation outside methodology pointer projection

## Ownership Boundary

Owned responsibilities:
- load current methodology execution by execution id or primary anchors
- stitch root, bindings, and minimal external reference context into a readable projection
- derive a stable status summary from persisted lane, stage, step, status, owner role, and next-action values
- derive a stable next-action projection from current pointer truth for the supported first slice
- derive an explain projection that summarizes why the current pointer is in its present state for the supported first slice
- return structured blocked or missing-truth results when the current projection cannot be safely produced

## Non-Ownership Boundary

Excluded responsibilities:
- current-state mutation or transition persistence
- repository SQL construction
- CLI output rendering
- command routing
- lane-aware preflight outcome categories such as `allowed`, `warn`, `blocked`, or `redirect`
- implementation-plan activity mutation
- workflow transition mutation
- queue claim mutation
- packet publication
- merge or issue-close execution

## Collaborators

| collaborator | collaborator_kind | dependency_role |
|---|---|---|
| `MethodologyExecutionRepository` | repository | load current pointer roots, bindings, and stitched projection input records |
| `MethodologyExecutionStateService` | service | provide aligned state-summary semantics and shared transition vocabulary for supported slices |
| StructuredLogger | adapter | emit projection diagnostics and missing-truth events |
| methodology transition-state authority | design authority | define stable transition semantics used by next-action and explanation projection |
| current project/work item/component identity truth | upstream model truth | provide stable external anchors surfaced in projection results |
| `MethodologyExecutionPreflightService` | downstream service | consume projection outputs when classifying command requests and redirect targets |
| `PAAOperatorCLI` | downstream host surface | render projection outputs for operator-facing pointer reads |

## Component Elements Table

| element_name | element_kind | description | owned_by_component |
|---|---|---|---|
| methodology_execution_projection_service_interface | interface | public application-service contract for loading status, next-action, and explain projections from methodology pointer truth | MethodologyExecutionProjectionService |
| methodology_execution_projection_service_models | dto | request, status-projection, next-action-projection, explain-projection, and result DTOs | MethodologyExecutionProjectionService |
| methodology_execution_projection_service_logic | implementation | default service logic for repository reads, projection stitching, summary derivation, and fail-closed outcomes | MethodologyExecutionProjectionService |
| methodology_execution_projection_service_verification_surface | verification-surface | tests and governed proof surfaces for projection loading, next-action derivation, explain summaries, and missing-truth behavior | MethodologyExecutionProjectionService |

## Realizations Table

| element_name | realization_kind | artifact_kind | artifact_target | verification_role |
|---|---|---|---|---|
| methodology_execution_projection_service_interface | service_interface | python-module | `packages/paa-core/src/paa_core/services/methodology_execution_projection/contracts.py` | interface contract validation |
| methodology_execution_projection_service_models | dto | python-module | `packages/paa-core/src/paa_core/services/methodology_execution_projection/models.py` | DTO and projection-shape validation |
| methodology_execution_projection_service_logic | service_implementation | python-module | `packages/paa-core/src/paa_core/services/methodology_execution_projection/default.py` | projection behavior and repository-coordination validation |
| methodology_execution_projection_service_verification_surface | test_module | python-module | `tests/unit/test_methodology_execution_projection_service.py` | service-level validation and proof |
| methodology_execution_projection_service_logic | package_export | python-module | `packages/paa-core/src/paa_core/services/methodology_execution_projection/__init__.py` | export-surface validation |

## 2. Component State Model

The service is stateless between calls.

It consumes persisted methodology-execution truth and returns structured projection objects over one bounded service call.

### Persistent state
This component owns no primary persistent records itself.

It reads from:
- `paa.methodology_executions`
- `paa.methodology_execution_events`
- `paa.methodology_execution_bindings`

through `MethodologyExecutionRepository`.

### In-memory working state
During one call, the service may hold:
- current methodology execution root
- current binding set
- stitched projection input record
- derived status summary
- derived next-action summary
- derived explanation summary
- blocked or missing-truth details

### State rule
This service decides supported operator-facing methodology pointer projection for the first governed slice.
It does not become the primary owner of unrelated downstream runtime truth.

## 3. Service Contract

The service provides explicit methodology pointer projection and explanation over one bounded service boundary.

### Inputs
- methodology execution id or primary anchors
- optional project id
- optional work item id
- optional component id
- optional projection mode such as `status`, `next`, or `explain`
- optional caller context and metadata

### Outputs
- structured status projections
- structured next-action projections
- structured explain projections
- explicit missing-truth or ambiguous-resolution result objects

### Guarantees
- operator-facing methodology pointer summaries are centralized outside CLI shells
- projection results are stable and suitable for CLI status/next/explain surfaces
- supported first-slice outputs fail closed when pointer truth is missing or ambiguous
- projection logic does not mutate current methodology pointer truth

### Non-guarantees
- this service does not render CLI output
- this service does not mutate methodology state
- this service does not perform queue or packet side effects
- this service does not decide full command-family preflight outcomes in the first slice

## 4. Data Contract

The service operates on structured request and response DTOs.

### Primary consumed records or views
- current `MethodologyExecutionRecord`
- current `MethodologyExecutionBindingRecord` set
- stitched `MethodologyExecutionProjectionInputRecord`
- transition-state-machine authority and supported next-action semantics

### `MethodologyExecutionProjectionRequest`
Carries:
- `methodology_execution_id` or primary anchors
- optional `project_id`
- optional `work_item_id`
- optional `component_id`
- optional `projection_mode`
- optional `actor_role_id`
- optional `actor_name`
- optional `metadata`

### `MethodologyExecutionStatusProjection`
Carries:
- current execution id
- current lane, stage, step, and status
- current owner role
- next action key
- blocked reason when present
- key bound ids and references
- concise human-readable summary text

### `MethodologyExecutionNextActionProjection`
Carries:
- current execution id
- recommended next action key
- recommended owner role
- current lane, stage, and step context
- prerequisite summary
- blocked reason when present
- optional follow-up references such as component id or implementation plan id

### `MethodologyExecutionExplainProjection`
Carries:
- current execution id
- current lane, stage, step, and status
- current owner role
- explanation summary text
- current transition context or last significant event summary when available
- key bound ids and references
- blocked reason when present

### `MethodologyExecutionProjectionResult`
Carries:
- request echo identifiers
- current execution id when resolved
- optional status projection
- optional next-action projection
- optional explain projection
- `ok`
- optional `reason`
- optional `details`
- optional `metadata`

### Data contract rule
The service should return stable structured projection objects suitable for pointer-facing CLI reads and later preflight classification.
It should not return ad hoc dicts that require downstream shells to reconstruct methodology meaning.

## 5. Interfaces

### Provided interface
- `MethodologyExecutionProjectionService`

### Required collaborator interfaces
- `MethodologyExecutionRepository`
- `MethodologyExecutionStateService`
- `StructuredLogger`

## Plan Seed Table

| plan_name | consumer_context_key | primary_component_name | implementation_target_kind | plan_status |
|---|---|---|---|---|
| plan-materialize-methodology-execution-projection-service-proof-python | governance-materialization-python-methodology-execution-projection-service | MethodologyExecutionProjectionService | python-runtime-service | draft_plan |

## Activity Seed Table

| activity_key | activity_name | sequence | activity_kind | element_name | realization_kind | done_definition |
|---|---|---:|---|---|---|---|
| methodology-execution-projection-service-interface-contract | Author methodology execution projection service interface contract | 10 | contract-authoring | methodology_execution_projection_service_interface | service_interface | Interface exposes stable status, next-action, and explain projection entrypoints for the supported first slice. |
| methodology-execution-projection-service-dto-models | Model methodology execution projection service DTOs | 20 | dto-materialization | methodology_execution_projection_service_models | dto | Request, status, next-action, explain, and result DTOs cover supported pointer-facing projection outcomes. |
| methodology-execution-projection-service-default-service | Implement default methodology execution projection service | 30 | service-implementation | methodology_execution_projection_service_logic | service_implementation | Default service loads current execution truth, derives stable projections for the supported first slice, and fails closed for missing or ambiguous pointer truth. |
| methodology-execution-projection-service-validation-surface | Add methodology execution projection service validation surface | 40 | verification | methodology_execution_projection_service_verification_surface | test_module | Unit coverage proves supported status, next-action, and explain projection behavior plus missing-truth outcomes for the first slice. |

## Activity Dependency Table

| activity_key | depends_on_activity_key | dependency_kind |
|---|---|---|
| methodology-execution-projection-service-dto-models | methodology-execution-projection-service-interface-contract | hard |
| methodology-execution-projection-service-default-service | methodology-execution-projection-service-dto-models | hard |
| methodology-execution-projection-service-validation-surface | methodology-execution-projection-service-default-service | hard |

## Verification Surface Table

| verification_surface | verification_kind | artifact_target | required_for_acceptance |
|---|---|---|---|
| methodology execution projection service contract tests | unit-test | `tests/unit/test_methodology_execution_projection_service.py` | true |
| methodology execution projection service DTO tests | unit-test | `tests/unit/test_methodology_execution_projection_service.py` | true |
| methodology execution projection service projection behavior tests | unit-test | `tests/unit/test_methodology_execution_projection_service.py` | true |
| methodology execution projection service governed model/code consistency | governance-check | `scripts/governance/paa_model_code_consistency.py --component MethodologyExecutionProjectionService` | true |

## 6. First Slice Focus

The first governed realization slice should support:
- load current methodology execution by execution id
- load current methodology execution by primary anchors
- derive one stable status projection from the current pointer root and bindings
- derive one stable next-action projection from the current pointer root
- derive one stable explain projection from the current pointer root and available context
- return fail-closed results for missing or ambiguous projection requests

The first slice does not need to support every lane-specific explanation variant or every deep external reference join.

## 7. Failure Modes

This service must fail closed for:
- missing current execution truth
- ambiguous primary-anchor resolution
- missing required root fields needed for a stable projection
- inconsistent binding sets that make the projection unsafe to interpret
- unsupported projection mode for the first slice
- repository read failure during root, event, or binding loading

Blocked or missing-truth outcomes should return structured reasons rather than ad hoc shell-facing exceptions unless the repository itself fails unexpectedly.

## 8. Acceptance Rule

This component is acceptable for the first governed slice when:
- the service interface and DTOs are stable and governed
- status, next-action, and explain projection outputs are implemented end to end for one supported slice
- missing or ambiguous pointer truth fails closed with structured reasons
- unit coverage proves both successful projection behavior and fail-closed outcomes
- model/code consistency passes for `MethodologyExecutionProjectionService`
