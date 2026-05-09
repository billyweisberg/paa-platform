# Team Worker Roles Design Spec

## Purpose

Define the target-state architecture for `Team Worker Roles`.

`Team Worker Roles` replaces the weaker idea of a fixed expanded worker-role list.
The goal is not only to support more known worker roles.
The goal is to let each consumer project define its own implementation-team roles as data.

This spec exists because the PAA database is already generic enough to store arbitrary roles, but the runtime, routing, branch/worktree logic, and automation layers are still partially hard-coded.

## Problem Statement

Today PAA supports:
- `Python Dev`
- `Frontend Dev`
- `Backend Dev`
- `Infra Dev`
- `Docs Dev`

But it supports them only as a fixed enumerated set in code.

That is not sufficient for the real target model.

The real target model is:
- a consumer project may define any number of team worker roles
- each role may have its own machine key and display name
- each role may have its own worker family
- each role may have its own branch suffix
- each role may have its own queue binding
- each role may have its own automation definition and bootstrap surface
- PAA should derive runtime behavior from that project role data rather than requiring code edits for every new role

## Scope

### In scope

- project-defined implementation-worker roles
- machine-readable role registry
- role-derived route policy
- role-derived branch/worktree naming
- role-derived automation configuration and launch assumptions
- role-derived bridge helper behavior for implementation workers

### Out of scope

- replacing `Delivery Architect` with a generic worker role
- replacing `QA` with a generic worker role
- removing `TechLead` as the routing hub
- redesigning the producer-side `Authority Architect` role
- final queue-topology scaling decisions across many projects

## Role Model

### Role categories

PAA role categories remain conceptually distinct:

- producer-side authority role
- consumer-side hub role
- specialized consumer review roles
- consumer-side team worker roles

For this spec:
- `TechLead` remains the hub
- `Delivery Architect` remains a specialized review role
- `QA` remains a specialized review role
- `Team Worker Roles` are the generalized implementation roles

### Team Worker Role definition

Each team worker role must be definable as data with at least:

- `key`
  - stable machine key
  - example: `python-team`
- `display_name`
  - user-facing / packet-facing role label
  - example: `Python Dev`
- `family`
  - stable grouping
  - examples: `implementation`, `docs`, `infra`
- `branch_suffix`
  - deterministic role-branch suffix
  - example: `dev`
- `queue_binding`
  - queue or queue-group key
  - example: `implementation`
- `automation_id`
  - automation registration id
  - example: `python-team-automation`
- `skill_id`
  - primary role execution skill id
  - example: `fractal-core-dev-result`
- `result_packet_family`
  - currently expected to be `worker_result_packet`
- `active`
  - whether the role is enabled for the project

Optional future fields:
- `model_preference`
- `reasoning_effort`
- `worktree_policy`
- `allowed_assignment_types`
- `allowed_result_types`
- `env_profile`

## Source Of Truth

The system needs one project-level source of truth for Team Worker Roles.

### Required source

Consumer project role registry file.

Initial install location:
- `.codex/paa/team-worker-roles.json`

Optional config override:
- consumer `project-config.json` may point to an alternate registry path

### Why this source

This keeps role truth:
- local to the consumer project
- installable with the repo-local runtime
- readable by runtime code without depending on DB seeding first
- versionable in PAA platform project-pack source

### Relationship to DB

`paa.roles` remains the persistence layer for role identity.

But the authoritative behavioral contract for Team Worker Roles should come from the project role registry, then be reflected into:
- runtime normalization
- queue route policy
- automation generation
- DB seeding/synchronization

## Packet Contract Implications

### Assignment packets

`techlead_assignment_packet` remains the assignment family.

`target_role` must be allowed to carry any active Team Worker Role display name defined in the project role registry.

### Worker result packets

`worker_result_packet` remains the default result family for Team Worker Roles.

Required identity fields remain:
- `worker_role`
- `worker_family`

The important rule is:
- `worker_role` is project-defined data
- not a hard-coded runtime enum

### Specialized packets remain specialized

- `delivery_review_packet` stays specialized to `Delivery Architect`
- `qa_verification_packet` stays specialized to `QA`

## Routing Contract

### Hub rule stays the same

Only `TechLead` may issue the next consumer-side assignment.

Allowed implementation-worker routes become data-derived:
- `TechLead -> <Team Worker Role>` via `techlead_assignment_packet`
- `<Team Worker Role> -> TechLead` via `worker_result_packet`

### Route policy derivation

Runtime route policy for Team Worker Roles should be derived from the active project role registry.

That means:
- no hard-coded tuple list for worker roles
- worker route pairs are synthesized from active Team Worker Role definitions

## Branch And Worktree Contract

### Canonical branch

- `issue-<issue_number>`

### Role branches

Derived from Team Worker Role definitions:
- `issue-<issue_number>-<branch_suffix>`

Examples:
- `issue-106-dev`
- `issue-106-frontend`
- `issue-106-backend`
- `issue-106-infra`
- `issue-106-docs`

### Worktree paths

Derived from role branch:
- `/Users/billyweisberg/.codex/worktrees/paa/<repo_name>/<role_branch>`

### Ownership rule

Unchanged:
- `TechLead` owns lineage authority and branch authorization
- the role automation owns create-or-reuse of its own prepared worktree beneath that authorization

## Automation Contract

### Required automation-level derivations

Each Team Worker Role must be able to derive:
- automation registration id
- prompt/skill binding
- repo root
- preflight command
- worktree entry contract
- result compile/send contract

### Required no-work behavior

Every Team Worker Role automation must:
- poll for claimable work without invoking the model
- exit with no model call when there is no work

### Required execution-environment behavior

Every Team Worker Role automation must:
- launch from the canonical consumer repo root
- use repo-local installed runtime wrappers
- transition into the prepared role worktree for execution
- use the role’s configured worktree and env policy

## Queue Contract

### Initial rule

The first implementation may bind multiple Team Worker Roles to the same implementation queue.

Initial assumption:
- `queue_binding = implementation`
- implementation queue name resolves to `fractal-core-python`

This is acceptable as an initial target-state stepping stone as long as:
- the role identity is explicit in the packet payload
- preflight and claim logic can still filter by target role

### Future expansion

Later we may allow:
- per-role queues
- per-family queues

But Team Worker Roles must not depend on that future queue-topology decision to exist.

## DB Contract

### What already works

The DB already stores roles generically in:
- `paa.roles`

And handoffs generically in:
- `paa.handoffs`

That is sufficient for the persistence foundation.

### What still needs design

We still need a synchronization contract between:
- project role registry
- `paa.roles`

That sync can be implemented as:
- bootstrap seeding
- explicit sync command
- install/update-time sync

The important rule is that runtime behavior should not require hand-editing code for new worker roles.

## Migration Strategy

### Phase T1

Introduce Team Worker Role registry and loader.

### Phase T2

Switch role normalization and branch suffix mapping to the registry.

### Phase T3

Switch worker route policy derivation to the registry.

### Phase T4

Switch worker bridge helpers to derive target worker behavior from the registry.

### Phase T5

Reconcile automation definitions and bootstrap logic with the registry.

### Phase T6

Prove at least one non-Python Team Worker Role end to end.

Recommended first proving role:
- `Docs Dev`

## Acceptance Criteria

This design is successfully implemented when:
- a consumer project can define Team Worker Roles in project data
- runtime role normalization does not require code edits for each new worker role
- route policy for implementation workers is registry-derived
- branch/worktree naming for implementation workers is registry-derived
- automation definitions can be aligned to registry-defined worker roles
- at least one non-Python Team Worker Role has been proven through the generic worker bridge

## Immediate Implementation Order

1. add the Team Worker Role registry to the project/runtime install surface
2. teach runtime loaders to read it
3. replace hard-coded worker normalization and branch suffix maps with registry-driven lookups
4. then generalize worker route policy and worker bridge behavior

