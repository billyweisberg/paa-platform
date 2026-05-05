# TechLead Hub Implementation Delta Plan

## Purpose

Translate the TechLead hub-and-spoke workflow design into a concrete implementation plan against the current `paa-platform` codebase and runtime surfaces.

This note defines the actual deltas required in five areas:

1. queue destination changes
2. packet compiler changes
3. new schema additions
4. DB metadata additions for branch lineage
5. automation prompt changes per role

It is intentionally incremental.
The goal is to move the existing mesh workflow into the hub model without breaking the current control spine.

Related design notes:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-04-current-mesh-vs-techlead-hub-spoke.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-04-techlead-hub-packet-and-decision-vocabulary.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-04-techlead-hub-state-and-routing-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/6_Deploy/2026-05-03-worktree-branch-strategy.md`

## Executive summary

The current codebase is still wired to the mesh in three major places:

- queue destinations still assume `Architect -> Python Dev -> QA -> Architect`
- packet compilers still emit old `from_role` / `to_role` combinations
- automation prompts still teach the old branch policy and role-to-role behavior

The least risky migration sequence is:

1. redirect existing packets to `TechLead` first
2. introduce TechLead-issued assignment/decision packets second
3. add branch lineage metadata during that shift
4. update automation prompts and skills to the new authority model at the same time
5. only then generalize worker schemas beyond Python-specific names

## Current implementation touchpoints

### Queue runtime

Current central queue runtime:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/handoff_runtime.py`

Important current assumptions:
- `SUPPORTED_SCHEMA_TYPES = {"architect_cycle_packet", "qa_verification_packet", "slice_result_packet"}`
- role mapping still assumes:
  - `Architect`
  - `Python Dev`
  - `QA`
  - `TechLead`
- `DEFAULT_QUEUES` still only models the current queue set:
  - `fractal-core-architecture`
  - `fractal-core-qa`
  - `fractal-core-python`

### Packet compilers

Current compiler entrypoints:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-producer/src/paa_producer/authority_runtime.py`

Current compiled packet assumptions:
- `materialize-architect-packet`
  - emits `schema_type = architect_cycle_packet`
  - `from_role = architect`
  - `to_role = python-team`
- `materialize-slice-result-packet`
  - emits `schema_type = slice_result_packet`
  - `from_role = python-team`
  - `to_role = args.to_role`
- `materialize-qa-verification-packet`
  - emits `schema_type = qa_verification_packet`
  - `from_role = qa`
  - `to_role = args.to_role`

### Consumer runtime

Current consumer queue wrapper:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-consumer/src/paa_consumer/delivery_runtime.py`

Current TechLead runtime/reporting:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-consumer/src/paa_consumer/techlead.py`

Important current assumptions:
- queue names are still modeled as:
  - `fractal-core-python`
  - `fractal-core-qa`
  - `fractal-core-architecture`
- report logic still reasons about architecture, dev, and QA queues in the old shape

### Prompt and skill layer

Current automation and skill sources:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/project-packs/fractal-core/automations/`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/project-packs/fractal-core/skills/`

Important current prompt mismatch:
- prompts and skills still teach:
  - one shared branch per issue: `issue-<issue_number>`
- but the current worktree strategy note allows:
  - canonical branch: `issue-<issue_number>`
  - optional role branches: `issue-<issue_number>-<role>`

That mismatch must be corrected before hardening automations.

## 1. Queue destination changes

## Goal

Make `TechLead` the only consumer-side routing hub without immediately requiring new packet schemas everywhere.

## Current behavior

Live and coded route pattern:
- `Architect -> Python Dev`
- `Python Dev -> QA`
- `QA -> Architect`

## Target behavior

During transition:
- `Architect or TechLead bootstrap -> Python Dev`
- `Python Dev -> TechLead`
- `QA -> TechLead`
- `TechLead -> next spoke role`

Long-term:
- `TechLead -> Delivery Architect`
- `TechLead -> worker role`
- `TechLead -> QA`
- each spoke role -> `TechLead`

## Required code deltas

### `paa_core.handoff_runtime`

File:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/handoff_runtime.py`

Changes:
- extend supported schema route validation to include new TechLead packet families
- add explicit route-policy validation:
  - disallow `Python Dev -> QA`
  - disallow `QA -> Architect`
  - disallow spoke-to-spoke routing
- update persistence comments/metadata to record route family and decision context

### `paa_consumer.delivery_runtime`

File:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-consumer/src/paa_consumer/delivery_runtime.py`

Changes:
- add helpers for TechLead-issued sends rather than generic queue-only sends
- likely grow a route helper that derives destination queue from role and packet schema

### `paa_consumer.techlead`

File:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-consumer/src/paa_consumer/techlead.py`

Changes:
- stop treating TechLead as mostly observational
- add explicit next-assignment preparation logic
- add queue/route expectation checks for hub behavior
- distinguish:
  - bootstrap packets
  - worker result packets
  - QA result packets
  - TechLead decision records

## Required route-policy changes

### Phase 1 destination deltas
- `slice_result_packet.to_role` should become `techlead`
- `qa_verification_packet.to_role` should become `techlead`
- TechLead should become the only legal issuer of the next consumer-side assignment packet

### Queue expectations

We should keep queue names stable initially if possible.
That means:
- worker result packets can still physically land on a queue TechLead watches
- QA packets can still physically land on a queue TechLead watches

Do not rename queues first.
Change routing authority first.

## Acceptance criteria
- Dev packets no longer route directly to QA
- QA packets no longer route directly to Architect
- TechLead can see every non-terminal result packet before the next assignment is made

## 2. Packet compiler changes

## Goal

Make compiled packet payloads reflect the hub model.

## Current compiler problem

Current compiler payloads bake the mesh into the envelope:
- `architect_cycle_packet` hardcodes `to_role = python-team`
- `slice_result_packet` defaults to Dev-result semantics
- `qa_verification_packet` assumes old QA return routes

## Required code deltas

### `materialize-architect-packet`

File:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-producer/src/paa_producer/authority_runtime.py`

Changes:
- treat as temporary bridge only
- support emitting to `techlead` or mark it as a bootstrap packet for TechLead-issued follow-up
- include explicit branch lineage fields in payload metadata
- add explicit note in compiler output that this schema is transitional

### `materialize-slice-result-packet`

File:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-producer/src/paa_producer/authority_runtime.py`

Changes:
- default `to_role` should become `techlead`
- add branch-lineage payload fields:
  - `canonical_branch`
  - `role_branch`
  - `branch_owner_role`
- add explicit `result_type`
- add optional `worker_role` field even before full `worker_result_packet` exists
- keep current validation/evidence shape during transition

### `materialize-qa-verification-packet`

File:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-producer/src/paa_producer/authority_runtime.py`

Changes:
- default `to_role` should become `techlead`
- add branch-lineage payload fields
- add explicit `result_type`
- preserve current QA proof/evidence semantics

### New packet compilers to add

Files to add later:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-consumer/src/paa_consumer/techlead_packets.py`
- or similar producer/consumer split once the final ownership is decided

Needed compiler commands:
- `materialize-techlead-assignment-packet`
- `materialize-techlead-decision-packet`
- later `materialize-worker-result-packet`
- later `materialize-delivery-review-packet`

## Acceptance criteria
- compiled envelopes no longer force the old mesh route
- branch lineage is present in compiled result packets
- TechLead assignment/decision packets become first-class compiled artifacts

## 3. New schema additions

## Goal

Introduce only the schema additions needed to support the hub model cleanly.

## Current schemas we can keep
- `architect_cycle_packet` temporarily
- `slice_result_packet` temporarily
- `qa_verification_packet` long-term

## New schema additions required

### `techlead_assignment_packet`

Purpose:
- one generic assignment envelope for Delivery Architect, worker roles, and QA

Where to add:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/schemas/handoff-packets/techlead_assignment_packet.schema.json`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/templates/packet-examples/techlead_assignment_packet.example.json`

Key fields:
- `assignment_type`
- `target_role`
- `canonical_branch`
- `role_branch`
- `allowed_result_types`
- `assignment_scope`
- `source_context`
- `decision_context`

### `techlead_decision_packet`

Where to add:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/schemas/handoff-packets/techlead_decision_packet.schema.json`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/templates/packet-examples/techlead_decision_packet.example.json`

Key fields:
- `decision_type`
- `decision_reason`
- `source_packet_ref`
- `next_target_role`
- `next_assignment_type`
- `branch_action`
- `canonical_branch`
- `role_branch`
- `work_item_status_update`

### `worker_result_packet` later

Where to add later:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/schemas/handoff-packets/worker_result_packet.schema.json`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/templates/packet-examples/worker_result_packet.example.json`

### `delivery_review_packet` later

Where to add later:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/schemas/handoff-packets/delivery_review_packet.schema.json`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/templates/packet-examples/delivery_review_packet.example.json`

## Runtime validator delta

File:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/handoff_runtime.py`

Changes:
- extend `SUPPORTED_SCHEMA_TYPES`
- add required-payload definitions for new schema types
- add route-family validation by schema type

## Acceptance criteria
- new TechLead packet families validate through the same runtime validator path
- current packets remain valid during transition
- new schemas are accompanied by example payloads

## 4. DB metadata additions for branch lineage

## Goal

Track canonical branch lineage and role worktree lineage without forcing an immediate new table.

## Recommended short-term storage

Use existing JSON metadata surfaces first:
- `paa.handoffs.notes` only for human summaries
- `paa.queue_messages.metadata_json`
- `paa.automation_runs.artifacts_json`
- optionally packet payload JSON itself for source-of-truth branch lineage

## Branch metadata fields to add now

Add to packet payload or metadata:
- `canonical_branch`
- `role_branch`
- `branch_owner_role`
- `branch_lineage_state`
- `superseded_branch`
- `reset_reason`
- `worktree_required`
- `worktree_id` if available

## Current code touchpoints

### Packet compiler payloads
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-producer/src/paa_producer/authority_runtime.py`

### Queue persistence metadata
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/handoff_runtime.py`

### TechLead reporting
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-consumer/src/paa_consumer/techlead.py`

## Short-term implementation approach

1. add branch lineage into packet payloads first
2. mirror selected lineage fields into `queue_messages.metadata_json`
3. update TechLead reporting to surface lineage problems
4. defer a dedicated branch-lineage table until the workflow is proven

## Future DB table candidate

Later, if needed:
- `paa.branch_lineages`

Possible columns:
- `branch_lineage_id`
- `project_id`
- `work_item_id`
- `canonical_branch`
- `role_branch`
- `owner_role_id`
- `status`
- `superseded_by_branch_lineage_id`
- `created_at`
- `updated_at`
- `metadata_json`

Do not start there.
Use metadata first.

## Acceptance criteria
- every active hub packet can tell us which canonical branch it belongs to
- role worktree branches are visible in persisted packet/report metadata
- TechLead can detect stale or unauthorized branch lineage

## 5. Automation prompt changes per role

## Goal

Bring the automation layer into alignment with the hub model and worktree strategy.

## Current prompt problems

Current prompts still teach:
- one shared branch per issue for everyone
- role-specific packets that imply the old mesh
- consumer roles operating without explicit TechLead hub ownership

Files needing prompt updates:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/project-packs/fractal-core/automations/fractal-core-authority-architect-automation/automation.toml`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/project-packs/fractal-core/automations/fractal-core-delivery-architect-automation/automation.toml`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/project-packs/fractal-core/automations/fractal-core-qa-automation/automation.toml`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/project-packs/fractal-core/automations/fractal-core-techlead-automation/automation.toml`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/project-packs/fractal-core/automations/python-team-automation/automation.toml`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/project-packs/fractal-core/skills/fractal-core-authority/SKILL.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/project-packs/fractal-core/skills/fractal-core-dev-result/SKILL.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/project-packs/fractal-core/skills/fractal-core-qa-review/SKILL.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/project-packs/fractal-core/skills/fractal-core-inbox/SKILL.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/project-packs/fractal-core/skills/fractal-core-techlead/SKILL.md`

## Role-specific prompt deltas

### Authority Architect

Keep responsible for:
- producer-side authority updates
- next authorized slice source preparation
- bootstrap packet preparation when needed

Prompt changes:
- make clear Authority Architect is not the consumer-side routing hub
- describe `architect_cycle_packet` as bootstrap or transitional where applicable
- stop implying Architect receives QA directly in the steady state

### TechLead

Prompt changes:
- explicitly state TechLead owns:
  - canonical branch creation
  - optional role branch authorization
  - next assignment issuance
  - branch reset/supersede decisions
  - merge-readiness preparation
- add route-decision vocabulary into the prompt
- add checks for branch lineage violations

### Delivery Architect

Prompt changes:
- explicitly state Delivery Architect never routes to Dev or QA directly
- returns review result only to TechLead
- branch behavior should be:
  - use canonical branch by default
  - use `issue-<n>-delivery` only when TechLead authorizes isolated worktree execution

### Worker role / Python Team

Prompt changes:
- explicitly state Dev returns result to TechLead, not QA
- branch behavior should be:
  - canonical branch if no isolated worktree is needed
  - `issue-<n>-dev` or future role-specific branch only if TechLead authorizes it
- forbid inventing branch names or new lineage

### QA

Prompt changes:
- explicitly state QA returns result to TechLead, not Architect
- branch behavior should be:
  - canonical branch if no isolated worktree is needed
  - `issue-<n>-qa` only when isolated worktree is explicitly authorized

## UI/global automation registration implication

Because the UI currently discovers global registrations, prompt deployment needs to stay consistent between:
- template/example content in `paa-platform`
- rendered deployed copies in project repos
- global UI registration entries under `/Users/billyweisberg/.codex/automations/`

The prompt changes above must therefore be reflected in:
- template source
- rendered project-local copies
- any active global UI registration copies

## Acceptance criteria
- prompts no longer teach the old mesh
- prompts no longer teach the obsolete “single shared branch for everyone” rule as the only valid model
- prompts teach TechLead-owned canonical branch plus optional role branches under authorization
- prompts teach spoke roles to return results only to TechLead

## Recommended rollout order

### Phase A: minimal hub transition
1. change Dev result destination to `TechLead`
2. change QA result destination to `TechLead`
3. update TechLead report/runtime to expect and manage that topology
4. update prompts to match

### Phase B: add first-class TechLead packet families
1. add `techlead_assignment_packet` schema and example
2. add `techlead_decision_packet` schema and example
3. extend runtime validator
4. add compiler commands for both

### Phase C: add branch lineage metadata
1. add canonical/role branch fields to result packets
2. mirror key lineage fields into queue metadata
3. make TechLead surface lineage violations

### Phase D: generalize worker roles
1. add `worker_result_packet`
2. add `delivery_review_packet`
3. migrate Python Dev from `slice_result_packet` to `worker_result_packet`
4. make future worker roles follow the same pattern

## Bottom line

The delta plan is intentionally pragmatic:

- redirect routing first
- introduce TechLead packet families second
- add branch lineage metadata alongside that work
- fix prompt and automation guidance at the same time
- generalize beyond Python-specific worker semantics only after the hub model is stable

That gives us a controlled path from the current mesh to the TechLead hub without another round of hidden workflow chaos.
