# PAA Solution Project Scaffolding Plan

Date: 2026-05-16

## Purpose

Derive the solution and project scaffolding plan from the layered component dependency graph so that code structure follows architectural dependencies instead of ad hoc file growth.

This note is the design-to-build bridge between:
- architecture selection
- dependency strata
- package/module layout
- first code scaffolding

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-authority-package-authoring-process.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-layered-architecture-proposal.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-layered-component-dependency-graph.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-repository-package-layout.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-stratum-2-service-dependency-comparison.md`

## Current Baseline

Current package roots already in place:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_producer/`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-consumer/`

Current structured scaffolding already in place:
- repository layout under:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/repositories/`

This means we are not starting from zero.
We are normalizing and extending an existing package baseline.

## Scaffolding Goal

The scaffolding should make these architectural facts visible in code layout:
- domain core is foundational
- policy contracts are upstream of domain services
- domain services are upstream of application/orchestration services
- infrastructure ports are separate from infrastructure adapters
- host surfaces are thin wrappers owned by producer or consumer packages

## Package Ownership Rules

## `paa-core`
Owns shared, topology-neutral code:
- domain models
- policy contracts and defaults
- domain services
- application service contracts and shared implementations where appropriate
- infrastructure ports
- infrastructure adapters that are not producer-only or consumer-only
- shared composition helpers

## `paa-producer`
Owns producer-side application composition and host surfaces:
- producer CLI host wiring
- future producer API host wiring
- future producer UI backend wiring
- producer-specific composition roots

## `paa-consumer`
Owns consumer-side application composition and host surfaces:
- consumer CLI host wiring
- background worker host wiring
- future consumer API host wiring
- future consumer UI backend wiring
- consumer-specific composition roots

## Standard Package Layout By Layer

## 1. Domain Core Layout

Root:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/domain/`

Each domain family package should use:
- `__init__.py`
- `models.py`

Optional later files:
- `enums.py`
- `value_objects.py`
- `rules.py`

Initial domain families:
- `core/`
- `authority_taxonomy/`

## 2. Policy Layer Layout

Root:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/policies/`

Each policy package should use:
- `__init__.py`
- `contracts.py`
- `models.py`
- `default.py`

Initial policy packages:
- `workflow_transition/`
- `routing/`
- `acceptance/`
- `reset_recovery/`
- `deployment_capability/`
- `projection_freshness/`

## 3. Domain Service Layout

Root:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/`

Each service package should use:
- `__init__.py`
- `contracts.py`
- `models.py`
- `default.py`

Initial Stratum 2 service packages:
- `component_design_planning/`
- `execution_package_resolution/`
- `workflow_lifecycle/`

Later service packages:
- `brief_assembly/`
- `verification_acceptance/`
- `work_item_coordination/`

## 4. Application / Orchestration Service Layout

Root:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/application/`

Each application-service package should use:
- `__init__.py`
- `contracts.py`
- `models.py`
- `default.py`

Initial application-service packages to create later:
- `authority_publication/`
- `techlead/`
- `role_return/`
- `projection_refresh/`
- `execution_surface_preparation/`

## 5. Infrastructure Port Layout

Existing repositories remain under:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/repositories/`

Non-repository shared port families should use dedicated roots under `paa-core`:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/message_bus/`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/execution_surfaces/`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/artifact_store/`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/git_provider/`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/runtime_support/`

Default layout for these port families:
- `__init__.py`
- `contracts.py`
- `models.py`

## 6. Infrastructure Adapter Layout

Adapters should live either:
- beside an existing repository package, or
- under the relevant shared port family root when the adapter family is not repository-shaped

Examples:
- repository adapters:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/repositories/<name>/postgres.py`
- message bus adapters:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/message_bus/rabbitmq.py`
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/message_bus/sqs.py`
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/message_bus/service_bus.py`
- execution surface adapters:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/execution_surfaces/local_worktree.py`
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/execution_surfaces/efs.py`
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/execution_surfaces/azure_files.py`

## 7. Host Surface Layout

Producer-side host roots:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_producer/hosts/`

Consumer-side host roots:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-consumer/src/paa_consumer/hosts/`

Suggested host family packages:
- `cli/`
- `worker/`
- `api/`
- `ui_backend/`

Each host family package should use:
- `__init__.py`
- `bootstrap.py`
- `composition.py`

Optional later files:
- `routes.py`
- `jobs.py`
- `commands.py`

## Composition Root Rule

Composition roots should not live in domain services.

Composition belongs in host or application wiring layers, typically under:
- `paa-producer.hosts.*`
- `paa-consumer.hosts.*`
- or shared bootstrap helpers under `paa_core.runtime_support`

## Scaffolding By Dependency Strata

## Stratum 0. Foundation scaffolding

Must exist first:
- `paa_core.domain.core`
- `paa_core.domain.authority_taxonomy`

Reason:
These name the semantic backbone used by all upstream layers.

## Stratum 1. Port and policy scaffolding

Should exist next:
- policy package roots
- shared non-repository port family roots
- repository package roots as needed
- runtime support roots for transaction/logging/clock/config contracts

Reason:
These are upstream dependencies for the first buildable domain services.

## Stratum 2. Earliest domain-service scaffolding

Should exist after Stratum 1:
- `component_design_planning`
- `execution_package_resolution`
- `workflow_lifecycle`

Reason:
These are the earliest graph-buildable domain services.

## Stratum 3+. Later scaffolding

Can follow when their dependencies are more mature:
- higher-level domain services
- application/orchestration services
- host-specific families

## First Scaffolding Cut To Create Now

Based on the graph, the first code scaffolding cut should create:

1. domain foundations
- `paa_core.domain.core`
- `paa_core.domain.authority_taxonomy`

2. policy roots
- all six initial policy package roots

3. shared non-repository port roots
- `message_bus`
- `execution_surfaces`
- `artifact_store`
- `git_provider`
- `runtime_support`

4. Stratum 2 service roots
- `component_design_planning`
- `execution_package_resolution`
- `workflow_lifecycle`

5. host roots only, not full host implementations yet
- `paa_producer.hosts`
- `paa_consumer.hosts`

This gives the codebase visible structure for the next dependency strata without pretending later components are already implemented.

## What This Plan Does Not Do Yet

This scaffolding plan does not:
- fully implement the services
- define every DTO or value object
- create every future host package
- replace current runtime scripts immediately

It only creates the correct structural landing zones for the next build sequence.

## Design Conclusion

The solution/project scaffolding should be derived from the dependency graph.

That means:
- shared domain, policy, service, and port code belongs in `paa-core`
- producer and consumer hosts belong in `paa-producer` and `paa-consumer`
- scaffolding should appear in dependency-strata order
- the first scaffold cut should make Strata 0, 1, and the first Stratum 2 services visible in code
