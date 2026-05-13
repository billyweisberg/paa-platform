# Component Design Repository Contract

Date: 2026-05-13

## Purpose

Define the first concrete Data Access Layer contract for the PAA system:
- `Component Design Repository`

This repository is the structured access boundary for the completed DB-primary Component Design model.

Its purpose is to give higher-level components a stable way to:
- read and write reusable Component Design records
- read and write derivative slice-design records
- access dependency and sequencing structure
- enforce normalization boundaries

without coupling runtime or design logic directly to raw tables.

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-data-access-layer-design.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-final-component-element-entity-design.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-component-design-normalization-rules.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-existing-component-design-model-audit.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-stable-table-classification-and-ownership-map.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/terminology/paa-engineering-terminology-glossary.md`

## Role

Provide structured access to:
1. stable reusable Component Design records
2. derivative slice-specific design artifacts
3. dependency and sequencing records derived from those artifacts
4. normalization and alignment state across the component-design layer

## Repository Boundary

The repository owns structured access to these DB tables:

### Stable component foundation
- `paa.components`
- `paa.component_surfaces`
- `paa.component_relationships`
- `paa.component_element_types`
- `paa.component_elements`
- `paa.component_element_type_realization_types`
- `paa.component_element_type_realization_types`
- `paa.component_element_realization_types`
- `paa.component_element_realizations`
- `paa.coder_brief_realization_targets`

### Derivative slice-design layer
- `paa.design_packages`
- `paa.design_package_signoffs`
- `paa.coder_run_briefs`

### Dependency and sequencing layer
- `paa.component_dependency_edges`
- `paa.coder_brief_sequence_states`

## Non-Goals

The repository does not:
- define workflow state or transitions
- own runtime event history
- publish authority packages
- interpret queue transport
- derive business semantics for acceptance or routing
- read repo-local report JSON as design truth

## Primary Consumers

The main consumers are:
- authority publication and derivation flows
- future PAA authority-authoring tools
- future Component Design tools
- future Component Design reports and projections
- `Runtime Lifecycle Engine` when it must resolve stable component or derivative slice context

## Canonical Read Models

The repository provides structured access to five logical read models.

### 1. Component Catalog View

Represents stable reusable component identity.

Includes:
- component identity
- role
- layer and tier
- description
- status
- stable metadata

Backed by:
- `paa.components`

### 2. Component Structure View

Represents the stable reusable structural definition of a component.

Includes:
- component surfaces
- component relationships
- component element taxonomy references
- component element instances
- allowed realization kinds
- concrete realization instances

Backed by:
- `paa.component_surfaces`
- `paa.component_relationships`
- `paa.component_element_types`
- `paa.component_elements`
- `paa.component_element_type_realization_types`
- `paa.component_element_type_realization_types`
- `paa.component_element_realization_types`
- `paa.component_element_realizations`
- `paa.coder_brief_realization_targets`

### 3. Design Package View

Represents derivative reviewed design state for a slice.

Includes:
- design package identity
- work-item linkage
- authority version linkage
- primary component linkage
- package status
- signoffs
- normalization state
- package payload JSON

Backed by:
- `paa.design_packages`
- `paa.design_package_signoffs`

### 4. Coder Brief View

Represents derivative execution-facing design state for a slice.

Includes:
- brief identity
- work-item linkage
- primary component linkage
- architecture constraints
- dependency contract
- behavioral contract
- test contract
- normalization state
- brief payload JSON

Backed by:
- `paa.coder_run_briefs`

### 5. Dependency And Sequencing View

Represents slice-derived dependency and readiness structure.

Includes:
- dependency edges
- dependency status
- sequencing requirement
- readiness state
- blocking cause
- parallel-group data

Backed by:
- `paa.component_dependency_edges`
- `paa.coder_brief_sequence_states`

## Required Repository Capabilities

## A. Stable Component Catalog Access

### Read capabilities
- get component by `component_id`
- get component by `(project_id, name)`
- list active components for a project
- list components by `system_layer`
- list components by `status`

### Write capabilities
- create component
- update component metadata and descriptive fields
- change component status

### Invariants
- component names are unique within a project
- reusable PAA system components must exist here before derivative slices may use them as stable primary components

## B. Component Surface And Relationship Access

### Read capabilities
- list component surfaces
- list primary surfaces for a component
- list outgoing relationships for a component
- list incoming relationships for a component

### Write capabilities
- register component surface
- update component surface responsibility and metadata
- register component relationship
- remove or supersede obsolete structural relationship

### Invariants
- a component surface is unique per `(component_id, surface_type, path)`
- stable structural relationships remain distinct from derivative dependency edges

## C. Component Element Taxonomy And Instance Access

### Read capabilities
- list all canonical component element types in sort order
- get element type by `element_key`
- list component elements for a component
- list component elements by element type
- get component element by `(component_id, component_element_type_id, element_key)`

### Write capabilities
- seed or upsert component element taxonomy
- create component element instance
- update component element definition and provenance
- change component element status
- seed or upsert component element realization taxonomy
- register allowed realization kinds for an element type
- create component element realization instance
- update component element realization definition and artifact refs
- create or update coder brief realization targets

### Invariants
- `component_element_types` is the standardized vocabulary for Component Elements
- `component_elements` must attach to stable component identity
- multi-instance element families use `element_key` for stable component-local identity
- derivative packages and briefs must not become the only place where a reusable Component Element exists
- a brief target that expects a concrete implementation artifact should resolve to a `component_element_realization`, not only a top-level element label

## D. Design Package Access

### Read capabilities
- get design package by `design_package_id`
- get active package for a `work_item_id`
- list design packages by `primary_component_id`
- list packages by normalization status
- list signoffs for a package

### Write capabilities
- create design package
- update package payload and provenance
- set package normalization status and notes
- record package signoff
- supersede prior package

### Invariants
- derivative package state may enrich stable component identity but may not replace it
- reusable-component slices must resolve `primary_component_id`, or explicitly declare transitional status

## E. Coder Brief Access

### Read capabilities
- get coder brief by `coder_run_brief_id`
- get active brief for a `work_item_id`
- list briefs by `primary_component_id`
- list briefs by normalization status
- resolve brief-targetable component element labels for a brief context
- list realization targets for a brief in execution order

### Write capabilities
- create coder brief
- update brief payload and generated-from provenance
- set brief normalization status and notes
- supersede prior brief

### Invariants
- a coder brief is derivative execution state, not stable component truth
- a brief may target a stable Component Element, but may not redefine the taxonomy

## F. Dependency And Sequencing Access

### Read capabilities
- list dependency edges for a design package
- list downstream dependencies for a component within a package
- list readiness records for a package or brief
- list execution-ready or blocked briefs

### Write capabilities
- create or update dependency edge
- update dependency status
- record or refresh readiness state projection

### Invariants
- `component_dependency_edges` remain derivative slice-level dependency truth unless explicitly promoted through architectural review
- readiness state is projection, not stable component authority

## Contract Shape

The repository should expose contract groups that reflect the actual data model rather than one monolithic bag of methods.

Recommended contract groups:
- `components`
- `component_structures`
- `component_elements`
- `design_packages`
- `coder_briefs`
- `dependencies`
- `sequencing`

This can still be implemented as one concrete repository component internally.

The important design rule is that consumers see explicit bounded access groups.

## Transaction Boundaries

The repository should support atomic write groups for these cases:

### Case 1: stable component registration
- create component
- register surfaces
- register relationships
- register initial component elements

### Case 2: design package publication
- create or supersede package
- update normalization fields
- persist signoffs

### Case 3: coder brief derivation
- create or supersede brief
- persist brief provenance
- refresh dependency or readiness records when part of the same derivation unit

### Case 4: component-design repair
- repair missing stable component identity
- backfill component elements
- update package or brief normalization state from transitional to normalized

## Prohibited Access Patterns

Consumers of this repository must not:
- read `package_json` or `brief_json` directly from raw SQL while also relying on repository-normalized stable component records in the same lifecycle path
- infer stable Component Elements from prose or package JSON when normalized `component_elements` exist
- treat readiness records as stable component-definition truth
- bypass the repository to update normalization state ad hoc

## Reporting Implication

This repository is the data source for future Component Design reports such as:
- stable component catalog reports
- component-element completeness reports
- primary-component normalization drift reports
- per-component dependency and sequencing reports
- brief-target coverage reports

Those reporting tools should query through this repository or through a projection layer built from it.

## Final Conclusion

The `Component Design Repository` is the first DAL contract because it sits at the exact boundary we just completed in the DB model.

It gives PAA a structured access layer for:
- stable component identity
- stable Component Elements
- derivative packages and briefs
- dependency and readiness structure

That is the correct foundation for DAL work because it removes the need to treat:
- package JSON
- brief JSON
- scattered prose labels
- raw table joins

as the primary way to access Component Design truth.
