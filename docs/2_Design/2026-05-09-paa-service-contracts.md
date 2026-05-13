# PAA Service Contracts

## Purpose

Primary consolidated handoff reference:
- `docs/2_Design/2026-05-12-paa-handoff-execution-contract.md`

Document the primary service contracts between major PAA runtime components.

This note focuses on behavior, not just stored data.
A service contract here means:
- what a component provides
- what inputs it expects
- what outputs or side effects it guarantees
- what assumptions or hard-coded limits exist today

## Service Boundaries

PAA currently has six meaningful service boundaries:

1. authority publishing
2. packet compilation and validation
3. queue transport
4. TechLead control and routing
5. role execution bridge
6. lifecycle / lineage mutation

## 1. Authority Publishing Contract

### Provider
- `paa-producer runtime`

### Consumers
- producer-side automations
- `Authority Architect`
- downstream consumer-side packet compilers and validators

### Inputs
- authority manifest
- design package
- coder brief
- issue / PR / branch context
- selected packet family and packet-specific arguments

### Outputs
- valid packet JSON
- optional review artifact markdown
- optional DB persistence record for packet compilation
- optional queue send to RabbitMQ

### Guarantees
- packet envelope is populated
- payload-required fields are validated by schema family
- route-policy validation is enforced before send
- packet compilation can be persisted in PAA DB

### Current limits
- packet compiler agent names are still mapped by fixed schema name
- worker-role normalization is still code-mapped, not discovered dynamically

## 2. Packet Validation Contract

### Provider
- `paa-core.handoff_runtime`

### Consumers
- producer runtime
- consumer runtime
- queue admin / validation commands

### Inputs
- packet JSON
- schema type
- route pair

### Outputs
- pass / fail validation result
- error details

### Guarantees
- schema type must be supported
- envelope fields must exist
- required payload fields must exist
- `from_role` and `to_role` must match allowed route policy for that schema

### Current limits
- supported route pairs are hard-coded tuples
- supported queue list is fixed
- role normalization is hard-coded

## 3. Queue Transport Contract

### Provider
- RabbitMQ plus PAA queue-state helpers

### Consumers
- producer packet senders
- TechLead runtime
- role automations
- queue admin commands

### Inputs
- exchange name
- queue name
- validated packet payload

### Outputs
- queued message
- claim / ack lifecycle
- queue preview visibility
- persisted queue-message record in PAA DB through runtime helpers

### Guarantees
- message send can be previewed and later claimed / acknowledged
- queue-message persistence is correlated to message id and work item when possible

### Current limits
- queue topology is static:
  - `fractal-core-architecture`
  - `fractal-core-python`
  - `fractal-core-qa`
- broader worker roles are not yet data-bound to queue policy

## 4. TechLead Control Contract

### Provider
- `paa-consumer techlead` runtime surface

### Consumers
- TechLead automation
- operator / developer CLI usage
- downstream spoke-role helpers

### Inputs
- current queue state
- issue / PR / branch lineage
- packet history
- role-specific target selection
- authority/design/brief context

### Outputs
- assignment packets
- decision packets
- lineage reports
- role entry contexts
- worktree preparation results
- lifecycle cleanup results
- preflight gate decisions

### Guarantees
- spoke routing is hub-owned
- all result packets return to `TechLead`
- lineage precedes branch/worktree mutation
- cleanup fails closed if lifecycle state is ineligible or ambiguous

### Current limits
- many commands still enumerate allowed target roles in CLI choices
- some lifecycle flows are still `python-team` only
- worker-family role discovery is not data-driven

## 5. Role Execution Bridge Contract

### Provider
- `paa-consumer` role bridge helpers

### Consumers
- role automations
- human-supervised role execution

### Inputs
- package id
- brief id
- target role
- lineage context
- assignment artifact
- optional branch / worktree overrides

### Outputs
- prepared role branch
- prepared or reused role worktree
- inspected role context
- role entry guidance
- result assist guidance
- role return compile/send surface

### Guarantees
- roles can operate within a bounded worktree context
- result packet family is constrained by target role
- queue-selection reasoning is hidden behind the runtime surface

### Current limits
- target roles are still enumerated in CLI and helper logic
- Python is still the only fully proven implementation worker lane
- worktree suffix mapping is still hard-coded

## 6. Lifecycle And Lineage Contract

### Provider
- TechLead lineage and cleanup helpers

### Consumers
- TechLead automation
- operators
- future automation cleanup flows

### Inputs
- issue / PR / branch state
- lineage metadata from packets
- role branch and worktree state
- target role

### Outputs
- lineage view
- ownership view
- staleness view
- reset-required lifecycle result
- physical reset cleanup result
- superseded cleanup result
- closed cleanup result

### Guarantees
- no physical cleanup occurs without a queryable lineage precursor
- cleanup preserves evidence and branch lineage according to the phase rules
- ineligible live states fail closed

### Current limits
- cleanup support is still narrow and role-specific in places
- lifecycle mutation paths remain specialized around the current proven role set

## 7. Automation Launch Contract

### Provider
- app-visible automation registration plus installed skills/prompts

### Consumers
- Codex app automation runner
- scheduled automation polling
- human operators launching automations in the UI

### Inputs
- automation registration
- launch cwd
- repo-local runtime wrappers
- installed skills
- no-work preflight result

### Outputs
- model invocation only when work exists
- correct role prompt and execution path
- correct repo root / worktree transition behavior

### Guarantees
- automation may skip model invocation when preflight says there is no work
- active automation should launch from repo-local runtime truth, not deprecated home-folder skills

### Current limits
- home-level UI registrations are still under-configured
- role-to-automation mapping is still name-bound, not data-bound
- dynamic worker-role bootstrap is not yet defined

## Service-Contract Summary

### Good news
The core PAA service boundaries already exist.
We are not inventing a system from zero.

### Main architectural problem
The service boundaries are real, but many of them still consume:
- fixed role names
- fixed branch suffixes
- fixed queue assumptions
- fixed automation names

That is why Dynamic Worker Roles needs a real design spec.
The DB can store dynamic roles, but the services do not yet derive behavior from dynamic role definitions.
