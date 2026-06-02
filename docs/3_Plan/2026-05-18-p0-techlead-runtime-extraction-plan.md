Title: P0 TechLead Runtime Extraction Plan
Doc-ID: paa-p0-techlead-runtime-extraction-plan
Doc-Type: plan
Status: active
Lifecycle-Stage: plan
Created: 2026-05-18
Last-Edited: 2026-05-18
Author: Billy Weisberg
Repo: paa-platform
Component: TechLeadRuntimeExtraction
Domain: techlead-runtime
Keywords: techlead, runtime, extraction, plan, remediation
Depends-On: 2026-05-18-paa-operational-remediation-backlog.md, 2026-05-18-techlead-assignment-decision-service-component-spec.md
Supersedes: 
Superseded-By: 
Canonical: true
Review-After: 2026-06-15
Owners: 
Expires: 
Issue: 
PR: 
Authority-Source: 
Implementation-Status: 
Summary: Defines the concrete P0 extraction sequence for shrinking the legacy TechLead runtime hub.

# P0 TechLead Runtime Extraction Plan

## Status
Draft.

## Purpose
This plan turns the `P0` operational-remediation cluster into a concrete extraction sequence.

The goal is to reduce the largest remaining hybrid zone in PAA:
- TechLead/runtime orchestration concentrated in `techlead.py`

This plan focuses only on the `P0` cluster:
1. assignment decision
2. worker review and QA routing
3. acceptance / reroute / closeout decision

## Current Hub

Current legacy runtime hub:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services`

This file currently mixes:
- CLI entrypoints
- queue inspection
- GitHub inspection
- workflow interpretation
- assignment derivation
- packet emission orchestration
- closeout decision logic
- closeout side effects

## Extraction Goal

Reduce `techlead.py` to:
- CLI parsing
- argument normalization
- composition of real services
- formatting and output

Move domain/application decision logic into smaller services.

## Target Components

### 1. `TechLeadAssignmentDecisionService`

#### Purpose
Own the decision of what next assignment should be emitted from the current workflow and packet context.

#### Responsibilities
- inspect current slice context
- interpret worker-result and QA-ready routing conditions
- derive assignment target role
- derive assignment type
- derive allowed result types
- derive source-packet references needed for downstream dispatch

#### Non-ownership
- does not dispatch packets
- does not mutate workflow truth
- does not inspect or mutate Git worktrees
- does not perform GitHub merge/closeout

#### Likely target package
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/techlead_assignment_decision/`

#### Current source ownership in hub
Primary extraction sources:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services:2521`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services:2795`
- supporting workflow helpers around:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services:1508`

### 2. `TechLeadWorkerReviewRoutingService`

#### Purpose
Own post-worker-result review interpretation and QA-routing decision logic.

#### Responsibilities
- consume worker-result packet context
- consume workflow lifecycle result context
- determine whether the slice is ready for QA routing
- derive review outcome and routing rationale
- provide worker-review decision outputs to assignment-emission layer

#### Non-ownership
- does not emit QA packets directly
- does not mutate workflow truth except through existing workflow services used by callers
- does not own acceptance or closeout

#### Likely target package
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/techlead_worker_review_routing/`

#### Current source ownership in hub
Primary extraction sources:
- worker-result branch in:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services:1661`
- assignment derivation path using worker review outcome in:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services:2521`
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services:2795`

### 3. `TechLeadAcceptanceDecisionService`

#### Purpose
Own terminal or near-terminal decision logic after QA return.

#### Responsibilities
- interpret QA result packet context
- interpret workflow state and acceptance constraints
- decide accept / reject / reroute / proof-close / closeout intent
- separate pure decision from side-effect execution

#### Non-ownership
- does not perform merge itself
- does not emit closeout side effects itself
- does not persist acceptance events directly except through a caller-owned repository/runtime path

#### Likely target package
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/techlead_acceptance_decision/`

#### Current source ownership in hub
Primary extraction sources:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services:2976`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services:3192`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services:3303`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services:3494`

## Exact File Ownership Plan

| Target component | New owning files | Existing file(s) to shrink |
|---|---|---|
| `TechLeadAssignmentDecisionService` | `packages/paa-core/src/paa_core/services/techlead_assignment_decision/__init__.py`, `contracts.py`, `models.py`, `default.py` | `packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services` |
| `TechLeadWorkerReviewRoutingService` | `packages/paa-core/src/paa_core/services/techlead_worker_review_routing/__init__.py`, `contracts.py`, `models.py`, `default.py` | `packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services` |
| `TechLeadAcceptanceDecisionService` | `packages/paa-core/src/paa_core/services/techlead_acceptance_decision/__init__.py`, `contracts.py`, `models.py`, `default.py` | `packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services` |
| focused tests | `tests/unit/test_techlead_assignment_decision_service.py`, `tests/unit/test_techlead_worker_review_routing_service.py`, `tests/unit/test_techlead_acceptance_decision_service.py` | `tests/unit/test_techlead_self_hosted.py` remains integration coverage |

## Extraction Sequence

### Phase 1. Extract `TechLeadAssignmentDecisionService`

#### Why first
This is the highest-leverage reduction of `techlead.py` complexity because it centralizes next-assignment derivation.

#### First thin slice
- input:
  - current task summary
  - workflow stage
  - current packet preview refs
  - PR/issue identity
- support only:
  - worker-result-review-ready -> QA assignment decision
  - explicit team-worker emission path
- output:
  - structured assignment decision DTO

#### Minimal hub replacement
- `derive_next_assignment_context(...)` becomes a thin adapter around the service

### Phase 2. Extract `TechLeadWorkerReviewRoutingService`

#### Why second
Once assignment decision is a real service, worker review should stop being embedded as packet heuristics inside the hub.

#### First thin slice
- input:
  - worker-result packet preview
  - workflow lifecycle evaluation result
  - current issue/PR context
- support only:
  - `worker_result_packet`
  - route-to-QA-ready decision
- output:
  - review-routing DTO used by assignment-decision service

#### Minimal hub replacement
- worker-result branch inside `derive_workflow(...)` becomes a thin call to the service

### Phase 3. Extract `TechLeadAcceptanceDecisionService`

#### Why third
Terminal decision logic should only be extracted after the earlier routing logic is cleaner, otherwise the decision boundary is still muddied by upstream hybrid behavior.

#### First thin slice
- input:
  - QA packet summary
  - workflow stage
  - issue/PR merge state
  - proof/live execution mode
- support only:
  - QA pass -> accept / proof-only-close decision derivation
- output:
  - acceptance decision DTO

#### Minimal hub replacement
- `derive_decision_context(...)` becomes a thin adapter around the service for the supported QA-pass path

## First Thin Slice Summary

| Service | First supported slice |
|---|---|
| `TechLeadAssignmentDecisionService` | worker-review-ready or explicit worker-target assignment decision |
| `TechLeadWorkerReviewRoutingService` | `worker_result_packet` -> review outcome -> QA-routing recommendation |
| `TechLeadAcceptanceDecisionService` | QA-pass -> accept / proof-only-close decision derivation |

## Dependencies To Reuse, Not Recreate

These extractions should reuse existing components rather than invent new ones:
- `WorkflowLifecycleService`
- `ExecutionPackageResolutionService`
- existing queue/handoff runtime helpers
- existing GitHub-state helpers where still necessary during transition

## Important Constraint

These services should be decision/application services.

They should not absorb:
- direct DB SQL
- packet transport internals
- worktree mutation logic
- GitHub side-effect execution

Those concerns should remain in:
- repositories
- runtime adapters
- thin consumer orchestration shells

## Success Condition

This `P0` cluster is successful when:
1. `techlead.py` no longer owns the primary decision logic for assignment, worker review routing, and acceptance decision
2. those decisions are expressed as smaller service boundaries in `paa_core`
3. `techlead.py` becomes a thin composition and runtime adapter layer rather than a logic hub