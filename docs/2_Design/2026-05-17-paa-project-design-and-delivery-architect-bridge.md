# PAA Project Design And Delivery Architect Bridge

Date: 2026-05-17

## Purpose

Make explicit the missing bridge between:
- reviewed producer-side authority
and:
- consumer-side coder-agent implementation briefing

This note exists because the current PAA methodology already models:
- System Design
- Component Design
- producer-side derivation
- coder briefing

But it did not yet explicitly model the step we just had to perform in practice:
- derive an implementation plan from a component spec and an active slice package before final coder briefing

That step is not optional.
Without it, there is no real software engineering bridge from abstract design to executable coding work.

## Core Decision

`Implementation-plan derivation` is now a first-class PAA process step.

It belongs to:
- `Project Design`

Its primary role owner is:
- `Delivery Architect`

It sits between:
- producer-side reviewed slice authority
and:
- final coder-agent execution briefing

## Why This Step Must Be Explicit

System Design and Component Design are not enough on their own to launch a coding run.

A coder agent still needs a derived implementation plan that answers:
- what concrete code artifacts will be built in this consumer context?
- what files or modules are in scope?
- what sequence should implementation follow?
- what verification surfaces are required?
- what consumer-side stack particulars shape the slice?

That is the work of `Project Design`.

In the current PAA cycle, we had to perform this step manually to prepare for implementation of:
- `Component Design Planning Service`

That proved the step exists whether or not the methodology names it.

## Role Owner

The right named owner for this step is:
- `Delivery Architect`

Why:
- `Authority Architect` owns the producer-side authority package and reviewed design authority
- `Delivery Architect` owns the consumer-side translation from approved authority into an executable implementation plan for the target runtime and stack

This role split is especially important when the same authority package may be consumed by different implementation environments, for example:
- Python consumer
- .NET consumer

The upstream authority package may stay stable while the implementation plan changes by consumer context.

## Architectural Placement

This bridge spans producer and consumer concerns.

### Producer-side inputs
- reviewed system design
- component specs
- active `DesignPackage`
- approved component and code-artifact taxonomy
- approved slice scope and verification obligations

### Consumer-side inputs
- implementation language and platform
- installed execution package
- local project structure
- available runtime adapters
- stack-specific testing conventions
- target build/deployment host assumptions

### Consumer-side outputs
- implementation plan
- scoped code-artifact targets for this consumer
- file/module touch plan
- sequencing and dependency constraints
- verification and proving plan
- final coder-brief inputs

## Relationship To Project Design

The glossary already defines `Project Design` as the phase that converts component designs into an executable development plan.

This note sharpens that definition:

`Project Design` includes implementation-plan derivation.

That means Project Design is not only:
- schedule planning
- dependency sequencing
- milestone mapping

It also includes:
- converting one approved component slice into a concrete, consumer-specific construction plan that a coder agent can execute

## Relationship To Producer Derivation

The current `Producer Derivation Subsystem` remains valid.
It owns the producer-side path from reviewed design authority toward derived execution artifacts.

But the system now needs to distinguish two different derivation layers:

### 1. Producer-side authority derivation
Transforms:
- reviewed design authority

into:
- slice packages
- draft briefs
- governed authority states
- packet-ready authority artifacts

### 2. Consumer-side implementation-plan derivation
Transforms:
- approved slice authority

into:
- concrete implementation plan for the target consumer stack
- final coder-agent execution briefing inputs

Important rule:
- producer-side derivation should not pretend consumer-specific implementation planning is unnecessary
- consumer-side implementation planning should not invent authority outside the approved slice package

## Consumer-Side Variation Principle

Implementation-plan derivation is intentionally consumer-aware.

Why:
- one authority package may be implemented in different target stacks
- the same component role may become different code artifacts depending on the consumer

Examples:
- a Python consumer may produce:
  - module package layout
  - dataclasses or typed records
  - `unittest` or `pytest` verification surfaces
- a .NET consumer may produce:
  - namespace/project layout
  - interfaces + concrete classes
  - xUnit/NUnit/MSTest verification surfaces

So the methodology must support:
- stable upstream authority
- variable downstream implementation plans

That is a core reason this step belongs at the consumer-side `Delivery Architect` layer.

## Required Outputs Of Implementation-Plan Derivation

At minimum, this step must produce:
- implementation target selection for the consumer stack
- concrete code-artifact set
- allowed touch surfaces
- protected seams and anti-goals
- dependency-aware build sequence
- proving and verification plan
- final coder-brief assembly inputs

If those outputs do not exist, coder briefing is not complete.

## Method Rule

From this point forward:
- coder briefing should be treated as downstream from implementation-plan derivation
- implementation-plan derivation should be treated as downstream from reviewed component specs and slice authority

The process chain is now:
- `System Design -> Component Design -> Project Design / Implementation-Plan Derivation -> Coder Briefing -> Coding Run`

## Tooling Direction

Target end state:
- implementation-plan derivation is synthesized automatically from:
  - component spec
  - active slice package
  - consumer execution context

Intermediary acceptable state:
- `Authority Architect` and `Delivery Architect` perform the step manually with tool support

That tool support should eventually help with:
- stack-specific artifact selection
- target surface resolution
- verification-surface derivation
- build-sequence derivation
- coder-brief assembly inputs

## Immediate Method Correction

The current PAA methodology should now explicitly include:
1. producer-side reviewed authority and slice packaging
2. consumer-side implementation-plan derivation under `Project Design`
3. coder briefing from that implementation plan

That closes the gap we just proved in practice.
