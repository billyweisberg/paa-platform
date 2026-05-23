Title: TechLead Worker Review Routing Service Component Spec
Doc-ID: paa-techlead-worker-review-routing-service-component-spec
Doc-Type: component-spec
Status: active
Lifecycle-Stage: design
Created: 2026-05-22
Last-Edited: 2026-05-22
Author: Billy Weisberg
Repo: paa-platform
Component: TechLeadWorkerReviewRoutingService
Domain: techlead-runtime
Keywords: techlead, worker-review, qa-routing, runtime, component
Depends-On: 2026-05-18-p0-techlead-runtime-extraction-plan.md, 2026-05-04-techlead-hub-state-and-routing-contract.md, 2026-05-05-phase-g-worker-result-and-delivery-review-contracts.md, 2026-05-17-workflow-lifecycle-service-component-spec.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-06-22
Summary: Defines the worker-result review and QA-routing application service extracted from the legacy TechLead runtime hub.

# TechLead Worker Review Routing Service Component Spec

## Purpose

Define the extracted application service that reviews worker-result context and derives the next routing recommendation for:
- QA assignment
- return to worker
- return to Delivery Architect
- escalation or pause

This service exists to remove worker-review and QA-routing logic from:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-consumer/src/paa_consumer/techlead.py`

## Architecture Placement

Layer:
- `Application Services`

Dependency stratum:
- `Stratum 3`

Primary upstream dependencies:
- `WorkflowLifecycleService`
- worker-result packet context
- issue / PR context resolved by the consumer runtime shell

Primary downstream consumers:
- `TechLead Runtime Shell`
- `QA assignment emission path`
- later `TechLeadAcceptanceDecisionService`

## 1. Role

`TechLeadWorkerReviewRoutingService` derives the next review-routing decision for one active slice after a worker result is returned.

Authority boundary:
- owns worker-result review outcome classification
- owns QA-routing recommendation derivation
- owns return-to-worker and return-to-delivery recommendation derivation
- owns allowed next-decision outputs for supported worker result types
- does not own packet transport
- does not own queue dispatch
- does not own workflow-state mutation
- does not own merge or closeout

## 2. Component State Model

The service is stateless between calls.

It consumes already-resolved runtime context and returns stable review-routing DTOs.

## 3. Service Contract

### Inputs
- worker result packet summary
- current workflow stage
- current issue identity
- current PR identity when present
- optional workflow-lifecycle evaluation result
- optional metadata

### Outputs
- structured review-routing decision DTOs
- supported next-action recommendation
- explicit blocked or unsupported reason codes when the review cannot proceed safely

### Guarantees
- worker-review routing logic is centralized outside `techlead.py`
- outputs are stable and structured
- unsupported or unsafe cases fail closed

## 4. Data Contract

### `TechLeadWorkerReviewRoutingRequest`
Carries:
- `project_slug`
- `issue_number`
- optional `pr_number`
- `workflow_stage`
- `worker_role`
- `worker_result_type`
- optional `source_packet_schema_type`
- optional `source_packet_message_id`
- optional `workflow_lifecycle_result`
- optional `metadata`

### `TechLeadWorkerReviewRoutingSummary`
Carries:
- `decision_supported`
- `recommended_next_decision`
- `recommended_target_role`
- `qa_assignment_allowed`
- `review_summary`
- `blocking_reasons`
- `notes`

### `TechLeadWorkerReviewRoutingResult`
Carries:
- request echo identifiers
- workflow stage
- source packet references
- review-routing summary
- `ok`
- optional `reason`
- optional `details`
- optional `recommended_actions`
- optional `unattended_safe`

## 5. Interfaces

### Provided interface
- `TechLeadWorkerReviewRoutingService`

## 6. Primary Supported Outcomes

- `implemented_ready_for_qa` -> recommend `assign_qa`
- `blocked` -> recommend `return_to_delivery_architect`, `assign_worker`, or `pause_slice`
- `needs_clarification` -> recommend `return_to_delivery_architect` or `assign_worker`
- `cannot_complete_without_scope_change` -> recommend `return_to_delivery_architect` or `escalate_to_authority_architect`
- `superseded_by_branch_reset` -> recommend `reset_branch` or `assign_worker`

## 7. Non-Goals

This service must not become a second runtime hub.
It must not compile packets, mutate DB workflow truth, or perform queue sends.
