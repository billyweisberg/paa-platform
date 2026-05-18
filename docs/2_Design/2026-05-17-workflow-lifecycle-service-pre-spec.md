# Workflow Lifecycle Service Pre-Spec

Date: 2026-05-17
Status: active

## Purpose

Define the modern pre-spec for `Workflow Lifecycle Service` before touching service implementation.

This note narrows the service boundary so we do not accidentally rebuild the older "workflow state machine" as one oversized component. The intent is to keep workflow truth authoritative while separating:

- workflow transition legality
- acceptance semantics
- reset / recovery semantics

into explicit policy collaborators.

## Why This Service Exists

PAA already has:

- DB-primary workflow truth modeled in:
  - `paa.workflow_states`
  - `paa.workflow_transitions`
- runtime evidence modeled through:
  - handoffs
  - queue messages
  - transition inputs
  - acceptance events
- execution-context truth modeled through:
  - `Execution Package Resolution Service`

What is still missing is the core domain service that:

- loads current workflow truth
- evaluates one requested transition against explicit policies
- applies legal state mutation
- records authoritative transition history

without treating:

- queue state
- GitHub state
- report files
- local memory

as workflow truth.

## Architecture Placement

- layer: `Domain Services`
- stratum: `Stratum 2`

This remains one of the earliest valid logic-service nodes in the dependency graph because it depends on already-modeled ports and policy boundaries rather than host-specific runtime behavior.

## Owned Responsibilities

`Workflow Lifecycle Service` owns:

- loading current workflow truth for one work item
- normalizing one proposed workflow transition request
- consulting policy collaborators for:
  - transition legality
  - acceptance semantics
  - reset / recovery handling
- coordinating the write group that updates:
  - current workflow state
  - transition history
- returning a structured result that explains:
  - applied vs rejected
  - resulting stage
  - blocking / repair implications

## Non-Owned Responsibilities

`Workflow Lifecycle Service` does not own:

- queue transport or claiming semantics
- execution-package install lookup logic
- acceptance-event persistence as a standalone runtime concern
- runtime event ingestion semantics
- projection refresh ownership
- GitHub issue or PR mutation
- coder-brief derivation

## Required Collaborators

### Repository collaborators

- `WorkflowStateRepository`
- `RuntimeEventRepository`

### Domain-service collaborator

- `Execution Package Resolution Service`

### Policy collaborators

- `WorkflowTransitionPolicy`
- `AcceptancePolicy`
- `ResetRecoveryPolicy`

### Common infrastructure contracts

- `TransactionRunner`
- `Clock`
- `StructuredLogger`

## Policy Decomposition

This service should not absorb all workflow semantics internally.

The minimum explicit policy split is:

### `WorkflowTransitionPolicy`

Owns:

- whether a requested transition is legal from the current workflow stage
- whether current owner / lineage / consistency state allows the move
- what next workflow stage should result when the move is legal

Does not own:

- acceptance-event meaning
- reset / repair recommendations
- DB mutation

### `AcceptancePolicy`

Owns:

- whether evidence or result context is sufficient to produce an accepted / passed / terminal acceptance outcome
- whether a transition should remain non-terminal despite a positive result packet

Does not own:

- workflow stage mutation
- queue routing
- repair semantics

### `ResetRecoveryPolicy`

Owns:

- whether the current state requires:
  - retry
  - blocked state
  - reset
  - manual repair
- whether stale or inconsistent runtime evidence should force a repair-oriented workflow outcome

Does not own:

- baseline legal transition routing
- acceptance success criteria
- execution-package lookup

## First Behavioral Slice

The first implementation slice should stay narrow.

### Scope

- load current workflow state for one `work_item_id`
- accept one narrow transition family:
  - role-result or QA-result driven transition
- resolve execution context only when required by the requested transition
- consult policy collaborators
- return applied vs rejected result

### Out of scope

- full hub-and-spoke orchestration
- mass repair flows
- background projection refresh
- broad GitHub lifecycle handling
- queue self-healing

## Relationship To Existing Design

This service is the modern decomposition successor to the earlier:

- `Workflow State Machine`

The important correction is:

- keep workflow truth ownership
- split volatile decision logic into explicit policies

That addresses the previously identified unresolved dependency question:

- exact internal split between `Workflow Lifecycle Service` and `WorkflowTransitionPolicy`

## Immediate Next Design Step

Before service code:

1. define `WorkflowTransitionPolicy`
2. define `AcceptancePolicy`
3. define `ResetRecoveryPolicy`

Only after that should the service contract and first behavioral slice be implemented.
