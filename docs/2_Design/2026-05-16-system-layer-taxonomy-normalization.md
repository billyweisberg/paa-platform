# System Layer Taxonomy Normalization

Date: 2026-05-16

## Purpose

Resolve the mismatch between:
- the preferred layered architecture vocabulary
- the persisted `paa.components.system_layer` enum

This run closes the follow-on finding discovered during proof-slice package materialization.

## Problem

The proof slice for `Component Design Planning Service` belongs to:
- `domain-services`

But the persisted `paa.system_layer` enum still reflected the older Baby-7 era taxonomy:
- `host-adapter`
- `model-core`
- `policy`
- `hierarchy`
- `diagnostics`
- `contract`
- `integration`
- `test`
- `docs`

That forced the proof slice to be stored temporarily as:
- `model-core`

with the intended architectural placement only recorded in metadata.

## Decision

Do not keep translating the layered architecture back into the older enum.

Instead:
- extend `paa.system_layer` so it can directly represent the preferred layered architecture
- preserve the old values for backward compatibility with older component rows

## Added Layer Values

The system layer enum now also supports:
- `domain-core`
- `domain-services`
- `application-orchestration`
- `infrastructure-ports`
- `infrastructure-adapters`
- `host-surfaces`

## Proof-Slice Update

The persisted `Component Design Planning Service` component row was updated from:
- `model-core`

to:
- `domain-services`

This removes the lossy translation from the proof slice and keeps the DB closer to the new architecture.

## Compatibility Rule

Older component rows may continue to use the legacy taxonomy.

New layered-architecture components may use the layered vocabulary directly.

This is a compatibility extension, not a forced backfill of all older component records.

## Implementation

Migration:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/011-step11-layered-system-layer-normalization.sql`

## Outcome

The earlier finding is now resolved:
- the DB no longer forces `domain-services` components to masquerade as `model-core`

This reduces friction for:
- future Stratum 2 service slices
- component catalog authoring
- brief derivation and reporting
- later migration of more layered-architecture components into the DB
