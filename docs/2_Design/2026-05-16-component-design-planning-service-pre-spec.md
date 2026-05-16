# Component Design Planning Service Pre-Spec

Date: 2026-05-16

## Purpose

Capture the pre-spec reasoning for `Component Design Planning Service` before writing the full `Component Spec`.

This note exists to make the component boundary explicit, surface open questions, and reduce the risk of writing an oversized or underspecified service contract.

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-layered-architecture-proposal.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-layered-component-dependency-graph.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-stratum-2-service-dependency-comparison.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-domain-object-model-and-oo-component-decomposition.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-component-design-repository-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-final-component-element-entity-design.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-component-element-realization-model.md`

## Architecture Placement

`Component Design Planning Service` belongs in:
- `Domain Services`

It is not:
- a repository
- a policy component
- an application/orchestration service
- a host surface
- a transport adapter

## Why This Service Exists

The system already has structured component-design data, but the existence of that data is not the same as planning logic.

We need a service that can take stable design structures such as:
- components
- component elements
- code artifact targets / realizations
- dependency edges
- brief target sequencing context

and turn them into coherent planning outputs that later services can use for:
- brief assembly
- sequencing validation
- component-targeted implementation guidance
- producer-side authority authoring support

Without this service, planning logic would drift into:
- ad hoc SQL queries
- producer CLI handlers
- brief assembly service
- future UI code

That would recreate the same sprawl in a different layer.

## Dependency Graph Position

From the current layered dependency graph, this service is a first Stratum 2 domain-service candidate.

Upstream dependencies already identified:
- `Authority Taxonomy Model`
- `ComponentDesignRepository`
- `StructuredLogger`

This is one reason it ranked first in readiness among the initial Stratum 2 services.

## Primary Domain Objects

This service appears to work primarily on:
- `Component`
- `ComponentElement`
- `ComponentElementType`
- `CodeArtifactType`
- `CodeArtifactTarget`

It likely also consumes supporting context from:
- `DesignPackage`
- `CoderBrief`
- `BriefTarget`
- package-scoped dependency edges

But those look more like downstream planning context than its core owned semantic focus.

## Owned Responsibility Boundary

The likely owned responsibility of this service is:
- interpret stable component-design structures and produce structured planning outputs suitable for implementation targeting and brief derivation

That suggests it should own decisions such as:
- what component elements apply to a component in structured form
- what code artifact forms are valid for those elements
- what realization targets are available for a component element
- what planning outputs should be exposed to downstream brief assembly or producer tooling

## Non-Owned Responsibility Boundary

This service should not own:
- workflow lifecycle semantics
- execution-package resolution
- role routing
- acceptance / QA / merge decisions
- transport packet handling
- installation or overlay activation
- application-service orchestration
- direct host/CLI/UI behavior

This service should also not become the final owner of:
- brief sequencing policy
n
It may contribute planning inputs to sequencing, but final brief assembly and execution ordering likely belongs downstream.

## Likely Collaborators

### Hard collaborators
- `ComponentDesignRepository`
- `StructuredLogger`

### Possible later collaborators
- `ComponentDependencyResolver` or dependency-planning helper if dependency interpretation becomes large enough to split
- `BriefAssemblyService` as a downstream consumer, not an injected dependency unless required by final design

### Important non-collaborators
This service should not directly depend on:
- `MessageBus`
- `GitProvider`
- `WorkflowStateRepository`
- `RuntimeEventRepository`
- `ExecutionPackageRepository`

If it starts needing those, the boundary is probably wrong.

## Candidate Inputs

Likely planning inputs include:
- component identity
- project identity
- component element selection filters
- realization type filters
- package-scoped dependency or sequencing context
- optional brief-derivation context

## Candidate Outputs

Likely outputs include:
- component planning view
- component element planning view
- valid realization target set for a component
- normalized planning payload for brief assembly
- dependency-aware planning summary for a component slice

## What This Service Probably Is Not

It is probably not:
- the component dependency engine for the entire system
- the brief assembly service itself
- the final sequencing service
- a component-spec authoring service

Those may relate to it, but rolling them all into this service would over-compress the design.

## Potential Internal Sub-Responsibilities

There are at least three sub-responsibilities visible already:

1. component-structure interpretation
- read component and element structures and normalize them for use

2. realization-target interpretation
- map component elements to valid code artifact forms and concrete realization instances

3. planning-output assembly
- produce structured outputs for downstream brief derivation or authoring surfaces

These may still fit inside one service initially.
If they start diverging heavily, we should split them later.

## Open Questions Before Full Spec

1. Should dependency-edge interpretation live here or in a separate planning helper/service?
- Current answer: likely light interpretation here, heavy dependency resolution elsewhere if needed.

2. Should this service return planning DTOs only, or also write planning records?
- Current answer: likely return planning DTOs first and avoid becoming a persistence owner.

3. How much sequencing logic belongs here versus `Brief Assembly Service`?
- Current answer: this service should provide structured planning inputs; final brief target sequencing likely belongs downstream.

4. Should this service know about `DesignPackage` and `CoderBrief` directly?
- Current answer: only as supporting context if necessary, not as the semantic center of the service.

5. Is a separate `Component Dependency Planning Service` needed later?
- Current answer: maybe, but not yet required to define the initial service boundary.

## Pre-Spec Conclusion

`Component Design Planning Service` currently looks like a well-bounded Stratum 2 domain service that:
- sits on top of the authority taxonomy and component-design repository
- interprets stable component-design structures
- emits planning-friendly outputs for downstream brief derivation and producer-side tooling
- has relatively few unresolved upstream dependencies

That is a good reason for it to become the first fully specified domain service in the current architecture.

## Next Step

Write the full `Component Spec` for:
- `Component Design Planning Service`

That spec should now be able to focus on:
- exact role
- exact inputs/outputs
- exact injected collaborators
- exact invariants
- exact non-goals

without reopening the broader architecture questions.
