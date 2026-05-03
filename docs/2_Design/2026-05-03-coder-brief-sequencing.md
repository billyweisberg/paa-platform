# 85. Coder Brief Sequencing

## Purpose
This document defines how coder-brief sequencing is computed from:
- authority task order
- Stage 1 design package readiness
- component dependency graph constraints

The output is not just one next brief.
It can also produce:
- blocked briefs
- contract-ready briefs
- execution-ready briefs
- safe parallel brief sets

## Core principle
Execution order is not the same as roadmap order.

Roadmap order gives high-level progression.
Dependency sequencing gives execution readiness.

The scheduler must honor both.

## Inputs
Sequencing computation consumes:
- approved Stage 1 design packages
- authority task order
- component dependency edges
- package signoff state
- dependency statuses
- shared-surface conflict metadata
- existing active coder briefs
- existing active execution records

## Output classes
For each candidate brief, sequencing should classify it as one of:
- `not_derivation_ready`
- `derivation_ready`
- `blocked_on_dependency`
- `blocked_on_contract`
- `execution_ready`
- `parallel_ready`
- `active`
- `completed`

## Sequencing algorithm

### Step 1: Filter to authority-eligible tasks
A slice cannot be sequenced if it is not currently eligible by authority order.

Keep only tasks that are:
- active
- explicitly reachable through predecessor/successor rules
- not superseded or already completed

### Step 2: Require approved Stage 1 package
For each authority-eligible task, require:
- package status `approved_for_derivation`
- required signoffs present
- dependency graph slice present

If not, classify:
- `not_derivation_ready`

### Step 3: Resolve hard dependency blockers
For each primary component, inspect incoming dependency edges.

If any incoming edge is:
- `dependency_strength = hard`
and its dependency status is not sufficient for the edge's sequencing rule,
then classify:
- `blocked_on_dependency`
or
- `blocked_on_contract`

### Step 4: Check contract-only dependencies
If an edge is:
- `sequencing_requirement = must_follow_contract_only`

then the dependent brief may proceed if the upstream dependency status is at least:
- `contract_ready`

It does not need full implementation completion.

### Step 5: Check shared-surface conflicts
If a candidate brief shares an edit surface with another active or ready brief and the graph marks a conflict, then:
- block parallel execution
- keep only one brief execution-ready
- mark the other as blocked pending serialization

### Step 6: Determine derivation and execution readiness
If all hard blockers are satisfied:
- the brief may be `derivation_ready`

If, in addition, required contracts are satisfied and no shared-surface conflict blocks it:
- the brief may be `execution_ready`

### Step 7: Compute safe parallel sets
Two or more execution-ready briefs may enter the same parallel set only when all pairwise conditions are true:
- no hard dependency edge requires precedence between them
- no shared-surface conflict exists
- no verification or hosting blocker forces serialization
- their graph edges or constraints explicitly allow parallelism

Then classify them:
- `parallel_ready`

### Step 8: Promote active brief set
From the execution-ready pool:
- if only one brief is ready, route it next
- if multiple are parallel-ready, form an approved parallel set
- otherwise, choose the next brief by authority priority plus dependency satisfaction

## Dependency sufficiency table
Use this sufficiency table when evaluating edges.

| Sequencing rule | Minimum upstream status |
| --- | --- |
| `must_precede` | `implementation_ready` or stronger |
| `must_follow_contract_only` | `contract_ready` or stronger |
| `may_parallelize` | `defined` plus no conflict blockers |

## Parallelism policy
Parallel coder runs are allowed only when explicitly proven safe.

The default is conservative:
- unknown means not parallel-safe

Parallelism requires:
- explicit graph support
- no shared-surface conflict
- no hard dependency precedence
- TechLead approval for the parallel set

## Recommended sequence outputs
The scheduler should eventually emit records like:
- `ready_now`
- `blocked_by_component`
- `blocked_by_contract`
- `blocked_by_shared_surface`
- `parallel_group_id`
- `recommended_next_owner`

These can later drive:
- TechLead reports
- Architect derivation queues
- coder-brief packet generation

## Attachment rule for coder briefs
Sequencing output should not remain external prose once derivation is complete.

For each derived `coder_run_brief`, attach:
- execution prerequisites
- blocking dependency edges
- parallel-safe peers if any
- shared-surface conflicts
- current readiness class
- dependency-readiness snapshot
- blocking causes

This turns sequencing from a separate planning artifact into execution-facing authority that a coding lane can obey directly.

## Simple computation model
At a practical level, sequencing can be implemented as:
1. topological filtering by hard dependency edges
2. contract-readiness relaxation for contract-only edges
3. conflict elimination for shared surfaces
4. authority-order tie breaking

That is simple enough to build incrementally and strong enough to be useful.

## Immediate implication for PAA
PAA should eventually compute, persist, or materialize:
- dependency readiness
- execution readiness
- parallel-safe brief sets
- blocking causes

This is better than relying on humans to mentally reconcile graph structure every cycle.

## Next step
The next useful build step is:
- add the DB layer for design packages and dedicated dependency edges
- then we can persist the graph and compute readiness from live records
