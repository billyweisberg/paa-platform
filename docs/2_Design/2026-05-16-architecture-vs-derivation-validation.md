# Architecture Vs Derivation Validation

Date: 2026-05-16
Phase: `Phase 4. Validate Architecture And Layering Against The Derivation Process`
Plan: `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-16-paa-derivation-method-validation-plan.md`

## Purpose

Validate whether the current layered architecture and component decomposition support the derivation process cleanly, or whether derivation is still being forced through ambiguous or misplaced component boundaries.

This phase is focused on the architecture question:
- does the current system design give `System Design -> Agent Team -> Functioning Software System` a clean architectural home?

## Validation inputs

Primary phase inputs:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-paa-derivation-pipeline-validation.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-component-design-planning-service-derivation-input-coverage.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-derivation-state-data-model-validation.md`

Primary architecture authority:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-layered-architecture-proposal.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-paa-producer-derivation-subsystem.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-layered-component-dependency-graph.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-domain-object-model-and-oo-component-decomposition.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-authority-package-authoring-process.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-component-design-planning-service-component-spec.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-data-access-layer-design.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-paa-solution-project-scaffolding-plan.md`

## Main question

Does derivation have a clean architectural home in the current layered system?

Answer:
- yes, mostly
- but the architecture still under-specifies the producer-side derivation-governance and review service families

That is the key Phase 4 result.

The architecture is no longer the blocker it used to be.
The remaining architectural work is about making the producer-side derivation path explicit and complete.

This is now addressed directly by:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-paa-producer-derivation-subsystem.md`

## The current layered architecture is directionally correct

The chosen layered architecture is:
1. `Domain Core`
2. `Domain Services`
3. `Policy Layer`
4. `Application / Orchestration Services`
5. `Infrastructure Ports`
6. `Infrastructure Adapters`
7. `Host Surfaces`

This is a good fit for derivation because derivation itself spans multiple layers:
- stable domain objects and taxonomies
- derivation and planning semantics
- approval and sequencing policy
- producer-side orchestration
- data and artifact access
- eventual host surfaces such as CLI, API, or UI

That means derivation should not live in one blob.
It should span the layers deliberately.

## Architectural home for each major derivation concern

## 1. Stable design authority

Best layer:
- `Domain Core`

Current architectural fit:
- `strong`

Why:
- the domain model already identifies the stable objects derivation works on:
  - `Component`
  - `ComponentElement`
  - `CodeArtifactTarget`
  - `DesignPackage`
  - `CoderBrief`
  - `BriefTarget`
- the authority taxonomy model is already a foundational semantic layer

Conclusion:
- derivation has the right semantic backbone

## 2. Component interpretation and planning

Best layer:
- `Domain Services`

Current architectural fit:
- `strong`

Why:
- `Component Design Planning Service` is already correctly placed here
- it interprets structured design, but does not orchestrate runtime or own persistence

Conclusion:
- this part of derivation has a clean architectural home

## 3. Code-artifact target shaping

Best layer:
- `Domain Services`

Current architectural fit:
- `strong`

Why:
- the element and realization model already supports this semantically
- `Component Design Planning Service` can interpret these structures without leaving the domain-service layer

Conclusion:
- the architecture supports code-artifact-target derivation well

## 4. Brief assembly

Best layer:
- `Domain Services`

Current architectural fit:
- `partial`

Why:
- the domain model already names `Brief Assembly Service`
- the layered architecture clearly has room for it
- but the service is still only a decomposition concept, not a fully specified architectural contract

Conclusion:
- the architecture supports it conceptually
- but this service family still needs to be made explicit as part of the derivation path

## 5. Derivation sequencing and readiness evaluation

Best layer:
- split across:
  - `Policy Layer`
  - `Domain Services`

Current architectural fit:
- `partial`

Why:
- the system has dependency graph and sequencing concepts
- but the architecture does not yet clearly separate:
  - sequencing policy
  - derivation-readiness policy
  - domain service execution of those policies

What is missing:
- explicit derivation-oriented policies such as:
  - `DerivationReadinessPolicy`
  - `BriefTargetSequencingPolicy`
  - possibly `BriefApprovalPolicy`

Conclusion:
- this part of the derivation architecture is still under-specified

## 6. Design-package and brief review / approval governance

Best layer:
- `Application / Orchestration Services`

Current architectural fit:
- `partial`

Why:
- review and approval are not pure domain-object interpretation
- they coordinate:
  - design authority roles
  - package state
  - brief state
  - signoff workflows
  - publication readiness
- the architecture has an application-service layer for exactly this kind of coordination

What is missing:
- explicit producer-side services for:
  - derivation orchestration
  - brief review and approval
  - package-to-brief progression

Conclusion:
- the layer is correct
- the service family is still implied rather than explicit

## 7. Producer-side authoring and publication flows

Best layer:
- `Application / Orchestration Services`
- surfaced through producer `Host Surfaces`

Current architectural fit:
- `partial`

Why:
- the architecture process note already identifies producer-side authoring opportunities
- the scaffolding plan places producer host surfaces in `paa-producer`
- the layered architecture clearly allows producer-side application services

What is missing:
- an explicit producer-side service family for authority authoring and derivation operations

Conclusion:
- derivation has a plausible producer-side home
- but producer-side service decomposition needs to be made more explicit

## 8. Persistence and query access

Best layer:
- `Infrastructure Ports`
- `Infrastructure Adapters`

Current architectural fit:
- `strong`

Why:
- the DAL work already created explicit repository boundaries
- derivation now has clear data access seams rather than raw-table access pressure

Conclusion:
- this is one of the strongest supporting parts of the current architecture

## 9. Delivery to execution surfaces

Best layer:
- `Application / Orchestration Services`
- `Host Surfaces`

Current architectural fit:
- `partial`

Why:
- the packet-integration rule is clear conceptually
- but the architecture does not yet explicitly identify the service responsible for:
  - taking an approved brief
  - embedding it in an architect packet
  - publishing that packet to execution transport

This is currently inferable, but not explicit enough.

Conclusion:
- another producer-side orchestration gap remains

## Validation against the Phase 4 questions

## Question 1. Are the right responsibilities in the right layers for derivation?

Answer:
- mostly yes

What is already placed correctly:
- stable semantic objects in `Domain Core`
- component interpretation in `Domain Services`
- repositories and access seams in `Infrastructure Ports` and `Adapters`
- producer and consumer entrypoints in `Host Surfaces`

What is still weak:
- derivation-governance responsibilities are not yet fully decomposed between:
  - `Policy Layer`
  - `Application / Orchestration Services`

## Question 2. Do producer-side services have a clear architectural home?

Answer:
- yes at the layer level
- not yet fully at the named-service level

The architecture clearly provides room for producer-side services in:
- `Application / Orchestration Services`
- producer `Host Surfaces`

But it does not yet name the full producer-side derivation service family explicitly enough.

## Question 3. Are we missing authoring-side components or service boundaries?

Answer:
- yes

This is the main Phase 4 finding.

The current architecture is missing explicit first-class producer-side derivation components such as:
- `Derivation Orchestration Service`
- `Brief Assembly Service`
- `Brief Review And Approval Service`
- `Derivation Readiness Evaluation Service` or equivalent decomposition through policy plus service
- `Packet Preparation / Brief Embedding Service`

These concerns exist in the process and data model, but they are not all yet explicit in the component architecture.

## Validation against the producer-side authoring opportunities

The process note says producer-side tooling should eventually support:
- system decomposition options
- domain object registration
- component catalog authoring
- component element authoring
- code artifact target authoring
- brief target sequencing
- volatility annotation
- deployment variant annotation
- policy selection

The current architecture supports these unevenly.

## 1. System decomposition options

Architectural support:
- `strong`

Why:
- this work already lives in design authority and does not depend on missing lower-level components

## 2. Domain object registration

Architectural support:
- `strong`

Why:
- the domain core and taxonomy layers are appropriate homes

## 3. Component catalog authoring

Architectural support:
- `strong`

Why:
- `Component Design Repository`
- `Component Design Planning Service`
- producer-side application services can support this cleanly

## 4. Component element authoring

Architectural support:
- `strong`

Why:
- the element taxonomy and repository layer already support it well

## 5. Code artifact target authoring

Architectural support:
- `strong`

Why:
- the realization model and repository layer give this a clear home

## 6. Brief-target sequencing

Architectural support:
- `partial`

Why:
- data model support exists
- architecture needs a clearer service and policy decomposition for sequencing and approval readiness

## 7. Volatility annotation

Architectural support:
- `partial`

Why:
- the analysis exists at design-note level
- no explicit producer-side service family yet owns structured volatility annotation authoring

## 8. Deployment variant annotation

Architectural support:
- `partial`

Why:
- the analysis exists and the layered architecture supports swappable boundaries
- but there is no explicit producer-side authoring service family for deployment-capability metadata yet

## 9. Policy selection

Architectural support:
- `partial`

Why:
- a `Policy Layer` exists architecturally
- but producer-side selection and approval of policy configurations is not yet clearly modeled as an authoring or orchestration concern

## Cleanest architectural conclusion

Derivation now has a clean home in the current architecture at the layer level.

The remaining problem is not that the architecture is wrong.
The remaining problem is that the producer-side derivation path is still under-decomposed.

In other words:
- the architecture is good enough
- the producer-side derivation subsystem is not yet explicit enough

That is a much narrower problem than we had before.

## Missing producer-side service families

These service families should now be made explicit in the architecture.

## 1. `Derivation Orchestration Service`

Layer:
- `Application / Orchestration Services`

Role:
- coordinate the end-to-end derivation pipeline from approved design package to approved coder brief

Why needed:
- derivation spans multiple domain services, policies, repositories, and review gates
- it should not be smeared into CLI flows or one domain service

## 2. `Brief Assembly Service`

Layer:
- `Domain Services`

Role:
- convert structured slice, component, contract, and target data into a draft coder brief and ordered brief-target set

Why needed:
- this is the direct design-to-brief bridge
- it is currently implied but not explicit enough

## 3. `Derivation Readiness Policy`

Layer:
- `Policy Layer`

Role:
- define when a slice is ready to enter derivation and what required inputs or signoffs are missing

Why needed:
- Phase 1 and Phase 3 both showed readiness is important and currently under-explicit

## 4. `Brief Target Sequencing Policy`

Layer:
- `Policy Layer`

Role:
- govern ordering and dependency of realization targets within and across coder briefs

Why needed:
- the realization and target model now exists
- architecture should expose the policy that interprets it

## 5. `Brief Review And Approval Service`

Layer:
- `Application / Orchestration Services`

Role:
- coordinate review, signoff, approval, rejection, and readiness progression for derived coder briefs

Why needed:
- design-package signoff exists, but brief-governance still lacks an explicit service home

## 6. `Packet Preparation Service`

Layer:
- `Application / Orchestration Services`

Role:
- take an approved brief and prepare the transport-ready architect packet with embedded brief and reference

Why needed:
- packet embedding is part of the derivation pipeline, but has no explicit component home yet

## Architectural refinements recommended from Phase 4

## Refinement 1. Make the producer-side derivation subsystem explicit

The architecture should explicitly identify a producer-side derivation subsystem composed of:
- domain services
- policies
- application/orchestration services
- producer hosts

This subsystem is one of the main engines of PAA and should be visible in the architecture.

## Refinement 2. Separate derivation policy from derivation orchestration

Do not let readiness, sequencing, and approval logic collapse into one producer application service.

Keep separate:
- policies that decide
- domain services that interpret and assemble
- application services that coordinate

## Refinement 3. Treat brief assembly as a first-class service

`Brief Assembly Service` should no longer remain only a decomposition idea.
It should become an explicit architecture component because it is central to the PAA mission.

## Refinement 4. Treat producer-side review and approval as architecture, not only workflow

Brief review and approval are not merely procedural steps.
They are part of the system architecture because they govern the transition from design authority to execution authority.

## Final Phase 4 conclusion

The layered architecture and component decomposition are good enough to support the derivation process.

That means the architecture is no longer the main blocker.

However, the current system still needs a more explicit producer-side derivation subsystem with named components for:
- derivation orchestration
- brief assembly
- readiness policy
- brief-target sequencing policy
- brief review and approval
- packet preparation

So the right conclusion is:
- derivation has a clean architectural home
- but its producer-side service decomposition is not yet fully explicit

## Exit criteria check

Phase 4 exit criteria were:
- derivation has a clean architectural home in the layered system
- missing producer-side service families are identified explicitly if present

Result:
- satisfied

## Recommendation for Phase 5

Proceed to:
- validate the tooling model against real producer-side use

Carry-forward conclusion:
- Phase 5 should assume the architecture is viable
- and should now test whether the current and planned tooling surfaces can actually drive the producer-side derivation subsystem identified in this phase
