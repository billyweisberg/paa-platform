# Component Design Repository Implementation Plan

Date: 2026-05-13

## Purpose

Sequence the first implementation work for the `Component Design Repository` after the DB model and repository contracts were completed.

This plan exists to make the first code implementation disciplined instead of drifting into one-off queries.

## Design Authority

Use these notes as authority for this plan:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-component-design-repository-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-final-component-element-entity-design.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-component-element-realization-model.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-component-design-normalization-rules.md`

## Implementation Goal

Deliver the first code-level repository interface and concrete implementation for the Component Design data boundary.

The first implementation slice must cover:
- stable component identity access
- component element taxonomy access
- component element instance access
- realization taxonomy access
- realization instance access
- brief realization target access

## Phase Order

### Phase 1: interface and concrete repository shell
- define the code-level repository interface
- define stable record DTOs or dataclasses
- create the Postgres-backed concrete repository class

### Phase 2: stable component and element reads
- component lookup by project/name
- component-element-type listing
- component-element listing for a component

### Phase 3: realization reads
- realization-type listing
- allowed realization lookup for an element type
- realization-instance listing for a component element

### Phase 4: brief-target reads
- brief realization target listing in execution order
- dependency ordering resolution through `depends_on_target_id`

### Phase 5: write-path expansion
- add creation and update methods once the read boundary proves stable

## Required Access Groups

The first implementation must expose these access groups explicitly:
- `components`
- `component_elements`
- `realization_types`
- `realizations`
- `brief_targets`

The goal is to make it impossible for callers to miss the realization layer.

## First Concrete Operations

The first implementation slice should provide at minimum:
- `get_component_by_name(project_id, name)`
- `list_component_element_types()`
- `list_component_elements_for_component(component_id)`
- `list_realization_types_for_element_type(element_type_key)`
- `list_realizations_for_component_element(component_element_id)`
- `list_brief_realization_targets(coder_run_brief_id)`

## Important Constraint

The first implementation is allowed to be read-focused.

That is acceptable because the immediate goal is to establish the repository boundary and remove ad hoc query behavior for the new Component Element and realization structures.

## Anti-Goals

Do not in the first slice:
- implement every contract method at once
- add business semantics into the repository
- let callers fall back to raw SQL for the realization layer
- model brief realization targets only through JSON parsing when DB rows exist

## Success Criteria

This plan is successful when:
1. a code-level `ComponentDesignRepository` interface exists
2. a concrete Postgres implementation exists
3. the implementation can read realization taxonomy, realization instances, and brief realization targets through the repository boundary
4. no realization-layer reads require direct raw SQL in callers
