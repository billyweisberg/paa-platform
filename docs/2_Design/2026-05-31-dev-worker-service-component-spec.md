Title: Dev Worker Service Component Spec
Doc-ID: dev-worker-service-component-spec
Doc-Type: component-spec
Status: active
Lifecycle-Stage: design
Created: 2026-05-31
Last-Edited: 2026-05-31
Author: Billy Weisberg
Repo: paa-platform
Component: DevWorkerService
Domain: worker-runtime
Keywords: paa, dev, worker, runtime, packet, microsoft-agent-framework, component, execution
Depends-On: 2026-05-28-paa-worker-runtime-architecture.md, 2026-05-31-governed-mvp-mode-policy.md, 2026-05-31-packet-context-assembly-service-component-spec.md, 2026-05-31-techlead-worker-service-component-spec.md, 2026-05-04-techlead-hub-packet-and-decision-vocabulary.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-06-30
Summary: Defines the bounded Dev worker runtime host that consumes TechLead assignment packets, assembles deterministic execution context through shared Core services, invokes one bounded execution run, and normalizes one worker result packet for return to TechLead.

# Dev Worker Service Component Spec

Date: 2026-05-31

## Purpose

Define the bounded Dev worker runtime host that consumes TechLead assignment packets, assembles deterministic execution context through shared Core services, invokes one bounded execution run, and normalizes one worker result packet for return to TechLead.

This component exists to replace the remaining Dev execution orchestration currently spread across runtime shells, ad hoc scripts, and direct operator supervision.

The intent is not to create a new monolith.
The intent is to create one explicit runtime host that:
- accepts one claimed `techlead_assignment_packet`
- expands thin packet context through `PacketContextAssemblyService`
- invokes one bounded execution run through a host-supplied agent or runner adapter
- normalizes the result into one deterministic `worker_result_packet`-ready surface
- fails closed when required authority, context, or execution prerequisites are missing

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/1_Vision/2026-05-28-paa-worker-runtime-architecture.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-31-governed-mvp-mode-policy.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-31-packet-context-assembly-service-component-spec.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-31-techlead-worker-service-component-spec.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-05-phase-g-worker-result-and-delivery-review-contracts.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/4_Build/2026-05-27-component-realization-loop.md`

## Architecture Placement

Layer:
- `Application Services`

Dependency stratum:
- `Stratum 4`

Primary upstream dependencies:
- `PacketContextAssemblyService`
- `MethodologyExecutionStateService`
- `MethodologyExecutionProjectionService`
- execution runner or agent-host adapter supplied by the runtime shell
- worker result packet assembler supplied by the runtime shell or later packet-runtime components

Primary downstream consumers:
- future `paa worker dev ...` CLI host surfaces
- future queue automation or scheduled Dev worker launcher surfaces
- `TechLeadWorkerService` return path through `worker_result_packet`

## Component Identity Table

| component_name | component_kind | alignment_state | system_layer | tier | status |
|---|---|---|---|---|---|
| DevWorkerService | service | aligned | application-services | runtime | active |

## 1. Role

`DevWorkerService` is the bounded Dev execution runtime host for one claimed assignment packet.

Authority boundary:
- owns deterministic Dev worker packet handling orchestration for supported assignment slices
- owns runtime coordination between packet context assembly, bounded execution, and normalized worker-result output
- owns normalized execution-run results suitable for CLI inspection and later queue publication
- does not own queue transport implementation
- does not own packet schema definitions
- does not own methodology execution policy logic outside explicit shared Core services
- does not own TechLead decision derivation
- does not own CLI rendering

## Ownership Boundary

Owned responsibilities:
- accept one claimed `techlead_assignment_packet` context
- assemble one deterministic runtime context package through `PacketContextAssemblyService`
- invoke one bounded execution run through the supplied runner or agent-host adapter
- normalize one structured worker-result summary and packet-ready output surface
- expose a dry-run-safe orchestration boundary suitable for CLI and automation hosts

## Non-Ownership Boundary

Excluded responsibilities:
- raw queue claim and ack transport implementation
- packet schema authoring
- direct SQL construction
- TechLead decision derivation
- QA verification decisions
- long-lived hidden agent memory or non-normalized model state
- CLI command parsing and output formatting

## Collaborators

| collaborator | collaborator_kind | dependency_role |
|---|---|---|
| `PacketContextAssemblyService` | service | expand thin assignment packet context into deterministic runtime context |
| `MethodologyExecutionStateService` | service | apply explicit methodology execution transitions when the supported slice requires them |
| `MethodologyExecutionProjectionService` | service | read current methodology execution state for supported execution reporting |
| execution runner collaborator | adapter | execute one bounded implementation run or dry-run simulation |
| worker result packet assembler | adapter | normalize runner outputs into deterministic worker-result packet surfaces |
| StructuredLogger | adapter | emit deterministic Dev worker runtime diagnostics |

## Component Elements Table

| element_name | element_kind | description | owned_by_component |
|---|---|---|---|
| dev_worker_service_interface | interface | public runtime-service contract for dry-run and live handling of one Dev-visible assignment packet | DevWorkerService |
| dev_worker_service_models | dto | request, execution-summary, result-summary, and orchestration-result DTOs | DevWorkerService |
| dev_worker_service_logic | implementation | default orchestration logic for supported assignment-packet handling and normalized worker-result output | DevWorkerService |
| dev_worker_service_verification_surface | verification-surface | tests and governed proof surfaces for supported Dev assignment handling and fail-closed blocked paths | DevWorkerService |

## Realizations Table

| element_name | realization_kind | artifact_kind | artifact_target | verification_role |
|---|---|---|---|---|
| dev_worker_service_interface | service_interface | python-module | `packages/paa-core/src/paa_core/services/dev_worker/contracts.py` | interface contract validation |
| dev_worker_service_models | dto | python-module | `packages/paa-core/src/paa_core/services/dev_worker/models.py` | DTO and result-shape validation |
| dev_worker_service_logic | service_implementation | python-module | `packages/paa-core/src/paa_core/services/dev_worker/default.py` | behavioral and orchestration validation |
| dev_worker_service_verification_surface | test_module | python-module | `tests/unit/test_dev_worker_service.py` | service-level validation and proof |
| dev_worker_service_logic | package_export | python-module | `packages/paa-core/src/paa_core/services/dev_worker/__init__.py` | export-surface validation |

## 2. Component State Model

The service is stateless between calls.

It consumes one claimed assignment-packet context, one assembled runtime context, and one bounded execution adapter.
It returns one structured orchestration result per call.

### Persistent state
This component owns no primary persistent records directly.

It coordinates reads and optional transitions through:
- `PacketContextAssemblyService`
- `MethodologyExecutionStateService`
- `MethodologyExecutionProjectionService`

### In-memory working state
During one call, the service may hold:
- claimed packet identity and schema type
- assembled runtime context package
- execution runner request and raw result
- normalized worker-result summary
- optional methodology transition result
- blocked or unsupported-path diagnostics

### State rule
This service is an execution host over shared Core services and a bounded execution adapter.
It must not become the new owner of packet-context assembly or methodology decision policy.

## 3. Service Contract

The service provides one deterministic runtime boundary for handling a claimed Dev-visible assignment packet.

### Inputs
- one claimed assignment packet summary or packet payload
- packet schema type
- packet source metadata
- runtime mode such as `dry_run` or `live`
- optional actor and host metadata

### Outputs
- structured assembled execution context summary
- structured execution-run summary
- optional normalized worker-result output summary
- optional methodology transition result
- explicit blocked or unsupported-path results when handling cannot proceed safely

### Guarantees
- supported assignment handling paths are centralized outside CLI and legacy shell modules
- bounded execution occurs through one explicit injected runner or agent-host adapter
- unsupported or unsafe cases fail closed with structured reasons

### Non-guarantees
- this service does not render CLI output
- this service does not own queue polling cadence
- this service does not guarantee live packet send in the first slice
- this service does not own QA or TechLead review decisions

## 4. Data Contract

The service operates on structured request and response DTOs.

### Primary consumed records or views
- claimed assignment packet summary or payload
- assembled runtime context result
- execution runner request and raw result

### `DevWorkerRequest`
Carries:
- `packet_schema_type`
- optional `packet_message_id`
- optional `packet_path`
- optional `packet_payload`
- `runtime_mode`
- optional `actor_name`
- optional `host_name`
- optional `metadata`

### `DevWorkerExecutionSummary`
Carries:
- `handler_key`
- `packet_schema_type`
- `context_supported`
- `execution_supported`
- `result_packet_family`
- `result_type`
- `methodology_transition_required`
- `blocking_reasons`
- `notes`

### `DevWorkerResult`
Carries:
- request echo identifiers
- assembled context result
- execution summary
- optional normalized worker-result output summary
- optional methodology transition result
- `ok`
- optional `reason`
- optional `details`
- optional `dry_run`
- optional `metadata`

### Data contract rule
The service must return stable orchestration objects suitable for:
- CLI inspection
- automation logging
- future queue publication and ack logic

It must not return ad hoc dicts that force each host to rediscover execution meaning.

## 5. Interfaces

### Provided interface
- `DevWorkerService`

### Required collaborator interfaces
- `PacketContextAssemblyService`
- `MethodologyExecutionStateService`
- `MethodologyExecutionProjectionService`
- execution runner collaborator
- worker result packet assembler collaborator

## 6. First Supported Slice

The first governed MVP slice should support only:
- one Dev-visible `techlead_assignment_packet`
- one `dry_run` execution path
- one packet-context assembly pass through `PacketContextAssemblyService`
- one normalized worker-result summary without live queue publication

This is intentionally narrow.

It proves:
- packet-to-context expansion reuse
- bounded execution-host composition
- normalized worker-result output shape
- fail-closed execution-host behavior before live publish and broader agent integration

## Plan Seed Table

| plan_name | consumer_context_key | primary_component_name | implementation_target_kind | plan_status |
|---|---|---|---|---|
| plan-materialize-dev-worker-service-proof-python | governance-materialization-python-dev-worker | DevWorkerService | python-runtime-service | draft_plan |

## Activity Seed Table

| activity_key | activity_name | sequence | activity_kind | element_name | realization_kind | done_definition |
|---|---|---:|---|---|---|---|
| dev-worker-interface-contract | Author Dev worker service interface contract | 10 | contract-authoring | dev_worker_service_interface | service_interface | Interface exposes stable dry-run and live packet-handling entrypoints plus supported execution contract. |
| dev-worker-dto-models | Model Dev worker service DTOs | 20 | dto-materialization | dev_worker_service_models | dto | Request, execution-summary, and result DTOs cover the supported first assignment-handling slice. |
| dev-worker-default-service | Implement default Dev worker service | 30 | service-implementation | dev_worker_service_logic | service_implementation | Default service handles the supported assignment dry-run path, composes packet-context assembly, and fails closed for unsupported packets. |
| dev-worker-validation-surface | Add Dev worker service validation surface | 40 | verification | dev_worker_service_verification_surface | test_module | Unit coverage proves supported assignment dry-run handling and blocked-path behavior. |

## Activity Dependency Table

| activity_key | depends_on_activity_key | dependency_kind |
|---|---|---|
| dev-worker-dto-models | dev-worker-interface-contract | hard |
| dev-worker-default-service | dev-worker-dto-models | hard |
| dev-worker-validation-surface | dev-worker-default-service | hard |

## Verification Surface Table

| verification_surface | verification_kind | artifact_target | required_for_acceptance |
|---|---|---|---|
| dev worker service unit tests | unit-test | `tests/unit/test_dev_worker_service.py` | true |
| dev worker service spec-to-model consistency | consistency-check | `scripts/governance/paa_component_spec_model_consistency.py` | true |
| dev worker service model-to-code consistency | consistency-check | `scripts/governance/paa_model_code_consistency.py` | true |

## Acceptance Criteria

The component is acceptable when:
- one `techlead_assignment_packet` can be handled deterministically for the first supported Dev runtime slice
- `PacketContextAssemblyService` is the sole packet-context expansion path for the supported slice
- the execution runner boundary is explicit and testable
- unsupported or missing context fails closed with structured reasons
- unit coverage and governed consistency checks pass
