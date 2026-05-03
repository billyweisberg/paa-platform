# 82. Stage 1 Design Package Contract

## Purpose
This document defines the exact formal shape of the Stage 1 design package.

It is the required upstream package that must exist before Stage 2 derivation may begin.

This artifact closes the gap between:
- broad project authority
- slice-level design intent
- repeatable coder-brief derivation

Without a formal Stage 1 package, derivation stays bespoke and coder briefs remain partially improvised.

## Position in the lifecycle
This contract belongs to:
- Stage 1: Design / Authoring

It is consumed by:
- Stage 2: Derivation

It is upstream of:
- `coder_run_brief`
- `architect_cycle_packet`
- execution handoff

## Core principle
Stage 1 should not merely produce scattered documents.
It should produce one coherent design package for a slice.

That package is the reviewed design authority bundle that says:
- what this slice is
- why it exists
- where it belongs in the system
- what it may and may not change
- what component structure it must preserve
- what evidence will later prove it was implemented correctly

## Design package definition
A Stage 1 design package is the complete set of records required to derive one execution-ready implementation slice.

Each design package must be:
- slice-scoped
- authority-versioned
- component-linked
- reviewable
- derivation-ready

## Required package sections
A Stage 1 design package must contain the following sections.

### 1. Authority context
Purpose:
- identify the exact place of the slice in project authority

Required fields:
- `project_id`
- `project_slug`
- `authority_version`
- `milestone_id`
- `phase_id`
- `task_id`
- `task_title`
- `predecessor_tasks`
- `allowed_successors`
- `issue_number` if materialized

Owned by:
- Architect

Gate rule:
- the slice must be identifiable as one and only one active authority task

### 2. Product and source basis
Purpose:
- anchor the slice in product truth and source authority

Required fields:
- `source_artifacts`
- `source_statements`
- `product_outcome_statement`
- `protected_product_truths`
- `roadmap_context`

Owned by:
- Product Owner
- Architect

Gate rule:
- the package must show why this slice exists, not only how to code it

### 3. Requirement set
Purpose:
- state the reviewed requirement obligations for the slice

Required fields:
- `requirements`
- `requirement_sources`
- `requirement_status`

Owned by:
- Product Owner
- Architect

Gate rule:
- every requirement included in the package must be tied to at least one source statement

### 4. Design decision set
Purpose:
- state the architectural or design choices that shape the slice

Required fields:
- `design_decisions`
- `decision_requirements`
- `decision_rationale`
- `decision_status`

Owned by:
- Architect
- Project Designer

Gate rule:
- the package must include the decisions required to prevent coder-side architectural invention

### 5. Spec fragment
Purpose:
- define the bounded canonical slice being authorized

Required fields:
- `spec_fragment_id`
- `spec_fragment_title`
- `canonical_statement`
- `fragment_kind`
- `authorized_delta_family`
- `out_of_scope_delta_families`
- `fragment_status`

Owned by:
- Architect

Gate rule:
- the fragment must define one bounded change family and name adjacent families that remain out of scope

### 6. Implementation target
Purpose:
- translate the fragment into practical implementation shape

Required fields:
- `implementation_target_id`
- `current_gap`
- `desired_state`
- `protected_baseline`
- `expected_touch_surfaces`
- `pre_handoff_scope_checks`
- `out_of_scope_items`
- `risk_level`
- `target_status`

Owned by:
- Architect
- Project Designer

Gate rule:
- the implementation target must make execution shape explicit enough that derivation can proceed without guessing scope

### 7. Architectural authority constraints
Purpose:
- prevent structural drift during implementation

Required fields:
- `required_architecture_seams`
- `target_module_boundaries`
- `max_responsibility_expansion`
- `forbidden_module_growth_patterns`
- `forbidden_dependency_shortcuts`
- `architectural_anti_goals`

Owned by:
- Architect

Gate rule:
- these constraints must be explicit before any coder brief is generated

### 8. Component model slice
Purpose:
- provide the structural construction context for derivation

Required fields:
- `primary_component`
- `supporting_components`
- `component_roles`
- `system_layers`
- `tiers` if relevant
- `component_status`

Owned by:
- Project Designer
- Architect

Gate rule:
- one and only one primary component must be assigned for the slice

### 9. Component surfaces
Purpose:
- define the concrete surfaces attached to the involved components

Required fields:
- `component_surfaces`
  - modules
  - tests
  - docs
  - config
  - contracts
  - integration surfaces
  - event surfaces
- `surface_responsibilities`
- `primary_surfaces`

Owned by:
- Project Designer

Gate rule:
- surfaces must be concrete enough that edit boundaries can later be derived mechanically

### 10. Component relationships, collaboration pattern, and dependency graph slice
Purpose:
- define the local architecture context the coder will be working inside
- define the dependency structure that governs derivation and execution order

Required fields:
- `component_relationships`
- `local_collaboration_pattern`
- `callers`
- `callees`
- `event_emitters`
- `event_consumers`
- `dependency_edges`
- `blocking_dependencies`
- `parallelizable_dependencies`
- `sequencing_constraints`

Owned by:
- Project Designer
- Architect

Gate rule:
- the package must include the local collaboration shape and a typed dependency graph slice strong enough to determine coder-brief sequencing

### 11. Verification contract basis
Purpose:
- define what later verification and testing will depend on

Required fields:
- `verification_obligations`
- `obligation_types`
- `pass_criteria`
- `expected_artifacts`
- `protected_baseline_checks`

Owned by:
- Architect
- TechLead

Gate rule:
- verification must be designed before coding, not reconstructed after implementation

### 12. Failure and recovery context
Purpose:
- capture known failure patterns or recovery concerns before execution begins

Required fields:
- `known_failure_modes`
- `contamination_risks`
- `recovery_hints`
- `loop_stop_conditions`

Owned by:
- TechLead
- Architect

Gate rule:
- if the slice is known to be easy to contaminate or decompose poorly, the package must say so explicitly

## Package statuses
A Stage 1 design package should move through these statuses:
- `draft`
- `under_review`
- `approved_for_derivation`
- `superseded`
- `rejected`

Only `approved_for_derivation` may enter Stage 2.

## Minimum completeness test
A Stage 1 package is not derivation-ready unless all of the following are true:
- authority context is complete
- source and product basis are present
- at least one reviewed requirement exists
- at least one reviewed design decision exists
- one canonical spec fragment exists
- one implementation target exists
- architectural constraints are explicit
- exactly one primary component is assigned
- component surfaces are mapped
- collaboration pattern is explicit
- dependency graph slice and sequencing constraints are explicit
- verification obligations are explicit
- protected baseline is explicit
- out-of-scope delta families are explicit

## Derivation readiness gate
A Stage 1 package is ready for Stage 2 only when all of the following are true:
- `status = approved_for_derivation`
- Architect signoff is present
- Product Owner signoff is present where product truths or invariants are involved
- Project Designer signoff is present for component placement and collaboration structure
- TechLead signoff is present for verification practicality or recovery-sensitive slices

## Signs the package is still under-specified
Do not move to derivation if any of these are true:
- the slice names a semantic change but no primary component
- the package references a broad diagram but no local collaboration pattern
- expected touch surfaces are vague or missing
- out-of-scope delta families are not named
- architectural seams are implied rather than explicit
- verification obligations exist, but protected baseline checks are not named
- component surfaces are not mapped to real modules or contracts
- the package would force a coder to decide where the responsibility belongs

## Recommended package representation in PAA
The package should eventually be persisted as a first-class artifact family in PAA.

Minimum DB direction:
- keep stable records normalized:
  - authority task
  - requirements
  - design decisions
  - spec fragments
  - implementation targets
  - components
  - surfaces
  - relationships
  - verification obligations
- add a package artifact that records:
  - package version
  - status
  - assembled package JSON
  - signoff state
  - provenance

## Relationship to coder brief derivation
The Stage 1 package is the full reviewed upstream bundle.
The `coder_run_brief` is a downstream derived construction brief.

The package is richer than the brief.
The brief is narrower than the package.

The package answers:
- what this slice means in the project and architecture

The brief answers:
- what the coder must build in this run

## Suggested simple tools
To support this stage, the first useful tools are:
- `check-design-package-completeness`
- `resolve-primary-component-gaps`
- `check-surface-mapping-completeness`
- `check-derivation-readiness`
- `assemble-design-package`

These should be small review/support tools, not autonomous design substitutes.

## Immediate next step
The next useful design step is:
- define a concrete package schema or record shape for Stage 1

That schema should be the direct parent of `coder_run_brief` derivation.
