# Execution Package Resolution Service Component Spec

Date: 2026-05-17

## Purpose

Define the full `Component Spec` for `Execution Package Resolution Service` using the PAA glossary's component-design discipline and the current layered architecture.

This service is the next fully specified Stratum 2 domain service in the preferred layered architecture after `Component Design Planning Service`.

It exists to resolve the effective execution-time package context for one runtime surface and provide normalized execution-package truth to:
- runtime lifecycle flows
- brief and work-item coordination consumers
- reporting or inspection consumers that need active install and overlay state
- future producer and consumer tooling that must reason about installed execution authority

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/terminology/paa-engineering-terminology-glossary.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-execution-package-resolution-service-pre-spec.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-layered-architecture-proposal.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-layered-component-dependency-graph.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-stratum-2-service-dependency-comparison.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-execution-package-repository-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-final-execution-package-registration-entity-design.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-runtime-consolidation-design-correction.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-domain-object-model-and-oo-component-decomposition.md`

## Architecture Placement

Layer:
- `Domain Services`

Dependency stratum:
- `Stratum 2`

Primary upstream dependencies:
- `Domain Core Model`
- `ExecutionPackageRepository`
- `DeploymentCapabilityPolicy`
- `StructuredLogger`

Primary downstream consumers:
- `Brief Assembly Service`
- `Work Item Coordination Service`
- `TechLead Application Service`
- future runtime inspection and reporting consumers

## 1. Role

`Execution Package Resolution Service` resolves the effective execution-time package context for one runtime surface and optional slice context by combining DB-primary install truth, active overlay truth, and deployment-capability rules into a normalized execution-context output.

Authority boundary:
- owns execution-time package-context resolution
- owns active install and active overlay interpretation at the domain-service level
- owns capability-evaluation application over the resolved context
- owns normalized execution-context output for downstream consumers
- does not own install registration mutation
- does not own overlay activation mutation
- does not own workflow lifecycle semantics
- does not own queue transport, GitHub, or host-surface orchestration
- does not own persistence beyond reading through the repository

## 2. Component State Model

The service should be stateless between calls.

### Persistent state
This component owns no primary persistent state.

It consumes persisted install and overlay records through `ExecutionPackageRepository`, but it does not own those rows.

### In-memory working state
During one call, the service may hold:
- resolved execution-surface identity
- resolved active install record
- resolved active overlay set
- deployment-capability request context
- capability decision DTOs
- normalized execution-context DTOs
- gap or missing-install diagnostics

### State rule
Any execution context produced by this service is a derived interpretation of persisted install and overlay truth.
It is not new primary truth.

## 3. Service Contract

The service provides a resolution-oriented contract over installed execution-package truth.

### Inputs
- execution-surface identity
- optional repo-root or runtime-root identity
- optional work-item identity
- optional coder-brief identity
- optional consumer-context key
- optional deployment-capability requirements

### Outputs
- active execution-package resolution views
- normalized installed execution-context views
- deployment-capability decisions
- resolution gaps and missing-install diagnostics
- install and overlay identity summaries for downstream consumers

### Guarantees
- execution-time package resolution is derived from DB-primary install and overlay registration truth
- active install truth is never inferred from directory scans alone
- active overlay truth is never inferred from overlay metadata files alone
- capability evaluation remains separate from raw repository reads
- the service does not silently fabricate execution context where no active install exists

### Non-guarantees
- this service does not install packages
- this service does not activate or deactivate overlays
- this service does not guarantee workflow readiness
- this service does not guarantee brief correctness
- this service does not mutate install state to repair missing execution context

## 4. Data Contract

The service operates on and emits structured execution-context DTOs.

### Primary consumed records
- `ExecutionPackageInstallRecord`
- `ExecutionPackageOverlayRecord`
- `InstalledExecutionContextRecord`
- `DeploymentCapabilityRequest`
- `DeploymentCapabilityDecision`

### Primary resolution DTOs to expose

#### `ExecutionPackageResolutionRequest`
Carries:
- optional `execution_surface_key`
- optional `execution_surface_type`
- optional `repo_root_path`
- optional `runtime_root_path`
- optional `work_item_id`
- optional `coder_run_brief_id`
- optional `consumer_context_key`
- optional `required_surface_types`
- optional `required_artifact_refs`
- optional `required_overlay_keys`
- optional `metadata`

#### `ExecutionPackageResolutionView`
Carries:
- execution-surface identity
- active install identity and package identity
- active overlay set
- resolved artifact surface pointers
- capability-decision summary
- warnings or gaps
- resolution metadata

#### `ExecutionPackageGap`
Carries:
- gap code
- severity
- affected execution surface
- explanatory note
- recommended next action
- metadata

#### `ExecutionPackageCapabilitySummary`
Carries:
- allowed or blocked decision
- satisfied capability set
- missing capability set
- blocking reasons
- notes

### Data contract rule
The service should return stable, structured execution-context outputs suitable for runtime and orchestration consumers.
It should not return only loosely shaped dictionaries or prose summaries.

## 5. Injected Services

### Required injected services
- `ExecutionPackageRepository`
- `DeploymentCapabilityPolicy`
- `StructuredLogger`

### Optional injected services
- `Clock` if later resolution outputs need explicit timestamps
- a future `ExecutionSurfaceIdentityHelper` if surface matching grows beyond the first slice

### Important non-injected collaborators
This service should not depend directly on:
- `WorkflowStateRepository`
- `RuntimeEventRepository`
- `MessageBus`
- `GitProvider`
- `ComponentDesignRepository`

If those become necessary, the boundary should be reconsidered.

## 6. Interfaces

### Provided interface
- `ExecutionPackageResolutionService`

### Required interfaces
- `ExecutionPackageRepository`
- `DeploymentCapabilityPolicy`
- `StructuredLogger`

### Recommended code realization
- interface / contract:
  - `execution_package_resolution_service_interface`
- default implementation:
  - `default_execution_package_resolution_service`

## 7. Functions

Minimum public functions:
- `resolve_execution_context(request)`
- `resolve_execution_context_for_surface(execution_surface_key, capability_request | None)`
- `resolve_execution_context_for_repo_root(repo_root_path, capability_request | None)`
- `resolve_execution_context_for_runtime_root(runtime_root_path, capability_request | None)`
- `evaluate_deployment_capability(request, context)`
- `detect_execution_package_gaps(request)`

Likely internal helper functions:
- `resolve_active_install(...)`
- `resolve_active_overlays(...)`
- `assemble_execution_context_view(...)`
- `derive_capability_request(...)`
- `derive_resolution_gaps(...)`
- `normalize_surface_identity(...)`

## 8. Messages Received

This component receives service-level commands and queries, not queue packets.

### Primary queries
- `ResolveExecutionContext`
- `ResolveExecutionContextForSurface`
- `ResolveExecutionContextForRepoRoot`
- `ResolveExecutionContextForRuntimeRoot`
- `DetectExecutionPackageGaps`

### Primary command-like operation
- `EvaluateDeploymentCapability`

This command-like operation still returns data; it does not imply persistence mutation.

## 9. Messages Published

This service should remain mostly request/response oriented.

If events are emitted later, they should remain internal domain or application events such as:
- `ExecutionContextResolved`
- `ExecutionPackageGapDetected`
- `DeploymentCapabilityRejected`

For the first implementation, returning structured results is sufficient.

## 10. Message Data Contracts

### `ResolveExecutionContext`
Carries:
- `ExecutionPackageResolutionRequest`

### `ExecutionContextResolved`
If emitted later, should carry:
- execution-surface identity
- active install identity
- overlay key set
- capability-decision summary
- generated-at timestamp

### `DeploymentCapabilityRejected`
If emitted later, should carry:
- execution-surface identity
- missing capability set
- blocking reasons
- recommended next action

## 11. Event Subscriptions

This service should not directly subscribe to transport events.

If later integrated into event-driven runtime flows, it may subscribe indirectly to internal events such as:
- install registration changed
- overlay activation changed
- execution surface requested

But those should be mediated through application services, not direct transport binding.

## 12. Events Published

This service does not need external runtime events for its first implementation.

Possible future internal events:
- `ExecutionContextRefreshed`
- `ExecutionPackageGapRegistered`

These are optional and should not be introduced until a real consumer exists.

## 13. Event Data Contracts

If future events are added, they should be simple, stable resolution notifications carrying:
- execution-surface identity
- install identity
- overlay summary
- capability summary
- timestamps

They should not carry raw repository rows.

## 14. Component Lifecycle

### Construction
- repository, policy, and logger are injected
- no IO happens at construction time

### Steady-state
- resolve execution-surface identity
- load active install and active overlay state
- evaluate deployment capability when requested
- assemble execution-context view
- emit warnings or gaps if structures are incomplete

### Recovery / failure
- fail closed when no active install can be resolved
- fail closed when required capability is not satisfied
- surface missing artifact-path or overlay-state problems explicitly
- do not self-repair registration state from this component

## 15. Configuration

Required runtime configuration is minimal:
- repository wiring
- logger wiring
- policy wiring

The service should not require large configuration bundles for its first implementation.

Possible future configuration:
- default surface-type expectations by consumer context
- optional strictness mode for missing artifact pointers
- capability profile shortcuts

### Configuration rule
Configuration should adjust resolution strictness or defaults, not redefine install truth.

## 16. Responsibility Summary

This service owns:
- active execution-package context resolution
- active overlay interpretation
- deployment-capability evaluation over resolved context
- normalized execution-context outputs for downstream consumers

This service does not own:
- install registration writes
- overlay activation writes
- workflow transitions
- queue routing
- coder-brief assembly
- reporting projections

## 17. Invariants

The implementation must preserve these invariants:

1. active install truth is DB-primary
2. active overlay truth is DB-primary
3. one execution-context resolution call yields at most one active install for one execution surface
4. capability evaluation is applied after resolution, not baked into repository lookup logic
5. missing active install state must be surfaced explicitly
6. missing required artifact surfaces must be surfaced explicitly
7. the service must not mutate install or overlay rows during resolution

## 18. Failure Model

Expected failure modes:
- no active install for the requested execution surface
- ambiguous surface identity provided by caller
- required artifact pointer missing on the active install
- required overlay missing
- capability request incompatible with resolved surface type
- repository lookup failure

Failure behavior:
- return structured gaps / diagnostics where possible
- raise explicit lookup or capability errors for hard-fail resolution paths
- never silently fall back to directory scans as primary truth

## 19. Dependency Summary

### Hard dependencies
- `ExecutionPackageRepository`
- `DeploymentCapabilityPolicy`
- `StructuredLogger`

### Deferred dependencies
These are intentionally deferred out of the first implementation slice:
- concrete workflow-state integration
- runtime-event correlation
- install or overlay mutation support
- projection or reporting coupling

## 20. Implementation Guidance

### First implementation slice
The first implementation slice should remain narrow and read-oriented.

It should support:
- resolve active install by `execution_surface_key`
- resolve active install by `repo_root_path`
- resolve active install by `runtime_root_path`
- resolve active overlays for the active install
- assemble normalized execution-context DTOs
- evaluate minimal deployment-capability requirements
- surface missing-install and missing-artifact gaps

It should not yet support:
- install registration writes
- overlay activation writes
- repair mutation flows
- projection persistence
- deep brief or workflow coupling

### Expected collaborator slice before implementation
The first implementation assumes:
- a concrete `ExecutionPackageRepository` adapter exists
- a real `DeploymentCapabilityPolicy` exists
- both are narrow and read-oriented for the first slice

### Likely code artifact targets
- `service_interface`
- `dto`
- `service_implementation`
- `test_module`
- `package_export`

### Most important discipline
Do not let execution-context resolution drift into:
- repository-side policy ownership
- runtime orchestration behavior
- directory-scan-based truth reconstruction

That discipline is what keeps this service small, testable, and consistent with the architecture.

## 21. Exit Condition For This Spec

This component is ready for implementation once:
- `ExecutionPackageRepository` read slice exists
- `DeploymentCapabilityPolicy` exists
- the first implementation is kept read-only and resolution-oriented

That condition is now satisfied.

## Next Step

Implement Phase 1 and Phase 2 for:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/execution_package_resolution/`

That first code slice should focus on:
- service contract
- DTO model
- default service shell
- then active install / overlay resolution reads using the now-real repository and policy inputs
