Title: Packet Context Assembly Service Component Spec
Doc-ID: packet-context-assembly-service-component-spec
Doc-Type: component-spec
Status: active
Lifecycle-Stage: design
Created: 2026-05-31
Last-Edited: 2026-05-31
Author: Billy Weisberg
Repo: paa-platform
Component: PacketContextAssemblyService
Domain: worker-runtime
Keywords: paa, packet, context, assembly, worker, runtime, execution-package, methodology-execution, component
Depends-On: 2026-05-28-paa-worker-runtime-architecture.md, 2026-05-31-governed-mvp-mode-policy.md, 2026-05-31-techlead-worker-service-component-spec.md, 2026-05-04-techlead-hub-packet-and-decision-vocabulary.md, 2026-05-13-paa-runtime-consolidation-design-correction.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-06-30
Summary: Defines the shared runtime service that expands thin queue packets into deterministic worker context by composing methodology execution truth, execution-package resolution, and packet payload references.

# Packet Context Assembly Service Component Spec

Date: 2026-05-31

## Purpose

Define the shared runtime service that expands thin queue packets into deterministic worker context for `TechLeadWorkerService`, `DevWorkerService`, and `QAWorkerService`.

This component exists to stop each host from reconstructing context differently.

The intent is not to create a packet monolith.
The intent is to create one explicit shared Core service that:
- accepts a minimal packet request or claimed packet context
- resolves authoritative methodology execution truth
- resolves installed execution-package context through `ExecutionPackageResolutionService`
- assembles the normalized runtime context package required by one worker slice
- fails closed when required context cannot be resolved safely

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/1_Vision/2026-05-28-paa-worker-runtime-architecture.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-31-governed-mvp-mode-policy.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-31-techlead-worker-service-component-spec.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-runtime-consolidation-design-correction.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-execution-package-resolution-service-pre-spec.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/4_Build/2026-05-27-component-realization-loop.md`

## Architecture Placement

Layer:
- `Application Services`

Dependency stratum:
- `Stratum 4`

Primary upstream dependencies:
- `MethodologyExecutionRepository`
- `MethodologyExecutionProjectionService`
- `ExecutionPackageResolutionService`
- packet payload or packet-file readers supplied by the runtime host

Primary downstream consumers:
- `TechLeadWorkerService`
- future `DevWorkerService`
- future `QAWorkerService`
- future `paa worker ...` diagnostic CLI surfaces

## Component Identity Table

| component_name | component_kind | alignment_state | system_layer | tier | status |
|---|---|---|---|---|---|
| PacketContextAssemblyService | service | aligned | application-services | runtime | active |

## 1. Role

`PacketContextAssemblyService` assembles one normalized runtime context package from thin packet references and authoritative execution truth.

Authority boundary:
- owns deterministic assembly of worker-runtime context for supported packet families
- owns normalization of minimal packet identifiers, payload references, and execution-package capability pointers into one typed context surface
- owns fail-closed missing-context results for supported slices
- does not own packet transport
- does not own methodology execution state mutation
- does not own execution-package installation or activation
- does not own worker decision policy or worker execution

## Ownership Boundary

Owned responsibilities:
- accept one thin packet-context request
- resolve one methodology execution summary or projection for that request
- resolve the relevant installed execution package for the active runtime surface
- return one normalized context package for the supported packet family
- expose blocked and missing-context results suitable for CLI and runtime hosts

## Non-Ownership Boundary

Excluded responsibilities:
- queue polling, claim, ack, or requeue
- packet schema authoring
- execution-package persistence or overlay mutation
- TechLead, Dev, or QA decision logic
- CLI rendering

## Collaborators

| collaborator | collaborator_kind | dependency_role |
|---|---|---|
| `MethodologyExecutionRepository` | repository | resolve raw execution bindings when direct lookup is required |
| `MethodologyExecutionProjectionService` | service | resolve current normalized methodology execution status |
| `ExecutionPackageResolutionService` | service | resolve installed execution-package context and capability pointers |
| packet payload reader | adapter | load packet payload from a claimed packet path when payload is not already in memory |
| StructuredLogger | adapter | emit deterministic context-assembly diagnostics |

## Component Elements Table

| element_name | element_kind | description | owned_by_component |
|---|---|---|---|
| packet_context_assembly_service_interface | interface | public service contract for assembling one normalized runtime context package | PacketContextAssemblyService |
| packet_context_assembly_service_models | dto | request, context-summary, gap-summary, and result DTOs | PacketContextAssemblyService |
| packet_context_assembly_service_logic | implementation | default context assembly logic for the first supported packet slice | PacketContextAssemblyService |
| packet_context_assembly_service_verification_surface | verification-surface | tests and governed proof surfaces for supported packet-context assembly and fail-closed gaps | PacketContextAssemblyService |

## Realizations Table

| element_name | realization_kind | artifact_kind | artifact_target | verification_role |
|---|---|---|---|---|
| packet_context_assembly_service_interface | service_interface | python-module | `packages/paa-core/src/paa_core/services/packet_context_assembly/contracts.py` | interface contract validation |
| packet_context_assembly_service_models | dto | python-module | `packages/paa-core/src/paa_core/services/packet_context_assembly/models.py` | DTO and result-shape validation |
| packet_context_assembly_service_logic | service_implementation | python-module | `packages/paa-core/src/paa_core/services/packet_context_assembly/default.py` | behavioral and orchestration validation |
| packet_context_assembly_service_verification_surface | test_module | python-module | `tests/unit/test_packet_context_assembly_service.py` | service-level validation and proof |
| packet_context_assembly_service_logic | package_export | python-module | `packages/paa-core/src/paa_core/services/packet_context_assembly/__init__.py` | export-surface validation |

## 2. Component State Model

The service is stateless between calls.

It consumes packet references, methodology execution truth, execution-package resolution, and optional in-memory payload.
It returns one normalized context assembly result per call.

### Persistent state
This component owns no primary persistent records directly.

It coordinates reads through:
- `MethodologyExecutionRepository`
- `MethodologyExecutionProjectionService`
- `ExecutionPackageResolutionService`

### In-memory working state
During one call, the service may hold:
- packet schema type and packet identifiers
- loaded packet payload
- resolved methodology execution summary
- resolved execution-package capability summary
- normalized runtime context package
- blocked or missing-context diagnostics

### State rule
This service is a shared context-construction boundary.
It must not become the new owner of worker decision logic or queue transport behavior.

## 3. Service Contract

The service provides one deterministic runtime boundary for assembling worker context from thin packet inputs.

### Inputs
- one packet schema type
- optional packet message id
- optional packet path
- optional packet payload
- optional methodology execution id or primary business anchors
- runtime surface identifier such as `techlead`, `dev`, or `qa`
- optional actor and host metadata

### Outputs
- structured resolved methodology execution summary when available
- structured execution-package capability summary when available
- normalized packet-context summary for the supported worker slice
- explicit blocked or missing-context results when assembly cannot proceed safely

### Guarantees
- supported worker hosts consume one shared context-assembly surface
- installed execution-package truth is resolved through the dedicated execution-package service, not reimplemented locally
- unsupported or unsafe cases fail closed with structured reasons

### Non-guarantees
- this service does not mutate methodology execution state
- this service does not render CLI output
- this service does not claim or acknowledge packets
- this service does not execute TechLead, Dev, or QA decisions

## 4. Data Contract

The service operates on structured request and response DTOs.

### Primary consumed records or views
- claimed packet summary or packet payload
- current methodology execution status projection
- execution-package resolution result and capability summaries

### `PacketContextAssemblyRequest`
Carries:
- `packet_schema_type`
- optional `packet_message_id`
- optional `packet_path`
- optional `packet_payload`
- optional `methodology_execution_id`
- optional `project_id`
- optional `work_item_id`
- optional `component_id`
- `runtime_surface`
- optional `actor_name`
- optional `host_name`
- optional `metadata`

### `PacketContextGapSummary`
Carries:
- `gap_key`
- `gap_summary`
- `blocking`
- `recommended_next_action`
- `notes`

### `PacketContextAssemblySummary`
Carries:
- `packet_schema_type`
- `runtime_surface`
- `methodology_execution_id`
- `execution_package_id`
- `context_kind`
- `assembly_supported`
- `required_capabilities`
- `resolved_capabilities`
- `blocking_gaps`
- `notes`

### `PacketContextAssemblyResult`
Carries:
- request echo identifiers
- current methodology execution summary
- execution-package resolution summary
- normalized packet-context summary
- normalized assembly summary
- `ok`
- optional `reason`
- optional `details`
- optional `metadata`

### Data contract rule
The service must return stable context objects suitable for:
- CLI inspection
- runtime host composition
- future queue packet replay or diagnostics

It must not return ad hoc dicts that force each host to rediscover context meaning.

## 5. Interfaces

### Provided interface
- `PacketContextAssemblyService`

### Required collaborator interfaces
- `MethodologyExecutionRepository`
- `MethodologyExecutionProjectionService`
- `ExecutionPackageResolutionService`
- packet payload reader supplied by the host

## 6. First Supported Slice

The first governed MVP slice should support only:
- one `worker_result_packet`
- one `techlead` runtime surface
- one methodology execution resolution by explicit id
- one execution-package resolution pass for that runtime surface
- one normalized context result suitable for `TechLeadWorkerService`

This is intentionally narrow.

It proves:
- thin-packet expansion
- methodology execution lookup reuse
- execution-package resolution reuse
- one stable shared context boundary before `DevWorkerService` and `QAWorkerService` arrive

## Plan Seed Table

| plan_name | consumer_context_key | primary_component_name | implementation_target_kind | plan_status |
|---|---|---|---|---|
| plan-materialize-packet-context-assembly-service-proof-python | governance-materialization-python-packet-context-assembly | PacketContextAssemblyService | python-runtime-service | draft_plan |

## Activity Seed Table

| activity_key | activity_name | sequence | activity_kind | element_name | realization_kind | done_definition |
|---|---|---:|---|---|---|---|
| packet-context-assembly-interface-contract | Author packet context assembly service interface contract | 10 | contract-authoring | packet_context_assembly_service_interface | service_interface | Interface exposes stable context-assembly entrypoints for the supported worker slice. |
| packet-context-assembly-dto-models | Model packet context assembly service DTOs | 20 | dto-materialization | packet_context_assembly_service_models | dto | Request, gap-summary, assembly-summary, and result DTOs cover the supported first context-assembly slice. |
| packet-context-assembly-default-service | Implement packet context assembly default service | 30 | service-implementation | packet_context_assembly_service_logic | service_implementation | Default service resolves the supported worker-result packet context through methodology execution and execution-package services and fails closed for missing context. |
| packet-context-assembly-validation-surface | Add packet context assembly service validation surface | 40 | verification | packet_context_assembly_service_verification_surface | test_module | Unit coverage proves supported packet-context assembly and fail-closed missing-context behavior. |

## Activity Dependency Table

| activity_key | depends_on_activity_key | dependency_kind |
|---|---|---|
| packet-context-assembly-dto-models | packet-context-assembly-interface-contract | hard |
| packet-context-assembly-default-service | packet-context-assembly-dto-models | hard |
| packet-context-assembly-validation-surface | packet-context-assembly-default-service | hard |

## Verification Surface Table

| verification_surface | verification_kind | artifact_target | required_for_acceptance |
|---|---|---|---|
| packet context assembly service unit tests | unit-test | `tests/unit/test_packet_context_assembly_service.py` | true |
| packet context assembly service spec-to-model consistency | consistency-check | `scripts/governance/paa_component_spec_model_consistency.py` | true |
| packet context assembly service model-to-code consistency | consistency-check | `scripts/governance/paa_model_code_consistency.py` | true |

## Acceptance Criteria

The component is acceptable when:
- one `worker_result_packet` context can be assembled deterministically for the `techlead` runtime surface
- methodology execution projection is resolved through shared services
- execution-package resolution is resolved through shared services
- missing required packet or execution-package context fails closed with structured gaps
- unit coverage and governed consistency checks pass
