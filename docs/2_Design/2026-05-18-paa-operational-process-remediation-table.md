# PAA Operational Process Remediation Table

## Status
Draft.

## Purpose
This document converts the strict process record table into a more operational view.

The goal is to answer, for each meaningful process step:
- what step it is
- what code or module currently owns it
- what DB-primary truth anchors it
- what automation is still missing
- what the next remediation should be

This is intended to help drive implementation sequencing and gap closure.

## Operational Remediation Table

| Step | Current Owning Code / Module | Primary DB Truth | Missing Automation | Next Remediation |
|---|---|---|---|---|
| Authority interpretation | Mixed docs and architect reasoning | None first-class | Structured authority-interpretation materialization | Decide whether authority interpretation becomes a first-class stored artifact or stays explicitly manual |
| System design | Design docs and architecture notes | Partial, indirect through downstream records | Stronger structured system-design persistence | Define whether system-design sections need DB-primary representation or remain document authority |
| Component model and dependency graph | Component design docs plus component records | `paa.components`, related component tables | Stronger graph authoring and validation tooling | Add explicit graph validation/report tooling over component dependencies |
| Slice selection | Architect/manual selection | Partial via downstream package records | First-class slice-selection record and decision audit | Add a narrow slice-selection record or explicit decision note standard |
| Design package materialization | Producer flows and package design tooling | `paa.design_packages` | Better operator-facing package authoring UX | Improve package authoring surfaces and validation ergonomics |
| Implementation plan root | Implementation-plan derivation code | `paa.implementation_plans` | Higher-level authoring and review UX | Add repository-backed plan review and editing surfaces |
| Implementation-plan activities | Implementation-plan derivation code | `paa.implementation_plan_activities`, dependency tables | Richer activity authoring and visualization | Add plan activity visualizer and stronger dependency editing |
| Activity-to-target mapping | Implementation plan + component/code-target model | `paa.component_elements`, realization target tables, implementation-plan records | Better structured mapping authoring | Add tools that show activity -> element -> target mapping directly |
| Draft brief derivation | Producer brief assembly | `paa.coder_run_briefs` | More explicit use of plan activities in all brief sections | Continue strengthening brief derivation from implementation-plan activity truth |
| Brief approval | Producer review flow | brief authority lifecycle tables and events | Stronger operator approval UX | Add clearer approval views and history inspection surfaces |
| Packet-ready execution authority | Packet preparation flow | coder brief authority state, packet prep metadata | Better packet inspection UX | Add packet inspection and packet-ready validation reports |
| Assignment decision | `techlead.py` and related runtime helpers | Workflow truth plus queue/handoff context | Replace remaining legacy decision heuristics | Extract TechLead decision logic into thinner application services |
| Assignment dispatch | Consumer and queue tooling | handoff, queue, workflow tables | More uniform dispatch service boundary | Move packet dispatch decisions behind cleaner application services |
| Worker execution-context resolution | Execution Package Resolution Service | execution-package install and overlay tables | More widespread runtime adoption | Replace remaining ad hoc execution-context lookup paths |
| Worker result return transition | Workflow Lifecycle Service | workflow state and transition tables | Broader runtime application usage | Connect `apply_workflow_transition(...)` in more result-handling runtime paths |
| Worker review and QA routing | `techlead.py` hybrid orchestration | Workflow state plus packet evidence | Replace hybrid packet heuristics | Continue decomposing TechLead review/routing logic |
| QA assignment dispatch | Consumer/queue runtime + workflow updates | handoff, queue, workflow tables | Better dedicated assignment application service | Extract QA assignment emission into cleaner service boundary |
| QA result return transition | Workflow Lifecycle Service | workflow state and transition tables | Runtime application path symmetry with worker results | Extend runtime application of `qa_result_returned` |
| Acceptance / reroute / closeout decision | `techlead.py` and closeout flows | acceptance events, workflow truth, package/runtime state | Stronger decision-service decomposition | Extract closeout and acceptance logic from the runtime hub |
| Runtime update and running code | execution-package/runtime flows | execution package installs, overlays, runtime state | Better end-to-end visibility from closeout to installed surface | Add stronger reporting from accepted slice to installed/running surface |

## Most Important Current Operational Gap
The largest remaining hybrid area is not the producer derivation path.

It is the runtime decision and orchestration layer around TechLead behavior, where:
- workflow truth exists
- transition services now exist
- but major orchestration still lives in a large consumer runtime hub

## Most Important Near-Term Remediations
1. extend runtime application to `qa_result_returned`
2. continue extracting TechLead workflow/routing behavior out of the runtime hub
3. improve activity-to-target and plan-review operator tooling
4. improve packet/approval/operator visibility over already-implemented authority flows
