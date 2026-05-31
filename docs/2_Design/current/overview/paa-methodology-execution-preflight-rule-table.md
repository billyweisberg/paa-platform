Title: PAA Methodology Execution Preflight Rule Table
Doc-ID: paa-methodology-execution-preflight-rule-table
Doc-Type: design-note
Status: active
Lifecycle-Stage: design
Created: 2026-05-30
Last-Edited: 2026-05-30
Author: Billy Weisberg
Repo: paa-platform
Component: MethodologyExecutionPreflightService
Domain: methodology-execution
Keywords: paa, methodology, preflight, rule-table, lane, command, status, next
Depends-On: 2026-05-30-paa-methodology-execution-transition-state-machine-table.md, 2026-05-30-paa-methodology-lane-and-command-model.md, 2026-05-30-paa-methodology-execution-object-model.md, 2026-05-30-methodology-execution-repository-contract-and-persistence-mapping.md, 2026-05-30-paa-operator-cli-command-family-decomposition.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-06-30
Summary: Defines explicit preflight rules for the first live PAA CLI command families so the future methodology-execution preflight service can return allowed, warn, blocked, and redirect outcomes from current pointer truth.

# PAA Methodology Execution Preflight Rule Table

## Purpose

Define the first explicit preflight rules for PAA CLI command execution against methodology pointer truth.

This note exists to answer:
- when a command is allowed
- when it should warn
- when it must block
- when it should redirect the operator to a better next command

## Design Rule

Preflight should evaluate commands against:
- current `lane`
- current `stage`
- current `step`
- current `status`
- bound related records
- current next-action expectation

The service should not rely on operator memory or command-family guesswork.

## Preflight Outcome Vocabulary

- `allowed`
- `warn`
- `blocked`
- `redirect`

## First Live Scope

This first table covers the live command families already present in the real Typer shell:
- `paa component materialize`
- `paa component progress`
- `paa component reconcile`
- `paa component next`
- `paa plan progress`
- `paa plan inspect`

It also seeds the first pointer-facing read commands that will matter soon:
- `paa status`
- `paa next`
- `paa explain`

## Preflight Rule Table

| rule_key | command_family | command_name | required_lane | required_stage | required_step | allowed_statuses | required_bindings | outcome_if_match | outcome_if_missing | redirect_target | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| component-materialize-allowed | component | materialize | component_realization | component_materialization | materialize_component_spec | `ready`, `active` | `project`, optional `component` | allowed | blocked | none | Allows explicit component-spec materialization when the component-realization lane is active. |
| component-materialize-warn-active-slice | component | materialize | component_realization | slice_execution | execute_component_activity | `active`, `waiting` | `implementation_plan` | warn | blocked | `component progress` | Warns when the operator tries to rematerialize while an active slice loop already exists. |
| component-progress-allowed | component | progress | component_realization | component_materialization or slice_execution | any | `ready`, `active`, `waiting`, `blocked`, `completed` | `implementation_plan` | allowed | blocked | none | Progress inspection is safe across most non-terminal component states if a plan is bound. |
| component-reconcile-allowed | component | reconcile | component_realization | slice_execution | reconcile_component_plan_progress or execute_component_activity | `ready`, `active`, `waiting` | `implementation_plan` | allowed | blocked | `component progress` | Reconcile is allowed only when the component plan already exists and the lane is active. |
| component-next-allowed | component | next | component_realization | slice_execution | derive_next_activity_bundle or reconcile_component_plan_progress | `ready`, `active`, `waiting` | `implementation_plan` | allowed | blocked | none | Direct next-slice derivation path for the realized component lane. |
| component-next-redirect-terminal | component | next | component_realization | slice_execution | derive_next_activity_bundle | `completed` | `implementation_plan` | redirect | blocked | `status` | If the component lane is already completed, direct the operator to pointer status instead of pretending another slice exists. |
| plan-progress-allowed | plan | progress | component_realization | component_materialization or slice_execution | any | `ready`, `active`, `waiting`, `blocked`, `completed` | `implementation_plan` | allowed | blocked | none | Plan progress is a safe read surface whenever an implementation plan is bound. |
| plan-inspect-allowed | plan | inspect | component_realization | component_materialization or slice_execution | any | `ready`, `active`, `waiting`, `blocked`, `completed` | `implementation_plan` | allowed | blocked | none | Plan inspect mirrors progress as a read-only inspection surface. |
| wrong-lane-component-command | component | * | authority_derivation or runtime_execution or acceptance_closeout | any | any | any non-terminal | none | redirect | blocked | lane-native command family | Component-family commands in the wrong lane should redirect, not just fail vaguely. |
| wrong-lane-plan-command | plan | * | authority_derivation or runtime_execution or acceptance_closeout | any | any | any non-terminal | none | redirect | blocked | lane-native command family | Plan-family commands in the wrong lane should redirect toward the active lane. |
| blocked-state-any-mutation | component or plan | mutating commands | any | any | any | `blocked` | none | blocked | blocked | `explain` | If the current methodology state is blocked, mutating commands should stop and surface the blocking reason. |
| status-read-allowed | status | inspect | any | any | any | any | `project`, `work_item` or `methodology_execution` | allowed | blocked | none | Pointer-facing status should be allowed across all lanes once the projection exists. |
| next-read-allowed | report | next | any | any | any | `ready`, `active`, `waiting`, `blocked`, `completed` | `methodology_execution` | allowed | blocked | none | Future next-step projection should read current pointer truth rather than derive from memory. |
| explain-read-allowed | report | explain | any | any | any | any | `methodology_execution` | allowed | blocked | none | Future explain surface should always be readable when a methodology execution thread exists. |

## Rule Interpretation Notes

### `required_stage`
This may be a single stage or a constrained set.
For implementation, the preflight service should support set membership rather than a single-string comparison only.

### `required_step`
`any` means step does not further constrain the command once lane and stage match.

### `allowed_statuses`
These should be treated as a closed set, not freeform text.

### `required_bindings`
Bindings should be checked against `MethodologyExecutionBinding` or direct root references.
Missing required bindings should produce explicit blocked outcomes.

### `redirect_target`
This should identify the operator-facing next best command family or command.
The first implementation may encode it as a string before later promoting it to a richer command-reference DTO.

## Command-Family Design Implications

### `component`
- should stay a mutation-and-inspection family for the component-realization lane
- should fail closed when no implementation plan is bound
- should redirect rather than confuse when the active lane is not component realization

### `plan`
- should behave as a read-oriented family over implementation-plan truth
- should remain available through most component-realization statuses once a plan exists
- should still redirect when the active lane is fundamentally elsewhere

### `status`, `next`, `explain`
- should become first-class pointer-reading commands once projection exists
- should not be implemented as ad hoc helpers over scattered records

## First Service Recommendation

The first `MethodologyExecutionPreflightService` slice should implement:
1. rule evaluation for `component` and `plan`
2. blocked-state handling
3. wrong-lane redirect handling
4. explicit missing-binding failures

That is enough to start moving the CLI from implicit assumptions to pointer-aware behavior.
