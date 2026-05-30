Title: PAA CLI Object Model
Doc-ID: paa-cli-object-model
Doc-Type: design-note
Status: active
Lifecycle-Stage: design
Created: 2026-05-30
Last-Edited: 2026-05-30
Author: Billy Weisberg
Repo: paa-platform
Component: PAAOperatorCLI
Domain: operator-cli
Keywords: paa, cli, object-model, typer, operator, business-objects, command, output, environment
Depends-On: 2026-05-28-paa-cli-system-architecture.md, 2026-05-30-paa-cli-node-diagram.md, 2026-05-30-paa-modeled-ownership-inventory.md, 2026-05-13-paa-domain-object-model-and-oo-component-decomposition.md, 2026-05-03-stage1-design-package-contract.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-06-30
Summary: Defines the Stage 1 business-object model for the unified PAA operator CLI, including CLI-owned invocation, rendering, environment, and bridge objects and the ownership boundaries between them and downstream modeled services.

# PAA CLI Object Model

## Purpose

Define the Stage 1 business-object model for the unified `paa` operator CLI.

This note exists because the CLI must not be designed only as:
- command names
- Typer callbacks
- file-level wrappers around existing modules

Before component specs and implementation slices are finalized, the Authority Architect must define the CLI object model that explains:
- what objects the CLI actually owns
- what objects it only normalizes or transports
- what objects belong to downstream modeled owners instead
- where object boundaries should prevent the CLI from becoming a new hybrid hub

## Relationship To Existing PAA Object Model

This note is a CLI-specific specialization of:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-domain-object-model-and-oo-component-decomposition.md`

The general PAA object model already defines durable system objects such as:
- `Project`
- `WorkItem`
- `Workflow`
- `QueueClaim`
- `HandoffPacket`
- `AutomationRun`
- `InstalledExecutionPackage`
- `ImplementationPlan`

The CLI object model must not redefine those.

Instead, it must define the operator-facing host-surface objects that:
- select commands
- normalize invocation context
- shape output
- bridge into existing producer, consumer, and core modeled owners

## Object Modeling Rule

The CLI owns host-surface and invocation-shaping objects.

It does not own:
- workflow truth
- implementation-plan truth
- queue claim truth
- handoff packet truth
- acceptance truth
- repository persistence truth

The CLI may:
- reference those objects
- request operations over those objects
- render summaries of those objects
- normalize user input into command-specific request objects

But it must not become their hidden owner.

## Part 1. CLI-Owned Core Objects

## 1. `OperatorCommandFamily`

### Meaning
A top-level lifecycle-oriented command namespace in the unified `paa` CLI.

### Examples
- `authority`
- `derive`
- `plan`
- `worker`
- `queue`
- `verify`
- `accept`
- `report`
- `ops`

### Owns
- family identity
- family display name
- family description
- family command registration set
- family default output expectations

### Important rule
This object is a CLI-owned classification object.
It is not a downstream service.

## 2. `OperatorCommandRegistration`

### Meaning
One registered operator command or subcommand that can be invoked through the CLI.

### Owns
- command family binding
- command name
- optional subcommand name
- alias set
- help summary
- argument schema reference
- target adapter identity
- output mode support

### Important rule
Registration is host-surface truth.
It determines discoverability and routing, not business behavior.

## 3. `OperatorCommand`

### Meaning
The normalized identity of one requested operator action.

### Owns
- family
- command name
- optional subcommand name
- canonical display label
- target execution mode

### Important rule
This object identifies what the operator is trying to do before argument normalization and before dispatch.

## 4. `OperatorInvocationContext`

### Meaning
The per-invocation context bundle that describes where and how the current CLI command is running.

### Owns
- repo root
- current working directory
- environment variables relevant to the invocation
- output mode request
- dry-run and strict-mode flags
- current timestamp / clock context
- optional project or consumer context override

### Important rule
This is host execution context, not domain truth.

## 5. `OperatorCommandRequest`

### Meaning
A normalized structured request created by the CLI from argv, environment, and command registration.

### Owns
- `OperatorCommand`
- argument map
- option map
- `OperatorInvocationContext`
- optional operator metadata

### Important rule
This is the central CLI-owned request object.
Downstream adapters should consume this rather than raw argv lists.

## 6. `OperatorCommandResult`

### Meaning
The normalized structured result returned to the CLI host after one command execution attempt.

### Owns
- command echo identity
- success / blocked / unsupported / failed outcome state
- human summary
- structured payload
- renderable sections and rows
- warnings
- blocking reasons
- exit-code hint

### Important rule
This is the central CLI-owned response object.
It separates execution meaning from print behavior.

## 7. `OperatorFailure`

### Meaning
A normalized failure or blocking result produced by the CLI or one command adapter.

### Owns
- failure class
- reason code
- summary
- blocking scope
- remediation hint
- optional source exception metadata

### Important rule
This object prevents raw module or script exceptions from becoming the operator interface.

## Part 2. CLI-Owned Rendering And Presentation Objects

## 8. `OperatorOutputMode`

### Meaning
The requested rendering format for command output.

### Examples
- `json`
- `table`
- `summary`

### Owns
- mode identity
- formatting expectations
- machine-readability requirements

## 9. `OutputSection`

### Meaning
A structured display section in a rendered operator response.

### Owns
- section title
- section order
- section body or rows
- optional severity or emphasis level

## 10. `OutputTable`

### Meaning
A tabular display payload suitable for rendering in terminal or export-friendly modes.

### Owns
- column definitions
- rows
- ordering rules
- optional footnotes

## 11. `OutputMessage`

### Meaning
A single rendered message item intended for summary or narrative output.

### Owns
- text
- severity
- source role
- ordering index

## Important rendering rule
Rendering objects are CLI-owned presentation objects.
They must not become substitutes for the structured payload itself.

## Part 3. CLI-Owned Environment And Resolution Objects

## 12. `EnvironmentBinding`

### Meaning
A normalized binding between one operator invocation and the environment or configuration values needed to execute it.

### Owns
- env key name
- resolved value
- source of value
- required or optional classification
- missing-state reason

## 13. `RepoContext`

### Meaning
A normalized view of the current repo-relative execution context.

### Owns
- repo root path
- package roots
- docs root
- runtime script roots
- optional installed package paths

## 14. `CommandCapability`

### Meaning
A classification object that records what a given registered command is allowed or expected to do.

### Examples
- read authority only
- mutate model truth
- mutate queue state
- invoke worker runtime
- render diagnostics only

### Important rule
This object should later help with dry-run gating and risk surfacing.

## Part 4. Bridge Objects To Downstream Modeled Owners

These objects are not the primary truth objects for downstream systems.
They are bridge objects used by the CLI to pass normalized requests into downstream owners.

## 15. `AuthorityOperationRequest`

### Meaning
A normalized CLI bridge request for one authority-family operation.

### Typical downstream owners
- authority runtime
- docs tooling
- authority publication helpers

## 16. `DerivationOperationRequest`

### Meaning
A normalized CLI bridge request for one derivation-family operation.

### Typical downstream owners
- design package derivation
- implementation-plan derivation
- coder brief assembly
- architect packet preparation

## 17. `PlanningOperationRequest`

### Meaning
A normalized CLI bridge request for plan-family operations.

### Typical downstream owners
- `ImplementationPlanProgressService`
- plan reconciliation and next-slice derivation surfaces

## 18. `WorkerOperationRequest`

### Meaning
A normalized CLI bridge request for one worker-family operation.

### Typical downstream owners
- current `techlead.py` transitional shell
- future `TechLeadWorkerService`
- future `DevWorkerService`
- future `QAWorkerService`

## 19. `QueueOperationRequest`

### Meaning
A normalized CLI bridge request for one queue-family operation.

### Typical downstream owners
- current `inbox.py`
- future queue/packet runtime controller component family

## 20. `VerificationOperationRequest`

### Meaning
A normalized CLI bridge request for one verification-family operation.

### Typical downstream owners
- runtime guardrails
- governance proof scripts or future verification subsystem services

## 21. `AcceptanceOperationRequest`

### Meaning
A normalized CLI bridge request for one acceptance-family operation.

### Typical downstream owners
- transitional `techlead.py` acceptance shell
- current TechLead acceptance and closeout decision services
- future acceptance runtime controllers

## 22. `ReportingOperationRequest`

### Meaning
A normalized CLI bridge request for one reporting-family operation.

### Typical downstream owners
- `techlead_service_map.py`
- implementation-plan progress projections
- repository-backed reporting surfaces

## 23. `OpsOperationRequest`

### Meaning
A normalized CLI bridge request for one operations or admin-family operation.

### Typical downstream owners
- runtime guardrails
- bootstrap scripts
- authority runtime operational helpers

## Part 5. Downstream Objects The CLI Depends On But Does Not Own

The CLI design depends on these downstream object families but must not redefine or absorb them:

### Planning and derivation objects
- `ImplementationPlan`
- `ImplementationPlanActivity`
- `ImplementationPlanVerificationSurface`
- `DerivedImplementationPlanResult`
- `MaterializedComponentSpecResult`
- `AssembledCoderBriefResult`

### Workflow and runtime objects
- `Workflow`
- `WorkflowTransition`
- `QueueClaim`
- `HandoffPacket`
- `HandoffRecord`
- `AutomationRun`
- `AcceptanceEvent`

### Installed-authority and execution-package objects
- `InstalledExecutionPackage`
- `PublishedExecutionPackage`
- `ExecutionOverlay`

### TechLead decision objects
- request/result objects belonging to the `TechLead*DecisionService` family

Important rule:
The CLI may render or relay these objects.
It should not flatten them into untyped dicts as its primary interface.

## Part 6. Ownership Boundaries

## CLI-owned objects
The CLI should directly own:
- `OperatorCommandFamily`
- `OperatorCommandRegistration`
- `OperatorCommand`
- `OperatorInvocationContext`
- `OperatorCommandRequest`
- `OperatorCommandResult`
- `OperatorFailure`
- `OperatorOutputMode`
- `OutputSection`
- `OutputTable`
- `OutputMessage`
- `EnvironmentBinding`
- `RepoContext`
- `CommandCapability`
- all operation request bridge objects

## Downstream-owned objects
The CLI should not own:
- implementation-plan entities
- workflow entities
- queue claim entities
- handoff packet entities
- acceptance entities
- installed execution-package entities
- domain-service result objects already governed elsewhere

## Transitional caution
Several current command families still terminate in modules or scripts rather than governed components.
During that transition, the CLI should still preserve the ownership split by using bridge objects instead of allowing module return values to become its permanent public interface.

## Part 7. Object Relationships

### Command and registration relationships
- one `OperatorCommandFamily` has many `OperatorCommandRegistration` objects
- one `OperatorCommandRegistration` resolves to one canonical `OperatorCommand`
- one `OperatorCommand` is executed in one `OperatorInvocationContext`

### Invocation relationships
- one `OperatorCommandRequest` contains one `OperatorCommand`
- one `OperatorCommandRequest` contains one `OperatorInvocationContext`
- one `OperatorCommandRequest` yields one `OperatorCommandResult`
- one `OperatorCommandResult` may include zero or more `OperatorFailure`, `OutputSection`, `OutputTable`, or `OutputMessage` objects

### Bridge relationships
- one `OperatorCommandRequest` is translated into one operation request bridge object for the selected command family
- that operation request is then passed to a current modeled owner or future governed component

## Design Consequences

This object model implies:
1. the CLI component spec should be revised to align its DTOs and collaborators with these objects
2. the next design artifact should define the CLI service injection and collaboration table
3. the dependency graph slice should distinguish between:
   - CLI-owned host objects
   - bridge objects
   - downstream truth-owning objects

## Non-Goals

This note does not yet define:
- the final package/module layout for every object
- persistence schemas for CLI-owned objects
- every future flag name or argument type
- worker-runtime object models in full detail

It only defines the Stage 1 object model needed to keep the CLI design governed and decomposed correctly.
