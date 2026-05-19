Title: PAA Governed Code Vocabulary And Type Enforcement
Doc-ID: paa-governed-code-vocabulary-and-type-enforcement
Doc-Type: design-note
Status: active
Lifecycle-Stage: design
Created: 2026-05-19
Last-Edited: 2026-05-19
Author: Billy Weisberg
Repo: paa-platform
Component: PaaGovernedCodeVocabulary
Domain: governance
Keywords: paa, governance, basedpyright, pyright, types, vocabulary, metadata, code-truth
Depends-On: 2026-05-19-paa-language-governance-rules.md, 2026-05-19-paa-component-naming-rules.md, 2026-05-19-paa-status-claim-rules.md
Supersedes: 
Superseded-By: 
Canonical: true
Review-After: 2026-06-15
Owners: 
Expires: 
Issue: 
PR: 
Authority-Source: 
Implementation-Status: 
Summary: Defines the plan for enforcing governed PAA vocabulary in code through typed models, component metadata, basedpyright, and doc-to-code consistency checks.

# PAA Governed Code Vocabulary And Type Enforcement

## Purpose

This note defines the next governance layer after document and language governance:
- code-truth enforcement

The goal is to make governed PAA language real in code rather than leaving it only in docs and chat.

## Problem

Document governance and language governance can define:
- approved terminology
- approved naming rules
- approved status-claim rules
- architecture anti-patterns

But those controls do not by themselves verify that the codebase actually encodes the same distinctions.

Without a code-truth layer, drift still enters when:
- a runtime hub is described as a service without structural change
- a repository begins owning policy behavior
- a status word exists in docs but has no governed representation in code
- a workflow/service/review result is passed as loose dicts instead of typed governed models

## Core Principle

PAA docs define the governed vocabulary.
Code must encode the governed vocabulary in typed forms.
Static tooling must verify those typed forms are used consistently.

## What Basedpyright Is For

`basedpyright` is not a prose verifier.
It is the code-truth enforcement layer for governed vocabulary.

It is the right tool for:
- protocol conformance
- DTO/model shape enforcement
- allowed literal values
- discriminated unions
- required metadata structure
- service/repository/policy contract consistency

It is not the right tool for:
- validating that markdown prose is semantically true
- deciding whether a narrative claim is overstated
- reasoning about architecture quality from prose alone

Those concerns remain in:
- language governance docs
- doc lint
- custom doc-to-code consistency checks

## Enforcement Architecture

The enforcement stack should have four layers.

### 1. Vocabulary authority in docs

Reference docs define allowed words and meanings.

Primary sources:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/terminology/2026-05-19-paa-language-governance-rules.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/terminology/2026-05-19-paa-component-naming-rules.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/terminology/2026-05-19-paa-status-claim-rules.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/terminology/2026-05-19-paa-architecture-anti-patterns.md`

### 2. Governed code vocabulary

The same distinctions must be represented in code using typed values.

Examples:
- `AlignmentState = Literal["aligned", "hybrid", "legacy"]`
- `ImplementationState = Literal["defined", "scaffolded", "partially_implemented", "implemented"]`
- `ValidationState = Literal["not_validated", "lint_clean", "unit_validated", "proof_validated"]`
- `ComponentKind = Literal["service", "repository", "policy", "adapter", "projection", "runtime_hub"]`

### 3. Governed component metadata

Major architectural elements should expose structured metadata that makes the doc vocabulary testable in code.

Minimal shape:
- component name
- component kind
- alignment classification
- owned responsibilities
- explicit non-ownership

### 4. Verification tooling

Use:
- `basedpyright` for static type and protocol enforcement
- custom repo-local checks for doc-to-code consistency where required

## Minimum First Slice

The first implementation slice should stay narrow and high-value.

### Step 1. Add `basedpyright` config

Add repo configuration for `basedpyright` with an initially narrow scope.

Recommended initial scope:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-producer/src`

Do not attempt whole-repo strictness immediately.

### Step 2. Add a governed vocabulary module

Recommended target:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/governance/language.py`

Expected contents:
- alignment-state literals
- implementation-state literals
- validation-state literals
- component-kind literals
- possibly lifecycle-stage literals if helpful

### Step 3. Add governed component metadata model

Recommended target:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/governance/component_metadata.py`

Expected contents:
- metadata dataclass or typed model
- validation helpers for allowed values

### Step 4. Apply the model to one vertical slice

Recommended first slice:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/workflow_lifecycle/`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/execution_package_resolution/`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/repositories/implementation_plan/`

Reason:
- these are already governed components
- they have clear contracts
- they are central enough to prove the method

### Step 5. Add a doc-to-code consistency checker

This checker should stay small at first.

Initial checks:
- doc `Component:` name maps to declared code metadata
- declared component kind is one of the governed values
- declared alignment state is one of the governed values
- major governed modules expose metadata where required

This checker is the bridge between:
- header governance
- language governance
- code truth

## What This Enables

Once the governed vocabulary exists in code, the repo gains new guarantees.

Examples:
- a module cannot silently return ad hoc status values when a governed `Literal` is required
- a repository implementation must satisfy the repository protocol cleanly
- a service cannot claim a governed component kind in metadata if that kind is invalid
- docs and code can refer to the same governed concept names rather than loose prose approximations

## What This Does Not Solve

This does not automatically prove:
- that a module is well designed
- that prose claims are all semantically correct
- that a runtime hub has been decomposed simply because metadata exists

That still requires:
- architecture review
- language governance
- anti-pattern detection
- bounded remediation planning

## Recommended Implementation Order

1. `basedpyright` repo config
2. governed vocabulary module
3. governed component metadata model
4. first vertical slice annotations
5. doc-to-code consistency checker
6. optional CI and pre-commit integration after the first slice is stable

## Recommendation

Proceed with the first slice rather than broad repo-wide typing.

The best next implementation task after this note is:
- add the governed vocabulary module
- add `basedpyright` config
- apply both to `WorkflowLifecycleService`, `ExecutionPackageResolutionService`, and `ImplementationPlanRepository`

That is the smallest slice that turns language governance into code-truth enforcement.