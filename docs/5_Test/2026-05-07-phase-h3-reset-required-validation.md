# Phase H3 Reset-Required Lifecycle Mutation Validation

## Goal

Validate the first cleanup-safe lifecycle mutation surface:
- `techlead-reset-required`
- `python-team` only
- no physical cleanup

## Commands used

Consumer repo:
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python`

### 1. Refresh installed consumer runtime

```bash
./.codex/paa/bin/paa-consumer update-consumer-runtime \
  --repo-root /Users/billyweisberg/Repos/billyweisberg/fractal-core-python
```

Observed result:
- `ok = true`

### 2. Verify command discovery

```bash
./.codex/paa/bin/paa-consumer help
```

Observed result:
- `techlead-reset-required` appears in the top-level command list

### 3. Validate fail-closed behavior on a non-reset fixture

Command:

```bash
./.codex/paa/bin/paa-consumer techlead-reset-required \
  --repo-root /Users/billyweisberg/Repos/billyweisberg/fractal-core-python \
  --package-id-external fcore-stage1-2026-05-02-issue106-retirement-boundary-diagnostics \
  --brief-id-external fcore-coder-2026-05-02-issue106-retirement-boundary-diagnostics
```

Observed result:
- `ok = false`
- `reason = reset_required_not_supported_for_current_stage`
- `workflow_stage = dev_in_progress`

And the returned payload still includes:
- `ownership_view`
- `stale_view`

That proves the command is:
- narrow
- query-rich
- fail-closed

### 4. Validate TechLead status schema still passes

```bash
./.codex/paa/bin/paa-consumer techlead-status --validate-schema
```

Observed result:
- command succeeded

## What this proves

Phase H3 is implemented as intended for the supported narrow boundary:
- it does not mutate branches or worktrees directly
- it reuses ownership and stale detection context
- it refuses non-reset workflow stages cleanly

## Remaining validation gap

A positive-path runtime test still requires a real or synthetic fixture where:
- `workflow_stage = dev_reset_required`

That follow-up should be part of the next lifecycle-mutation validation slice.
