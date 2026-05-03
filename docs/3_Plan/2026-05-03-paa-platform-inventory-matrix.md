# 2026-05-03 PAA Platform Inventory Matrix

## Purpose

This document is the first formal platform inventory for the PAA consolidation.

It exists to prevent another partial migration where repo topology is cleaned up but core platform capabilities remain stranded in transitional lanes.

This inventory is derived from:

- the staged lifecycle definition
- coder brief derivation docs
- Stage 1 design package and dependency graph contracts
- readiness materialization docs
- packet compiler and transport-trace docs
- the current producer/platform/consumer repo state

## Audit rule

This migration must be audited by **lifecycle stage and capability**, not only by repo/worktree spread.

A repo can look cleaner while still missing required platform capabilities.
That is exactly what happened when the first consolidation pass missed:

- `coder_run_brief` source artifacts
- `stage1_design_package` source artifacts
- `dependency_graph_slice` source artifacts
- parts of the derivation/runtime chain that only existed in transitional lanes and old docs

## Canonical target repos

### PAA platform repo
- repo: `paa-platform`
- role: platform source of truth
- owns:
  - shared producer/consumer packages
  - install/update tooling
  - queue/claim runtime
  - packet compilers
  - runtime resolver
  - platform schemas/templates
  - migration and operating docs

### Authority producer repo
- repo: `appdev`
- role: authority source producer
- owns:
  - source authority manifest
  - source authority docs
  - source derivation artifacts
  - source package publication config
  - producer-side repo-local PAA install

### Consumer runtime repo
- repo: `fractal-core-python`
- role: installed authority consumer and execution repo
- owns:
  - repo-local consumer-mode PAA install
  - installed authority package
  - project-local automations and skills
  - mutable runtime state under `.project/data/paa/`

## Inventory matrix

| Lifecycle stage | Capability / artifact family | Required by docs | Current source of truth | Current installed/runtime location | Target home | Status | Gap / risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Stage 1 Design / Authoring | Authority manifest + schema | `79`, `82` | `appdev/docs/architecture/tom-baby7-fractal-core/project-authority/` | published package `authority/` and consumer install `authority/current/authority/` | `appdev` source, packaged for consumer | Consolidated | Good shape now. |
| Stage 1 Design / Authoring | Source authority docs | `79`, `82` | `appdev/docs/architecture/tom-baby7-fractal-core/` | selected docs in published package `docs/` | `appdev` source, packaged selectively | Partial | Many advanced PAA docs still live only in transitional lanes. |
| Stage 1 Design / Authoring | Stage 1 design package source artifacts | `82`, `84` | `appdev/docs/architecture/tom-baby7-fractal-core/artifact-examples/stage1_design_package.*.json` | packaged under `artifacts/` and installed under consumer `authority/current/artifacts/` | `appdev` source and package | Consolidated for known slices | Need a formal rule for new slice generation and naming. |
| Stage 1 Design / Authoring | Dependency graph slice source artifacts | `82`, `83` | `appdev/docs/architecture/tom-baby7-fractal-core/artifact-examples/dependency_graph_slice.*.json` | packaged under `artifacts/` and installed under consumer `authority/current/artifacts/` | `appdev` source and package | Consolidated for known slices | No dedicated derivation command in `paa-platform` yet. |
| Stage 1 Design / Authoring | Artifact schemas for Stage 1 design packages and dependency graph | `82`, `83` | `appdev/docs/architecture/tom-baby7-fractal-core/artifact-schemas/` | packaged under `artifacts/` today via explicit config, not yet separated into a schema bundle in the installed package | `appdev` source + `paa-platform` schema bundle | Partial | Schema ownership split across producer docs and platform install. |
| Stage 2 Derivation | `coder_run_brief` source artifacts | `75`, `76`, `80`, `81` | `appdev/docs/architecture/tom-baby7-fractal-core/artifact-examples/coder_run_brief.*.json` | packaged under `artifacts/` and installed under consumer `authority/current/artifacts/` | `appdev` source and package | Consolidated for known slices | Good for source artifact migration; still missing compiled derivation flow in platform repo. |
| Stage 2 Derivation | `coder_run_brief` schema | `75`, `76`, `81` | `appdev/docs/architecture/tom-baby7-fractal-core/handoff-schemas/coder_run_brief.schema.json` | packaged under `artifacts/` today | `appdev` source + platform schema ownership | Partial | Schema currently piggybacks on artifact packaging instead of a formal platform schema install. |
| Stage 2 Derivation | Coder brief derivation method / field matrix | `80`, `81` | Transitional docs in `appdev-authority-source` | none | `appdev` docs or `paa-platform` design docs | Missing from canonical producer | The producer repo does not yet carry the key derivation-method docs that define how the system works. |
| Stage 2 Derivation | Stage 1 design package contract docs | `82`, `83`, `84`, `85` | Transitional docs in `appdev-authority-source` | none | `appdev` docs and `paa-platform` design docs | Missing from canonical producer | These are core platform docs and should not remain stranded. |
| Stage 2 Derivation | Readiness materializer script | `90` | Transitional source / installed home skill copies | `.codex/skills/fractal-core-authority/scripts/materialize_coder_brief_readiness.py` in consumer rescue/consolidation branch | `paa-platform` package/CLI | Missing from platform extraction | Still sourced from old skill copies, not from `paa-platform`. |
| Stage 2 Derivation | PAA-backed brief resolution | `93` | Transitional docs + old skill/runtime copies | current consumer skill copy and home skill copy | `paa-platform` producer/consumer tooling | Missing from platform extraction | Resolution path exists operationally but not yet owned by the platform repo. |
| Stage 3 Execution | `architect_cycle_packet` compiler | `94` | Transitional docs + old authority helper path | consumer/home skill copies via `project_authority.py` | `paa-platform` CLI/tooling | Missing from platform extraction | Core compiled packet path still not rehomed. |
| Stage 3 Execution | `slice_result_packet` compiler | `95` | Transitional docs + old authority helper path | consumer/home skill copies | `paa-platform` CLI/tooling | Missing from platform extraction | Same issue. |
| Stage 4 Verification | `qa_verification_packet` compiler | `95` | Transitional docs + old authority helper path | consumer/home skill copies | `paa-platform` CLI/tooling | Missing from platform extraction | Same issue. |
| Stage 3-4 Runtime | Packet compilation persistence in PAA | `96` | Concept/docs and old runtime helpers | PAA DB `automation_runs` | `paa-platform` DB migrations + runtime | Missing from platform extraction | Persistence model is documented but not yet rehomed under platform migrations/tooling. |
| Stage 3-5 Runtime | Compiled packet transport trace | `97` | Concept/docs and old runtime helpers | PAA DB queue/handoff tables + transport helpers | `paa-platform` queue runtime | Missing from platform extraction | Transport provenance remains outside the new platform repo. |
| Stage 3 Execution | Producer-mode PAA install | install contract docs | `appdev/.codex/paa/` | local producer command + `.project/data/paa/publish/` | `appdev` | Consolidated | This is now real and validated. |
| Stage 3 Execution | Consumer-mode PAA install | install contract docs | `fractal-core-python/.codex/paa/` | local consumer command + `.project/data/paa/authority/current/` | `fractal-core-python` | Consolidated locally | Branch exists cleanly now, but still needs push/review. |
| Stage 3 Execution | Project-local automations | workflow/ops docs | `fractal-core-python/.codex/automations/` on consolidation branch | repo-local | `fractal-core-python` | Consolidated locally | Still copied from `$HOME/.codex`; installer/sync command does not exist yet. |
| Stage 3 Execution | Project-local skills | workflow/ops docs | `fractal-core-python/.codex/skills/` on consolidation branch | repo-local | `fractal-core-python` | Consolidated locally | Still copied from `$HOME/.codex`; installer/sync command does not exist yet. |
| Stage 3-5 Runtime | Queue/claim runtime | `42`, `43`, `97` | old skill/runtime copies in producer transitional lanes and home `.codex` | role workspaces and home runtime | `paa-platform` package/runtime | Missing from platform extraction | One of the largest remaining migration blocks. |
| Stage 3-5 Runtime | TechLead reporting / traceability | `103` | old skill/runtime copies + docs in transitional lanes | home skill copy and repo-local copied skill | `paa-platform` CLI/reporting package | Missing from platform extraction | Reporting contract exists but platform ownership is not established. |
| Stage 5 Acceptance | Delivery-side acceptance flow | `79`, `94-97` | mixed between role automations, old helper scripts, GitHub | consumer repo and role workspaces | `fractal-core-python` + `paa-platform` runtime | Partial | Architect runtime behavior still depends on copied skills/automation logic. |
| Stage 6 Authority Update / Re-Derivation | Producer publication flow | install contract + producer publication docs | `appdev/.codex/paa/` + `appdev` source tree | package output in `.project/data/paa/publish/` | `appdev` with platform-owned publisher | Consolidated functionally | Still using copied library payload from `paa-platform` rather than a true installer/update command. |
| Cross-stage Governance | Role split: Authority Architect vs Delivery Architect | staged lifecycle + architecture cleanup | implicit in current discussion only | none | documented role model in `paa-platform` and producer/consumer repos | Missing | This needs to be codified, not just understood verbally. |
| Cross-stage Governance | Canonical startup / stale-workspace checks | operational need discovered in migration | ad hoc today | role workspaces and automations | `paa-platform` runtime + repo-local automations | Missing | This is the guardrail that would prevent another branch/workspace drift loop. |

## Current consolidation scorecard

### Completed or functionally cut over
- `appdev` is the canonical authority producer repo.
- `appdev` can publish a versioned authority package from repo-local PAA install.
- `fractal-core-python` now has a clean consumer consolidation branch with repo-local PAA install.
- source authority manifest is in the canonical producer repo.
- issue-specific coder brief, stage1 design package, and dependency-graph source artifacts are now in the canonical producer repo.
- published package now carries those artifacts.
- installed consumer package now carries those artifacts.

### Partially cut over
- selected source docs are in `appdev`, but many key PAA derivation/runtime docs still remain only in transitional lanes.
- consumer repo has repo-local automations and skills, but they were copied, not installed through a platform command.
- package format now carries artifacts, but schema ownership and install semantics still need tightening.

### Not yet cut over
- readiness materializer implementation
- packet compilers and their CLI entrypoints
- packet compilation persistence / transport trace runtime
- queue/claim runtime
- TechLead reporting runtime
- explicit role split documentation and enforcement
- startup stale-workspace validation
- platform installer/update commands for producer and consumer repos

## Gaps that must be closed before the next automation/runtime slice

### Gap 1: Core derivation and runtime docs are still stranded
The canonical producer repo still does not carry the full set of docs that define the PAA derivation/runtime model.

Minimum docs to migrate or rehome next:
- `75-coder-run-brief.md`
- `76-coder-run-brief-packet-integration.md`
- `79-paa-staged-lifecycle.md`
- `80-coder-brief-derivation-method.md`
- `81-coder-brief-field-derivation-matrix.md`
- `82-stage1-design-package-contract.md`
- `83-component-dependency-graph-contract.md`
- `84-stage1-schema-and-record-shape.md`
- `85-coder-brief-sequencing.md`
- `90-coder-brief-readiness-materializer.md`
- `93-paa-backed-architect-packet-brief-resolution.md`
- `94-architect-packet-compiler.md`
- `95-dev-and-qa-packet-compilers.md`
- `96-packet-compilation-persistence.md`
- `97-compiled-packet-transport-trace.md`
- `103-techlead-traceability-reporting.md`

### Gap 2: Platform code ownership is still wrong for the runtime chain
The runtime chain still depends on copied or home-installed skill code instead of first-class `paa-platform` packages/commands.

That affects:
- readiness materialization
- brief resolution
- packet compilers
- queue send/claim/ack helpers
- TechLead reporting

### Gap 3: Consumer automation payload is copied, not installed
The consumer repo now has the right files locally, but there is no canonical install/update command to keep:
- `.codex/paa/`
- `.codex/automations/`
- `.codex/skills/`

aligned with `paa-platform`.

### Gap 4: Role model is still implicit
We need a documented and enforced split between:
- Authority Architect on the producer side
- Delivery Architect on the consumer side

Without that, platform responsibilities will blur again.

### Gap 5: Stale-workspace protection is still missing
We need runtime checks that fail closed when a role workspace is:
- behind canonical `origin/main`
- detached from the installed authority package version
- operating from a stale PR-head snapshot when canonical mainline has already moved on

This is the operational guardrail the system is still missing.

## Recommended next sequence

1. migrate the core derivation/runtime docs into the canonical producer and/or platform repo
2. define the formal Authority Architect vs Delivery Architect role split
3. add producer and consumer install/update commands in `paa-platform`
4. move readiness materializer and packet compiler surfaces into `paa-platform`
5. move queue/claim runtime and TechLead reporting into `paa-platform`
6. add stale-workspace startup validation to repo-local automation workflows

## Decision rule for future migrations

A platform capability is not considered migrated until all of the following are true:

1. source docs describing the capability are in the canonical producer or platform repo
2. source artifacts for the capability are in the canonical producer repo if they are project-specific
3. runtime code for the capability is owned by `paa-platform`
4. consumer installation of the capability is performed by repo-local install/update flow, not by ad hoc copying
5. role ownership of the capability is explicit
