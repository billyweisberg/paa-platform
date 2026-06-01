Title: Queue Claim Runtime Service Component Spec
Doc-ID: queue-claim-runtime-service-component-spec
Doc-Type: component-spec
Status: active
Lifecycle-Stage: design
Created: 2026-06-01
Last-Edited: 2026-06-01
Author: Billy Weisberg
Repo: paa-platform
Component: QueueClaimRuntimeService
Domain: runtime-workers
Keywords: paa, queue, claim, preview, runtime, packet, rabbitmq, adapter
Depends-On: 2026-05-28-paa-worker-runtime-architecture.md, 2026-05-31-governed-mvp-mode-policy.md, 2026-05-31-queue-packet-runtime-controller-component-spec.md, 2026-05-30-paa-cli-command-inventory-and-migration-map.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-07-01
Summary: Defines the governed runtime service that previews or claims one queue packet, normalizes queue transport state into stable DTOs, and supplies deterministic packet intake surfaces for the runtime controller and queue CLI hosts.

# Queue Claim Runtime Service Component Spec

Date: 2026-06-01

## Purpose

Define the governed runtime service that previews or claims one queue packet, normalizes queue transport state into stable DTOs, and supplies deterministic packet intake surfaces for the runtime controller and queue CLI hosts.

This component exists to stop queue preview and claim behavior from remaining split across consumer scripts, queue wrappers, and CLI-only helper logic.

The intent is not to turn RabbitMQ transport details into workflow truth.
The intent is to create one explicit runtime service that:
- previews one queue head or shallow queue packet view
- claims one queue packet for bounded runtime handling
- normalizes one claimed or previewed packet into stable DTOs
- exposes deterministic fail-closed results when queue state, packet shape, or claim prerequisites are missing
- can later support ack and requeue without forcing those concerns into CLI hosts or worker services

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/1_Vision/2026-05-28-paa-worker-runtime-architecture.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-31-governed-mvp-mode-policy.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-31-queue-packet-runtime-controller-component-spec.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-30-paa-cli-command-inventory-and-migration-map.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-12-paa-handoff-execution-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/4_Build/2026-05-27-component-realization-loop.md`

## Architecture Placement

Layer:
- `Application Services`

Dependency stratum:
- `Stratum 4`

Primary upstream dependencies:
- shared handoff runtime adapter supplied by the runtime shell
- queue state / claim adapter supplied by the runtime shell
- packet envelope validation collaborator supplied by the runtime shell
- StructuredLogger

Primary downstream consumers:
- `QueuePacketRuntimeController`
- future `paa queue ...` CLI host surfaces
- future queue-polling runtime shells
- future worker launchers that need one deterministic claim or preview input

## Component Identity Table

| component_name | component_kind | alignment_state | system_layer | tier | status |
|---|---|---|---|---|---|
| QueueClaimRuntimeService | service | aligned | application-services | runtime | active |

## 1. Role

`QueueClaimRuntimeService` is the shared runtime service for queue preview and claim intake.

Authority boundary:
- owns deterministic queue preview and claim normalization for the first supported slice
- owns stable runtime DTOs for queue intake results
- owns fail-closed claim and preview results when queue state is missing or unsupported
- does not own worker dispatch logic already held by `QueuePacketRuntimeController`
- does not own packet business logic
- does not own queue topology provisioning
- does not own CLI rendering

## Ownership Boundary

Owned responsibilities:
- preview one supported queue head packet
- claim one supported next queue packet
- normalize claimed or previewed queue packet identity and payload into stable DTOs
- expose deterministic dry-run-safe intake surfaces for CLI and runtime controller hosts

## Non-Ownership Boundary

Excluded responsibilities:
- worker-host routing decisions
- methodology execution mutation
- packet schema authoring
- long-lived workflow truth
- direct CLI command parsing and formatting
- agent-host execution policy

## Collaborators

| collaborator | collaborator_kind | dependency_role |
|---|---|---|
| queue transport collaborator | adapter | query queue preview and claim the next queue packet |
| queue claim state collaborator | adapter | expose or persist claim metadata when required by the runtime |
| packet envelope validator | adapter | validate one queue packet before it is exposed downstream |
| StructuredLogger | adapter | emit deterministic queue runtime diagnostics |

## Component Elements Table

| element_name | element_kind | description | owned_by_component |
|---|---|---|---|
| queue_claim_runtime_service_interface | interface | public queue preview and claim contract for normalized intake results | QueueClaimRuntimeService |
| queue_claim_runtime_service_models | dto | request, preview summary, claim summary, and intake result DTOs | QueueClaimRuntimeService |
| queue_claim_runtime_service_logic | implementation | default preview and claim normalization logic for the first supported queue slice | QueueClaimRuntimeService |
| queue_claim_runtime_service_verification_surface | verification-surface | tests and governed proof surfaces for supported queue intake and fail-closed blocked paths | QueueClaimRuntimeService |

## Realizations Table

| element_name | realization_kind | artifact_kind | artifact_target | verification_role |
|---|---|---|---|---|
| queue_claim_runtime_service_interface | service_interface | python-module | `packages/paa-core/src/paa_core/services/queue_claim_runtime/contracts.py` | interface contract validation |
| queue_claim_runtime_service_models | dto | python-module | `packages/paa-core/src/paa_core/services/queue_claim_runtime/models.py` | DTO and result-shape validation |
| queue_claim_runtime_service_logic | service_implementation | python-module | `packages/paa-core/src/paa_core/services/queue_claim_runtime/default.py` | behavioral and intake validation |
| queue_claim_runtime_service_verification_surface | test_module | python-module | `tests/unit/test_queue_claim_runtime_service.py` | service-level validation and proof |
| queue_claim_runtime_service_logic | package_export | python-module | `packages/paa-core/src/paa_core/services/queue_claim_runtime/__init__.py` | export-surface validation |

## 2. Component State Model

The service is stateless between calls.

It consumes one queue name, one preview or claim request, and one transport adapter pass.
It returns one structured queue-intake result per call.

### Persistent state
This component owns no primary persistent records directly.

It coordinates runtime calls through injected queue transport and claim-state collaborators.

### In-memory working state
During one call, the service may hold:
- queue name
- queue packet identity
- claim id
- packet schema type
- packet payload preview or normalized payload
- validation outcome
- blocked or unsupported-path diagnostics

### State rule
This service must remain a queue intake boundary.
It must not absorb worker dispatch logic or methodology decision logic.

## 3. Service Contract

The service provides one deterministic runtime boundary for previewing or claiming one queue packet.

### Inputs
- one queue name
- one intake mode such as `preview` or `claim_next`
- optional packet depth or preview limit metadata
- optional claimant identity
- optional host metadata

### Outputs
- structured queue preview or claim summary
- normalized packet identity and payload view
- explicit blocked or unsupported-path results when intake cannot proceed safely

### Guarantees
- supported queue preview and claim behavior is centralized outside CLI-only helpers
- queue packet identity and payload normalization occur through explicit service boundaries
- unsupported or unsafe cases fail closed with structured reasons

### Non-guarantees
- this service does not dispatch worker hosts
- this service does not render CLI output
- this service does not own queue polling cadence
- this service does not guarantee ack or requeue behavior in the first slice

## 4. Data Contract

The service operates on structured request and response DTOs.

### Primary consumed records or views
- queue name
- queue packet preview or claim transport result
- normalized packet payload or envelope

### `QueueClaimRuntimeRequest`
Carries:
- `queue_name`
- `intake_mode`
- optional `packet_message_id`
- optional `packet_schema_type`
- optional `claimant_name`
- optional `host_name`
- optional `metadata`

### `QueuePacketPreviewSummary`
Carries:
- `queue_name`
- `packet_message_id`
- `packet_schema_type`
- `preview_supported`
- `claim_supported`
- `blocking_reasons`
- `notes`

### `QueueClaimRuntimeResult`
Carries:
- request echo identifiers
- preview or claim summary
- optional `claim_id`
- optional normalized packet payload
- `ok`
- optional `reason`
- optional `details`
- optional `metadata`

### Data contract rule
The service must return stable queue-intake objects suitable for:
- runtime-controller input
- CLI inspection
- automation logging

It must not return ad hoc dicts that force each host to rediscover queue intake meaning.

## 5. Interfaces

### Provided interface
- `QueueClaimRuntimeService`

### Required collaborator interfaces
- queue transport collaborator
- queue claim state collaborator
- packet envelope validator
- StructuredLogger

## 6. Error Handling

Fail closed when:
- queue name is missing or unsupported
- preview or claim transport cannot return a packet
- packet envelope cannot be validated for the supported slice
- claimant identity is required but missing for a claim path

Return structured results with:
- `ok = false`
- stable `reason`
- concise `details`
- structured blocking reasons on the summary DTO

## 7. Verification Surface

The component is considered minimally proven when:
- one supported queue preview path returns a normalized packet view
- one supported queue claim path returns a normalized claim result
- unsupported intake modes fail closed
- missing queue packet results fail closed
- invalid packet envelope results fail closed
- code exports and governed metadata remain aligned with the component spec

## 8. First Supported Slice

### Included
- one supported queue: `fractal-core-architecture`
- one supported packet family: `worker_result_packet`
- `preview`
- `claim_next`
- one normalized intake result shape for runtime-controller and CLI consumption

### Excluded
- `ack`
- `requeue`
- packet send
- multi-message queue history traversal
- QA or Dev queue slices
- queue topology provisioning

## 9. Collaboration Notes

`QueueClaimRuntimeService` should become the shared queue intake boundary that sits between:
- runtime shells or queue adapters
- and `QueuePacketRuntimeController`

The CLI should host it.
The runtime controller should consume it.
Neither should recreate queue preview or claim normalization locally.

## Plan Seed Table

| plan_name | consumer_context_key | primary_component_name | implementation_target_kind | plan_status |
|---|---|---|---|---|
| plan-materialize-queue-claim-runtime-service-proof-python | governance-materialization-python-queue-claim-runtime | QueueClaimRuntimeService | python-runtime-service | draft_plan |

## Activity Seed Table

| activity_key | activity_name | sequence | activity_kind | element_name | realization_kind | done_definition |
|---|---|---:|---|---|---|---|
| queue-claim-runtime-interface-contract | Author queue claim runtime service interface contract | 10 | contract-authoring | queue_claim_runtime_service_interface | service_interface | Interface exposes stable queue preview and claim entrypoints plus supported intake contract. |
| queue-claim-runtime-dto-models | Model queue claim runtime service DTOs | 20 | dto-materialization | queue_claim_runtime_service_models | dto | Request, preview-summary, claim-summary, and result DTOs cover the first supported queue intake slice. |
| queue-claim-runtime-default-service | Implement default queue claim runtime service | 30 | service-implementation | queue_claim_runtime_service_logic | service_implementation | Default service previews or claims the supported architecture-queue packet slice and fails closed for blocked intake. |
| queue-claim-runtime-validation-surface | Add queue claim runtime service validation surface | 40 | verification | queue_claim_runtime_service_verification_surface | test_module | Unit coverage proves supported queue preview/claim intake and blocked-path behavior. |

## Activity Dependency Table

| activity_key | depends_on_activity_key | dependency_kind |
|---|---|---|
| queue-claim-runtime-dto-models | queue-claim-runtime-interface-contract | hard |
| queue-claim-runtime-default-service | queue-claim-runtime-dto-models | hard |
| queue-claim-runtime-validation-surface | queue-claim-runtime-default-service | hard |

## Verification Surface Table

| verification_surface | verification_kind | artifact_target | required_for_acceptance |
|---|---|---|---|
| queue claim runtime service unit tests | unit-test | `tests/unit/test_queue_claim_runtime_service.py` | true |
| queue claim runtime service spec-to-model consistency | consistency-check | `scripts/governance/paa_component_spec_model_consistency.py` | true |
| queue claim runtime service model-to-code consistency | consistency-check | `scripts/governance/paa_model_code_consistency.py` | true |

## Acceptance Criteria

The component is acceptable when:
- one `worker_result_packet` can be previewed deterministically from `fractal-core-architecture`
- one `worker_result_packet` can be claimed deterministically from `fractal-core-architecture`
- queue preview and claim normalization are explicit and testable outside CLI hosts
- unsupported or missing queue intake fails closed with structured reasons
- unit coverage and governed consistency checks pass
