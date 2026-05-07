# Phase G Python Migration To `worker_result_packet`

## Goal

Move the Python lane from:

- `slice_result_packet`

to:

- `worker_result_packet`

without breaking the already-proven TechLead hub flow.

## Why migrate now

We have already proven:

- `worker_result_packet` contract
- schema/runtime validation
- producer compiler support
- TechLead runtime interpretation
- Delivery Architect bridge on the new packet-family model

That means the remaining question is no longer whether the generic worker lane is viable.
It is whether the Python lane should keep carrying a Python-specific result schema any longer.

## Migration policy

Use a controlled cutover, not a big-bang replacement.

Rules:

1. keep runtime acceptance for both packet families during transition
2. switch Python compile/return helpers to `worker_result_packet` first
3. keep TechLead interpretation compatible with both families during overlap
4. only retire `slice_result_packet` after one clean end-to-end Python round trip succeeds on the generic lane

## Recommended stages

### Stage G5

Switch the Python role-side bridge to emit `worker_result_packet` instead of `slice_result_packet`.

Scope:

- update `techlead-role-result-assist`
- update `techlead-role-return`
- update role-entry/manual command surfaces
- update the Python skill/prompt text

Keep:

- `materialize-slice-result-packet`
- runtime acceptance for `slice_result_packet`

Outcome:

- new Python bridge traffic uses `worker_result_packet`
- old historical/result compatibility remains intact

### Stage G6

Validate one clean Python generic-worker round trip.

Flow:

1. TechLead emits Python assignment
2. Python branch/worktree prepared
3. Python role-entry/result-assist surfaces point to `worker_result_packet`
4. Python role-return compiles and sends `worker_result_packet`
5. TechLead reads the returned packet as `techlead_dev_review_pending`
6. TechLead emits QA assignment from the generic worker result path

Acceptance:

- no fallback to `slice_result_packet` needed in the active bridge

### Stage G7

Demote `slice_result_packet` to legacy compatibility only.

Meaning:

- stop presenting it as the default Python result lane
- keep validator/runtime support for historical overlap
- keep old docs only where needed for migration notes

### Stage G8

Retirement decision.

Only after:

- generic Python worker round trip is stable
- traceability/reporting covers the new lane
- prompts/automation paths no longer teach `slice_result_packet`

Then decide whether to:

- keep `slice_result_packet` indefinitely as legacy read support
- or fully remove active compile/send surfaces

## Immediate next slice

The next implementation slice should be:

1. change the Python role bridge helpers to use `worker_result_packet`
2. keep `slice_result_packet` compiler/runtime support intact
3. run one controlled Python round trip on the generic worker lane

## Explicit non-goals

Do not do these in the first migration slice:

- remove `materialize-slice-result-packet`
- delete old schema support
- rewrite historical records
- change QA packet family
- change TechLead decision packet family

## Decision

Proceed with migration.

The generic worker lane is now mature enough that keeping Python permanently on
`slice_result_packet` would create more long-term inconsistency than short-term safety.
