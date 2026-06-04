# Traceability Module Audit

Date: 2026-06-04

## Scope

This audit classifies:

- `packages/paa-core/src/paa_core/traceability.py`

It does **not** change `packages/paa-core/src/paa_core/db.py`.

## Current State

`packages/paa-core/src/paa_core/traceability.py` is a small reporting/query helper backed by the DB projection view:

- `paa.v_work_item_full_chain_traceability`

It currently exposes one function:

- `full_chain_rows(project_slug, issue_number=None, db_profile=None)`

The module is not a wrapper. It contains real behavior:

- builds a reporting query
- executes it through `paa_core.db`
- normalizes rows into a response shape for higher-level reporting use

## Usage Audit

As of this audit:

- there are no active code imports of `paa_core.traceability`
- there are no active code call sites of `full_chain_rows(...)`
- the module is still referenced in planning and design docs as a canonical reporting helper

So the module is:

- **real**, because it owns actual reporting behavior
- **currently dormant**, because no live code path imports it today

## Classification Decision

`packages/paa-core/src/paa_core/traceability.py` should remain a **permitted canonical module** for now.

It should **not** be deleted as dead residue, because it is not a compatibility shim and it still represents a legitimate reporting/query ownership point.

It should also **not** be moved during this pass, because there is no active caller forcing a better package boundary yet.

## Deferred Placement Decision

If or when traceability/reporting becomes a broader active subsystem, the preferred future homes are:

1. `paa_core.application.reporting`
2. `paa_core.runtime.reporting`
3. a dedicated `paa_core.reporting`

Do not move it speculatively.

## Immediate Rule

For now:

- keep `packages/paa-core/src/paa_core/traceability.py`
- do not treat it as wrapper residue
- do not fold it into the `db.py` cleanup slice
- revisit only when a real reporting package is being built or when new callers appear
