# Coder Brief Authority Lifecycle Governance

Date: 2026-05-16

## Purpose

Close Priority 0 remediation item 3 by making the transition from:
- `draft_brief`
- `approved_brief`
- `packet_ready_execution_authority`

explicit in the architecture, process, and DB model.

This note defines the lifecycle model and the governance meaning of each state.

## Related Notes

- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-16-paa-derivation-remediation-backlog.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-coder-brief-derivation-method.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-coder-run-brief.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-coder-run-brief-packet-integration.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/010-step10-coder-brief-authority-lifecycle.sql`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-component-design-planning-service-slice-package-materialization.md`

## Problem Statement

The earlier model could persist coder briefs, but it still conflated:
- brief existence
- brief approval
- packet readiness
- active execution use

That meant a useful draft could be mistaken for execution authority.

The system needed a first-class answer to:
- is this brief only a draft?
- has it been approved?
- is it actually packet-ready authority for a coding lane?

## Lifecycle Decision

PAA now treats coder-brief authority as a distinct lifecycle separate from the broader artifact row status.

### Artifact status still answers
- does this row exist?
- is it active or superseded as a stored artifact?

### Authority lifecycle now answers
- is this brief still draft authority?
- is it approved for execution?
- is it packet-ready for transport and lane execution?

## Canonical Authority States

### `draft_brief`
Meaning:
- the brief exists as a derived artifact
- it may be structurally useful
- it is not yet execution authority

Typical allowed conditions:
- slice package exists
- target taxonomy may still be incomplete
- review may still be pending
- packet preparation has not been cleared

### `approved_brief`
Meaning:
- the brief has passed producer-side review/approval
- the brief is approved in content
- but it is not yet necessarily packet-ready for transport

Typical allowed conditions:
- review completed
- signoff complete for brief authority
- packet-specific checks may still be pending

### `packet_ready_execution_authority`
Meaning:
- the approved brief is now ready to be embedded in an `architect_cycle_packet`
- the coding lane may treat this artifact as execution authority

Typical required conditions:
- approved brief exists
- packet preparation checks passed
- embedded/ref-linked packet representation is ready
- any remaining blockers are resolved or explicitly waived by authority

### `superseded_authority`
Meaning:
- this brief was once part of the authority chain but has been replaced by a newer authority artifact

### `rejected_authority`
Meaning:
- this brief is not valid execution authority and must not progress without re-derivation or revision

## Transition Rules

Allowed transitions:
1. `draft_brief -> approved_brief`
2. `approved_brief -> packet_ready_execution_authority`
3. `draft_brief -> rejected_authority`
4. `approved_brief -> rejected_authority`
5. `draft_brief -> superseded_authority`
6. `approved_brief -> superseded_authority`
7. `packet_ready_execution_authority -> superseded_authority`
8. `rejected_authority -> draft_brief` only through explicit re-open / re-derivation

Forbidden shortcut:
- do not treat `draft_brief` as execution authority just because the brief body exists

## DB Model

Primary DB support now consists of:
- `paa.coder_run_briefs.authority_state`
- `paa.coder_run_briefs.authority_state_updated_at`
- `paa.coder_run_briefs.approved_at`
- `paa.coder_run_briefs.packet_ready_at`
- `paa.coder_run_briefs.approval_json`
- `paa.coder_run_briefs.packet_preparation_json`
- `paa.coder_brief_authority_events`

### Why this is sufficient for Priority 0

This gives the system:
- one queryable current authority state
- timestamps for approval and packet readiness
- explicit review / packet-preparation metadata surfaces
- a durable transition history table

That is enough to stop the draft/approved/packet-ready conflation that blocked the proof slice.

## Proof-Slice Application

For `Component Design Planning Service`:
- a governed draft brief may exist after derivation
- it must remain `draft_brief` until review/approval is completed
- it must not become execution authority until it reaches `packet_ready_execution_authority`

That means the proof slice can now be represented honestly in DB state as:
- package materialized
- taxonomy extended
- brief still draft or review-bound

instead of pretending the existence of a draft JSON file means the run is launch-ready.

Persisted proof-slice governed draft:
- brief artifact:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-component-design-planning-service-governed-draft-coder-run-brief.json`
- `coder_run_brief_id`:
  - `fceab499-60f4-4a11-851d-b1059d8dbde9`
- initial authority event:
  - `transition_kind = derive_draft`
  - `to_state = draft_brief`

## Decision

Decision:
- `Priority 0 item 3 complete`

Meaning:
- the authority lifecycle is now explicit enough to govern coder-brief execution authority cleanly

Not implied:
- the proof slice is not automatically approved or packet-ready
- implementation still does not resume from thread memory alone
- the next work is to make the producer-side derivation path executable and then re-run the proof slice through that refined path
