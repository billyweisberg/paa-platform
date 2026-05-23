Title: TechLead Acceptance Decision Service Component Spec
Doc-ID: paa-techlead-acceptance-decision-service-component-spec
Doc-Type: component-spec
Status: active
Lifecycle-Stage: design
Created: 2026-05-22
Last-Edited: 2026-05-22
Author: Billy Weisberg
Repo: paa-platform
Component: TechLeadAcceptanceDecisionService
Domain: techlead-runtime
Keywords: techlead, acceptance, closeout, decision, runtime, component
Depends-On: 2026-05-18-p0-techlead-runtime-extraction-plan.md, 2026-05-04-techlead-hub-state-and-routing-contract.md, 2026-05-05-phase-g-worker-result-and-delivery-review-contracts.md, 2026-05-17-workflow-lifecycle-service-component-spec.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-06-22
Summary: Defines the acceptance, reroute, and closeout decision application service extracted from the legacy TechLead runtime hub.

# TechLead Acceptance Decision Service Component Spec

## Purpose

Define the extracted application service that turns QA verification context into acceptance, reroute, pause, or closeout decisions.

This service exists to remove terminal decision logic from:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-consumer/src/paa_consumer/techlead.py`

## Architecture Placement

Layer:
- `Application Services`

Dependency stratum:
- `Stratum 3`

Primary upstream dependencies:
- `WorkflowLifecycleService`
- QA verification packet context
- acceptance event and merge-state context resolved by the consumer runtime shell

Primary downstream consumers:
- `TechLead Runtime Shell`
- closeout and acceptance flows
- merge-preparation and proof-only closeout paths

## 1. Role

`TechLeadAcceptanceDecisionService` derives the next terminal or near-terminal decision for one active slice after QA verification.

Authority boundary:
- owns acceptance decision derivation from QA context
- owns reroute / pause / reject recommendation derivation from QA non-pass context
- owns structured terminal-decision outputs
- does not own queue dispatch
- does not own packet transport
- does not own GitHub mutation
- does not own merge execution
- does not own direct workflow-state persistence

## 2. Component State Model

The service is stateless between calls.

It consumes authoritative acceptance and workflow context and returns stable acceptance-decision DTOs.

## 3. Service Contract

### Inputs
- QA verification packet summary
- current workflow stage
- current issue / PR identity
- optional workflow-lifecycle evaluation result
- optional merge state summary
- optional acceptance event summary
- optional metadata

### Outputs
- structured acceptance decision DTOs
- explicit next-step recommendation
- blocked or unsupported reason codes when the decision cannot be made safely

### Guarantees
- acceptance decision logic is centralized outside `techlead.py`
- outputs are structured and stable
- unsupported or unsafe terminal cases fail closed

## 4. Data Contract

### `TechLeadAcceptanceDecisionRequest`
Carries:
- `project_slug`
- `issue_number`
- optional `pr_number`
- `workflow_stage`
- `qa_result_type`
- optional `source_packet_schema_type`
- optional `source_packet_message_id`
- optional `workflow_lifecycle_result`
- optional `merge_state`
- optional `acceptance_event_state`
- optional `metadata`

### `TechLeadAcceptanceDecisionSummary`
Carries:
- `decision_supported`
- `recommended_next_decision`
- `acceptance_allowed`
- `closeout_allowed`
- `decision_summary`
- `blocking_reasons`
- `notes`

### `TechLeadAcceptanceDecisionResult`
Carries:
- request echo identifiers
- workflow stage
- source packet references
- acceptance-decision summary
- `ok`
- optional `reason`
- optional `details`
- optional `recommended_actions`
- optional `unattended_safe`

## 5. Interfaces

### Provided interface
- `TechLeadAcceptanceDecisionService`

## 6. Primary Supported Outcomes

- `pass` -> recommend `prepare_merge` or `close_slice`
- `fail_fixable` -> recommend `return_to_worker`
- `fail_scope` -> recommend `return_to_delivery_architect` or `escalate_to_authority_architect`
- `needs_human_review` -> recommend `return_to_delivery_architect`, `escalate_to_authority_architect`, or `pause_slice`
- `blocked` -> recommend `return_to_worker`, `assign_qa`, or `pause_slice`

## 7. Non-Goals

This service must not become a second TechLead hub.
It must not send packets, mutate queue state, or directly merge PRs.
