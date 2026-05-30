Title: Component Spec Section To Model Mapping Table
Doc-ID: paa-component-spec-section-to-model-mapping-table
Doc-Type: design-note
Status: active
Lifecycle-Stage: design
Created: 2026-05-20
Last-Edited: 2026-05-20
Author: Billy Weisberg
Repo: paa-platform
Component: PaaComponentSpecMapping
Domain: design-authority
Keywords: paa, component-spec, mapping, model, components, elements, realizations, implementation-plan, activities
Depends-On: 2026-05-20-component-spec-template-materialization-bridge.md, 2026-05-19-governed-code-backed-component-materialization-policy.md, 2026-05-17-implementation-plan-entity-design.md, 2026-05-17-implementation-plan-repository-contract.md, 2026-05-17-project-delivery-projection-contract.md
Supersedes: 
Superseded-By: 
Canonical: true
Review-After: 2026-06-20
Owners: 
Expires: 
Issue: 
PR: 
Authority-Source: 
Implementation-Status: defined
Summary: Maps governed Component Spec template sections to primary PAA model entities so the design-authority doc can drive materialization into executable model truth.

# Component Spec Section To Model Mapping Table

## Purpose

Make the bridge explicit from:
- `Component Spec` sections

to:
- primary PAA model entities
- downstream derivation surfaces

This table is the gap detector for whether a component spec is structurally able to drive model materialization.

## Section To Model Mapping

| Component Spec Section | Structured Fields Expected | Primary PAA Model Entity Or Surface | Materialization Action | Notes |
|---|---|---|---|---|
| Header | `Component`, `Domain`, `Doc-Type`, `Authority-Source`, `Implementation-Status` | governed doc index and downstream resolution context | identify spec, scope, and authority posture | supports discovery and governance, not direct DB row creation |
| Architecture Placement | `layer`, `stratum`, `tier` | `paa.components` | set component classification fields | should use controlled vocabulary |
| Role | concise role statement | supporting authority only | no direct materialization | remains narrative authority |
| Ownership Boundary | owned responsibilities list | code metadata, review criteria, plan scope | seed ownership metadata and plan scope | should not be inferred from prose elsewhere |
| Non-Ownership Boundary | excluded responsibilities list | review criteria and scope guardrails | seed non-ownership constraints | protects against god-component drift |
| Collaborators | collaborator component names and dependency roles | dependency graph, plan derivation context | seed collaborator references | should resolve to known governed component names when possible |
| Component Identity Table | `component_name`, `component_kind`, `alignment_state`, `system_layer`, `tier`, `status` | `paa.components` | create or reconcile component row | this is the component-row source section |
| Component Elements Table | `element_name`, `element_kind`, `description`, `owned_by_component` | `paa.component_elements` | create component elements | one row per stable element; current active `element_kind` vocabulary is intentionally narrow |
| Realizations Table | `element_name`, `realization_kind`, `artifact_kind`, `artifact_target`, `verification_role` | `paa.component_element_realizations` | create realizations and artifact targets | each realization should point back to one element |
| Plan Seed Table | `plan_name`, `consumer_context_key`, `primary_component_name`, `implementation_target_kind`, `plan_status` | `paa.implementation_plans` | create or seed implementation plan row | should attach to the active work-item and target context; current `plan_status` field seeds implementation-plan `authority_state` |
| Activity Seed Table | `activity_key`, `activity_name`, `sequence`, `activity_kind`, `element_name`, `realization_kind`, `done_definition` | `paa.implementation_plan_activities` | create implementation-plan activities | this is the main project-design bridge |
| Activity Dependency Table | `activity_key`, `depends_on_activity_key`, `dependency_kind` | activity dependency truth | create activity dependency rows | required for critical-path truth; current active dependency vocabulary is intentionally narrow |
| Verification Surface Table | `verification_surface`, `verification_kind`, `artifact_target`, `required_for_acceptance` | validation planning and projection surfaces | seed verification targets and acceptance expectations | can later bridge to validation records |
| Constraints And Non-Goals | constrained behaviors and excluded responsibilities | authority only first, later policy inputs | no direct materialization in v1 | remain explicit to prevent downstream invention |

## Materialization Priority

| Priority | Section | Why |
|---|---|---|
| P0 | Component Identity Table | no component row can be created without it |
| P0 | Component Elements Table | elements are required to create realizations and activity mappings |
| P0 | Realizations Table | realizations connect design to code artifacts |
| P0 | Plan Seed Table | implementation-plan truth needs an explicit root |
| P0 | Activity Seed Table | executable work structure depends on it |
| P0 | Activity Dependency Table | critical-path truth depends on it |
| P1 | Verification Surface Table | needed for acceptance and reporting durability |
| P1 | Ownership and Non-Ownership | needed to prevent scope drift during derivation |
| P2 | Role and narrative rationale | still valuable, but not primary materialization drivers |

## Gap Rule

If a section maps to a P0 materialization target and the section is missing or unstructured, the component spec is not ready to drive:
- component materialization
- implementation-plan derivation
- activity derivation

If a section uses a controlled field with a non-canonical active value, the component spec should also be treated as not materialization-ready even if the table is otherwise present.

## First Applied Use

Use this mapping table to refactor:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-workflow-lifecycle-service-component-spec.md`

into a template-conformant component spec that can drive materialization for:
- `paa.components`
- `paa.component_elements`
- `paa.component_element_realizations`
- `paa.implementation_plans`
- `paa.implementation_plan_activities`

## Summary

The `Component Spec` remains the human-centered design authority.

This mapping table defines the exact sections that must become structurally strict so the same doc can serve as the bridge into executable PAA model truth.
