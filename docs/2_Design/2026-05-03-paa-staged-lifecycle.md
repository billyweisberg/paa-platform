# 79. PAA Staged Lifecycle

## Purpose
This document defines the staged operating lifecycle for Project for Autonomous Agents (PAA).

The goal is to support high-assurance, architecture-led software delivery for complex projects in this portfolio.

This is not an Agile ticket stream where implementation agents infer the system while coding.
It is a staged engineering process where:
- design is authored and reviewed before coding
- implementation packets are derived before execution
- runtime loops are governed
- changes to the system feed back through published authority

## Design philosophy
For this portfolio, the right model is closer to:
- staged systems engineering
- architecture-first decomposition
- reviewed derived implementation packets
- controlled execution with autonomous agents

This does **not** mean giant big-bang implementation.
It means:
- narrow slices
- strong upstream design
- clear ownership
- explicit gates
- repeatable derivation

## Lifecycle overview
The PAA lifecycle has six stages:

1. Design / Authoring
2. Derivation
3. Execution
4. Verification
5. Acceptance
6. Authority Update / Re-Derivation

Each stage has:
- owners
- required inputs
- required outputs
- gate conditions

## Stage 1: Design / Authoring

### Owners
- Product Owner
- Architect
- Project Designer

### Purpose
Define what the system should become before any coder agent is asked to implement it.

### Inputs
- source artifacts
- source statements
- product vision
- roadmap
- existing authority version
- current system state
- prior acceptance/rejection history

### Outputs
- reviewed requirements
- reviewed design decisions
- spec fragments
- implementation targets
- successor relationships
- authority task definitions
- architectural authority constraints

### Required architectural outputs
These must be explicit before derivation:
- `required_architecture_seams`
- `target_module_boundaries`
- `max_responsibility_expansion`
- `forbidden_module_growth_patterns`
- `authorized_delta_family`
- `out_of_scope_delta_families`
- `expected_touch_surfaces`
- `pre_handoff_scope_checks`

### Gate
Do not move to derivation unless the slice is:
- narrow
- architecturally placed
- bounded against adjacent deltas
- clear enough that coder agents do not need to invent structure

## Stage 2: Derivation

### Owners
- Architect
- Project Designer
- TechLead

### Purpose
Turn reviewed design authority into implementation-facing authority.

### Inputs
- authority task
- spec fragment
- implementation target
- component model
- component surfaces
- component relationships

### Outputs
- `coder_run_brief`
- packet-ready `architect_cycle_packet`
- implementation boundary checks
- test contract
- anti-goals
- collaboration pattern mapping

### Derived artifact requirements
The `coder_run_brief` must answer:
- what component is being built
- what role it plays
- which system layer it belongs to
- which tier it belongs to, if relevant
- which aspects are being implemented
- which modules may be edited
- which modules may not grow
- which collaborators participate in the pattern
- which dependencies must be injected
- what tests prove the run
- what scope checks block QA handoff

### Gate
Do not move to execution unless the coder brief is:
- complete
- validated
- packet-embedded
- tied to the current authority version

## Stage 3: Execution

### Owners
- TechLead

### Executing agents
- Python Dev
- other coder agents in other projects as applicable

### Purpose
Implement the assigned slice against the coder-facing brief, not against ad hoc interpretation.

### Inputs
- claimed `architect_cycle_packet`
- embedded `coder_run_brief`
- GitHub issue / PR execution state
- current authority mirror

### Outputs
- code changes
- tests
- artifacts
- `slice_result_packet`

### Rules
- coder-facing implementation authority comes from the embedded `coder_run_brief`
- GitHub is the execution record, not the design authority
- if pre-handoff scope checks fail, do not send QA handoff
- if the slice becomes contaminated, stop and surface the failure

### Gate
Do not move to QA unless:
- tests pass
- protected baseline checks pass
- pre-handoff scope checks pass
- the work remains inside the authorized implementation boundary

## Stage 4: Verification

### Owners
- QA

### Purpose
Independently verify that implementation matches the authorized slice and did not damage the protected baseline.

### Inputs
- `slice_result_packet`
- authority mirror
- coder brief context as needed
- GitHub issue / PR state

### Outputs
- `qa_verification_packet`
- verification evidence
- findings
- escalation if needed

### Gate
Do not move to Architect acceptance unless QA has either:
- `pass`
- or an explicit escalation state like `needs_human_review`

## Stage 5: Acceptance

### Owners
- Architect

### Purpose
Accept or reject the verified slice and preserve the engineering record.

### Inputs
- `qa_verification_packet`
- GitHub PR / issue state
- published authority
- acceptance gate rules

### Outputs
- merge or non-merge decision
- acceptance or rejection record
- PAA persistence of the decision

### Rules
- Architect owns acceptance and merge
- non-pass QA packets fail closed
- if the slice is rejected, the runtime loop must route to the correct recovery owner

## Stage 6: Authority Update / Re-Derivation

### Owners
- Product Owner
- Architect
- Project Designer
- TechLead

### Purpose
Publish new project truth after acceptance or system design change, then re-derive downstream implementation authority.

### Inputs
- accepted merge state
- updated project knowledge
- successor authoring decisions
- system-change decisions

### Outputs
- new authority version
- published authority mirrors
- next task authoring
- new or regenerated coder briefs
- next `architect_cycle_packet`

### Important rule
If no allowed successor exists after merge:
- stop the runtime loop
- treat that as a clean authoring stop
- do not fabricate the next slice from execution continuity alone

## TechLead role in this lifecycle
TechLead is not the upstream designer.
TechLead is the runtime governor.

### TechLead responsibilities
- reconcile state
- route next owner
- detect recovery modes
- stop bad loops
- verify readiness for unattended continuation
- escalate to humans / Architect / Product Owner when the process leaves its safe envelope

## Recovery model placement
Recovery belongs between execution and acceptance, but is governed by TechLead.

Examples:
- `dev_rework_required`
- `dev_reset_required`
- `fresh_qa_reverification_required`
- `merged_but_no_authorized_successor`

Recovery should not be rediscovered ad hoc by coder agents.
It should be recognized as a first-class lifecycle state.

## Why this lifecycle matters
This process keeps coder agents where they belong:
- inside prepared implementation authority
- not improvising system design

It also keeps system change where it belongs:
- upstream
- reviewed
- published
- re-derived

That is the difference between:
- autonomous coding chaos
and
- controlled autonomous engineering.

## Immediate application
Use this lifecycle as the governing model for:
- Fractal Core
- AgentHub
- GIS
- AIF Workbench

The role names may differ per project.
The staged lifecycle should remain portable.
