Title: PAA Implementation Plan Activity State Transition Command Surface
Doc-ID: paa-implementation-plan-activity-state-transition-command-surface
Doc-Type: design-note
Status: active
Lifecycle-Stage: design
Created: 2026-05-30
Last-Edited: 2026-05-30
Author: Billy Weisberg
Repo: paa-platform
Component: PAAOperatorCLI
Domain: implementation-plan
Keywords: paa, implementation-plan, activity, state, command, complete, reconcile, cli
Depends-On: 2026-05-27-component-realization-loop.md, 2026-05-30-paa-methodology-lane-and-command-model.md, 2026-05-30-paa-operator-cli-command-family-decomposition.md, 2026-05-23-component-completion-policy.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-06-30
Summary: Defines the missing command surface for explicit implementation-plan activity state transitions, including a low-level producer command and an operator-facing `paa component complete` flow.

# PAA Implementation Plan Activity State Transition Command Surface

## Purpose

Define the missing operator and producer command surface for implementation-plan activity state transitions.

This note exists because the current component-realization loop requires an explicit step to mark one activity complete after implementation and verification, but the current public command surfaces do not expose that step directly.

Without that command surface:
- operators must reach into repository code directly
- the loop described in authority is not fully executable from public tooling
- one of the most important realization actions remains implicit rather than governed

## Problem Statement

The current public loop exposes:
- `materialize-component-spec`
- `implementation-plan-progress`
- `reconcile-implementation-plan-progress`
- `derive-next-activity-bundle`

But it does not expose:
- `complete one implementation-plan activity`

That gap creates avoidable cognitive load and breaks the goal of making the methodology directly operable from the CLI.

## Design Goal

Provide a governed command surface that:
- mutates implementation-plan activity state through one explicit boundary
- supports the current manual realization loop
- fits both the low-level producer runtime and the higher-level `paa` operator CLI
- fails closed when prerequisites or state assumptions do not hold

## Scope

This note covers:
- activity-state transition command semantics
- low-level producer command shape
- operator-facing `paa component complete` shape
- required preflight and post-action behavior

This note does not define:
- a new repository capability
- a new persistence model
- methodology pointer command semantics beyond this transition surface

## Current Underlying Capability

The underlying mutation capability already exists in code through:
- `ImplementationPlanActivityStateUpdateSpec`
- `PostgresImplementationPlanRepository.set_implementation_plan_activity_state(...)`

The gap is therefore not missing persistence logic.
The gap is missing operator-safe command exposure.

## Command Surface Model

### Layer 1. Low-level producer mutation command

Purpose:
- provide a direct governed command over activity-state mutation for producer/runtime tooling

Recommended command:
- `paa-producer set-implementation-plan-activity-state`

Required arguments:
- `--plan-id`
- `--activity-key`
- `--activity-state`

Optional arguments:
- `--blocking-reason`
- `--started-at`
- `--completed-at`
- `--metadata-json`

Behavior:
- update the selected activity state through the repository boundary
- return a structured result describing the requested transition
- do not silently reconcile or derive the next activity unless explicitly requested by a separate higher-level command

Rationale:
- this keeps the low-level surface honest and composable
- it matches the producer/runtime role as a more direct tool layer

### Layer 2. Operator-facing `paa component complete`

Purpose:
- expose the common realization-loop action through the real operator CLI

Recommended command:
- `paa component complete`

Required arguments:
- `--plan-id`
- `--activity-key`

Optional arguments:
- `--completed-at`
- `--metadata-json`
- `--no-reconcile`
- `--no-next`

Default behavior:
1. preflight the requested completion action
2. set the activity state to `completed`
3. reconcile implementation-plan progress
4. derive the next activity bundle
5. print a structured completion result including:
   - updated plan summary
   - updated realization state
   - next activity key or `none`

Rationale:
- this matches the actual operator loop
- it removes the need to remember separate follow-up commands in the common case

## Command Responsibility Split

| surface | responsibility |
|---|---|
| `paa-producer set-implementation-plan-activity-state` | low-level state mutation |
| `paa component complete` | operator-safe completion action with loop follow-through |

This split preserves both:
- a stable automation primitive
- a low-cognitive-load operator action

## Supported First Transition

The first required transition is:
- `planned|ready|active -> completed`

The first implementation slice does not need to expose the full state machine.

Later extensions may add:
- `paa component start`
- `paa component block`
- `paa component defer`
- `paa component reopen`

Those should be designed after the completion path is stable.

## Preflight Requirements

### For low-level producer command

Minimum checks:
- plan exists
- activity exists in the selected plan
- target state is a valid controlled-vocabulary state

Fail-closed behavior:
- if any required lookup fails, return non-zero and do not mutate state

### For `paa component complete`

Required checks:
- plan exists
- activity exists
- activity is not already `completed`
- activity is not `superseded` or `skipped`
- if methodology pointer truth is available later, active lane is `component_realization`
- if methodology pointer truth is available later, current step is compatible with completion action

Recommended warning path:
- if the activity is still `planned` rather than `active`, allow completion only if explicit verification has already been performed or the current implementation model intentionally uses completion as a direct proof step

## Post-Action Behavior

### Producer command

Return structured JSON including:
- `implementation_plan_id`
- `activity_key`
- `requested_state`
- `ok`
- `metadata`

### `paa component complete`

Return structured JSON or rendered CLI output including:
- `implementation_plan_id`
- `activity_key`
- `transition_applied`
- reconciled plan summary
- `authority_state_summary`
- `realization_state`
- `completion_ratio`
- `next_activity_key`
- `next_bundle_activity_keys`

## Failure Modes

The command surface must fail closed for:
- unknown plan id
- unknown activity key
- unsupported state transition target
- malformed metadata JSON
- repository write failure
- reconcile failure
- next-activity derivation failure when follow-through is enabled

Operator-facing failure messages should state:
- what failed
- whether the mutation was applied already
- whether reconcile and next-activity derivation remain pending

## CLI Family Placement

This surface belongs to:
- low-level producer: implementation-plan mutation utility
- high-level operator CLI: `component` command family

It should not be hidden under:
- `plan`
- `ops`

Reason:
- the action semantically belongs to the component-realization lane, not generic reporting or administration.

## First Implementation Recommendation

### Step 1
Add:
- `paa-producer set-implementation-plan-activity-state`

### Step 2
Add:
- `paa component complete`

### Step 3
Default `paa component complete` to:
- mutate
- reconcile
- derive next

### Step 4
Update the operator guide and loop docs with the real command examples.

## Operator Example

Low-level:

```bash
PYTHONPATH=packages/paa-core/src:packages/paa-core/src:packages/paa-cli/src:. \
python -m paa_cli producer set-implementation-plan-activity-state \
  --plan-id <implementation-plan-id> \
  --activity-key <activity-key> \
  --activity-state completed
```

Operator-facing:

```bash
paa component complete \
  --plan-id <implementation-plan-id> \
  --activity-key <activity-key>
```

## Authority Outcome

After this command surface exists:
- the documented realization loop becomes directly executable from public tooling
- `mark activity complete` is no longer an implicit internal step
- the operator CLI gains a clearer component-realization control surface
