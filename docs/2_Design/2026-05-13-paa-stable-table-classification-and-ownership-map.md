# PAA Stable Table Classification And Ownership Map

Date: 2026-05-13

## Purpose

Execute Phase 1 of the DB Model Completion Plan by making the current DB table set explicit in two ways:
1. stable classification within the V2 PAA data model
2. target ownership by V2 system component

This note exists to stop the next design steps from speaking vaguely about "the DB" as if every table has the same role.

The DB model is already large enough that we need a crisp ownership and classification map before finalizing new entity families.

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-13-paa-db-model-completion-plan.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-db-model-diagram-and-gap-analysis.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-v2-component-relationships.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-data-access-layer-design.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-existing-component-design-model-audit.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-component-design-foundation-and-derivation-baseline.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-final-execution-package-registration-entity-design.md`

## Classification Model

Each persisted DB surface is classified as one of these:
- `stable_authority`: long-lived structured design or authority facts
- `derivative_slice`: per-slice artifacts derived from upstream authority
- `runtime_event`: append-only or historical execution/transport facts
- `workflow_truth`: authoritative current workflow state and transition truth
- `projection`: read-model or reporting surface derived from primary truth

Important rule:
- a table may support multiple use cases, but it must have one primary classification
- if a table is being used as if it were in two classifications at once, that is a design smell to correct

## Ownership Model

The target V2 system components that may own table semantics are:
- `Authority Publication And Derivation`
- `Installed Execution Package Manager`
- `Component Design Derivation Engine`
- `Runtime Lifecycle Engine`
- `Workflow State Machine`
- `Reporting And Traceability Projection`

Ownership here means semantic ownership, not merely "writes some rows sometimes."

## Stable Table Classification Matrix

| Table | Primary Classification | Target Owner | Keep/Extend/Add/Demote | Notes |
| --- | --- | --- | --- | --- |
| `paa.projects` | `stable_authority` | `Authority Publication And Derivation` | `keep` | Top-level system/project identity. |
| `paa.roles` | `stable_authority` | `Authority Publication And Derivation` | `keep` | Canonical role vocabulary. |
| `paa.authority_versions` | `stable_authority` | `Authority Publication And Derivation` | `keep` | Versioned published authority lineage. |
| `paa.authority_version_fragments` | `stable_authority` | `Authority Publication And Derivation` | `keep` | Authority-version to fragment bindings. |
| `paa.authority_version_targets` | `stable_authority` | `Authority Publication And Derivation` | `keep` | Authority-version to implementation target bindings. |
| `paa.source_artifacts` | `stable_authority` | `Authority Publication And Derivation` | `keep` | Source-authority inventory. |
| `paa.source_statements` | `stable_authority` | `Authority Publication And Derivation` | `keep` | Fine-grained extracted authority statements. |
| `paa.requirements` | `stable_authority` | `Authority Publication And Derivation` | `keep` | Stable requirement model. |
| `paa.requirement_sources` | `stable_authority` | `Authority Publication And Derivation` | `keep` | Requirement traceability to source statements. |
| `paa.design_decisions` | `stable_authority` | `Authority Publication And Derivation` | `keep` | Stable design-decision catalog. |
| `paa.decision_requirements` | `stable_authority` | `Authority Publication And Derivation` | `keep` | Decision-to-requirement linkage. |
| `paa.spec_fragments` | `stable_authority` | `Authority Publication And Derivation` | `keep` | Stable scoped fragment model. |
| `paa.spec_fragment_requirements` | `stable_authority` | `Authority Publication And Derivation` | `keep` | Requirement coverage in fragments. |
| `paa.spec_fragment_decisions` | `stable_authority` | `Authority Publication And Derivation` | `keep` | Decision shaping of fragments. |
| `paa.implementation_targets` | `stable_authority` | `Authority Publication And Derivation` | `keep` | Stable implementation-target catalog. |
| `paa.components` | `stable_authority` | `Component Design Derivation Engine` | `extend` | Stable component identity must become current and complete for V2. |
| `paa.component_surfaces` | `stable_authority` | `Component Design Derivation Engine` | `extend` | Stable component-owned surfaces. |
| `paa.component_relationships` | `stable_authority` | `Component Design Derivation Engine` | `extend` | Stable structural relationships, not runtime sequencing. |
| `paa.work_items` | `stable_authority` | `Authority Publication And Derivation` | `keep` | Work-item identity and scope anchor. |
| `paa.design_packages` | `derivative_slice` | `Component Design Derivation Engine` | `extend` | Reviewed Stage 1 slice packages. |
| `paa.design_package_signoffs` | `derivative_slice` | `Component Design Derivation Engine` | `keep` | Signoff history over derivative packages. |
| `paa.coder_run_briefs` | `derivative_slice` | `Component Design Derivation Engine` | `extend` | Execution-facing slice briefs derived from packages. |
| `paa.component_dependency_edges` | `derivative_slice` | `Component Design Derivation Engine` | `extend` | Package-scoped dependency/sequencing edges; not stable structure yet. |
| `paa.coder_brief_sequence_states` | `projection` | `Reporting And Traceability Projection` | `extend` | Derived readiness state; should remain clearly downstream of stable and derivative inputs. |
| `paa.execution_records` | `runtime_event` | `Runtime Lifecycle Engine` | `extend` | Runtime execution evidence/history, not workflow truth. |
| `paa.handoffs` | `runtime_event` | `Runtime Lifecycle Engine` | `extend` | Handoff intents and return links; input to workflow transitions. |
| `paa.queue_messages` | `runtime_event` | `Runtime Lifecycle Engine` | `extend` | Packet transport history and payload persistence. |
| `paa.automation_runs` | `runtime_event` | `Runtime Lifecycle Engine` | `extend` | Run identity/history; should absorb structured milestones now lost to files. |
| `paa.verification_obligations` | `runtime_event` | `Runtime Lifecycle Engine` | `keep` | Verification work generated from slices and runtime. |
| `paa.evidence` | `runtime_event` | `Runtime Lifecycle Engine` | `keep` | Evidence references and structured proof links. |
| `paa.acceptance_events` | `runtime_event` | `Runtime Lifecycle Engine` | `extend` | Acceptance/closeout event history; should align more tightly with workflow transitions. |
| `paa.v_work_item_full_chain_traceability` | `projection` | `Reporting And Traceability Projection` | `keep` | Read model only, never primary truth. |

## Missing Entity Families And Their Target Owners

| Proposed Entity Family | Target Classification | Target Owner | Reason |
| --- | --- | --- | --- |
| `paa.workflow_states` | `workflow_truth` | `Workflow State Machine` | Canonical current workflow truth is currently missing. |
| `paa.workflow_transitions` | `workflow_truth` | `Workflow State Machine` | Canonical transition history is currently missing. |
| `paa.queue_claims` | `runtime_event` | `Runtime Lifecycle Engine` | Claim/lease truth is operationally significant, but semantically transport-support state. |
| `paa.execution_package_installs` | `stable_authority` | `Installed Execution Package Manager` | Current active install state must be queryable in DB. |
| `paa.execution_package_overlays` | `stable_authority` | `Installed Execution Package Manager` | Active overlay state must be queryable in DB. |
| `paa.transition_inputs` | `runtime_event` | `Runtime Lifecycle Engine` | Structured transition inputs need canonical rows when operationally significant. |
| `paa.automation_run_events` | `runtime_event` | `Runtime Lifecycle Engine` | Structured run milestones must move out of file-only logs. |
| `paa.workflow_status_projections` | `projection` | `Reporting And Traceability Projection` | Optional explicit projection family for operator status. |
| `paa.lineage_projections` | `projection` | `Reporting And Traceability Projection` | Optional explicit lineage read model. |
| `paa.accepted_chain_projections` | `projection` | `Reporting And Traceability Projection` | Optional explicit accepted-chain read model. |

## Ownership Rules

### 1. `Authority Publication And Derivation`
Owns semantics for:
- source-authority extraction
- requirements, decisions, fragments, targets
- role vocabulary
- authority-version publication
- work-item identity and scope

Does not own:
- workflow truth
- queue transport lifecycle
- installed execution-package activation state in consumer environments

### 2. `Installed Execution Package Manager`
Owns semantics for:
- which execution package is installed
- which overlays are active
- provenance of install and overlay activation

Does not own:
- source-authority publication
- workflow state
- runtime handoff lifecycle

### 3. `Component Design Derivation Engine`
Owns semantics for:
- stable component catalog
- stable component surfaces and structural relationships
- Stage 1 design-package derivation
- coder-brief derivation
- package-scoped dependency edges

Does not own:
- current workflow state
- queue transport state
- reporting projections as primary truth

### 4. `Runtime Lifecycle Engine`
Owns semantics for:
- handoff execution
- queue message persistence
- automation-run history
- evidence and verification history
- acceptance/closeout event recording
- queue-claim lifecycle

Does not own:
- current workflow truth
- stable component design structure
- projection truth

### 5. `Workflow State Machine`
Owns semantics for:
- current owner
- current workflow stage
- transition legality
- transition application
- blocked/closed/superseded state

Consumes but does not own:
- handoffs
- queue messages
- queue claims
- automation runs
- acceptance events
- design packages
- coder briefs
- GitHub state

### 6. `Reporting And Traceability Projection`
Owns semantics for:
- lineage views
- accepted-chain views
- operator status views
- readiness projections

Does not own:
- source truth of any workflow transition
- source truth of any runtime event
- source truth of any stable component definition

## Hard Separation Rules

1. `paa.handoffs` and `paa.queue_messages` are not workflow truth.
2. `paa.coder_brief_sequence_states` is not stable Component Design structure.
3. `paa.design_packages` and `paa.coder_run_briefs` are not substitutes for `paa.components`.
4. projection views and report exports may summarize truth, but may not define truth.
5. installed execution-package files remain local runtime inputs, but active install/overlay state must be registered in DB.

## Decisions Locked By This Note

This note intentionally locks these baseline decisions:

1. `paa.coder_brief_sequence_states` is classified as a projection layer record, not stable authority and not workflow truth.
2. `paa.component_dependency_edges` remains derivative and package-scoped until a later design explicitly splits stable dependency structure from slice-specific sequencing.
3. `paa.queue_claims` is treated as a runtime-event family owned semantically by the `Runtime Lifecycle Engine`, even though the `Workflow State Machine` depends on it.
4. `paa.work_items` remains a stable-authority anchor, not a workflow-state substitute.

## Phase 1 Exit Statement

Phase 1 of the DB Model Completion Plan is complete when this note is accepted as the baseline classification and ownership map.

From that point forward:
- every new DB-primary entity proposal must declare its classification and owner
- every existing table extension must preserve the separation defined here
- no design note should refer to "the DB" as a single undifferentiated surface

## Hard Conclusion

The next PAA data-model work should be disciplined, not exploratory.

We already know:
- which tables are stable authority
- which are derivative slice artifacts
- which are runtime events
- which are projections
- which new entity families are missing

That means the next correct move is not another audit.
It is final entity design for the missing workflow-state layer from this baseline.
