# Phase H3 Positive-Path Reset-Required Fixture Validation

## Goal

Create a disposable synthetic `dev_reset_required` fixture and validate the positive Phase H3 path against it.

## Why a synthetic fixture was used

At the time of validation, there was no live consumer issue fixture currently sitting in:
- `workflow_stage = dev_reset_required`

So this validation uses a repeatable synthetic runtime fixture instead of mutating live queue state or pretending that the current active issue is in reset-required recovery.

## Harness script

Repo-owned validation harness:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/runtime/validate_phase_h3_reset_required_fixture.py`

Execution command:

```bash
uv run --python 3.12 --no-project python \
  /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/runtime/validate_phase_h3_reset_required_fixture.py
```

## What the harness does

The harness:
1. creates a disposable synthetic QA packet file under the consumer repo reports directory
2. patches the TechLead lineage view to a controlled `dev_reset_required` state
3. runs the real `reset_required_lifecycle()` path
4. lets the real decision compiler/validator run
5. verifies the result fields before exiting

This validates the Phase H3 command logic without requiring a live reset incident on the real issue board.

## Observed result

The harness returned:
- `ok = true`
- `workflow_stage = dev_reset_required`
- `target_role = python-team`
- `cleanup_candidate = true`
- `worktree_staleness.status = stale`
- `worktree_staleness.reasons = ["lineage_state_reset_required"]`

And the embedded decision result returned:
- `ok = true`
- `decision_type = reset_branch`
- `lineage_state = reset_required`
- `lineage_action = reset`
- `resolved_queue = fractal-core-architecture`
- `sent = false`

## What this proves

Phase H3 now has both:
- fail-closed validation on a non-reset live fixture
- positive-path validation on a repeatable synthetic reset-required fixture

That is enough to say the slice is behaving as designed within its current narrow scope.

## Important boundary

This still does **not** prove physical cleanup behavior.

The current slice proves:
- lifecycle mutation planning
- ownership/staleness integration
- decision compilation/validation

The next lifecycle slice should decide how physical reset cleanup will consume this state.
