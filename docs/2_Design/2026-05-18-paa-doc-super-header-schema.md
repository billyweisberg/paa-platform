Title: PAA Doc Super Header Schema
Doc-ID: paa-doc-super-header-schema
Doc-Type: schema-note
Status: active
Lifecycle-Stage: design
Created: 2026-05-18
Last-Edited: 2026-05-18
Author: Billy Weisberg
Repo: paa-platform
Component: PaaDocHeaderSystem
Domain: doc-governance
Keywords: docs, headers, schema, metadata, indexing
Depends-On: 2026-05-18-paa-system-design-tables-method.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-06-15
Summary: Defines the strict super-header metadata contract for governed PAA markdown documents.

# PAA Doc Super Header Schema

## Status
Draft.

## Purpose

Define a strict, lightweight, header-only metadata schema for PAA design and planning documents.

The goal is to let tooling recover useful document context by reading only the first lines of a document instead of loading the entire body.

This is intended to improve:
- document discovery
- continuity across long-horizon work
- canonical-doc selection
- supersession handling
- context efficiency for agents and humans
- lintable doc governance

## Design Goals

The header system should be:
- strict
- short
- parseable without ambiguity
- easy to lint
- valuable even when only the header is loaded
- durable across many document types

The header system should not be:
- a prose summary substitute
- a full document database embedded in markdown
- flexible enough that every document invents its own fields

## Placement Rule

The super header must appear at the top of every governed markdown document.

### Header placement
- the header begins on line 1
- the header is a contiguous set of `Key: Value` lines
- the header ends at the first blank line
- the document body begins after that blank line

### Header read limit
Tooling should be able to recover the full header by reading only the first `40` lines.

## Format Rule

Each header field must use this exact form:

```text
Key: Value
```

Rules:
- one field per line
- no multiline values
- no YAML frontmatter
- no nested structures in v1
- list-like values use comma-separated strings
- empty allowed fields may be blank after the colon

Example:

```md
Title: Workflow Lifecycle Service Component Spec
Doc-ID: paa-workflow-lifecycle-service-component-spec
Doc-Type: component-spec
Status: active
Lifecycle-Stage: design
Created: 2026-05-17
Last-Edited: 2026-05-18
Author: Billy Weisberg
Repo: paa-platform
Component: WorkflowLifecycleService
Domain: workflow-lifecycle
Keywords: workflow, lifecycle, service, state, transition
Depends-On: 2026-05-17-workflow-lifecycle-service-pre-spec.md, 2026-05-13-workflow-state-machine-component-design.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-06-01
Summary: Defines the authoritative workflow transition service boundary for work-item lifecycle coordination.

# Workflow Lifecycle Service Component Spec
```

## Field Model

### Required fields
These must appear in every governed markdown document.

| Field | Purpose | Example |
|---|---|---|
| `Title` | Human-readable document title | `Workflow Lifecycle Service Component Spec` |
| `Doc-ID` | Stable machine-readable identifier | `paa-workflow-lifecycle-service-component-spec` |
| `Doc-Type` | Closed-set document type | `component-spec` |
| `Status` | Lifecycle/governance status | `draft` |
| `Lifecycle-Stage` | Process-stage classification | `design` |
| `Created` | Creation date | `2026-05-17` |
| `Last-Edited` | Last significant edit date | `2026-05-18` |
| `Author` | Primary document author | `Billy Weisberg` |
| `Repo` | Repo authority name | `paa-platform` |
| `Canonical` | Whether this is the primary current doc for its topic | `true` |
| `Summary` | One-sentence description | `Defines the workflow transition service boundary.` |

### Recommended fields
These should appear in most design and planning documents.

| Field | Purpose | Example |
|---|---|---|
| `Component` | Primary component or service | `WorkflowLifecycleService` |
| `Domain` | Broad subject area | `workflow-lifecycle` |
| `Keywords` | Lightweight discovery terms | `workflow, lifecycle, state, transition` |
| `Depends-On` | Direct referenced prerequisites | `2026-05-17-workflow-lifecycle-service-pre-spec.md` |
| `Supersedes` | Prior docs replaced by this one | `2026-05-13-old-workflow-design.md` |
| `Superseded-By` | Current replacement if this doc is obsolete | `2026-05-17-workflow-lifecycle-service-component-spec.md` |
| `Review-After` | Date when the doc should be reviewed again | `2026-06-01` |

### Optional fields
These are allowed when useful, but not required for v1.

| Field | Purpose | Example |
|---|---|---|
| `Owners` | Ongoing maintainers | `Billy Weisberg, Codex` |
| `Expires` | Date after which the doc should be treated as stale unless reviewed | `2026-07-01` |
| `Issue` | Related GitHub issue number or key | `#123` |
| `PR` | Related pull request | `#456` |
| `Authority-Source` | External authority source key | `tom-note-2026-05-14` |
| `Implementation-Status` | Narrower implementation note | `hybrid` |

## Field Semantics

### `Doc-ID`
`Doc-ID` is the most important machine key.

Rules:
- globally unique within the repo
- lowercase
- hyphen-separated
- stable across renames when possible
- should not include the date prefix unless the date is part of the conceptual identity

### `Doc-Type`
`Doc-Type` must use a closed enum in v1.

Allowed values:
- `design-note`
- `component-spec`
- `contract`
- `plan`
- `validation-note`
- `policy`
- `schema-note`
- `proof`
- `runbook`
- `glossary`
- `reference`

### `Status`
`Status` must use a closed enum in v1.

Allowed values:
- `draft`
- `active`
- `superseded`
- `archived`

### `Lifecycle-Stage`
`Lifecycle-Stage` must use a normalized enum aligned to the repo’s lifecycle-oriented docs structure.

Allowed values:
- `design`
- `plan`
- `build`
- `test`
- `deploy`
- `operate`
- `reference`

### `Canonical`
Allowed values:
- `true`
- `false`

Meaning:
- `true` means this is the primary current doc for its exact topic
- `false` means supporting, historical, or non-primary

### `Summary`
Rules:
- one sentence preferred
- maximum `200` characters in v1
- should tell a reader why the doc exists, not restate the title mechanically

## Parsing Rules

### Required parser behavior
A compliant parser must:
1. read from line 1 downward
2. parse contiguous `Key: Value` pairs
3. stop at the first blank line
4. reject malformed required header lines
5. preserve raw string values for comma-separated list fields before normalization

### Field normalization
The indexer/linter should normalize these fields:
- `Keywords` -> list of trimmed values
- `Depends-On` -> list of trimmed values
- `Supersedes` -> list of trimmed values
- `Superseded-By` -> list of trimmed values
- `Owners` -> list of trimmed values

## Validation Rules

### Required validation
The linter must check:
1. all required fields present
2. no duplicate required fields
3. required enums valid
4. date fields use `YYYY-MM-DD`
5. `Canonical` is exactly `true` or `false`
6. `Doc-ID` is unique in the repo index
7. header ends before line `40`
8. no unknown field names unless explicitly allowed by configuration

### Cross-document validation
The linter should also check:
1. `Superseded-By` references resolve to existing docs when non-empty
2. `Supersedes` references resolve when non-empty
3. `Depends-On` references resolve when they name repo-local docs
4. only one `Canonical: true` doc exists per exact `Doc-ID` topic family when such grouping is configured

## Initial Governance Rules

### Rule 1
All new docs in the governed PAA design/planning system should use the header.

### Rule 2
Docs without the header are still readable, but should be treated as legacy docs until upgraded.

### Rule 3
The indexer must tolerate legacy docs, but the linter should report them.

### Rule 4
The header is metadata, not body content.
It should stay short and not become a second abstract section.

## Why This Helps

This schema helps solve the actual continuity problem:
- agents and humans can find canonical docs without reading everything
- superseded docs can be filtered out early
- related docs can be discovered through header relationships
- context loading can become header-first instead of prose-first

## v1 Adoption Recommendation

Adopt this schema first in:
- `docs/2_Design`
- `docs/3_Plan`
- `docs/5_Test`
- other high-value PAA methodology and execution-governance docs

Then backfill the most active/canonical docs before attempting a full historical retrofit.

## Conclusion

The `PAA Doc Super Header` should become the standard document metadata contract for governed markdown docs.

It is intentionally strict because the value comes from:
- consistency
- fast parsing
- reliable indexing
- low-context navigation
