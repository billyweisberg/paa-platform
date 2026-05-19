Title: Derive Design Package Flow
Doc-ID: paa-derive-design-package-flow
Doc-Type: runbook
Status: active
Lifecycle-Stage: build
Created: 2026-05-18
Last-Edited: 2026-05-18
Author: Billy Weisberg
Repo: paa-platform
Component: DesignPackageDeriver
Domain: design-package-derivation
Keywords: design-package, producer, derivation, build, flow
Depends-On: 2026-05-16-paa-producer-derivation-subsystem.md, 2026-05-03-stage1-design-package-contract.md
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
Summary: Defines the producer-side flow for validating and materializing a Stage 1 design package into governed authority records.

# Derive Design Package Flow

Date: 2026-05-16

## Purpose

Define and record the first producer-side implementation of:
- `derive-design-package`

This flow closes Priority 1 item 4 by turning the previously manual proof-slice package materialization into a repeatable producer command.

## Related Notes

- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-16-paa-derivation-remediation-backlog.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-paa-producer-derivation-subsystem.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-stage1-design-package-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-component-design-planning-service-slice-package-materialization.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-producer/src/paa_producer/design_package_deriver.py`

## Problem

Before this run, PAA had:
- a Stage 1 design package contract
- manual package artifacts
- DB tables for design packages
- downstream flows such as readiness and packet materialization

What it did **not** have was a first-class producer command that could:
- validate a Stage 1 design package artifact
- materialize the required DB authority records
- return the resulting bindings cleanly

That left the refined derivation process partially note-driven.

## First Implementation Scope

The first implementation intentionally solves the narrowest useful path.

Input:
- one Stage 1 design package JSON artifact

Output:
- validated package artifact
- persisted or updated:
  - project
  - signoff roles
  - authority version
  - spec fragment
  - implementation target
  - primary component
  - work item
  - design package
  - design package signoffs

This is enough to make the proof-slice package materialization executable instead of manual.

## Command Surface

Producer command:
- `paa-producer derive-design-package`

Arguments:
- `--design-package <path>`
- `--schema-path <path>` optional
- `--project-slug <slug>` optional override
- `--project-name <name>` optional override
- `--repo-root <path>` optional
- `--dry-run`

## Validation Rule

The command validates the package against the Stage 1 schema before any DB mutation.

Default schema resolution order:
1. explicit `--schema-path`
2. local platform copy:
   - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/schemas/derivation/stage1_design_package.schema.json`
3. current shared canonical appdev copy:
   - `/Users/billyweisberg/Repos/Individual-Centricity/appdev/docs/architecture/tom-baby7-fractal-core/artifact-schemas/stage1_design_package.schema.json`

## Idempotency Rule

The command is designed to be rerunnable.

Stable identity rules used in the first implementation:
- project by `slug`
- authority version by `(project_id, version_label)`
- spec fragment by `(project_id, delta_family)`
- implementation target by stable external `implementation_target_id`, with the title as a fallback matcher for older rows
- component by `(project_id, name)`
- work item by:
  - `issue_number` when present
  - otherwise `spec_fragment_ref`
- design package by `(project_id, package_id_external)`
- design package signoff by `(design_package_id, role_id)`

Validation update:
- `2026-05-16`: rerun validated as idempotent against the proof slice
- a parsing bug in scalar `psql` result handling was fixed during validation
- implementation-target matching was tightened to reuse the canonical target row instead of creating duplicate slice targets on rerun

## Proof-Slice Validation

The first real proof run is the `Component Design Planning Service` slice package:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-component-design-planning-service-stage1-design-package.json`

That artifact is now valid command input rather than a one-off manually inserted special case.

## Current Limitation

This command materializes the Stage 1 package and its directly required authority records.

It does **not** yet:
- evaluate derivation readiness
- derive coder briefs
- author brief targets
- review coder briefs
- prepare architect packets

Those are the next Priority 1 steps.

## Decision

Decision:
- `Priority 1 item 4 complete`

Meaning:
- the producer-side `derive-design-package` flow now exists as a real implementation path
- the next work should move into:
  - `evaluate-derivation-readiness`
  - `assemble-coder-brief`