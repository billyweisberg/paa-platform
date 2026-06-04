Title: Execution Package Resolution Service Validation
Doc-ID: paa-execution-package-resolution-service-validation
Doc-Type: validation-note
Status: active
Lifecycle-Stage: test
Created: 2026-05-18
Last-Edited: 2026-05-19
Author: Billy Weisberg
Repo: paa-platform
Component: ExecutionPackageResolutionService
Domain: execution-package-resolution
Keywords: validation, execution-package, runtime, service, consumer
Depends-On: 2026-05-17-execution-package-resolution-service-component-spec.md
Supersedes: 
Superseded-By: 
Canonical: true
Review-After: 2026-06-15
Owners: 
Expires: 
Issue: 
PR: 
Authority-Source: code
Implementation-Status: 
Summary: Validates repository, policy, and downstream-consumer alignment for the execution package resolution service.

# Execution Package Resolution Service Validation

Date: 2026-05-17
Status: passed

## Purpose

Validate execution-context bridge alignment across:
- repository rows
- capability-policy inputs
- service outputs

Then confirm one real downstream consumer path now uses the service instead of direct manifest-path guessing.

## Fixture Used

Validation used the real self-hosted authority install already present on disk under:

- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/.project/data/paa/authority/current/`

The fixture was registered in the local PAA-owned Postgres DB as:

- install id: `84a21cc7-f6e2-4fff-a00e-eb0b461b89da`
- execution surface key: `repo:paa-platform:self-hosted-proof`
- project id: `414927ef-6834-4434-9ebf-74bd69582aee`
- authority version id: `572cd77f-2d39-4044-9c70-09dd8b28dfcb`

The active overlay was registered as:

- overlay id: `71845d47-eb22-4e30-ab3a-ccf37438a891`
- overlay key: `task-brief-overlay`
- work item id: `f1dfc44f-8d70-418f-80eb-7b33fc8dea11`

## Repository Alignment

Repository reads resolved the expected active install row by:

- repo root
- runtime root
- execution surface key

Resolved install fields:

- `execution_surface_type = consumer_repo_runtime`
- `repo_root_path = /Users/billyweisberg/Repos/billyweisberg/paa-platform`
- `runtime_root_path = /Users/billyweisberg/Repos/billyweisberg/paa-platform/.project/data/paa`
- `installed_manifest_path = /Users/billyweisberg/Repos/billyweisberg/paa-platform/.project/data/paa/authority/current/authority/paa-platform-authority.json`
- `installed_package_metadata_path = /Users/billyweisberg/Repos/billyweisberg/paa-platform/.project/data/paa/authority/current/package-metadata.json`

Resolved active overlay fields:

- `overlay_key = task-brief-overlay`
- `overlay_type = task_override`
- `overlay_manifest_task_path = /Users/billyweisberg/Repos/billyweisberg/paa-platform/.project/data/paa/authority/current/overlays/task-brief-overlay/manifest-task.json`

## Policy Alignment

Capability-policy inputs were validated with:

- required artifact refs:
  - `installed_manifest`
  - `package_metadata`
- required overlay keys:
  - `task-brief-overlay`

The policy decision returned:

- `allowed = true`
- satisfied capabilities:
  - `active_install`
  - `artifact:installed_manifest`
  - `artifact:package_metadata`
  - `overlay:task-brief-overlay`
- missing capabilities:
  - none
- blocking reasons:
  - none

## Service Output Alignment

`DefaultExecutionPackageResolutionService` returned a normalized `ExecutionPackageResolutionView` for:

- `resolve_execution_context_for_repo_root(...)`
- `resolve_execution_context_for_runtime_root(...)`
- `resolve_execution_context_for_surface(...)`

The normalized view consistently returned:

- install id `84a21cc7-f6e2-4fff-a00e-eb0b461b89da`
- package name `paa-platform-authority`
- package version `2026-05-16.1`
- authority version id `572cd77f-2d39-4044-9c70-09dd8b28dfcb`
- active overlay keys:
  - `task-brief-overlay`
- manifest path:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/.project/data/paa/authority/current/authority/paa-platform-authority.json`
- package metadata path:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/.project/data/paa/authority/current/package-metadata.json`
- `gaps = ()`
- `warnings = ()`

## Downstream Consumer Integration

The first real consumer-path integration was added in:

- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services`

`repo_auth_current(...)` now:

1. tries to resolve installed authority manifest location through `Execution Package Resolution Service`
2. requires the `installed_manifest` artifact surface
3. falls back to direct filesystem manifest discovery if execution-context resolution is unavailable

This is the correct narrow first integration because TechLead is a real consumer-side runtime path that previously depended on direct manifest-path guessing.

## Decision

`GO`

Validated alignment now exists from:

- execution-package repository truth
- through deployment-capability policy evaluation
- through normalized resolution-service output
- into one real downstream consumer path

## Remaining Follow-On

This does not yet prove every runtime consumer has migrated.

Follow-on work should move the same service-backed lookup into other remaining direct manifest consumers, especially:

- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_producer/authority_runtime.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/runtime_guardrails.py`
