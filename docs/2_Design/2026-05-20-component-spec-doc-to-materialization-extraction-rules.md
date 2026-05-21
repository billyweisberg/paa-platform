Title: Component Spec Doc To Materialization Extraction Rules
Doc-ID: paa-component-spec-doc-to-materialization-extraction-rules
Doc-Type: design-note
Status: active
Lifecycle-Stage: design
Created: 2026-05-20
Last-Edited: 2026-05-20
Author: Billy Weisberg
Repo: paa-platform
Component: PaaComponentSpecExtraction
Domain: design-authority
Keywords: paa, component-spec, extraction, materialization, parser, tables, workflow-lifecycle
Depends-On: 2026-05-20-component-spec-template-materialization-bridge.md, 2026-05-20-component-spec-section-to-model-mapping-table.md, 2026-05-17-workflow-lifecycle-service-component-spec.md
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
Summary: Defines the first doc-to-materialization extraction rules for reading governed Component Spec tables and reconciling model truth from the WorkflowLifecycleService proof slice.

# Component Spec Doc To Materialization Extraction Rules

## Purpose

Define the first narrow extraction contract for reading a governed `Component Spec` doc and turning its structured tables into materialization inputs.

This rule set is intentionally narrow.

It applies first to:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-workflow-lifecycle-service-component-spec.md`

## Scope

The v1 extractor reads these sections only:
- `Component Identity Table`
- `Component Elements Table`
- `Realizations Table`
- `Plan Seed Table`
- `Activity Seed Table`
- `Activity Dependency Table`
- `Verification Surface Table`

It does not parse narrative sections for materialization truth.

## Extraction Rules

| Section | Extraction Rule | Output Shape |
|---|---|---|
| Component Identity Table | read exactly one row | one component seed |
| Component Elements Table | read one row per element | ordered element seeds keyed by `element_name` |
| Realizations Table | read one row per realization | ordered realization seeds keyed by `element_name` plus `realization_kind` plus `artifact_target` |
| Plan Seed Table | read exactly one row | one implementation-plan seed |
| Activity Seed Table | read one row per activity | ordered activity seeds keyed by `activity_key` |
| Activity Dependency Table | read one row per dependency | ordered dependency seeds |
| Verification Surface Table | read one row per surface | ordered verification-surface seeds |

## Table Parsing Rules

- section names must match exactly
- each materialization table must be a Markdown pipe table directly under its section heading
- the first row is the header row
- the second row is the delimiter row
- all subsequent rows are data rows
- blank lines end the table block
- all required columns must be present exactly as named in the governing template
- extra columns are allowed but ignored by the v1 extractor

## Normalization Rules

- trim leading and trailing whitespace from all cell values
- preserve case for names, keys, artifact targets, and status values
- normalize `required_for_acceptance` to boolean by accepting only `true` or `false`
- normalize `sequence` to integer
- do not infer missing rows from prose
- do not infer missing columns from neighboring tables

## Fail-Closed Rules

The extractor must fail closed when:
- a required section is missing
- a required table is missing
- a required column is missing
- a single-row table has zero rows or more than one row
- an activity references an unknown `element_name`
- a realization references an unknown `element_name`
- an activity dependency references an unknown `activity_key`

## Reconciliation Rules

The first narrow materializer should reconcile:
- the component row by component name
- component elements by `element_name`
- realizations by a stable derived realization key
- the implementation plan by `plan_name`
- implementation-plan activities by `activity_key`

For the first proof slice, if an existing plan already contains an older activity set for the same `plan_name`, the materializer may replace that plan's activity and dependency rows before re-writing the activity set from the doc.

That replacement rule is allowed only for the governed proof slice.

## Stable Derived Keys

Because the current v1 spec tables do not carry explicit realization keys, the extractor derives them as follows:
- `realization_key = <component_slug>__<element_name>__<realization_kind>`

For `WorkflowLifecycleService`, `component_slug` is:
- `workflow_lifecycle_service`

Example:
- `workflow_lifecycle_service__workflow_transition_interface__service_interface`

## Output Contract

The extractor should produce a structured seed object containing:
- component identity seed
- element seeds
- realization seeds
- plan seed
- activity seeds
- activity dependency seeds
- verification surface seeds

That seed object is then the input contract for the narrow materializer.

## First Proof Operation

The first proof operation is:
- read the structured tables from the `WorkflowLifecycleService` component spec
- reconcile the component, elements, realizations, implementation plan, and implementation-plan activities
- validate that the resulting model truth remains consistent with governed code metadata and downstream checkers

## Not In Scope Yet

Not in scope for v1:
- parsing narrative ownership sections into model truth
- parsing collaborator sections into dependency graph truth
- deriving coder-brief targets directly from the component spec
- generic multi-component batch materialization
