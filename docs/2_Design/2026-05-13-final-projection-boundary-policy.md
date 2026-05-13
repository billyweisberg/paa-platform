# Final Projection Boundary Policy

Date: 2026-05-13

## Purpose

Finalize the projection boundary for the PAA DB model.

This note defines:
- which persisted surfaces are primary truth
- which persisted or file-backed surfaces are projections only
- how projection surfaces must be derived
- what file artifacts may remain after DB-primary normalization

This closes the last outstanding DB-model design gap before Data Access Layer design resumes.

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-13-paa-db-model-completion-plan.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-stable-table-classification-and-ownership-map.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-final-workflow-state-entity-design.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-final-runtime-input-and-run-event-entity-design.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-component-design-normalization-rules.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-db-primary-data-consolidation-audit.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-data-access-layer-design.md`

## Final Decisions

This note locks the following decisions:

1. workflow truth is projection input, never projection output.
2. runtime-event history is projection input, never projection output.
3. stable Component Design records are projection input, never projection output.
4. derivative slice-artifact records are projection input, never projection output.
5. report JSON, markdown reports, status summaries, readiness summaries, and lineage summaries are projections only.
6. file-backed projections may remain for inspection and portability, but they may not again become primary operational truth.
7. the Data Access Layer may expose projection repositories, but those repositories remain read-only over derived state.

## Primary Truth Surfaces

The following surfaces are primary truth after normalization.

### Stable authority
- `paa.projects`
- `paa.roles`
- `paa.authority_versions`
- `paa.source_artifacts`
- `paa.source_statements`
- `paa.requirements`
- `paa.requirement_sources`
- `paa.design_decisions`
- `paa.decision_requirements`
- `paa.spec_fragments`
- `paa.spec_fragment_requirements`
- `paa.spec_fragment_decisions`
- `paa.implementation_targets`
- `paa.authority_version_fragments`
- `paa.authority_version_targets`
- `paa.work_items`
- `paa.components`
- `paa.component_surfaces`
- `paa.component_relationships`

### Derivative slice truth
- `paa.design_packages`
- `paa.design_package_signoffs`
- `paa.coder_run_briefs`
- `paa.component_dependency_edges`

### Workflow truth
- `paa.workflow_states`
- `paa.workflow_transitions`

### Runtime-event truth
- `paa.queue_claims`
- `paa.handoffs`
- `paa.queue_messages`
- `paa.automation_runs`
- `paa.automation_run_events`
- `paa.execution_records`
- `paa.acceptance_events`
- `paa.verification_obligations`
- `paa.evidence`
- `paa.transition_inputs`

### Installed execution-package registration truth
- `paa.execution_package_installs`
- `paa.execution_package_overlays`

## Projection Surfaces

The following surfaces are projections only.

### DB-backed projections
- `paa.coder_brief_sequence_states`
- `paa.v_work_item_full_chain_traceability`
- any future:
  - `paa.workflow_status_projections`
  - `paa.lineage_projections`
  - `paa.accepted_chain_projections`

### File-backed projections and exports
- `.project/data/paa/reports/techlead-status-report.json`
- `.project/data/paa/reports/techlead-assignment.*.json`
- `.project/data/paa/reports/worker-result.*.json`
- `.project/data/paa/reports/delivery-review.*.json`
- `.project/data/paa/reports/qa-verification.*.json`
- `.project/data/paa/reports/techlead-decision.*.json`
- `.project/data/paa/reports/role-result-input.*.json`
- markdown companions under `.project/data/paa/reports/`

### File-backed narrative or operator aids
- `.project/data/paa/automation-memory/*.md`

These may remain useful, but they are not primary truth.

## Projection Derivation Rules

## Rule 1: projections derive only from primary truth

A projection may derive from:
- primary DB truth surfaces listed above
- installed execution-package artifacts when the artifact itself is the needed local runtime input

A projection may not derive from:
- another projection as its sole source
- report files as if they were canonical
- markdown operator memory as if it were state

## Rule 2: projection rows and files are disposable and reproducible

If a projection is deleted, the system should be able to regenerate it from primary truth.

This is the key test for whether a surface is really a projection.

## Rule 3: projections may summarize, but not reinterpret ownership

A projection may summarize:
- current owner
- current stage
- readiness state
- lineage state
- accepted-chain state

But it may not redefine those values independently from the primary truth tables.

## Rule 4: readiness remains a projection concern

`paa.coder_brief_sequence_states` remains a projection layer derived from:
- stable component identity
- derivative design packages
- derivative coder briefs
- derivative dependency edges

It must not become the only place where component dependency meaning exists.

## Rule 5: file exports remain optional convenience views

Repo-local JSON and markdown reports may remain for:
- local inspection
- debugging
- portability
- manual review support

They must not be required for:
- recovering workflow truth
- determining claim truth
- determining current install truth
- determining acceptance truth

## File Surface Policy

## Files that remain as local runtime inputs

These remain outside the DB for technical reasons:
- installed execution-package files under `.project/data/paa/authority/current/`
- installed overlay artifact files under `.project/data/paa/authority/current/overlays/`
- source-controlled schema files under `schemas/`
- checked-out Git worktrees and source files
- raw append-only automation log streams

Important distinction:
- these are not projection files in every case
- some are runtime inputs or raw evidence
- they are outside the DB for technical reasons, not because they are workflow truth

## Files that are explicitly demoted to projections

These must be treated as derived/export surfaces:
- report JSON under `.project/data/paa/reports/`
- report markdown companions
- any repo-local status summary files
- any file-only lineage summary exports

## Files that are explicitly demoted to narrative-only aids

These may remain, but are never recovery-critical truth:
- `.project/data/paa/automation-memory/*.md`

## Projection Repository Boundary

The future `Projection Repository` may expose:
- workflow status read models
- lineage read models
- accepted-chain read models
- readiness read models
- report export generation inputs

But it must remain read-only over derived state.

It may not:
- mutate workflow truth
- mutate runtime-event truth
- mutate stable Component Design truth
- mutate execution-package registration truth

## Status And Lineage Policy

### Current owner and current stage
Primary source:
- `paa.workflow_states`

### Transition explanations
Primary source:
- `paa.workflow_transitions`

### Queue claim / lifecycle detail
Primary source:
- `paa.queue_claims`
- plus `paa.queue_messages` and `paa.handoffs`

### Acceptance and closeout summary
Primary source:
- `paa.workflow_states`
- `paa.workflow_transitions`
- `paa.acceptance_events`

### Readiness and sequence summary
Primary source:
- stable and derivative component-design truth
- derived through projection surfaces such as `paa.coder_brief_sequence_states`

### Installed package and overlay summary
Primary source:
- `paa.execution_package_installs`
- `paa.execution_package_overlays`

## Acceptance Test For The Projection Boundary

The projection boundary is correct only if these statements are true:

1. deleting report JSON does not destroy workflow truth
2. deleting markdown automation memory does not destroy recovery truth
3. deleting a local status export does not destroy current owner/stage truth
4. deleting raw logs does not destroy the structured run milestone history kept in DB
5. deleting a projection view or materialized read model does not destroy the primary records used to rebuild it

## Final DB-Model Completion Decision

With this note in place, the DB model is now complete enough for the next design step.

That means:
- the primary truth layers are defined
- the missing DB entity families are defined
- the component normalization rules are defined
- the projection boundary is defined

So the next correct move is:
- resume Data Access Layer design against the completed model

Not:
- invent more DB-primary truth through file artifacts
- blur projections back into operational state

## Hard Conclusion

The projection boundary is now explicit:
- workflow truth is not a report
- runtime-event truth is not a log summary
- stable component truth is not a package JSON shortcut
- derivative slice truth is not a readiness projection

Projections may remain valuable, but they are derived and disposable.

That is the final projection-boundary baseline for the PAA DB model.
