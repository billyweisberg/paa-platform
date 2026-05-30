Title: PAA CLI Service Injection And Collaboration Table
Doc-ID: paa-cli-service-injection-and-collaboration-table
Doc-Type: design-note
Status: active
Lifecycle-Stage: design
Created: 2026-05-30
Last-Edited: 2026-05-30
Author: Billy Weisberg
Repo: paa-platform
Component: PAAOperatorCLI
Domain: operator-cli
Keywords: paa, cli, service-injection, collaboration, adapters, typer, dependencies, runtime
Depends-On: 2026-05-30-paa-cli-node-diagram.md, 2026-05-30-paa-cli-object-model.md, 2026-05-30-paa-cli-component-relationships-and-dependency-graph-slice.md, 2026-05-30-paa-modeled-ownership-inventory.md, 2026-05-03-stage1-design-package-contract.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-06-30
Summary: Defines the Stage 1 service injection and collaboration table for the unified PAA operator CLI, including required injections, transitional collaborators, future redirection targets, and ownership rules for each CLI node.

# PAA CLI Service Injection And Collaboration Table

## Purpose

Define the Stage 1 service injection and collaboration structure for the unified `paa` operator CLI.

This note exists to answer the next practical design question after nodes, objects, and dependency edges are known:
- what must be injected into each CLI node?
- which collaborators are current governed services versus transitional module-backed owners?
- which collaborations are intentionally temporary until future runtime controllers exist?
- where must the CLI avoid absorbing behavior instead of delegating it?

## Design Rule

The CLI should inject stable collaborator surfaces instead of reaching directly into arbitrary modules from Typer callbacks.

That means:
- host-surface nodes should depend on explicit collaborators
- family adapters should depend on explicit command-owner collaborators
- transitional module-backed owners should be wrapped behind adapter-oriented interfaces as soon as practical
- future governed runtime controllers should replace temporary shell-backed collaborators without changing CLI-owned invocation and result semantics

## Injection Classification

This note uses four collaborator classes:

### `required_governed`
A collaborator that should be treated as a stable modeled owner and injected directly or through a stable interface.

### `required_host_support`
A collaborator owned by the CLI host surface itself and needed for any invocation.

### `transitional_module`
A current module-backed owner that the CLI may call through an adapter boundary for now, but which should not become permanent CLI business logic.

### `future_governed_target`
A planned component or controller that should replace a current transitional collaborator later.

## Host-Surface Injection Table

| target_node | injected_collaborator | collaborator_class | current_owner | purpose | replacement_rule |
|---|---|---|---|---|---|
| `PAAOperatorCLI` | `EnvironmentResolver` | required_host_support | CLI host surface | resolve repo root, config, runtime path, and env bindings | none |
| `PAAOperatorCLI` | `CommandRouter` | required_host_support | CLI host surface | select command-family adapter for the invocation | none |
| `PAAOperatorCLI` | `CommandResultNormalizer` | required_host_support | CLI host surface | normalize execution results into stable `OperatorCommandResult` objects | none |
| `PAAOperatorCLI` | `OutputRenderer` | required_host_support | CLI host surface | render normalized results as JSON, table, or summary output | none |
| `PAAOperatorCLI` | `StructuredLogger` | required_governed | shared adapter / logging surface | emit structured operator diagnostics and failures | none |

## Command-Family Adapter Injection Table

| target_node | injected_collaborator | collaborator_class | current_owner | purpose | replacement_rule |
|---|---|---|---|---|---|
| `AuthorityCommandAdapter` | authority runtime adapter | transitional_module | producer module family | run current authority commands and authority-runtime operations | later promote to governed authority-tooling component family |
| `AuthorityCommandAdapter` | authority package install adapter | transitional_module | `authority_install.py` | install and inspect published authority packages from the CLI | later absorb into governed authority install component |
| `AuthorityCommandAdapter` | `StructuredLogger` | required_governed | shared adapter / logging surface | emit command diagnostics | none |
| `DeriveCommandAdapter` | implementation-plan derivation adapter | required_governed | `ImplementationPlanDerivationService` | derive implementation plans through a governed service boundary | none |
| `DeriveCommandAdapter` | design-package derivation adapter | transitional_module | `design_package_deriver.py` | drive current Stage 1 design-package derivation | later promote to governed design-package derivation component |
| `DeriveCommandAdapter` | coder-brief assembly adapter | transitional_module | `coder_brief_assembler.py`, `brief_target_author.py`, `brief_reviewer.py` | drive current coder-brief and target derivation flows | later promote to governed coder-brief component family |
| `DeriveCommandAdapter` | architect-packet preparation adapter | transitional_module | `architect_packet_preparer.py` | prepare architect packet outputs from the CLI | later promote to governed architect-packet preparation component |
| `DeriveCommandAdapter` | `StructuredLogger` | required_governed | shared adapter / logging surface | emit derivation diagnostics | none |
| `PlanCommandAdapter` | progress service adapter | required_governed | `ImplementationPlanProgressService` | provide progress, reconciliation, and next-slice operations | none |
| `PlanCommandAdapter` | `StructuredLogger` | required_governed | shared adapter / logging surface | emit planning diagnostics | none |
| `WorkerCommandAdapter` | TechLead worker adapter | transitional_module | consumer module family, currently `techlead.py` | expose current worker-oriented TechLead command surfaces | replace with `TechLeadWorkerService` when realized |
| `WorkerCommandAdapter` | Dev worker adapter | future_governed_target | future `DevWorkerService` | expose bounded Dev worker runtime commands | initially absent; add when controller exists |
| `WorkerCommandAdapter` | QA worker adapter | future_governed_target | future `QAWorkerService` | expose bounded QA worker runtime commands | initially absent; add when controller exists |
| `WorkerCommandAdapter` | `WorkflowLifecycleService` | required_governed | governed core service | support workflow-aware inspection or dry-run logic where needed | none |
| `WorkerCommandAdapter` | `StructuredLogger` | required_governed | shared adapter / logging surface | emit worker diagnostics | none |
| `QueueCommandAdapter` | queue runtime adapter | transitional_module | consumer module family, currently `inbox.py` and runtime helpers | expose claim, ack, validate, send, and inspect queue operations | replace with `QueuePacketRuntimeController` when realized |
| `QueueCommandAdapter` | queue runtime controller adapter | future_governed_target | future `QueuePacketRuntimeController` | provide governed queue and packet operations | initially absent; add when controller exists |
| `QueueCommandAdapter` | `StructuredLogger` | required_governed | shared adapter / logging surface | emit queue diagnostics | none |
| `VerificationCommandAdapter` | runtime guardrails adapter | transitional_module | `runtime_guardrails.py` | drive current runtime validation and preflight flows | later promote to governed runtime-guardrails component |
| `VerificationCommandAdapter` | governance proof adapter | transitional_module | governance scripts under `scripts/governance/` | run current model/code and spec/model proof commands | later promote to governed verification subsystem |
| `VerificationCommandAdapter` | TechLead decision-service adapter set | required_governed | TechLead decision-service family | support governed decision diagnostics where verification needs them | none |
| `VerificationCommandAdapter` | `StructuredLogger` | required_governed | shared adapter / logging surface | emit verification diagnostics | none |
| `AcceptanceCommandAdapter` | acceptance and closeout adapter | transitional_module | consumer module family, currently `techlead.py` | drive current acceptance and merge orchestration commands | later redirect to governed runtime controller and acceptance subsystem |
| `AcceptanceCommandAdapter` | TechLead acceptance and closeout service adapter set | required_governed | TechLead decision-service family | align CLI acceptance paths to governed acceptance and closeout semantics | none |
| `AcceptanceCommandAdapter` | `WorkflowLifecycleService` | required_governed | governed core service | support lifecycle-aware acceptance checks when needed | none |
| `AcceptanceCommandAdapter` | `StructuredLogger` | required_governed | shared adapter / logging surface | emit acceptance diagnostics | none |
| `ReportingCommandAdapter` | reporting projection adapter | required_governed | governed repositories and reporting read models | read durable truth for plan, workflow, and runtime reporting | later narrow to explicit reporting components if introduced |
| `ReportingCommandAdapter` | techlead service-map adapter | transitional_module | `techlead_service_map.py` | expose service ownership and runtime map reporting | later absorb into governed reporting subsystem |
| `ReportingCommandAdapter` | progress service adapter | required_governed | `ImplementationPlanProgressService` | expose realization and progress reporting views | none |
| `ReportingCommandAdapter` | `StructuredLogger` | required_governed | shared adapter / logging surface | emit reporting diagnostics | none |
| `OpsCommandAdapter` | runtime guardrails adapter | transitional_module | `runtime_guardrails.py` | run preflight, runtime validation, and diagnostics | later promote to governed ops/runtime guardrails component |
| `OpsCommandAdapter` | authority ops adapter | transitional_module | producer module family and runtime helper scripts | run install/update/bootstrap helper flows | later absorb into governed ops subsystem |
| `OpsCommandAdapter` | `ExecutionPackageResolutionService` | required_governed | governed core service | support install or execution-context diagnostics where needed | none |
| `OpsCommandAdapter` | `StructuredLogger` | required_governed | shared adapter / logging surface | emit ops diagnostics | none |

## Collaboration And Ownership Rules

### Rule 1. Typer callbacks do not own business logic
Typer command functions should collaborate with:
- `CommandRouter`
- a selected command-family adapter
- `CommandResultNormalizer`
- `OutputRenderer`

They should not directly own:
- queue logic
- derivation logic
- workflow logic
- acceptance logic
- reporting logic

### Rule 2. Governed services are preferred over modules
If a governed service already exists for a capability, the CLI should inject that service or a stable adapter over it rather than routing around it through older shell modules.

Important current examples:
- `ImplementationPlanProgressService`
- `ImplementationPlanDerivationService`
- `WorkflowLifecycleService`
- the `TechLead` decision-service family
- `ExecutionPackageResolutionService`

### Rule 3. Transitional modules must stay behind adapters
Current producer and consumer modules may still be used.
But they should appear to the CLI as injected collaborators, not as freeform callback-local imports with ad hoc result handling.

### Rule 4. Future runtime controllers should be drop-in collaborator replacements
The design goal is that:
- `WorkerCommandAdapter`
- `QueueCommandAdapter`
- parts of `AcceptanceCommandAdapter`

can later swap from transitional module-backed collaborators to governed runtime controllers without changing:
- `OperatorCommandRequest`
- `OperatorCommandResult`
- command-family identity
- CLI render behavior

## Transitional Collaboration Map

| current_transitional_collaborator | current_used_by | long_term_target |
|---|---|---|
| producer authority and derivation modules | `AuthorityCommandAdapter`, `DeriveCommandAdapter`, `OpsCommandAdapter` | governed authority-tooling, derivation, and ops component families |
| `inbox.py` and queue runtime helpers | `QueueCommandAdapter` | `QueuePacketRuntimeController` |
| `techlead.py` shell command surfaces | `WorkerCommandAdapter`, `AcceptanceCommandAdapter` | `TechLeadWorkerService` plus governed acceptance/runtime controllers |
| `runtime_guardrails.py` | `VerificationCommandAdapter`, `OpsCommandAdapter` | governed runtime-guardrails / verification subsystem |
| `techlead_service_map.py` | `ReportingCommandAdapter` | governed reporting subsystem |
| governance scripts under `scripts/governance/` | `VerificationCommandAdapter` | governed verification subsystem |

## Required Host-Support Collaborators

The CLI host itself must treat these as stable internal support collaborators:
- `EnvironmentResolver`
- `CommandRouter`
- `CommandResultNormalizer`
- `OutputRenderer`

These should be explicitly modeled and injected or composed as first-class host-surface collaborators rather than implicitly recreated across command handlers.

## Collaboration Readiness Reading

### Strongest current collaborator path
The strongest current first-slice collaborator path is:
- `PlanCommandAdapter -> ImplementationPlanProgressService`
- `DeriveCommandAdapter -> ImplementationPlanDerivationService`

Reason:
- those already have governed service ownership and stable model-backed semantics

### Medium-strength current collaborator path
These are workable but still partly transitional:
- `AuthorityCommandAdapter`
- `ReportingCommandAdapter`
- `VerificationCommandAdapter`
- `OpsCommandAdapter`

Reason:
- they have meaningful current behavior, but some of that behavior still sits in modules or scripts rather than first-class governed component families

### Weakest current collaborator path
These should not be the first implementation focus for the unified CLI:
- `WorkerCommandAdapter`
- `QueueCommandAdapter`
- `AcceptanceCommandAdapter`

Reason:
- they still depend more heavily on transitional runtime shell behavior and future worker/controller design

## Immediate Design Consequences

This collaboration table implies:
1. the CLI implementation should begin with the host support collaborators and the strongest governed command-family adapters first
2. the revised `PAAOperatorCLI` component spec should explicitly reference these injected collaborators rather than broad prose-only collaborator lists
3. later componentization work should target the transitional collaborator families so the CLI can stop depending on scripts and shell modules over time

## Non-Goals

This note does not yet define:
- the final Python module path for every adapter interface
- the final dependency-injection framework choice
- every concrete method signature
- the full runtime worker collaboration tables for `TechLeadWorkerService`, `DevWorkerService`, or `QAWorkerService`

It only defines the Stage 1 collaboration and service-injection structure required to keep the CLI design disciplined.
