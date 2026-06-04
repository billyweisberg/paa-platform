# Component Design Planning Service Implementation Plan

Date: 2026-05-17

## Purpose

Turn the approved `Component Design Planning Service` component spec into a build-ready implementation sequence.

This plan exists to keep the first Stratum 2 domain-service implementation narrow, dependency-graph-driven, and aligned to the validated PAA derivation path.

## Design Authority

Use these notes as authority for this implementation plan:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-component-design-planning-service-component-spec.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-component-design-planning-service-pre-spec.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-layered-component-dependency-graph.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-stratum-2-service-dependency-comparison.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-component-design-repository-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-16-paa-derivation-remediation-backlog.md`

## Implementation Goal

Deliver the first concrete Stratum 2 domain service in `paa-core`:
- a real `ComponentDesignPlanningService` interface
- a default implementation that interprets structured component-design records into planning DTOs
- dedicated unit coverage that proves the service stays inside its intended domain-service boundary

The first implementation slice must support:
- component planning by component identity or name
- element-level planning views
- realization-option planning views
- brief-planning payload construction
- explicit design-gap detection

## Current Code Targets

The current scaffold already exists and should be filled in rather than replaced:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/component_design_planning/contracts.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/component_design_planning/models.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/component_design_planning/default.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/component_design_planning/__init__.py`

Dedicated test target:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/tests/unit/test_component_design_planning_service.py`

## Dependency Preconditions

This service may proceed now because its upstream dependencies are already mature enough:
- `Authority Taxonomy Model`
- `ComponentDesignRepository`
- `StructuredLogger`

This service must not expand its dependency surface in the first slice to include:
- `WorkflowStateRepository`
- `RuntimeEventRepository`
- `ExecutionPackageRepository`
- `MessageBus`
- `GitProvider`

If implementation pressure creates a need for those collaborators, stop and revisit the component boundary before coding further.

## Phase Order

### Phase 1. Service contract and DTO model

Define the code-level service surface and stable planning DTOs.

Files:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/component_design_planning/contracts.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/component_design_planning/models.py`

Deliver:
- `ComponentDesignPlanningService` protocol or abstract contract
- request DTOs
- planning view DTOs
- gap DTOs
- any small enum or literal helpers needed to keep outputs structured

Minimum DTOs:
- `ComponentPlanningRequest`
- `ComponentPlanningView`
- `ComponentElementPlanningView`
- `RealizationOptionView`
- `PlanningGap`
- `BriefPlanningPayload`

Important rule:
- model outputs for stable downstream consumption
- do not return loose nested dicts from the service boundary if dataclasses or typed records are reasonable

### Phase 2. Default service shell and collaborator composition

Create the default implementation and wire collaborator injection.

Files:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/component_design_planning/default.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/component_design_planning/__init__.py`

Deliver:
- `DefaultComponentDesignPlanningService`
- constructor injection for:
  - `ComponentDesignRepository`
  - `StructuredLogger`
- stable exports from package `__init__.py`

Important rule:
- keep the service stateless between calls
- no hidden caches in the first slice

### Phase 3. Component and element planning reads

Implement the first read-oriented planning functions over repository data.

Primary functions:
- `plan_component(request)`
- `plan_component_by_name(project_id, component_name)`
- `list_component_element_plans(component_id)`

Expected behavior:
- load component identity
- load component elements
- attach allowed realization types
- attach current realization instances
- assemble stable planning views

Important rule:
- the service interprets repository records
- it does not mutate repository state in this phase

### Phase 4. Realization option and gap detection logic

Implement the planning logic that makes the service useful to derivation and future authoring tools.

Primary functions:
- `list_realization_options(component_element_id)`
- `detect_component_design_gaps(component_id)`

Expected behavior:
- determine allowed realization options by element type
- surface missing required element structures
- surface missing or incomplete realization coverage
- report planning gaps explicitly rather than silently inferring away missing design

Important rule:
- gaps are outputs, not exceptions, unless required identity lookup fails

### Phase 5. Brief-planning payload assembly

Implement the first bridge from component planning into derivation-ready structured output.

Primary function:
- `build_brief_planning_payload(component_id, coder_run_brief_id | None)`

Expected behavior:
- package component planning into a stable payload that a future `Brief Assembly Service` can consume
- include:
  - component identity
  - element planning views
  - realization options
  - existing brief-target context when `coder_run_brief_id` is provided
  - gap/warning set

Important rule:
- do not absorb sequencing ownership from the future `Brief Assembly Service`
- do not absorb producer-side approval or orchestration logic

### Phase 6. Unit validation and boundary hardening

Add focused unit tests that prove both behavior and non-expansion of responsibility.

File:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/tests/unit/test_component_design_planning_service.py`

Minimum test groups:
- planning by component name
- component-element planning view assembly
- realization option view assembly
- gap detection
- brief-planning payload assembly
- missing component failure behavior
- explicit proof that no persistence mutation is required for the planning path

## First Concrete Operations

The first implementation slice should expose at minimum:
- `plan_component(request)`
- `plan_component_by_name(project_id, component_name)`
- `list_component_element_plans(component_id)`
- `list_realization_options(component_element_id)`
- `build_brief_planning_payload(component_id, coder_run_brief_id | None = None)`
- `detect_component_design_gaps(component_id)`

## Internal Helper Shape

The default implementation will likely need helpers such as:
- `load_component_context(...)`
- `load_component_elements(...)`
- `load_realization_type_map(...)`
- `load_realization_instances(...)`
- `load_brief_target_context(...)`
- `assemble_element_planning_view(...)`
- `assemble_component_planning_view(...)`
- `derive_planning_gaps(...)`

These helpers are implementation detail and should remain private to the default service module in the first slice.

## Anti-Goals

Do not in the first implementation slice:
- merge this service with `Brief Assembly Service`
- add producer CLI behavior into the service
- add workflow, execution-package, queue, or GitHub semantics
- write directly to the component-design repository from planning flows
- invent persistence-owned planning state
- absorb target sequencing authority that belongs downstream

## Verification Commands

Minimum validation commands for the first slice:

```bash
PYTHONPATH=packages/paa-core/src python -m unittest discover -s tests/unit -p 'test_component_design_planning_service*.py'
python -m py_compile \
  /Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/component_design_planning/contracts.py \
  /Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/component_design_planning/models.py \
  /Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/component_design_planning/default.py \
  /Users/billyweisberg/Repos/billyweisberg/paa-platform/tests/unit/test_component_design_planning_service.py
```

Recommended broader confidence pass after the dedicated service tests are green:

```bash
PYTHONPATH=packages/paa-core/src:packages/paa-core/src:packages/paa-cli/src:. python -m unittest discover -s tests/unit -p 'test_*.py'
```

## Success Criteria

This plan is successful when:
1. a code-level `ComponentDesignPlanningService` interface exists
2. a default implementation exists in `paa-core`
3. the service can derive stable planning views from `ComponentDesignRepository` records without mutating primary truth
4. gap detection is explicit and structured
5. a brief-planning payload can be produced for downstream derivation work
6. dedicated unit tests prove the service remains a narrow Domain Service

## Recommended Leave-Off Point

After this implementation slice lands, the next dependency-graph-driven target should be reassessed between:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-stratum-2-service-dependency-comparison.md`

Most likely next candidates:
1. `Execution Package Resolution Service`
2. `Brief Assembly Service` if producer-side derivation pressure makes it the more natural next downstream dependency

The important rule is unchanged:
- do not jump to `Workflow Lifecycle Service` before its policy and adapter dependencies mature further
