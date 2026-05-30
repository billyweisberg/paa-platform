Title: PAA CLI Component Relationships And Dependency Graph Slice
Doc-ID: paa-cli-component-relationships-and-dependency-graph-slice
Doc-Type: design-note
Status: active
Lifecycle-Stage: design
Created: 2026-05-30
Last-Edited: 2026-05-30
Author: Billy Weisberg
Repo: paa-platform
Component: PAAOperatorCLI
Domain: operator-cli
Keywords: paa, cli, dependency-graph, component-relationships, sequencing, command-family, stage1
Depends-On: 2026-05-03-component-dependency-graph-contract.md, 2026-05-03-stage1-design-package-contract.md, 2026-05-30-paa-cli-node-diagram.md, 2026-05-30-paa-cli-object-model.md, 2026-05-30-paa-modeled-ownership-inventory.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-06-30
Summary: Defines the Stage 1 component relationships and local dependency-graph slice for the unified PAA operator CLI, including typed dependency edges, blocking dependencies, and contract-before-implementation sequencing rules.

# PAA CLI Component Relationships And Dependency Graph Slice

## Purpose

Define the local Stage 1 dependency-graph slice for the unified `paa` operator CLI.

This note exists to make explicit:
- which CLI nodes are primary versus supporting
- which typed dependencies must be satisfied before implementation begins
- which edges are hard versus soft
- which nodes may parallelize after contract stabilization
- which current modeled owners are still transitional dependencies rather than final governed component dependencies

## Relationship To Stage 1 Design Package

This note fulfills the Stage 1 requirement for:
- component relationships
- collaboration pattern
- dependency graph slice
- blocking dependencies
- sequencing constraints

It is the CLI-specific application of:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-component-dependency-graph-contract.md`

## Primary Design Question

What must be defined before `PAAOperatorCLI` can safely enter implementation?

Answer:
- the host-surface object model
- the command-family structure
- the normalization and rendering boundaries
- the bridge relationship to current producer and consumer owners
- the typed dependency edges between the CLI host and downstream modeled owners

## Graph Scope

This is a local graph slice for the current CLI authority package.

It covers:
- host-surface nodes
- command-family nodes
- current downstream owner nodes that materially block CLI design and first-slice implementation

It does not yet attempt to represent:
- every downstream module function
- every future worker-runtime internal node
- every code-artifact-level edge inside future CLI subpackages

## Primary Component

Primary component:
- `PAAOperatorCLI`

Role:
- unified host-surface operator application for the PAA methodology

## Supporting Components And Nodes

Supporting structural nodes in this graph slice:
- `EnvironmentResolver`
- `CommandRouter`
- `CommandResultNormalizer`
- `OutputRenderer`
- `AuthorityCommandAdapter`
- `DeriveCommandAdapter`
- `PlanCommandAdapter`
- `WorkerCommandAdapter`
- `QueueCommandAdapter`
- `VerificationCommandAdapter`
- `AcceptanceCommandAdapter`
- `ReportingCommandAdapter`
- `OpsCommandAdapter`

Important current downstream supporting owners:
- `ImplementationPlanProgressService`
- `ImplementationPlanDerivationService`
- `WorkflowLifecycleService`
- `TechLead decision-service family`
- governed repositories
- producer module family
- consumer module family

## Node Table

| node_name | node_role | system_layer | tier | status | surface_set |
|---|---|---|---|---|---|
| `PAAOperatorCLI` | primary host surface | host-surfaces | runtime | planned | Typer root app, package export |
| `EnvironmentResolver` | host support node | host-surfaces | runtime | planned | repo-root resolution, environment binding |
| `CommandRouter` | host support node | host-surfaces | runtime | planned | family and subcommand dispatch |
| `CommandResultNormalizer` | host support node | host-surfaces | runtime | planned | normalized result shaping |
| `OutputRenderer` | host support node | host-surfaces | runtime | planned | JSON, table, summary output |
| `AuthorityCommandAdapter` | family adapter node | host-surfaces | runtime | planned | authority-family command entrypoints |
| `DeriveCommandAdapter` | family adapter node | host-surfaces | runtime | planned | derivation-family command entrypoints |
| `PlanCommandAdapter` | family adapter node | host-surfaces | runtime | planned | planning-family command entrypoints |
| `WorkerCommandAdapter` | family adapter node | host-surfaces | runtime | planned | worker-family command entrypoints |
| `QueueCommandAdapter` | family adapter node | host-surfaces | runtime | planned | queue-family command entrypoints |
| `VerificationCommandAdapter` | family adapter node | host-surfaces | runtime | planned | verification-family command entrypoints |
| `AcceptanceCommandAdapter` | family adapter node | host-surfaces | runtime | planned | acceptance-family command entrypoints |
| `ReportingCommandAdapter` | family adapter node | host-surfaces | runtime | planned | reporting-family command entrypoints |
| `OpsCommandAdapter` | family adapter node | host-surfaces | runtime | planned | ops-family command entrypoints |
| `ImplementationPlanProgressService` | downstream governed service | application-services | runtime | active | progress summary and next-slice logic |
| `ImplementationPlanDerivationService` | downstream governed service | domain-services | runtime | active | implementation-plan derivation |
| `WorkflowLifecycleService` | downstream governed service | domain-services | runtime | active | workflow interpretation |
| `TechLead decision-service family` | downstream governed service family | application-services | runtime | active | assignment, routing, acceptance, closeout policy surfaces |
| `Producer module family` | downstream transitional owner | host-surfaces | runtime | active | authority, derivation, packet, and brief modules |
| `Consumer module family` | downstream transitional owner | host-surfaces | runtime | active | queue, runtime shell, guardrail, install modules |
| `Governed repositories` | downstream persistence owner | infrastructure-ports | runtime | active | workflow, runtime-event, execution-package, implementation-plan, component-design truth |
| `TechLeadWorkerService` | future runtime controller | application-services | runtime | planned | worker runtime controller |
| `DevWorkerService` | future runtime controller | application-services | runtime | planned | bounded Dev worker runtime |
| `QAWorkerService` | future runtime controller | application-services | runtime | planned | bounded QA worker runtime |
| `QueuePacketRuntimeController` | future runtime controller | application-services | runtime | planned | queue and packet runtime control |

## Relationship Summary Table

| from_node | to_node | relationship_kind | explanation |
|---|---|---|---|
| `PAAOperatorCLI` | `EnvironmentResolver` | hosts | root host depends on invocation environment normalization |
| `PAAOperatorCLI` | `CommandRouter` | hosts | root host delegates family and subcommand dispatch |
| `PAAOperatorCLI` | `CommandResultNormalizer` | hosts | root host requires stable structured command results |
| `PAAOperatorCLI` | `OutputRenderer` | hosts | root host requires human and machine output rendering |
| `CommandRouter` | all command-family adapters | dispatches_to | routing selects one adapter based on family and subcommand |
| command-family adapters | `CommandResultNormalizer` | returns_to | adapters must return structured results for normalization |
| `CommandResultNormalizer` | `OutputRenderer` | renders_through | normalized results are rendered after semantic shaping |
| `PlanCommandAdapter` | `ImplementationPlanProgressService` | depends_on_service | planning commands rely on governed progress service |
| `DeriveCommandAdapter` | `ImplementationPlanDerivationService` | depends_on_service | derivation commands rely on governed derivation service or adjacent derivation surfaces |
| `WorkerCommandAdapter` | `TechLeadWorkerService` | future_runtime_target | long-term worker commands should target worker controllers |
| `WorkerCommandAdapter` | `DevWorkerService` | future_runtime_target | Dev worker operations should target a governed runtime controller |
| `WorkerCommandAdapter` | `QAWorkerService` | future_runtime_target | QA worker operations should target a governed runtime controller |
| `QueueCommandAdapter` | `QueuePacketRuntimeController` | future_runtime_target | queue commands should target a governed queue runtime surface |
| `VerificationCommandAdapter` | `TechLead decision-service family` | depends_on_service | verification diagnostics may consult governed decision services |
| `AcceptanceCommandAdapter` | `TechLead decision-service family` | depends_on_service | acceptance-family commands rely on existing acceptance and closeout policy surfaces |
| `WorkerCommandAdapter` | `Consumer module family` | transitional_dependency | worker operations currently still lean on consumer modules |
| `QueueCommandAdapter` | `Consumer module family` | transitional_dependency | queue operations currently still lean on `inbox.py` and related runtime helpers |
| `AuthorityCommandAdapter` | `Producer module family` | transitional_dependency | authority operations currently still lean on producer modules and scripts |
| `DeriveCommandAdapter` | `Producer module family` | transitional_dependency | derivation operations currently still lean on producer modules |
| `VerificationCommandAdapter` | `Producer module family` | transitional_dependency | verification operations still rely partly on governance scripts and producer-side proof surfaces |
| `ReportingCommandAdapter` | `Governed repositories` | depends_on_state | reporting reads projected or durable model truth |
| `OpsCommandAdapter` | `Producer module family` | transitional_dependency | ops commands still rely partly on runtime/bootstrap helpers |
| `OpsCommandAdapter` | `Consumer module family` | transitional_dependency | ops commands still rely partly on runtime guardrail helpers |

## Typed Dependency Edge Table

| from_node | to_node | dependency_type | dependency_strength | sequencing_requirement | blocking_scope | notes |
|---|---|---|---|---|---|---|
| `PAAOperatorCLI` | `EnvironmentResolver` | depends_on_hosting | hard | must_precede | design | invocation environment must be modeled before host implementation |
| `PAAOperatorCLI` | `CommandRouter` | depends_on_contract | hard | must_precede | design | routing contract is part of the CLI host boundary |
| `PAAOperatorCLI` | `CommandResultNormalizer` | depends_on_contract | hard | must_precede | design | CLI public interface requires normalized result semantics |
| `PAAOperatorCLI` | `OutputRenderer` | depends_on_hosting | hard | must_precede | design | output behavior must be defined before host implementation |
| `CommandRouter` | command-family adapters | depends_on_contract | hard | must_precede | design | family adapter contracts must exist before routing implementation is stable |
| `AuthorityCommandAdapter` | `Producer module family` | depends_on_injection | soft | must_follow_contract_only | execution | first slice may wrap existing producer owners through a stable adapter contract |
| `DeriveCommandAdapter` | `Producer module family` | depends_on_injection | soft | must_follow_contract_only | execution | first slice may wrap existing producer owners through a stable adapter contract |
| `PlanCommandAdapter` | `ImplementationPlanProgressService` | depends_on_contract | hard | must_precede | design | planning adapter contract should follow governed progress service surface |
| `PlanCommandAdapter` | `ImplementationPlanProgressService` | depends_on_injection | hard | must_follow_contract_only | execution | adapter can implement once service contract is stable |
| `DeriveCommandAdapter` | `ImplementationPlanDerivationService` | depends_on_contract | hard | must_precede | design | derivation adapter requires governed derivation semantics |
| `DeriveCommandAdapter` | `ImplementationPlanDerivationService` | depends_on_injection | hard | must_follow_contract_only | execution | first slice can inject the existing service |
| `WorkerCommandAdapter` | `Consumer module family` | depends_on_hosting | soft | must_follow_contract_only | execution | current dependency is transitional and should later be replaced |
| `WorkerCommandAdapter` | `TechLeadWorkerService` | depends_on_contract | soft | must_follow_contract_only | design | future worker controller should replace shell-backed worker paths |
| `QueueCommandAdapter` | `Consumer module family` | depends_on_hosting | soft | must_follow_contract_only | execution | current dependency is transitional and should later be replaced |
| `QueueCommandAdapter` | `QueuePacketRuntimeController` | depends_on_contract | soft | must_follow_contract_only | design | future queue runtime component is planned but not yet realized |
| `VerificationCommandAdapter` | `Producer module family` | depends_on_hosting | soft | must_follow_contract_only | execution | proof scripts remain transitional downstream owners |
| `VerificationCommandAdapter` | `TechLead decision-service family` | depends_on_contract | soft | must_follow_contract_only | design | some diagnostic commands need governed decision semantics |
| `AcceptanceCommandAdapter` | `TechLead decision-service family` | depends_on_contract | hard | must_precede | design | acceptance-family CLI paths must align to governed decision services |
| `ReportingCommandAdapter` | `Governed repositories` | depends_on_state | hard | must_follow_contract_only | execution | reporting needs durable truth but does not own it |
| `OpsCommandAdapter` | `Producer module family` | depends_on_hosting | soft | must_follow_contract_only | execution | operational helpers remain transitional |
| `OpsCommandAdapter` | `Consumer module family` | depends_on_hosting | soft | must_follow_contract_only | execution | operational helpers remain transitional |
| `CommandResultNormalizer` | `OutputRenderer` | depends_on_contract | hard | must_precede | design | rendering must consume a stable normalized result contract |

## Blocking Dependencies

The current hard blocking dependencies for first-slice CLI work are:
- `EnvironmentResolver`
- `CommandRouter`
- `CommandResultNormalizer`
- `OutputRenderer`
- command-family adapter contracts
- stable `PlanCommandAdapter -> ImplementationPlanProgressService` contract alignment
- stable `DeriveCommandAdapter -> ImplementationPlanDerivationService` contract alignment
- stable `AcceptanceCommandAdapter -> TechLead decision-service family` contract alignment

Important rule:
- module-backed downstream owners are not all design blockers for the first slice
- but the adapter contract over them must be explicit before implementation begins

## Parallelizable Dependencies

After the root host contract and result-normalization contract are stable, the following families may parallelize in later implementation slices:
- `AuthorityCommandAdapter`
- `DeriveCommandAdapter`
- `PlanCommandAdapter`
- `VerificationCommandAdapter`
- `ReportingCommandAdapter`
- `OpsCommandAdapter`

The following should not be treated as parallel-safe yet without further runtime design:
- `WorkerCommandAdapter`
- `QueueCommandAdapter`
- `AcceptanceCommandAdapter`

Reason:
- they still depend more heavily on transitional shell/runtime owners or acceptance-sensitive flows

## Contract-Before-Implementation Decisions

The graph implies these explicit contract-first rules:

1. `PAAOperatorCLI` host contract must be defined before Typer implementation
2. `OperatorCommandRequest` and `OperatorCommandResult` semantics must be stable before adapter implementations
3. `PlanCommandAdapter` must follow the governed `ImplementationPlanProgressService` contract
4. `DeriveCommandAdapter` must follow the governed `ImplementationPlanDerivationService` contract where applicable
5. `AcceptanceCommandAdapter` must follow governed acceptance and closeout decision-service semantics
6. `WorkerCommandAdapter` and `QueueCommandAdapter` may use transitional module-backed owners first, but only through explicit adapter contracts

## Sequencing Reading

The graph currently supports this first design/build sequence:
1. host-surface object model and contracts
2. root host and routing contract
3. result normalization and rendering contract
4. plan and derive adapter slices first
5. reporting and authority adapter slices next
6. verification and ops slices after those
7. worker, queue, and acceptance slices after additional runtime-controller design stabilizes

This means the first real CLI implementation should not try to absorb every family at once.
It should start where modeled ownership is already strongest.

## Design Conclusion

This dependency-graph slice shows that the unified CLI is structurally placeable, but only if we respect the split between:
- host-owned CLI objects and contracts
- adapter-owned bridge objects
- downstream governed services
- downstream transitional modules
- future runtime controllers

The biggest design risk is not missing a Typer root.
It is accidentally collapsing transitional module-backed behavior into permanent CLI-owned business logic.

## Immediate Follow-On Artifact

The next CLI design artifact should define:
- `PAA CLI Service Injection And Collaboration Table`

That note should make explicit:
- which services and adapters are injected into each command-family adapter
- which downstream owners are temporary transitional collaborators
- which collaborations should later be redirected to governed runtime controllers
