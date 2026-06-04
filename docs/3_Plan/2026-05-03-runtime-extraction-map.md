# 2026-05-03 Runtime Extraction Map

## Purpose
This document corrects an earlier false conclusion that several PAA runtime capabilities were still only designed but not implemented.

After checking the live code and the live `paa_dev` database, the accurate state is:
- the database-backed runtime exists
- packet compilation persistence exists
- coder-brief readiness materialization exists
- TechLead reporting and DB persistence exist
- queue and claim persistence exist

The real problem is not feature absence.
The real problem is that these capabilities are still spread across:
- `$HOME/.codex/skills`
- transitional authority repo copies
- hardcoded repo paths and mirror roots
- partially synchronized runtime state

This extraction map defines:
1. what runtime code already exists
2. where it lives now
3. where it should move in `paa-platform`
4. what config/path assumptions must be removed during the move

## Verified Live Runtime Capabilities
The following are confirmed live today:
- PAA database: `agenthub-mm-db` / `paa_dev` / `mmuser`
- live tables:
  - `paa.coder_run_briefs`
  - `paa.design_packages`
  - `paa.component_dependency_edges`
  - `paa.coder_brief_sequence_states`
  - `paa.automation_runs`
  - `paa.handoffs`
  - `paa.queue_messages`
  - `paa.evidence`
- live reporting view:
  - `paa.v_work_item_full_chain_traceability`
- live persisted packet compilation runs for issues `#101`, `#103`, `#106`, `#201`
- live persisted TechLead reports in `paa.automation_runs`

## Runtime Extraction Inventory

| Capability | Runtime Code Exists? | Current Live Location(s) | Current Role in System | Target `paa-platform` Home | Remove / Replace Assumptions |
| --- | --- | --- | --- | --- | --- |
| Authority manifest resolution and issue/task materialization | Yes | `<codex_home>/skills/fractal-core-authority/scripts/project_authority.py` and duplicate copies under `<producer_repo_root>/tools/codex-skills/fractal-core-authority/scripts/project_authority.py` and `<producer_repo_root>-authority-source/tools/codex-skills/fractal-core-authority/scripts/project_authority.py` | Resolve active task, sync issue, compile packets, write PAA rows | `packages/paa-core/src/paa_producer/authority_runtime.py` plus shared DB/path helpers in `packages/paa-core/src/paa_core/` | Remove hardcoded `~/.codex/authority/...`; remove fallback to `appdev-arch`; replace direct repo path guesses with producer config and installed authority package paths |
| Authority publication | Yes | `<codex_home>/skills/fractal-core-authority/scripts/publish_current.py`, `<producer_repo_root>/tools/codex-skills/fractal-core-authority/scripts/publish_current.py` | Publish current authority package / mirrors | Already partially moved to `packages/paa-core/src/paa_producer/publish.py`; continue by extracting remaining wrapper behavior | Remove repo-specific mirror fanout assumptions; replace with producer config-driven package publish and optional consumer install step |
| Coder-brief readiness materializer | Yes | `<codex_home>/skills/fractal-core-authority/scripts/materialize_coder_brief_readiness.py`; duplicate in `<producer_repo_root>-authority-source/tools/codex-skills/fractal-core-authority/scripts/materialize_coder_brief_readiness.py` | Compute and optionally persist readiness state and dependency status for coder briefs | `packages/paa-core/src/paa_core/readiness.py` for algorithm and DB access; producer/consumer entrypoints in `paa-producer` and `paa-consumer` | Remove direct docker/psql shell coupling from business logic; remove assumption that source briefs must come from ad hoc directories only; support producer artifacts and installed consumer packages via config |
| RabbitMQ handoff runtime and DB-backed queue trace persistence | Yes | `<codex_home>/skills/fractal-core-handoff-common/scripts/rabbitmq_handoff.py`; duplicate in `appdev` and `appdev-authority-source` skill copies | Queue check/claim/send/ack/requeue; persist handoff linkage into `paa.automation_runs`, `paa.handoffs`, `paa.queue_messages` | `packages/paa-core/src/paa_core/handoff_runtime.py` plus CLI surfaces in `paa-consumer` and shared runtime templates | Remove hardcoded RabbitMQ defaults as the only mode; replace queue names and state roots with consumer config; remove dependence on `$HOME/.codex/state` as primary claim root |
| TechLead report generation and DB persistence | Yes | `<codex_home>/skills/fractal-core-techlead/scripts/techlead_status.py` | Reconcile authority, queue state, GitHub state, automation visibility, traceability; persist report into `paa.automation_runs` | `packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services` with shared helpers in `paa-core`; schema under `schemas/runtime-records/` | Remove hardcoded `appdev-arch`; remove hardcoded paths to `~/.codex/authority`, `~/.codex/automations`, QA work dirs, and role workspace roots; drive entirely from consumer repo config and installed runtime |
| Inbox / claim workflow skill layer | Yes, but thin | Skill wrappers under `<codex_home>/skills/fractal-core-inbox/`, `<codex_home>/skills/fractal-core-queue-admin/`, `<codex_home>/skills/fractal-core-dev-result/`, `<codex_home>/skills/fractal-core-qa-review/`, `<codex_home>/skills/fractal-core-architect-handoff/` | Role-facing entrypoints over the shared queue and authority runtime | Repo-local templates under `templates/skills/` and `templates/automations/`; generated/installable payloads from `paa-platform` | Remove primary dependence on home-installed skills; treat these as install artifacts produced from `paa-platform` into repo-local `.codex/` |
| Packet schemas and reference examples | Yes | `<codex_home>/skills/fractal-core-handoff-common/references/` and duplicates under `appdev/tools/codex-skills/fractal-core-handoff/fractal-core-handoff-common/references/` | Validate and document `architect_cycle_packet`, `slice_result_packet`, `qa_verification_packet` | `schemas/handoff-packets/` and `templates/packet-examples/` inside `paa-platform` | Remove duplicated schema copies across skills and producer repos; keep one canonical platform source |
| Full-chain reporting view and proof queries | Yes | SQL docs under `<producer_repo_root>-authority-source/docs/architecture/tom-baby7-fractal-core/100-paa-single-slice-full-chain-proof-queries.sql`, `<producer_repo_root>-authority-source/docs/architecture/tom-baby7-fractal-core/102-paa-full-chain-reporting-view.sql`, `<producer_repo_root>-authority-source/docs/architecture/tom-baby7-fractal-core/98-paa-full-chain-proof-queries.sql` | DB reporting and proof queries for traceability | `migrations/` and `packages/paa-core/src/paa_core/sql/` in `paa-platform` | Remove assumption that reporting SQL lives only as architecture docs in transitional repos; promote to versioned platform-owned SQL assets |
| DB schema steps for control plane and knowledge graph | Yes | SQL docs in transitional authority/source trees (`54`/`55`/`60`/`77`/`86` and related notes) and live DB already applied | Define runtime schema for projects, work items, briefs, packages, dependencies, evidence, acceptance, reporting | `migrations/` in `paa-platform` with ordered migration plan and install/apply tooling | Remove reliance on docs-only SQL and historical repo copies as canonical migration source |

## Concrete Source-to-Target Moves

### Move 1: Shared DB and path helpers into `paa-core`
Move or extract logic from:
- `<codex_home>/skills/fractal-core-authority/scripts/project_authority.py`
- `<codex_home>/skills/fractal-core-authority/scripts/materialize_coder_brief_readiness.py`
- `<codex_home>/skills/fractal-core-handoff-common/scripts/rabbitmq_handoff.py`
- `<codex_home>/skills/fractal-core-techlead/scripts/techlead_status.py`

Into:
- `packages/paa-core/src/paa_core/db.py`
- `packages/paa-core/src/paa_core/runtime_paths.py`
- `packages/paa-core/src/paa_core/readiness.py`
- `packages/paa-core/src/paa_core/handoff_runtime.py`
- `packages/paa-core/src/paa_core/traceability.py`

### Move 2: Producer-side authority runtime into `paa-producer`
Move or wrap:
- task resolution
- issue sync/materialization
- packet shell compilation that belongs on producer side
- authority publication wrappers

Target:
- `packages/paa-core/src/paa_producer/authority_runtime.py`
- `packages/paa-core/src/paa_producer/publish.py`
- `packages/paa-core/src/paa_producer/cli_*.py` as the CLI grows

### Move 3: Consumer-side delivery/runtime into `paa-consumer`
Move or wrap:
- TechLead reporting
- queue/inbox operations
- packet send/ack flows
- consumer authority install/update and validation
- stale-workspace checks

Target:
- `packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services`
- `packages/paa-consumer/src/paa_consumer/inbox.py`
- `packages/paa-consumer/src/paa_consumer/runtime_guardrails.py`
- `packages/paa-consumer/src/paa_consumer/install_authority.py`

### Move 4: SQL migrations and reporting views into `paa-platform`
Move or codify:
- Step 1 / 2 / 3 / 4 / 5 DDL
- reporting views
- proof queries that should become supported diagnostics

Target:
- `migrations/postgres/`
- `packages/paa-core/src/paa_core/sql/`
- `docs/5_Test/` for proof-query validation guidance

## Hardcoded Assumptions to Remove

### Home-directory authority root
Current assumptions include:
- `~/.codex/authority/fractal-core-python/current/...`
- `~/.codex/automations/...`
- `~/.codex/skills/...`

Replace with:
- repo-local install roots under `.codex/paa/`
- repo-local automations/skills under `.codex/`
- authority package install root under `.project/data/paa/authority/current/`

### Hardcoded producer repo path
Current assumptions include direct references to:
- `appdev-arch`
- `appdev-authority-source`

Replace with:
- producer repo config in `.codex/paa/project-config.json`
- explicit producer `repo_root`
- explicit source artifact / manifest paths from config

### Hardcoded consumer role workspace paths
Current assumptions include direct references to:
- `<consumer_repo_root>-automation-dev-source`
- `<consumer_repo_root>-automation-qa-source`

Replace with:
- canonical consumer repo config
- disposable role workspace policy
- stale-workspace detection instead of role-workspace identity as truth

### Hardcoded DB container and direct `docker exec psql`
Current assumptions include:
- `agenthub-mm-db`
- `paa_dev`
- `mmuser`
- direct shell invocation of `docker exec ... psql`

Replace with:
- shared DB config contract in producer/consumer config
- one `paa-core` DB adapter layer
- keep `docker exec psql` as a backend only if necessary, not the business-logic interface

### Mirror fanout assumptions
Current assumptions include multi-root mirror lookups across:
- producer repo-local `.codex/runtime/...`
- role-workspace `.codex/runtime/...`
- home `.codex/authority/...`

Replace with:
- producer publishes package once
- consumer installs package once
- repo-local runtime reads from installed package under `.project/data/paa/authority/current/`

## What Is Not a Gap Anymore
The following should no longer be described as missing implementation:
- coder-brief readiness persistence
- design package persistence
- dependency edge persistence
- sequence-state persistence
- packet compilation persistence
- TechLead report generation
- TechLead DB persistence
- traceability reporting view

These exist today.
They are migration targets, not greenfield requirements.

## Actual Remaining Gaps
The real remaining gaps are:
1. `paa-platform` does not yet own the executable runtime code for these capabilities.
2. producer and consumer repos do not yet install/update these capabilities from `paa-platform`.
3. the live scripts still encode old path topology.
4. the live DB/runtime truth is not yet fully synchronized with the new canonical producer/consumer cutover.

## Recommended Next Extraction Order
1. Extract shared DB/path helpers into `paa-core`.
2. Extract `materialize_coder_brief_readiness.py` into `paa-core` and producer/consumer entrypoints.
3. Extract `techlead_status.py` into `paa-consumer` and remove old path hardcoding.
4. Extract `rabbitmq_handoff.py` runtime into `paa-core` plus consumer-facing CLI wrappers.
5. Rehome SQL migrations and reporting views into `paa-platform/migrations`.
6. Replace repo/home skill copies with repo-local install/update from `paa-platform`.
7. Add startup guardrails so stale role workspaces fail closed against canonical producer/consumer state.
