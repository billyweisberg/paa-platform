# 113. PAA Platform Repo Design

Date: 2026-05-03

## Purpose

This document defines the proposed `PAA platform repo` as a standalone software product.

Its job is to provide:

- installable producer tooling
- installable consumer/runtime tooling
- a consistent authority publication contract
- a consistent runtime resolver and packet/queue contract

It is not a Fractal Core source repo and not a Fractal Core implementation repo.

## Repo identity

Working name:
- `paa-platform`

Role:
- source of truth for shared PAA software

Consumers:
- authority producer repos such as:
  - `/Users/billyweisberg/Repos/Individual-Centricity/appdev`
- project consumer repos such as:
  - `billyweisberg/fractal-core-python`

## Product boundaries

### In scope

- authority package publication engine
- authority package install/update engine
- queue and claim runtime
- packet schemas and validators
- packet compilers
- runtime resolver
- PAA DB tooling and migrations
- reporting/status tools
- producer and consumer installation logic
- shared automation templates
- shared project-local skills and wrappers

### Out of scope

- product-specific authority content
- product-specific source diagrams and requirements
- implementation code for consumer repos
- product-specific GitHub issue bodies except through data-driven templates

## Target repo structure

```text
paa-platform/
  README.md
  docs/
    architecture/
    install/
    operations/
  packages/
    paa-core/
    paa-producer/
    paa-consumer/
  schemas/
    authority-package/
    handoff-packets/
    runtime-records/
  scripts/
    install/
    publish/
    runtime/
    db/
  templates/
    automations/
    skills/
    configs/
  migrations/
  tests/
    unit/
    integration/
    contract/
```

## Package model

### `paa-core`

Shared foundation used by both producer and consumer installs.

Contains:
- common schema helpers
- shared file/path utilities
- config loader
- package metadata reader
- logging / diagnostics helpers

### `paa-producer`

Installed into source-authority repos.

Contains:
- authority manifest validation
- dependency graph derivation
- Stage 1 design package derivation
- coder brief derivation
- publication tooling
- producer-side reporting commands

### `paa-consumer`

Installed into execution repos.

Contains:
- authority package installer/updater
- queue/claim runtime
- packet compilers and validators
- runtime resolver
- Dev / QA / Architect support commands
- runtime reporting/status commands

## Command surface

### Producer-side commands

Examples:
- `paa producer validate-authority`
- `paa producer derive-dependency-graph`
- `paa producer derive-stage1-packages`
- `paa producer derive-coder-briefs`
- `paa producer publish-authority-package`

These commands operate only on the producer repo’s source inputs.

### Consumer-side commands

Examples:
- `paa consumer install-authority-package`
- `paa runtime resolve-active-state`
- `paa runtime check-queue`
- `paa runtime claim`
- `paa runtime ack`
- `paa runtime materialize-slice-result-packet`
- `paa runtime materialize-qa-verification-packet`
- `paa runtime materialize-architect-cycle-packet`
- `paa runtime techlead-status`

These commands operate only on the consumer repo’s runtime and the installed authority package.

## Runtime resolver contract

One of the key jobs of the platform repo is to provide a shared resolver that answers:

- active authority task
- explicit design package id
- explicit coder brief id
- authoritative runtime readiness
- unresolved predecessor follow-through state
- open queue/claim state
- next required role action

That command should replace a large amount of prompt-level branching logic.

## Platform config contract

The platform repo should support a small project-local config file in both producer and consumer repos.

Example conceptual path:
- `.codex/paa/project-config.json`

Producer config should declare:
- project id
- authority source manifest path
- supporting docs paths
- publication output root
- derivation inputs

Consumer config should declare:
- project id
- authority package install root
- runtime data root
- queue names
- GitHub repo name
- runtime DB settings or connection profile name

## Install modes

### Producer install mode

Installed into:
- `.codex/paa/`

Expected contents:
- producer commands
- producer templates
- schemas needed for publication

### Consumer install mode

Installed into:
- `.codex/paa/`

Expected contents:
- runtime commands
- packet compilers
- queue/claim runtime
- consumer automation templates

## Versioning

The platform repo must version:
- installable PAA runtime
- authority package format version
- packet schema versions

The platform version and authority package version should be related but independent.

That means:
- PAA platform can upgrade without changing every authority version
- authority packages can roll forward without forcing a new platform runtime every time

## Testing strategy

### Unit tests

Cover:
- schema validation
- config parsing
- package metadata handling
- runtime resolver state classification

### Integration tests

Cover:
- producer publication flow
- consumer installation flow
- queue claim/ack flow
- packet compilation flow

### Contract tests

Cover:
- authority package installability
- packet schema compatibility
- terminal-task completion flow
- re-verification / re-presentation routing

## Non-negotiable invariants

1. role runs do not patch platform code in flight
2. consumer repos do not depend on home-folder project runtime state
3. authority package identity is explicit, versioned, and installable
4. active task package/brief identity is explicit, not inferred
5. terminal completion is a first-class supported lifecycle path
6. stale verification recovery is a first-class supported lifecycle path

## First platform milestones

### M1. Extract publication and runtime foundations

Move into `paa-platform`:
- authority publication logic
- packet compilation logic
- queue/claim runtime
- shared schemas

### M2. Install contract

Deliver:
- producer installer
- consumer installer
- project-local config contract

### M3. Runtime resolver

Deliver:
- one authoritative next-action resolver

### M4. Re-verification routing

Deliver:
- machine-detectable stale-verification / re-presentation flow

### M5. Reporting and operator surfaces

Deliver:
- runtime status report
- blocked-state explanation
- next-role recommendation

## Recommended next document

The next document should define:
- the install contract
- the authority package format
- the first extraction wave from current repos and home-folder state

That becomes the execution plan for actually moving into this model.
