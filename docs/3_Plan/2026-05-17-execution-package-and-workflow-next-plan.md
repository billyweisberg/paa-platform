# Execution Package And Workflow Next Plan

Date: 2026-05-17
Status: active, Steps 1 through 10 established

## Purpose

Define the next ordered execution plan after successful completion of:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-17-paa-next-execution-plan.md`

This plan continues the dependency-graph-driven implementation sequence by:
1. finishing `Execution Package Resolution Service` into a real read-oriented Stratum 2 service
2. using that stronger execution-context backbone to reduce risk before beginning `Workflow Lifecycle Service`

## Why This Plan Exists

The prior plan is effectively exhausted as an execution sequence.

We now have:
- `ImplementationPlan` repo/service backbone
- `Component Design Planning Service`
- implementation-plan to coder-brief bridge
- `DeploymentCapabilityPolicy` first slice
- `ExecutionPackageRepository` first adapter slice
- `Execution Package Resolution Service` full component spec
- `Execution Package Resolution Service` Phase 1 and Phase 2

That means the next coherent work is no longer generic infrastructure buildout.
It is the next real service wave.

## Current Status Snapshot

### Established already

#### `Execution Package Resolution Service` design
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-execution-package-resolution-service-pre-spec.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-execution-package-resolution-service-component-spec.md`

#### `ExecutionPackageRepository` first slice
- read-oriented Postgres adapter exists under:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/repositories/execution_package/`

#### `DeploymentCapabilityPolicy` first slice
- policy contract and default implementation exist under:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/policies/deployment_capability/`

#### `Execution Package Resolution Service` Phase 1 and Phase 2
- service contract
- DTOs
- default shell
- tests

### Not yet implemented

#### `Execution Package Resolution Service` useful behavior
- active install resolution reads
- active overlay resolution reads
- normalized execution-context view assembly
- capability-evaluation integration
- execution-package gap detection
- downstream consumer integration

#### `Workflow Lifecycle Service` modern decomposition and code
- explicit `Workflow Lifecycle Service` pre-spec
- policy contract decomposition from legacy workflow-state-machine design
- repository adapter slices for workflow/runtime event support
- new service contract/DTOs/default shell
- first real transition-read and transition-application slice

## Dependency Logic

The dependency-graph-selected next service remains:
- `Execution Package Resolution Service`

The service after that remains:
- `Workflow Lifecycle Service`

This ordering is still correct because:
- `Execution Package Resolution Service` has fewer unresolved dependencies
- `Workflow Lifecycle Service` depends on execution-context truth and still has heavier policy decomposition work

## Ordered Execution Plan

## Step 1. Implement `Execution Package Resolution Service` Phase 3
Status: established

### Why first
The service shell now exists. The next move is to make it a real read service over the execution-package repository.

### Deliverables
- active install resolution by:
  - execution surface key
  - repo root
  - runtime root
- active overlay resolution for the active install
- normalized `ExecutionPackageResolutionView`
- focused unit tests

### Target files
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/execution_package_resolution/default.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/tests/unit/test_execution_package_resolution_service.py`

### Minimum scope
- `resolve_execution_context(...)`
- `resolve_execution_context_for_surface(...)`
- `resolve_execution_context_for_repo_root(...)`
- `resolve_execution_context_for_runtime_root(...)`

## Step 2. Implement `Execution Package Resolution Service` Phase 4
Status: established

### Why second
Once resolution reads work, capability evaluation and gap detection can be applied over real context instead of placeholders.

### Deliverables
- capability-policy application inside the service
- `ExecutionPackageCapabilitySummary` population
- `ExecutionPackageGap` derivation for:
  - missing active install
  - missing required artifact paths
  - missing required overlays
  - incompatible surface type
- focused unit tests

### Target files
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/execution_package_resolution/default.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/tests/unit/test_execution_package_resolution_service.py`

## Step 3. Validate execution-context bridge alignment
Status: established

### Why third
Before wiring more consumers to this service, confirm that repository truth, policy truth, and service outputs align the same way the planning bridge did.

### Deliverables
- validation note comparing:
  - execution-package repository rows
  - capability-policy decision inputs
  - service outputs
  - downstream consumer expectations

### Output target
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/5_Test/2026-05-17-execution-package-resolution-service-validation.md`

## Step 4. Connect `Execution Package Resolution Service` into the next real consumer path
Status: established

### Why fourth
A service is only proven once a real downstream consumer uses it.

### Preferred first consumers
- `Brief Assembly Service` inputs that need installed execution-package context
- `Work Item Coordination Service` or related orchestration path
- selected runtime or handoff resolution path where current package lookup is still duplicated

### Deliverables
- narrow integration into one consumer path
- focused tests proving the consumer uses the service output rather than ad hoc package lookup logic

### Completed consumer path
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-consumer/src/paa_consumer/techlead.py`
- `repo_auth_current(...)` now resolves the authority manifest through `Execution Package Resolution Service` before falling back to direct filesystem lookup

## Step 5. Write `Workflow Lifecycle Service` pre-spec
Status: established

### Why fifth
Before touching workflow code, replace the earlier over-compressed mental model with the explicit service boundary we now want.

### Deliverables
- modern pre-spec note for `Workflow Lifecycle Service`
- explicit owned vs non-owned responsibilities
- explicit relationship to:
  - `Execution Package Resolution Service`
  - `WorkflowStateRepository`
  - `RuntimeEventRepository`
  - policy components

### Target file
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-workflow-lifecycle-service-pre-spec.md`

## Step 6. Define workflow policy contracts
Status: established

### Why sixth
`Workflow Lifecycle Service` should not absorb all policy logic directly.

### Deliverables
- `WorkflowTransitionPolicy`
- `AcceptancePolicy`
- `ResetRecoveryPolicy`

### Target files
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/policies/workflow_transition/`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/policies/acceptance/`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/policies/reset_recovery/`

### Minimum rule
Each policy must pass the same four-part check:
1. already named in architecture or dependency graph
2. protects a real policy boundary
3. already needed by a downstream service
4. has clear non-ownership

### Completed policy packages
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/policies/workflow_transition/`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/policies/acceptance/`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/policies/reset_recovery/`

## Step 7. Implement repository adapter slices for workflow support
Status: established

### Why seventh
`Workflow Lifecycle Service` needs real repository collaborators, not only design docs.

### Deliverables
- `WorkflowStateRepository` first adapter slice
- `RuntimeEventRepository` first adapter slice
- focused unit tests

### Minimum scope
- current-state reads
- transition-history reads
- append transition row
- update current workflow-state row
- runtime-event lookup support needed for first transition slice

### Completed repository slices
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/repositories/workflow_state/`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/repositories/runtime_event/`

## Step 8. Write full `Workflow Lifecycle Service` component spec
Status: established

### Why eighth
Once the policy and repository prerequisites are real enough, the service spec can be written against actual collaborators rather than placeholders.

### Deliverables
- full component spec for `Workflow Lifecycle Service`

### Target file
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-workflow-lifecycle-service-component-spec.md`

## Step 9. Implement `Workflow Lifecycle Service` Phase 1 and Phase 2
Status: established

### Why ninth
Start with the same disciplined pattern:
- contract
- DTOs
- default shell
- focused tests

### Deliverables
- service contract
- DTO models
- injected shell
- unit tests

### Completed service files
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/workflow_lifecycle/__init__.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/workflow_lifecycle/contracts.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/workflow_lifecycle/models.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/workflow_lifecycle/default.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/tests/unit/test_workflow_lifecycle_service.py`

## Step 10. Implement `Workflow Lifecycle Service` first behavioral slice
Status: established

### Why tenth
Only after the collaborators and contracts are real should transition logic begin.

### First slice scope
- load current workflow state
- validate one narrow transition family
- apply one narrow transition path
- record transition history
- fail closed on illegal transitions

### Completed first slice
- supported transition family:
  - `worker_result_returned`
- current-state source:
  - `WorkflowStateRepository`
- runtime evidence sources:
  - queue message lookup
  - transition-input fallback
- policy application:
  - `WorkflowTransitionPolicy`
  - `ResetRecoveryPolicy`
- successful state move:
  - `worker_execution_in_progress -> techlead_worker_review_pending`
- successful mutation behavior:
  - update current workflow state
  - append applied workflow transition history
- fail-closed behavior:
  - unsupported transition type
  - mismatched current stage
  - missing or wrong source packet schema
  - repair-required workflow state

## Step 11. Validate and connect the workflow slice into one downstream runtime path
Status: established

### Why eleventh
The workflow slice is most useful once a real runtime or orchestration path consumes it instead of duplicating transition logic.

### Deliverables
- one focused validation note for the worker-result transition family
- one narrow downstream integration that uses `WorkflowLifecycleService`
- focused tests proving the consumer path delegates transition handling to the service

### Preferred first consumers
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-consumer/src/paa_consumer/techlead.py`
- selected queue-result handling path that currently interprets worker-result return state inline

### Completed consumer bridge
- consumer integration:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-consumer/src/paa_consumer/techlead.py`
- validation note:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/5_Test/2026-05-17-workflow-lifecycle-techlead-bridge-validation.md`
- established behavior:
  - resolve DB-primary `work_item_id` from issue context
  - evaluate pending `worker_result_packet` through `WorkflowLifecycleService`
  - surface workflow decision details back into TechLead escalation context

## Step 12. Choose the next workflow expansion slice
Status: in progress

### Why twelfth
The first consumer bridge is proven. The next work should extend the workflow model deliberately instead of broadening the consumer path ad hoc.

### Preferred next choices
1. add `qa_result_returned`
2. connect workflow transition application into one real runtime action path
3. continue replacing inline workflow heuristics in `techlead.py` incrementally

### Current progress
- `qa_result_returned` is now supported in `WorkflowLifecycleService`
- supported QA transition family:
  - `qa_execution_in_progress -> techlead_qa_review_pending`
- supported QA packet schema:
  - `qa_verification_packet`
- lifecycle behavior now advances lineage from:
  - `awaiting_result -> awaiting_acceptance`
- one real runtime action path now uses:
  - `apply_workflow_transition(...)`
- connected runtime path:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-consumer/src/paa_consumer/techlead.py`
  - `emit_next_assignment(...)`
- current applied runtime family:
  - `worker_result_returned`

### Remaining next choice
1. extend runtime application to `qa_result_returned`
2. continue replacing inline workflow heuristics in `techlead.py` incrementally

## Priority Summary

### Immediate priority
1. `Execution Package Resolution Service` Phase 3
2. `Execution Package Resolution Service` Phase 4
3. execution-context bridge validation

### Next priority
4. one real consumer integration for `Execution Package Resolution Service`
5. `Workflow Lifecycle Service` pre-spec and policy decomposition

### Then
6. workflow repository adapters
7. `Workflow Lifecycle Service` spec and initial code slices

## Success Condition

This execution plan is successful when:
1. `Execution Package Resolution Service` is a real read-oriented domain service, not just a shell
2. at least one real downstream consumer uses it instead of ad hoc package lookup logic
3. `Workflow Lifecycle Service` begins against explicit policy and repository collaborators rather than another oversized blob

## When To Use The PAA System And Methodology

Use the PAA methodology now.
We are already using it for:
- dependency-graph-based next-target selection
- component boundary definition
- repository and policy boundary checks
- implementation-plan derivation
- coder-brief derivation

Use the PAA system whenever the slice has these prerequisites:
1. approved authority / design package
2. consumer-specific implementation plan
3. implementation-plan activities mapped to:
   - component
   - component element
   - code artifact target
4. coder-brief derivation inputs are explicit enough to assemble governed brief authority

In practice, that means:
- for new implementation slices, use the methodology first to define the component and plan cleanly
- then use the system to materialize:
  - design package
  - implementation plan
  - coder brief
  - targets
  - governed authority

The more accurate answer is not “later.”
It is:
- use the methodology continuously
- use the system as soon as a slice is structured enough to materialize authoritative records instead of relying on architect memory or prose only
