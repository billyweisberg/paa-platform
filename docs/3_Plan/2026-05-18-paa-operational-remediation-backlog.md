Title: PAA Operational Remediation Backlog
Doc-ID: paa-operational-remediation-backlog
Doc-Type: plan
Status: active
Lifecycle-Stage: plan
Created: 2026-05-18
Last-Edited: 2026-05-18
Author: Billy Weisberg
Repo: paa-platform
Component: PaaOperationalRemediation
Domain: methodology
Keywords: remediation, backlog, operations, runtime, extraction
Depends-On: 2026-05-18-paa-operational-process-remediation-table.md
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
Summary: Prioritizes the operational remediation work needed to reduce the remaining hybrid zones in PAA.

# PAA Operational Remediation Backlog

## Status
Draft.

## Purpose
This backlog turns the operational process-remediation table into an ordered execution backlog.

The goal is to answer:
- what should be remediated first
- why that item is worth doing now
- what architectural payoff it creates
- what extraction order is most sensible

This backlog assumes the current state is:
- producer-side derivation is materially real
- workflow and execution-context services are materially real
- the largest remaining hybrid zone is the TechLead/runtime orchestration layer

## Prioritized Remediation Backlog

| Priority | Area | Why now | Expected architectural payoff | Suggested extraction order |
|---|---|---|---|---|
| P0 | Assignment decision | This is the first major runtime decision point after packet-ready authority, and it still depends heavily on legacy `techlead.py` heuristics. | Makes the system route work from authoritative workflow and assignment logic instead of a large runtime hub. | 1. Extract TechLead assignment-decision service. 2. Move decision derivation out of `techlead.py`. 3. Leave CLI as composition only. |
| P0 | Worker review and QA routing | This is where worker-result evaluation becomes next-step routing, and it still mixes packet inspection, workflow interpretation, and runtime policy in one hub. | Creates a clean post-worker-review boundary and reduces the most immediate orchestration ambiguity. | 1. Extract worker-review service. 2. Move QA-routing decision logic into it. 3. Keep `WorkflowLifecycleService` as state truth, not routing owner. |
| P0 | Acceptance / reroute / closeout decision | This is the terminal decision layer and still mixes workflow, QA result interpretation, GitHub state, and closeout orchestration. | Gives PAA a clean acceptance boundary and prevents terminal decisions from staying trapped in legacy script logic. | 1. Extract acceptance-decision service. 2. Separate decision from closeout side effects. 3. Let closeout runtime consume the decision instead of creating it. |
| P1 | QA assignment dispatch | Dispatch exists, but the decision-to-dispatch bridge is still too coupled to the TechLead runtime hub. | Produces a cleaner application-service boundary between routing decisions and queue emission. | 1. Extract QA-assignment emitter. 2. Reuse handoff/queue runtime under a smaller application service. 3. Remove dispatch-specific branching from `techlead.py`. |
| P1 | QA result return transition runtime application | `qa_result_returned` exists in `WorkflowLifecycleService`, but runtime application is not yet symmetric with the worker-result path. | Completes the runtime use of authoritative workflow truth for both result-return families. | 1. Connect `apply_workflow_transition(...)` for QA-return runtime path. 2. Validate the path end to end. 3. Remove equivalent inline state heuristics. |
| P1 | Assignment dispatch generalization | Both worker and QA dispatch still pass through a large consumer runtime entrypoint. | Gives a reusable dispatch application surface and reduces role-specific branching. | 1. Extract common assignment dispatch service. 2. Keep role-specific packet compilation separate. 3. Reduce duplicated dispatch/error/ack patterns. |
| P2 | Activity-to-target mapping authoring | The underlying model exists, but authoring/inspection is still weaker than the rest of the derivation pipeline. | Makes implementation planning and coder-brief derivation more inspectable and less architect-memory-dependent. | 1. Add mapping visualizer/report. 2. Add authoring/edit support. 3. Tighten validation over missing mappings. |
| P2 | Implementation-plan review and editing UX | Plans are materialized, but operator-facing review/edit loops are still immature. | Improves project-design usability and makes `ImplementationPlan` more viable as the project truth backbone. | 1. Add plan inspection report. 2. Add review-oriented editing path. 3. Add change-history/audit support if needed. |
| P2 | Packet-ready execution authority inspection | Packetization exists, but visibility into what is packet-ready is still weaker than it should be. | Makes execution authority easier to trust and easier to diagnose. | 1. Add packet inspection report. 2. Add packet-ready validation summary. 3. Connect into operator workflows. |
| P2 | Brief approval UX and history inspection | Approval is real, but operator ergonomics and historical inspection are still limited. | Improves governance quality without changing core execution semantics. | 1. Add approval-history view. 2. Add clearer diff/review surfaces. 3. Connect to operator checkpoints. |
| P3 | Slice-selection record | Slice selection is still partly implicit/manual and not strongly represented as a first-class record. | Improves traceability from component graph to selected execution slice. | 1. Decide whether to model slice selection as DB-primary or explicit authority note. 2. Add decision record. 3. Connect to package materialization. |
| P3 | Component graph validation tooling | The component model exists, but graph validation/reporting is still lighter than it should be. | Improves structural confidence before slice derivation. | 1. Add dependency-graph validator. 2. Add reporting over unresolved graph gaps. 3. Use it upstream of slice selection. |
| P3 | Structured system-design persistence | System design still lives mostly in document authority, not strongly in structured records. | Could improve downstream automation, but only after runtime orchestration is less hybrid. | 1. Decide persistence scope. 2. Add only the minimum structured sections needed. 3. Avoid over-modeling narrative design prose. |
| P3 | Authority interpretation materialization | The interpretation layer from note to architecture is still mainly human/manual. | Potential long-term payoff, but it is upstream and less urgent than the runtime orchestration gaps. | 1. Decide if this should be a first-class artifact. 2. Keep it small if modeled. 3. Avoid creating a redundant ontology. |

## Priority Logic

### P0
Items that still make the live runtime path feel hybrid even though the underlying services and workflow truth now exist.

### P1
Items that complete symmetry and remove dispatch/orchestration coupling after the most critical decision layers are extracted.

### P2
Items that improve operator usability, inspection, and governance once the runtime architecture is less hybrid.

### P3
Items that improve upstream modeling and traceability, but are not the current bottleneck to trustworthy execution.

## Recommended Extraction Order

1. Assignment decision service
2. Worker review and QA routing service
3. Acceptance / reroute / closeout decision service
4. QA assignment dispatch service
5. Runtime application of `qa_result_returned`
6. Shared assignment dispatch service
7. Activity-to-target mapping tooling
8. Implementation-plan review/edit tooling
9. Packet-ready inspection tooling
10. Brief approval/history tooling
11. Slice-selection record
12. Component-graph validation tooling
13. Structured system-design persistence
14. Authority-interpretation materialization

## Most Important Near-Term Architectural Claim
The biggest remaining hybrid problem is not:
- design packages
- implementation plans
- coder briefs
- workflow truth

It is:
- the TechLead/runtime orchestration and decision layer

That is where the next meaningful architectural payoff sits.