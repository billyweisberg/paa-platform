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

## Current documentation map

### Design
- `docs/2_Design/2026-05-03-paa-platform-repo-design.md`
- `docs/2_Design/2026-05-03-paa-install-contract-and-extraction-plan.md`
- `docs/2_Design/2026-05-03-paa-staged-lifecycle.md`
- `docs/2_Design/2026-05-03-authority-architect-vs-delivery-architect.md`
- `docs/2_Design/2026-05-03-coder-run-brief.md`
- `docs/2_Design/2026-05-03-coder-run-brief-packet-integration.md`
- `docs/2_Design/2026-05-03-coder-brief-derivation-method.md`
- `docs/2_Design/2026-05-03-coder-brief-field-derivation-matrix.md`
- `docs/2_Design/2026-05-03-stage1-design-package-contract.md`
- `docs/2_Design/2026-05-03-component-dependency-graph-contract.md`
- `docs/2_Design/2026-05-03-stage1-schema-and-record-shape.md`
- `docs/2_Design/2026-05-03-coder-brief-sequencing.md`

### Planning
- `docs/3_Plan/2026-05-03-paa-platform-inventory-matrix.md`

### Build
- `docs/4_Build/2026-05-03-coder-brief-readiness-materializer.md`
- `docs/4_Build/2026-05-03-paa-backed-architect-packet-brief-resolution.md`
- `docs/4_Build/2026-05-03-architect-packet-compiler.md`
- `docs/4_Build/2026-05-03-dev-and-qa-packet-compilers.md`

### Deploy
- `docs/6_Deploy/install-readme.md`
- `docs/6_Deploy/producer-publication.md`
- `docs/6_Deploy/2026-05-03-packet-compilation-persistence.md`
- `docs/6_Deploy/2026-05-03-compiled-packet-transport-trace.md`

### Monitor
- `docs/7_Monitor/2026-05-03-techlead-traceability-reporting.md`

## Current implementation status

Implemented now:
- initial `paa-core`, `paa-producer`, and `paa-consumer` package scaffolds
- config-driven authority publication
- producer runtime install/update command
- consumer runtime install/update command
- consumer authority-package install command
- first formal platform inventory matrix

Still to extract or formalize:
- readiness materializer runtime
- packet compiler runtime
- queue/claim runtime
- TechLead reporting runtime
- project-local automation and skill install/update flows
- stale-workspace startup validation
