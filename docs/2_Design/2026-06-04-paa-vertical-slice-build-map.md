Title: PAA Vertical Slice Build Map
Doc-ID: paa-vertical-slice-build-map
Doc-Type: design-note
Status: active
Lifecycle-Stage: design
Created: 2026-06-04
Last-Edited: 2026-06-04
Author: Billy Weisberg
Repo: paa-platform
Component: PAAVerticalSliceBuildMap
Domain: system-design
Keywords: paa, python, vertical slice, build map, cli, api, services, data layer, methodology execution, producer, runtime
Depends-On: 2026-06-04-paa-python-north-star-architecture.md, 2026-06-04-paa-python-phase-ordered-progress-tree.md, 2026-06-04-paa-python-build-sequence-from-structure.md, 2026-06-04-paa-vertical-slice-build-strategy.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-07-01
Owners:
Expires:
Issue:
PR:
Authority-Source:
Implementation-Status: in-progress
Summary: Defines the ordered vertical-slice build map for the Python PAA system, with layer-by-layer ownership for each slice.

# PAA Vertical Slice Build Map

## Purpose

This note turns the current North Star, dependency review, phase-ordered progress tree, and aligned vertical-slice strategy into one ordered build table.

Each row is one vertical slice.
Each slice should be built in this aligned layer order:
1. aligned data layer
2. aligned domain/app logic
3. aligned API surface
4. aligned CLI surface
5. aligned end-to-end CLI proof

## Slice Ordering Rule

Slices are ordered by:
- dependency readiness
- aligned PAA workflow and methodology sequence
- `MethodologyExecution` support needs
- how early the slice unlocks later slices

The earlier rows should be built first unless the design is updated deliberately.

## Vertical Slice Table

| Seq | Slice | Workflow / Capability | Data Layer | Domain / App Logic | API | CLI | End-to-End Proof |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S01 | Realization Type Registry | Governed component-realization vocabulary foundation | `paa_core.repositories.component_design` list/add/show/update realization-type operations; first `db.py` inventory for taxonomy persistence if needed | `paa_core.application.contracts.component_taxonomy.py`; `paa_core.application.dto.component_taxonomy.py`; `paa_core.application.services.component_taxonomy.py` for realization type operations | `paa_core.api.runtime.routers.component_taxonomy.py` realization-type routes | `paa component realization-type list|show|add|update ...` under `paa_cli.app.py` / `paa_cli.router.py` | `paa component realization-type list`; `paa component realization-type add ...`; verify returned governed rows through the real stack |
| S02 | Element-Realization Mapping | Governed allowed-mapping management between element types and realization types | `paa_core.repositories.component_design` list/add/update mapping operations for `component_element_type_realization_types` | Same `component_taxonomy` contract/dto/service surface, adding mapping operations and rule validation | Same `component_taxonomy` router, mapping endpoints | `paa component realization-map list|add|update ...` | `paa component realization-map add ...`; `paa component realization-map list --element-type ...` |
| S03 | Methodology Pointer Inspection And Transition | Persisted answer to where the system is and what is valid next | `paa_core.repositories.methodology_execution` read current execution, read projection, append event / apply transition where needed | `paa_core.application.contracts.methodology_execution.py`; `paa_core.application.dto.methodology_execution.py`; `paa_core.application.services.methodology_execution.py`; reuse `runtime.workflow.methodology_execution_preflight`, `methodology_execution_projection`, `methodology_execution_state` | `paa_core.api.runtime.routers.methodology_execution.py` | `paa methodology current`; `paa methodology next`; `paa methodology transition ...` or equivalent preflight path | `paa methodology current`; `paa methodology next`; pointer-aware result proves lane/stage/step ownership through the real stack |
| S04 | Design Package Derivation | Source authority to Stage 1 design package | `paa_core.repositories.component_design`; `paa_core.repositories.execution_package`; only extract `db.py` helpers if this slice needs them | Existing producer modules: `paa_core.producer.design_package_deriver`, `paa_core.application.services.producer_commands` | Existing `paa_core.api.runtime.routers.producer.py` design-package route | Existing `paa producer derive-design-package ...` | Run `paa producer derive-design-package ...` through API path and verify produced design-package payload |
| S05 | Derivation Readiness Evaluation | Evaluate whether a package can enter coder-brief / plan derivation | Data access in `repositories.component_design`, `repositories.methodology_execution`, and readiness-support queries; extract only slice-specific `db.py` reads if needed | Existing `paa_core.producer.derivation_readiness`, `paa_core.producer.readiness`, `paa_core.application.services.producer_commands`; pointer-aware readiness preflight if required | Existing producer readiness routes in `routers/producer.py` | Existing `paa producer evaluate-derivation-readiness ...` | Run readiness command through `paa`; verify result and any pointer constraints |
| S06 | Implementation Plan Derivation | Design package to governed implementation plan | `paa_core.repositories.implementation_plan`; `repositories.component_design`; `repositories.methodology_execution` as needed | Existing `paa_core.producer.implementation_plan_deriver`; permanent `paa_core.services.implementation_plan_derivation`; app service surface in `producer_commands` | Existing producer route for plan derivation | Existing `paa producer derive-implementation-plan ...` | Run `paa producer derive-implementation-plan ...`; verify plan rows and response through `paa` |
| S07 | Implementation Plan Progress And Activity State | Inspect/update plan progress and derive next activity | `paa_core.repositories.implementation_plan`; `repositories.workflow_state`; `repositories.methodology_execution` for pointer awareness | Existing `paa_core.producer.implementation_plan_progress`, `implementation_plan_activity_state`; permanent `paa_core.services.implementation_plan_progress`; app services in `producer_commands` and future `methodology_execution` coordination | Existing producer routes for progress, activity state, and next activity bundle | Existing `paa producer implementation-plan-progress ...`; `set-implementation-plan-activity-state ...`; `derive-next-activity-bundle ...` | Run the progress commands through `paa`; verify the next activity and updated state |
| S08 | Brief Targets And Coder Brief Assembly | Turn plan/package truth into a coder brief with explicit realization targets | `repositories.component_design`; `repositories.implementation_plan`; `repositories.methodology_execution`; brief-target persistence rows | Existing `paa_core.producer.brief_target_author`, `coder_brief_assembler`, `brief_reviewer`; app service surface in `producer_commands` | Existing producer routes for `author-brief-targets`, `assemble-coder-brief`, `review-coder-brief` | Existing `paa producer author-brief-targets ...`; `assemble-coder-brief ...`; `review-coder-brief ...` | Run brief-target and coder-brief commands end to end; verify produced brief and target rows |
| S09 | Architect Packet Preparation And Publication | Convert accepted brief/package truth into runtime-ready packets and authority outputs | `repositories.execution_package`; `repositories.runtime_event`; packet persistence helpers; slice-specific `db.py` packet helpers only if required | Existing `paa_core.producer.architect_packet_preparer`, `authority_packets`, `publish`, `authority_runtime`, `authority_support` | Existing producer routes for `prepare-architect-packet`, `publish-authority-package`, `authority ...` | Existing `paa producer prepare-architect-packet ...`; `paa producer publish-authority-package ...`; `paa producer authority ...` | Run architect-packet and authority commands through `paa`; verify packet payload / manifest summary |
| S10 | Runtime Bootstrap And Queue Topology | Local process bootstrap and queue topology setup | `repositories.runtime_identity`; `repositories.runtime_event`; transport persistence and queue-admin records if present | Existing `paa_core.runtime.support.install`; `paa_core.runtime.control.supervisor`; `paa_core.application.services.runtime_admin` and `queue_admin`; bootstrap exception remains local for start/stop/install | `paa_core.api.runtime.routers.supervisor.py`; `routers/queues.py` where API-backed behavior applies | `paa runtime start|stop|status`; `paa queue ensure-topology ...` | Run runtime bootstrap commands and queue topology checks; accept the direct local bootstrap exception where HTTP cannot own process start |
| S11 | Runtime Claim, Dispatch, And Workflow State | Consume architect/runtime packets and advance workflow state | `repositories.runtime_event`; `repositories.workflow_state`; `repositories.runtime_identity`; transport state in `runtime.transport` and workflow repositories | Existing `paa_core.runtime.transport.packet_dispatch`, `claim_ledger`, `handoff_runtime`; `runtime.orchestration.queue_claim_runtime`, `queue_packet_runtime_controller`; `runtime.workflow.workflow_lifecycle` | Existing runtime routes in `routers/packets.py`, `routers/workflow.py`, `routers/status.py` | `paa queue claim ...`; `paa runtime dispatch ...`; `paa report/status ...` or equivalent runtime commands | Run queue claim / dispatch / workflow-status commands through `paa`; verify workflow state changes |
| S12 | Worker Execution And Result Packets | Execute bounded role work and publish result packets | `repositories.runtime_event`; `repositories.workflow_state`; result-packet persistence; evidence tables / rows; any worker-specific low-level extraction from `db.py` only if required | Existing `paa_core.runtime.workers.*`; `runtime.hosts.*`; `runtime.bridges.*`; `runtime.packets.*`; `runtime.support.runtime_evidence`; producer-side `authority_packet_results` for result shaping | Existing runtime/producer result-facing routes in `routers/packets.py`, `routers/status.py`, `routers/producer.py` where needed | `paa worker ...`; `paa verify runtime-smoke`; any worker dry-run / replay commands | Run one bounded worker or dry-run flow through `paa`; verify emitted result packet and evidence |
| S13 | Verification, Acceptance, And Closeout | QA/acceptance decisioning and safe completion of slices | `repositories.runtime_event`; `repositories.workflow_state`; closeout / acceptance records; methodology pointer advancement | Permanent services: `paa_core.services.techlead_acceptance_decision`, `techlead_delivery_review_decision`, `techlead_closeout_decision`, `techlead_worker_review_routing`; producer `authority_acceptance`; application runtime status / operator services | Existing and planned routes in `routers/status.py`, `routers/workflow.py`, `routers/producer.py`, `routers/operators.py` for accept/reject/report paths | `paa verify ...`; `paa accept ...`; `paa report ...` | Run verification and acceptance commands through `paa`; verify state transition, decision record, and closeout outputs |

## Immediate Working Set

Based on the current phase-ordered progress tree, the immediate active working set is:
1. `S01` Realization Type Registry
2. `S02` Element-Realization Mapping
3. `S03` Methodology Pointer Inspection And Transition

These slices directly satisfy the current active phase:
- `Phase 2. Data Layer Foundation`
- then `Phase 3. Services/App Logic Over Data`
- then `Phase 4. API Exposure`
- then `Phase 5. CLI Proof Surface`

Current build position inside the working set:
- active slice: `S03`
- completed layer: data layer
- next layer: domain/app logic

## `db.py` Extraction Rule Inside The Map

`db.py` is not a slice by itself.

It is handled inside slices only when:
- the slice needs a data responsibility that still lives in `db.py`
- the destination repository or low-level data module is already defined
- the CLI proof path for that slice already exists or is being completed in the same slice

## Usage Rule

Use this table to decide the next implementation slice.

For each slice:
1. confirm the row is the next one allowed by dependencies
2. mark that slice as active in the phase-ordered progress tree
3. build left to right across the row
4. prove the row through `paa`
5. mark the row complete in the phase-ordered progress tree
6. only then move to the next row

That is how the full Python PAA system should be assembled into one coherent governed system.
