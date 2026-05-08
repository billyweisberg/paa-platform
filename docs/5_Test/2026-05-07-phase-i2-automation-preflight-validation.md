# Phase I2 Automation Preflight Validation

## Purpose

Validate the deterministic pre-run no-work gate for the current proven consumer role set.

## Command surface

Top-level consumer wrapper:
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-consumer automation-preflight`

Supported roles in this slice:
- `techlead`
- `delivery-architect`
- `python-team`
- `qa`

## Zero-work validation

With all three queues empty, the command returned `should_invoke_model = false` for:
- `techlead`
- `delivery-architect`
- `python-team`
- `qa`

Observed gate result:
- `skip_model_invocation = true`
- `gate_reason = no_*_work_detected`
- `next_step_hint = exit_without_model_invocation`

This proves queue polling can happen without waking the model when there is no work.

## Positive-path validation

A disposable `techlead_assignment_packet` for `Python Dev` was sent to:
- `fractal-core-python`

Observed gate result for `python-team` while the packet was waiting:
- `should_invoke_model = true`
- `skip_model_invocation = false`
- `gate_reason = claimable_assignment_packet_available`
- `queue_candidates[0].schema_type = techlead_assignment_packet`

The test packet was then:
- claimed with `queue-claim-next --claimed-by phase-i2-preflight`
- acknowledged with `queue-ack`

Observed gate result after cleanup:
- `should_invoke_model = false`
- `skip_model_invocation = true`

## Current slice boundary

This slice proves:
- deterministic non-model gating based on queue/runtime state
- role-aware gate answers for the current proven role set
- no-work scheduled polling can exit without model invocation

This slice does not yet prove:
- environment-variable correctness
- cwd/worktree/`uv` execution correctness
- full role execution readiness
