# PAA Runtime Consolidation Design Correction

Date: 2026-05-13

## Purpose

Define the concrete design correction for the three highest-impact hybrid implementations still active in PAA:
1. authoritative workflow-state model
2. installed execution package as sole execution-time truth
3. runtime-vs-skill contract reduction

This note is a design correction, not a rollout plan.
It defines the corrected target architecture and the component boundaries that future implementation work should satisfy.

## Related Notes

Read alongside:
- `docs/2_Design/2026-05-13-paa-v2-component-relationships.md`
- `docs/terminology/paa-engineering-terminology-glossary.md`
- `docs/2_Design/2026-05-13-paa-system-component-diagram-v2.md`
- `docs/2_Design/2026-05-12-paa-handoff-execution-contract.md`
- `docs/2_Design/2026-05-12-paa-messaging-simplification-note.md`
- `docs/2_Design/2026-05-13-paa-hybrid-implementation-audit.md`
- `docs/2_Design/2026-05-09-paa-service-contracts.md`
- `docs/2_Design/2026-05-09-paa-data-contracts.md`
- `docs/2_Design/2026-05-09-team-worker-roles-design-spec.md`

## Design Summary

The corrected PAA runtime model is:
- workflow state is authoritative in a durable workflow state machine
- queue packets are wakeup and transport signals, not workflow truth
- installed execution package is the sole execution-time truth for consumer repos
- runtime code owns lifecycle invariants
- skills and automations express role intent and operator guidance only
- repo-local files are artifacts, logs, and evidence, not primary workflow-state truth

This correction removes the most harmful ambiguity from the current system.

## System Components Introduced Or Clarified

This correction clarifies three component roles.

### 1. Workflow State Machine

**Role**
Own the authoritative current workflow owner, workflow stage, and handoff-closeout state for each active slice.

### 2. Installed Execution Package

**Role**
Provide the single authorized package/brief/config context from which consumer runtime decisions are made.

### 3. Runtime Lifecycle Engine

**Role**
Own all transactionally important role and TechLead lifecycle behavior, independent of prompt wording.

## 1. Authoritative Workflow-State Model

### Role

Maintain the durable truth for:
- current owner role
- current workflow stage
- source handoff state
- terminal decision state
- whether a slice is active, waiting, blocked, or closed

### Corrected state model

For every active slice, durable workflow state must contain at least:
- `slice_key`
- `issue_number`
- `package_id_external`
- `brief_id_external`
- `current_owner_role`
- `workflow_stage`
- `source_packet_message_id`
- `source_packet_status`
- `last_transition_at`
- `lineage_state`
- `acceptance_decision`

The runtime may project this state into reports and logs, but it should not reconstruct it from queue residue.

### Service contract

The Workflow State Machine must provide:
1. `load_current_workflow_state(slice_key)`
2. `transition_workflow_state(source_state, transition_type, transition_evidence)`
3. `mark_source_packet_closed(source_packet_message_id)`
4. `record_terminal_decision(slice_key, decision_type, evidence)`
5. `derive_operator_summary(slice_key)`

### Messages received

The Workflow State Machine accepts transition intents from:
- `TechLead` assignment emission
- role result return
- QA verification return
- TechLead closeout and acceptance steps

### Messages published

The Workflow State Machine should publish normalized transition events such as:
- `workflow_state_transitioned`
- `workflow_owner_changed`
- `workflow_terminal_decision_recorded`

These events may remain internal implementation details, but the contract should be explicit.

### Corrected authority boundary

Queue packets do not define the workflow stage.
They only carry:
- wakeup signal
- execution context
- evidence reference

GitHub does not define the workflow stage either.
It remains external engineering truth used for validation and closeout, not as the primary state machine.

### Required invariants

1. A slice has one authoritative `current_owner_role` at a time.
2. A slice has one authoritative `workflow_stage` at a time.
3. A stale queue packet cannot change workflow interpretation.
4. Top-level status, lineage, and accepted-chain reporting must all derive from the same workflow semantics.

## 2. Installed Execution Package As Sole Execution-Time Truth

### Role

Provide the single execution-time source for:
- authorized issue/brief context
- canonical package and coder brief
- project-scoped role registry
- runtime policy/config relevant to a consumer repo

### Corrected model

There are two valid authority phases:

1. **Publication-time authority**
- producer repo compiles and publishes versioned authority artifacts
- DB may persist publication records and indexes

2. **Execution-time authority**
- consumer repo executes only against the installed execution package under:
  - `.project/data/paa/authority/current/`

The consumer runtime must not reconcile multiple competing authority truths during normal execution.

### Service contract

The Installed Execution Package must provide:
1. `load_current_authority_manifest()`
2. `load_design_package(package_id_external)`
3. `load_coder_brief(brief_id_external)`
4. `load_project_role_registry()`
5. `load_runtime_policy_views()`

### Data contract

The installed execution package must fully contain the execution-time data needed for:
- assignment compilation
- result validation
- branch/worktree derivation
- role registry lookups
- authoring checks

Consumer runtime should not require live DB reads to reconstruct active package or brief content.

### Corrected authority boundary

Producer DB is authoritative for publication workflows.
Installed execution package is authoritative for consumer execution workflows.

That means:
- DB content may be used to build the package
- DB content may be used to report on publication history
- consumer execution paths should read the installed package, not attempt to reconcile package truth against DB copies

### Overlay rule

Pilot or disposable overlays are allowed only if they materialize into the installed execution package surface before execution.

An overlay is valid only after it becomes part of the installed execution-time package surface.

### Required invariants

1. Consumer execution logic has one installed execution package surface.
2. Package/brief drift cannot exist between execution inputs and runtime validation inputs.
3. A queue packet cannot authorize work outside the installed execution package.
4. Overlay content must behave exactly like installed authority content once applied.

## 3. Runtime-Vs-Skill Contract Reduction

### Role

Move all lifecycle-critical behavior into runtime code and reduce skills/automations to declarative role guidance.

### Corrected model

The runtime lifecycle engine owns:
- claim validation
- role worktree preparation/reuse
- source packet closeout
- next packet emission
- terminal decision persistence
- merge/close orchestration
- transition evidence persistence

Skills and automations should describe:
- the role being performed
- the approved runtime entry points to call
- fail-closed expectations
- allowed slice scope

They should not be the place where transactional workflow semantics are invented.

### Service contract

The Runtime Lifecycle Engine must provide stable commands or service methods for:
1. preflight and claimability check
2. source packet claim and validation
3. role worktree preparation and entry
4. result input materialization
5. result packet return and source closeout
6. next assignment emission and source closeout
7. acceptance/merge/closeout

### Skill contract

A role skill should only need to say:
1. recover the current assignment through the runtime entry point
2. operate inside the authorized work surface
3. materialize result input
4. call the runtime return path
5. stop immediately on runtime contract failure

A role skill should not have to define:
- packet closeout semantics
- ack policy
- queue head verification rules
- lineage mutation rules
- acceptance state mutation rules

### Automation contract

An automation should only need to define:
- role identity
- schedule or trigger policy
- the runtime entry path to invoke
- logging/memory expectations
- fail-closed behavior

Automation prompt text should not be a hidden workflow engine.

### Required invariants

1. If a runtime path sends the next packet, the same runtime path closes the source packet.
2. If the runtime cannot verify the source packet, it fails closed.
3. If a role run succeeds, the source assignment lifecycle is fully resolved by runtime code.
4. Prompt wording changes cannot redefine workflow lifecycle semantics.

## Corrected Component Relationships

### Relationship 1: Workflow State Machine <-> Runtime Lifecycle Engine

The Runtime Lifecycle Engine performs transitions.
The Workflow State Machine persists and exposes the resulting authoritative state.

### Relationship 2: Installed Execution Package <-> Runtime Lifecycle Engine

The Runtime Lifecycle Engine reads all execution-time authorization from the installed execution package.
It does not reconcile active authority against a competing DB copy.

### Relationship 3: Skills / Automations <-> Runtime Lifecycle Engine

Skills and automations invoke the Runtime Lifecycle Engine.
They do not own transactional semantics.

### Relationship 4: Queue Transport <-> Runtime Lifecycle Engine

Queue transport delivers signals and context only.
It does not define workflow truth.

## Sequence Correction

### Corrected handoff sequence

1. runtime loads the authoritative workflow state machine state
2. runtime loads installed execution package
3. runtime determines whether work is claimable
4. runtime claims and validates the source packet
5. runtime executes the bounded transition
6. runtime persists the authoritative workflow transition
7. runtime emits the next packet if needed
8. runtime closes the source packet in the same controlled path
9. runtime writes logs and evidence artifacts

This ordering is the key correction.
The queue and artifacts now follow authoritative runtime state, not the other way around.

## What Files Become After This Correction

Repo-local files still matter, but their role narrows.

### Files that remain important
- installed execution package artifacts
- compiled review/result/decision artifacts
- automation logs
- automation memory
- human-readable reports

### Files that should no longer be treated as primary workflow truth
- queue residue previews
- ad hoc report artifacts used to infer current owner/stage
- prompt-local memory used to reconstruct lifecycle state

## Acceptance Criteria For The Correction

The correction should be considered satisfied only when all of the following are true:

1. `techlead-status`, lineage, and accepted-chain reporting derive from one workflow-state model.
2. Consumer runtime executes from one installed execution package surface only.
3. Skills can be simplified without losing correctness.
4. Prompt wording changes cannot change queue-closeout semantics.
5. Queue residue can be operationally noisy without altering workflow truth.

## Design Conclusion

The correct architecture is not:
- queue as workflow truth
- DB as partial truth
- repo-local files as backup truth
- skills/prompts as hidden transaction logic

The correct architecture is:
- durable workflow state machine as truth
- installed execution package as execution-time truth
- runtime lifecycle engine as the sole owner of transactional semantics
- skills and automations reduced to declarative role guidance

That is the concrete design correction that should govern the next round of consolidation work.
