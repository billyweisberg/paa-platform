Title: TechLead Runtime Design Tables Proof
Doc-ID: paa-techlead-runtime-design-tables-proof
Doc-Type: proof
Status: active
Lifecycle-Stage: design
Created: 2026-05-18
Last-Edited: 2026-05-18
Author: Billy Weisberg
Repo: paa-platform
Component: TechLeadRuntime
Domain: techlead-runtime
Keywords: techlead, runtime, tables, proof, extraction
Depends-On: 2026-05-18-paa-system-design-tables-method.md, 2026-05-18-p0-techlead-runtime-extraction-plan.md, 2026-05-18-techlead-assignment-decision-service-component-spec.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-06-15
Summary: Applies the system-design tables method to the TechLead runtime extraction area as a proof case.

# TechLead Runtime Design Tables Proof

## Status
Draft.

## Purpose

Apply the `PAA System Design Tables Method` to one active area immediately so the method becomes part of real system work rather than a postponed improvement.

Proof target:
- TechLead runtime extraction

Current hybrid hub:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-consumer/src/paa_consumer/techlead.py`

This area is the right proof target because it is:
- active now
- high leverage
- clearly hybrid
- already partially decomposed through workflow and execution services
- still missing clean decision-service extraction

## Why This Area Needs Tables

The TechLead runtime area currently mixes:
- assignment decision
- worker review and QA routing
- acceptance and closeout decision
- packet emission orchestration
- queue acknowledgement behavior
- GitHub and branch-context interpretation

A diagram can show that this area is complex.
A table can show exactly:
- which step is owned where
- what truth anchors it
- what remains hybrid
- what should be extracted first

## Table Set Used For This Proof

This proof uses four table types from the method.

1. strict process record table
2. operational remediation table
3. prioritized remediation backlog table
4. extraction plan table

## Proof 1: Strict Runtime Decision Slice Table

| Step | Role | Input Record | Transformation | Output Record | Current Implementation Status |
|---|---|---|---|---|---|
| 1 | TechLead runtime shell | packet-ready authority + workflow state + packet preview | inspect current active slice context | runtime decision context | Hybrid |
| 2 | TechLead runtime shell | runtime decision context + packet schema identity | derive next assignment candidate | assignment decision | Hybrid |
| 3 | PAA System | assignment decision | materialize assignment packet | `techlead_assignment_packet` | Implemented / hybrid |
| 4 | PAA System | assignment packet | dispatch queue message and handoff | queue message + handoff record | Implemented / hybrid |
| 5 | Worker or QA runtime | assignment packet | claim and execute | result packet | Implemented |

### What this reveals
The weak point is not packet materialization.
The weak point is Step 2, where assignment decision remains hybrid and trapped in the runtime hub.

## Proof 2: Operational Remediation Slice Table

| Step | Current Owning Code / Module | Primary DB Truth | Missing Automation | Next Remediation |
|---|---|---|---|---|
| Assignment decision | `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-consumer/src/paa_consumer/techlead.py` | workflow truth plus queue/handoff context | clean assignment-decision service boundary | extract `TechLeadAssignmentDecisionService` |
| Worker review and QA routing | `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-consumer/src/paa_consumer/techlead.py` | workflow truth plus packet evidence | clean review/routing service boundary | extract `TechLeadWorkerReviewRoutingService` |
| Acceptance / reroute / closeout decision | `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-consumer/src/paa_consumer/techlead.py` | acceptance events, workflow truth, package/runtime state | clean acceptance-decision boundary | extract `TechLeadAcceptanceDecisionService` |

### What this reveals
The same file owns too many decision layers.
The next work should not be broad refactoring.
It should be targeted service extraction.

## Proof 3: Prioritized Remediation Table

| Priority | Area | Why now | Expected architectural payoff | Suggested extraction order |
|---|---|---|---|---|
| P0 | Assignment decision | earliest live runtime decision after packet-ready authority | reduces the largest immediate hub responsibility | first |
| P0 | Worker review and QA routing | directly downstream from worker result handling | removes packet-heuristic routing from hub | second |
| P0 | Acceptance / reroute / closeout decision | terminal decision layer still trapped in hub | cleans up end-of-slice governance behavior | third |

### What this reveals
The tables do not just describe the problem.
They create a stable implementation order.

## Proof 4: Extraction Plan Table

| Target component | Current source ownership | New owning files | First thin slice |
|---|---|---|---|
| `TechLeadAssignmentDecisionService` | `techlead.py` assignment derivation path | `packages/paa-core/src/paa_core/services/techlead_assignment_decision/` | worker-review-ready to QA assignment and explicit worker-target emission |
| `TechLeadWorkerReviewRoutingService` | `techlead.py` worker-result review branch | `packages/paa-core/src/paa_core/services/techlead_worker_review_routing/` | `worker_result_packet` to QA-routing recommendation |
| `TechLeadAcceptanceDecisionService` | `techlead.py` terminal decision paths | `packages/paa-core/src/paa_core/services/techlead_acceptance_decision/` | QA-pass to accept / proof-only-close decision |

### What this reveals
The tables bridge directly from design diagnosis to implementation scope.
That is stronger than a diagram because it names:
- current owner
- future owner
- file target
- first slice

## Promotion Analysis For This Area

This proof area also shows why not every useful table should become DB-primary.

### Keep as document-first
- prioritized remediation table
- extraction plan table
- operational remediation table

Reason:
- they govern migration and decomposition
- they are valuable immediately
- runtime execution does not need to query them directly

### Candidate for future structured promotion
- assignment-decision support matrix
- transition-family support matrix

Reason:
- if TechLead runtime decomposition continues, some decision tables may become stable enough to drive validation or test generation

### Already DB-primary and should remain so
- workflow states
- workflow transitions
- queue and handoff records
- acceptance events

Reason:
- these are operational truth, not only decomposition guidance

## Main Findings

This proof demonstrates three things.

### 1. Tables improve decomposition quality
The TechLead runtime problem becomes much clearer when shown as:
- owned step
- current code owner
- DB truth anchor
- missing automation
- next remediation

### 2. Tables prevent premature DB expansion
The useful tables here are essential to design governance, but they do not all need DB schema.
That is a valuable discipline.

### 3. Tables create continuity across long-horizon work
This area has drifted repeatedly because the reasoning lived too much in conversation and not enough in stable structured artifacts.
The tables reduce that risk.

## Immediate Outcome

Using the method on this active area has already produced concrete work artifacts:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-18-p0-techlead-runtime-extraction-plan.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-18-techlead-assignment-decision-service-component-spec.md`

That is the proof that the method is not theoretical.
It is already changing implementation order and component design.

## Conclusion

The TechLead runtime area is a successful proof case for `System Design Tables`.

The tables:
- exposed the hybrid center of gravity
- sequenced remediation
- clarified file ownership
- supported a real component spec
- did so without forcing premature DB modeling

That is the pattern PAA should reuse in other active areas.
