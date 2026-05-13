# Final Component Element Entity Design

Date: 2026-05-13

## Purpose

Define the stable DB entity model for standardized **Component Elements**.

This note closes the remaining stable Component Design data-model gap without overfitting the glossary into fifteen separate top-level tables.

Instead, the model uses:
1. a reference taxonomy of allowed Component Element types
2. per-component Component Element records attached to stable component identity

That gives PAA a standard vocabulary for authoring, normalization, briefing, and reporting such as:
- `Event Subscriptions` for `Workflow State Machine`
- `Service Contract` for `Runtime Lifecycle Engine`
- `Component Configuration` for `Installed Execution Package Manager`

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/terminology/paa-engineering-terminology-glossary.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-component-design-normalization-rules.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-existing-component-design-model-audit.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-stable-table-classification-and-ownership-map.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-db-model-diagram-and-gap-analysis.md`

## Design Decision

PAA does **not** introduce one table per glossary element.

PAA does introduce:
- `paa.component_element_types`
- `paa.component_elements`

This keeps the model standardized without forcing premature specialization.

## Entity 1: `paa.component_element_types`

This is the stable reference taxonomy.

It defines:
- the canonical key for the element type
- the human label used in authority artifacts and briefs
- a broad category for grouping/reporting
- whether the element type is brief-targetable
- whether multiple instances of the element type are expected for a component
- display ordering

### Purpose

This table is the single standardized vocabulary for the things Components are composed of.

It is the source of labels such as:
- `Role`
- `Service Contract`
- `Event Subscriptions`
- `Functions`

## Entity 2: `paa.component_elements`

This is the stable per-component instance layer.

Each row says:
- this Component owns this kind of Component Element
- here is the stable definition of that element
- here is its current status and provenance

### Purpose

This table allows a component to have:
- one `Service Contract`
- many `Functions`
- many `Event Subscriptions`
- one `Component Lifecycle`
- many other standardized element instances

### Identity Rule

The row identity is not only `(component_id, component_element_type_id)`.

Some element types are naturally multi-instance:
- `Functions`
- `Injected Services`
- `Interfaces`
- `Messages Received`
- `Messages Published`
- `Event Subscriptions`
- `Events Published`

So the stable uniqueness rule is:
- `(component_id, component_element_type_id, element_key)`

Where `element_key` is a stable component-local identity such as:
- `apply_transition`
- `workflow_transition_applied`
- `github_pr_merged`

## Final Field Model

## `paa.component_element_types`

Core fields:
- `component_element_type_id`
- `element_key`
- `label`
- `category`
- `description`
- `is_brief_targetable`
- `is_multi_instance`
- `sort_order`
- `metadata_json`
- `created_at`
- `updated_at`

## `paa.component_elements`

Core fields:
- `component_element_id`
- `project_id`
- `component_id`
- `component_element_type_id`
- `element_key`
- `title`
- `status`
- `definition_json`
- `provenance_json`
- `metadata_json`
- `created_by_role_id`
- `created_by_agent_id`
- `created_at`
- `updated_at`

## Why `definition_json` Is Acceptable Here

This model is still DB-primary even though `definition_json` is JSONB.

That is acceptable because:
- the truth is in DB rows, not in repo-local files
- the taxonomy is normalized
- the per-component instance identity is normalized
- detailed element payloads are likely to vary significantly across element types

This is the correct first stable Component Element model.

If some element families later prove stable enough for stronger normalization, PAA can add child tables later without discarding this foundation.

## Seeded Canonical Element Types

The reference taxonomy is seeded with the full glossary vocabulary:
- `role`
- `component_state_model`
- `service_contract`
- `data_contract`
- `injected_services`
- `interfaces`
- `functions`
- `messages_received`
- `messages_published`
- `message_data_contracts`
- `event_subscriptions`
- `events_published`
- `event_data_contracts`
- `component_lifecycle`
- `component_configuration`

This gives briefs and reports a stable vocabulary immediately.

## Briefing Implication

This model directly supports structured brief targeting such as:
- `primary_component = Workflow State Machine`
- `target_component_element_type = Event Subscriptions`
- `target_component_element_key = workflow_transition_applied`

That is the intended bridge from stable Component Design to execution briefs.

## What This Design Replaces As Primary Truth

These should no longer be treated as the only source of Component Element meaning:
- embedded `component_model_slice` JSON in design packages
- ad hoc labels buried in brief JSON
- prose-only component-element naming in docs

Those may still exist as derivative artifacts or rendered exports.

The stable source of truth becomes:
- component identity in `paa.components`
- component-element taxonomy in `paa.component_element_types`
- component-element instances in `paa.component_elements`

## Extension: Component Element Realizations

This note is now extended by:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-component-element-realization-model.md`

That extension adds the second-level realization taxonomy needed to constrain autonomous implementation runs.

## What This Design Does Not Do Yet

This design does not yet:
- add separate specialized tables for every element family
- define DAL repositories
- change runtime code
- rewrite coder-brief derivation

It only completes the stable `Component Element` layer itself. Realization-level targeting is defined in the follow-on realization model note.

## Final Conclusion

The stable Component Design model is now completed through:
- `paa.components`
- `paa.component_surfaces`
- `paa.component_relationships`
- `paa.component_element_types`
- `paa.component_elements`

That is sufficient to move forward into Data Access Layer design without pretending that derivative package JSON is still the stable component-definition substrate.
