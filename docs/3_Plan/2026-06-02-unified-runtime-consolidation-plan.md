Title: Unified Runtime Consolidation Plan
Doc-ID: paa-unified-runtime-consolidation-plan
Doc-Type: plan
Status: active
Lifecycle-Stage: plan
Created: 2026-06-02
Last-Edited: 2026-06-02
Author: Billy Weisberg
Repo: paa-platform
Component: UnifiedRuntimeConsolidation
Domain: runtime-architecture
Keywords: paa, runtime, cli, object-oriented, consolidation, techlead, queue, supervisor
Depends-On: 2026-05-28-paa-cli-system-architecture.md, 2026-05-28-paa-worker-runtime-architecture.md, 2026-05-30-paa-operator-cli-component-spec.md, 2026-05-30-paa-cli-command-inventory-and-migration-map.md, 2026-05-18-p0-techlead-runtime-extraction-plan.md, 2026-05-27-techlead-final-extraction-sequence-plan.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-06-16
Owners:
Expires:
Issue:
PR:
Authority-Source:
Implementation-Status: active execution
Summary: Defines the hard removal order and architectural constraints for collapsing the remaining compatibility layers into one coherent object-oriented PAA runtime and operator system.

# Unified Runtime Consolidation Plan

## Status
Active.

## Purpose

This plan exists to prevent further drift while the remaining hybrid runtime surfaces are removed.

The goal is simple:
- one user-facing CLI
- one runtime bootstrap path
- one coherent object-oriented system shape
- no parallel command surfaces
- no wrapper layers masquerading as architecture

This plan is the durable reminder for future execution turns.

## Target End State

The target system is:

1. `paa` is the only user-facing CLI
2. `paa_core` owns:
   - queue transport
   - claim state
   - runtime guardrails
   - runtime install/bootstrap services
   - packet transport/admin services
   - runtime control abstractions
3. runtime hosts are composed through typed interfaces, not helper shims
4. `paa_consumer` is an internal package boundary only if still needed for host implementations
5. `techlead.py` is not part of the active operator/runtime path
6. queue/runtime/ops behavior is exposed through modeled services and repositories, not command wrappers

## Hard Constraints

These are execution constraints, not suggestions.

### Constraint 1. No new user-facing CLI outside `paa`

Do not create:
- another command root
- another control script as a primary surface
- another forwarding shell as a “temporary” convenience

### Constraint 2. No new forwarding layer unless it is removed in the same slice

Do not add:
- new compatibility shims
- new adapter trampolines
- new wrapper commands

If a bridge is unavoidable, it must be scheduled for removal immediately and should not survive beyond the slice that introduced it.

### Constraint 3. No new `paa_consumer` command ownership

`paa_consumer` must not regain ownership of:
- runtime control
- queue admin
- operator workflows
- packet validation/sending as user-facing commands

### Constraint 4. No new active dependency on `techlead.py`

If active runtime behavior still depends on `techlead.py`, the work must be extraction/removal work, not expansion.

### Constraint 5. Typed services over utility wrappers

Behavior should move toward:
- repositories
- services
- typed host objects
- explicit composition

Behavior should move away from:
- shell-style wrappers
- module-level helper sprawl
- command-oriented utility trampolines

## Current Remaining Hybrid Surfaces

The remaining compatibility/hybrid zones are:

1. `paa_cli -> paa_consumer` internal delegation
2. `paa_consumer.inbox -> handoff_runtime.main(...)` queue wrapper path
3. runtime supervisor control still implemented in internal consumer modules
4. runtime host builders still sourced through internal consumer package boundaries
5. active `techlead.py` dependency for `automation-preflight`
6. consumer-named install/config/guardrail APIs
7. legacy DB compatibility profiles and related operational residue

## Consolidation Order

The order matters.

### Phase 1. Queue and packet transport consolidation

Goal:
- remove `paa_cli -> paa_consumer.inbox -> handoff_runtime` as the active queue path

Required outcome:
- `paa_cli` queue commands call typed runtime services or repositories directly
- queue admin and packet send/validate/claim/ack/requeue are owned by coherent service objects
- `handoff_runtime.py` becomes internal compatibility code only, then removable from active paths

Primary targets:
- `packages/paa-cli/src/paa_cli/app.py`
- `packages/paa-consumer/src/paa_consumer/inbox.py`
- `packages/paa-core/src/paa_core/handoff_runtime.py`
- queue transport and claim-ledger modules under `packages/paa-core/src/paa_core/`

### Phase 2. Runtime supervisor and host composition consolidation

Goal:
- remove `paa_cli` helper-level delegation into consumer runtime control wrappers

Required outcome:
- runtime supervisor control lives behind typed runtime services
- runtime host builders are composed through explicit interfaces
- `paa_cli` no longer needs `_consumer_hosts_module()` or `_runtime_supervisor_control_module()`

Primary targets:
- `packages/paa-cli/src/paa_cli/app.py`
- `packages/paa-consumer/src/paa_consumer/runtime_supervisor_control.py`
- `packages/paa-consumer/src/paa_consumer/hosts/`
- new or extracted runtime control abstractions in `packages/paa-core/src/paa_core/`

### Phase 3. Remove active `techlead.py` dependency

Goal:
- stop using `techlead.py` for active operator/runtime flows

Start with:
- `automation-preflight`

Required outcome:
- preflight behavior is owned by modeled service(s)
- `paa ops automation-preflight` no longer dispatches into `techlead.py`
- legacy TechLead shell code is no longer on the active path

Primary targets:
- `packages/paa-consumer/src/paa_consumer/techlead.py`
- preflight and TechLead service extractions in `packages/paa-core/src/paa_core/services/`

### Phase 4. Rename neutral runtime/system APIs

Goal:
- stop encoding historical “consumer” naming into system-level APIs

Required outcome:
- neutral names for install, guardrail, config, and runtime helpers
- old names removed or confined to short-lived compatibility aliases during refactor only

Examples:
- `install_consumer_runtime(...)`
- `validate_consumer_runtime(...)`
- `load_consumer_project_config(...)`
- `repo_consumer_bin(...)`

### Phase 5. Retire residual compatibility artifacts

Goal:
- remove the leftovers after active-path consolidation is done

Includes:
- deprecated `paa_consumer` module stub if no longer needed
- legacy DB profile assumptions where safe
- stale docs that still describe split command ownership
- internal historical wrappers that are no longer used

## Anti-Goals

Do not do these things while executing this plan:

1. build another CLI surface
2. add more wrapper scripts as primary operations
3. re-expand `techlead.py`
4. add convenience shims that preserve old command habits
5. keep old names indefinitely “for compatibility”
6. accept a result that still requires two mental models for one runtime

## Validation Rule

Each phase is complete only when:

1. the user-facing `paa` path works
2. the replaced compatibility layer is no longer on the active path
3. focused tests pass
4. the live queue/runtime proof still works
5. docs and command guidance reflect the new truth

## Final Proof Condition

This plan is complete only when all of the following are true:

1. `paa` alone can:
   - bootstrap runtime
   - ensure queue topology
   - start/stop/status/log supervisor
   - validate/send/claim/ack/requeue packets
   - run runtime hosts
2. active runtime/queue/operator behavior no longer depends on:
   - `paa_consumer` as a CLI
   - `paa_consumer.inbox` wrappers
   - `handoff_runtime.main(...)` on the main operator path
   - `techlead.py`
3. the system shape is explainable as:
   - host CLI
   - typed services
   - repositories
   - runtime hosts
   - transport/state infrastructure

## Immediate Next Step

Start with Phase 1:
- replace the active `paa_cli -> paa_consumer.inbox -> handoff_runtime` queue path with direct typed runtime services in `paa_core`

That is the first mandatory cut because it removes a real wrapper layer from the canonical operator path.
