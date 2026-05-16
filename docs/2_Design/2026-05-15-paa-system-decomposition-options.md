# PAA System Decomposition Options

Date: 2026-05-15

## Purpose

Brainstorm and compare multiple candidate methods for decomposing the PAA system into components and services.

This note exists to prevent premature convergence on a single decomposition style before we evaluate the tradeoffs.

The goal is to create several viable design options so we can choose a system architecture that:
- matches the domain well
- isolates volatility well
- adapts to multiple deployment models
- supports better authority authoring and producer-side tooling

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-authority-package-authoring-process.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-domain-object-model-and-oo-component-decomposition.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-system-component-diagram-v2.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-v2-component-relationships.md`

## Evaluation Criteria

Each option is evaluated against:
- domain clarity
- change isolation
- deployment flexibility
- implementation clarity
- producer-side authoring support
- coder-agent assignment friendliness
- long-term maintainability

## Option 1. Functional Decomposition

### Description
Decompose the system into capability-oriented services based on what the system does.

Example services:
- `Work Item Coordination Service`
- `Workflow Lifecycle Service`
- `Execution Package Resolution Service`
- `Brief Assembly Service`
- `Verification And Acceptance Service`
- `Projection / Reporting Service`
- `Authority Publication Service`

### Strengths
- intuitive and easy to explain
- close to use-case language
- straightforward for CLI-first implementation
- easy to map to current runtime capabilities

### Risks
- tends to create broad “service” blobs
- can mix orchestration and domain logic
- can hide infrastructure or volatility seams
- may fossilize current scripts into bigger classes

### Best use
Useful as an initial explanatory decomposition and as a bridge from current runtime behavior.

## Option 2. Domain-Centered Decomposition

### Description
Decompose around first-class domain objects and their aggregate boundaries.

Candidate roots and entities:
- `WorkItem`
- `Workflow`
- `WorkflowTransition`
- `InstalledExecutionPackage`
- `CoderBrief`
- `BriefTarget`
- `Component`
- `ComponentElement`
- `CodeArtifactTarget`
- `VerificationObligation`

### Strengths
- strong ownership boundaries
- good OO design discipline
- prevents transport from impersonating state ownership
- aligns well with durable data modeling
- supports precise reasoning about invariants

### Risks
- can underemphasize orchestration flows
- may feel abstract when mapping to scripts and hosts
- can become theory-heavy if not grounded in deployment and policy concerns

### Best use
Useful as the stable semantic backbone of the system.

## Option 3. Volatility-Based Decomposition

### Description
Decompose around expected change axes so that change is isolated and blast radius is minimized.

Expected volatility axes:
- storage backend
- message transport
- deployment topology
- authority package schema/version
- orchestration policy
- UI/API host surfaces
- execution topology

Candidate boundaries:
- repository layer
- message bus abstraction
- execution surface abstraction
- policy engines
- package-resolution boundary
- projection layer

### Strengths
- excellent for future adaptability
- naturally supports swappable components
- reduces future rewrite pressure
- strong fit for multi-environment deployment

### Risks
- can become over-abstract too early
- may produce too many seams for a first implementation
- can obscure core domain language if overused

### Best use
Useful for identifying what must be isolated, swapped, or versioned independently.

## Option 4. Deployment-Centered Decomposition

### Description
Decompose around likely runtime topologies and hosting scenarios.

Candidate scenarios:
- laptop CLI
- Docker Compose
- Docker Desktop
- Kubernetes
- EKS with EFS
- AKS with Azure Files
- split role processes / pods
- future FastAPI host
- future producer or consumer UI

Candidate deployment-driven boundaries:
- host runtime layer
- background worker host
- role process boundary
- shared artifact store abstraction
- file/share abstraction
- transport adapter

### Strengths
- keeps the system honest about real deployment needs
- good for identifying swappable adapters
- prevents “only works on a laptop” architecture

### Risks
- deployment concerns can dominate too early
- may split things that should stay logically cohesive
- can encourage host-first design instead of domain-first design

### Best use
Useful as a validation lens, not as the sole primary decomposition method.

## Option 5. Layered Hybrid Decomposition

### Description
Decompose the system into layered component families that combine domain clarity, volatility isolation, and deployment flexibility.

Proposed layers:

1. `Domain Core`
- stable domain objects
- domain invariants
- core semantic concepts

2. `Domain Services`
- workflow lifecycle semantics
- execution package resolution
- brief assembly
- verification and acceptance
- component planning

3. `Policy Layer`
- routing policy
- transition policy
- acceptance policy
- reset/recovery policy
- deployment capability policy

4. `Application / Orchestration Services`
- TechLead orchestration
- role return orchestration
- authority publication orchestration
- projection refresh orchestration

5. `Infrastructure Ports`
- repositories
- message bus
- execution surface provider
- artifact store
- Git provider

6. `Infrastructure Adapters`
- Postgres repositories
- RabbitMQ transport
- SQS transport
- Azure Service Bus transport
- local filesystem artifact store
- shared file-store implementations
- GitHub adapter

7. `Host Surfaces`
- CLI host
- background worker host
- FastAPI host
- producer UI backend
- consumer UI backend

### Strengths
- preserves strong domain semantics
- isolates change well
- supports multiple deployment models
- gives producer-side tooling a clear authoring structure
- avoids collapsing transport, orchestration, and domain semantics together
- likely the best fit for long-term PAA evolution

### Risks
- more design effort up front
- requires discipline to keep layers clean
- can look heavier than the current runtime scripts

### Best use
This is currently the strongest candidate for the preferred PAA architecture.

## Comparative Summary

| Option | Main Idea | Strength | Main Risk | Recommended Role |
|---|---|---|---|---|
| Functional | decompose by capability | intuitive | service blobs | baseline explanatory view |
| Domain-Centered | decompose by domain objects | strong ownership | may underplay orchestration | semantic backbone |
| Volatility-Based | decompose by expected change | blast-radius control | early over-abstraction | change-isolation lens |
| Deployment-Centered | decompose by runtime topology | host adaptability | host-first bias | validation lens |
| Layered Hybrid | combine domain, policy, orchestration, and adapters | best overall balance | more upfront design work | preferred architecture candidate |

## Current Recommendation

The current recommended direction is:
- use `Domain-Centered Decomposition` for semantic backbone
- use `Volatility-Based Decomposition` to define isolation seams
- use `Deployment-Centered Decomposition` as a validation lens
- adopt `Layered Hybrid Decomposition` as the preferred overall system architecture

In short:
- not purely functional
- not purely deployment-driven
- not purely abstract volatility slicing
- but a layered architecture informed by all three

## Why This Matters For Producer-Side Tooling

A strong decomposition method enables better producer-side authoring support for:
- system decomposition option authoring
- domain object registration
- component catalog authoring
- component element authoring
- code artifact target authoring
- brief target sequencing
- volatility annotation
- deployment variant annotation
- policy selection

That means decomposition is not just a design discussion.
It becomes part of the authority-authoring toolchain.

## Next Notes Suggested By This One

This option set naturally leads to:
1. `PAA Volatility Analysis`
2. `PAA Deployment Variants And Swappable Boundaries`
3. `PAA Layered Architecture Proposal`

Those notes should refine and select the preferred architecture rather than forcing the decision prematurely in this note.

## Design Conclusion

PAA should not be decomposed from current scripts upward.

It should be decomposed through:
- domain understanding
- volatility analysis
- deployment analysis
- layered architecture selection

The current best path is a layered hybrid model built on a domain-centered backbone and shaped by volatility and deployment realities.
