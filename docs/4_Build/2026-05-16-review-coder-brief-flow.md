# Build Note: `review-coder-brief` Flow

Date: 2026-05-16
Status: `implemented and validated`

## Purpose

Define and implement the producer-side governed review step for coder briefs.

This flow closes the remaining Priority 1 governance gap between:
- a persisted draft brief with authored targets

and:
- an explicitly approved producer-side authority artifact

It makes brief approval a real action with:
- transition checks
- persisted approval metadata
- authority-event history
- idempotent rerun behavior

## Implementation Surfaces

CLI wiring:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-producer/src/paa_producer/__main__.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-producer/src/paa_producer/commands.py`

Producer flow:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-producer/src/paa_producer/brief_reviewer.py`

Tests:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/tests/unit/test_brief_reviewer.py`

## What the flow does

`paa-producer review-coder-brief` now supports governed decisions:
- `approve`
- `reject`
- `reopen-draft`

The flow can resolve the target brief by:
- `--coder-run-brief-id`
- or `--design-package`

For an approval decision, it validates:
- the current authority state allows approval
- the brief readiness class is `derivation_ready`
- realization targets are already materialized

When the transition is valid, it updates:
- `paa.coder_run_briefs.authority_state`
- `paa.coder_run_briefs.status`
- `paa.coder_run_briefs.approved_at`
- `paa.coder_run_briefs.approval_json`

And it appends a durable event row to:
- `paa.coder_brief_authority_events`

## Idempotence behavior

If the requested decision would keep the brief in its current authority state, the command returns a clean no-op result instead of failing.

That means a rerun on an already approved brief:
- preserves the prior approval state
- does not append a duplicate approval event
- still reports the current governed state and review checks

## Proof Slice Validation

Validated against:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-component-design-planning-service-stage1-design-package.json`

Generated approval artifact:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-component-design-planning-service-brief-review-approval.json`

Persisted proof-slice brief:
- `coder_run_brief_id = fceab499-60f4-4a11-851d-b1059d8dbde9`

Validated governed state in DB:
- `authority_state = approved_brief`
- `status = approved`
- `approved_at` populated
- `approval_json` populated with review summary and notes

Validated authority-event history for the proof slice:
1. `derive_draft`
2. `approve_brief`

That confirms the slice is no longer only a useful draft. It is now a governed approved brief.

## Validation Commands

Unit tests:
```bash
PYTHONPATH=packages/paa-core/src:packages/paa-producer/src python -m unittest tests.unit.test_brief_reviewer
```

Proof-slice review:
```bash
PYTHONPATH=packages/paa-core/src:packages/paa-producer/src python -m paa_producer review-coder-brief \
  --coder-run-brief-id fceab499-60f4-4a11-851d-b1059d8dbde9 \
  --decision approve \
  --review-summary "Proof slice approved after target authoring validation." \
  --notes "Approved through producer-side governed review flow." \
  --output docs/2_Design/2026-05-16-component-design-planning-service-brief-review-approval.json
```

## Exit Result

This remediation item is complete.

The next move is no longer producer-side derivation completion for Priority 1.
The next move is to use the proof slice again against the now-complete Priority 1 path.
