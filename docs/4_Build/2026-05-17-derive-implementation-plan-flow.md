# Derive Implementation Plan Flow

Date: 2026-05-17

## Purpose

Record the first producer-side flow that materializes `ImplementationPlan` truth from a Stage 1 design package for the proof slice.

## Flow

1. evaluate derivation readiness for the Stage 1 package
2. ensure component elements and realizations exist for the service-oriented target taxonomy
3. derive implementation-plan activities from:
   - component
   - component elements
   - code artifact targets
4. persist the implementation-plan root, activities, and dependencies
5. emit an implementation-plan artifact for operator review
6. connect the persisted `implementation_plan_id` forward into `paa.coder_run_briefs` during brief assembly

## Proof Slice

Validated against:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-component-design-planning-service-stage1-design-package.json`

Derived artifact:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-component-design-planning-service-implementation-plan.json`

Connected draft brief artifact:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-component-design-planning-service-assembled-draft-coder-run-brief.json`

## Commands

```bash
PYTHONPATH=packages/paa-core/src:packages/paa-producer/src python -m paa_producer.__main__ derive-implementation-plan \
  --design-package docs/2_Design/2026-05-16-component-design-planning-service-stage1-design-package.json \
  --output docs/2_Design/2026-05-17-component-design-planning-service-implementation-plan.json
```

```bash
PYTHONPATH=packages/paa-core/src:packages/paa-producer/src python -m paa_producer.__main__ assemble-coder-brief \
  --design-package docs/2_Design/2026-05-16-component-design-planning-service-stage1-design-package.json \
  --output docs/2_Design/2026-05-17-component-design-planning-service-assembled-draft-coder-run-brief.json
```
