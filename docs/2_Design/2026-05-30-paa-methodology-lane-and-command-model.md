Title: PAA Methodology Lane And Command Model
Doc-ID: paa-methodology-lane-and-command-model
Doc-Type: design-note
Status: active
Lifecycle-Stage: design
Created: 2026-05-30
Last-Edited: 2026-05-30
Author: Billy Weisberg
Repo: paa-platform
Component: PAAOperatorCLI
Domain: operator-cli
Keywords: paa, methodology, lane, command, cli, preflight, command-family
Depends-On: 2026-05-30-paa-methodology-execution-state-model.md, 2026-05-28-paa-cli-system-architecture.md, 2026-05-30-paa-cli-command-inventory-and-migration-map.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-06-30
Summary: Defines how PAA CLI command families map directly to methodology lanes, current-step truth, and command preflight so operators do not have to infer the active process lane manually.

# PAA Methodology Lane And Command Model

## Purpose

Define the command model that removes lane ambiguity from the operator experience.

This note exists because the operator should not need to remember whether a command belongs to:
- producer-side authority derivation
- code-backed component realization
- runtime execution
- acceptance and closeout

The system should make that explicit.

## Core Decision

PAA CLI command families should map directly to methodology lanes and current-step truth.

Command preflight should use persisted `MethodologyExecution` state to:
- confirm the active lane
- confirm the current step
- allow, warn, or reject the requested command
- explain why a command is or is not valid now

## Lane To Command Family Mapping

### `authority_derivation`

Primary command families:
- `paa authority`
- `paa package`
- `paa readiness`
- `paa brief`
- `paa packet`

Canonical command intent:
- inspect authority
- derive design package
- evaluate derivation readiness
- derive implementation plan from Stage 1 package
- assemble and review coder brief artifacts
- prepare execution packets

### `component_realization`

Primary command family:
- `paa component`

Canonical command intent:
- materialize a governed component spec
- inspect plan progress
- reconcile progress
- derive the next activity bundle
- complete one implementation activity
- inspect verification obligations for the component slice

### `runtime_execution`

Primary command families:
- `paa worker`
- `paa queue`

Canonical command intent:
- inspect or consume queue work
- run one bounded worker invocation
- inspect normalized worker results
- replay or dry-run runtime work

### `acceptance_closeout`

Primary command families:
- `paa verify`
- `paa accept`
- `paa report`

Canonical command intent:
- evaluate proving surfaces
- inspect verification outcomes
- accept or reject work
- finalize and report terminal progress

### Cross-lane family

`paa ops`
- environment and repair operations that may support any lane
- still subject to safety preflight where the operation mutates active state

## Why Separate Families Matter

A single `paa derive` family is too ambiguous once the system supports both:
- Stage 1 producer-side derivation
- component realization successor derivation

Separate families reduce operator memory load and make the active lane explicit in the command grammar itself.

## Command Preflight Model

Every mutating command should run preflight against `MethodologyExecution` truth.

Preflight should answer:
- what lane is active?
- what stage is active?
- what step is active?
- does this command belong to that lane?
- is the requested transition allowed from the current step?
- what blocking record or prerequisite is missing if not?

## Preflight Outcomes

### `allowed`
The requested command matches the current lane and current-step transition rules.

### `warn`
The command is safe but unusual for the current step, and the system should explain why.

### `blocked`
The command should not run because:
- required predecessor step is missing
- wrong lane is active
- the current state is blocked or terminal
- the linked authority record is missing

### `redirect`
The command is not the best next move, and the system should point to the expected family and step instead.

## Example Preflight Rules

### Rule: `paa component next`
Allowed only when:
- active lane = `component_realization`
- an `implementation_plan_id` is bound
- the component spec is already materialized

Blocked when:
- there is no materialized plan root
- a predecessor activity is incomplete

### Rule: `paa brief assemble`
Allowed only when:
- active lane = `authority_derivation`
- stage = `implementation_plan_derivation` or later
- derivation readiness = `derivation_ready`

Blocked when:
- readiness has not been evaluated
- readiness is not `derivation_ready`

### Rule: `paa worker run`
Allowed only when:
- active lane = `runtime_execution`
- a queue packet or bounded worker request exists

Blocked when:
- no runnable worker request is bound
- the execution thread is still in producer-side derivation or component realization

## Initial Command Family Shape

### `paa authority`
- inspect
- sync-current
- lint
- snapshot
- diff

### `paa package`
- derive
- inspect

### `paa readiness`
- evaluate
- inspect

### `paa brief`
- assemble
- targets
- review
- inspect

### `paa packet`
- prepare
- inspect

### `paa component`
- materialize
- progress
- reconcile
- next
- complete
- inspect

### `paa worker`
- run
- dry-run
- inspect
- replay

### `paa queue`
- inspect
- preview
- claim
- ack
- resend

### `paa verify`
- run
- inspect

### `paa accept`
- review
- accept
- reject
- close

### `paa report`
- status
- next
- explain
- progress

### `paa ops`
- diagnose
- reconcile
- repair

## Operator-Facing Pointer Commands

The command model should eventually expose the methodology pointer directly:
- `paa status`
- `paa next`
- `paa explain`

These should read from the `MethodologyExecutionProjection` rather than forcing the operator to infer the current step manually.

## Transitional Rule

Until the methodology execution model is implemented, the CLI may still bridge from:
- implementation-plan progress
- derivation-readiness state
- workflow state
- queue/runtime evidence

But that bridging should be understood as transitional logic, not the final operator architecture.

## Success Condition

This model is successful when:
- command-family selection itself tells the operator which methodology lane is active
- preflight can block wrong-lane commands before mutation happens
- future `paa status` and `paa next` can be generated from persisted methodology-execution truth
