# Phase G Prep: Multi-Role Generalization And Delivery Architect Integration

## Purpose

Prepare Phase G so we do not mix three separate concerns into one uncontrolled change:
- multi-worker generalization
- Delivery Architect integration
- packet-family cleanup

Phase F proved that the current bridge orchestration is reusable.
Phase G now needs to decide where the schema boundary really belongs.

## What Phase F proved

The current bridge shape is good enough to keep:
- TechLead assignment emission
- role branch/worktree preparation
- role entry guidance
- role-result assist
- role-return compile/validate/send

This has now been validated for:
- `Python Dev`
- `QA`

That means the orchestration layer should not be rewritten in Phase G unless a real contradiction appears.

## What is still not good enough

### 1. `slice_result_packet` is still too Python-specific

It works for the current `Python Dev` lane.
It is not a good final name for a generic worker result family.

So the real Phase G question is not:
- do we need a new bridge?

It is:
- do we keep `slice_result_packet` as a transitional Python-only result family while adding broader worker support?
- or do we introduce `worker_result_packet` now?

### 2. Delivery Architect is still mostly a design-level role

The hub model already assumes:
- `TechLead -> Delivery Architect`
- `Delivery Architect -> TechLead`

But that role is not yet implemented as a first-class assignment/result lane in the runtime.

That means Delivery Architect should be treated as the second major Phase G concern.

## Recommended Phase G shape

Phase G should be split into two internal tracks, but kept in one phase because they share the same generalization boundary.

### Track 1: Worker result contract

Goal:
- decide whether worker-role generalization requires `worker_result_packet` now

Recommendation:
- yes, but do it as a controlled contract addition, not a forced migration of all existing historical data

Why:
- `slice_result_packet` is fine as a transitional artifact for Python
- it is a bad long-term contract for:
  - `Frontend Dev`
  - `Backend Dev`
  - `Infra Dev`
  - `Docs Dev`

So the likely right move is:
- keep `slice_result_packet` accepted for the Python lane during transition
- add `worker_result_packet` as the generic future worker result family
- let `Python Dev` eventually move onto `worker_result_packet` once the generic lane is proven

### Track 2: Delivery Architect integration

Goal:
- add a real Delivery Architect spoke path without overloading QA or worker semantics

Recommendation:
- introduce `delivery_review_packet`
- do not force Delivery Architect into `worker_result_packet`

Why:
- Delivery Architect is a scoped architectural review role
- QA is verification
- workers are implementation roles
- those three semantics should stay distinct

## Recommended Phase G sequence

### G1. Lock packet-family decisions

Decide and document:
- `slice_result_packet` remains transitional
- `worker_result_packet` is introduced as the new generic worker result family
- `qa_verification_packet` remains retained
- `delivery_review_packet` is introduced for Delivery Architect

### G2. Add `worker_result_packet` without migrating everything yet

Implement:
- schema
- examples
- validator/runtime acceptance
- compiler path
- queue persistence support

But keep:
- existing `slice_result_packet` support alive for current Python transition runs

### G3. Add Delivery Architect assignment/result path

Implement:
- TechLead assignment emission for `Delivery Architect`
- Delivery Architect result return via `delivery_review_packet`
- route-policy support for:
  - `TechLead -> Delivery Architect`
  - `Delivery Architect -> TechLead`

### G4. Prove one non-Python generalized path

Choose one proving path:
- either Delivery Architect as the first non-worker spoke
- or one synthetic future worker family contract proving run

My recommendation:
- prove Delivery Architect first

Reason:
- it is already part of the target hub model
- it is the smallest non-Python expansion with current business relevance

## What not to do in Phase G

Do not:
- rewrite the existing branch/worktree bridge
- couple worktree cleanup into packet-family work
- migrate historical packets aggressively
- rename everything at once
- broaden into full automation unpause work

## Acceptance criteria for Phase G

Phase G is done when:
- `worker_result_packet` exists and is accepted by the control spine
- `delivery_review_packet` exists and is accepted by the control spine
- TechLead can route at least one non-Python spoke cleanly
- the bridge remains compatible with both transitional and generalized packet families
- the current Python lane is still functional during the transition

## Recommended next slice inside Phase G

The next slice should be:
- define the exact `worker_result_packet` and `delivery_review_packet` contracts side by side

That gives us the cleanest boundary before code changes start.
