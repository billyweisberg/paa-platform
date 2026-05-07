# Phase I Canonical E2E Runbook

This is the canonical current-state end-to-end slice for the proven role set:
- `TechLead`
- `Delivery Architect`
- `Python Dev`
- `QA`

It is the acceptance runbook for Phase I hardening.

## Scope

This runbook validates:
- assignment emission
- role bridge surfaces
- role result return
- queue alignment
- branch/worktree alignment
- TechLead follow-up decision surfaces

This runbook does not require:
- broader worker-role families
- automatic role execution
- automatic branch retirement beyond already-built lifecycle commands

## Canonical path

### 1. Delivery Architect assignment
- emit assignment from `TechLead` to `Delivery Architect`
- confirm packet family:
  - `techlead_assignment_packet`
- confirm queue:
  - `fractal-core-architecture`

### 2. Delivery Architect return
- prepare role branch/worktree as needed
- return result via:
  - `delivery_review_packet`
- confirm TechLead can interpret:
  - `ready_for_dev`

### 3. TechLead routes to Python Dev
- emit assignment from `TechLead` to `Python Dev`
- confirm queue:
  - `fractal-core-python`
- confirm branch/worktree preparation surfaces work

### 4. Python Dev return
- return result via:
  - `worker_result_packet`
- confirm TechLead can interpret:
  - worker review pending
- confirm next assignment derives to:
  - `QA`

### 5. QA assignment
- emit assignment from `TechLead` to `QA`
- confirm queue:
  - `fractal-core-qa`
- confirm branch/worktree preparation surfaces work

### 6. QA return
- return result via:
  - `qa_verification_packet`
- confirm TechLead sees the QA result and can derive or record the next decision

### 7. TechLead decision
- validate that TechLead can record the resulting decision path using:
  - `techlead_decision_packet`

### 8. Lifecycle fallback
If the slice transitions into a failure or terminal state, the already-built lifecycle surfaces are available:
- `techlead-reset-required`
- `techlead-reset-cleanup`
- `techlead-superseded-cleanup`
- `techlead-closed-cleanup`

## Required active packet families

- `techlead_assignment_packet`
- `techlead_decision_packet`
- `delivery_review_packet`
- `worker_result_packet`
- `qa_verification_packet`

Legacy compatibility only:
- `slice_result_packet`

## Required wrapper surfaces

- `techlead-emit-next-assignment`
- `techlead-lineage`
- `techlead-prepare-role-branch`
- `techlead-prepare-role-worktree`
- `techlead-handoff-to-role-worktree`
- `techlead-inspect-role-worktree`
- `techlead-role-entry`
- `techlead-role-result-assist`
- `techlead-role-return`
- `techlead-emit-decision`
- `techlead-worktree-ownership`
- `techlead-worktree-stale`
- lifecycle cleanup commands

## Pass conditions

- no queue-resolution ambiguity
- no branch/worktree ownership ambiguity
- no prompt/runtime contradiction on active paths
- no need to use legacy `slice_result_packet` on the active Python lane
- TechLead remains the routing hub throughout

## Fail conditions

- any spoke-to-spoke routing requirement reappears
- active prompts teach a different packet family than the runtime uses
- queue names or target roles require manual correction
- worktree ownership is not deterministically attributable
- lifecycle cleanup commands contradict lineage state
