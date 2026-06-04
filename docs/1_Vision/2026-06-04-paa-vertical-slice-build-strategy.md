Title: PAA Vertical Slice Build Strategy
Doc-ID: paa-vertical-slice-build-strategy
Doc-Type: vision
Status: active
Lifecycle-Stage: vision
Created: 2026-06-04
Last-Edited: 2026-06-04
Author: Billy Weisberg
Repo: paa-platform
Component: PAAVerticalSliceBuildStrategy
Domain: build-strategy
Keywords: paa, python, build strategy, vertical slice, cli, api, services, data layer, methodology execution
Depends-On: 2026-06-04-paa-python-north-star-architecture.md, 2026-06-04-paa-python-phase-ordered-progress-tree.md, 2026-06-04-paa-python-build-sequence-from-structure.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-07-01
Owners:
Expires:
Issue:
PR:
Authority-Source:
Implementation-Status: in-progress
Summary: Defines the vertical-slice build strategy for constructing the Python PAA system in dependency order and proving each slice end to end through paa.

# PAA Vertical Slice Build Strategy

## Vision Marker

This document is a Vision-layer authority document.

It defines how the Python PAA system should be built from this point forward.

## Core Statement

The Python PAA system should be built in small vertical slices.

The unit of progress is not:
- a package cleanup
- a broad subsystem refactor
- a horizontal layer-only rewrite

The unit of progress is:
- one smallest meaningful governed capability
- implemented through the full stack
- proven end to end through `paa`

## Slice Selection Rule

A slice is chosen based on:
- dependency order
- PAA workflow and methodology sequence
- current `MethodologyExecution` position
- the smallest group of functionality that produces a real usable system behavior

A slice should be as small as possible while still being a real capability.

## Required Slice Sub-Sequence

Every slice should be implemented in this exact order:

1. data layer
2. domain/app logic
3. API
4. CLI
5. end-to-end CLI proof

That means:
- persistence and resource access first
- then service and orchestration behavior
- then transport exposure
- then operator surface
- then proof through the real system path

## Canonical Slice Flow

```text
data layer
  -> services/app logic
  -> api
  -> cli
  -> end-to-end test through paa
```

## Data Layer Rule

For the selected slice, build or normalize:
- repository operations
- schema-facing behavior
- persistent records needed by the capability
- any required extraction from `db.py`

Constraint:
- do not extract from `db.py` speculatively
- only extract what the current slice needs
- only when the destination ownership is already defined by the North Star structure

## Domain/App Logic Rule

For the selected slice, build:
- service behavior
- orchestration logic
- business rules
- methodology-pointer-aware behavior where needed

Constraint:
- this layer owns meaning and behavior
- not the API
- not the CLI

## API Rule

For the selected slice, expose the same behavior through the HTTP path.

Constraint:
- the API is a transport surface only
- controllers do not own business logic

## CLI Rule

For the selected slice, expose the same behavior through `paa`.

Constraint:
- `paa` is the proof surface
- the CLI should exercise the same real system path, not a shortcut path

## End-To-End Proof Rule

Each slice is only considered complete when it is proven through the real command path:

```text
paa -> api -> services/app logic -> data layer
```

Preferred proof order:
1. CLI integration proof through `paa`
2. HTTP/API confirmation when useful
3. `basedpyright`
4. lint and compile checks

Helper-only unit tests are not the main proof for this strategy.

## System-Building Rule

By repeating this slice flow, we build the entire PAA system into one coherent system.

That means:
- each slice fills in the target structure already defined in the North Star architecture
- each slice leaves behind a real working path
- each slice reduces transitional residue instead of adding more of it
- over time, the entire system is assembled as one governed stack

## Relationship To The North Star

This strategy does not replace the North Star structure.
It is how we realize it.

The North Star defines:
- where things belong
- what the final structure is

This strategy defines:
- how we move toward that structure
- how we decide the next slice
- how we prove each slice is real

## Non-Negotiable Constraints

1. do not build by horizontal cleanup alone
2. do not choose slices by convenience only
3. do not add shortcuts that bypass the real stack
4. do not extract from `db.py` before the destination layer is real
5. do not move to the next slice until the current slice works through `paa`

## Practical Meaning

From here forward, implementation should sound like this:
- choose the smallest next governed capability
- build its data layer
- build its service/app logic
- expose it through the API
- expose it through `paa`
- prove it end to end
- then move to the next slice

That is how we will build the full PAA system.
