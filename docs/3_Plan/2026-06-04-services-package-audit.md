# Services Package Audit

Date: 2026-06-04

## Scope

This audit classifies the remaining `packages/paa-core/src/paa_core/services/` subpackages after the runtime and producer package refactors.

`db.py` is explicitly out of scope for this audit.

## Classification

### Permanent domain candidates

These packages still represent real business/application services and are not just old wrappers.

- `services/component_design_planning`
- `services/implementation_plan_derivation`
- `services/implementation_plan_progress`
- `services/techlead_acceptance_decision`
- `services/techlead_assignment_decision`
- `services/techlead_closeout_decision`
- `services/techlead_delivery_review_decision`
- `services/techlead_lineage_decision`
- `services/techlead_reset_recovery_decision`
- `services/techlead_worker_review_routing`

Reason:
- they are still imported by active runtime, producer, application, governance, and CLI code
- they are not just compatibility exports
- several of them define shared contracts and models that other package trees already depend on

### Transitional wrapper candidates

These packages still exist primarily to support historical import paths and test/governance references after their real implementation moved under `paa_core.runtime`.

- `services/dev_worker`
- `services/qa_worker`
- `services/techlead_worker`
- `services/queue_claim_runtime`
- `services/queue_packet_runtime_controller`
- `services/methodology_execution_preflight`
- `services/methodology_execution_projection`
- `services/methodology_execution_state`
- `services/workflow_lifecycle`

Reason:
- the active runtime implementation now lives under `paa_core.runtime.*`
- current references are mostly tests, metadata checks, or compatibility imports
- these can be retired after import consumers are rewritten to final paths

### Unclear / targeted relocation candidate

- `services/runtime_worktree`

Reason:
- it did not show active import demand in the quick audit
- it needs an isolated check before deletion or relocation because the surrounding runtime worktree functionality has already been partially moved

## Decision

### Keep as a real top-level internal domain for now

Keep `paa_core.services` as the permanent home for the active decision/planning services listed above.

Why:
- they are application/business services, not transport adapters
- forcing them under `runtime/` would mix domain decision logic with runtime host orchestration
- forcing them under `application/` would mix service contracts and orchestration adapters with reusable business-service implementations

So the current intended internal split is:

- `paa_core.api`
- `paa_core.application`
- `paa_core.runtime`
- `paa_core.producer`
- `paa_core.services`
- `paa_core.repositories`
- `paa_core.policies`
- `paa_core.governance`
- `paa_core.domain`

### Retire wrapper residue from `services/`

The wrapper candidates should be removed once imports are rewritten to their final runtime package homes.

## Next actions

1. rewrite tests and metadata references off the wrapper candidates to `paa_core.runtime.*`
2. remove the wrapper candidate packages from `paa_core.services`
3. perform a focused audit of `services/runtime_worktree`
4. leave `db.py` untouched until the services decision is stable
