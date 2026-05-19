Title: Assemble Coder Brief Flow
Doc-ID: paa-assemble-coder-brief-flow
Doc-Type: runbook
Status: active
Lifecycle-Stage: build
Created: 2026-05-18
Last-Edited: 2026-05-18
Author: Billy Weisberg
Repo: paa-platform
Component: CoderBriefAssembler
Domain: coder-brief-derivation
Keywords: coder-brief, brief, assembly, producer, build, flow
Depends-On: 2026-05-16-evaluate-derivation-readiness-flow.md, 2026-05-03-coder-brief-derivation-method.md
Supersedes: 
Superseded-By: 
Canonical: true
Review-After: 2026-06-15
Owners: 
Expires: 
Issue: 
PR: 
Authority-Source: 
Implementation-Status: 
Summary: Defines the producer-side flow for assembling a governed draft coder brief from active derivation state.

# Assemble Coder Brief Flow

Date: 2026-05-16

## Purpose

Define and record the first producer-side implementation of:
- `assemble-coder-brief`

This flow closes Priority 1 item 6 by turning draft coder-brief construction into a real producer-side derivation step instead of leaving it spread across notes, prior dry-run artifacts, and downstream packet materialization logic.

## Related Notes

- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-16-paa-derivation-remediation-backlog.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-coder-brief-derivation-method.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-coder-brief-field-derivation-matrix.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-component-design-planning-service-stage1-design-package.json`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/4_Build/2026-05-16-evaluate-derivation-readiness-flow.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-producer/src/paa_producer/coder_brief_assembler.py`

## Problem

Before this run, PAA had:
- a validated slice package
- a validated derivation-readiness gate
- persisted coder-brief storage and authority lifecycle support
- older packet-time brief selection logic

What it did **not** have was a first-class producer step that could:
- derive a draft `coder_run_brief` body from the active Stage 1 package and current structured derivation state
- validate that brief against the brief schema
- persist or refresh one governed draft brief row for the slice
- write a draft brief artifact that later producer-side steps can inspect and refine

That left draft brief construction partly informal.

## First Implementation Scope

The first implementation intentionally assembles one schema-valid draft brief from:
- the active Stage 1 package
- the derivation-readiness result
- the currently materialized slice bindings in DB
- the current service-oriented target-model mappings

It then:
- validates the brief against the local coder-brief schema copy
- optionally writes the brief artifact to disk
- persists or refreshes one `draft_brief` row in `paa.coder_run_briefs`
- preserves the existing proof-slice draft brief row instead of creating duplicates on rerun

This is enough to make draft brief derivation executable before brief-target authoring begins.

## Command Surface

Producer command:
- `paa-producer assemble-coder-brief`

Arguments:
- `--design-package <path>`
- `--package-schema-path <path>` optional
- `--brief-schema-path <path>` optional
- `--project-slug <slug>` optional override
- `--output <path>` optional artifact output path
- `--no-persist-db` optional validation-only mode

## What This Assembler Derives

The first implementation assembles:
- `brief_id`
- `project`
- `authority_context`
- `slice_scope_ref`
- `component_assignment`
- `architecture_constraints`
- `collaboration_context`
- `execution_prerequisites`
- `dependency_contract`
- `behavioral_contract`
- `test_contract`
- `execution_readiness`
- `change_budget`
- `anti_goals`

It intentionally does **not** yet assemble:
- `coder_brief_realization_targets`
- review/approval transitions
- packet-preparation state

Those remain the next explicit producer-side steps.

## Proof-Slice Validation

Validated against:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-component-design-planning-service-stage1-design-package.json`

Validated output artifact:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-component-design-planning-service-assembled-draft-coder-run-brief.json`

Validated persisted row:
- `coder_run_brief_id = fceab499-60f4-4a11-851d-b1059d8dbde9`
- `brief_id_external = paa-coder-2026-05-16-component-design-planning-service-governed-draft`
- `authority_state = draft_brief`
- `readiness_class = derivation_ready`

## Important Finding During Validation

The local `coder_run_brief` schema copy was still using older architecture vocabulary for:
- `component_assignment.system_layer`
- `component_assignment.component_aspects`

The assembler correctly produced values aligned to the new PAA architecture and component-element taxonomy, so the local schema copy was updated to accept:
- layered architecture terms such as `domain-services`
- current component-element aspect keys such as `interfaces` and `data_contract`

This was the correct fix.

The assembler should not regress its language back to older taxonomy just to satisfy a stale schema copy.

## Idempotence Rule

On rerun, the assembler:
- reuses the existing proof-slice draft brief row for the design package when present
- refreshes the row contents and provenance instead of creating a new draft brief row
- preserves the `derive_draft` authority event if it already exists

This keeps proof-slice derivation stable across iterative runs.

## Decision

Decision:
- `Priority 1 item 6 complete`

Meaning:
- draft coder-brief construction now exists as a real producer-side derivation step
- the next work should move into:
  - `author-brief-targets`
  - `review-coder-brief`