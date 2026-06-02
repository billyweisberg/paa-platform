Title: PAA Operator CLI Component Spec
Doc-ID: paa-operator-cli-component-spec
Doc-Type: component-spec
Status: active
Lifecycle-Stage: design
Created: 2026-05-30
Last-Edited: 2026-06-02
Author: Billy Weisberg
Repo: paa-platform
Component: PAAOperatorCLI
Domain: operator-cli
Keywords: paa, cli, typer, operator, authority, package, readiness, brief, packet, plan, component, worker, queue, verify, accept, report, ops
Depends-On: 2026-05-28-paa-cli-system-architecture.md, 2026-05-28-paa-authority-stack-and-operator-architecture.md, 2026-05-28-paa-operator-system-implementation-plan.md, 2026-05-30-paa-cli-command-inventory-and-migration-map.md, 2026-05-30-paa-modeled-ownership-inventory.md, 2026-05-30-paa-cli-node-diagram.md, 2026-05-30-paa-cli-object-model.md, 2026-05-30-paa-cli-component-relationships-and-dependency-graph-slice.md, 2026-05-30-paa-cli-service-injection-and-collaboration-table.md, 2026-05-30-paa-cli-business-object-ownership-map.md, 2026-05-30-paa-methodology-execution-state-model.md, 2026-05-30-paa-methodology-lane-and-command-model.md, 2026-05-30-paa-operator-cli-command-family-decomposition.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-06-30
Summary: Defines the governed unified Typer-based operator CLI that consolidates producer, consumer, authority, verification, queue, and worker command surfaces into one lifecycle-oriented PAA application boundary.

# PAA Operator CLI Component Spec

Date: 2026-05-30

## Purpose

Define the full `Component Spec` for `PAAOperatorCLI` as the operator-facing application boundary for the full PAA methodology.

This component exists to replace the former split between:
- `paa-producer` command roots
- `paa-consumer` command roots
- operator-relevant scripts under `scripts/docs/`, `scripts/governance/`, and `scripts/runtime/`

with one governed CLI application that exposes the methodology as an operable system.

`PAAOperatorCLI` is not a toy wrapper around existing commands.
It is the real operator shell for:
- authority inspection and publication
- derivation and materialization
- implementation-plan progress and successor-slice derivation
- worker and queue operations
- verification and acceptance
- reporting and system operations

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/1_Vision/2026-05-28-paa-authority-stack-and-operator-architecture.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/1_Vision/2026-05-28-paa-cli-system-architecture.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/1_Vision/2026-05-28-paa-worker-runtime-architecture.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/1_Vision/2026-05-28-paa-operator-system-implementation-plan.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-30-paa-cli-command-inventory-and-migration-map.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-30-paa-modeled-ownership-inventory.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-30-paa-cli-node-diagram.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-30-paa-cli-object-model.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-30-paa-cli-component-relationships-and-dependency-graph-slice.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-30-paa-cli-service-injection-and-collaboration-table.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-30-paa-cli-business-object-ownership-map.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-30-paa-methodology-execution-state-model.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-30-paa-methodology-lane-and-command-model.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-30-paa-operator-cli-command-family-decomposition.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/current/policy/component-spec-template-materialization-bridge.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/4_Build/2026-05-27-component-realization-loop.md`

## Architecture Placement

Layer:
- `Host Surfaces`

Dependency stratum:
- `Stratum 4`

Primary upstream dependencies:
- host-support collaborators: `EnvironmentResolver`, `CommandRouter`, `CommandResultNormalizer`, and `OutputRenderer`
- governed core services where stable modeled owners already exist
- transitional producer and internal consumer-package collaborators behind explicit adapter boundaries
- future worker-runtime controller components such as `TechLeadWorkerService`, `DevWorkerService`, `QAWorkerService`, and `QueuePacketRuntimeController`

Primary downstream consumers:
- human operators using the PAA system directly
- local automation wrappers that require a stable operator entrypoint
- future role-specific worker-host programs that need shared operator diagnostics and dry-run surfaces

## Component Identity Table

| component_name | component_kind | alignment_state | system_layer | tier | status |
|---|---|---|---|---|---|
| PAAOperatorCLI | service | aligned | host-surfaces | runtime | active |

## 1. Role

`PAAOperatorCLI` provides the unified Typer-based command application for the full PAA methodology.

Authority boundary:
- owns top-level command-family grammar and command registration
- owns CLI host-surface objects such as command identity, invocation context, normalized command requests, normalized command results, failures, and render structures
- owns operator-facing argument normalization and output-shape normalization
- owns lifecycle-oriented command grouping across authority-derivation, component-realization, runtime-execution, acceptance-closeout, and cross-lane ops families
- owns fail-closed operator error surfacing when required authority or runtime context is missing
- owns JSON and table output shaping for operator-safe command results
- owns thin adapter dispatch into existing producer, internal consumer-package, and core capabilities
- owns bridge-only operation request objects used to communicate with downstream owners
- does not own core business decisions already governed by domain services
- does not own implementation-plan persistence or implementation-plan truth
- does not own workflow truth, queue truth, acceptance truth, or execution-package truth
- does not own queue transport primitives directly
- does not own worker-runtime orchestration policy
- does not own GitHub mutation or acceptance policy

## Ownership Boundary

Owned responsibilities:
- top-level `paa` command root
- command-family registration for:
  - `authority`
  - `package`
  - `readiness`
  - `brief`
  - `packet`
  - `plan`
  - `component`
  - `worker`
  - `queue`
  - `verify`
  - `accept`
  - `report`
  - `ops`
- host-support coordination for environment resolution, command routing, result normalization, and rendering
- command invocation normalization from CLI args and environment into structured CLI-owned request objects
- stable operator output formatting in JSON and table modes
- bounded exit-code semantics and fail-closed error reporting
- bridge-only translation from unified CLI requests into downstream authority, derivation, planning, worker, queue, verification, acceptance, reporting, and ops operations
- migration bridge from current producer, internal consumer-package, and script command surfaces to the unified operator application

## Non-Ownership Boundary

Excluded responsibilities:
- implementation-plan derivation logic itself
- implementation-plan progress computation itself
- workflow lifecycle policy itself
- TechLead decision policy itself
- queue message transport primitives
- worker-host agent execution
- acceptance and merge policy evaluation
- direct persistence ownership for repositories already modeled elsewhere
- ownership of downstream primary-truth objects such as `Workflow`, `QueueClaim`, `HandoffPacket`, `AcceptanceEvent`, `InstalledExecutionPackage`, or `ImplementationPlan`
- allowing transitional module return shapes to become the permanent public CLI contract
- freeform shell scripting as the long-term operator interface

## Collaborators

| collaborator | collaborator_kind | dependency_role |
|---|---|---|
| `EnvironmentResolver` | host-support | resolve repo-root, config, and environment bindings for each invocation |
| `CommandRouter` | host-support | dispatch one normalized operator command into the selected command-family adapter |
| `CommandResultNormalizer` | host-support | normalize adapter and collaborator outputs into stable CLI-owned result objects |
| `OutputRenderer` | host-support | render normalized command results in JSON, table, or summary modes |
| `StructuredLogger` | adapter | emit structured operator diagnostics and failure details |
| `ImplementationPlanProgressService` | service | provide stable planning progress, reconciliation, and next-slice command results |
| `ImplementationPlanDerivationService` | service | provide stable implementation-plan derivation semantics where governed service ownership already exists |
| `WorkflowLifecycleService` | service | support workflow-aware inspection and diagnostics where needed |
| `ExecutionPackageResolutionService` | service | support execution-package and runtime-context diagnostics where needed |
| `TechLead` decision-service family | service family | support governed decision diagnostics and acceptance-aligned inspection surfaces |
| transitional producer module-backed collaborators | transitional-module | provide authority, derivation, coder-brief, packet, and ops functionality behind explicit adapter boundaries until governed replacements exist |
| transitional consumer package-backed collaborators | transitional-module | provide queue, runtime host, guardrail, and reporting surfaces behind explicit adapter boundaries while the internal package boundary still exists |
| future `TechLeadWorkerService`, `DevWorkerService`, `QAWorkerService`, and `QueuePacketRuntimeController` | future-governed-target | replace current runtime-shell and queue-helper collaborators without changing CLI-owned invocation or render semantics |

## Component Elements Table

| element_name | element_kind | description | owned_by_component |
|---|---|---|---|
| operator_cli_interface | interface | public application contract for invoking one normalized operator command request and receiving one normalized command result | PAAOperatorCLI |
| operator_cli_models | dto | CLI-owned invocation, result, failure, output, and bridge request DTOs aligned to the CLI object model and ownership map | PAAOperatorCLI |
| operator_cli_environment_resolution | implementation | repo-root, config, environment-binding, and invocation-context resolution support | PAAOperatorCLI |
| operator_cli_command_router | implementation | family and subcommand dispatch over registered command adapters | PAAOperatorCLI |
| operator_cli_result_normalization | implementation | normalization of adapter and collaborator outputs into stable CLI-owned result objects | PAAOperatorCLI |
| operator_cli_output_rendering | implementation | JSON, table, and summary rendering of normalized command results | PAAOperatorCLI |
| operator_cli_command_adapters | implementation | thin lane-aware command-family adapters that translate normalized operator requests into governed services or transitional collaborators | PAAOperatorCLI |
| operator_cli_typer_shell | implementation | Typer root application that composes host-support collaborators and registered command-family adapters | PAAOperatorCLI |
| operator_cli_validation_surface | verification-surface | tests and governed proofs covering grammar stability, object ownership, fail-closed behavior, and command-to-owner mapping | PAAOperatorCLI |

## Realizations Table

| element_name | realization_kind | artifact_kind | artifact_target | verification_role |
|---|---|---|---|---|
| operator_cli_interface | service_interface | python-module | `packages/paa-cli/src/paa_cli/contracts.py` | interface contract validation |
| operator_cli_models | dto | python-module | `packages/paa-cli/src/paa_cli/models.py` | DTO and ownership-boundary validation |
| operator_cli_environment_resolution | service_implementation | python-module | `packages/paa-cli/src/paa_cli/environment.py` | invocation-context and environment-binding validation |
| operator_cli_command_router | service_implementation | python-module | `packages/paa-cli/src/paa_cli/router.py` | grammar and dispatch validation |
| operator_cli_result_normalization | service_implementation | python-module | `packages/paa-cli/src/paa_cli/normalization.py` | normalized-result and transition-shape validation |
| operator_cli_output_rendering | service_implementation | python-module | `packages/paa-cli/src/paa_cli/rendering.py` | JSON, table, and summary rendering validation |
| operator_cli_command_adapters | service_implementation | python-module | `packages/paa-cli/src/paa_cli/command_adapters.py` | adapter dispatch and collaborator-mapping validation |
| operator_cli_typer_shell | service_implementation | python-module | `packages/paa-cli/src/paa_cli/app.py` | root grammar and composition validation |
| operator_cli_typer_shell | package_export | python-module | `packages/paa-cli/src/paa_cli/__init__.py` | export-surface validation |
| operator_cli_validation_surface | test_module | python-module | `tests/unit/test_paa_operator_cli.py` | service-level validation and proof |

## 2. Component State Model

The CLI should be stateless across invocations.

### Persistent state
This component owns no primary persistent state.

It may observe or route to persistent truth through existing repositories and services, but it should not become the primary owner of:
- implementation plans
- workflow state
- runtime events
- queue claims
- execution packages

### In-memory working state
During one invocation, the component may hold:
- parsed argv and environment-derived options
- normalized `OperatorCommand`, `OperatorInvocationContext`, and `OperatorCommandRequest` objects
- selected command-family registration state, including lane-aware family bindings
- bridge-only operation request objects for the selected command family
- structured `OperatorCommandResult`, `OperatorFailure`, `OutputSection`, `OutputTable`, and `OutputMessage` objects
- formatting mode and output-buffer state
- transient diagnostics and warnings

### State rule
The CLI must not create hidden authority or workflow truth.
It is an operator surface over existing model truth and runtime actions.

## 3. Service Contract

The component provides a normalized operator-command invocation contract over the full PAA methodology surface.

### Inputs
- top-level command family identity
- command name or subcommand identity
- normalized arguments and options
- output mode request such as `json` or `table`
- optional repo-root or environment overrides
- optional dry-run flags
- optional strict-mode flags
- optional worker or queue target selectors

### Outputs
- structured command result DTOs
- normalized success, blocked, unsupported, and failed outcomes
- machine-readable payloads for JSON mode
- human-readable table or summary payloads for terminal mode
- explicit exit-code mapping guidance for adapter shells

### Guarantees
- command nouns remain lifecycle-oriented rather than repository-oriented
- raw producer or consumer exceptions are normalized into operator-safe failure results
- missing authority or unsupported command-state combinations fail closed with explicit reasons
- output formatting remains stable enough for both human operators and wrapper automation
- Typer is the application framework, but business logic remains outside command functions

### Non-guarantees
- this component does not replace domain-service contracts
- this component does not decide policy that belongs in underlying services
- this component does not guarantee that every current script is preserved as-is
- this component does not own long-running worker execution loops

## 4. Data Contract

The component operates on CLI-owned host-surface objects and bridge-only operation request objects.

### Primary consumed records or views
- normalized command-family registry
- current authority and derivation collaborator surfaces
- current planning and runtime collaborator surfaces
- environment and repo-root resolution context
- optional queue, worker, verification, or reporting diagnostic views returned by downstream owners

### CLI-owned DTOs to expose

#### `OperatorCommandFamily`
Carries:
- family identity
- display name
- family description
- family default output expectations

#### `OperatorCommandRegistration`
Carries:
- family binding
- command name
- optional subcommand name
- alias set
- help summary
- target adapter identity
- output mode support

#### `OperatorCommandRequest`
Carries:
- normalized command identity
- normalized arguments
- normalized options
- invocation context
- optional dry-run and strict-mode flags
- optional invocation metadata

#### `OperatorCommandResult`
Carries:
- command echo identifiers
- normalized command summary
- `ok`
- optional `exit_code`
- optional `reason`
- optional `details`
- optional `structured_payload`
- optional `display_sections`
- optional `metadata`

#### `OperatorFailure`
Carries:
- failure class
- reason code
- summary
- blocking scope
- remediation hint
- optional source exception metadata

### Bridge-only operation request DTO families
The CLI should also define bridge-only request objects for:
- authority operations
- derivation operations
- planning operations
- worker operations
- queue operations
- verification operations
- acceptance operations
- reporting operations
- ops operations

### Ownership rule
The CLI must own:
- invocation, registration, result, failure, rendering, and environment-binding objects
- bridge-only request objects used to communicate with downstream owners

The CLI must not own downstream primary-truth objects such as:
- `Workflow`
- `QueueClaim`
- `HandoffPacket`
- `AcceptanceEvent`
- `InstalledExecutionPackage`
- `ImplementationPlan` and related planning entities
- governed TechLead decision-service DTO families

### Data contract rule
The CLI must return stable structured command results.
It should not require command adapters or tests to reconstruct meaning from ad hoc print strings, raw module dicts, or direct script stdout.

## 5. Injected Services

### Required injected services and host-support collaborators
- `EnvironmentResolver`
- `CommandRouter`
- `CommandResultNormalizer`
- `OutputRenderer`
- `StructuredLogger`

### Required governed collaborator surfaces
- `ImplementationPlanProgressService`
- `ImplementationPlanDerivationService`
- `WorkflowLifecycleService` when workflow-aware inspection is required
- `ExecutionPackageResolutionService` when execution-context diagnostics are required
- governed TechLead decision-service collaborators where verification or acceptance-aligned inspection depends on them

### Required command-family adapter surfaces
- authority command adapter surface
- package command adapter surface
- readiness command adapter surface
- brief command adapter surface
- packet command adapter surface
- plan command adapter surface
- component command adapter surface
- worker command adapter surface
- queue command adapter surface
- verification command adapter surface
- acceptance command adapter surface
- reporting command adapter surface
- ops command adapter surface

### Transitional injected collaborators
The first implementation slices may still inject transitional module-backed collaborators behind explicit adapter boundaries, especially for:
- authority operations
- derivation adjuncts such as design-package, coder-brief, and packet preparation flows
- queue operations
- worker operations
- runtime guardrails and governance proof scripts
- reporting surfaces such as `techlead_service_map.py`

### Future governed targets
The design should allow later collaborator replacement by:
- `TechLeadWorkerService`
- `DevWorkerService`
- `QAWorkerService`
- `QueuePacketRuntimeController`
- future governed authority-tooling, reporting, verification, and ops component families

### Important non-injected collaborators
This component should not depend directly on:
- raw queue transport clients when an existing runtime adapter is available
- raw database sessions when a governed repository or service already exists
- Typer callback-local business logic as the primary execution owner
- transitional module return shapes as if they were stable public CLI objects

If those become necessary, the component boundary should be reconsidered.

## 6. Interfaces

### Provided interface
- `PAAOperatorCLI`

### Required interfaces
- host-support interface set for environment resolution, routing, normalization, and rendering
- authority command-adapter interface
- package command-adapter interface
- readiness command-adapter interface
- brief command-adapter interface
- packet command-adapter interface
- plan command-adapter interface
- component command-adapter interface
- worker command-adapter interface
- queue command-adapter interface
- verification command-adapter interface
- acceptance command-adapter interface
- reporting command-adapter interface
- ops command-adapter interface
- `StructuredLogger`

## 7. Constraints And Non-Goals

### Constraints
- the implementation must be a real Typer application
- command-family names must align with `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/1_Vision/2026-05-28-paa-cli-system-architecture.md`
- the CLI must preserve fail-closed authority behavior
- the first slice must consolidate existing capabilities rather than reimplement them from scratch
- the first slice should start where modeled ownership is strongest, especially `component` and `plan`, before worker and queue-heavy families
- command handlers must remain thin and delegate to modeled owners or adapters
- JSON output must remain stable enough for automation consumers

### Non-goals
- fully rewriting every producer and consumer command in the first slice
- designing every final subcommand flag in this component spec
- replacing future worker-runtime controllers with CLI-only logic
- preserving a parallel standalone `paa-consumer` CLI once migration is complete

## Plan Seed Table

| plan_name | consumer_context_key | primary_component_name | implementation_target_kind | plan_status |
|---|---|---|---|---|
| plan-materialize-paa-operator-cli-proof-python | paa-platform-python | PAAOperatorCLI | python-package | active_plan |

## Activity Seed Table

| activity_key | activity_name | sequence | activity_kind | element_name | realization_kind | done_definition |
|---|---|---:|---|---|---|---|
| operator-cli-interface-contract | Implement operator CLI interface contract | 10 | contract-authoring | operator_cli_interface | service_interface | interface protocol exists and reflects CLI-owned versus bridge-only ownership boundaries |
| operator-cli-dto-models | Implement operator CLI DTO and bridge request models | 20 | dto-materialization | operator_cli_models | dto | CLI-owned invocation/result/failure/output DTOs and bridge-only operation request DTOs exist and align to the ownership map |
| operator-cli-host-support | Implement environment resolution, routing, normalization, and rendering host-support nodes | 30 | service-implementation | operator_cli_environment_resolution | service_implementation | host-support modules exist for environment resolution, routing, normalization, and rendering, and the root host composes them explicitly |
| operator-cli-component-and-plan-adapters | Implement first command-family adapters for `component` and `plan` | 40 | service-implementation | operator_cli_command_adapters | service_implementation | the strongest governed adapter paths exist first and route through component materialization, implementation-plan progress, reconciliation, and next-slice derivation |
| operator-cli-validation-surface | Implement operator CLI validation surface | 50 | verification | operator_cli_validation_surface | test_module | tests prove grammar stability, ownership boundaries, fail-closed behavior, host-support composition, and first-family adapter mapping |

## Activity Dependency Table

| activity_key | depends_on_activity_key | dependency_kind |
|---|---|---|
| operator-cli-dto-models | operator-cli-interface-contract | hard |
| operator-cli-host-support | operator-cli-dto-models | hard |
| operator-cli-component-and-plan-adapters | operator-cli-host-support | hard |
| operator-cli-validation-surface | operator-cli-component-and-plan-adapters | hard |

## Verification Surface Table

| verification_surface | verification_kind | artifact_target | required_for_acceptance |
|---|---|---|---|
| operator_cli_contract_tests | unit-test | `tests/unit/test_paa_operator_cli.py` | true |
| operator_cli_model_tests | unit-test | `tests/unit/test_paa_operator_cli.py` | true |
| operator_cli_command_grammar_tests | unit-test | `tests/unit/test_paa_operator_cli.py` | true |
| operator_cli_host_support_tests | unit-test | `tests/unit/test_paa_operator_cli.py` | true |
| operator_cli_ownership_boundary_tests | unit-test | `tests/unit/test_paa_operator_cli.py` | true |
| operator_cli_component_and_plan_adapter_tests | unit-test | `tests/unit/test_paa_operator_cli.py` | true |
| operator_cli_model_code_consistency | governance-proof | `scripts/governance/paa_model_code_consistency.py --component PAAOperatorCLI` | true |
| operator_cli_spec_model_consistency | governance-proof | `scripts/governance/paa_component_spec_model_consistency.py --spec docs/2_Design/2026-05-30-paa-operator-cli-component-spec.md` | true |
