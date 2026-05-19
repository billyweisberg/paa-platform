# PAA Strict Process Record Table

## Status
Draft.

## Purpose
This document restates the PAA process pipeline in stricter form.

Instead of only describing:
- role
- process
- system support

it forces each step to declare:
- the input record
- the transformation
- the output record
- the current implementation status

The goal is to reduce ambiguity and make process gaps easier to see.

## Strict Process Record Table

| Step | Role | Input Record | Transformation | Output Record | Current Implementation Status |
|---|---|---|---|---|---|
| 1 | Tom | Idea, note, requirement, review comment | Express intent in durable note form | Source note | Manual |
| 2 | Authority Architect | Source note | Interpret intent into engineering meaning | Authority interpretation note or working authority intent | Manual / hybrid |
| 3 | Authority Architect | Authority interpretation | Produce formal system design | System design | Implemented in docs, still author-driven |
| 4 | Authority Architect | System design | Derive component set, relationships, and dependency graph | Component model and dependency graph | Implemented in docs and model artifacts |
| 5 | Authority Architect | Component model and dependency graph | Choose one narrow execution slice | Slice selection decision | Manual / hybrid |
| 6 | Authority Architect | Selected slice + system authority | Materialize authoritative execution slice | Design package | Implemented |
| 7 | Delivery Architect | Design package | Derive consumer-specific project design | Implementation plan | Implemented |
| 8 | Delivery Architect | Implementation plan | Derive ordered execution activities | Implementation-plan activities and dependencies | Implemented |
| 9 | Delivery Architect | Activities | Map each activity to component, component element, and code artifact target | Structured coder inputs | Implemented |
| 10 | PAA System | Design package + implementation plan + activity mappings | Assemble draft execution briefing | Draft CoderBrief | Implemented |
| 11 | Architect or TechLead governance + PAA System | Draft CoderBrief | Review and approve execution authority | Approved CoderBrief | Implemented |
| 12 | PAA System | Approved CoderBrief | Produce transport-ready execution authority | Packet-ready execution packet | Implemented |
| 13 | TechLead | Packet-ready authority + current workflow state | Decide next assignment target | Assignment decision | Hybrid |
| 14 | PAA System | Assignment decision | Materialize and dispatch assignment packet | Queue assignment packet + handoff record + workflow state update | Implemented / hybrid |
| 15 | Worker Agent | Assignment packet + execution context | Claim work and prepare runnable environment | Active worker execution context | Implemented |
| 16 | Worker Agent | Active worker execution context + CoderBrief | Generate or edit code | Working code changes | Implemented |
| 17 | Worker Agent | Working code changes | Run tests and local validation | Validation evidence | Implemented |
| 18 | Worker Agent | Working code + validation evidence | Return execution result | Worker result packet | Implemented |
| 19 | PAA System | Worker result packet + workflow state | Apply worker-result lifecycle transition | Updated workflow state and transition record | Implemented |
| 20 | TechLead | Worker result packet + workflow state | Review worker result | Review decision or QA routing intent | Hybrid |
| 21 | TechLead | Review decision | Emit QA assignment | QA assignment decision | Hybrid |
| 22 | PAA System | QA assignment decision | Dispatch QA assignment and update workflow truth | QA assignment packet + handoff record + workflow state update | Implemented / hybrid |
| 23 | QA Agent | QA assignment packet + execution context | Verify slice | QA verification work and evidence | Implemented |
| 24 | QA Agent | QA verification work and evidence | Return QA result | `qa_verification_packet` | Implemented |
| 25 | PAA System | QA result packet + workflow state | Apply QA-result lifecycle transition | Updated workflow state and transition record | Implemented |
| 26 | TechLead | QA result packet + workflow state + merge state | Accept, reject, reroute, or close | Acceptance or routing decision | Hybrid |
| 27 | PAA System | Acceptance or routing decision | Record closeout, acceptance, and runtime/package update | Acceptance event, closeout state, updated runtime state | Implemented / hybrid |
| 28 | Runtime / Installed System | Updated package and runtime state | Resolve installed execution surfaces and run | Running code | Implemented |

## Status Meaning

| Label | Meaning |
|---|---|
| Manual | Human-performed and not yet system-governed |
| Hybrid | Partly system-backed, but still dependent on legacy orchestration or manual interpretation |
| Implemented | Backed by concrete PAA records and active code paths |
| Implemented / hybrid | Implemented in the system, but still passing through legacy or transitional orchestration paths |

## Most Important Structural Insight
The core software-engineering bridge is:
- `Design package -> Implementation plan -> Implementation-plan activities -> CoderBrief`

This is the point where source authority becomes executable engineering work.

## Most Important Governance Insight
The system should not allow broad summary claims without record-level backing.

The stricter table is intended to force each stage to answer:
- what record came in
- what transformation occurred
- what record came out
- whether the path is actually implemented or still hybrid
