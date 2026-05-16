# Derivation State Data Model Validation

Date: 2026-05-16
Phase: `Phase 3. Validate The Data Model Against Derivation State`
Plan: `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-16-paa-derivation-method-validation-plan.md`

## Purpose

Validate whether the current PAA DB/data model can represent the derivation-process state required by the normalized derivation pipeline and the Phase 2 input-coverage findings.

This phase is not asking:
- can the DB store some JSON?

It is asking:
- can the DB manage the derivation process state explicitly enough that `System Design -> Agent Team -> Functioning Software System` is governable rather than implicit?

## Inputs to this validation pass

Primary validation inputs:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-paa-derivation-pipeline-validation.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-component-design-planning-service-derivation-input-coverage.md`

Primary DB/model authority:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/001-step1-control-plane.sql`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/002-step2-verification-recovery.sql`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/003-step3-knowledge-graph.sql`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/004-step4-coder-briefs.sql`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/005-step5-design-packages-and-sequencing.sql`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/006-step6-workflow-install-runtime-normalization.sql`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/007-step7-component-elements.sql`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/008-step8-component-element-realizations.sql`

Supporting design notes:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-schema-and-data-surface-audit.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-db-primary-data-consolidation-audit.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-existing-component-design-model-audit.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-component-design-foundation-and-derivation-baseline.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-component-design-normalization-rules.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-final-projection-boundary-policy.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-final-component-element-entity-design.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-component-element-realization-model.md`

## Validation question

Do we already have the records needed to manage derivation state explicitly?

Answer:
- mostly yes for the core slice, brief, target, sequencing, and proof structures
- not yet fully for a normalized derivation-state lifecycle and review history model

That distinction matters.

The current model is stronger than the Phase 2 note alone might suggest.
Many derivation inputs that looked missing are not DB-model gaps.
They are authoring and population gaps.

## Tables most relevant to derivation-state management

### Slice and authority binding
- `paa.work_items`
- `paa.authority_versions`
- `paa.spec_fragments`
- `paa.implementation_targets`
- `paa.authority_version_fragments`
- `paa.authority_version_targets`

### Design-package state
- `paa.design_packages`
- `paa.design_package_signoffs`
- `paa.component_dependency_edges`

### Coder-brief state
- `paa.coder_run_briefs`
- `paa.coder_brief_sequence_states`
- `paa.coder_brief_realization_targets`

### Component-target model
- `paa.components`
- `paa.component_surfaces`
- `paa.component_relationships`
- `paa.component_element_types`
- `paa.component_elements`
- `paa.component_element_realization_types`
- `paa.component_element_type_realization_types`
- `paa.component_element_realizations`

### Proving and execution evidence
- `paa.verification_obligations`
- `paa.evidence`
- `paa.execution_records`
- `paa.transition_inputs`
- `paa.automation_run_events`

## Coverage scale

Use these ratings:
- `strong`: directly represented in the DB model with clear ownership
- `partial`: representable, but spread across multiple records, JSON sections, or lacking explicit lifecycle semantics
- `missing`: not cleanly represented in the current model

## Validation against the major Phase 2 gaps

## 1. Explicit slice package for this implementation run

Phase 2 gap:
- no normalized, task-bound `DesignPackage` had yet been materialized for the `Component Design Planning Service` implementation run

DB-model verdict:
- `strong`

Why:
- `paa.design_packages` already exists as the slice-scoped derivative artifact root
- it already binds:
  - `project_id`
  - `work_item_id`
  - `spec_fragment_id`
  - `implementation_target_id`
  - `authority_version_id`
  - `primary_component_id`
  - `status`
  - `package_json`
  - `provenance_json`
- `paa.design_package_signoffs` already exists for role-level package approval state

Conclusion:
- this is not a schema gap
- it is a materialization and authoring gap

## 2. Explicit slice identity record

Phase 2 gap:
- missing task id, work item id, authorized delta family, out-of-scope scope, issue binding

DB-model verdict:
- `partial`

What is already represented strongly:
- `paa.work_items` already provides:
  - `work_item_id`
  - `authority_version_id`
  - `title`
  - `issue_number`
  - `spec_fragment_id`
  - `implementation_target_id`
- `paa.execution_records` can hold issue or PR execution linkage
- `paa.design_packages` and `paa.coder_run_briefs` can bind to `work_item_id`

What is only partial:
- `authorized_delta_family`
- `out_of_scope_delta_families`
- canonical run-level slice naming in the precise coder-brief sense

Why partial:
- these values appear derivable from:
  - `spec_fragments`
  - `implementation_targets`
  - `slice_scope_ref_json`
  - `package_json`
- but they are not yet normalized as explicit structured fields in the design-package or coder-brief root rows

Conclusion:
- slice identity is representable
- but some of its most important derivation fields still rely on JSON sections rather than first-class typed columns

## 3. Explicit proving contract for the run

Phase 2 gap:
- missing tests to run, tests to add or update, protected baseline checks, expected verification artifacts, and verification-obligation binding

DB-model verdict:
- `partial`

What is already represented strongly:
- `paa.verification_obligations`
- `paa.evidence`
- `paa.coder_run_briefs.test_contract_json`
- `paa.implementation_targets.protected_baseline_json`
- `paa.implementation_targets.pre_handoff_scope_checks_json`

What is only partial:
- the exact run-specific mapping from verification obligations into the specific coder brief for one run is still largely embedded in JSON or derived informally
- `tests_to_add_or_update` is representable in `test_contract_json`, but not normalized beyond that

Conclusion:
- the proving contract is not missing from the model
- but it is not yet normalized into a more explicit derivation-state structure

## 4. Explicit run-level placement and edit boundaries

Phase 2 gap:
- missing target modules, allowed edit surfaces, forbidden edit surfaces, required seams restated as run instructions

DB-model verdict:
- `partial`

What is already represented strongly:
- stable structure exists through:
  - `paa.components`
  - `paa.component_surfaces`
  - `paa.component_relationships`
- run-level architecture boundary sections exist in:
  - `paa.coder_run_briefs.component_assignment_json`
  - `paa.coder_run_briefs.architecture_constraints_json`

What is only partial:
- target modules and edit surfaces for one run are still stored as section JSON rather than as normalized boundary rows
- there is no dedicated row model for brief-time edit-boundary instances

Conclusion:
- representable today
- but not yet explicitly normalized for queryability or fine-grained signoff

## 5. Explicit run-level code artifact target set

Phase 2 gap:
- no formal derived target set for this service implementation run

DB-model verdict:
- `strong`

Why:
- the full structured target chain now exists:
  - `paa.component_element_types`
  - `paa.component_elements`
  - `paa.component_element_realization_types`
  - `paa.component_element_type_realization_types`
  - `paa.component_element_realizations`
  - `paa.coder_brief_realization_targets`

Conclusion:
- this is not a schema gap
- it is a derivation and population gap

## 6. Explicit derivation-state / readiness record for the candidate run

Phase 2 gap:
- missing derivation-ready state, blocked reasons, pending signoffs, run-level readiness classification

DB-model verdict:
- `partial`

What is already represented strongly:
- `paa.design_packages.status`
- `paa.design_package_signoffs`
- `paa.coder_run_briefs.status`
- `paa.coder_brief_sequence_states.readiness_state`
- `paa.coder_brief_sequence_states.blocking_cause`
- `paa.component_dependency_edges.dependency_status`
- `paa.component_dependency_edges.blocking_scope`
- `paa.component_dependency_edges.sequencing_requirement`

What is still weak:
- there is no single normalized derivation-state lifecycle record that ties together:
  - design package readiness
  - derivation start and completion state
  - derivation blocking reasons
  - review pending state
  - brief approval pending state
  - packet-embedding state
- `paa.coder_brief_sequence_states` is explicitly a projection surface, not the primary lifecycle owner

Conclusion:
- this is a real remaining DB-model gap
- the lifecycle is partially representable, but not explicitly modeled as one primary derivation-state machine

## Validation against the normalized pipeline

## Stage 0. Upstream System Design authority

DB verdict:
- `strong`

Represented by:
- stable knowledge graph and component-design tables

## Stage 1. Active slice package

DB verdict:
- `strong`

Represented by:
- `paa.design_packages`
- `paa.work_items`
- linked authority and component records

## Stage 2. Derivation readiness gate

DB verdict:
- `partial`

Represented by:
- `paa.design_packages.status`
- `paa.design_package_signoffs`
- `paa.component_dependency_edges`
- `paa.coder_brief_sequence_states`

Gap:
- no primary derivation-readiness record distinct from projection state

## Stage 3. Top-level identity and authority context

DB verdict:
- `partial`

Represented by:
- `paa.work_items`
- `paa.execution_records`
- `paa.design_packages`
- `paa.coder_run_briefs.slice_scope_ref_json`

Gap:
- delta-family and slice-scope identity are not fully normalized

## Stage 4. Primary component assignment

DB verdict:
- `strong`

Represented by:
- `paa.design_packages.primary_component_id`
- `paa.coder_run_briefs.primary_component_id`
- `paa.components`

## Stage 5. Scope and placement boundaries

DB verdict:
- `partial`

Represented by:
- stable component and surface model
- brief JSON sections

Gap:
- no dedicated normalized row set for brief-time placement boundaries

## Stage 6. Collaboration and dependency contracts

DB verdict:
- `strong`

Represented by:
- `paa.component_relationships`
- `paa.component_dependency_edges`
- `paa.coder_run_briefs.collaboration_context_json`
- `paa.coder_run_briefs.dependency_contract_json`

## Stage 7. Behavioral and proving contracts

DB verdict:
- `partial`

Represented by:
- `paa.coder_run_briefs.behavioral_contract_json`
- `paa.coder_run_briefs.test_contract_json`
- `paa.verification_obligations`
- `paa.evidence`
- authority-layer implementation target records

Gap:
- stronger structured binding between verification obligations and one derived coder brief would help

## Stage 8. Change budget and anti-goals

DB verdict:
- `partial`

Represented by:
- `paa.coder_run_briefs.change_budget_json`
- `paa.coder_run_briefs.anti_goals_json`
- implementation-target scope-check fields

Gap:
- still JSON-section based, not normalized for finer process governance

## Stage 9. Sequencing and execution readiness

DB verdict:
- `partial`

Represented by:
- `paa.component_dependency_edges`
- `paa.coder_brief_sequence_states`
- `paa.coder_brief_realization_targets`

Gap:
- the main readiness table is projection-layer, not primary derivation-lifecycle truth

## Stage 10. Assemble, validate, and approve the brief

DB verdict:
- `partial`

Represented by:
- `paa.coder_run_briefs`
- `paa.design_package_signoffs`
- status fields
- provenance JSON

Gap:
- no explicit review-event or approval-transition history for the brief artifact itself

## Stage 11. Persist approved brief with provenance

DB verdict:
- `strong`

Represented by:
- `paa.coder_run_briefs`
- `generated_from_json`
- `metadata_json`
- `created_by_role_id`
- `created_by_agent_id`
- linked realization targets

Gap note:
- field-level provenance and reviewer detail are still mostly packed into JSON, but persistence is clearly supported

## Stage 12. Embed brief into architect packet

DB verdict:
- `partial`

Represented by:
- the brief artifact is persistable
- runtime event and transition input tables can capture packet-handling evidence

Gap:
- there is no dedicated persistent packet-embedding state tied to one brief beyond runtime/event traces and packet payloads

## Strongly supported derivation-state capabilities

The current model already supports these well:
- authoritative work-item identity with issue binding
- authority-version binding
- spec-fragment and implementation-target binding
- design-package root records
- role-level package signoff state
- primary component binding
- stable component catalog and relationships
- stable component-element taxonomy
- concrete realization taxonomy and instances
- brief-specific realization targets with sequence and dependency
- persisted coder briefs with structured section JSON
- verification obligations and evidence collection
- dependency-edge based readiness computation inputs

This is a much stronger base than a file-sprawl system.

## Real DB-model gaps for derivation management

These are the remaining structural gaps that appear real after this validation pass.

## Gap 1. No explicit primary derivation-state lifecycle record

Need:
- one primary lifecycle owner for the derivation process itself

Why:
- current state is spread across:
  - `design_packages.status`
  - `design_package_signoffs`
  - `coder_run_briefs.status`
  - projection-layer readiness state
- this is workable, but not explicit enough for full derivation governance

Possible future shape:
- `paa.derivation_states`
- and possibly `paa.derivation_state_transitions`

This is the clearest structural gap.

## Gap 2. No explicit brief review / approval history table

Need:
- durable history of review and approval transitions for a derived coder brief

Why:
- brief persistence exists
- signoff exists for design packages
- but coder-brief review state is still mostly implied by current status plus JSON provenance

Possible future shape:
- `paa.coder_brief_reviews`
- or a more general `paa.derivation_reviews`

## Gap 3. No explicit normalized slice-scope / delta-family model inside the derivation layer

Need:
- cleaner structured representation of:
  - authorized delta family
  - out-of-scope delta families
  - canonical slice scope identity

Why:
- these are important briefing and governance fields
- they are currently representable, but not cleanly normalized in the derivative layer

This is a medium-priority gap.

## Gap 4. No explicit normalized brief-time boundary rows

Need:
- queryable row-level structure for:
  - target modules
  - allowed edit surfaces
  - forbidden edit surfaces
  - required seams at brief time

Why:
- these are important for governance and later tooling
- currently they live well enough in JSON sections, but not as first-class queryable records

This is useful, but lower priority than the lifecycle gap.

## Gap 5. No explicit packet-embedding state record for one brief

Need:
- if packet embedding becomes a governed derivation milestone, it may deserve its own explicit state or event row family

Why:
- packet embedding is currently inferable from runtime/event history
- that may be sufficient, but if derivation is treated as a formal governed pipeline, explicit embedding state may be cleaner

This is a lower-priority design choice, not yet a mandatory gap.

## Final Phase 3 conclusion

The current DB model is already strong enough to support a large portion of the derivation process as designed.

That means:
- the Phase 2 gaps were not mostly schema absences
- they were mostly missing authored or derived records within an already-capable model

However, the model is not yet fully complete for derivation-state governance.

The clearest remaining structural gap is:
- no explicit primary derivation-state lifecycle model

The next most useful gaps are:
- explicit brief review history
- better normalized slice-scope and edit-boundary derivative records

## Exit criteria check

Phase 3 exit criteria were:
- we can state whether the DB model is complete enough for derivation-state management
- all known derivation-state gaps are recorded explicitly

Result:
- satisfied

The DB model is:
- complete enough for meaningful derivation-state management work to continue
- not yet complete enough for fully explicit derivation governance without a few targeted extensions

## Recommendation for Phase 4

Proceed to:
- validate the layered architecture and component decomposition against the derivation process

Important carry-forward conclusion:
- Phase 4 should assume the data model is largely viable
- but it should also test whether the architecture provides a clean home for the missing derivation-lifecycle services and producer-side review flows identified here
