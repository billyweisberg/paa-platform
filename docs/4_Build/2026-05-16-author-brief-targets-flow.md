Title: Author Brief Targets Flow
Doc-ID: paa-author-brief-targets-flow
Doc-Type: runbook
Status: active
Lifecycle-Stage: build
Created: 2026-05-19
Last-Edited: 2026-05-19
Author: Billy Weisberg
Repo: paa-platform
Component: BriefTargetAuthor
Domain: brief-target-authoring
Keywords: brief-targets, producer, authoring, build, flow
Depends-On: 2026-05-16-assemble-coder-brief-flow.md, 2026-05-16-derive-design-package-flow.md
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
Summary: Defines the producer-side flow for materializing explicit brief targets from a derivation-ready slice package and draft coder brief.

# Author Brief Targets Flow

Date: 2026-05-16
Status: active build-flow authority

## Purpose

Define and implement the producer-side derivation step that materializes explicit brief targets from a derivation-ready slice package and an assembled draft coder brief.

This flow is the bridge from:
- draft brief body

into:
- component element instances
- realization instances
- ordered coder-brief realization targets

for one execution-authoritative slice.

## Implementation Surfaces

CLI wiring:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-producer/src/paa_producer/__main__.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-producer/src/paa_producer/commands.py`

Producer flow:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-producer/src/paa_producer/brief_target_author.py`

Repository support extended for this flow:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/repositories/component_design/contracts.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/repositories/component_design/models.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/repositories/component_design/postgres.py`

Tests:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/tests/unit/test_component_design_repository.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/tests/unit/test_brief_target_author.py`

## What the flow does

`paa-producer author-brief-targets` now:
- requires a derivation-ready Stage 1 package
- ensures the draft coder brief exists in DB
- materializes component-element instances for the active slice component
- materializes realization instances for the service-oriented target model
- materializes ordered `paa.coder_brief_realization_targets`
- preserves idempotence on rerun by upserting all three layers

## Proof Slice Validation

Proof-slice validation ran against:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-component-design-planning-service-stage1-design-package.json`

Generated output artifact:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-component-design-planning-service-authored-brief-targets.json`

Persisted proof-slice brief:
- `coder_run_brief_id = fceab499-60f4-4a11-851d-b1059d8dbde9`

Persisted proof-slice target model:
- `paa.component_elements = 4` rows for the service component
- `paa.component_element_realizations = 5` rows for the service component
- `paa.coder_brief_realization_targets = 5` rows for the proof-slice brief

Authored target chain:
1. `interfaces -> service_interface`
2. `data_contract -> dto`
3. `functions -> service_implementation`
4. `verification_surfaces -> test_module`
5. `interfaces -> package_export`

Observed execution order for the proof slice:
- `10 -> 20 -> 30 -> 40 -> 50`

Observed dependency chain for the proof slice:
- `dto` depends on `service_interface`
- `service_implementation` depends on `dto`
- `test_module` depends on `service_implementation`
- `package_export` depends on `service_implementation`

## Important design correction captured by this run

The proof slice is no longer repository-shaped at the target level.

The target model now cleanly supports a service slice with explicit artifacts for:
- service interface
- DTO/data contract
- service implementation
- test module
- package export

That is a better match to the actual service component spec than the earlier repository-oriented examples.

## Validation Commands

Unit tests:
```bash
PYTHONPATH=packages/paa-core/src:packages/paa-producer/src python -m unittest tests.unit.test_component_design_repository tests.unit.test_derivation_readiness tests.unit.test_brief_target_author
```

Proof-slice materialization:
```bash
PYTHONPATH=packages/paa-core/src:packages/paa-producer/src python -m paa_producer author-brief-targets \
  --design-package docs/2_Design/2026-05-16-component-design-planning-service-stage1-design-package.json \
  --output docs/2_Design/2026-05-16-component-design-planning-service-authored-brief-targets.json
```

## Exit Result

This governed build-flow slice is established for the proof path.

The next remaining Priority 1 blocker at this point in the sequence was:
- `review-coder-brief`