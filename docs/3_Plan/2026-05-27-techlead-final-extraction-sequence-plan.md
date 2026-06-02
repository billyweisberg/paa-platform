Title: TechLead Final Extraction Sequence Plan
Doc-ID: paa-techlead-final-extraction-sequence-plan
Doc-Type: plan
Status: active
Lifecycle-Stage: plan
Created: 2026-05-27
Last-Edited: 2026-05-27
Author: Billy Weisberg
Repo: paa-platform
Component: TechLeadFinalExtractionSequence
Domain: techlead-runtime
Keywords: techlead, extraction, plan, delivery-review, reset, lineage, closeout
Depends-On: 2026-05-18-p0-techlead-runtime-extraction-plan.md, 2026-05-18-techlead-assignment-decision-service-component-spec.md, 2026-05-22-techlead-worker-review-routing-service-component-spec.md, 2026-05-22-techlead-acceptance-decision-service-component-spec.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-06-27
Summary: Defines the remaining four extraction services required to reduce techlead.py to a thin orchestration shell before CLI-system automation hardening.

# TechLead Final Extraction Sequence Plan

## Purpose

Define the exact remaining extraction order after the successful delivery of:
- `TechLeadAssignmentDecisionService`
- `TechLeadWorkerReviewRoutingService`
- `TechLeadAcceptanceDecisionService`

The goal is to finish draining remaining decision ownership out of:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services`

After these four extractions, `techlead.py` should mainly own:
- queue operations
- GitHub operations
- packet emission, validation, and ack
- runtime composition
- helper and request-building glue

## Why This Sequence Exists

The order is deliberate:
1. start with the least coupled decision pocket
2. leave the most side-effect-adjacent closeout logic for last

This keeps the runtime shell stable while the remaining business-logic pockets are extracted into governed services.

## Extraction 1. Delivery Review Decision

### Component
- `TechLeadDeliveryReviewDecisionService`

### Purpose
Interpret `delivery_review_packet` context and derive the next TechLead routing decision.

### First thin slice
Support only:
- `workflow_stage = techlead_delivery_review_pending`
- `source_packet_schema_type = delivery_review_packet`
- `payload.result_type = ready_for_dev`
- `techlead_action_recommended.action = assign_worker`
- supported Team Worker Role target resolution

Output only a structured review decision DTO.

Do not own:
- packet emission
- workflow mutation
- queue side effects
- GitHub mutation

### Current source ownership
Primary extraction sources:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services:1743`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services:2917`

### Expected files
- `packages/paa-core/src/paa_core/services/techlead_delivery_review_decision/__init__.py`
- `packages/paa-core/src/paa_core/services/techlead_delivery_review_decision/contracts.py`
- `packages/paa-core/src/paa_core/services/techlead_delivery_review_decision/models.py`
- `packages/paa-core/src/paa_core/services/techlead_delivery_review_decision/default.py`
- `tests/unit/test_techlead_delivery_review_decision_contract.py`
- `tests/unit/test_techlead_delivery_review_decision_models.py`
- `tests/unit/test_techlead_delivery_review_decision_service.py`

## Extraction 2. Reset Recovery Decision

### Component
- `TechLeadResetRecoveryDecisionService`

### Purpose
Own reset-required decision derivation when repeated QA or Architect history indicates contaminated branch recovery is needed.

### First thin slice
Support only:
- lineage or escalation context that indicates `reset_required`
- derive:
  - `reset_branch`
  - target role `Python Dev`
  - rationale
  - branch-reset metadata

### Current source ownership
Primary extraction sources:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services:1935`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services:1992`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services:3254`

## Extraction 3. Supersede Lineage Decision

### Component
- `TechLeadLineageDecisionService`

### Purpose
Own superseded-lineage decisions that are neither assignment, worker review, nor acceptance.

### First thin slice
Support only:
- superseded QA escalation case
- derive:
  - `supersede_branch_lineage`
  - lineage action `superseded`
  - rationale
  - superseded branch context

### Current source ownership
Primary extraction sources:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services:1965`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services:3315`

## Extraction 4. Closeout Decision Context

### Component
- `TechLeadCloseoutDecisionService`

### Purpose
Own pure closeout decision and context derivation for:
- `closed`
- `proof_only_closed`

while leaving side effects in the shell.

### First thin slice
Support only:
- QA pass
- proof-only execution mode
- derive:
  - `proof_only_close_slice`
  - closeout intent
  - work-item status intent
  - lineage action
  - source packet requirements

Do not own:
- merge execution
- GitHub issue close
- queue ack
- packet emission

### Current source ownership
Primary extraction sources:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services:3376`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services:3543`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services:3734`

## Exact Order Of Implementation

1. `TechLeadDeliveryReviewDecisionService`
2. `TechLeadResetRecoveryDecisionService`
3. `TechLeadLineageDecisionService`
4. `TechLeadCloseoutDecisionService`

## Why This Order

1. delivery review is the simplest remaining decision pocket
2. reset recovery is more coupled, but still mostly pure decision logic
3. supersede lineage is adjacent to reset logic and benefits from the same mental model
4. closeout is the most side-effect-adjacent and should come last

## Execution Rule

Each extraction should use the same governed loop already proven for the first three TechLead services:
1. author component spec
2. materialize component spec
3. reconcile implementation-plan progress
4. derive next activity bundle
5. implement one thin slice
6. verify
7. mark activity complete
8. repeat until fully realized
9. wire the shell seam only after the supported slice is real and verified

## End State

After these four extractions, `techlead.py` should no longer be the primary owner of remaining TechLead decision logic.

That is the right point to start building clean CLI surfaces and stronger automation on top of the extracted system shape rather than around the legacy hub.
