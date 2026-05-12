# Target Worker-Family Expansion Implementation Plan

Superseded as the top-level design authority by:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-09-team-worker-roles-design-spec.md`

This note remains useful as the implementation sequencing plan for the expansion work, but the term `Team Worker Roles` is now the authoritative design vocabulary.

## Purpose

Make Team Worker Roles expansion a first-class implementation authority instead of a deferred note.

This plan exists to prevent rebuilding the automation layer twice.
From this point forward, the target implementation must assume the broader worker family is real and must be accommodated directly in:
- packet contracts
- role vocabulary
- route policy
- branch and worktree naming
- automation prompts
- automation launch/bootstrap behavior
- TechLead routing and reporting

## Authority Statement

This document is now subordinate to the `Team Worker Roles` design spec.

Use the design spec as the authority for:
- terminology
- role model
- source-of-truth rules
- route derivation expectations
- automation implications

Use this document as the implementation sequencing plan layered beneath that authority.

Use this plan together with:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-05-phase-g-worker-result-and-delivery-review-contracts.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-05-techlead-hub-master-execution-map.md`

## Work Area Checklist

- [x] dynamic role registry
  - status: complete
  - authority:
    - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/project-packs/fractal-core/config/team-worker-roles.json`
    - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-09-team-worker-roles-design-spec.md`

- [ ] runtime role derivation
  - status: in progress, substantial
  - done:
    - assignment targeting is registry-aware
    - worker result acceptance is registry-aware
    - key role bridge surfaces accept Team Worker role keys
  - remaining:
    - sweep ancillary normalization, reporting, and edge-path surfaces to remove remaining fixed-role assumptions

- [ ] routing and queue policy
  - status: in progress, shared-queue model only
  - done:
    - route policy for Team Worker assignment/result paths is data-driven
    - current queue binding model derives from the registry
  - remaining:
    - decide whether to stay on a shared implementation queue or introduce per-role/per-family queue topology

- [ ] branch and worktree policy
  - status: substantially complete
  - done:
    - role branch suffixes are registry-defined
    - deterministic worktree behavior remains intact
    - non-Python proof exists through `Docs Dev`
    - canonical source resolution now prefers `origin/<canonical_branch>` when available
  - remaining:
    - broaden live automation proof for Team Worker app-launched execution surfaces beyond the current proving lane if desired

- [ ] automation contract
  - status: substantially complete
  - done:
    - repo-local Team Worker automation definitions exist
    - home-level UI registrations are aligned to the Team Worker-aware installed automation definitions
    - deterministic no-work preflight exists
    - installed consumer vendor/runtime path is healthy again
    - explicit Team Worker automation contract now exists:
      - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/6_Deploy/2026-05-09-team-worker-automation-contract.md`
    - pilot-only authority overlay/install step now exists for disposable fixtures:
      - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/6_Deploy/2026-05-10-pilot-authority-overlay-install.md`
    - Stage W7 supervised Team Worker pilot slice passed through:
      - `Delivery Architect`
      - `Python Dev`
      - `QA`
    - TechLead closeout for `qa_verification_packet pass` now exists and is validated
  - remaining:
    - decide whether recorded closeout decision packets should remain queue-visible or be auto-acknowledged after persistence
    - resolve traceability metadata drift for the active work chain

- [ ] migration plan
  - status: complete as authority, in progress as rollout
  - authority:
    - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-09-team-worker-roles-design-spec.md`
    - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-09-target-worker-family-expansion-implementation-plan.md`
  - rollout proof already complete:
    - `TechLead -> Docs Dev -> TechLead -> QA`

## Why We Are Doing This Now

The current proven role set validated the hub loop:
- `TechLead`
- `Delivery Architect`
- `Python Dev`
- `QA`

That proof was necessary.
It is not sufficient as the final target architecture.

The deferred Team Worker Roles requirement is now promoted because:
- future worker roles are a real requirement, not optional stretch work
- re-hardening automations for only the current role set would create duplicate migration work
- the generic worker lane already exists in runtime through `worker_result_packet`
- the remaining task is to make the rest of the system speak the same broader role model

## In Scope

### Worker roles in target scope

Initial target worker families to support:
- `Python Dev`
- `Frontend Dev`
- `Backend Dev`
- `Infra Dev`
- `Docs Dev`

### Roles not generalized under `worker_result_packet`

These remain specialized spoke roles:
- `Delivery Architect`
- `QA`

These remain hub or producer-side roles:
- `TechLead`
- `Authority Architect`

## Target Model

### Routing model

The target routing model remains:
- `TechLead` is the only consumer-side routing hub
- worker roles do bounded implementation work only
- worker roles return only to `TechLead`
- worker roles do not route directly to other spokes
- `QA` and `Delivery Architect` remain specialized reviews returning only to `TechLead`

### Packet model

Target packet families:
- `techlead_assignment_packet`
- `worker_result_packet`
- `delivery_review_packet`
- `qa_verification_packet`
- `techlead_decision_packet`

Rules:
- `worker_result_packet` is the default result family for all implementation workers
- `delivery_review_packet` is only for `Delivery Architect`
- `qa_verification_packet` is only for `QA`
- `slice_result_packet` remains legacy compatibility only, not active target-state guidance

### Worker identity model

The schema name no longer identifies the worker family.
The payload does.

Required worker identity fields:
- `worker_role`
- `worker_family`

Initial target values:
- `Python Dev` / `implementation`
- `Frontend Dev` / `implementation`
- `Backend Dev` / `implementation`
- `Infra Dev` / `infra`
- `Docs Dev` / `docs`

## Naming And Execution Surface Model

### Canonical branch

- `issue-<issue_number>`

### Authorized role branches

Target branch naming should be deterministic and role-explicit:
- `issue-<issue_number>-delivery`
- `issue-<issue_number>-dev`
- `issue-<issue_number>-frontend`
- `issue-<issue_number>-backend`
- `issue-<issue_number>-infra`
- `issue-<issue_number>-docs`
- `issue-<issue_number>-qa`

### Deterministic worktree model

Target worktree root remains:
- `/Users/billyweisberg/.codex/worktrees/paa/<repo_name>/<role_branch>`

Role automations are responsible for:
- create-or-reuse of their own deterministic worktree
- execution inside that worktree
- returning results from that worktree context

`TechLead` remains responsible for:
- lineage authority
- branch authorization
- routing
- lifecycle decisions

## Automation Implications

Automation design must now assume the target worker family exists even if some worker roles are not yet fully UI-launched.

That means:
- prompts must teach the broader worker-role vocabulary now
- no new prompts should hard-code a Python-only future
- launch/bootstrap contracts must be reusable by all worker-family roles
- preflight no-work polling must be reusable by all worker-family roles
- role-entry, result-assist, and return surfaces must be parameterized by target worker role, not special-cased around Python only

## Implementation Sequence

## Stage W1: Consolidate role vocabulary and branch naming

Goal:
- make the vocabulary and deterministic branch names explicit everywhere

Required changes:
- define target worker role list in one authoritative place
- define target role-branch mapping in one authoritative place
- remove stale prompt references that imply only Python worker support
- preserve current runtime compatibility for existing `issue-<issue_number>-dev` Python lane

Success:
- prompts, skills, and design docs stop contradicting the target role set

## Stage W2: Generalize TechLead assignment semantics

Goal:
- make assignment intent generic across worker-family roles

Required changes:
- ensure `techlead_assignment_packet` examples and guidance are written for generalized worker targets
- confirm assignment payload vocabulary does not assume Python-specific implementation detail names
- make TechLead decision guidance capable of assigning a generic worker role without changing packet family shape

Success:
- `TechLead` can assign any target worker role by vocabulary and route policy, not by Python-only conventions

## Stage W3: Generalize runtime role mapping and route policy

Goal:
- make the control spine accept the target worker family explicitly

Required changes:
- ensure role normalization supports:
  - `Frontend Dev`
  - `Backend Dev`
  - `Infra Dev`
  - `Docs Dev`
- ensure queue route policy can map new worker roles cleanly into the correct consumer queue model
- decide whether new worker families share the existing `fractal-core-python` queue initially or require additional queues

Current target assumption:
- new worker families share the existing consumer-side implementation queue until a later queue-topology decision is made

Success:
- runtime acceptance and routing no longer treat broader worker roles as unsupported vocabulary

## Stage W4: Generalize role bridge helpers

Goal:
- stop teaching Python as the only worker-role bridge

Required changes:
- generalize:
  - `techlead-handoff-to-role-worktree`
  - `techlead-inspect-role-worktree`
  - `techlead-role-entry`
  - `techlead-role-result-assist`
  - `techlead-role-return`
- make them operate on the target worker-role vocabulary and branch map
- preserve specialized behavior for:
  - `Delivery Architect`
  - `QA`

Success:
- one worker-family bridge shape serves all implementation workers

## Stage W5: Generalize automation definitions and bootstrap contracts

Goal:
- make automation configuration target-state correct before wider unpause

Required changes:
- rewrite automation definitions so they point at generalized worker-role entry contracts
- define launcher/bootstrap behavior that is reusable for all worker-family roles
- ensure preflight no-work gate works for all target worker families without model invocation
- stop encoding Python-only assumptions into home-level UI registrations and installed automation prompts

Success:
- automation launch configuration is worker-family aware, not Python-only with placeholders

## Stage W6: Prove one additional non-Python worker-family lane

Goal:
- validate that the broader worker-family model is real, not just renamed docs

Recommended first proving lane:
- `Docs Dev`

Why:
- lowest execution-risk worker family
- easiest to validate without deep runtime/compiler proliferation
- proves the generic worker-family lane without requiring a full new QA discipline

Required outcome:
- `TechLead -> Docs Dev -> TechLead` succeeds on the same generic worker bridge

Success:
- one non-Python worker-family result returns through `worker_result_packet` cleanly

## Stage W7: Reconcile automation pilot and cutover work against target state

Goal:
- resume automation design/testing only after the automation surfaces match the broader worker-family model

Required changes:
- re-baseline the automation pilot plan against the new worker-family authority
- verify current proven role set automations still work under the broader vocabulary
- only then continue UI-launched automation pilot work

Success:
- automation testing is no longer proving a temporary architecture we intend to replace

## Inputs

The primary fixed proving inputs remain:
- consumer repo:
  - `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python`
- platform repo:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform`
- producer repo:
  - `/Users/billyweisberg/Repos/Individual-Centricity/appdev`
- current canonical proving fixture:
  - issue `106`
  - PR `107`
  - canonical branch `issue-106`

Additional proving inputs to introduce during this plan:
- one synthetic or lightweight real fixture for a non-Python worker-family role
- initial recommended proving role:
  - `Docs Dev`

## Variables And Knobs

These are the adjustable variables for the implementation plan:
- worker-role set enabled in runtime vocabulary
- branch suffix mapping per worker role
- queue topology choice for broader worker families
- which non-Python worker family is used as the first proving lane
- whether the first proving lane is synthetic or attached to a live issue
- whether UI-visible automations are created for all worker families immediately or staged after runtime bridge generalization

## Non-Goals

This plan does not require:
- replacing `Delivery Architect` with a generic worker role
- replacing `QA` with a generic worker role
- deleting legacy `slice_result_packet` support immediately
- changing the `Authority Architect` producer-side model
- solving all future queue-topology scaling questions before vocabulary and bridge generalization are in place

## Acceptance Criteria

This plan is complete when:
- the broader worker-role vocabulary is first-class in docs, runtime, and prompts
- runtime routing and bridge helpers are generic across worker-family roles
- automation configuration is aligned to the broader worker-family model
- at least one non-Python worker-family lane has been proven through `worker_result_packet`
- current proven role set behavior still passes after the generalization work

## Current Implementation Status

### Completed in the first Team Worker Roles slice

- Stage W1 is complete
  - project-level Team Worker Role registry exists
  - deterministic branch suffixes are now defined as data
  - consumer and producer installs now carry the registry file

- Stage W2 has an initial implementation pass
  - explicit Team Worker Role assignment emission can now target registry-defined worker roles
  - Delivery Architect `ready_for_dev` follow-up can now derive any active Team Worker Role from the registry

- Stage W3 has an initial implementation pass
  - route validation for `techlead_assignment_packet` and `worker_result_packet` is now registry-derived
  - role normalization accepts registry-defined Team Worker Role names

- Stage W4 has an initial implementation pass
  - role bridge CLI surfaces now accept Team Worker Role keys, not just `python-team`
  - initial installed-runtime validation passed for `Docs Dev`

- Stage W5 has an initial implementation pass
  - home-level UI registrations now exist for:
    - `fractal-core-techlead-automation`
    - `fractal-core-delivery-architect-automation`
    - `python-team-automation`
    - `fractal-core-qa-automation`
    - `frontend-dev-automation`
    - `backend-dev-automation`
    - `infra-dev-automation`
    - `docs-dev-automation`
  - home-level UI registration prompts are now synchronized to the repo-local installed Team Worker-aware automation definitions
  - the shared Team Worker execution skill contract is now role-agnostic
  - project-pack automation definitions now exist for:
    - `python-team`
    - `frontend-dev`
    - `backend-dev`
    - `infra-dev`
    - `docs-dev`
  - consumer install manifest now installs those Team Worker automations
  - installed consumer runtime now carries those automation definitions
  - installed consumer vendoring now validates `techlead-status --validate-schema` successfully again

- Stage W6 is complete
  - `TechLead -> Docs Dev -> TechLead` now succeeds on the generic worker bridge
  - TechLead can derive `QA` from the returned docs worker packet

### Stage W7 status

- Stage W7 automation pilot work is now complete through the supervised pilot closeout path
  - Stage W7 Phase 0 readiness snapshot passed
  - Stage W7 Phase 1 UI visibility validation passed
  - Stage W7 Phase 2 no-work poll and non-invocation validation passed
  - Stage W7 Phase 3 Team Worker single-role launch environment validation passed
  - Stage W7 Phase 4 supervised live pilot slice passed on disposable issue `108`
  - Delivery Architect, Python Dev, QA, and TechLead closeout behavior all executed on the Team Worker model
  - passing QA closeout now auto-acknowledges the self-addressed terminal closeout decision packet after persistence/send
  - pilot overlay install now synchronizes DB-backed traceability rows so issue `108` resolves to `TeamWorkerAutomationPilotNote` in `paa.v_work_item_full_chain_traceability`

## Immediate Next Slice

1. generalize the remaining Team Worker automation contract away from `local` launcher assumptions and reconcile it with true Codex-native worktree/environment configuration
2. keep full-run automation observability visible beyond preflight-only logs
