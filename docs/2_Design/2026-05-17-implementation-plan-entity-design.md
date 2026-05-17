# Implementation Plan Entity Design

Date: 2026-05-17

## Purpose

Define `ImplementationPlan` as a first-class PAA data-model and architectural concept.

This note exists because the current PAA methodology now explicitly recognizes:
- `implementation-plan derivation`
- `Project Design`
- `Delivery Architect` ownership of the bridge from approved slice authority to coder briefing

That bridge should not remain only:
- a manual note
- a thread habit
- or an implied intermediate artifact

It needs a DB-backed model and explicit architectural ownership.

## Core Decision

`ImplementationPlan` is a primary PAA object.

It is:
- not the same thing as `Project`
- not the same thing as `ImplementationTarget`
- not the same thing as `CoderBrief`
- not a projection

It is the primary truth object for:
- `Project Design`
- consumer-specific implementation planning
- the final software-engineering bridge between approved design and coder execution

## Why This Object Matters

The current model already distinguishes:
- stable design authority
- slice-scoped design packages
- coder execution briefs
- runtime workflow and delivery state

What was still missing was the project-design object that answers:
- what exact build activities make up this slice in this consumer context?
- what artifacts are being constructed?
- what sequence should the build follow?
- what proving plan applies?
- what stack-specific details shape the implementation?

That object is `ImplementationPlan`.

Without it:
- coder briefing is under-specified
- consumer-specific variation is hidden
- the “Project” people want to see is forced to assemble itself from weaker surrogate objects

## Distinction Between `Project` And `ImplementationPlan`

### `Project`
`Project` remains the top-level product / engineering namespace.

Examples:
- `paa-platform`
- `fractal-core-python`

It owns:
- work items
- authority versions
- components
- design packages
- implementation plans

### `ImplementationPlan`
`ImplementationPlan` is one slice-scoped, consumer-aware build plan derived under `Project Design`.

It owns:
- consumer target context
- selected code-artifact set
- touch surfaces
- protected seams restated as implementation constraints
- dependency-aware build sequence
- proving and verification plan
- briefing inputs for one coder or worker lane

Important rule:
- many implementation plans may exist under one project
- the project is the namespace
- the implementation plan is the executable project-design unit

## Distinction Between `ImplementationTarget` And `ImplementationPlan`

### `ImplementationTarget`
`ImplementationTarget` is upstream design authority.

It describes:
- current gap
- desired state
- protected baseline
- expected touch surfaces
- out-of-scope items

It is still relatively architecture-facing and authority-facing.

### `ImplementationPlan`
`ImplementationPlan` is downstream project design.

It describes:
- what this consumer will actually build
- in what artifact forms
- in what order
- in which files/modules/projects
- with which tests and proving surfaces

Important rule:
- one `ImplementationTarget` may yield different `ImplementationPlan` records for different consumers or stacks

Examples:
- Python consumer
- .NET consumer
- same authority target, different implementation plans

## Distinction Between `ImplementationPlan` And `CoderBrief`

### `ImplementationPlan`
Primary project-design truth for a slice.

### `CoderBrief`
Execution-authority artifact derived from:
- slice package
- implementation plan
- code-artifact target taxonomy
- sequencing and readiness state

Important rule:
- the coder brief should be downstream from the implementation plan
- the coder brief should not be expected to invent it

## Proposed Domain Object

## `ImplementationPlan`

### Meaning
A consumer-specific, slice-scoped build plan derived from approved design authority and active slice packaging.

### Owns
- implementation-plan identity
- project and work-item binding
- design-package binding
- implementation-target binding
- consumer target context
- authoritative activity list
- build sequence
- proving contract
- plan status and approval state

### Key identity
- `implementation_plan_id`
- `project_id`
- `work_item_id`
- `design_package_id`
- optional consumer target key such as:
  - `python`
  - `.net`

### Important rule
This is a primary truth object for planning, not merely a rendered report.

## Proposed Supporting Objects

### `ImplementationPlanActivity`
Represents one build activity in the plan.

Examples:
- implement service interface
- implement DTO module
- implement service implementation
- add test module
- prepare package export

Important rule:
This is the authoritative project-activity list for the slice.

### `ImplementationPlanArtifact`
Represents one concrete code or build artifact produced or modified by one implementation-plan activity.

Examples:
- service interface module
- DTO module
- service implementation module
- test module
- package export surface

### `ImplementationPlanActivityDependency`
Represents one directed dependency edge between implementation-plan activities.

Examples:
- DTO before service implementation
- service implementation before package export
- service implementation before test module

### `ImplementationPlanVerificationSurface`
Represents one proving surface or verification obligation bound to the plan.

Examples:
- dedicated unit test module
- baseline test suite
- compile check
- protected-path validation

### `ImplementationPlanApproval`
Represents review and approval progression for the plan itself.

This may later be modeled as:
- dedicated rows
or:
- an event family

The key point is that implementation-plan review should be durable and queryable.

## Proposed DB Model

## 1. `paa.implementation_plans`

Primary record for project-design truth.

Suggested fields:
- `implementation_plan_id UUID PRIMARY KEY`
- `project_id UUID NOT NULL`
- `work_item_id UUID NOT NULL`
- `design_package_id UUID NOT NULL`
- `implementation_target_id UUID NOT NULL`
- `primary_component_id UUID`
- `consumer_context_key TEXT`
- `plan_title TEXT NOT NULL`
- `plan_kind TEXT`
- `plan_status TEXT`
- `authority_state TEXT`
- `build_sequence_json JSONB`
- `touch_surfaces_json JSONB`
- `protected_constraints_json JSONB`
- `verification_plan_json JSONB`
- `metadata_json JSONB`
- `created_by_role_id UUID`
- `created_by_agent_id UUID`
- `approved_at TIMESTAMPTZ`
- `created_at TIMESTAMPTZ`
- `updated_at TIMESTAMPTZ`

Important note:
- some of these JSON surfaces should probably normalize further over time
- but one primary root row is needed immediately

## 2. `paa.implementation_plan_activities`

One row per authoritative build activity in the plan.

Suggested fields:
- `implementation_plan_activity_id UUID PRIMARY KEY`
- `implementation_plan_id UUID NOT NULL`
- `component_element_id UUID`
- `component_element_realization_id UUID`
- `activity_key TEXT NOT NULL`
- `activity_title TEXT NOT NULL`
- `activity_kind TEXT NOT NULL`
- `sequence_order INTEGER`
- `activity_state TEXT NOT NULL`
- `target_path TEXT`
- `target_module TEXT`
- `blocking_reason TEXT`
- `started_at TIMESTAMPTZ`
- `completed_at TIMESTAMPTZ`
- `metadata_json JSONB`

Important note:
- this table is the primary answer to:
  - what are the project activities?
  - which one is current?
  - what comes next?
  - what is blocked?

## 3. `paa.implementation_plan_artifacts`

One row per selected artifact in the plan.

Suggested fields:
- `implementation_plan_artifact_id UUID PRIMARY KEY`
- `implementation_plan_id UUID NOT NULL`
- `implementation_plan_activity_id UUID`
- `component_element_id UUID`
- `component_element_realization_id UUID`
- `artifact_type_key TEXT NOT NULL`
- `artifact_title TEXT`
- `target_path TEXT`
- `sequence_order INTEGER`
- `status TEXT`
- `metadata_json JSONB`

## 4. `paa.implementation_plan_activity_dependencies`

Directed internal plan graph.

Suggested fields:
- `implementation_plan_activity_dependency_id UUID PRIMARY KEY`
- `implementation_plan_id UUID NOT NULL`
- `predecessor_activity_id UUID NOT NULL`
- `successor_activity_id UUID NOT NULL`
- `dependency_kind TEXT`
- `dependency_strength TEXT`
- `metadata_json JSONB`

## 5. `paa.implementation_plan_verification_surfaces`

Proving and validation surfaces for the plan.

Suggested fields:
- `implementation_plan_verification_surface_id UUID PRIMARY KEY`
- `implementation_plan_id UUID NOT NULL`
- `implementation_plan_activity_id UUID`
- `surface_kind TEXT NOT NULL`
- `surface_ref TEXT`
- `required BOOLEAN`
- `sequence_order INTEGER`
- `status TEXT`
- `metadata_json JSONB`

## Classification And Ownership

### Classification
`ImplementationPlan` should be classified as:
- `derivative_slice`

Reason:
- it is derived from approved authority
- it is slice-scoped
- it is primary truth for project design
- but it is not stable product authority like `spec_fragments` or `implementation_targets`

### Target semantic owner
This note proposes a new owner family:
- `Project Design And Delivery Planning`

Why:
- it is no longer correct to force this fully into `Authority Publication And Derivation`
- it is also not runtime-event truth
- and it is not merely reporting

This owner family is the architectural home of:
- `Delivery Architect`
- implementation-plan derivation
- consumer-specific project design

## Architectural Placement

This model implies one explicit subsystem/component family:
- `Project Design And Delivery Planning`

Likely component set:
- `Implementation Plan Derivation Service`
- `Implementation Plan Approval Service`
- `Implementation Plan Repository`
- `Project Build Projection Service`

Important rule:
- this family should sit between producer-side derivation and coder-brief execution authority
- it should not be collapsed into generic producer tooling

## Activity-Centric Truth Rule

The authoritative project activity list should live in:
- `paa.implementation_plan_activities`

The system should not infer the activity list only from:
- `CoderBrief`
- runtime queue packets
- report JSON
- freeform implementation-plan notes

Those can support execution and display.
They should not replace the primary activity list.

## Relationship To Projection

This is the key distinction:

### `ImplementationPlan` is not a projection
It is planning truth.

### The operator-facing “Project” view is a projection
What people typically want to see as:
- “the Project”
- “the build”
- “the current implementation plan”
- “what is blocked / next / in progress / done”

should be a projection derived from:
- implementation plans
- implementation-plan artifact status
- workflow state
- coder brief state
- runtime execution evidence
- acceptance events

That projection is a view of project delivery state.
It is not the same as the underlying implementation-plan records.

## Proposed Projection Family

Future projection family:
- `paa.project_delivery_projections`

Possible projection outputs:
- current slice plan state
- current activity
- next activity
- completed activity set
- blocked activity set
- critical path
- blocked artifact count
- approved vs executing vs complete plans
- per-consumer build status
- milestone rollups

This is likely the projection “everyone wants to see.”

But it must derive from real implementation-plan truth, not substitute for it.

## Immediate Design Consequences

The PAA model should now explicitly recognize:
1. `ImplementationPlan` as a primary project-design object
2. a DB model for implementation-plan truth
3. a new owner family for project-design / delivery-planning semantics
4. project-level delivery projections as downstream views over implementation-plan truth

## Recommendation

Before further large-scale coder-brief automation expands, the next design step should be:
1. add `ImplementationPlan` to the domain object model
2. add it to the stable table ownership/classification map
3. define the repository and service boundaries around it
4. then decide the first migration slice for the new DB family
