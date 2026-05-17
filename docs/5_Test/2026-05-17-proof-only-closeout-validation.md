# Proof-Only Closeout Validation

Date: 2026-05-17
Repo: `/Users/billyweisberg/Repos/billyweisberg/paa-platform`
Proof slice:
- package: `paa-stage1-2026-05-16-component-design-planning-service`
- brief: `paa-coder-2026-05-16-component-design-planning-service-governed-draft`
- issue: `9002`
- proof PR linkage: `9001`

## Goal
Validate that PAA can support a governed proof-only terminal path for a validation slice without borrowing live GitHub merge / issue-close semantics.

## What was implemented

### 1. Proof-only execution mode became real authority
The Stage 1 design package now carries:
- `authority_context.execution_mode = proof_only`

The Stage 1 package schema and package materialization flow were updated so this is a first-class persisted authority field rather than an ad hoc extension.

### 2. TechLead closeout now branches intentionally on proof mode
`paa_consumer.techlead.closeout_qa_pass` now:
- detects `proof_only` execution mode from the persisted design package
- allows QA-pass closeout without requiring merged PR or closed issue
- records a distinct acceptance decision:
  - `proof_only_closed`
- emits a distinct TechLead decision packet shape:
  - `decision_type = proof_only_close_slice`
  - `lineage_action = proof_only_closed`
- preserves queue hygiene by acknowledging the QA packet and the self-addressed terminal decision packet when sent

### 3. Reporting / projection distinction was added
The DB acceptance-decision enum now includes:
- `proof_only_closed`

The full-chain reporting view was updated so proof-only terminal slices can remain distinct from live accepted / merged slices.

### 4. Installed consumer runtime was refreshed
The repo-local installed consumer runtime under `.codex/paa/` was updated after the source changes so wrapper commands match the final proof-only runtime behavior.

## Validation sequence

### A. Schema + DB update
Applied migration:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/012-step12-proof-only-closeout.sql`

Result:
- `proof_only_closed` added to `paa.acceptance_decision`
- reporting view recreated

### B. Persist proof-only design package authority
Re-ran:
- `paa_producer derive-design-package`

Result:
- persisted package now includes `execution_mode = proof_only`
- design package metadata now records:
  - `execution_mode = proof_only`
  - `proof_slice = true`

### C. Execute proof-only closeout from current source
Ran from current source tree:
- `paa_consumer techlead-closeout-qa-pass ... --send-decision --ack-qa-packet`

Result:
- `ok = true`
- `execution_mode = proof_only`
- `closeout_mode = proof_only`
- passing QA packet acknowledged
- self-addressed terminal decision packet acknowledged

Decision packet produced:
- `.project/data/paa/reports/techlead-decision.issue9002.proof-only-closed.json`
- `.project/data/paa/reports/techlead-decision.issue9002.proof-only-closed.md`

### D. Persist durable DB terminal record
Validated in DB:
- latest `paa.acceptance_events` row for issue `9002` shows:
  - `decision = proof_only_closed`
  - `metadata_json.closeout_mode = proof_only`

### E. Clean stale proof queue residue
Two duplicate stale `architect_cycle_packet`s for the same proof slice were still sitting on `fractal-core-python` from the earlier proof run.

These were explicitly claimed and acknowledged as stale proof residue.

Result:
- `fractal-core-python` queue drained to `0`
- terminal proof state no longer competed with stale upstream authorization packets

### F. Validate operator-facing lineage / status
Validated with repo-local installed wrapper:
- `paa-consumer techlead-lineage ...`

Result:
- `workflow_stage = proof_only_closed`
- `lineage.lineage_state = closed`
- `lineage.latest_lineage_action = proof_only_closed`
- `recommended_actions = []`
- `unattended_safe = true`

This is the key operator-facing proof that the proof-only terminal path is now governed and visible.

## Final result
Validated as `GO`:
- `QA Pass -> Proof-Only Closeout`
- `Proof-Only Closeout -> Durable Acceptance Event`
- `Proof-Only Closeout -> Queue Hygiene`
- `Proof-Only Closeout -> Terminal Lineage View`

Not validated in this run:
- live GitHub-backed closeout
- merged PR / closed issue delivery closeout

That remains a separate optional proof.

## Important caveat
The DB full-chain reporting view now shows:
- `acceptance_decision = proof_only_closed`

But for this proof slice it still reports:
- `full_chain_state = design_packaged`

This does **not** mean proof-only closeout failed.
It means the older packet-compilation / evidence-linkage surfaces for this slice are still not rich enough to satisfy the view's stricter full-chain rollup cases.

So the current state is:
- proof-only terminal governance is real and validated
- the broad one-row traceability rollup still has a separate follow-on refinement opportunity

## Decision
Proof-only closeout is now implemented and validated as a first-class governed path.

A separate live GitHub-backed closeout proof is now optional rather than required for this proof slice.
