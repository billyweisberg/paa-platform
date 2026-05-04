# 90. Coder Brief Readiness Materializer

## Purpose
This note defines the first practical tool that turns Stage 1 design artifacts into execution-facing coder-brief state.

The materializer is intentionally small.
It does not replace PAA sequencing later.
It proves the derivation path now.

Script:
- `future `paa-platform` readiness materializer command`

## What it reads
The script reads:
- one Stage 1 design package
- one dependency graph slice
- one directory of `coder_run_brief*.json` artifacts

By default, it reads the dependency graph embedded in the Stage 1 package.

It can also read from PAA directly using:
- `design_packages.package_json`
- `coder_run_briefs.brief_json`
- `component_dependency_edges`

## What it writes
For each coder brief, it materializes:
- `execution_prerequisites`
- `execution_readiness`

Those sections contain:
- prerequisite briefs
- blocking dependency edges
- parallel-safe peers
- shared-surface conflicts
- sequencing notes
- readiness class
- dependency readiness rows
- blocking causes
- recommended next owner
- readiness snapshot source

## Why this matters
This is the first point where sequencing stops being separate planning prose and becomes execution-facing authority.

A coder lane can now be told, directly in the brief:
- whether execution is allowed yet
- which upstream brief must land first
- which blocking edge is still unresolved
- whether parallel execution is even on the table

That is a major step up from relying on humans to mentally reconcile the graph.

## Current computation model
The materializer is deliberately conservative.

It currently uses:
- Stage 1 package approval state
- incoming hard dependency edges
- sequencing requirement sufficiency rules
- shared-surface conflict flags
- explicit parallel-safe edges

It then computes a readiness class such as:
- `execution_ready`
- `blocked_on_contract`
- `blocked_on_dependency`
- `parallel_ready`

## Current limitations
This first version now supports both:
- design artifacts on disk
- design package and brief records in PAA

But it still computes readiness from package and edge state rather than from a fuller orchestration runtime.

That means:
- edge dependency statuses are still fairly simple
- parallel-group assignment is provisional
- it inserts sequence-state snapshots, but does not yet reconcile active coder runs or verification outcomes

That is acceptable for now.
The goal is to prove the materialization path before wiring it into the database runtime.

## Example
Base run against the retirement subsystem proving set:

```bash
python3 future `paa-platform` readiness materializer command \
  --design-package <producer_repo>/docs/architecture/tom-baby7-fractal-core/artifact-examples/stage1_design_package.retirement_subsystem_decomposition.example.json \
  --brief-dir <producer_repo>/docs/architecture/tom-baby7-fractal-core/artifact-examples \
  --write
```

Expected result:
- `RetirementPolicyResolver` -> `execution_ready`
- `RetirementLifecycleExecutor` -> `blocked_on_contract`
- `RetirementBoundaryDiagnostics` -> `blocked_on_contract`

PAA-backed run:

```bash
python3 future `paa-platform` readiness materializer command \
  --db-package-id-external fcore-stage1-2026-05-02-retirement-subsystem-decomposition \
  --db-write
```

This mode:
- reads the proving package from `paa.design_packages`
- reads briefs from `paa.coder_run_briefs`
- reads dependency statuses from `paa.component_dependency_edges`
- updates `brief_json` in `paa.coder_run_briefs`
- appends a new snapshot row in `paa.coder_brief_sequence_states`

Simulated rerun after resolver contract readiness:

```bash
python3 future `paa-platform` readiness materializer command \
  --design-package <producer_repo>/docs/architecture/tom-baby7-fractal-core/artifact-examples/stage1_design_package.retirement_subsystem_decomposition.example.json \
  --brief-dir <producer_repo>/docs/architecture/tom-baby7-fractal-core/artifact-examples \
  --set-edge-status edge-executor-needs-resolver-contract=contract_ready \
  --set-edge-status edge-diagnostics-needs-resolver-contract=contract_ready \
  --write
```

Expected result:
- `RetirementLifecycleExecutor` becomes eligible beyond contract blocking
- `RetirementBoundaryDiagnostics` becomes eligible beyond contract blocking
- TechLead or the future sequencing runtime still decides whether true parallel execution is approved

## Next step
The next evolution should be:
- reconcile active coder runs and verification state with sequence readiness
- materialize approved parallel sets rather than single-brief readiness only
- generate coder-brief packet content from that live state rather than from static examples alone
