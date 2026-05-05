# Phase D Mini Plan: Branch And Worktree Lineage Persistence

## Summary

Implement the first explicit lineage layer for the TechLead hub model so branch ownership and worktree state are no longer implied only by prompts, queue packets, or Git history.

Chosen scope:
- persist canonical branch and optional role branch lineage inside the existing control spine
- record TechLead branch ownership decisions alongside assignment and decision packets
- surface lineage in TechLead reporting
- keep the initial implementation metadata-first
- do **not** introduce automatic branch mutation in this slice
- do **not** split DB roles in this slice
- do **not** require a new dedicated lineage table if packet and queue metadata are sufficient for the first pass

This phase is about making branch state durable and queryable before we automate more branch behavior.

## Implementation Changes

### 1. Define a lineage metadata contract
Add a small, explicit lineage payload contract for TechLead-controlled issue flow.

Required first-pass fields:
- `canonical_branch`
- `role_branch`
- `branch_owner_role`
- `lineage_state`
- `lineage_action`
- `source_branch`
- `superseded_branch`
- `worktree_hint`
- `reset_reason`

Initial meaning:
- `canonical_branch`: durable issue branch, for example `issue-123`
- `role_branch`: optional role worktree branch, for example `issue-123-qa`
- `branch_owner_role`: normally `TechLead`
- `lineage_state`: `active`, `superseded`, `reset_required`, `closed`
- `lineage_action`: `created`, `reused`, `reset`, `superseded`, `closed`
- `source_branch`: branch the new role branch was derived from
- `superseded_branch`: prior branch replaced by this one
- `worktree_hint`: stable hint for automation worktree naming
- `reset_reason`: required when lineage action is `reset`

### 2. Persist lineage on TechLead packet families
Extend:
- `techlead_assignment_packet`
- `techlead_decision_packet`

to include the first-pass lineage metadata.

Rules:
- every emitted TechLead assignment must carry `canonical_branch`
- role-targeted assignment packets may include `role_branch`
- every TechLead decision packet must carry the branch state transition it is recording
- this remains packet-level metadata first, not a separate branch registry yet

### 3. Preserve lineage through queue and DB persistence
Reuse the existing queue/control spine:
- `paa.handoffs`
- `paa.queue_messages`
- `paa.automation_runs`

Persist lineage through `metadata_json` and/or packet payload rather than adding a new table in the first pass.

Minimum DB objective:
- given an issue number, we can reconstruct the current canonical branch, latest role branch, and last lineage action from persisted packet and queue records

### 4. Surface lineage in TechLead reporting
Update TechLead runtime/reporting so the report includes:
- canonical branch
- active role branch if any
- branch owner role
- lineage state
- latest lineage action
- whether a reset or supersession is pending

Important behavior:
- TechLead report becomes the control view for issue branch state
- branch state should no longer need to be inferred from free-form comments or only from GitHub PR branch names

### 5. Keep branch mutation manual but explicit
Do not add automatic git branch creation or deletion in this slice.

Instead:
- packet payloads and reports state what branch action is required
- human or later automation performs the actual git mutation
- this keeps the slice narrow and fail-closed

## Test Plan

### Schema and packet checks
- validate that TechLead assignment and decision packets can carry lineage metadata
- validate compile output includes canonical branch for supported cases
- validate role branch is present only when appropriate

### Persistence checks
- send a TechLead assignment packet with lineage metadata
- confirm queue and PAA persistence retain the lineage fields
- send a TechLead decision packet with a reset or supersession action
- confirm the later packet becomes the visible current lineage state

### Reporting checks
- confirm TechLead report includes current branch lineage section
- confirm reset/superseded states are surfaced clearly
- confirm no lineage fields are silently dropped when loading historical packet records

### Compatibility checks
- confirm Phase C emission still works without requiring automatic branch creation
- confirm packets that only include canonical branch still validate
- confirm existing worker result packets remain accepted in the current transition model

## Assumptions and defaults

- Phase D is a persistence and reporting slice, not a git automation slice.
- TechLead remains the branch owner in the consumer-side hub model.
- Canonical branch stays `issue-<issue_number>`.
- Role branches remain optional and deterministic, for example `issue-<issue_number>-qa`.
- Existing packet families are extended before any new branch-specific schema family is introduced.
- If metadata-first persistence proves insufficient, a dedicated lineage table can be a later follow-up, not the default starting point.
