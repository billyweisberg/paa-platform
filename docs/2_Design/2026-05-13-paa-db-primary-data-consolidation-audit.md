# PAA DB-Primary Data Consolidation Audit

Date: 2026-05-13

## Purpose

Apply a stricter DB-primary test to the current PAA data surfaces.

This note answers one question:
- what is currently outside the DB that should be moved into the DB, and what should remain outside the DB only for a technical reason

This is intentionally stricter than the earlier schema/data surface audit.

The default assumption for this note is:
- if a surface carries operational truth, recovery-critical state, transition state, or execution history, it belongs in the DB unless there is a strong technical reason not to do so

## Related Notes

Read alongside:
- `docs/2_Design/2026-05-13-paa-schema-and-data-surface-audit.md`
- `docs/2_Design/2026-05-13-paa-runtime-consolidation-design-correction.md`
- `docs/2_Design/2026-05-13-paa-v2-component-relationships.md`
- `docs/2_Design/2026-05-13-paa-system-component-diagram-v2.md`
- `docs/2_Design/2026-05-12-paa-handoff-execution-contract.md`

## DB-Primary Rule

For PAA, the DB should be primary for:
- current workflow truth
- transition history
- execution history
- claim and lease state
- acceptance and closeout state
- installation and package registration state
- traceability and reporting state
- structured operational evidence metadata

Files should remain outside the DB only when they are one of these:
1. source-controlled contract definitions
2. installable package artifacts required as local runtime inputs
3. Git-managed code and worktree content
4. bulky or append-only logs where the DB should store only summaries or indexes
5. human-readable exports that are projections of DB truth rather than the truth itself

## Current Out-Of-DB Surfaces That Must Move Into The DB

### 1. Current workflow-state interpretation derived from repo-local report artifacts

Current out-of-DB surfaces:
- `.project/data/paa/reports/techlead-status-report.json`
- repo-local result and decision report JSON used to reconstruct current state
- queue-preview plus report-file driven lineage/status inference in consumer runtime

Why this must move:
- current owner and workflow stage are primary operational truth
- current workflow truth cannot depend on whether a JSON report file exists on disk

Current DB support already available:
- `paa.work_items`
- `paa.handoffs`
- `paa.queue_messages`
- `paa.acceptance_events`
- `paa.automation_runs`
- `paa.v_work_item_full_chain_traceability`

Required correction:
- move authoritative current workflow state into a dedicated DB-backed workflow-state model
- report JSON becomes projection only

Likely DB target:
- new `paa.workflow_states`
- new `paa.workflow_transitions`
- or an equivalent normalized state machine built on top of `work_items` plus transition rows

### 2. Queue claim state under `.project/data/paa/claims/`

Current out-of-DB surface:
- `.project/data/paa/claims/*.json`
- generated and read from `packages/paa-core/src/paa_core/handoff_runtime.py`

Why this must move:
- claims are not merely local cache
- claims determine whether a source packet is still open, already claimed, or safe to ack
- that is operational truth for the handoff lifecycle

Current DB support already available:
- `paa.handoffs.status`
- `paa.queue_messages.status`
- `claimed_at`, `acknowledged_at`

Required correction:
- claims must become DB-backed leases or claim records
- file-backed claim JSON must stop being the primary claim source

Likely DB target:
- new `paa.queue_claims`
- or a more complete lease model extending `paa.queue_messages` and `paa.handoffs`

### 3. Queue runtime durable fallback state under `.project/data/paa/queue-state/`

Current out-of-DB surface:
- `.project/data/paa/queue-state/fractal-core-handoff/`

Why this must move:
- this directory is being used as durable queue runtime state
- durable queue runtime state belongs in DB, not in a repo-local fallback directory

Required correction:
- DB must own durable queue runtime state
- any repo-local queue-state directory should be reduced to transient cache or be removed entirely

Likely DB target:
- queue lease / cursor / recovery state tables associated with queue message lifecycle

### 4. Structured transition artifacts in `.project/data/paa/reports/*.json`

Current out-of-DB surfaces include:
- `techlead-assignment.*.json`
- `worker-result.*.json`
- `delivery-review.*.json`
- `qa-verification.*.json`
- `techlead-decision.*.json`
- `role-result-input.*.json`

Why this must move:
- these files carry structured transition inputs and outputs
- if the runtime needs them to understand what happened, they are too important to exist only as repo-local files

Current DB support already available:
- `paa.queue_messages.payload_json`
- `paa.handoffs`
- `paa.acceptance_events`
- `paa.evidence`
- `paa.automation_runs`

Required correction:
- every structured transition artifact must have a DB-backed canonical row representation
- files may remain as exports or inspection artifacts only

Likely DB target:
- queue packet payloads remain in `paa.queue_messages.payload_json`
- structured role input may need a new table such as `paa.transition_inputs`
- evidence references remain in `paa.evidence`

### 5. Automation run summaries and meaningful event metadata in file-only logs

Current out-of-DB surfaces:
- `.project/data/paa/logs/automations/*/summary.json`
- `.project/data/paa/logs/automations/*/events.jsonl`

Why this must move, at least partially:
- a run's identity, status, role, issue, package/brief context, and phase outcomes are operational history
- those fields belong in DB queryable form
- only the raw append-only log stream has a strong case to remain file-based

Current DB support already available:
- `paa.automation_runs`

Required correction:
- promote structured run summary fields and major events into DB-backed rows
- keep file log streams only as raw evidence/log storage if needed

Likely DB target:
- existing `paa.automation_runs`
- new `paa.automation_run_events`

### 6. Automation memory used for operational recovery

Current out-of-DB surfaces:
- `.project/data/paa/automation-memory/*.md`

Why this must move, if it affects recovery:
- if automation memory is used to recover the current state of a slice, it is carrying operational truth
- operational truth must not live in model-written markdown memory files

Required correction:
- any structured facts currently depended upon from automation memory must move into DB-backed runtime state
- markdown memory may remain only for operator narrative, notes, or debugging context

Likely DB target:
- `paa.automation_runs`
- `paa.workflow_states`
- `paa.workflow_transitions`

### 7. Installed package installation state and current-install registration

Current out-of-DB surfaces:
- `.project/data/paa/authority/current/package-metadata.json`
- repo-local install metadata under `.codex/paa/install-metadata.json`

Why this must move, at least in part:
- which package version is installed and active is operational truth
- that should be queryable in DB, not only recoverable from local JSON files

Required correction:
- local metadata files may remain as installed artifacts
- but DB must record active installed execution package registration for each consumer repo / project

Likely DB target:
- new `paa.execution_package_installs`
- or an extension of `paa.authority_versions` with install registration records

### 8. Overlay application state currently stored only in overlay files

Current out-of-DB surfaces:
- `.project/data/paa/authority/current/overlays/.../overlay-metadata.json`
- `.project/data/paa/authority/current/overlays/.../manifest-task.json`
- fixture summary JSON generated during pilot overlay install flows

Why this must move, at least in part:
- if overlays alter authorized execution-time truth, their application history and current activation state are operational truth
- overlay activation should not be discoverable only from local JSON files

Current DB support already available:
- `paa.design_packages`
- `paa.coder_run_briefs`
- `paa.coder_brief_sequence_states`
- `paa.work_items`

Required correction:
- overlay application and removal must be reflected in DB-backed install/activation records
- file overlay artifacts may remain as package content only

Likely DB target:
- new `paa.execution_package_overlays`

## Current Out-Of-DB Surfaces That May Stay Outside The DB For Technical Reasons

These are the exceptions.
They stay outside the DB not because they are unimportant, but because the DB is the wrong storage medium for them.

### 1. Canonical JSON schema files in `paa-platform/schemas/`

Examples:
- `schemas/handoff-packets/*.schema.json`
- `schemas/authority-package/*.schema.json`
- `schemas/runtime-records/*.schema.json`

Why they stay outside the DB:
- these are source-controlled contract definitions
- they need normal code review, diffing, versioning, and packaging
- they are closer to code/contracts than runtime state

DB requirement that still applies:
- the DB may store which schema version was used or referenced by a run or packet
- but not replace the repo as the canonical source of schema definitions

### 2. Installed execution package artifact files themselves

Examples:
- `.project/data/paa/authority/current/authority/*.json`
- `.project/data/paa/authority/current/artifacts/*.json`
- `.project/data/paa/authority/current/docs/*`

Why they stay outside the DB:
- these are local installed runtime inputs
- the consumer runtime needs a filesystem package surface to execute against
- docs bundles and JSON package artifacts are naturally installable files

DB requirement that still applies:
- DB should register which installed execution package version is active
- DB should track overlay activation
- DB should track provenance and install history

### 3. Git worktrees and checked-out code surfaces

Examples:
- repo-local role worktrees
- checked-out branches
- actual code files in worktrees

Why they stay outside the DB:
- Git already owns this content
- the DB should record metadata about worktree ownership or status if needed, not the checked-out source tree itself

### 4. Raw append-only automation log streams

Examples:
- `events.jsonl`
- `stdout.log`
- `stderr.log`

Why they may stay outside the DB:
- these are bulky, append-only, and operationally closer to log files than relational state
- storing every raw line in Postgres is usually a poor fit

DB requirement that still applies:
- major run metadata and structured event summaries should still be persisted in DB
- the DB should point to or summarize the raw logs

### 5. Human-readable markdown exports

Examples:
- `*.md` report companions under `.project/data/paa/reports/`

Why they may stay outside the DB:
- markdown reports are presentation/export artifacts
- they are useful for human review but should be generated from DB-backed state and structured JSON, not treated as truth

## Surfaces That Should Be Demoted Rather Than Deleted

Some file surfaces should remain, but only as secondary exports or local convenience views.

### Report JSON files

Examples:
- `techlead-assignment.*.json`
- `worker-result.*.json`
- `qa-verification.*.json`
- `techlead-status-report.json`

Correct role after consolidation:
- human-inspectable export
- debug artifact
- reproducible projection

Incorrect role after consolidation:
- canonical transition record
- primary workflow-state source
- sole source of structured role-return state

### Automation memory markdown

Correct role after consolidation:
- optional narrative notes
- operator debugging aid

Incorrect role after consolidation:
- recovery-critical state
- authoritative slice memory

### Overlay metadata files

Correct role after consolidation:
- installed package artifact
- local inspection view

Incorrect role after consolidation:
- sole source of overlay activation truth

## What Must Become Explicitly DB-Backed Next

If the system is serious about the DB being primary, these are the next mandatory DB-backed capabilities:

1. `workflow_states`
- one authoritative current state row per active slice

2. `workflow_transitions`
- append-only transition history with source packet and target owner/stage

3. `queue_claims` or equivalent lease model
- claim identity, claimant role/agent, lease timestamps, ack outcome

4. `automation_run_events`
- structured run milestones and outcomes

5. `execution_package_installs`
- what package/version is installed and active in each consumer repo

6. `execution_package_overlays`
- which overlays are applied, when, and to which installed package

## Existing DB Surfaces That Should Be Used More Aggressively

The following DB tables already exist and should absorb more of the runtime truth burden:
- `paa.handoffs`
- `paa.queue_messages`
- `paa.automation_runs`
- `paa.acceptance_events`
- `paa.design_packages`
- `paa.coder_run_briefs`
- `paa.coder_brief_sequence_states`
- `paa.evidence`
- `paa.work_items`
- `paa.execution_records`

## Hard Design Conclusion

The current mess did not happen because files exist.
It happened because too many **stateful** things were allowed to remain file-primary when they should have been DB-primary.

The items that must move into the DB are the ones carrying:
- workflow truth
- claim truth
- transition truth
- install activation truth
- structured run truth

The items that may remain outside the DB are the ones that are fundamentally:
- source-controlled contracts
- installable local package artifacts
- Git worktrees
- raw log streams
- human-readable exports

That is the stricter rule we should apply from here forward.
