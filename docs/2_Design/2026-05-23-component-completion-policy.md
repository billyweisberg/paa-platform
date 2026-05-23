Title: Component Completion Policy
Doc-ID: paa-component-completion-policy
Doc-Type: policy
Status: active
Lifecycle-Stage: design
Created: 2026-05-23
Last-Edited: 2026-05-23
Author: Billy Weisberg
Repo: paa-platform
Component: PaaComponentCompletionPolicy
Domain: governance
Keywords: paa, component, completion, implementation-plan, verification, iterative delivery
Depends-On: 2026-05-23-component-realization-status-vocabulary.md, 2026-05-17-implementation-plan-entity-design.md, 2026-05-20-component-spec-doc-to-materialization-extraction-rules.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-06-23
Owners:
Expires:
Issue:
PR:
Authority-Source:
Implementation-Status: defined
Summary: Defines how component completion is tracked through implementation-plan truth and verification surfaces during recursive thin-slice implementation.

# Component Completion Policy

Date: 2026-05-23

## Purpose

Define how PAA determines what part of one component has been implemented, what remains, and when a component should be treated as partially or fully realized.

This policy closes the gap between:
- complete design authority
- iterative thin-slice implementation
- durable progress truth over multiple accepted loops

## Core Decision

Component completion should be tracked through the existing `ImplementationPlan` family.

Important rule:
- completion is not a prose-only claim
- completion is computed from implementation-plan activities, dependencies, and verification surfaces
- the computed progress surface should live on the implementation-plan root metadata in this slice

## Policy

### Rule 1: authority-complete is the prerequisite for derivation

A component may enter iterative execution only when its component spec is `authority_complete`.

That means the current governed authority is sufficient to define:
- plan seed
- activity seed
- dependency truth
- verification surfaces

### Rule 2: component completion is activity-based

Component completion should be tracked by classifying each implementation-plan activity as one of:
- completed
- remaining
- blocked
- deferred

The component realization state should then be derived from the aggregate.

### Rule 3: required verification is part of completion

An activity is eligible for `completed` only when:
- its implementation state is complete
- and its required verification surfaces are satisfied

If required verification remains unresolved, the activity must not be promoted to completed current-state truth.

### Rule 4: metadata-backed current-state reporting is valid in v1

Until dedicated typed progress columns are introduced, the implementation-plan root may store computed completion truth in:
- `metadata_json.component_completion`

That metadata should remain:
- derived from primary plan/activity/proof truth
- not hand-maintained by ad hoc callers

### Rule 5: fully realized is bounded by the current plan

A component is `fully_realized` only when the current authoritative implementation plan has:
- no remaining required incomplete activities
- no unresolved required verification surfaces

### Rule 6: deferred is not the same as complete

Deferred work must remain visible in progress truth.

The system should preserve:
- which activities were deferred
- why they were deferred
- what remains before full realization can be claimed

## Required Progress Surface

The implementation-plan progress surface should report at minimum:
- `realization_state`
- `completion_ratio`
- `current_activity_key`
- `next_activity_key`
- `remaining_activity_count`
- `deferred_activity_count`
- `blocked_activity_count`
- `last_completed_activity_key`

## Non-Goals

This policy does not:
- define how coder briefs are assembled
- define packet transport or queue behavior
- require a new top-level progress table in this slice
- imply that every accepted slice automatically finishes a component

## Success Condition

This policy is successful when the system can answer:
- which activities are done
- which activities are deferred
- which thin slice was most recently completed
- what remains before the component is fully realized
