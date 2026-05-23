Title: Component Slice Successor Derivation Policy
Doc-ID: paa-component-slice-successor-derivation-policy
Doc-Type: policy
Status: active
Lifecycle-Stage: design
Created: 2026-05-23
Last-Edited: 2026-05-23
Author: Billy Weisberg
Repo: paa-platform
Component: PaaComponentSliceSuccessorDerivationPolicy
Domain: governance
Keywords: paa, implementation-plan, successor, next slice, dependency graph, thin slice
Depends-On: 2026-05-23-component-realization-status-vocabulary.md, 2026-05-23-component-completion-policy.md, 2026-05-17-implementation-plan-entity-design.md
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
Summary: Defines how the next valid implementation slice is derived from implementation-plan activity state, dependency truth, and verification status.

# Component Slice Successor Derivation Policy

Date: 2026-05-23

## Purpose

Define how PAA derives the next valid implementation slice for a partially realized component after one thin slice has been verified and accepted.

## Core Decision

Successor-slice derivation should operate on implementation-plan truth.

It should use:
- activity state
- dependency truth
- verification-surface status
- current plan authority state

It should not invent the next slice from memory, prose, or convenience.

## Policy

### Rule 1: the next slice must be executable

The next slice may only contain activities whose hard predecessors are satisfied.

### Rule 2: blocked predecessors fail closed

If a remaining activity depends on a blocked predecessor, the system must report a blocked result.

It must not silently skip ahead.

### Rule 3: unresolved graph ambiguity fails closed

If the system cannot determine one valid next activity because of:
- duplicate sequencing ambiguity
- unresolved dependency truth
- conflicting completion evidence

it must fail closed and surface blocking reasons.

### Rule 4: v1 defaults to one activity at a time

In this slice, successor derivation should emit:
- one next incomplete executable activity

A larger bundle is allowed only when policy explicitly authorizes it.

### Rule 5: no remaining work means completion

If no required incomplete activities remain, the system should report:
- `completed_plan`
- `fully_realized`
- no next bundle

### Rule 6: deferred work remains visible

Deferred activities do not belong in the immediate next bundle.

They still remain part of the plan-completion surface until explicitly cancelled or superseded by authority.

## Required Successor Result Surface

A successor-derivation result should report at minimum:
- whether derivation succeeded
- next bundle activity key or keys
- bundle kind
- decision reason
- blocking reasons
- unattended-safe flag
- recommended next authority action

## Non-Goals

This policy does not:
- generate a coder brief in this slice
- generate queue packets in this slice
- orchestrate runtime execution in this slice

## Success Condition

This policy is successful when, after one accepted slice, the system can deterministically answer:
- what is next
- why it is next
- or why no valid next slice currently exists
