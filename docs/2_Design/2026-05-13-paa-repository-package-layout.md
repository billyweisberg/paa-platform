# PAA Repository Package Layout

Date: 2026-05-13

## Purpose

Define the standard package layout for DAL repository code inside `paa-core`.

This note exists so repository implementations do not drift into inconsistent file shapes as more repositories are added.

## Standard Layout

Each repository gets its own package under:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/repositories/`

Example:
- `component_design/`

Each repository package should use this structure:
- `__init__.py`
- `contracts.py`
- `models.py`
- `postgres.py`

## File Responsibilities

### `contracts.py`
- repository interfaces / protocols only
- public method signatures
- no SQL
- no row mapping

### `models.py`
- DTOs / dataclasses / small read-model records used by the repository boundary
- no SQL
- no runtime business semantics

### `postgres.py`
- concrete Postgres-backed implementation
- SQL text
- row-to-model mapping
- DB helper usage

### `__init__.py`
- stable public exports for the repository package
- keeps caller imports consistent even if internal files evolve

## Optional Future Files

These are allowed only when the repository grows enough to justify them:
- `writes.py`
- `reads.py`
- `queries.py`
- `mappers.py`
- `fixtures.py`

But the default shape should remain the four-file layout above.

## Package Placement Rule

Shared repository code belongs in:
- `paa-core`

Not in:
- `paa-producer`
- `paa-consumer`

Those higher-level packages should depend on repository contracts and implementations from `paa-core`.

## Deployment Rule

This layout is chosen to support all three runtime topologies:
- producer-only install
- consumer-only install
- self-hosted combo install

The repository package layout must not assume only one of those modes.

## Current First Example

The first repository package following this layout is:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/repositories/component_design/`

## Leave-Off Marker

After this layout refactor, the next implementation slice to resume is:
- `ComponentDesignRepository` write path expansion

Specifically:
1. realization taxonomy upsert
2. realization instance create/update
3. coder brief realization target create/update

That is the next code step after the layout work.
