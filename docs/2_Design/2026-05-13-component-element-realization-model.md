# Component Element Realization Model

Date: 2026-05-13

## Purpose

Define the second-level taxonomy and instance model for **Component Element Realizations**.

This note exists because top-level `Component Elements` are not specific enough to constrain autonomous coding runs safely.

A coder brief that says only:
- `Interfaces` for `Workflow State Repository`

still leaves too much room for drift.

The system needs to say more precisely:
- implement `repository_interface`
- then implement `concrete_repository_class`

That precision belongs in structured DB-backed design data, not only in prose.

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/terminology/paa-engineering-terminology-glossary.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-final-component-element-entity-design.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-component-design-repository-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-db-model-diagram-and-gap-analysis.md`

## Design Decision

PAA keeps the existing two-level Component Design foundation:
1. `Component`
2. `Component Element`

And adds a third level:
3. `Component Element Realization`

This third level is how we constrain what a coder agent is actually expected to build.

## Why This Model Is Needed

Top-level `Component Elements` answer:
- what design concern is being specified

They do **not** answer:
- what concrete implementation artifact should be produced

That gap is what allows coder-agent drift.

Examples:
- `Interfaces` could mean many things
- `Functions` could mean helper methods, query objects, or a concrete class
- `Data Contract` could mean a DTO, a schema file, or both

The realization model closes that ambiguity.

## Final Entity Model

PAA adds four DB-backed entities.

### 1. `paa.component_element_realization_types`

Reference taxonomy for concrete realization kinds.

Examples:
- `repository_interface`
- `service_interface`
- `concrete_repository_class`
- `service_implementation`
- `dto`
- `mapper`
- `query_object`
- `event_handler`
- `test_module`
- `policy_adapter`
- `package_export`
- `projection_view`
- `schema_definition`

### 2. `paa.component_element_type_realization_types`

Allowed-mapping table between:
- top-level `component_element_types`
- allowed `component_element_realization_types`

This is the policy layer that says, for example:
- `Interfaces` may be realized as `repository_interface`
- `Functions` may be realized as `concrete_repository_class`
- `Data Contract` may be realized as `dto`

### 3. `paa.component_element_realizations`

Per-component, per-element realization instances.

Each row says:
- this `Component Element` has this concrete realization artifact
- here is its stable key, status, definition, and artifact linkage

### 4. `paa.coder_brief_realization_targets`

Explicit brief-target table tying a brief to one or more realization instances.

Each row says:
- for this brief
- target this concrete realization
- with this intent
- in this sequence
- optionally after this other target

This is the table that supports ordered instructions like:
1. implement `repository_interface`
2. then implement `concrete_repository_class`

## Hierarchy

The final hierarchy is:
- `Component`
- `Component Element`
- `Component Element Realization`
- `Coder Brief Realization Target`

That gives us:
- stable architecture identity
- stable design concern identity
- stable implementation-artifact identity
- stable run-target identity

## Realization Types Are Not Top-Level Component Elements

This is an important rule.

These are **not** top-level Component Elements:
- `repository_interface`
- `concrete_repository_class`

They are realization kinds.

That keeps the top-level taxonomy clean while still giving autonomous runs the specificity they need.

## Final Field Model

## `paa.component_element_realization_types`

Purpose:
- standardized vocabulary for concrete implementation artifact kinds

Core fields:
- `component_element_realization_type_id`
- `realization_key`
- `label`
- `category`
- `description`
- `is_brief_targetable`
- `is_multi_instance`
- `sort_order`
- `metadata_json`

## `paa.component_element_type_realization_types`

Purpose:
- constrain which realization kinds are valid for which top-level Component Elements

Core fields:
- `component_element_type_realization_type_id`
- `component_element_type_id`
- `component_element_realization_type_id`
- `is_default`
- `sort_order`
- `metadata_json`

## `paa.component_element_realizations`

Purpose:
- stable per-component realization instances

Core fields:
- `component_element_realization_id`
- `project_id`
- `component_id`
- `component_element_id`
- `component_element_realization_type_id`
- `realization_key`
- `title`
- `status`
- `sequence_order`
- `definition_json`
- `artifact_ref_json`
- `provenance_json`
- `metadata_json`
- `created_by_role_id`
- `created_by_agent_id`
- `created_at`
- `updated_at`

## `paa.coder_brief_realization_targets`

Purpose:
- explicit brief-time targeting of concrete realization artifacts

Core fields:
- `coder_brief_realization_target_id`
- `project_id`
- `work_item_id`
- `coder_run_brief_id`
- `component_id`
- `component_element_id`
- `component_element_realization_id`
- `depends_on_target_id`
- `target_intent`
- `sequence_order`
- `is_required`
- `target_notes`
- `target_contract_json`
- `metadata_json`
- `created_at`

## Key Invariants

1. a `Component Element Realization` must always belong to a stable `component_element`
2. a brief target must always resolve to one concrete realization instance
3. allowed realization kinds are constrained by `component_element_type_realization_types`
4. sequence and dependency between brief targets must be explicit in structured fields, not only implied in prose
5. a coder brief may target multiple realization instances for one component, but the sequence must be queryable

## Initial Canonical Use Case

For a repository component such as `Workflow State Repository`:

Top-level Component Element:
- `Interfaces`
  - realization: `repository_interface`

Top-level Component Element:
- `Functions`
  - realization: `concrete_repository_class`

Then a brief can carry targets like:
1. target `repository_interface`
2. target `concrete_repository_class`
   - `depends_on_target_id = repository_interface target`

That is the exact level of structure needed to constrain autonomous coding runs.

## Briefing Implication

This model lets a brief say, in structured form rather than narrative prose:
- component: `Workflow State Repository`
- target element: `Interfaces`
- target realization: `repository_interface`
- intent: `implement`
- sequence: `1`

Then:
- component: `Workflow State Repository`
- target element: `Functions`
- target realization: `concrete_repository_class`
- intent: `implement`
- sequence: `2`
- depends on sequence `1`

## Final Conclusion

This model is important because it closes a real control gap in autonomous implementation.

Without `Component Element Realizations`, the system knows:
- what a component is
- what design concerns it has

But it still does **not** know, in structured form, what exact artifact the agent is expected to build.

With this model, it does.
