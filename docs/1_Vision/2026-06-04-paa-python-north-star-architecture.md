Title: PAA Python North Star Architecture
Doc-ID: paa-python-north-star-architecture
Doc-Type: vision
Status: active
Lifecycle-Stage: vision
Created: 2026-06-04
Last-Edited: 2026-06-04
Author: Billy Weisberg
Repo: paa-platform
Component: PAAOperatorSystem
Domain: system-architecture
Keywords: paa, python, north star, cli, api, services, data layer, methodology execution, target structure
Depends-On: 2026-05-28-paa-authority-stack-and-operator-architecture.md, 2026-05-28-paa-cli-system-architecture.md, 2026-06-04-paa-python-realization-profile.md, 2026-06-04-paa-language-profile-terminology-framework.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-07-01
Owners:
Expires:
Issue:
PR:
Authority-Source:
Implementation-Status: in-progress
Summary: Defines the North Star architecture, final target structure, and methodology-pointer placement for the Python PAA system.

# PAA Python North Star Architecture

## Vision Marker

This document is a Vision-layer authority document.

It is the North Star for the Python PAA system.

Design, plan, build, and refactor work should converge on this structure instead of preserving accidental repository history.

## Core Statement

The Python PAA system should be built as one governed operator system with one real command surface and one real application path.

The structural rule is:
- `cli -> api -> services/app logic -> data layer`

The governing state rule is:
- the `MethodologyExecution` pointer is the canonical answer to where the system is now and what action is valid next

## North Star Principles

1. `paa` is the operator-facing command surface
2. the API is a transport surface, not a second business owner
3. services/app logic own orchestration and business behavior
4. the data layer owns persistence and resource access
5. the methodology pointer governs transitions across the workflow
6. legacy structure should be removed instead of protected once the destination structure is real

## Final Target Structure

```text
paa-platform/
├── packages/
│   ├── paa-cli/
│   │   └── src/paa_cli/
│   │       ├── app.py
│   │       ├── router.py
│   │       ├── command_adapters.py
│   │       ├── rendering.py
│   │       ├── normalization.py
│   │       ├── environment.py
│   │       ├── models.py
│   │       └── contracts.py
│   │
│   └── paa-core/
│       └── src/paa_core/
│           ├── application/
│           │   ├── contracts/
│           │   ├── dto/
│           │   ├── services/
│           │   ├── operator_router.py
│           │   ├── operator_command_adapters.py
│           │   └── operator_result_normalizer.py
│           │
│           ├── api/
│           │   └── runtime/
│           │       ├── app.py
│           │       ├── client.py
│           │       ├── dependencies.py
│           │       └── routers/
│           │
│           ├── runtime/
│           │   ├── hosts/
│           │   ├── control/
│           │   ├── transport/
│           │   ├── orchestration/
│           │   ├── workflow/
│           │   ├── bridges/
│           │   ├── workers/
│           │   ├── packets/
│           │   └── support/
│           │
│           ├── producer/
│           │   ├── authority_runtime.py
│           │   ├── authority_parser.py
│           │   ├── authority_queries.py
│           │   ├── authority_issues.py
│           │   ├── authority_acceptance.py
│           │   ├── authority_reviews.py
│           │   ├── authority_packets.py
│           │   ├── authority_packet_results.py
│           │   ├── authority_techlead_packets.py
│           │   ├── authority_support.py
│           │   ├── authority_packet_support.py
│           │   ├── authority_resolution.py
│           │   └── support/
│           │
│           ├── repositories/
│           │   ├── component_design/
│           │   ├── methodology_execution/
│           │   ├── implementation_plan/
│           │   ├── runtime_event/
│           │   ├── runtime_identity/
│           │   ├── workflow_state/
│           │   └── execution_package/
│           │
│           ├── services/
│           │   ├── component_design_planning/
│           │   ├── implementation_plan_derivation/
│           │   ├── implementation_plan_progress/
│           │   ├── techlead_acceptance_decision/
│           │   ├── techlead_assignment_decision/
│           │   ├── techlead_closeout_decision/
│           │   ├── techlead_delivery_review_decision/
│           │   ├── techlead_lineage_decision/
│           │   ├── techlead_reset_recovery_decision/
│           │   └── techlead_worker_review_routing/
│           │
│           ├── policies/
│           ├── governance/
│           ├── domain/
│           └── sql/
```

## MethodologyExecution Placement

The `MethodologyExecution` pointer is not a side concept.
It is part of the North Star system design.

### Data layer
Persisted truth lives in:
- `paa_core.repositories.methodology_execution`

This package owns:
- `MethodologyExecution`
- `MethodologyExecutionEvent`
- `MethodologyExecutionBinding`
- `MethodologyExecutionProjection`

### Services/app logic layer
Application-facing operations live in:
- `paa_core.application.contracts.methodology_execution.py`
- `paa_core.application.dto.methodology_execution.py`
- `paa_core.application.services.methodology_execution.py`

This layer owns:
- load current pointer
- evaluate next valid action
- apply explicit transitions
- expose normalized pointer summaries to API and CLI surfaces

### Runtime workflow layer
Runtime-specific interpretation lives in:
- `paa_core.runtime.workflow.methodology_execution_preflight/`
- `paa_core.runtime.workflow.methodology_execution_projection/`
- `paa_core.runtime.workflow.methodology_execution_state/`

This layer owns:
- runtime-facing preflight and projection logic
- workflow-step resolution used by runtime flows
- pointer-aware execution helpers

### API layer
HTTP exposure lives in:
- `paa_core.api.runtime.routers.methodology_execution.py`

### CLI layer
CLI access lives in:
- `paa_cli.app.py`
- future `paa methodology ...` or equivalent pointer-aware command/preflight behavior

## Dishka Placement

Dishka is allowed in this architecture only as a composition tool.

It belongs at the API and CLI composition edges.
It does not replace the package ownership model.
It does not define business boundaries.

## Transitional Residue Rule

The following items are not part of the desired long-term ownership model:
- `paa_core.db.py` as a giant shared data dump
- placeholder or dormant packages with no clear owner
- wrapper paths preserved after their real destinations exist

Transitional residue should remain visible in planning until it is either:
1. moved into the North Star structure, or
2. removed

## Non-Negotiable Proof Rule

The Python PAA system is not considered structurally real until important operations work through the actual stack:
- `paa`
- API
- services/app logic
- data layer

Integration proof through the CLI is the main evidence that the North Star is being realized.

## Usage Rule

Use this document as the structural reference when deciding:
- where a new capability belongs
- where a `db.py` responsibility should move
- whether a module is permanent or transitional
- whether a new shortcut violates the architecture

If a proposed change does not fit this structure, stop and update the design first.
