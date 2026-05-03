# 2026-05-03 Authority Architect Vs Delivery Architect

## Purpose

This note defines the explicit architectural role split required by the PAA migration.

The old single label `Architect` covered two different responsibilities:

- upstream authority design and publication
- downstream delivery acceptance and runtime progression

That ambiguity contributed directly to workflow drift, stale-workspace confusion, and responsibility bleed between producer-side and consumer-side control.

## Decision

PAA now recognizes two distinct architecture roles.

### Authority Architect

Side:
- producer side

Canonical repo:
- `appdev`

Primary responsibility:
- author, review, approve, and publish project authority and derivation inputs

Owns:
- authority task definitions
- source authority manifest
- source authority docs
- Stage 1 design packages
- dependency graph slices
- coder brief source artifacts
- authority publication decisions
- authority version advancement rules
- authoring stop conditions when no successor exists

Does not own:
- implementation execution in consumer repos
- QA verification execution
- PR merge acceptance in the consumer delivery loop

### Delivery Architect

Side:
- consumer side

Canonical repo:
- `fractal-core-python`

Primary responsibility:
- accept or reject verified implementation work against an installed authority package and the execution record

Owns:
- acceptance gate over `qa_verification_packet`
- merge or non-merge decision in the consumer repo
- runtime-loop progression after acceptance
- delivery-side fail-closed behavior when packet, readiness, CI, or scope state is invalid
- ensuring the consumer runtime is operating against an installed authority package rather than live producer continuity

Does not own:
- editing upstream authority content as part of routine acceptance
- inventing new authority tasks from runtime continuity
- patching producer-side authority publication logic during consumer acceptance runs

## Collaboration rule

The producer side defines what work exists.
The consumer side decides whether delivered implementation satisfied the currently installed authority package.

That means:
- Authority Architect produces authority and derivation truth
- Delivery Architect consumes published authority and governs acceptance

## Runtime implications

This role split implies:
- producer-side commands and docs belong in `paa-platform` + `appdev`
- delivery-side automations and runtime checks belong in `paa-platform` + `fractal-core-python`
- Delivery Architect must fail closed when installed authority is stale, missing, or inconsistent
- Authority Architect must not be embedded implicitly in consumer acceptance flows

## Migration effect

Any current automation, skill, or doc still using a single ambiguous `Architect` role should be treated as transitional until it is reclassified as either:
- Authority Architect
- Delivery Architect
