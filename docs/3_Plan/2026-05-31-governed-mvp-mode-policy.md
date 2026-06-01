Title: Governed MVP Mode Policy
Doc-ID: governed-mvp-mode-policy
Doc-Type: process-policy
Status: active
Lifecycle-Stage: plan
Created: 2026-05-31
Last-Edited: 2026-05-31
Author: Billy Weisberg
Repo: paa-platform
Component: PAAOperatorSystem
Domain: methodology-governance
Keywords: paa, governance, mvp, process, component, worker, cli, runtime
Depends-On: 2026-05-28-paa-operator-system-implementation-plan.md, 2026-05-27-component-realization-loop.md, 2026-05-30-paa-modeled-ownership-inventory.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-06-14
Summary: Defines the lightweight governance policy for building the PAA MVP without abandoning component boundaries, realization truth, or deterministic validation.

# Governed MVP Mode Policy

## Purpose

Define the minimum governance required to build the PAA MVP quickly without recreating:
- shell monoliths
- ad hoc runtime logic
- duplicated host behavior
- packet, queue, and lifecycle drift

This policy exists because the full governed build process is valuable, but applying maximum ceremony to every obvious thin slice creates operator drag.

## Core Rule

Use full governance when creating or changing shared system truth.

Use lightweight governance when wiring an already-governed truth into a host surface.

## Full-Governance Required Changes

These changes must go through the full governed component-realization loop:
- any new governed component
- any new repository boundary
- any new service boundary
- any new packet schema or result vocabulary
- any new methodology execution model or state vocabulary
- any new worker-runtime host with shared orchestration responsibility
- any change that alters ownership boundaries between Core, CLI, worker runtime, or queue runtime

Full governance means:
1. publish or revise governing design authority
2. materialize component spec when applicable
3. reconcile progress
4. derive next activity bundle
5. implement one thin slice
6. verify with focused tests and consistency checks
7. mark activity complete
8. repeat

## Lightweight-Governance Allowed Changes

These changes may use a lighter path when they do not introduce new shared truth:
- wiring an existing service into the CLI host
- adding or revising a thin command over existing services
- adding tests over an already-governed contract
- adding help text, operator docs, or README guidance for existing behavior
- adding diagnostic output fields that do not change contracts
- adding compatibility aliases that do not introduce new domain logic

Lightweight governance means:
1. confirm the governing component or service already exists
2. implement the host or test change directly
3. run focused tests and compile checks
4. commit clearly with the governing component named in the message when useful

## MVP Scope Rule

For the PAA MVP, the system is considered minimally coherent when these runtime hosts exist over shared Core units:
- `PAAOperatorCLI`
- `TechLeadWorkerService`
- `DevWorkerService`
- `QAWorkerService`

The CLI is the manual operator host.

The worker services are the automated runtime hosts.

All four must consume shared Core components instead of duplicating business logic.

## Shared-Core Rule

Every new runtime behavior should be built in this order:
1. repository or service in Core
2. DTOs and deterministic contract in Core
3. one host composition root using that Core unit
4. focused validation

Do not place new domain logic first in:
- `app.py`
- `techlead.py`
- automation prompts
- worker-host wrappers
- queue helper scripts

## Thin-Slice Rule

Every new governed component should begin with one narrow supported path only.

Examples:
- one packet type
- one transition key
- one assignment type
- one role family
- one normalized result path

A slice is too broad if it requires:
- multiple packet families at once
- cross-cutting refactors before first proof
- speculative future worker support before one real role path is stable

## Verification Rule

For MVP work, every governed slice must prove at least:
- contract tests
- DTO shape tests
- behavioral tests for the supported path
- fail-closed tests for unsupported or blocked paths
- compile checks

Consistency scripts remain required when the component spec is materialized.

## Host-Boundary Rule

The CLI and worker runtimes may compose the same Core components, but they must not become alternate domain owners.

Specifically:
- CLI owns parsing, routing, rendering, and operator UX
- worker runtimes own packet claim, dispatch orchestration, side-effect sequencing, and ack/requeue behavior
- Core owns deterministic business logic and structured state transitions

## Immediate MVP Build Order

From the current PAA state, Governed MVP Mode sets the next required governed components in this order:
1. `TechLeadWorkerService`
2. `PacketContextAssemblyService`
3. `DevWorkerService`
4. `QAWorkerService`

The CLI may continue to evolve in lightweight mode so long as it stays a thin host over those shared services.

## Stop Rule

Stop and re-author authority before coding if any slice would force a new answer to one of these questions:
1. who owns this business decision?
2. is this packet/result/state part of Core truth or host-local glue?
3. which runtime host is supposed to advance this execution state?
4. is this a new component boundary or only a new host wiring?

If the answer is unclear, the slice is not ready for lightweight mode.

## Decision

The PAA MVP should be built in Governed MVP Mode.

Do not suspend governance.

Do not use full ceremony for every host wiring change.

Use full governance for new shared components and shared truth.
Use lightweight governance for thin host integration over already-governed Core units.
