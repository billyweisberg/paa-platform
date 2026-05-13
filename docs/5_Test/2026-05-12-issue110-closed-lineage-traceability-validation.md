# Issue 110 Closed-Lineage And Traceability Validation

Date: 2026-05-12

## Goal

Resolve the closed-slice reporting drift for issue `110` so that:
- `techlead-lineage` reports the slice as `closed`
- the DB-backed full-chain traceability view reports the slice as `accepted_full_chain`
- `techlead-status` reports issue `110` as the latest accepted chain

## Root Causes

1. `techlead-lineage` only derived closeout state from queue previews and active branch state.
   - After `techlead-accept-and-merge`, the terminal closeout packet auto-acks.
   - With no queue head remaining, lineage fell back to an older active-role interpretation.

2. Accepted-chain reporting for Team Worker slices was incomplete.
   - `techlead-closeout-qa-pass` did not persist a TechLead `acceptance_event` for accepted QA passes.
   - `paa.v_work_item_full_chain_traceability` still treated only `packet_compilation:slice_result_packet` as the dev leg.
   - send-time evidence persistence ignored `worker_result_packet`, so Team Worker Python legs did not contribute dev evidence rows.

## Fixes Applied

### 1. Local closeout fallback for lineage

Updated:
- `packages/paa-consumer/src/paa_consumer/techlead.py`

Changes:
- `techlead-lineage` now consults the latest repo-local `techlead_decision.issue<issue>.closed.json` artifact when the closeout packet has already auto-acked.
- Closed local decision state can override stale active-branch inference when GitHub and queue state are consistent with closure.

### 2. Persist accepted closeout decisions into `paa.acceptance_events`

Updated:
- `packages/paa-consumer/src/paa_consumer/techlead.py`

Changes:
- `techlead-closeout-qa-pass` now persists an `accepted` `acceptance_event` for merged/closed QA-pass slices.
- The same persistence path is shared by the autonomous `techlead-accept-and-merge` flow.
- DB argument defaults were hardened so direct CLI closeout runs can execute the persistence path without special parser wiring.

### 3. Team Worker dev-leg traceability support

Updated:
- `packages/paa-core/src/paa_core/sql/full_chain_reporting_view.sql`
- `packages/paa-core/src/paa_core/handoff_runtime.py`

Changes:
- the full-chain traceability view now recognizes both:
  - `packet_compilation:slice_result_packet`
  - `packet_compilation:worker_result_packet`
  as valid dev-leg compilation runs
- send-time evidence persistence now supports `worker_result_packet`
  - validation commands from `payload.validation_summary` are normalized into dev evidence rows

## Backfill Applied For Issue 110

Because issue `110` completed before the Team Worker evidence persistence fix landed:
- the updated full-chain reporting view SQL was applied to the active PAA DB
- the existing worker result packet artifact was replayed through the persistence helper to backfill dev evidence for issue `110`

Backfilled packet:
- `<consumer_repo_root>/.project/data/paa/reports/worker-result.issue110.python-dev.json`

## Validation Results

### Slice-specific lineage

Command result:
- `workflow_stage = techlead_decision_recorded`
- `current_owner_role = TechLead`
- `lineage.lineage_state = closed`
- `lineage.latest_lineage_action = closed`
- `lineage.current_packet_type = techlead_decision_packet`

### DB-backed traceability row for issue 110

Observed row state:
- `full_chain_state = accepted_full_chain`
- `acceptance_decision = accepted`
- `dev_compilation_run_id IS NOT NULL = true`
- `qa_compilation_run_id IS NOT NULL = true`
- `dev_evidence_count = 3`
- `qa_evidence_count = 1`
- `component_name = TeamWorkerAutomationPilotNote`

### TechLead status traceability section

Observed report state:
- `traceability.latest_accepted_chain.issue_number = 110`
- `traceability.latest_accepted_chain.full_chain_state = accepted_full_chain`
- `traceability.latest_accepted_chain.component_name = TeamWorkerAutomationPilotNote`

## Residual Note

`techlead-status` still reports the top-level idle workflow summary as:
- `workflow.current_stage = blocked`
- `workflow.current_owner_role = Unknown`

when all queues are empty and there is no active work. That is a separate idle-state summary behavior, not an issue `110` closed-slice drift defect.
