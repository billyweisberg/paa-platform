# PAA Hybrid Implementation Audit

Date: 2026-05-13

## Purpose

Identify the parts of the current PAA system that are still implemented as split or hybrid models and should be consolidated.

A hybrid implementation, for this note, means one where the same operational concern is owned by more than one authority surface at runtime, or where the system must reconcile multiple surfaces to answer a basic question such as:
- who owns the slice now
- what work is authorized
- where the runtime should execute
- which state is durable truth
- which installed surface is current

This note is not a rollout plan.
It is a design audit intended to make the remaining consolidation targets explicit.

## Related Notes

Read alongside:
- `docs/2_Design/2026-05-12-paa-handoff-execution-contract.md`
- `docs/2_Design/2026-05-13-paa-runtime-consolidation-design-correction.md`
- `docs/2_Design/2026-05-12-paa-messaging-simplification-note.md`
- `docs/2_Design/2026-05-09-paa-service-contracts.md`
- `docs/2_Design/2026-05-09-paa-data-contracts.md`
- `docs/2_Design/2026-05-09-team-worker-roles-design-spec.md`
- `docs/6_Deploy/2026-05-03-worktree-branch-strategy.md`

## Summary

The deepest remaining hybrid in PAA is not Python dependency management anymore.
That model has now been consolidated onto the consumer repo `.venv`.

The main remaining hybrid is workflow truth.
Today, workflow state is still spread across:
- queue packet lifecycle
- DB-backed runtime/reporting state
- repo-local runtime artifacts
- GitHub issue and PR state

That is the center of gravity for most of the confusion and brittleness that still exists.

Eight active hybrid implementations remain meaningful enough to call out:
1. workflow state truth
2. authority/package truth
3. install surfaces
4. handoff behavior surfaces
5. reporting surfaces
6. worktree ownership model references
7. producer vs consumer repo boundaries
8. packet vocabulary and evidence naming

## 1. Workflow State Truth Is Hybrid

### Current split

Current workflow state is inferred from a mixture of:
- RabbitMQ queue contents and claim lifecycle
- DB-backed control-plane and reporting state
- repo-local decision/result artifacts under `.project/data/paa/reports/`
- GitHub issue and PR state

Relevant implementation surfaces:
- `packages/paa-core/src/paa_core/handoff_runtime.py`
- `packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services`
- `packages/paa-core/src/paa_core/sql/full_chain_reporting_view.sql`

### Why this is a problem

A queue cleanup defect can look like a workflow-state defect.
A missing report artifact can distort lineage even when the queue and DB are otherwise correct.
GitHub can confirm implementation state while the internal runtime still appears undecided.

The system therefore has to reconcile too many signals to answer:
- who owns the slice now
- which stage the slice is in now
- whether the previous handoff is actually closed

### Consolidation target

Make durable workflow state authoritative outside the queue.
Preferred model:
- DB-backed workflow owner and stage are the sole runtime truth
- queue is wakeup and transport only
- repo-local files are evidence and logs only
- GitHub remains external engineering history, not internal workflow truth

## 2. Authority And Package Truth Is Hybrid

### Current split

Producer-side package and brief data exist in DB-backed runtime surfaces.
Consumer-side execution uses the installed authority package under `.project/data/paa/authority/current/`.
Some runtime paths still need to prefer installed authority artifacts over stale DB-backed brief content.

Relevant implementation surfaces:
- `packages/paa-producer/src/paa_producer/authority_runtime.py`
- `packages/paa-consumer/src/paa_consumer/authority_install.py`
- `scripts/runtime/install_pilot_authority_overlay.py`

### Why this is a problem

The consumer runtime can end up reconciling:
- published authority package content
- DB-cached package or brief content
- disposable overlay content

That creates ambiguity around what is actually authorized at execution time.

### Consolidation target

Use a single execution-time authority surface:
- producer DB and publication flow build versioned authority artifacts
- installed authority package is the only execution-time truth for consumer repos
- DB copies may index or report on published content, but consumer runtime should not reconcile the two during normal execution

## 3. Install Surfaces Are Hybrid

### Current split

The system currently spans multiple install and registration surfaces:
- source-of-truth project pack in `paa-platform`
- installed repo-local runtime under consumer `.codex/`
- home-level automation registrations under `<codex_home>/automations/`
- historical references to home-folder skills and automations

Relevant implementation surfaces:
- `project-packs/fractal-core/pack.json`
- `packages/paa-core/src/paa_core/install.py`
- `docs/3_Plan/2026-05-03-runtime-extraction-map.md`
- `docs/3_Plan/2026-05-03-helper-script-inventory-and-retirement-table.md`

### Why this is a problem

A behavior change can appear fixed in one surface while stale in another.
It is also too easy to confuse:
- source package content
- installed runtime content
- UI registration metadata

### Consolidation target

Normalize to:
- one source-of-truth project pack in `paa-platform`
- one installed runtime surface in each repo under `.codex/`
- one thin UI registration layer, ideally generated from repo-local install metadata rather than manually duplicated

## 4. Handoff Behavior Is Hybrid Across Code, Skills, And Automations

### Current split

The handoff lifecycle is currently expressed in multiple layers:
- runtime code in `paa-consumer` and `paa-core`
- role and TechLead `SKILL.md` files
- automation prompts and automation metadata
- repo-local automation memory written during execution

Relevant implementation surfaces:
- `packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services`
- `packages/paa-core/src/paa_core/handoff_runtime.py`
- `project-packs/fractal-core/skills/`
- `project-packs/fractal-core/automations/`

### Why this is a problem

Runtime invariants can drift into prompt discipline.
When a role recovers around a missing or stale surface, it can still appear to succeed even though lifecycle ownership is unclear.
The operator then has to ask whether the real contract lives in:
- code
- skill text
- automation prompt

### Consolidation target

Move all lifecycle invariants into runtime code.
Then narrow skills and automations to:
- role intent
- safe usage instructions
- fail-closed requirements

The runtime should own all transactionally important behavior.

## 5. Reporting Is Hybrid

### Current split

There are still two partially different views of system truth:
- queue-driven or lineage-driven active-state summaries
- DB-backed traceability and accepted-chain reporting

Relevant implementation surfaces:
- `packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services`
- `packages/paa-core/src/paa_core/sql/full_chain_reporting_view.sql`

### Why this is a problem

An idle repo can still report as `blocked` or `Unknown` at the top level while traceability correctly shows the latest accepted chain.
That weakens operator trust in the summary view.

### Consolidation target

Define one reporting model with explicit top-level states such as:
- idle
- waiting_on_delivery_architect
- waiting_on_worker
- waiting_on_qa
- qa_verified_pending_acceptance
- closed

Then ensure:
- top-level status
- slice lineage
- accepted-chain reporting
all derive from the same state semantics.

## 6. Worktree Ownership References Are Still Hybrid

### Current split

The active implementation now uses PAA-managed deterministic role worktrees under a repo-local root.
However, some older references still preserve other concepts such as home-folder worktree roots or Codex-native worktree assumptions.

Relevant implementation surfaces:
- `packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services`
- `docs/6_Deploy/2026-05-03-worktree-branch-strategy.md`

### Why this is a problem

This creates an avoidable reopening of an already-made design decision:
- does Codex own worktree creation
- or does PAA own deterministic role worktrees

The current design intends the latter.

### Consolidation target

Keep only one active worktree model in live design docs and runtime contracts:
- PAA-managed deterministic role worktrees
- repo-local worktree root
- explicit canonical branch source and freshness behavior

Alternative paths should remain only as rejected or historical notes.

## 7. Producer And Consumer Responsibilities Were Historically Hybrid

### Current split

The intended repo boundary is now much clearer:
- producer repo publishes authority/package outputs
- consumer repo installs and executes runtime behavior

But some historical docs and retired artifact references still preserve older mixed assumptions.

Relevant implementation surfaces:
- `appdev/AGENTS.md`
- `docs/3_Plan/2026-05-03-core-audit-doc-classification-and-helper-inventory.md`
- `docs/3_Plan/2026-05-03-helper-script-inventory-and-retirement-table.md`

### Why this is a problem

Mixed historical guidance can accidentally revive the wrong install or execution pattern, especially when runtime extraction or migration work is revisited.

### Consolidation target

Make the repo boundary explicit and stable:
- producer repo owns authority publication and producer-only helper tools
- consumer repo owns TechLead, role execution, QA, queue polling, and closeout
- historical mixed material should be marked clearly as retired context, not live instruction

## 8. Packet Vocabulary And Evidence Naming Are Still Hybrid

### Current split

The runtime now uses Team Worker packet families such as:
- `worker_result_packet`
- `delivery_review_packet`
- `qa_verification_packet`

But some runtime and reporting names still preserve older terminology such as `slice_result`.

Relevant implementation surfaces:
- `packages/paa-core/src/paa_core/handoff_runtime.py`
- `packages/paa-core/src/paa_core/sql/full_chain_reporting_view.sql`

### Why this is a problem

Even when behavior is correct, older naming suggests an older lifecycle model and increases the cost of reasoning about logs, evidence, and reporting code.

### Consolidation target

Normalize the runtime vocabulary to the Team Worker model end to end.
Keep backward-compatibility naming only at explicit migration boundaries.

## Resolved Hybrid: Python Runtime Dependency Model

This note should also record one important consolidation that is already complete.

### Old model

The installed PAA runtime previously used a hybrid dependency strategy:
- repo `.venv`
- repo-local vendored runtime dependencies under `.codex/paa/vendor`
- fallback behavior that could drift into ambient `python3`

### Current model

The active model is now:
- one consumer repo
- one `.venv`
- installed PAA runtime code under `.codex/paa/`
- no vendored dependency tree under `.codex/paa/vendor`
- fail-closed wrapper behavior if the repo `.venv` is missing

Relevant implementation surfaces:
- `packages/paa-core/src/paa_core/install.py`
- consumer repo `pyproject.toml`
- consumer repo `uv.lock`

This hybrid should be considered closed unless future changes reintroduce a second dependency surface.

## Consolidation Priorities

If the system is going to reduce complexity meaningfully, prioritize consolidation in this order:

1. workflow-state authority
2. execution-time authority/package truth
3. install surfaces and registration surfaces
4. handoff lifecycle ownership in runtime code
5. unified reporting semantics
6. worktree-model cleanup
7. producer/consumer boundary cleanup
8. vocabulary cleanup

## Design Conclusion

The most important unresolved hybrid in PAA is this:
- workflow truth is still split across queue state, DB state, repo-local file artifacts, and external GitHub state

Until that is consolidated, the system will continue to feel harder to reason about than the underlying workflow actually is.

The correct long-term direction is:
- authoritative state outside the queue
- installed authority package as sole consumer execution truth
- one runtime install surface per repo
- runtime code owning handoff invariants
- files demoted to artifacts, logs, and evidence
