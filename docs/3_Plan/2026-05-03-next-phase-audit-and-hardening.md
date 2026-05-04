# 2026-05-03 Next Phase Audit And Hardening

## Purpose

Capture the next set of PAA migration and hardening concerns before changing more system flow.
This note is intentionally operational. It records what we know now, what remains open, and the recommended sequencing.

## Summary

We have made real progress on:
- canonical producer / consumer / platform separation
- repo-local installs
- project-pack separation
- generic issue loading into PAA
- producer-side source-to-PAA sync in the architect packet flow

We do **not** yet have the whole system fully audited, fully normalized, or fully validated end-to-end.
The next phase should focus on audit, hardening, automation review, environment consistency, and testability before deeper workflow changes.

## Item 1. Remaining PAA Docs In `appdev`

### Question
Have we read all the docs related to PAA that were in the `appdev` repo? Are remaining docs there intentional? Do we have full coverage migrated and documented in `paa-platform`?

### Current state
- No, we should not yet claim full coverage.
- We did read and migrate the key lifecycle / derivation / runtime / reporting docs that directly affected the live control plane.
- There are still many documents in:
  - `/Users/billyweisberg/Repos/Individual-Centricity/appdev/docs/architecture/tom-baby7-fractal-core/`
- Those remaining docs include both:
  - project/source-authority documents that should remain in `appdev`
  - possible PAA-related operational/design documents that still need classification

### Current conclusion
- It is intentional that **not all** docs moved into `paa-platform`.
- `appdev` should remain the home of project-specific source, vision, architecture, and authority content.
- What is **not** yet complete is the classification audit proving which remaining docs belong to:
  - producer/source only
  - platform design/runtime ownership
  - both via cross-reference

### Required action
- Do a doc coverage audit against `appdev/.../README.md` and classify every remaining numbered doc into:
  - `producer-source`
  - `platform-runtime`
  - `historical / archive`
  - `needs split`

## Item 2. Audit, Update, And Validate Automations

### Current state
- Producer now has a repo-local automation:
  - `fractal-core-authority-architect-automation`
- Consumer has repo-local automations for:
  - Delivery Architect
  - QA
  - TechLead
  - Python Team
- We have **not** yet done a full prompt and behavior audit against the new topology.

### Current conclusion
- Automation installs are now structurally better.
- Automation correctness is not yet fully revalidated after all the migration work.

### Required action
- Audit every repo-local automation for:
  - role correctness
  - prompt correctness
  - branch/worktree assumptions
  - path assumptions
  - authority package assumptions
  - queue / handoff assumptions
  - stale workspace behavior

## Item 3. Repo-Level `config.toml`

### Current state
- Current runtime config is JSON-based under `.codex/paa/project-config.json`.
- There is no repo-level `config.toml` yet for broader environment/session/automation concerns.

### Current conclusion
- A repo-level `config.toml` is a good candidate for:
  - shared repo automation settings
  - uv/python environment settings
  - canonical branch definitions
  - workspace policy
  - queue profile / DB profile defaults
  - terminal/session bootstrap settings
- This should complement, not necessarily replace, the current PAA JSON contract.

### Required action
- Design whether repo-level configuration should be:
  - one `config.toml`
  - or `config.toml` plus existing `.codex/paa/project-config.json`
- Prefer one clear ownership model before introducing new config files.

## Item 4. Role Workspaces / Worktrees

### Current state
- We previously used full per-role repo copies.
- That worked as a stopgap but created drift and truth ambiguity.
- We have not yet designed the replacement operating model.

### Current conclusion
- The old full-copy model should not be the long-term answer.
- We need a deliberate decision between:
  - canonical repo + ephemeral worktrees
  - canonical repo + branch-refresh workflow
  - canonical repo + no dedicated role worktrees except when explicitly needed

### Required action
- Design and test a proper role workspace strategy.
- Define:
  - when a role gets a worktree
  - who creates it
  - who refreshes it
  - how staleness is detected
  - whether worktrees are ephemeral per issue/PR or semi-persistent per role

## Item 5. Helper Script Inventory

### Current state
- We have located many core runtime scripts and moved or rehomed a large portion of their logic.
- We have **not** yet produced a complete helper-script inventory across all repos and legacy surfaces.

### Current conclusion
- We should assume there are still helpers we have not fully classified.
- This includes things like:
  - TOML editing helpers
  - queue helpers
  - publishing helpers
  - DB/reconciliation helpers
  - ad hoc recovery scripts

### Required action
- Create a dedicated helper/script inventory with columns:
  - script path
  - current purpose
  - canonical replacement
  - still used?
  - deprecate / migrate / keep

## Item 6. Shared `uv` Environment

### Current state
- We are still using explicit Python paths like `/opt/homebrew/bin/python3.12` in several places.
- We do not yet have a single, documented `uv` environment setup used consistently by:
  - interactive sessions
  - repo-local wrappers
  - automation runs

### Current conclusion
- This is a real consistency gap.
- We need one supported Python/runtime environment strategy for both humans and automations.

### Required action
- Define a `uv`-based environment model for:
  - `paa-platform`
  - producer repo installs
  - consumer repo installs
- Decide whether wrappers should:
  - use the repo-local `uv` environment directly
  - or install fully self-contained payloads that do not rely on an activated environment

## Item 7. `AGENTS.md` For Authority Architect

### Current state
- Authority Architect is now an explicit conceptual role.
- We do not yet have an `AGENTS.md` in the producer/publishing repo describing that role and its operating rules.

### Current conclusion
- We should add an `AGENTS.md` to the producer repo.
- It should explicitly state that you and I act as Authority Architect on the producer side.

### Required action
- Create `AGENTS.md` in `/Users/billyweisberg/Repos/Individual-Centricity/appdev`
- Include:
  - Authority Architect scope
  - relationship to Delivery Architect
  - publish/load rules
  - doc ownership rules
  - change-control expectations for producer-side authority

## Item 8. Big Automation Prompt Review

### Current state
- Some prompts were updated during migration.
- We have not yet performed a holistic prompt review.

### Current conclusion
- This is necessary.
- Many of the system failures came from prompt assumptions that no longer matched reality.

### Required action
- Review prompts for:
  - Authority Architect automation
  - Delivery Architect automation
  - Python Team automation
  - QA automation
  - TechLead automation
- Look specifically for:
  - outdated topology references
  - hidden assumptions
  - duplicated instructions
  - unclear role boundaries
  - places where prompts compensate for missing runtime checks

## Item 9. End-To-End Testing

### Current state
- We have validated many slices in isolation.
- We do not yet have a formal end-to-end test plan for the migrated system.

### Current conclusion
- We need explicit E2E scenarios.
- Otherwise we will continue validating pieces but not the integrated workflow.

### Required action
- Define an end-to-end test matrix including:
  - source issue load into PAA
  - obligation materialization
  - architect packet compile
  - dev packet compile
  - QA packet compile
  - evidence persistence
  - TechLead report correctness
  - accepted full-chain reporting
  - repo-local install refresh from platform

## Item 10. Documentation Strategy For Lifecycle Folders

### Current state
- `paa-platform` now has lifecycle folders:
  - `1_Vision`
  - `2_Design`
  - `3_Plan`
  - `4_Build`
  - `5_Test`
  - `6_Deploy`
  - `7_Monitor`
- We do not yet have a documented documentation strategy/process for how content should move through those folders.

### Current conclusion
- This needs explicit rules so the folder structure becomes a working system, not just a filing structure.

### Required action
- Define:
  - what belongs in each folder
  - how docs progress from idea to design to build to validation
  - when docs are superseded vs archived
  - naming rules
  - review/update ownership

## Recommended Order

1. Full doc coverage audit and classification
2. Helper script inventory
3. Automation audit and prompt review
4. Workspace/worktree strategy
5. `uv` environment strategy
6. Repo-level config strategy (`config.toml` and/or JSON contract)
7. `AGENTS.md` in producer repo
8. End-to-end test plan
9. Documentation strategy for lifecycle folders
10. Only then resume deeper workflow changes

## Important guardrail

Do not claim the migration is fully understood or fully complete until:
- remaining `appdev` PAA-related docs are classified
- helper scripts are inventoried
- automations are re-audited
- environment/workspace strategy is explicit
- end-to-end test plan exists

That is the threshold for saying we actually understand the migrated platform rather than just the pieces we most recently touched.
