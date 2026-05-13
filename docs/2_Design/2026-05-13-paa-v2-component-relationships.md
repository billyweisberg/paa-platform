# PAA V2 Component Relationships

Date: 2026-05-13

## Purpose

Define the logical relationships between the PAA System Design V2 components more explicitly.

This note follows the glossary's System Design phase for:
- logical relationships between components
- dependency and ownership rules
- control-plane, data-plane, and event-plane semantics

It should be read as the relationship contract for:
- `docs/2_Design/2026-05-13-paa-system-component-diagram-v2.md`

## Related Notes

Read alongside:
- `docs/2_Design/2026-05-13-paa-db-primary-data-consolidation-audit.md`
- `docs/2_Design/2026-05-13-paa-schema-and-data-surface-audit.md`
- `docs/terminology/paa-engineering-terminology-glossary.md`
- `docs/2_Design/2026-05-13-paa-system-component-diagram-v2.md`
- `docs/2_Design/2026-05-13-paa-runtime-consolidation-design-correction.md`
- `docs/2_Design/2026-05-12-paa-handoff-execution-contract.md`
- `docs/2_Design/2026-05-09-paa-data-contracts.md`

## Relationship Types Used In This Note

### Control-plane relationship

A component decides, authorizes, orchestrates, or constrains another component's behavior.

### Data-plane relationship

A component provides or consumes durable or transient data required by another component.

### Event-plane relationship

A component publishes or consumes wakeup signals, transport packets, or lifecycle events.

## High-Level Relationship Rules

The V2 system is intentionally asymmetric.

Key asymmetries:
1. producer side publishes execution inputs but does not execute consumer runtime transitions
2. installed execution package supplies execution-time truth but does not own transitions
3. runtime lifecycle engine performs transitions but does not invent its own execution-time authority
4. workflow state machine owns current workflow truth but does not execute work
5. data access components provide structured access but do not own higher-level semantics
6. RabbitMQ carries wakeup and transport signals but does not own workflow truth
7. skills and automations invoke runtime entry points but do not own transactional semantics

## Relationship Matrix

| From | To | Plane | Relationship |
|---|---|---|---|
| Senior Architect / Authority Publisher | Producer Repo | Control | approves and frames publication inputs |
| Producer Repo | Authority Publication Pipeline | Control + Data | provides source materials and publication commands |
| Authority Publication Pipeline | Published Authority Artifacts | Data | compiles versioned execution inputs |
| Authority Publication Pipeline | PAA Postgres DB | Data | persists publication records and indexes |
| Published Authority Artifacts | Installed Execution Package | Data | materializes execution-time package content |
| Consumer Repo | Installed Execution Package | Data + Hosting | hosts installed execution package surface |
| Installed Execution Package | Runtime Lifecycle Engine | Data + Control Constraint | supplies execution-time truth and bounds legal runtime actions |
| Runtime Lifecycle Engine | Workflow State Repository | Data Access Request | reads/writes authoritative workflow-state records through a repository boundary |
| Runtime Lifecycle Engine | Execution Package Repository | Data Access Request | reads installed execution-time package content through a repository boundary |
| Runtime Lifecycle Engine | Component Design Repository | Data Access Request | reads stable component-design and slice-derivation records through a repository boundary |
| Runtime Lifecycle Engine | Runtime Event Repository | Data Access Request | reads and persists runtime transport/execution history through a repository boundary |
| Workflow State Machine | Workflow State Repository | Data Access Request | loads and persists authoritative workflow-state records through a repository boundary |
| Reporting And Traceability Projection | Projection Repository | Data Access Request | reads and writes reporting projections through a repository boundary |
| Reporting And Traceability Projection | Workflow State Repository | Data Access Request | reads authoritative workflow-state records for projection only |
| Reporting And Traceability Projection | Runtime Event Repository | Data Access Request | reads runtime event history for projection only |
| Component Design Repository | PAA Postgres DB | Data | reads and writes stable component-design and slice-derivation records |
| Workflow State Repository | PAA Postgres DB | Data | reads and writes workflow-state and workflow-transition records |
| Runtime Event Repository | PAA Postgres DB | Data | reads and writes handoff, queue, execution, and acceptance event records |
| Execution Package Repository | Repo-local Artifacts / Logs / Evidence | Data | reads installed execution-package artifacts and metadata |
| Projection Repository | PAA Postgres DB | Data | reads and writes projection views or materialized reporting records |
| Runtime Lifecycle Engine | Workflow State Machine | Control | requests legal workflow transitions |
| Workflow State Machine | PAA Postgres DB | Data | persists authoritative workflow state |
| PAA Postgres DB | Workflow State Machine | Data | reloads authoritative current state |
| Runtime Lifecycle Engine | Worktree Policy And Preparation | Control | requests worktree resolution and preparation |
| Worktree Policy And Preparation | Consumer Repo | Data + Hosting | creates and inspects repo-local execution surfaces |
| Runtime Lifecycle Engine | Reporting And Traceability Projection | Control | requests operator-visible projections |
| Reporting And Traceability Projection | PAA Postgres DB | Data | reads and writes traceability/reporting state |
| Reporting And Traceability Projection | Repo-local Artifacts / Logs / Evidence | Data | materializes reports and evidence |
| TechLead / Delivery Architect / Worker / QA Automations | Runtime Lifecycle Engine | Control | invoke approved runtime entry points |
| Installed Skills | Runtime Lifecycle Engine | Control Guidance | constrain how role flows are invoked |
| Automation UI Registration | Automations | Control Exposure | exposes launch surfaces only |
| Runtime Lifecycle Engine | RabbitMQ Transport | Event | sends wakeup and transport packets |
| RabbitMQ Transport | Runtime Lifecycle Engine | Event | delivers claimable packets and queue signals |
| Runtime Lifecycle Engine | GitHub Issues / PRs | Control + Data | validates state, comments, merges, closes |
| GitHub Issues / PRs | Runtime Lifecycle Engine | Data | supplies issue/PR/merge state |
| Runtime Lifecycle Engine | Repo-local Artifacts / Logs / Evidence | Data | writes execution evidence |


### Data access layer rule

Structured access to the PAA data model must pass through explicit Data Access Components.

That means higher-level components should not mix:
- raw SQL against unrelated tables
- direct installed-package file reads
- direct projection/report file interpretation

inside the same lifecycle path.

The Data Access Layer exists to separate:
- workflow-state access
- execution-package access
- component-design access
- runtime-event access
- projection access

so those concerns stop bleeding into each other.

## Explicit Logical Relationships

### 1. Senior Architect / Authority Publisher -> Producer Repo

**Plane**
- control-plane

**Meaning**
The publisher role decides what issue/slice/package content is eligible to become published authority input.

**Ownership rule**
The producer repo does not self-authorize publication intent.
It holds source materials and tooling only.

**Visibility rule**
Consumer runtime does not read intent directly from this relationship.
It only sees the downstream published package.

### 2. Producer Repo -> Authority Publication Pipeline

**Plane**
- control-plane
- data-plane

**Meaning**
The producer repo supplies:
- source documents
- publication helpers
- package/brief generation inputs

to the publication pipeline.

**Ownership rule**
The publication pipeline owns transformation into publishable artifacts.
The producer repo owns the source materials, not the installed execution package.

### 3. Authority Publication Pipeline -> Published Authority Artifacts

**Plane**
- data-plane

**Meaning**
This relationship creates the installable package inputs:
- manifest
- design package
- coder brief

**Ownership rule**
Once published, these artifacts are the only valid upstream inputs for consumer-side installed execution package materialization.

### 4. Authority Publication Pipeline -> PAA Postgres DB

**Plane**
- data-plane

**Meaning**
The pipeline persists publication records, indexes, and provenance.

**Non-ownership rule**
DB persistence here does not make the DB the consumer execution-time package source.
It makes the DB the publication record source.

### 5. Published Authority Artifacts -> Installed Execution Package

**Plane**
- data-plane

**Meaning**
Published artifacts are transformed into the installed execution package for a given consumer repo.

**Ownership rule**
The installed execution package is the consumer's sole execution-time package truth.

**Non-ownership rule**
Consumer runtime must not reconstruct equivalent package truth from DB copies when the installed package is present.

### 6. Consumer Repo -> Installed Execution Package

**Plane**
- data-plane
- hosting relationship

**Meaning**
The consumer repo hosts the installed execution package and the runtime environment that uses it.

**Ownership rule**
The consumer repo owns the environment and local installation surface.
It does not own publication-time package truth.

### 7. Installed Execution Package -> Runtime Lifecycle Engine

**Plane**
- data-plane
- control constraint

**Meaning**
The runtime lifecycle engine may only act within the package, brief, role-registry, and policy boundaries provided by the installed execution package.

**Ownership rule**
The runtime engine owns transitions.
The installed execution package owns the allowed execution context.

**Non-ownership rule**
The runtime engine may not invent authorization outside the installed package.

### 8. Runtime Lifecycle Engine -> Workflow State Machine

**Plane**
- control-plane

**Meaning**
The runtime lifecycle engine proposes transitions such as:
- assignment issued
- result returned
- QA verified
- closeout recorded

**Ownership rule**
The lifecycle engine does not directly redefine current workflow truth.
It must transition workflow truth through the workflow state machine.

### 9. Workflow State Machine <-> PAA Postgres DB

**Plane**
- data-plane

**Meaning**
The workflow state machine persists and reloads authoritative current state from DB-backed storage.

**Ownership rule**
The workflow state machine owns semantics.
The DB owns durability.

**Non-ownership rule**
The DB row set by itself is not the workflow engine.
It is the persistence substrate for the workflow state machine.

### 10. Runtime Lifecycle Engine -> Worktree Policy And Preparation

**Plane**
- control-plane

**Meaning**
The lifecycle engine requests deterministic execution surfaces for bounded work.

**Ownership rule**
The lifecycle engine owns when a worktree is needed.
The worktree component owns how canonical branch source, role branch, and repo-local worktree preparation are derived and enforced.

### 11. Worktree Policy And Preparation -> Consumer Repo

**Plane**
- data-plane
- hosting relationship

**Meaning**
Prepared worktrees live inside the consumer repo execution surface.

**Ownership rule**
The worktree component may create and inspect these surfaces.
It does not own the broader workflow stage or merge state.

### 12. Runtime Lifecycle Engine -> Reporting And Traceability Projection

**Plane**
- control-plane

**Meaning**
The lifecycle engine requests projections after meaningful transitions.

**Ownership rule**
The reporting component may project current state and history.
It does not define the underlying workflow truth.

### 13. Reporting And Traceability Projection -> DB / Repo-local Artifacts

**Plane**
- data-plane

**Meaning**
The reporting component reads authoritative runtime data and materializes:
- status summaries
- lineage views
- accepted-chain views
- human-readable reports

**Non-ownership rule**
A report artifact is not itself authoritative state.
It is a projection.

### 14. Automations / Installed Skills -> Runtime Lifecycle Engine

**Plane**
- control-plane

**Meaning**
Automations and skills invoke the runtime through approved entry points.

**Ownership rule**
Automations own scheduling and launch behavior.
Skills own role guidance.
The runtime owns transactional semantics.

**Non-ownership rule**
Neither automation prompt wording nor skill wording may redefine queue-closeout or workflow-transition semantics.

### 15. Runtime Lifecycle Engine <-> RabbitMQ Transport

**Plane**
- event-plane

**Meaning**
RabbitMQ delivers claimable packets and receives new packets emitted by runtime transitions.

**Ownership rule**
RabbitMQ owns transport mechanics.
The runtime owns interpretation and transition behavior.

**Non-ownership rule**
Queue residue is not allowed to redefine workflow truth.

### 16. Runtime Lifecycle Engine <-> GitHub Issues / PRs

**Plane**
- data-plane
- control-plane

**Meaning**
The lifecycle engine reads GitHub state to validate execution reality and may write comments, merge PRs, or close issues during approved transitions.

**Ownership rule**
GitHub owns durable engineering history.
The runtime owns internal workflow transitions.

**Non-ownership rule**
GitHub state alone must not act as the internal workflow-state machine.

### 17. Runtime Lifecycle Engine -> Repo-local Artifacts / Logs / Evidence

**Plane**
- data-plane

**Meaning**
The lifecycle engine writes artifacts and logs that support:
- operator review
- debugging
- evidence
- packet inspection

**Non-ownership rule**
These outputs are evidence surfaces, not primary workflow-state truth.

## Visibility Rules

### Components allowed to read installed execution package content
- Runtime Lifecycle Engine
- Reporting And Traceability Projection, if projecting execution-package-derived context
- approved inspection helpers

### Components allowed to mutate workflow truth
- Workflow State Machine only

### Components allowed to publish queue packets
- Runtime Lifecycle Engine only
- producer-side publication/runtime paths where explicitly authorized by design

### Components allowed to define worktree paths and role-branch policy
- Worktree Policy And Preparation only

### Components allowed to interpret queue state into workflow meaning
- Runtime Lifecycle Engine through Workflow State Machine semantics only

## Dependency Rules

### Hard dependencies

The following dependencies are required for the corrected model:
- Runtime Lifecycle Engine depends on Installed Execution Package
- Runtime Lifecycle Engine depends on Workflow State Machine
- Runtime Lifecycle Engine depends on Worktree Policy And Preparation
- Reporting And Traceability Projection depends on Workflow State Machine semantics
- Workflow State Machine depends on DB persistence

### Prohibited dependencies

The following dependency directions are prohibited in the corrected model:
- RabbitMQ Transport -> Workflow State Machine semantics
- Installed Skills -> direct workflow truth mutation
- Automation UI Registration -> runtime semantics
- Repo-local report artifacts -> current workflow-state definition
- GitHub -> internal workflow-state definition
- Consumer runtime -> competing DB reconstruction of installed package truth

## Design Conclusion

The V2 component diagram becomes much more explicit when read through these relationships:
- publication builds installable execution inputs
- installed execution inputs constrain runtime behavior
- runtime behavior transitions workflow state through a state machine
- projections, queue transport, GitHub, and repo-local artifacts all become supporting surfaces instead of competing sources of truth

That is the corrected logical relationship model for the PAA system.
