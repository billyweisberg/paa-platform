# PAA Deployment Variants And Swappable Boundaries

Date: 2026-05-15

## Purpose

Document the major deployment variants PAA should be able to support over time, and identify the component boundaries that must remain swappable or composable across those variants.

This note exists to ensure the system design is not accidentally optimized only for the current local CLI/runtime mode.

It should help us answer:
- where can this system run?
- what parts may need to move out of process?
- what parts must remain topology-neutral?
- what boundaries should be adapter-based from the beginning?

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-authority-package-authoring-process.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-system-decomposition-options.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-volatility-analysis.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-domain-object-model-and-oo-component-decomposition.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-system-component-diagram-v2.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-v2-component-relationships.md`

## Core Design Goal

PAA should preserve a stable semantic core across multiple deployment variants.

That means the following should remain stable regardless of deployment shape:
- domain object model
- workflow semantics
- execution package semantics
- coder brief and brief target semantics
- repository contracts
- policy semantics

The following should be allowed to vary by deployment:
- host surface
- process topology
- message transport
- storage backend
- file/share backend
- operator UI and API exposure

## Analysis Method

For each deployment variant, this note records:
1. what the runtime topology looks like
2. why that variant matters
3. what is likely to change relative to the current mode
4. what boundaries must remain swappable or composable
5. what architecture rules follow from that variant

## Variant 1. Local Laptop CLI

### Topology
- producer and/or consumer repo on a laptop
- local Python environment
- CLI commands run directly by a human or local automation host
- local filesystem and repo-local worktrees
- local or nearby Postgres and RabbitMQ

### Why it matters
This is the current working mode and the minimum viable deployment shape.

### What changes relative to others
- most things are in process
- local paths and local worktrees are cheap
- operator interaction is direct

### Swappable boundaries still required
- repositories
- message bus adapter
- execution surface provider
- Git provider
- artifact store

### Architecture rules
- local mode must not hardcode away future separability
- CLI is a host surface, not the core architecture
- repo-local files may exist, but primary truth must still remain conceptually clean

## Variant 2. Docker Compose Deployment

### Topology
- producer and/or consumer runtime services in containers
- Postgres and transport in companion containers
- shared bind mount or named volume for repo/execution artifacts
- one machine, multiple containers

### Why it matters
This is a natural team-dev and small deployment mode.

### What changes relative to local CLI
- processes are split into containers
- local path assumptions become container-path assumptions
- startup and composition become service concerns

### Swappable boundaries required
- host/runtime surface separation
- execution surface provider
- artifact store abstraction
- transport adapter
- configuration provider

### Architecture rules
- service composition should not assume a single process
- repo/execution path logic must be injectable or configurable
- runtime services should be able to run headless

## Variant 3. Docker Desktop On Laptop

### Topology
- similar to Compose, but optimized for local developer workstation workflows
- possible mix of local repo + containerized supporting services

### Why it matters
This is a pragmatic bridge mode between pure local execution and real containerized deployment.

### What changes
- mixed host/container path behavior
- volume-mount semantics matter more
- environment bootstrapping matters more

### Swappable boundaries required
- execution surface provider
- artifact store abstraction
- environment/runtime configuration layer

### Architecture rules
- avoid embedding assumptions that the same filesystem path is visible to every component
- keep runtime path resolution explicit

## Variant 4. Kubernetes With Shared File Backend

### Topology
- API/worker/services in separate pods
- Postgres external or managed
- shared file backend such as EFS or Azure Files
- possibly separate role runtimes per pod

### Why it matters
This is the likely serious production-style direction.

### What changes relative to local mode
- no shared process memory
- no guarantee that one pod owns the whole flow
- role execution may be physically separated
- network and storage behavior become first-class concerns

### Swappable boundaries required
- message bus abstraction
- execution surface provider
- artifact store
- host runtime layer
- orchestration services
- configuration / secret provider

### Architecture rules
- workflow truth must be fully durable and externalized
- no logic may depend on in-memory continuity between role steps
- work execution must be idempotent and retry-safe
- the system must tolerate independent role service restarts

## Variant 5. EKS With EFS

### Topology
- Kubernetes on AWS
- shared file backend via EFS
- likely SQS or RabbitMQ depending deployment choices
- pods for TechLead, QA, workers, supporting services

### Why it matters
This is a specific but realistic cloud deployment target.

### What changes
- AWS-native infrastructure becomes attractive
- file semantics are shared but remote
- transport may drift toward AWS-native options

### Swappable boundaries required
- `MessageBus`
- `ExecutionSurfaceProvider`
- `ArtifactStore`
- cloud-aware configuration provider

### Architecture rules
- transport and shared-file assumptions must be abstracted
- runtime should support both RabbitMQ-style and SQS-style deployment strategies
- EFS is an adapter detail, not a domain concept

## Variant 6. AKS With Azure Files

### Topology
- Kubernetes on Azure
- shared file backend via Azure Files or similar
- possibly Azure Service Bus instead of RabbitMQ

### Why it matters
This is another realistic enterprise cloud target.

### What changes
- Azure-native managed services become attractive
- file/share semantics differ from EFS
- transport may shift to Azure Service Bus

### Swappable boundaries required
- `MessageBus`
- `ExecutionSurfaceProvider`
- `ArtifactStore`
- cloud-aware configuration provider

### Architecture rules
- AWS-specific assumptions must not leak into core logic
- shared storage and transport must be provider-agnostic at the service boundary

## Variant 7. Split Role Services / Per-Role Pods

### Topology
- TechLead runs in its own service/process/pod
- Delivery Architect runs separately
- QA runs separately
- worker role families run separately
- possibly one orchestrator service plus many role services

### Why it matters
The user explicitly wants us to consider a future where each role is independently hosted.

### What changes
- role lifecycle becomes cross-process by default
- claim/ack and transition durability become even more important
- orchestration cannot rely on direct function call chains between all steps

### Swappable boundaries required
- role orchestration contracts
- message bus abstraction
- workflow lifecycle service boundary
- run-event persistence and idempotency discipline

### Architecture rules
- role runtimes must be independent consumers of shared domain and repository contracts
- role execution contracts should be message-safe and retry-safe
- role-specific host surfaces should remain thin

## Variant 8. In-Process CLI First, FastAPI Later

### Topology
- initial phase uses CLI commands and in-process composition
- later phase exposes application services through FastAPI or another API surface

### Why it matters
This is one of the most likely evolution paths.

### What changes
- transport into the system changes from CLI invocations to HTTP/API invocations
- operator tooling and UI integration become easier

### Swappable boundaries required
- application service layer
- host surface abstraction
- authentication/authorization boundary
- DTO/contract discipline for API exposure

### Architecture rules
- command handlers should call application services, not own business logic
- domain services should not know whether callers are CLI or HTTP

## Variant 9. Producer UI Added Later

### Topology
- producer-side authoring workflows gain a UI
- decomposition selection, domain object modeling, component authoring, and brief generation may become interactive

### Why it matters
This is a major future value area for PAA.

### What changes
- producer-side authoring becomes a first-class application surface
- richer draft/save/compare/publish workflows emerge

### Swappable boundaries required
- producer-side application services
- component catalog services
- authoring registries
- policy selection services
- publication orchestration service

### Architecture rules
- producer-side authoring logic must not be trapped in ad hoc CLI scripts
- authoring operations should be callable by both CLI and UI hosts

## Variant 10. Consumer UI Added Later

### Topology
- runtime status, lineage, proofs, queue health, acceptance state, and role status may be shown in a UI

### Why it matters
- operator visibility matters
- human-supervised and semi-autonomous modes benefit from clear status views

### What changes
- projection and status services become more important
- read-model freshness and consistency visibility matter more

### Swappable boundaries required
- projection repository
- projection services
- application query services
- UI-facing DTOs / API contracts

### Architecture rules
- projections should remain downstream and read-only
- UI needs must not redefine primary truth

## Variant 11. Self-Hosted Combined Producer/Consumer Repo

### Topology
- one repo contains both producer and consumer roles for the same system
- shared package code, shared DB, shared runtime concepts
- publication and execution may both occur in one installation

### Why it matters
PAA itself may eventually run in this mode.

### What changes
- producer/consumer package boundaries remain, but may be composed together
- deployment is combined, but domain responsibilities remain distinct

### Swappable boundaries required
- package boundaries between `paa-core`, `paa-producer`, and `paa-consumer`
- publication and execution package separation
- producer application services versus consumer application services

### Architecture rules
- code organization should support producer-only, consumer-only, and combined installs
- combined deployment must not collapse domain boundaries

## Swappable Boundary Catalog

The following boundaries should be treated as intentionally swappable or composable:

### 1. Repository layer
Examples:
- Postgres now
- other persistence engines later

### 2. Message bus
Examples:
- RabbitMQ
- SQS
- Azure Service Bus
- in-memory bus for local/dev

### 3. Execution surface provider
Examples:
- repo-local worktrees
- Docker volume-backed workspace
- EFS-backed workspace
- Azure Files-backed workspace

### 4. Artifact store
Examples:
- local filesystem
- shared file system
- object-store-backed evidence or exports later

### 5. Git / collaboration provider
Examples:
- GitHub now
- possible other SCM later

### 6. Host runtime surface
Examples:
- CLI
- background worker
- FastAPI
- UI backend

### 7. Configuration / secret provider
Examples:
- env vars locally
- Kubernetes secrets/config maps
- cloud secret stores later

## Boundaries That Should Be Stable, Not Swappable

To keep the architecture sane, these should remain stable conceptual backbone elements:
- `WorkItem`
- `Workflow`
- `WorkflowTransition`
- `InstalledExecutionPackage`
- `CoderBrief`
- `BriefTarget`
- `Component`
- `ComponentElement`
- `CodeArtifactTarget`
- repository contracts as logical roles
- policy categories as logical roles

Adapters may vary.
Core domain language should not vary lightly.

## Topology-Neutral Design Rules

Across all deployment variants, the system should preserve these rules:

1. domain services must not depend directly on host-specific APIs
2. workflow truth must be durable and externalized
3. transport must remain event-plane infrastructure, not workflow truth
4. file/share backend details must remain behind explicit abstractions
5. projections must remain derived and read-only
6. producer-side authoring logic should be callable from both CLI and future UI/API surfaces
7. role runtimes should tolerate separate processes and retries

## Implications For The Preferred Architecture

This deployment analysis reinforces the layered-hybrid recommendation:
- domain core must be topology-neutral
- domain services must remain free of host and transport details
- application/orchestration services must coordinate use cases without owning persistence or transport mechanics
- infrastructure ports/adapters must isolate storage, messaging, file/share, and SCM variability
- host surfaces must remain thin

## Producer-Side Tooling Implications

Deployment variants should eventually become structured authoring inputs on the producer side.

Producer tooling should be able to annotate or select:
- supported deployment variants
- required swappable boundaries
- infrastructure capability assumptions
- policy compatibility for a target deployment
- brief and component guidance constrained by deployment model

This matters because deployment strategy should be part of the authority model, not only an ops afterthought.

## Next Note Suggested By This One

This note should feed directly into:
- the layered architecture proposal

That proposal should synthesize:
- decomposition options
- domain object model
- volatility analysis
- deployment variants and swappable boundaries

## Design Conclusion

PAA should be designed so that:
- the core semantics survive deployment change
- transport, storage, file/share, host, and SCM concerns are adapter-level concerns
- role runtimes can move from in-process automation to independently hosted services without forcing a domain redesign

That is the purpose of deployment-aware decomposition in this system.
