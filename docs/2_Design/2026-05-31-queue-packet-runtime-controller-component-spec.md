Title: Queue Packet Runtime Controller Component Spec
Doc-ID: queue-packet-runtime-controller-component-spec
Doc-Type: component-spec
Status: active
Lifecycle-Stage: design
Created: 2026-05-31
Last-Edited: 2026-05-31
Author: Billy Weisberg
Repo: paa-platform
Component: QueuePacketRuntimeController
Domain: runtime-workers
Keywords: paa, queue, packet, runtime, controller, composition-root, worker, orchestration
Depends-On: 2026-05-28-paa-worker-runtime-architecture.md, 2026-05-31-governed-mvp-mode-policy.md, 2026-05-31-techlead-worker-service-component-spec.md, 2026-05-31-dev-worker-service-component-spec.md, 2026-05-31-qa-worker-service-component-spec.md, 2026-05-04-techlead-hub-packet-and-decision-vocabulary.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-06-30
Summary: Defines the governed runtime composition-root controller that receives or previews claimed queue packets, selects the correct worker host, composes shared Core collaborators, and coordinates normalized packet handling for TechLead, Dev, and QA runtime slices.

# Queue Packet Runtime Controller Component Spec

Date: 2026-05-31

## Purpose

Define the governed runtime composition-root controller that receives or previews claimed queue packets, selects the correct worker host, composes shared Core collaborators, and coordinates normalized packet handling for TechLead, Dev, and QA runtime slices.

This component exists to stop queue/runtime orchestration from remaining split across CLI helpers, queue scripts, and role-specific shells.

The intent is not to create a new monolith.
The intent is to create one explicit runtime controller that:
- accepts one claimed or previewed queue packet
- classifies the packet into one supported worker-host route
- composes the correct worker host over shared Core services and runtime adapters
- invokes one deterministic packet-handling pass
- returns one normalized runtime-control result suitable for CLI inspection and later live queue ack/send orchestration
- fails closed when required queue context, runtime collaborators, or supported-path prerequisites are missing

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/1_Vision/2026-05-28-paa-worker-runtime-architecture.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-31-governed-mvp-mode-policy.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-31-techlead-worker-service-component-spec.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-31-dev-worker-service-component-spec.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-31-qa-worker-service-component-spec.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-31-packet-context-assembly-service-component-spec.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-04-techlead-hub-packet-and-decision-vocabulary.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/4_Build/2026-05-27-component-realization-loop.md`

## Architecture Placement

Layer:
- `Application Services`

Dependency stratum:
- `Stratum 4`

Primary upstream dependencies:
- `TechLeadWorkerService`
- `DevWorkerService`
- `QAWorkerService`
- queue packet reader / claimer adapter supplied by the runtime shell
- packet send / ack adapter supplied by the runtime shell
- packet payload or packet-file reader adapter supplied by the runtime shell

Primary downstream consumers:
- future `paa queue ...` CLI host surfaces
- future `paa worker ...` CLI host surfaces
- future scheduled queue-polling runtime shells
- future TechLead, Dev, and QA launch programs that want one governed queue/runtime controller

## Component Identity Table

| component_name | component_kind | alignment_state | system_layer | tier | status |
|---|---|---|---|---|---|
| QueuePacketRuntimeController | service | aligned | application-services | runtime | active |

## 1. Role

`QueuePacketRuntimeController` is the runtime composition-root controller for supported queue packet handling.

Authority boundary:
- owns deterministic queue-packet classification and supported-host dispatch for the first runtime-controller slice
- owns composition of the correct worker host with injected runtime adapters for the supported slice
- owns normalized runtime-control results that describe what worker host ran and what queue side effects would occur
- does not own worker business logic already held by `TechLeadWorkerService`, `DevWorkerService`, or `QAWorkerService`
- does not own packet schema definitions
- does not own queue transport implementation
- does not own CLI rendering

## Ownership Boundary

Owned responsibilities:
- accept one claimed or previewed queue packet summary
- determine the supported runtime route for that packet
- invoke the correct worker host for the supported slice
- normalize packet-handling results into one stable runtime-control result
- expose a dry-run-safe orchestration boundary for CLI and automation hosts

## Non-Ownership Boundary

Excluded responsibilities:
- raw queue transport implementation
- worker decision logic already owned by worker services
- packet schema authoring
- direct SQL construction
- CLI command parsing and output formatting
- long-lived hidden agent memory or framework state

## Collaborators

| collaborator | collaborator_kind | dependency_role |
|---|---|---|
| `TechLeadWorkerService` | service | handle supported TechLead-visible worker-result packet slices |
| `DevWorkerService` | service | handle supported Dev-visible assignment packet slices |
| `QAWorkerService` | service | handle supported QA-visible verification packet slices |
| queue packet reader / claimer adapter | adapter | provide claimed or previewed queue packet input |
| queue send / ack adapter | adapter | normalize future packet publication or ack side effects |
| packet payload reader adapter | adapter | resolve packet payload when only a packet path is available |
| StructuredLogger | adapter | emit deterministic runtime-controller diagnostics |

## Component Elements Table

| element_name | element_kind | description | owned_by_component |
|---|---|---|---|
| queue_packet_runtime_controller_interface | interface | public runtime-controller contract for packet preview, dispatch, and normalized runtime results | QueuePacketRuntimeController |
| queue_packet_runtime_controller_models | dto | request, dispatch summary, and runtime result DTOs | QueuePacketRuntimeController |
| queue_packet_runtime_controller_logic | implementation | default classification and worker-host dispatch logic for the first supported queue slice | QueuePacketRuntimeController |
| queue_packet_runtime_controller_verification_surface | verification-surface | tests and governed proof surfaces for supported dispatch and fail-closed blocked paths | QueuePacketRuntimeController |

## Realizations Table

| element_name | realization_kind | artifact_kind | artifact_target | verification_role |
|---|---|---|---|---|
| queue_packet_runtime_controller_interface | service_interface | python-module | `packages/paa-core/src/paa_core/services/queue_packet_runtime_controller/contracts.py` | interface contract validation |
| queue_packet_runtime_controller_models | dto | python-module | `packages/paa-core/src/paa_core/services/queue_packet_runtime_controller/models.py` | DTO and result-shape validation |
| queue_packet_runtime_controller_logic | service_implementation | python-module | `packages/paa-core/src/paa_core/services/queue_packet_runtime_controller/default.py` | behavioral and dispatch validation |
| queue_packet_runtime_controller_verification_surface | test_module | python-module | `tests/unit/test_queue_packet_runtime_controller.py` | service-level validation and proof |
| queue_packet_runtime_controller_logic | package_export | python-module | `packages/paa-core/src/paa_core/services/queue_packet_runtime_controller/__init__.py` | export-surface validation |

## 2. Component State Model

The service is stateless between calls.

It consumes one claimed or previewed queue packet context, one supported route selection, and one worker-host invocation path.
It returns one structured orchestration result per call.

### Persistent state
This component owns no primary persistent records directly.

It coordinates runtime calls through:
- `TechLeadWorkerService`
- `DevWorkerService`
- `QAWorkerService`

### In-memory working state
During one call, the service may hold:
- queue name and packet identity
- packet schema type and route decision
- selected worker-host handler
- worker-host result
- normalized queue-side-effect summary
- blocked or unsupported-path diagnostics

### State rule
This service is the runtime composition root over worker hosts.
It must not absorb worker decision logic that already belongs in the realized worker services.

## 3. Service Contract

The service provides one deterministic runtime boundary for handling one queue packet through one supported worker-host route.

### Inputs
- one claimed or previewed packet summary or packet payload
- queue identity
- packet schema type
- runtime mode such as `dry_run` or `live`
- optional actor and host metadata

### Outputs
- structured route-selection summary
- selected worker-host result
- normalized queue-side-effect summary
- explicit blocked or unsupported-path results when handling cannot proceed safely

### Guarantees
- supported queue packet routes are centralized outside CLI and legacy queue helpers
- worker-host invocation occurs through explicit injected service boundaries
- unsupported or unsafe cases fail closed with structured reasons

### Non-guarantees
- this service does not render CLI output
- this service does not own queue polling cadence
- this service does not guarantee live send/ack behavior in the first slice
- this service does not replace the worker services themselves

## 4. Data Contract

The service operates on structured request and response DTOs.

### Primary consumed records or views
- claimed or previewed queue packet summary
- worker-host selection result
- selected worker-host orchestration result

### `QueuePacketRuntimeRequest`
Carries:
- `queue_name`
- `packet_schema_type`
- optional `packet_message_id`
- optional `packet_path`
- optional `packet_payload`
- `runtime_mode`
- optional `actor_name`
- optional `host_name`
- optional `metadata`

### `QueuePacketDispatchSummary`
Carries:
- `handler_key`
- `packet_schema_type`
- `target_worker_host`
- `dispatch_supported`
- `queue_side_effect_required`
- `ack_required`
- `blocking_reasons`
- `notes`

### `QueuePacketRuntimeResult`
Carries:
- request echo identifiers
- dispatch summary
- optional selected worker-host result
- optional normalized queue-side-effect summary
- `ok`
- optional `reason`
- optional `details`
- optional `dry_run`
- optional `metadata`

### Data contract rule
The service must return stable orchestration objects suitable for:
- CLI inspection
- automation logging
- future queue claim/ack/send integration

It must not return ad hoc dicts that force each host to rediscover dispatch meaning.

## 5. Interfaces

### Provided interface
- `QueuePacketRuntimeController`

### Required collaborator interfaces
- `TechLeadWorkerService`
- `DevWorkerService`
- `QAWorkerService`
- queue packet reader / claimer adapter
- queue send / ack adapter

## 6. First Supported Slice

The first governed MVP slice should support only:
- one `worker_result_packet`
- one `dry_run` execution path
- one route selection to `TechLeadWorkerService`
- one normalized runtime-control result without live queue ack/send side effects

This is intentionally narrow.

It proves:
- worker-host composition through one governed runtime controller
- stable queue packet classification and dispatch shape
- normalized runtime-control results
- fail-closed behavior before live queue operations and broader route expansion

## Plan Seed Table

| plan_name | consumer_context_key | primary_component_name | implementation_target_kind | plan_status |
|---|---|---|---|---|
| plan-materialize-queue-packet-runtime-controller-proof-python | governance-materialization-python-queue-runtime | QueuePacketRuntimeController | python-runtime-service | draft_plan |

## Activity Seed Table

| activity_key | activity_name | sequence | activity_kind | element_name | realization_kind | done_definition |
|---|---|---:|---|---|---|---|
| queue-packet-runtime-controller-interface-contract | Author queue packet runtime controller interface contract | 10 | contract-authoring | queue_packet_runtime_controller_interface | service_interface | Interface exposes stable dry-run and live queue-packet dispatch entrypoints plus supported runtime-controller contract. |
| queue-packet-runtime-controller-dto-models | Model queue packet runtime controller DTOs | 20 | dto-materialization | queue_packet_runtime_controller_models | dto | Request, dispatch-summary, and result DTOs cover the supported first queue-dispatch slice. |
| queue-packet-runtime-controller-default-service | Implement default queue packet runtime controller | 30 | service-implementation | queue_packet_runtime_controller_logic | service_implementation | Default controller handles the supported queue dry-run path, composes the TechLead worker host, and fails closed for unsupported packet routes. |
| queue-packet-runtime-controller-validation-surface | Add queue packet runtime controller validation surface | 40 | verification | queue_packet_runtime_controller_verification_surface | test_module | Unit coverage proves supported queue dry-run dispatch and blocked-path behavior. |

## Activity Dependency Table

| activity_key | depends_on_activity_key | dependency_kind |
|---|---|---|
| queue-packet-runtime-controller-dto-models | queue-packet-runtime-controller-interface-contract | hard |
| queue-packet-runtime-controller-default-service | queue-packet-runtime-controller-dto-models | hard |
| queue-packet-runtime-controller-validation-surface | queue-packet-runtime-controller-default-service | hard |

## Verification Surface Table

| verification_surface | verification_kind | artifact_target | required_for_acceptance |
|---|---|---|---|
| queue packet runtime controller unit tests | unit-test | `tests/unit/test_queue_packet_runtime_controller.py` | true |
| queue packet runtime controller spec-to-model consistency | consistency-check | `scripts/governance/paa_component_spec_model_consistency.py` | true |
| queue packet runtime controller model-to-code consistency | consistency-check | `scripts/governance/paa_model_code_consistency.py` | true |

## Acceptance Criteria

The component is acceptable when:
- one `worker_result_packet` can be routed deterministically through the first supported runtime-controller slice
- `TechLeadWorkerService` is composed through the controller rather than bypassed by ad hoc host logic
- queue packet classification and normalized runtime-control results are explicit and testable
- unsupported or missing context fails closed with structured reasons
- unit coverage and governed consistency checks pass
