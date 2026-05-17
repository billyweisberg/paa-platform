# Implementation Plan Activity Derivation Policy

Date: 2026-05-17

## Purpose

Define how the operator-facing project activity states are derived from:
- implementation-plan truth
- workflow truth
- runtime execution evidence

This note answers the practical question:
- where does PAA determine the current execution step of the Agent Team?

The answer after this design correction is:
- the authoritative activity list lives in `ImplementationPlan`
- the operator-facing activity state is derived from implementation-plan records plus workflow/runtime state

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-implementation-plan-entity-design.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-final-projection-boundary-policy.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-domain-object-model-and-oo-component-decomposition.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-layered-architecture-proposal.md`

## Core Decision

The following are distinct:

### Primary truth
- `ImplementationPlan`
- `ImplementationPlanActivity`
- `ImplementationPlanActivityDependency`
- `ImplementationPlanVerificationSurface`
- `WorkflowState`
- `WorkflowTransition`
- runtime execution evidence

### Derived operator-facing view
- current activity
- next activity
- completed activities
- blocked activities

Important rule:
- these operator-facing states should be projections
- but they must derive from primary planning truth, not from report files or queue residue

## Source Sets

## 1. Planning truth inputs
- `paa.implementation_plans`
- `paa.implementation_plan_activities`
- `paa.implementation_plan_activity_dependencies`
- `paa.implementation_plan_artifacts`
- `paa.implementation_plan_verification_surfaces`

## 2. Execution-authority inputs
- `paa.coder_run_briefs`
- `paa.coder_brief_realization_targets`
- `paa.coder_brief_authority_events`

## 3. Workflow truth inputs
- `paa.workflow_states`
- `paa.workflow_transitions`

## 4. Runtime execution evidence inputs
- `paa.queue_claims`
- `paa.handoffs`
- `paa.queue_messages`
- `paa.automation_runs`
- `paa.automation_run_events`
- `paa.execution_records`
- `paa.acceptance_events`
- `paa.evidence`

## Activity State Model

The implementation-plan activity table should own the explicit planning-level state:
- `planned`
- `ready`
- `active`
- `completed`
- `blocked`
- `skipped`
- `superseded`

Important rule:
- this is not the full workflow state machine
- it is the project-design activity state model

## Derivation Principles

## Principle 1. The activity list is explicit

The system must not derive the set of project activities only by inspecting:
- coder briefs
- queue packets
- source code diffs
- freeform notes

The activity list must come from:
- `paa.implementation_plan_activities`

## Principle 2. Workflow and runtime evidence refine display state

Workflow and runtime evidence help determine what is currently happening.

They do not replace the activity list.

## Principle 3. Explicit activity state wins over weak inference

If an activity row explicitly says:
- `active`
- `completed`
- `blocked`
- `superseded`

that explicit planning truth should beat weak heuristic inference from reports or logs.

Runtime evidence may justify updating that state through services later.
It should not silently override it in a projection query.

## Principle 4. Terminal workflow closes the remaining open activities

If workflow is terminal:
- accepted
- rejected
- proof-only closed
- superseded

then no activity should appear as current or next.

Remaining non-completed activities are interpreted according to terminal outcome:
- `superseded`
- or unresolved historical residue

## Derivation Rules

## A. Current Activity

### Definition
The `current activity` is the activity or set of activities the system should present as actively being executed now.

### Derivation rule

1. Start from activities in the active implementation plan whose state is:
- `active`

2. If one or more such activities exist:
- they are the current activity set

3. If no activity is explicitly `active`, consult workflow/runtime evidence:
- current owner role from `workflow_states`
- active queue claim
- active automation run
- active coder brief in `approved_brief` or `packet_ready_execution_authority` progression

4. If the current execution lane can be mapped to one or more implementation-plan activities by:
- component element
- realization target
- target path
- assigned role

then those mapped activities become the effective current activity set for projection purposes.

### Important rule
If neither explicit activity state nor reliable workflow/runtime mapping exists:
- current activity = none

Do not invent one from guesswork.

## B. Next Activity

### Definition
The `next activity` is the next executable activity or parallel-safe activity set that should start once current work is done.

### Eligibility rule
An activity is eligible to be `next` only when all are true:
- activity state is `planned` or `ready`
- activity is not `blocked`, `completed`, `skipped`, or `superseded`
- all hard predecessor activities are `completed`
- the implementation plan is at least `approved_plan`
- workflow is not terminal
- required verification surfaces that must precede the activity are satisfied

### Selection rule

From the eligible set:
1. sort by `sequence_order`
2. preserve dependency constraints from `implementation_plan_activity_dependencies`
3. if multiple eligible activities share:
- the same sequence band
- and only `may_parallelize` relationships between them

then expose them as the `next activity set`

Otherwise:
- the earliest eligible activity is the `next activity`

## C. Completed Activities

### Definition
Activities that have successfully finished for the current implementation plan.

### Derivation rule

An activity is `completed` when any of the following is true:
1. `activity_state = completed`
2. a plan-state synchronization service has already promoted it to completed from runtime evidence
3. all of the following are true:
- the expected artifact(s) exist or are recorded as produced
- required verification surfaces tied to that activity are `passed` or `waived`
- no later supersede or rejection invalidates the result

### Important rule
Completion should eventually be made explicit in primary activity state.
Projection inference is a fallback, not the preferred long-term owner.

## D. Blocked Activities

### Definition
Activities that should not currently execute.

### Derivation rule

An activity is `blocked` when any of the following is true:
1. `activity_state = blocked`
2. one or more hard predecessors are not completed
3. the implementation plan is not yet approved for briefing/execution
4. workflow is blocked, reset-required, or otherwise not execution-ready
5. a required verification surface that must precede the activity is failed or missing
6. the activity depends on an unresolved external contract or consumer-context prerequisite

### Important rule
Blocked activities should carry a visible blocking reason.
The operator-facing project view should not merely hide them.

## E. Activities That Are Neither Current Nor Next

An activity may be:
- `planned` but not yet eligible
- `ready` but lower priority than an earlier ready activity
- `skipped`
- `superseded`

These should remain queryable as distinct planning states, not collapsed into “not started.”

## Projection Output Contract

The operator-facing project projection should be able to emit, at minimum:
- `current_activity_set`
- `next_activity_set`
- `completed_activity_set`
- `blocked_activity_set`
- `parallel_ready_activity_set`
- `terminal_activity_state` if workflow is terminal
- `critical_path_activity_set`

## Resolution Precedence

When conflicting signals exist, resolve in this order:

1. explicit terminal workflow truth
2. explicit implementation-plan activity state
3. explicit implementation-plan dependency truth
4. explicit verification-surface state
5. runtime execution evidence
6. convenience summaries or report artifacts

Important rule:
- report files are last, not first

## Relationship To The Future Project Projection

The future:
- `paa.project_delivery_projections`

should derive from this policy.

That projection is what people will most likely perceive as:
- “the Project”

But its correctness depends on:
- implementation-plan truth existing first
- workflow/runtime truth being linked to activities

## Design Consequence

This note implies at least three future implementation responsibilities:

1. `ImplementationPlanRepository`
- owns primary access to plan, activity, dependency, and verification-surface records

2. `Implementation Plan Derivation Service`
- creates the authoritative activity list and dependency graph from approved slice authority

3. `Project Delivery Projection Service`
- derives the current/next/completed/blocked operator-facing view from plan truth plus workflow/runtime state
