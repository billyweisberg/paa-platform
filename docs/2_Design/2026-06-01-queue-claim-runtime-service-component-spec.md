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

## 10. Build Seed

### Plan Seed Table

| activity_key | description | depends_on | exit_criteria |
|---|---|---|---|
| `queue-claim-runtime-interface-contract` | define queue intake service and collaborator contracts |  | interface exports exist and focused contract tests pass |
| `queue-claim-runtime-dto-models` | define queue intake DTOs and typed result surfaces | `queue-claim-runtime-interface-contract` | request/result DTOs exist and model tests pass |
| `queue-claim-runtime-default-service` | implement preview and claim normalization for the first supported slice | `queue-claim-runtime-dto-models` | supported behavior and fail-closed tests pass |
| `queue-claim-runtime-validation-surface` | prove governed validation and consistency for the service | `queue-claim-runtime-default-service` | consistency checks and focused validation pass |

### Verification Surface Table

| verification_target | verification_kind | command_hint |
|---|---|---|
| `queue_claim_runtime_service_interface` | unit | `python -m unittest tests.unit.test_queue_claim_runtime_service` |
| `queue_claim_runtime_service_models` | unit | `python -m unittest tests.unit.test_queue_claim_runtime_service_models` |
| `queue_claim_runtime_service_logic` | unit | `python -m unittest tests.unit.test_queue_claim_runtime_service` |
| `queue_claim_runtime_service_spec_alignment` | consistency | `python scripts/governance/paa_component_spec_model_consistency.py --spec docs/2_Design/2026-06-01-queue-claim-runtime-service-component-spec.md` |
