# Existing Component Design Model Audit

Date: 2026-05-13

## Purpose

Before starting new Component Design work for PAA V2, identify what is already modeled in the existing PAA database and runtime contracts that relates to **Component Design**.

This note answers four questions:
- what component-design-related tables already exist
- what those tables define
- how the runtime currently uses them
- where the current model is partial, stale, or bypassed

This is a hard design note, not a migration plan.

## Related Notes

Read alongside:
- `docs/terminology/paa-engineering-terminology-glossary.md`
- `docs/2_Design/2026-05-13-paa-system-component-diagram-v2.md`
- `docs/2_Design/2026-05-13-paa-v2-component-relationships.md`
- `docs/2_Design/2026-05-13-paa-schema-and-data-surface-audit.md`
- `docs/2_Design/2026-05-13-paa-db-primary-data-consolidation-audit.md`
- `docs/2_Design/2026-05-03-stage1-design-package-contract.md`
- `docs/2_Design/2026-05-03-component-dependency-graph-contract.md`
- `docs/2_Design/2026-05-03-coder-brief-sequencing.md`

## Glossary Alignment

Per `docs/terminology/paa-engineering-terminology-glossary.md`, **Component Design** should eventually specify fifteen elements for each component, including:
- Role
- Component State Model
- Service Contract
- Data Contract
- Messages Received / Published
- Events Published / Subscribed
- Component Lifecycle
- Component Configuration

The current DB model does **not** cover all fifteen elements explicitly.

What it does provide is an important partial substrate for Component Design across:
- component identity
- component surfaces
- component relationships
- per-slice design packages
- per-slice coder run briefs
- dependency edges
- sequencing/readiness states

So the right interpretation is:
- we already modeled part of Component Design in the DB
- we did not complete it into a coherent V2 component-design system
- newer slices are using some of the newer artifact tables while only partially using the explicit component graph

## Existing DB Model

The current component-design-related tables are defined mainly in:
- `migrations/postgres/004-step4-coder-briefs.sql`
- `migrations/postgres/005-step5-design-packages-and-sequencing.sql`

The relevant tables are:
- `paa.components`
- `paa.component_surfaces`
- `paa.component_relationships`
- `paa.coder_run_briefs`
- `paa.design_packages`
- `paa.design_package_signoffs`
- `paa.component_dependency_edges`
- `paa.coder_brief_sequence_states`

## What Each Table Models

### `paa.components`

Models stable component identity for a project.

Fields capture:
- `name`
- `role`
- `system_layer`
- `tier`
- `description`
- `status`
- `metadata_json`

This is the closest current DB representation of the glossary's **Role** element.

Current limitation:
- there is no full V2 component catalog for PAA itself
- the populated rows are currently historical retirement-subsystem components, not the newer PAA V2 system components

### `paa.component_surfaces`

Models the concrete code/doc/test/config/event surfaces associated with a component.

Fields capture:
- `surface_type`
- `path`
- `responsibility`
- `is_primary`

This is useful Component Design support data, especially for:
- implementation surface definition
- scope narrowing
- traceability between design and repo surfaces

Current limitation:
- surfaces are present only for the older modeled components
- newer slices are not consistently normalized through this table

### `paa.component_relationships`

Models stable inter-component relationships.

Relationship types currently include:
- `calls`
- `injects`
- `emits_to`
- `consumes_from`
- `contains`
- `coordinates`
- `depends_on`

This table is the closest current DB representation of a stable component graph.

Current limitation:
- it is populated only for the retirement subsystem examples
- it does not yet represent the PAA V2 component relationships
- it lacks many operational semantics that later moved into `component_dependency_edges`

### `paa.design_packages`

Models Stage 1 slice-level design artifacts.

Fields capture:
- package identity
- work-item linkage
- optional `primary_component_id`
- `status`
- full `package_json`
- provenance and metadata

This is not a stable component catalog.
It is a per-slice design artifact carrier.

It currently carries a large amount of what should eventually be grounded in Component Design, including:
- `component_model_slice`
- `component_surfaces`
- `dependency_graph_slice`
- `design_decision_set`
- `authority_context`
- `verification_contract_basis`

Current limitation:
- the data is per-slice and partly embedded in JSON
- newer slices can exist here even when the stable component model is not aligned

### `paa.coder_run_briefs`

Models execution-facing derived slice briefs.

Fields capture:
- brief identity
- work-item linkage
- optional `primary_component_id`
- `component_assignment_json`
- `architecture_constraints_json`
- `dependency_contract_json`
- `behavioral_contract_json`
- `test_contract_json`
- `brief_json`

This is the strongest existing bridge between design-time structure and execution-time work.

It partially covers Component Design elements such as:
- Role
- Data Contract
- partial Service Contract / behavior constraints
- execution constraints

Current limitation:
- it is still slice-oriented, not a reusable component-design record
- newer slices can carry a component assignment even when no stable `primary_component_id` is resolved

### `paa.component_dependency_edges`

Models operational dependency/sequencing edges between components within a design package.

Fields capture:
- dependency type
- dependency strength
- sequencing requirement
- blocking scope
- dependency status
- conflict hints and notes

This goes beyond `component_relationships`.
It is the current operational sequencing model.

Current limitation:
- it is package-scoped, not a stable component-relationship model
- it is populated only where a design package has been fully decomposed into known components
- newer Team Worker slices do not currently populate this table with meaningful new component entries

### `paa.coder_brief_sequence_states`

Models computed readiness / sequencing state for coder briefs.

Fields capture:
- `readiness_state`
- `blocking_cause`
- `parallel_group_id`
- linkage to package / brief / primary component

This is not a Component Design record.
It is a derived operational projection.

It belongs conceptually to project-design sequencing and runtime readiness, not to the stable component-design catalog.

Current limitation:
- it is useful, but it depends on the quality of the upstream component and dependency model
- it inherits gaps from incomplete component modeling

## Current Live Population

Live database inspection shows:
- `paa.components`: `3`
- `paa.component_relationships`: `3`
- `paa.component_surfaces`: `10`
- `paa.coder_run_briefs`: `10`
- `paa.design_packages`: `6`
- `paa.design_package_signoffs`: `4`
- `paa.component_dependency_edges`: `7`
- `paa.coder_brief_sequence_states`: `24`

### What is actually populated

The stable component graph tables are currently populated with a narrow historical component family:
- `RetirementBoundaryDiagnostics`
- `RetirementLifecycleExecutor`
- `RetirementPolicyResolver`

The relationship graph currently reflects only that retirement subsystem.

The package/brief tables are populated more broadly and include newer Team Worker slices such as:
- `fcore-stagew7-2026-05-10-issue108-team-worker-automation-runtime-note`
- `fcore-stagew7-2026-05-10-issue110-team-worker-automation-runtime-note`
- corresponding coder briefs for issues `108` and `110`

This is the key finding:
- the package/brief substrate is active and in use for newer work
- the stable component catalog and relationship model are not being kept in lockstep with that newer work

## How The Runtime Uses These Tables Today

### Producer-side load path

`packages/paa-producer/src/paa_producer/issue_loader.py`:
- loads design-package artifacts from files
- loads coder-brief artifacts from files
- inserts rows into `paa.design_packages`
- inserts rows into `paa.coder_run_briefs`
- inserts rows into `paa.coder_brief_sequence_states`
- attempts to resolve `primary_component_id` by matching component name in `paa.components`

Important consequence:
- if the component named in the artifact is not present in `paa.components`, the package and brief still load, but `primary_component_id` remains null

That is already happening in newer slices.

### Readiness / sequencing path

`packages/paa-core/src/paa_core/readiness.py`:
- reads `paa.design_packages`
- reads `paa.coder_run_briefs`
- reads `paa.component_dependency_edges`
- computes readiness
- updates `paa.coder_run_briefs.brief_json`
- inserts new `paa.coder_brief_sequence_states`

This means the sequencing engine is already DB-backed.

Important consequence:
- if the dependency edge model is incomplete, readiness becomes shallower or falls back to simpler execution assumptions

### Producer runtime resolution path

`packages/paa-producer/src/paa_producer/authority_runtime.py`:
- reads `paa.design_packages`
- reads `paa.coder_run_briefs`
- reads `paa.coder_brief_sequence_states`
- resolves package/brief content for packet compilation and reporting

This means package/brief persistence is not theoretical.
It is an active producer-runtime dependency.

### Consumer runtime usage

`packages/paa-consumer/src/paa_consumer/techlead.py`:
- reads `paa.design_packages`
- uses package resolution in support of status/routing/reporting behavior

The consumer runtime is therefore already partially coupled to this DB-backed design-artifact layer.

## What Is Already Modeled Versus What Is Missing

### Already modeled in a meaningful way

The DB already meaningfully models:
- stable component identity
- stable component surfaces
- stable component relationships
- per-slice design package artifacts
- per-slice coder run briefs
- per-slice dependency graph edges
- per-slice readiness / sequencing states
- signoff records for design packages

That is enough to say:
- yes, we already created a real component-design-adjacent schema model
- it should not be ignored when doing PAA V2 system design

### Missing or incomplete

The current DB model does **not** yet provide a complete V2 Component Design system because it lacks or only partially covers:
- a current PAA V2 component catalog
- a reusable stable record for all 15 Component Design elements
- stable service contracts per component
- stable message/event contracts per component
- stable component lifecycle and configuration models
- separation between stable component definitions and per-slice derivative artifacts
- enforced alignment between `component_model_slice` JSON and `paa.components`

## Important Drift Findings

### 1. Package/brief model is ahead of component-catalog fidelity

The system is actively using:
- `paa.design_packages`
- `paa.coder_run_briefs`
- `paa.coder_brief_sequence_states`

But the stable component catalog is not being updated with the same rigor.

That means the system has drifted toward:
- artifact-first slice modeling
- with only partial stable component normalization

### 2. Newer slices can bypass `primary_component_id`

At least one newer Team Worker slice is present with:
- valid package row
- valid coder brief row
- no resolved `primary_component_id`

That means the current runtime permits a slice to participate in the DB artifact model without full participation in the explicit component model.

### 3. Dependency modeling is still historical and narrow

`paa.component_dependency_edges` is real and useful, but the populated graph is still centered on the retirement subsystem.

So the system has an operational dependency model, but not yet a current one for the newer PAA runtime / Team Worker concerns.

## Design Interpretation

The correct interpretation is not:
- we need to invent Component Design persistence from scratch

The correct interpretation is:
- we already have a partial DB-backed Component Design substrate
- it was strong enough to support Stage 1 package / brief / sequencing work
- but it was not carried forward into a coherent, current, V2 component model

So before new Component Design work begins, we should treat this existing substrate as:
- something to evolve and regularize
- not something to ignore and replace blindly

## Hard Conclusions

1. PAA already has a real DB-backed component-design-related model.
2. That model is split between:
   - stable component graph tables
   - per-slice package/brief artifact tables
   - derived sequencing/readiness tables
3. The stable component graph is currently narrow and historical.
4. The package/brief layer is more active than the stable component model.
5. Newer slices already prove that the system can persist design and execution artifacts without fully resolving stable components.
6. That drift is a design problem and should be corrected explicitly in V2.

## Implications For Next Design Work

When we start Component Design for the V2 system components:
- `Workflow State Machine`
- `Installed Execution Package`
- `Runtime Lifecycle Engine`

we should not begin from an empty schema assumption.

We should instead decide, explicitly:
- which existing tables remain stable foundations
- which existing JSON-heavy artifact tables become transitional layers only
- which missing Component Design elements need first-class DB representation
- how stable component records and per-slice derivative artifacts are kept aligned

## Recommended Baseline Rule

For PAA V2:
- stable component definitions belong in stable component tables
- per-slice derivative artifacts belong in package/brief tables
- derived readiness belongs in sequencing/projection tables
- the runtime should not be allowed to treat those layers as interchangeable

That separation is the design correction needed before detailed Component Design begins.
