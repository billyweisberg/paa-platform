# PAA Volatility Analysis

Date: 2026-05-15

## Purpose

Identify the major axes of change that are likely to affect the PAA system over time, and define the architectural seams that should isolate those changes.

This note exists so we do not decompose the system only around today's implementation scripts or today's deployment shape.

The goal is to minimize future blast radius by making expected change explicit before we finalize the layered architecture and deeper component specs.

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-authority-package-authoring-process.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-system-decomposition-options.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-domain-object-model-and-oo-component-decomposition.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-system-component-diagram-v2.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-v2-component-relationships.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-data-access-layer-design.md`

## Definition

In this note, **volatility** means:
- an aspect of the system that is likely to change independently of other aspects
- with meaningful risk that the change could propagate unnecessary rewrites if not isolated

A good architecture does not pretend volatility does not exist.
It identifies it and contains it.

## Analysis Method

For each volatility axis, this note answers:
1. what may change?
2. why is it likely to change?
3. what should remain stable?
4. what blast radius do we want to avoid?
5. what architectural seam should isolate the change?

## Volatility Axis 1. Persistence Backend

### What may change
- Postgres today
- SQL Server later
- MySQL or MariaDB in some deployment
- document or multi-model store for selected projection workloads later
- managed cloud database variants

### Why it is likely to change
- customer or deployment constraints
- enterprise stack standardization
- cloud-specific managed-service preferences
- operational scaling decisions

### What should remain stable
- domain object model
- repository contracts
- workflow semantics
- brief and package semantics
- projection meaning

### Blast radius to avoid
We should not need to rewrite:
- domain logic
- orchestration services
- component specs
- coder brief derivation

just because the persistence engine changes.

### Required seam
- repository interfaces
- transaction boundary abstraction
- query/projection boundary isolation
- schema migration/version strategy

### Architectural implication
The DAL is not optional.
It is one of the primary volatility-isolation layers.

## Volatility Axis 2. Message Transport

### What may change
- RabbitMQ today
- AWS SQS later
- Azure Service Bus later
- in-process event bus for local/dev use
- other message brokers later

### Why it is likely to change
- deployment platform choices
- operational maturity differences across environments
- cloud vendor alignment
- simpler local-dev mode requirements

### What should remain stable
- handoff packet semantics
- workflow transition semantics
- queue-claim meaning
- runtime orchestration rules
- role routing and acceptance policy

### Blast radius to avoid
We should not need to rewrite:
- TechLead logic
- role-return logic
- workflow lifecycle logic
- verification flow

because the transport changes.

### Required seam
- `MessageBus` port
- transport adapter implementations
- envelope serialization boundary
- transport-specific claim/ack adapter logic

### Architectural implication
Transport must be treated as event-plane infrastructure, not as workflow truth.

## Volatility Axis 3. Execution Surface And File / Share Model

### What may change
- local filesystem today
- repo-local worktrees today
- EFS in EKS later
- Azure Files in AKS later
- Docker volumes in Compose or Desktop
- possibly remote ephemeral workspaces later

### Why it is likely to change
- deployment topology changes
- scale-out execution
- shared workspace requirements
- containerized role execution

### What should remain stable
- execution package semantics
- worktree policy meaning
- branch ownership rules
- artifact identity and evidence semantics

### Blast radius to avoid
We should not need to rewrite:
- workflow logic
- brief targeting
- package-resolution logic
- verification semantics

because the filesystem or shared storage changes.

### Required seam
- `ExecutionSurfaceProvider`
- artifact store abstraction
- worktree-preparation abstraction
- runtime path-resolution abstraction

### Architectural implication
File layout is a deployment concern plus runtime input concern, not a core domain concern.

## Volatility Axis 4. Runtime Hosting Model

### What may change
- CLI + in-process runtime today
- background worker processes later
- FastAPI host later
- per-role service processes later
- containerized role runtimes in Kubernetes later
- hybrid producer/consumer self-hosted repo mode

### Why it is likely to change
- growth in automation maturity
- need for remote or unattended execution
- operator UI/API needs
- cloud or enterprise hosting expectations

### What should remain stable
- domain services
- workflow semantics
- package semantics
- repository contracts
- policy objects

### Blast radius to avoid
We should not need to rewrite core business logic when moving from:
- CLI to API
- in-process to background workers
- monolithic host to split services

### Required seam
- application service layer
- host surface abstraction
- dependency injection / composition root discipline
- infrastructure ports that do not assume CLI-only invocation

### Architectural implication
The host surface must remain thin.
Business logic should not live in CLI handlers.

## Volatility Axis 5. Role Execution Topology

### What may change
- all roles run in one process today
- TechLead in one container, QA in another later
- separate pod per role in Kubernetes
- long-lived worker services versus one-shot automation runs
- multi-tenant role runners later

### Why it is likely to change
- scaling needs
- reliability isolation
- deployment and security requirements
- independent role lifecycle management

### What should remain stable
- role contract semantics
- assignment and return semantics
- workflow lifecycle semantics
- verification and acceptance rules

### Blast radius to avoid
We should not need to redesign the whole system if role runtimes move into separate processes or containers.

### Required seam
- role orchestration service boundaries
- message bus abstraction
- idempotent application service contracts
- durable workflow and claim state

### Architectural implication
PAA should assume role runtimes may become independently hosted.
The architecture should not require shared in-memory state.

## Volatility Axis 6. Authority Package Shape And Versioning

### What may change
- package schema versions
- package contents
- overlay model
- producer-side derivation rules
- project-specific authority conventions

### Why it is likely to change
- maturing producer-side tooling
- self-hosting PAA use cases
- project-specific specialization
- package format evolution over time

### What should remain stable
- installed execution package as execution-time truth
- publication/install distinction
- authority package identity and versioning discipline

### Blast radius to avoid
We should not need to rewrite:
- runtime lifecycle semantics
- repository contracts
- workflow logic

for routine package-format evolution.

### Required seam
- execution package repository
- package schema version boundary
- package publication pipeline
- overlay resolution service

### Architectural implication
Package versioning must be explicit and insulated from unrelated runtime logic.

## Volatility Axis 7. Policy And Decision Rules

### What may change
- routing rules
- acceptance rules
- QA gates
- reset/supersede/closed semantics
- unattended-safe policy
- escalation thresholds

### Why it is likely to change
- process refinement
- project-specific policy needs
- lessons from real automation runs
- maturity of agent trust and verification

### What should remain stable
- core domain objects
- repository contracts
- packet vocabulary at the conceptual level
- transition history model

### Blast radius to avoid
We should not need to rewrite persistence layers or host surfaces when policy changes.

### Required seam
- `TransitionPolicy`
- `RoutingPolicy`
- `AcceptancePolicy`
- `RecoveryPolicy`
- policy selection/configuration layer

### Architectural implication
Policy should be isolated from both storage and host surfaces.

## Volatility Axis 8. Projection And Reporting Needs

### What may change
- top-level status views
- dashboards
- traceability formats
- operational health reporting
- exported report shapes
- human-readable summary expectations

### Why it is likely to change
- operator feedback
- UI introduction
- audit/reporting needs
- project-specific monitoring expectations

### What should remain stable
- primary truth records
- domain semantics
- authoritative workflow and event models

### Blast radius to avoid
We should not need to change workflow truth or runtime event semantics because a dashboard changes.

### Required seam
- projection repository
- projection services
- read-model generation boundary
- export layer

### Architectural implication
Projection is a volatile read concern and must remain downstream from primary truth.

## Volatility Axis 9. SCM / Collaboration Provider

### What may change
- GitHub today
- possibly other SCM or review systems later
- partial offline or mirrored modes

### Why it is likely to change
- enterprise adoption constraints
- future ecosystem changes
- hybrid deployment needs

### What should remain stable
- work-item semantics
- acceptance semantics
- workflow semantics
- comment / merge / close conceptual operations

### Blast radius to avoid
We should not need to rewrite workflow logic because the collaboration provider changes.

### Required seam
- `GitProvider` or collaboration provider abstraction
- work-item synchronization boundary
- merge/closeout adapter boundary

### Architectural implication
GitHub is important, but it should be an adapter-facing external system, not a core domain owner.

## Volatility Axis 10. Producer-Side Authoring Tooling

### What may change
- manual note authoring today
- structured authoring services later
- producer UI later
- guided decomposition and catalog tooling later

### Why it is likely to change
- we are actively discovering the process now
- this is one of the main future value areas of PAA
- authoring must become toolable to scale

### What should remain stable
- authority authoring process phases
- core decomposition and modeling concepts
- component and brief vocabulary
- publication/install contract

### Blast radius to avoid
We should not need to redesign the core system just because producer tooling becomes richer or more interactive.

### Required seam
- producer-side application services
- authoring registries
- domain-object and component catalog services
- policy-driven brief derivation services

### Architectural implication
Producer tooling should be designed as a first-class future subsystem, not an afterthought.

## Volatility Axis 11. Agent Execution Model

### What may change
- simple automations today
- richer agent runtimes later
- independent tool-using agents in separate containers later
- human-supervised plus autonomous mixed modes

### Why it is likely to change
- agent platform evolution
- reliability and observability needs
- deployment and security isolation

### What should remain stable
- brief semantics
- brief target sequencing
- code artifact target vocabulary
- role result semantics
- verification requirements

### Blast radius to avoid
We should not need to rebuild the producer-side authority model when the agent runtime becomes more capable.

### Required seam
- brief and target model
- agent-facing assignment contract
- execution outcome contract
- role orchestration boundary

### Architectural implication
The agent runtime is not the domain model.
It consumes the authority model.

## Volatility Classification Summary

| Axis | Expected Volatility | Desired Isolation Strength | Primary Seam |
|---|---|---|---|
| Persistence backend | high | strong | repositories + transactions |
| Message transport | high | strong | message bus abstraction |
| Execution surface / files | high | strong | execution surface + artifact store |
| Runtime hosting model | high | strong | application services + hosts |
| Role execution topology | high | strong | orchestration service boundaries |
| Authority package shape | medium-high | strong | package resolution / publication boundary |
| Policy / decision rules | high | strong | policy layer |
| Projection / reporting | high | strong | projection services |
| SCM / collaboration provider | medium | moderate-strong | Git provider |
| Producer-side tooling | high | strong | authoring services |
| Agent execution model | high | strong | brief / target contract |

## Stability Backbone

The following areas should be treated as the most stable backbone of the system:
- domain object model
- work item / workflow semantics
- execution package concept
- coder brief / brief target concept
- component / component element / code artifact target model
- primary-truth boundaries

These should change more slowly than:
- storage adapters
- message bus adapters
- host surfaces
- transport mechanisms
- operator reporting

## Architectural Consequences

This analysis supports the following architectural consequences:

1. PAA should use a layered architecture, not a script-centered architecture.
2. Domain services should not depend directly on transport, host, or file-layout details.
3. Repositories and infrastructure adapters are required because volatility is real, not hypothetical.
4. Policy should be isolated because it is expected to evolve rapidly.
5. Producer-side authoring services should be treated as first-class future components.
6. Agent-facing brief targets are a long-term stable abstraction and should be invested in early.

## Producer-Side Tooling Implications

The volatility analysis strengthens the case for producer-side tooling that can explicitly author or annotate:
- decomposition choices
- domain objects
- component catalogs
- component elements
- code artifact targets
- volatility characteristics
- deployment capabilities
- policy selections
- brief target sequencing

This is especially important because the producer side is where volatility decisions should be captured before they become runtime accidents.

## Next Note Suggested By This One

This note should be followed by:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-deployment-variants-and-swappable-boundaries.md`

Then by:
- a layered architecture proposal that synthesizes:
  - decomposition options
  - domain object model
  - volatility analysis
  - deployment variant analysis

## Design Conclusion

The future PAA architecture should not be optimized for the current local script topology.

It should be optimized to preserve a stable domain backbone while isolating the effects of change in:
- storage
- transport
- hosting
- execution topology
- policy
- reporting
- producer-side tooling

That is the architectural value of volatility-based decomposition in this system.
