# PAA Schema And Data Surface Audit

Date: 2026-05-13

## Purpose

Provide a hard design inventory of the current PAA schema and data surfaces before further Component Design or messaging refactors.

This note answers four questions:
1. where existing schemas and data contracts are located
2. what they define
3. how they are used today
4. which surfaces are canonical, installed copies, durable persistence, transport payloads, or runtime evidence only

This note exists because the current system has real data richness in the DB and real schema richness in files, but those surfaces are not yet cleanly rationalized.

## Related Notes

Read alongside:
- `docs/2_Design/2026-05-13-paa-db-primary-data-consolidation-audit.md`
- `docs/2_Design/2026-05-09-paa-data-contracts.md`
- `docs/2_Design/2026-05-12-paa-handoff-execution-contract.md`
- `docs/2_Design/2026-05-13-paa-hybrid-implementation-audit.md`
- `docs/2_Design/2026-05-13-paa-runtime-consolidation-design-correction.md`
- `docs/2_Design/2026-05-13-paa-system-component-diagram-v2.md`
- `docs/2_Design/2026-05-13-paa-v2-component-relationships.md`
- `docs/2_Design/2026-05-13-existing-component-design-model-audit.md`

## Audit Scope

This audit covers the schema and data surfaces currently visible in:
- `paa-platform`
- installed consumer runtime surfaces in `fractal-core-python`

It distinguishes between:
- canonical source schemas
- installed schema copies
- DB persistence schemas
- transport packet schemas
- installed execution package artifacts
- repo-local runtime evidence
- unrelated consumer-app artifact schemas that are not part of the PAA runtime itself

## Executive Summary

PAA currently has six distinct schema/data surface families:

1. **DB persistence schema**
- Postgres DDL, enums, tables, and reporting SQL

2. **Canonical JSON schema bundles owned by `paa-platform`**
- handoff-packet schemas
- authority-package schemas
- runtime-record schemas

3. **Published and installed execution-package artifacts**
- manifest
- project-authority schema
- design package JSON
- coder brief JSON
- package metadata
- overlay artifacts

4. **Transport packet JSON payloads**
- RabbitMQ message envelopes and packet families

5. **Repo-local runtime evidence and operator artifacts**
- reports
- queue-state
- claims
- logs
- automation memory

6. **Consumer application artifact schemas unrelated to PAA runtime**
- proving/parity/reference schemas in the consumer repo docs tree

The most important current design fact is:
- **the DB already models far more of the system than the runtime currently treats as authoritative**

That is why a workflow-state refactor cannot be reasoned about only from file artifacts or queue behavior.

## Surface Family 1: DB Persistence Schema

### Canonical location
- `migrations/postgres/001-step1-control-plane.sql`
- `migrations/postgres/002-step2-verification-recovery.sql`
- `migrations/postgres/003-step3-knowledge-graph.sql`
- `migrations/postgres/004-step4-coder-briefs.sql`
- `migrations/postgres/005-step5-design-packages-and-sequencing.sql`
- `packages/paa-core/src/paa_core/sql/full_chain_reporting_view.sql`
- `packages/paa-core/src/paa_core/sql/full_chain_proof_queries.sql`
- `packages/paa-core/src/paa_core/sql/single_slice_proof_queries.sql`

### What it defines

#### Step 1: durable control plane
Defined in:
- `migrations/postgres/001-step1-control-plane.sql`

Core types:
- `paa.project_status`
- `paa.role_category`
- `paa.authority_status`
- `paa.work_item_status`
- `paa.execution_record_status`
- `paa.handoff_status`
- `paa.queue_message_status`

Core tables:
- `paa.projects`
- `paa.roles`
- `paa.authority_versions`
- `paa.work_items`
- `paa.execution_records`
- `paa.handoffs`
- `paa.queue_messages`

#### Step 2: verification and recovery
Defined in:
- `migrations/postgres/002-step2-verification-recovery.sql`

Core types:
- `paa.agent_type`
- `paa.automation_run_status`
- `paa.verification_type`
- `paa.verification_status`
- `paa.evidence_result`
- `paa.acceptance_decision`

Core tables:
- `paa.agents`
- `paa.automation_runs`
- `paa.verification_obligations`
- `paa.evidence`
- `paa.acceptance_events`

#### Step 3: knowledge graph / authority graph
Defined in:
- `migrations/postgres/003-step3-knowledge-graph.sql`

Core tables include:
- `paa.source_artifacts`
- `paa.source_statements`
- `paa.requirements`
- `paa.requirement_sources`
- `paa.design_decisions`
- `paa.decision_requirements`
- `paa.spec_fragments`
- `paa.spec_fragment_requirements`
- `paa.spec_fragment_decisions`
- `paa.implementation_targets`
- `paa.authority_version_fragments`
- `paa.authority_version_targets`

#### Step 4: component and coder-brief layer
Defined in:
- `migrations/postgres/004-step4-coder-briefs.sql`

Core tables:
- `paa.components`
- `paa.component_surfaces`
- `paa.component_relationships`
- `paa.coder_run_briefs`

#### Step 5: design-package and sequencing layer
Defined in:
- `migrations/postgres/005-step5-design-packages-and-sequencing.sql`

Core tables:
- `paa.design_packages`
- `paa.design_package_signoffs`
- `paa.component_dependency_edges`
- `paa.coder_brief_sequence_states`

### How it is used today

The DB is already used for:
- publication records
- packet/handoff persistence
- queue-message persistence
- acceptance events
- design package persistence
- coder brief persistence
- reporting queries and traceability views

Relevant code surfaces:
- `packages/paa-core/src/paa_core/handoff_runtime.py`
- `packages/paa-producer/src/paa_producer/authority_runtime.py`
- `packages/paa-core/src/paa_core/sql/full_chain_reporting_view.sql`

### Important design finding

The DB already contains enough structure to support much stronger runtime-state ownership than the current runtime actually uses.

That is especially true for:
- workflow-state derivation
- acceptance state
- design-package and coder-brief traceability
- component and dependency graphs

## Surface Family 2: Canonical JSON Schema Bundles Owned By `paa-platform`

### Canonical location
- `schemas/handoff-packets/`
- `schemas/authority-package/`
- `schemas/runtime-records/`

### 2A. Handoff-packet schemas

Location:
- `schemas/handoff-packets/*.schema.json`

Defined packet families:
- `architect_cycle_packet`
- `delivery_review_packet`
- `qa_verification_packet`
- `slice_result_packet`
- `techlead_assignment_packet`
- `techlead_decision_packet`
- `worker_result_packet`

Supporting note:
- `schemas/handoff-packets/README.md`

What they define:
- canonical JSON envelope and payload requirements for transport packets

How they are used:
- copied into installed runtime under `.codex/paa/schemas/handoff-packets/`
- referenced by producer/runtime packet compilation and validation flows
- schema type drives route policy and payload checks in:
  - `packages/paa-core/src/paa_core/handoff_runtime.py`
  - `packages/paa-producer/src/paa_producer/authority_runtime.py`

Important design finding:
- packet schemas are canonical in files, not in DB
- queue persistence stores packet JSON payloads, but the JSON schema definitions themselves live in the file bundle

### 2B. Authority-package schemas

Location:
- `schemas/authority-package/*.schema.json`

Defined schemas:
- `package-metadata.schema.json`
- `project-config.consumer.schema.json`
- `project-config.producer.schema.json`
- `project-config.producer-consumer.schema.json`

Supporting note:
- `schemas/authority-package/README.md`

What they define:
- publication/install contract for authority packages and project config files

How they are used:
- copied into installed runtime under `.codex/paa/schemas/authority-package/`
- used by installer/publication flows in:
  - `packages/paa-core/src/paa_core/install.py`
  - `packages/paa-producer/src/paa_producer/publish.py`
  - `packages/paa-consumer/src/paa_consumer/authority_install.py`

Important design finding:
- these schemas define package/install structure, not workflow state
- they are part of the publication/install contract, not the queue/runtime-state contract

### 2C. Runtime-record schemas

Location:
- `schemas/runtime-records/*.schema.json`

Defined schemas:
- `techlead-status-report.schema.json`

Supporting note:
- `schemas/runtime-records/README.md`

What it defines:
- the shape of the `techlead-status` runtime report

How it is used:
- copied into installed runtime under `.codex/paa/schemas/runtime-records/`
- referenced directly by consumer runtime in:
  - `packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services`
- validated via `jsonschema` when `--validate-schema` is requested

Important design finding:
- this schema governs a projected report, not primary workflow truth
- it is an output schema, not the authoritative workflow-state schema

## Surface Family 3: Published And Installed Execution-Package Artifacts

### Canonical publication surfaces
Producer publication code:
- `packages/paa-producer/src/paa_producer/publish.py`
- `packages/paa-consumer/src/paa_consumer/authority_install.py`
- `packages/paa-core/src/paa_core/install.py`

### Installed execution package location in consumer repo
- `.project/data/paa/authority/current/`

Observed structure in `fractal-core-python`:
- `.project/data/paa/authority/current/authority/`
- `.project/data/paa/authority/current/artifacts/`
- `.project/data/paa/authority/current/docs/`
- `.project/data/paa/authority/current/overlays/`
- `.project/data/paa/authority/current/package-metadata.json`

### What it contains

#### Authority root
- `authority/fractal-core-python-authority.json`
- `authority/project-authority.schema.json`

#### Design/coder artifact bundle
Examples observed:
- `artifacts/stage1_design_package.issue110.team_worker_automation_runtime_note.json`
- `artifacts/coder_run_brief.issue110.team-worker-automation-runtime-note.json`
- `artifacts/stage1_design_package.schema.json`
- `artifacts/coder_run_brief.schema.json`
- `artifacts/dependency_graph_slice.schema.json`

#### Supporting docs bundle
Examples observed:
- roadmap and authority docs under `docs/`

#### Overlay material
Examples observed:
- `overlays/pilot-fixtures/issue-108/`
- `overlays/pilot-fixtures/issue-110/`

### How it is used today

The installed execution package is used by the consumer runtime to recover:
- current manifest
- design package content
- coder brief content
- installed docs used as execution-time authority context

Important implementation note:
- runtime had to be corrected to prefer installed authority artifacts over stale DB-cached brief content in some paths

Important design finding:
- this surface already behaves much more like a real installed execution package than many other parts of the runtime do
- this is the strongest candidate for execution-time truth consolidation

## Surface Family 4: Transport Packet JSON Payloads

### Canonical definitions
The packet schema files in:
- `schemas/handoff-packets/`

### Runtime packet handling
Main handling code:
- `packages/paa-core/src/paa_core/handoff_runtime.py`
- `packages/paa-producer/src/paa_producer/authority_runtime.py`
- `packages/paa-consumer/src/paa_consumer/inbox.py`
- `packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services`

### What they define in practice
A packet carries:
- message envelope
- schema type
- role route
- GitHub context
- authority context
- packet-family-specific payload

### Where packets exist
Packets exist in at least four forms:
1. canonical schema definition in `paa-platform`
2. installed schema copy under consumer `.codex/paa/schemas/`
3. actual queue payload in RabbitMQ
4. persisted queue payload JSON in DB `paa.queue_messages.payload_json`
5. repo-local review/report artifact JSON under `.project/data/paa/reports/`

### Important design finding

This is one of the biggest sources of sprawl.
The same conceptual packet exists as:
- schema definition
- live queue message
- persisted DB payload
- report file

Those are not the same thing and should not be treated as equal sources of truth.

## Surface Family 5: Repo-local Runtime Evidence And Operator Artifacts

### Location in consumer repo
- `.project/data/paa/`

Observed sub-surfaces:
- `.project/data/paa/authority/`
- `.project/data/paa/automation-memory/`
- `.project/data/paa/cache/`
- `.project/data/paa/claims/`
- `.project/data/paa/evidence/`
- `.project/data/paa/logs/automations/`
- `.project/data/paa/queue-state/`
- `.project/data/paa/reports/`

### What these define

#### Reports
Examples observed:
- `techlead-assignment.issue110.python-dev.json`
- `worker-result.issue110.python-dev.json`
- `delivery-review.issue110.delivery-architect.json`
- `qa-verification.issue110.qa.json`
- `techlead-decision.issue110.closed.json`
- `techlead-status-report.json`

These define human-readable and machine-readable runtime outputs for specific slices or runtime commands.

#### Queue-state / claims
These define repo-local durable runtime state for:
- queue claim tracking
- local queue runtime fallback state

#### Automation memory
These define role/automation-local durable notes, not formal workflow truth.

#### Logs
These define run logs and run summaries for automation execution.

### How they are used today

These surfaces are used for:
- debugging
- operator review
- packet inspection
- preflight and run evidence
- some lineage/status reconstruction in runtime paths

### Important design finding

This surface is extremely useful operationally, but it is too easy to over-read it as primary truth.

The design correction direction should be:
- keep these surfaces
- demote them to artifacts, logs, and evidence
- stop using them as competing workflow-state authorities

## Surface Family 6: Consumer Application Artifact Schemas Unrelated To PAA Runtime

### Location in consumer repo
- `docs/artifact-schemas/`
- `docs/artifact-examples/`
- `fixtures/blessed/`

Examples observed:
- `docs/artifact-schemas/proving.schema.json`
- `docs/artifact-schemas/parity.schema.json`
- `docs/artifact-schemas/final_tier_c_run_set_evidence.schema.json`
- `docs/artifact-schemas/proving_bundle_manifest.schema.json`

### What they define
These schemas belong to the consumer application's own proving/parity/artifact model.
They are not part of the PAA runtime contract itself.

### Why this distinction matters
Without separating these from PAA runtime schemas, the overall repo can look more schema-sprawled than the PAA runtime really is.

The sprawl is real, but these app-specific schemas should not be confused with:
- PAA packet schemas
- PAA runtime-record schemas
- PAA authority-package schemas
- PAA DB schemas

## Installed Schema Copies In The Consumer Runtime

### Location
- `.codex/paa/schemas/authority-package/`
- `.codex/paa/schemas/handoff-packets/`
- `.codex/paa/schemas/runtime-records/`

### What they are
These are installed copies of the canonical `paa-platform` schema bundles.

### How they are used
They support runtime validation inside the consumer repo without requiring the runtime to read directly from the `paa-platform` source checkout.

### Important design finding
These installed copies are useful and legitimate.
But they are copies, not canonical source schemas.

That means the model is:
- canonical schema source in `paa-platform`
- installed schema copies in consumer runtime

This is acceptable if the ownership boundary remains explicit.

## Current Canonical-vs-Copy-vs-Evidence Model

### Canonical schema definitions
Located in:
- `paa-platform/schemas/`
- `paa-platform/migrations/postgres/`
- `paa-platform/packages/paa-core/src/paa_core/sql/`

### Installed copies
Located in:
- consumer `.codex/paa/schemas/`
- consumer `.project/data/paa/authority/current/`

### Durable persistence
Located in:
- Postgres tables and views under the `paa` schema

### Runtime evidence only
Located in:
- consumer `.project/data/paa/reports/`
- consumer `.project/data/paa/logs/`
- consumer `.project/data/paa/automation-memory/`
- consumer `.project/data/paa/claims/`
- consumer `.project/data/paa/queue-state/`

## Where The Runtime Still Underuses The DB

This audit confirms that the runtime still underuses DB-backed structure in several important areas.

The DB already has rich structures for:
- workflow and handoff persistence
- queue message persistence
- automation run persistence
- acceptance events
- component modeling
- component relationships
- design packages
- coder briefs
- dependency edges
- sequence/readiness states

Yet the runtime still relies heavily on file surfaces for:
- current status projection
- packet inspection and transition context
- local lifecycle state recovery
- report-driven operator truth

That mismatch is real.
It is one of the core reasons the system still feels hybrid.

## Most Important Audit Conclusions

1. The DB is not a thin afterthought.
It already contains enough structure to support stronger runtime-state ownership than the current runtime uses.

2. Packet schemas are canonical in files, not in DB.
That is fine, but packet payloads then sprawl across queue, DB, and report artifacts.

3. The installed execution package is already a real execution-time data surface.
It should be treated as a first-class component, not an incidental install byproduct.

4. Repo-local reports and logs are valuable evidence surfaces.
They should remain, but they should stop competing with DB-backed workflow truth.

5. Consumer-app artifact schemas must be kept separate from PAA runtime schema discussions.
Otherwise the schema picture becomes harder to reason about than it really is.

## Design Implication

Before changing workflow-state modeling or messaging contracts further, we should treat these data surfaces explicitly as:

1. **canonical source schemas**
2. **installed execution-package schemas and artifacts**
3. **durable DB persistence schemas**
4. **transport payloads**
5. **runtime evidence outputs**

Any future Component Design for:
- `Workflow State Machine`
- `Installed Execution Package`
- `Runtime Lifecycle Engine`

must state exactly which of those five layers it owns and which it only projects, copies, or consumes.

## Design Conclusion

The schema problem in PAA is not only that there are many files.
The deeper problem is that the same conceptual thing often appears in multiple forms:
- schema definition
- installed copy
- DB persistence row
- queue payload
- repo-local evidence artifact

The correction is not to delete all file surfaces.
The correction is to make the role of each surface explicit and non-competing.

That is the necessary baseline before component-state and messaging redesign can be done cleanly.
