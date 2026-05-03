# 83. Component Dependency Graph Contract

## Purpose
This document defines the formal role of the component dependency graph in PAA.

The dependency graph is not just documentation.
It is an execution-governing artifact that determines:
- whether a slice is structurally ready for derivation
- which components must be designed before others
- which coder briefs may run first
- which briefs may run in parallel
- which briefs must wait for prerequisite components or surfaces

## Why this matters
Without a strong dependency graph, decomposition is still partially narrative.
That leads to familiar failure modes:
- coder briefs generated in the wrong order
- downstream slices trying to build on undefined component contracts
- hidden dependency creation during implementation
- parallel runs that conflict structurally
- QA discovering architectural incompleteness that should have been caught in design

A formal dependency graph lets us move from:
- component descriptions
to:
- executable structural sequencing

## Core principle
The dependency graph should be treated as a first-class Stage 1 design artifact.

It must be strong enough to answer:
- what depends on what
- what kind of dependency it is
- whether the dependency is design-time, implementation-time, runtime, or verification-time
- whether a component may be implemented before its dependency is complete
- whether two slices can proceed independently or in parallel

## Graph definition
A component dependency graph is a directed graph where:
- nodes are components
- edges are typed dependency relationships
- edge metadata defines sequencing and parallelism constraints

## Node definition
Each node must identify:
- `component_id`
- `component_name`
- `component_role`
- `system_layer`
- `tier` if relevant
- `status`
- `surface_set`

A node is not just a class or file.
It is an architecturally meaningful implementation unit.

## Required edge types
The graph must distinguish at least these dependency types.

### `depends_on_contract`
Meaning:
- component A requires component B's interface, contract, or semantic guarantees to be defined before A can be safely implemented

Typical consequence:
- B must be designed first
- A may not enter coder execution until B's contract is stable enough

### `depends_on_injection`
Meaning:
- component A expects component B or B's service to be injected or provided through an explicit dependency path

Typical consequence:
- B's dependency contract must exist before A's implementation brief is approved

### `depends_on_event`
Meaning:
- component A consumes events emitted by component B, or vice versa

Typical consequence:
- event shapes and emitter/consumer responsibilities must be stabilized before implementation of the dependent side

### `depends_on_state`
Meaning:
- component A relies on state managed, exposed, or transitioned by component B

Typical consequence:
- state ownership must be explicit before A is coded

### `depends_on_test_fixture`
Meaning:
- component A's implementation or verification depends on test fixtures or proving artifacts associated with component B

Typical consequence:
- test sequencing may lag design sequencing; QA and coder test contracts must account for it

### `depends_on_hosting`
Meaning:
- component A relies on hosting or integration surfaces provided by component B or a host boundary

Typical consequence:
- host contract and integration surfaces must be present before downstream implementation

## Optional edge attributes
Every dependency edge should eventually support attributes such as:
- `dependency_strength`
  - `hard`
  - `soft`
- `sequencing_requirement`
  - `must_precede`
  - `may_parallelize`
  - `must_follow_contract_only`
- `blocking_scope`
  - `design`
  - `derivation`
  - `execution`
  - `verification`
- `notes`

These make the graph operational instead of merely descriptive.

## Dependency graph outputs required in Stage 1
For a slice to be derivation-ready, Stage 1 should produce a local dependency graph slice containing:
- `primary_component`
- `supporting_components`
- `incoming_dependencies`
- `outgoing_dependencies`
- `blocking_dependencies`
- `parallelizable_dependencies`
- `dependency_edge_types`
- `contract-precedes-implementation` decisions

This is the graph slice relevant to the current work item, not necessarily the entire project graph.

## Dependency graph gates
The dependency graph must answer these gate questions before a coder brief is approved.

### Gate 1: Is the primary component structurally placeable?
If the primary component's role, layer, or dependency edges are ambiguous, derivation must stop.

### Gate 2: Are all hard upstream dependencies defined enough?
If a component has unresolved hard dependencies, its coder brief may not become active.

### Gate 3: Can the slice proceed independently?
If not, the graph must identify the prerequisite slice or predecessor brief.

### Gate 4: Can any part of the slice parallelize?
If yes, the graph must explicitly identify which dependent work packets are safe to run in parallel.

### Gate 5: Is any dependency being hidden inside implementation?
If a dependency exists but is not present in the graph, the Stage 1 package is under-specified.

## How the graph determines coder-brief sequencing
This is the central operational rule.

A coder brief should not be sequenced merely by issue order or roadmap order.
It should be sequenced by:
- authority task order
- plus dependency graph constraints

## Sequencing rules

### Rule 1: Hard prerequisites block execution
If component A has a hard `depends_on_contract` or `depends_on_injection` edge to component B, then:
- B's design package or coder brief must be approved first
- A cannot move to execution until B satisfies the relevant contract gate

### Rule 2: Contract completion may be enough
Sometimes A does not need B fully implemented.
It only needs:
- B's interface
- B's event shape
- B's injected contract

In that case the graph should mark:
- `must_follow_contract_only`

That allows more parallelism without design drift.

### Rule 3: Parallelism must be explicit
Two coder briefs may run in parallel only if the graph explicitly says their relationship is:
- independent
or
- `may_parallelize`

Parallelism should never be assumed from lack of information.

### Rule 4: Shared surface conflicts must stop parallelism
If two components share an edit surface or module boundary in a way that risks conflict, the graph should block parallel execution unless an explicit decomposition decision says otherwise.

### Rule 5: Verification dependencies also matter
A slice may look executable, but if its verification contract depends on upstream artifacts or fixtures that do not exist, the graph should block approval or downgrade readiness.

## Relationship to `coder_run_brief`
The dependency graph should directly influence these sections of the brief:
- `component_assignment`
- `collaboration_context`
- `dependency_contract`
- `change_budget`
- `anti_goals`

It should also drive additional brief metadata such as:
- prerequisite components
- prerequisite briefs
- safe parallel briefs
- blocking dependency edges

Those may belong in a future schema extension.

## Relationship to Stage 1 design package
The Stage 1 design package must include a dependency graph slice.

This means section 10 of the Stage 1 package should be strengthened from:
- component relationships and collaboration pattern

to also include:
- dependency graph slice
- typed dependency edges
- sequencing constraints
- parallelism constraints

## Relationship to PAA data model
The current Step 4 DB model already gives us a starting point:
- `paa.components`
- `paa.component_relationships`
- `paa.component_surfaces`

But to support sequencing strongly, we should extend the relationship model or add a dedicated dependency-layer model that captures:
- dependency edge type
- dependency strength
- sequencing requirement
- blocking scope
- contract completeness status

That will let PAA compute:
- next derivation-ready slice
- next execution-ready coder brief
- safe parallel execution sets

## Recommended minimal DB extension
A future extension should add either:
- more operational fields to `paa.component_relationships`
or
- a dedicated `paa.component_dependency_edges` table

Minimum useful fields:
- `from_component_id`
- `to_component_id`
- `dependency_type`
- `dependency_strength`
- `sequencing_requirement`
- `blocking_scope`
- `dependency_status`
- `notes`

## Suggested simple tools
The first useful graph-driven tools are:
- `check-component-dependency-completeness`
- `derive-brief-sequencing`
- `check-parallel-safety`
- `resolve-blocking-dependencies`
- `list-prerequisite-briefs`

These should answer concrete execution-order questions, not just visualize the graph.

## Readiness rules
A slice is not ready for Stage 2 derivation unless:
- the primary component is known
- its blocking dependencies are known
- its prerequisite contracts are known
- its parallel-safety status is known
- its shared-surface conflicts are known

A coder brief is not ready for Stage 3 execution unless:
- all hard blocking dependencies are satisfied
- all required upstream contracts are defined
- no unsanctioned shared-surface conflict exists

## Immediate implication
This changes how we should think about decomposition.

We are not only decomposing the system into components.
We are decomposing it into:
- components
- component contracts
- dependency edges
- execution order
- safe parallelism sets

That is what makes the system executable by autonomous coders instead of merely understandable to humans.

## Next step
The next useful move is:
- update the Stage 1 package contract so dependency graph slice is a first-class required section
- then define the concrete record shape or schema for that graph slice
