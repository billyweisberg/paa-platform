# Execution Package Resolution Service Pre-Spec

Date: 2026-05-17

## Purpose

Capture the pre-spec reasoning for `Execution Package Resolution Service` before writing the full `Component Spec`.

This note exists to make the component boundary explicit, surface the remaining unresolved seams, and reduce the risk of collapsing execution-package semantics into runtime orchestration or repository logic.

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-layered-architecture-proposal.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-layered-component-dependency-graph.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-stratum-2-service-dependency-comparison.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-domain-object-model-and-oo-component-decomposition.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-execution-package-repository-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-final-execution-package-registration-entity-design.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-runtime-consolidation-design-correction.md`

## Architecture Placement

`Execution Package Resolution Service` belongs in:
- `Domain Services`

It is not:
- a repository
- a policy component
- an application/orchestration service
- a host surface
- a file-system adapter

## Why This Service Exists

The system already models installed execution-package truth and overlay truth, but those records are not the same thing as execution-time resolution.

We need a service that can take:
- installed execution-package registrations
- overlay activation state
- runtime surface identity
- deployment-capability constraints

and resolve the effective execution context that runtime and downstream services are allowed to use.

Without this service, package-resolution behavior would drift into:
- repository adapters
- runtime lifecycle handlers
- queue or handoff code
- ad hoc file reads against installed package surfaces

That would make execution authority harder to reason about and harder to test.

## Dependency Graph Position

From the current layered dependency graph, this service is the next Stratum 2 domain-service candidate after `Component Design Planning Service`.

Upstream dependencies already identified:
- `Domain Core Model`
- `ExecutionPackageRepository`
- `DeploymentCapabilityPolicy`
- `StructuredLogger`

This is why it remains the next likely implementation target, but also why it is not as implementation-ready yet: the repository adapter slice and policy contract are less mature than the `Component Design Planning Service` inputs were.

## Primary Domain Objects

This service appears to work primarily on:
- `InstalledExecutionPackage`
- `PublishedExecutionPackage`
- `ExecutionOverlay`
- execution-surface identity
- effective execution context

It likely also consumes supporting context from:
- `WorkItem`
- `CoderBrief`
- runtime-surface selection inputs

But those look like caller-provided resolution context, not the semantic center of the service.

## Owned Responsibility Boundary

The likely owned responsibility of this service is:
- resolve the effective execution-time package context for one work item and runtime surface

That suggests it should own decisions such as:
- which installed execution package is currently effective for an execution surface
- which active overlays are in effect on that install
- which package-local artifact pointers should be treated as execution-time truth
- whether the resolved package context satisfies deployment-capability constraints
- what normalized execution-context DTO should be exposed to downstream services

## Non-Owned Responsibility Boundary

This service should not own:
- workflow transition legality
- queue routing or message dispatch
- coder-brief assembly
- component-design planning
- application-level orchestration
- package installation or overlay activation mutations
- direct GitHub or host-surface behavior

It also should not become the file-system truth owner.

The repository may read installed artifact surfaces, but the service should consume normalized repository outputs rather than reinterpret raw files itself.

## Likely Collaborators

### Hard collaborators
- `ExecutionPackageRepository`
- `DeploymentCapabilityPolicy`
- `StructuredLogger`

### Possible later collaborators
- a package-context DTO assembler helper if installed-package and overlay normalization grows too large
- runtime-surface identity helper if surface matching expands beyond the current scope

### Important non-collaborators
This service should not directly depend on:
- `WorkflowStateRepository`
- `RuntimeEventRepository`
- `MessageBus`
- `GitProvider`
- `ComponentDesignRepository`

If it starts needing those, the boundary is likely wrong.

## Candidate Inputs

Likely resolution inputs include:
- execution-surface key
- execution-surface type
- repo/runtime root identity
- optional work-item identity
- optional brief identity
- optional consumer-context or runtime-profile key

## Candidate Outputs

Likely outputs include:
- active execution-package resolution view
- effective overlay set for the resolved install
- normalized execution-context payload
- deployment-capability decision summary
- execution-package gap or missing-install diagnostics

## What This Service Probably Is Not

It is probably not:
- the install/refresh/remove service for execution packages
- the overlay activation manager
- the runtime lifecycle engine
- the policy owner for deployment capability itself

Those relate to it, but should not be collapsed into it.

## Potential Internal Sub-Responsibilities

There are at least three sub-responsibilities visible already:

1. active install resolution
- resolve the active installed package registration for one execution surface

2. overlay resolution
- resolve the active overlay set that modifies the installed package context

3. effective context assembly
- normalize the effective package, overlay, and artifact-pointer context for downstream runtime consumers

These may still fit inside one service initially.
If overlay normalization becomes heavy, we may split it later.

## Open Questions Before Full Spec

1. How much overlay interpretation belongs here versus `ExecutionPackageRepository`?
- Current answer: repository should expose normalized overlay records; service should decide effective execution context.

2. What is the exact contract for `DeploymentCapabilityPolicy`?
- Current answer: still unresolved and needs to be made explicit before full implementation.

3. Should this service return DTOs only, or also persist resolution snapshots?
- Current answer: return DTOs first; avoid turning the service into a projection or persistence owner.

4. Should this service know about `CoderBrief` directly?
- Current answer: only as optional caller context if a resolved package must be matched to brief scope.

5. Does the first implementation slice require a concrete `ExecutionPackageRepository` adapter first?
- Current answer: yes, or at least a testable repository seam with active-install and overlay resolution behaviors.

## Pre-Spec Conclusion

`Execution Package Resolution Service` currently looks like a well-bounded Stratum 2 domain service that:
- sits on top of execution-package registration truth and deployment-capability policy
- resolves effective execution-time package context
- should feed runtime and brief consumers without owning orchestration
- is the next dependency-graph-selected service after `Component Design Planning Service`

Its remaining readiness gap is not conceptual confusion.
It is the need to make the repository adapter slice and policy contract explicit enough to support a clean implementation.

## Next Step

Write the full `Component Spec` for:
- `Execution Package Resolution Service`

That spec should now be able to focus on:
- exact role
- exact resolution inputs and outputs
- exact injected collaborators
- exact invariants
- exact non-goals

without reopening the broader architecture questions.
