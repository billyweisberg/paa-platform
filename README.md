# PAA Platform

`paa-platform` is the shared control-plane and automation platform for project authority authoring, publication, runtime routing, packet compilation, and queue/claim execution.

It is designed to separate three concerns that had become too entangled:

- the PAA platform itself
- the authority-producing source repo
- the consuming implementation repo

The default operating model uses separate producer and consumer repos, but the platform must also support a unified topology where one repo acts as both the authority producer and the runtime consumer.

## Purpose

This repo is the source of truth for shared PAA software.

It is expected to provide:

- producer-side tooling for authority publication
- consumer-side tooling for runtime execution
- shared queue/claim runtime
- packet schemas and validators
- packet compilers
- runtime resolver and reporting tools
- installer/update tooling for producer and consumer repos

It is not intended to hold:

- product-specific source authority content
- product-specific implementation code
- long-lived mutable runtime state for consuming repos

## Target model

The working three-repo model is:

1. `paa-platform`
   - shared control-plane product
2. authority producer repo
   - source requirements, source authority, source planning artifacts
3. consumer repo
   - implementation + installed PAA runtime + installed authority package

The platform must also support a greenfield or tightly-coupled variant:

4. unified producer-consumer repo
   - source authority + implementation + installed PAA runtime in one repo

## Initial layout

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

## First milestones

1. define the platform repo itself
2. define the install contract and authority package format
3. extract publication/runtime tooling out of source repos and home-folder state without changing behavior first

## Current source architecture docs

The initial architecture lives in:

- `docs/architecture/113-paa-platform-repo-design.md`
- `docs/architecture/114-paa-install-contract-and-extraction-plan.md`

## Status

This repo is currently a skeleton and architecture baseline. The first implementation slice should move shared publication and runtime tool surfaces here without changing external behavior yet.
