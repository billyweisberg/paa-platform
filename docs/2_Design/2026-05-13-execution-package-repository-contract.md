# Execution Package Repository Contract

Date: 2026-05-13

## Purpose

Define the concrete Data Access Layer contract for:
- `Execution Package Repository`

This repository is the structured access boundary for installed execution-package truth.

Its purpose is to give higher-level components a stable way to:
- resolve which Installed Execution Package is active for an execution surface
- resolve which overlays are active on that install
- access installed package artifacts through a consistent contract
- persist and inspect install and overlay registration history

without treating local metadata files as the canonical truth or scattering direct file access across runtime paths.

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-data-access-layer-design.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-final-execution-package-registration-entity-design.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-runtime-consolidation-design-correction.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-v2-component-relationships.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-final-projection-boundary-policy.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-workflow-state-repository-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-component-design-repository-contract.md`

## Role

Provide structured access to:
1. execution-package install registration history
2. execution-package overlay activation history
3. current active install and overlay state for an execution surface
4. installed package artifact paths and resolved local package content

## Repository Boundary

The repository owns structured access to these DB tables:
- `paa.execution_package_installs`
- `paa.execution_package_overlays`

It also owns structured file-surface access to the installed package artifacts referenced by those rows, including paths under:
- `.project/data/paa/authority/current/`
- `.project/data/paa/authority/current/overlays/`

It may join supporting identity tables only as needed for lookup resolution:
- `paa.projects`
- `paa.roles`
- `paa.work_items`
- `paa.authority_versions`
- `paa.design_packages`
- `paa.coder_run_briefs`

It does **not** own primary access to:
- workflow-state tables
- runtime event history tables
- stable component-design tables
- published producer-side source-authority docs
- read-model projections or report views

Those remain outside this repository boundary.

## Non-Goals

The repository does not:
- publish authority packages
- derive design packages or coder briefs from source authority
- decide legal workflow transitions
- replace the `Component Design Repository`
- treat local artifact paths as truth without corresponding install or overlay registration rows

## Primary Consumers

The main consumers are:
- `Runtime Lifecycle Engine`
- `Workflow State Machine` when package or brief identity must be resolved for a slice
- `Reporting And Traceability Projection`
- install, refresh, overlay, and repair tooling

## Canonical Read Models

The repository provides structured access to five logical read models.

### 1. Execution Surface Install View

Represents the active or historical install registration for one execution surface.

Includes:
- execution surface identity
- package identity and authority version
- install status and provenance
- install timing
- install content pointers

Backed by:
- `paa.execution_package_installs`

### 2. Active Overlay View

Represents the active or historical overlay state for one install.

Includes:
- overlay identity and type
- overlay status and provenance
- overlay linkage to work item when relevant
- overlay content pointers

Backed by:
- `paa.execution_package_overlays`

### 3. Installed Package Artifact View

Represents the resolved artifact surface for one active install.

Includes:
- installed manifest path
- installed package metadata path
- installed docs root
- installed artifacts root
- resolved active overlay roots when present

Backed by:
- `paa.execution_package_installs`
- `paa.execution_package_overlays`
- local installed package files referenced by those rows

### 4. Installed Execution Context View

Represents the execution-time context that higher-level runtime paths need.

Includes:
- active install registration
- active overlays
- authority version linkage
- optional package/brief linkage when derivable from installed artifacts

Backed by:
- `paa.execution_package_installs`
- `paa.execution_package_overlays`
- installed manifest and package metadata artifacts

### 5. Install And Overlay History View

Represents the historical record of package installation, replacement, and overlay activation.

Includes:
- install replacement chains
- overlay replacement chains
- deactivation reasons
- install and overlay timestamps

Backed by:
- `paa.execution_package_installs`
- `paa.execution_package_overlays`

## Required Repository Capabilities

## A. Install Registration Access

### Read capabilities
- get install by `execution_package_install_id`
- get active install for an `execution_surface_key`
- list install history for an `execution_surface_key`
- list installs by `authority_version_id`
- list installs by `install_status`
- list installs by `execution_surface_type`

### Write capabilities
- create install registration row
- mark install active
- mark install superseded, removed, failed, or repaired
- attach replacement or supersession linkage
- update install content-pointer metadata

### Invariants
- at most one active install row may exist for a given `execution_surface_key`
- active install truth is DB-primary and must not be inferred only from local metadata files
- install path fields are artifact pointers, not the canonical truth themselves

## B. Overlay Registration Access

### Read capabilities
- get overlay by `execution_package_overlay_id`
- list overlays for an `execution_package_install_id`
- get active overlay by `(execution_package_install_id, overlay_key)`
- list overlays for a `work_item_id`
- list overlays by `overlay_status`
- list overlays by `overlay_type`

### Write capabilities
- create overlay registration row
- mark overlay active
- mark overlay superseded, removed, failed, or repaired
- attach replacement or supersession linkage
- update overlay content-pointer metadata

### Invariants
- at most one active overlay row may exist for a given `(execution_package_install_id, overlay_key)`
- overlay activation truth is DB-primary and must not be inferred only from local overlay metadata files
- overlay rows remain historical even after removal or supersession

## C. Active Execution Package Resolution

### Read capabilities
- resolve active installed execution context for an `execution_surface_key`
- resolve active package identity and authority version for a repo/runtime root
- resolve all active overlays on the active install for an execution surface
- resolve whether an execution surface has any active install at all

### Invariants
- consumers should ask this repository for active install and overlay state rather than scanning local directories directly
- active execution-package resolution must be deterministic from DB state plus referenced artifact paths

## D. Installed Artifact Access

### Read capabilities
- load installed manifest content for an active install
- load installed package metadata content for an active install
- resolve installed docs root and artifact root paths
- resolve overlay root and metadata paths for active overlays
- resolve installed package-local package and brief artifact paths when present

### Non-goal
- this repository does not reinterpret source-authority publication inputs
- it only exposes the installed execution-time package surface

### Invariants
- file reads are allowed here because the installed package is a legitimate local runtime input surface
- but those reads must be anchored through an active install or overlay registration row

## E. Repair And Reconciliation Support

### Read capabilities
- list execution surfaces with no active install row
- list installs missing expected artifact pointers
- list overlays whose artifact paths are missing
- list installs or overlays requiring manual repair

### Write capabilities
- mark install or overlay repaired
- persist explicit repair metadata and deactivation reasons
- repair or backfill missing install/overlay registration pointers when the underlying installed artifacts are known-good

### Invariants
- repair actions must become durable registration history, not ad hoc local fixes only
- local artifact repair without DB registration repair is not sufficient

## F. Lookup And Resolution Support

### Read capabilities
- resolve `authority_version_id` from active install state
- resolve likely `design_package_id` or `coder_run_brief_id` linkage from installed metadata when that linkage is materialized
- resolve install rows by repo root or runtime root path

### Non-goal
- this repository does not become a general package-publication or authority-derivation service
- it only provides the minimum lookup support needed for execution-time resolution

## Contract Shape

The repository should expose bounded access groups rather than one flat method set.

Recommended contract groups:
- `installs`
- `overlays`
- `active_resolution`
- `artifacts`
- `repairs`
- `lookups`

This can still be implemented as one concrete repository component internally.

The important design rule is that consumers see explicit execution-package access boundaries.

## Transaction Boundaries

The repository should support atomic write groups for these cases.

### Case 1: package install registration
- create install registration row
- mark prior install superseded when applicable
- persist install artifact pointers in the same unit

### Case 2: overlay activation registration
- create overlay registration row
- supersede prior overlay row with the same overlay key when applicable
- persist overlay artifact pointers in the same unit

### Case 3: install removal or replacement
- mark install deactivated or superseded
- update replacement linkage
- deactivate or supersede dependent overlay rows when required by policy

### Case 4: repair registration
- mark install or overlay repaired
- persist repaired artifact pointers or repair metadata
- close invalid active rows in the same unit when compensation requires it

## Prohibited Access Patterns

Consumers of this repository must not:
- scan `.project/data/paa/authority/current/` and decide current install truth without checking DB registration rows
- scan overlay directories and decide active overlay truth without DB registration rows
- write workflow-state rows through this repository
- treat installed package files as the publication-time source of truth
- bypass the repository to mutate install or overlay registration state ad hoc

## Reporting Implication

This repository is the data source for future execution-package reports such as:
- active install per execution surface
- overlay activation history per slice
- install replacement chains
- repair-required execution surfaces
- active authority version coverage across consumer runtimes

Reporting tools should query through this repository or through a projection layer built from it.

## Final Conclusion

The `Execution Package Repository` is the fourth concrete DAL contract because it owns the remaining execution-time truth boundary between DB registration state and installed local runtime artifacts.

It gives PAA a structured access layer for:
- install registration truth
- overlay activation truth
- installed package artifact access
- execution-time package resolution

That is the correct boundary for stopping execution-package truth from being reconstructed out of:
- local metadata files alone
- directory scans
- ad hoc path assumptions.
