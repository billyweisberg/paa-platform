# Component Design Planning Service Derivation Dry Run

Date: 2026-05-16
Phase: `Phase 6. Perform A Concrete Derivation Dry Run`
Plan: `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-16-paa-derivation-method-validation-plan.md`

## Purpose

Use `Component Design Planning Service` as the first concrete dry-run target and test whether the current PAA derivation method can move from reviewed System Design to a coder-agent-ready implementation brief.

This phase is intentionally not an implementation pass.
It is a derivation validation pass.

The question is:
- can the current PAA system derive a credible implementation brief for `Component Design Planning Service`, and if not, exactly where does the current derivation system stop being execution-capable?

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-paa-derivation-pipeline-validation.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-component-design-planning-service-derivation-input-coverage.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-derivation-state-data-model-validation.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-architecture-vs-derivation-validation.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-producer-tooling-validation.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-paa-producer-derivation-subsystem.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-component-design-planning-service-component-spec.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-coder-brief-derivation-method.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-coder-brief-field-derivation-matrix.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-coder-brief-sequencing.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-coder-run-brief-packet-integration.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-coder-run-brief.md`

## Dry-Run Rule

This pass is allowed to use manual bridging where producer-side derivation tooling is not yet first-class.

However:
- every manual bridge must be called out explicitly
- every place where the current model cannot encode the intended outcome must be called out explicitly
- the final result must distinguish:
  - what the current system can already derive
  - what it can derive only manually
  - what it cannot yet encode cleanly

## Starting State Evidence

The current PAA system already contains live derivation records, but none for this service.

Observed current DB state during this pass:
- `paa.design_packages`: `6`
- `paa.coder_run_briefs`: `10`
- full-text match for `Component Design Planning Service` in `design_packages` or `coder_run_briefs`: `0`

Observed current code state for the target service:
- service scaffold exists at:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/component_design_planning/`
- current files are placeholders only:
  - `__init__.py`
  - `contracts.py`
  - `models.py`
  - `default.py`

Implication:
- this dry run is not replaying an existing derivation artifact
- it is testing whether the current design and derivation system are sufficient to derive a new service implementation slice for the first time

## Dry-Run Outcome Summary

The current PAA system can derive a credible **draft implementation brief** for `Component Design Planning Service`.

The current PAA system cannot yet derive a fully **execution-authoritative coder brief and packet** for this service without manual bridging and a few targeted model/tool refinements.

That is a good result.
It means the method is directionally valid, but the last bridge from component design into execution authority still needs a few explicit structures.

## Dry-Run Stage Results

| Stage | Goal | Current support | Dry-run result |
| --- | --- | --- | --- |
| 0 | reviewed upstream authority | strong | passed |
| 1 | materialize active slice design package | partial | manual bridge required |
| 2 | confirm derivation readiness | partial | manual bridge required |
| 3 | resolve slice identity and authority context | partial | provisional values required |
| 4 | resolve primary component assignment | strong | passed |
| 5 | resolve scope and placement boundaries | partial | passed with manual narrowing |
| 6 | resolve collaboration and dependency contracts | strong | passed |
| 7 | resolve behavioral and proving contracts | partial | passed with manual authoring |
| 8 | resolve change budget and anti-goals | partial | passed with manual authoring |
| 9 | compute brief-target sequencing | partial | blocked by taxonomy gap |
| 10 | assemble draft coder brief | strong enough | passed |
| 11 | persist and approve brief | partial | not fully supported |
| 12 | embed brief into architect packet | strong once approved brief exists | not attempted |

## Stage-by-Stage Dry Run

## Stage 0. Reviewed upstream authority

Inputs used:
- layered architecture proposal
- dependency graph and stratum notes
- producer derivation subsystem note
- `Component Design Planning Service` pre-spec and component spec
- solution scaffolding plan

Result:
- enough reviewed design authority exists to justify deriving a draft implementation brief for this component

Status:
- `passed`

## Stage 1. Materialize the active slice design package

Expected normal behavior:
- one explicit `DesignPackage` row and artifact for this service implementation slice

What exists now:
- the source design is spread across multiple approved notes
- no normalized `DesignPackage` exists yet for the implementation of this service
- no bound `work_item_id`, `task_id`, or issue exists for this slice

Dry-run bridge used:
- treat the following note set as the provisional slice design package:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-component-design-planning-service-component-spec.md`
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-component-design-planning-service-pre-spec.md`
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-paa-producer-derivation-subsystem.md`
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-paa-solution-project-scaffolding-plan.md`

Result:
- the slice can be reasoned about
- the slice is not yet materialized as a real producer-side design package record

Status:
- `manual bridge required`

## Stage 2. Confirm derivation readiness

Expected normal behavior:
- package status, signoffs, and dependency state prove derivation readiness

What exists now:
- design maturity is strong
- dependency position is clear
- no actual package approval/signoff record exists for this slice

Dry-run decision:
- treat the service as `derivation-ready for dry run only`
- do not treat it as execution-ready authority

Status:
- `manual bridge required`

## Stage 3. Resolve slice identity and authority context

Expected normal behavior:
- derive project, authority version, milestone, phase, task, work item, issue binding, and authorized delta family from structured slice records

What exists now:
- project context is obvious
- component identity is explicit
- no actual issue, PR, work item, or task binding exists for this slice

Dry-run bridge used:
- assign provisional dry-run identity values in the draft brief:
  - `project = paa-platform`
  - `authority_version = 2026-05-16-dry-run`
  - `task_id = paa-stratum2-component-design-planning-service`
  - `issue_number = null`
  - `pr_number = null`
  - `authorized_delta_family = component-design-planning-service-implementation`

Important rule:
- these are acceptable for a dry run
- they are not a substitute for a real task-bound authority package

Status:
- `provisional values required`

## Stage 4. Resolve primary component assignment

Inputs used:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-component-design-planning-service-component-spec.md`

Derived result:
- primary component: `Component Design Planning Service`
- role: domain service that interprets structured component design into planning-ready outputs for brief derivation and producer authoring flows
- system layer: `domain-services`
- tier: `runtime`

Status:
- `passed`

## Stage 5. Resolve scope and placement boundaries

Inputs used:
- component spec
- solution scaffolding plan
- current service scaffold files

Derived target modules:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/component_design_planning/contracts.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/component_design_planning/models.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/component_design_planning/default.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/component_design_planning/__init__.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/tests/unit/test_component_design_planning_service.py`

Derived architecture constraints:
- keep the service in the `Domain Services` layer
- keep repository access injected through `ComponentDesignRepository`
- do not place raw SQL, DB profile handling, or packet logic inside the service
- do not let the service absorb brief assembly, sequencing, or producer orchestration concerns

Status:
- `passed with manual narrowing`

## Stage 6. Resolve collaboration and dependency contracts

Inputs used:
- component spec
- repository contracts
- producer derivation subsystem note

Derived collaborators:
- injected:
  - `ComponentDesignRepository`
  - `StructuredLogger`
- optional later collaborator:
  - `DependencyPlanningHelper`
- likely callers:
  - `Brief Assembly Service`
  - `Derivation Orchestration Service`
  - future producer-side authoring hosts

Derived forbidden hidden dependencies:
- no direct SQL
- no direct filesystem authority lookups
- no GitHub coupling
- no workflow-state or runtime-event access
- no packet assembly logic

Status:
- `passed`

## Stage 7. Resolve behavioral and proving contracts

Inputs used:
- component spec
- repository contract
- service scaffold plan

Derived behavioral contract is strong enough to draft.

Derived core behavior:
- resolve one component by stable identity
- load and normalize component element instances
- load allowed realization types for each relevant element
- load current realization instances
- emit structured planning views and planning gaps
- build a planning payload suitable for downstream brief assembly

Derived test/proving contract is only partial.

What can be stated now:
- add unit tests for happy-path planning views
- add unit tests for missing-component and missing-taxonomy cases
- preserve repository boundary purity
- preserve stateless service behavior

What is still missing:
- a more explicit run-level proving contract tied to producer-side derivation governance
- structured verification-obligation linkage for this specific service slice

Status:
- `passed with manual authoring`

## Stage 8. Resolve change budget and anti-goals

What can be derived now:
- implementation should remain inside the service package plus tests
- the service should not mutate component-design records by default
- the service should not become a mini-orchestrator or persistence layer

Derived anti-goals:
- do not implement `Brief Assembly Service` here
- do not add raw SQL or direct DB access here
- do not broaden into `Workflow Lifecycle Service` or `Execution Package Resolution Service`
- do not silently create new taxonomy values from code without producer-side authority updates

Status:
- `passed with manual authoring`

## Stage 9. Compute brief-target sequencing

This is where the dry run exposed the most important new finding.

Expected normal behavior:
- derive ordered `coder_brief_realization_targets` from component element realizations
- express concrete implementation targets such as interface, implementation class, DTOs, tests, and supporting exports in sequence

What the current model supports well:
- repository-oriented realization targets such as:
  - `repository_interface`
  - `concrete_repository_class`
  - `dto`
  - `mapper`
  - `query_object`

What this service needs instead:
- a service contract / interface artifact
- a default service implementation artifact
- service request/response model artifacts
- a unit-test artifact
- possibly an export / package-surface artifact

Current taxonomy gap:
- the current seeded realization types do not yet include service-oriented artifact kinds such as:
  - `service_interface`
  - `service_implementation`
  - `test_module`
  - `package_export`

Consequence:
- we can describe the intended build sequence in prose
- we cannot yet encode that sequence faithfully in the current structured realization-target taxonomy without overloading repository-shaped labels

Provisional target sequence we want:
1. define the service interface contract in `contracts.py`
2. define planning request/response models in `models.py`
3. implement the default service in `default.py`
4. expose the public package surface in `__init__.py`
5. add unit tests in `test_component_design_planning_service.py`

Status:
- `blocked by taxonomy gap`

## Stage 10. Assemble draft coder brief

This stage succeeded.

Output artifact created in this phase:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-component-design-planning-service-draft-coder-run-brief.json`

Important rule:
- this artifact is a draft dry-run brief
- it is not approved execution authority

Status:
- `passed`

## Stage 11. Persist and approve brief

What the current system can do:
- persist coder briefs
- persist brief realization targets
- embed coder briefs into packet payloads

What is still weak for this slice:
- no real task-bound design package exists yet
- no review/approval history was executed for this dry run
- no brief realization targets can be cleanly persisted because the realization taxonomy is not yet expressive enough for this component type

Status:
- `not fully supported`

## Stage 12. Embed brief into architect packet

The current `materialize-coder-brief` and `materialize-architect-packet` surfaces are real and viable.

However they depend on:
- a persisted design package
- a persisted coder brief
- execution-eligible readiness

Because this dry run produced only a draft candidate brief and not an approved DB-backed brief, packet embedding was not attempted.

Status:
- `not attempted`

## Candidate Draft Brief

The dry-run candidate brief is saved at:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-component-design-planning-service-draft-coder-run-brief.json`

That artifact proves the method can already derive a concrete brief body for this service.

It does **not** prove that the current structured model can yet derive and persist the correct realization-target sequence for this service category.

## What This Dry Run Validates

The dry run validates these claims:
- the current PAA System Design is strong enough to derive a credible draft brief from reviewed component design
- the producer derivation subsystem now has a clear architectural home
- the current DB model is already close enough that the main remaining problems are targeted, not foundational
- the brief body shape itself is not the main blocker anymore

## What This Dry Run Invalidates

The dry run invalidates the idea that the current realization-target taxonomy is already general enough.

It is not.

It is strong for repository-shaped implementation slices.
It is not yet strong enough for service-shaped implementation slices.

That means the current model would still force drift or awkward label overloading during a real coder run for this service.

## Final Phase 6 Findings

### Finding 1. A real slice design package is still missing for this service run

We can dry-run derivation from notes.
We cannot yet perform a fully normal derivation cycle without materializing a real package/work-item/task identity for this slice.

### Finding 2. The draft brief body is derivable now

This is a real success.
The design and architecture are no longer too vague to produce concrete coder-agent instructions.

### Finding 3. The current realization taxonomy is incomplete for service implementation runs

This is the biggest new finding in this phase.

The system needs additional code-artifact target kinds for service-oriented implementation work.
At minimum, likely additions include:
- `service_interface`
- `service_implementation`
- `test_module`
- `package_export`

### Finding 4. Brief approval and persistence governance is still partially manual

The current system can store briefs and packet payloads.
But the explicit review-and-approval lifecycle for dry-run-to-approved-brief progression still needs stronger first-class handling.

## Phase 6 Verdict

The derivation method is valid enough to continue.

The current PAA system can already do this:
- `System Design -> Draft Coder Brief`

The current PAA system cannot yet do this cleanly for this service without refinement:
- `System Design -> Approved Structured Brief Targets -> Execution-Authoritative Packet`

That is exactly the kind of answer this phase was supposed to produce.

## Recommended follow-on for Phase 7

Feed these refinements back into the method and process record:
1. require explicit slice-package materialization before claiming a derivation is execution-authoritative
2. add a service-oriented code-artifact target extension to the realization taxonomy
3. make brief review and approval lifecycle state more explicit
4. distinguish clearly between:
   - draft derivation output
   - approved coder brief
   - packet-ready execution authority
