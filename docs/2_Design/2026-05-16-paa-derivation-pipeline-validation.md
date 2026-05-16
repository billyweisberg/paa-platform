# PAA Derivation Pipeline Validation

Date: 2026-05-16
Phase: `Phase 1. Reconstruct And Normalize The Derivation Pipeline`
Plan: `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-16-paa-derivation-method-validation-plan.md`

## Purpose

Reconstruct and normalize the end-to-end derivation pipeline that turns reviewed System Design into coder-agent execution authority.

This note treats the existing coder-brief derivation documents as the current authority baseline, then organizes them into one coherent pipeline so later phases can test:
- whether current System Design outputs satisfy derivation inputs
- whether the DB/data model can manage derivation state
- whether the architecture and producer-side tooling model can actually support the derivation process in reality

This is the direct validation target for the core PAA transformation:
- `System Design -> Agent Team -> Functioning Software System`

## Source notes reviewed

Primary derivation notes:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-coder-brief-derivation-method.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-coder-brief-field-derivation-matrix.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-coder-brief-sequencing.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-coder-run-brief-packet-integration.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-coder-run-brief.md`

Contextual system-design notes used only to normalize terminology and current architecture intent:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-authority-package-authoring-process.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-layered-architecture-proposal.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-layered-component-dependency-graph.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-domain-object-model-and-oo-component-decomposition.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-component-design-planning-service-component-spec.md`

## Phase 1 conclusion

The existing derivation notes do define one coherent end-to-end pipeline.

However, that pipeline is currently spread across five documents that each describe a different slice of the flow:
- artifact definition
- field derivation rules
- stage pipeline
- sequencing/readiness computation
- execution packet integration

The pipeline is therefore recoverable, but not yet normalized into one operational view.

This note provides that normalized view.

## The normalized derivation pipeline

The derivation pipeline is best understood as 13 ordered stages, including the upstream Stage 0 authority gate.

### Stage 0. Approve upstream System Design authority

Purpose:
- establish the reviewed design authority that derivation is allowed to consume

Required upstream authority:
- product / architect / designer authority
- spec fragments
- implementation targets
- component model
- architectural constraints
- authority task definition
- verification obligations

Result:
- reviewed Stage 1 design authority exists for the slice

This stage is upstream of the coder-brief notes, but the derivation method assumes it is already complete.

### Stage 1. Materialize the active slice design package

Purpose:
- assemble the exact design package for the active task or work item

Inputs:
- authority version
- task id
- work item identity
- linked spec fragment
- linked implementation target
- linked design decisions
- linked component entries
- linked verification obligations

Result:
- active slice package

This is the entry gate into derivation.
Without this package, there is nothing stable to derive from.

### Stage 2. Check derivation readiness

Purpose:
- determine whether the slice is ready to enter derivation at all

Required gate conditions:
- Stage 1 package is complete
- required architectural constraints exist
- required signoffs are present
- dependency graph slice exists
- package status is approved for derivation

Failure outcome:
- `not_derivation_ready`

Success outcome:
- the slice may proceed into coder-brief derivation

This stage is implied across the method and sequencing notes, but it should be treated as a distinct gate.

### Stage 3. Resolve top-level identity and authority context

Purpose:
- establish the brief identity and its binding to project authority

Derived scope includes:
- authority version
- project id
- initiative, milestone, phase, task
- work item identity
- issue or PR linkage if already materialized
- canonical slice name
- authorized delta family
- out-of-scope delta families

Result:
- top-level brief identity and scope context

This comes from the field derivation matrix and is the root context for all later sections.

### Stage 4. Resolve primary component assignment

Purpose:
- assign exactly one primary implementation component for the run

Inputs:
- spec fragment
- implementation target
- component model
- design decisions

Outputs:
- primary component
- supporting components
- component role
- system layer
- optional tier

Rule:
- every coder brief must have exactly one primary implementation component

This is the most important construction-binding decision in the derivation method.

### Stage 5. Resolve component scope and placement boundaries

Purpose:
- convert the component assignment into concrete edit and placement boundaries

Inputs:
- component surfaces
- expected touch surfaces
- implementation target desired state
- target module boundaries
- required architecture seams
- forbidden growth patterns

Outputs:
- component aspects in scope
- target modules
- allowed edit surfaces
- forbidden edit surfaces
- target module boundaries
- required seams

This is where the derivation process protects structure and prevents convenience-driven module growth.

### Stage 6. Resolve local collaboration and dependency contracts

Purpose:
- define the local construction context the coder is allowed to operate within

Inputs:
- component relationships
- pattern definitions
- sequence or activity views
- constructor and setup model
- configuration contracts

Outputs:
- collaboration pattern
- collaborating components
- callers and callees
- event emitters and event consumers where relevant
- dependencies to inject
- runtime inputs
- configuration inputs
- forbidden hidden dependencies

This stage tells the coder how the component is expected to collaborate, without asking the coder to rediscover architecture from the codebase.

### Stage 7. Resolve behavioral and proving contracts

Purpose:
- translate semantic design authority into implementation-operational requirements

Inputs:
- spec fragment
- implementation target
- requirements
- design decisions
- verification obligations
- protected baseline rules
- artifact expectations

Outputs:
- behavior to add or change
- invariants to preserve
- edge cases
- error conditions
- tests to run
- tests to add or update
- protected baseline checks
- expected artifacts

This is the point where semantic intent becomes coding behavior and proving requirements.

### Stage 8. Resolve change budget and anti-goals

Purpose:
- constrain the implementation run so the coder does not expand scope or drift structurally

Inputs:
- implementation target
- architectural constraints
- prior failure history
- prior rejection history if any

Outputs:
- max responsibility expansion
- expected touch surfaces
- pre-handoff scope checks
- anti-goals
- common failure modes

This stage is essential because it converts past failure patterns into explicit execution constraints.

### Stage 9. Compute sequencing and execution readiness

Purpose:
- attach dependency and scheduling authority to the derived brief

Inputs:
- approved Stage 1 design package
- authority task order
- component dependency graph
- package signoff state
- dependency status state
- shared-surface conflict metadata
- active coder briefs
- active execution records

Outputs:
- readiness class
- dependency readiness
- prerequisite briefs
- blocking dependency edges
- shared-surface conflicts
- parallel-safe peers or parallel group id
- blocking causes
- recommended next owner
- readiness snapshot source

This stage is not optional scheduling commentary.
It is part of coder-execution authority.
Once derivation is complete, sequencing state must be attached to the brief itself.

### Stage 10. Assemble, validate, and approve the coder brief

Purpose:
- consolidate the derivation outputs into one approved execution artifact

Inputs:
- outputs of Stages 3 through 9

Validation gates:
- schema validation
- architecture review
- scope review
- test-contract review
- packet-readiness review
- required role signoff by authored or validated field families

Outputs:
- draft `coder_run_brief`
- approved `coder_run_brief`

This is the point where authored, inferred, validated, and enriched values are frozen into execution authority.

### Stage 11. Persist the approved brief with provenance

Purpose:
- make the approved brief durable, reviewable, and traceable

Persisted information should include:
- approved brief content
- authority version binding
- source record provenance
- derivation status by field or section
- reviewer identity
- signoff status
- generation timestamp
- readiness snapshot

The existing derivation notes clearly expect provenance preservation, even if the full persistence model is not yet specified in one place.

### Stage 12. Embed the brief into the architect packet for execution

Purpose:
- convert approved derivation output into queue-transport execution authority

Outputs inside `architect_cycle_packet.payload`:
- `coder_run_brief_ref`
- embedded full `coder_run_brief`

Consumption rule:
- the coding lane must consume the embedded brief first
- the reference remains for auditing, traceability, regeneration, and review

This is the bridge from derivation into actual coder execution.

## Classification model across the pipeline

The derivation method defines four derivation statuses:
- `authored`
- `inferred`
- `validated`
- `enriched`

Those statuses are best understood as cross-cutting field provenance categories, not pipeline stages.

### `authored`
- direct authority input from Product Owner, Architect, or Project Designer
- should not be guessed downstream

### `inferred`
- mechanically derived from structured records
- should be reproducible from live system state

### `validated`
- drafted or inferred, then explicitly reviewed before approval
- this is where design authority prevents silent bad inference

### `enriched`
- execution-helpful context added later, often by TechLead or tooling
- must never override authored authority

Important normalization rule:
- the pipeline stage and the derivation status are different dimensions
- one pipeline stage may produce fields from more than one derivation status class

## Role of each existing derivation note

Each existing note has a clear role once the pipeline is normalized.

### `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-coder-run-brief.md`
Role:
- defines the target artifact and its minimum authority fields

### `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-coder-brief-derivation-method.md`
Role:
- defines the stage pipeline and derivation philosophy

### `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-coder-brief-field-derivation-matrix.md`
Role:
- defines field-level provenance, signoff, and derivation rules

### `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-coder-brief-sequencing.md`
Role:
- defines readiness, blocking, and safe execution ordering as part of coder authority

### `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-coder-run-brief-packet-integration.md`
Role:
- defines the handoff from approved brief to executable transport packet

## Ambiguities and overlaps found in Phase 1

The derivation notes are directionally coherent, but several ambiguities remain.

### 1. The entry gate into derivation is implied, not explicit enough

The method assumes a complete Stage 1 package exists.
The sequencing note assumes package approval and dependency graph presence.
The field matrix assumes task and component authority have already been resolved.

What is missing:
- one explicit derivation-entry contract stating exactly what must exist before Stage 2 derivation begins

### 2. Sequencing is treated as adjacent, but is actually part of derivation output

The sequencing note correctly says readiness should attach to each derived brief.
However, in the note set overall, sequencing can still read like a separate planning subsystem.

What should be normalized:
- sequencing and execution readiness are not external commentary
- they are part of coder-facing execution authority

### 3. Persistence and provenance are expected, but not normalized as a dedicated pipeline stage

The derivation method says provenance should live in PAA.
The field matrix implies field-level provenance.
The packet integration note assumes a durable authoritative brief exists.

What is missing:
- one explicit persistence stage that freezes approved brief content and derivation provenance before packet embedding

### 4. The current derivation notes still speak in older component-model terms

The current notes rely on:
- component model
- component surfaces
- component relationships
- implementation target

Those are still valid, but the system now also has newer structured concepts that are not yet reflected in the derivation notes:
- component element types
- component elements
- code artifact types
- component element realizations
- coder brief realization targets

What this means:
- the old derivation notes are still usable
- but they are not yet aligned to the newer component-design and brief-target model we have now established

### 5. The pipeline does not yet separate section-level derivation from code-artifact-target derivation

The existing notes explain how to derive a coder brief.
They do not yet clearly explain how to derive:
- specific code artifact targets
- specific target sequencing within a run or across runs
- implementation forms such as repository interface before concrete repository class

That is now a real need in the system.

### 6. The current notes do not yet define a normalized derivation-state lifecycle

They define field statuses and readiness classes, but not one unified derivation-state lifecycle such as:
- design package approved
- derivation ready
- derivation in progress
- derivation blocked
- derivation complete pending review
- brief approved
- packet embedded
- execution authority active

This is likely needed for explicit process-state management in the DB.

## Proposed document updates from Phase 1

These are document refinements implied by this normalization pass.
No implementation is implied yet.

### Update 1. Add one normalized derivation-pipeline view

Either:
- add a new canonical pipeline section to `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-coder-brief-derivation-method.md`

Or:
- treat this validation note as the canonical Phase 1 normalized pipeline and cross-link it from the derivation method

### Update 2. Add an explicit derivation-entry contract

Define the exact design package and signoff prerequisites required before a slice may enter derivation.

### Update 3. Normalize sequencing as part of derivation output authority

Strengthen the wording that:
- sequencing state
- dependency blockers
- shared-surface conflict state
- parallel-safe state

are part of the coder-facing brief authority, not merely scheduling metadata.

### Update 4. Extend derivation docs to include the newer component-design structures

The derivation model should be updated to use the newer structured vocabulary where appropriate:
- component elements
- code artifact types
- component element realizations
- brief realization targets

This is especially important if derivation is expected to produce implementation-target instructions precise enough for autonomous coder runs.

### Update 5. Add a derivation-state lifecycle note or section

The process now likely needs an explicit derivation-state model that complements:
- field derivation statuses
- brief sequencing readiness classes
- packet execution state

This will likely be needed for later DB-state validation.

## Phase 1 validation result

### What is validated

The existing derivation notes do support one coherent end-to-end interpretation of the pipeline.

The normalized flow is:
1. approve upstream System Design authority
2. materialize the active slice design package
3. check derivation readiness
4. resolve top-level identity and scope
5. resolve primary component assignment
6. resolve scope and placement boundaries
7. resolve collaboration and dependency contracts
8. resolve behavioral and proving contracts
9. resolve change budget and anti-goals
10. compute sequencing and readiness
11. assemble, validate, and approve the brief
12. persist the approved brief with provenance
13. embed the brief into the architect packet for execution

### What is not yet fully validated

Phase 1 does not yet prove:
- that current System Design artifacts provide all required derivation inputs
- that the DB/data model is complete for derivation-state management
- that the architecture and tooling model fully support the process operationally

Those remain the targets of later phases.

## Exit criteria check

Phase 1 exit criteria were:
- one coherent derivation pipeline can be stated end to end
- each existing derivation note has a clear role in that pipeline

Result:
- satisfied

## Recommendation for Phase 2

Proceed to:
- map current System Design outputs for `Component Design Planning Service` to the normalized derivation inputs

The immediate goal of Phase 2 should be to determine whether the current System Design and component-spec outputs are sufficient to drive this derivation pipeline without architectural guessing.
