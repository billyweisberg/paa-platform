# Team Worker Automation Contract

## Purpose

Define the explicit automation contract for `Team Worker Roles`.

This contract sits between:
- the Team Worker role registry
- repo-local installed automation definitions
- home-level UI registration entries
- the installed consumer runtime wrappers
- the shared Team Worker execution skill

The goal is to make Team Worker automation behavior derive from project role data rather than from fixed named-worker assumptions.

## Authority

Use this contract together with:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-09-team-worker-roles-design-spec.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/project-packs/fractal-core/config/team-worker-roles.json`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/6_Deploy/2026-05-07-phase-i2-automation-execution-environment-contract.md`

This document supersedes any earlier Python-only automation interpretation when the target role is a Team Worker Role.

## Scope

This contract applies to all Team Worker Roles, including the current Fractal Core set:
- `Python Dev`
- `Frontend Dev`
- `Backend Dev`
- `Infra Dev`
- `Docs Dev`

It does not replace the specialized automation contracts for:
- `TechLead`
- `Delivery Architect`
- `QA`

## Source-of-truth model

### 1. Project role registry

Primary role-definition source:
- consumer installed registry file:
  - `.codex/paa/team-worker-roles.json`

The registry defines, per active Team Worker Role:
- `key`
- `display_name`
- `family`
- `branch_suffix`
- `queue_binding`
- `automation_id`
- `skill_id`
- `result_packet_family`
- `active`

### 2. Repo-local installed automation definitions

Runtime launcher source inside the consumer repo:
- `.codex/automations/<automation_id>/automation.toml`

These are the authoritative runtime launcher definitions for a Team Worker Role.

### 3. Home-level UI registration layer

App/UI registration surface:
- `/Users/billyweisberg/.codex/automations/<automation_id>/automation.toml`

These are machine-local registration copies.
They must mirror the repo-local installed Team Worker automation definitions closely enough that the app is launching the same logical role contract.

## Derivation rules

For each active Team Worker Role, the automation contract must derive these fields from the registry:

- role CLI key:
  - `key`
- role display name:
  - `display_name`
- worker family:
  - `family`
- deterministic role branch suffix:
  - `branch_suffix`
- home-level and repo-local automation id:
  - `automation_id`
- primary shared execution skill:
  - `skill_id`
- result packet family:
  - `result_packet_family`
- queue binding group:
  - `queue_binding`

No Team Worker automation prompt should hard-code a future worker role that contradicts the registry.

## Launch contract

### Launch root

All Team Worker automations launch from the canonical consumer repo root:
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python`

### Execution environment

Current launcher base remains:
- `execution_environment = "local"`

Meaning:
- launch from canonical repo root
- run no-work preflight there first
- resolve queue/runtime/authority state there first
- transition into the prepared Team Worker role worktree only after real work exists

This does not mean Team Worker code executes on the shared canonical repo root.
It means the launcher begins from the canonical repo root before changing into the prepared worktree.

### Required launcher references

Each Team Worker automation prompt must reference:
- repo-local installed authority skill
- repo-local installed inbox skill
- repo-local installed shared Team Worker execution skill

Current expected skill reference set:
- `fractal-core-authority`
- `fractal-core-inbox`
- `fractal-core-dev-result`

## Preflight contract

Every Team Worker automation must begin with deterministic non-model preflight:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer automation-preflight \
  --repo-root {{REPO_ROOT}} \
  --target-role <worker_role_cli>
```

Required behavior:
- if `should_invoke_model = false`, exit without model invocation
- if `should_invoke_model = true`, continue with repo-local runtime only

Success for this layer means Team Worker polling is cheap when no work exists.

## Worktree transition contract

When work exists, the Team Worker automation must:

1. inspect the prepared role worktree
2. resolve role entry context
3. change cwd into the prepared deterministic role worktree
4. perform assigned work there
5. return `worker_result_packet` only to `TechLead`

Deterministic role branch form:
- `issue-<issue_number>-<branch_suffix>`

Deterministic worktree path form:
- `/Users/billyweisberg/.codex/worktrees/paa/fractal-core-python/<role_branch>`

The Team Worker automation must never invent a branch suffix outside the registry-derived role branch contract.

## Result-return contract

All Team Worker Roles currently return through:
- `worker_result_packet`

Required path:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-role-return \
  --repo-root {{REPO_ROOT}} \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role <worker_role_cli> \
  --send
```

Team Worker automations must not:
- return directly to `QA`
- return directly to `Delivery Architect`
- return directly to producer-side roles

## Bootstrap/runtime contract

### Required wrapper layer

Team Worker automations must use repo-local wrappers:
- `.codex/paa/bin/paa-consumer`
- `.codex/paa/bin/paa-producer`

### Required interpreter bootstrap expectation

The installed wrapper/runtime layer must be able to execute with a Python 3.12-compatible vendor set.

This matters specifically for:
- `jsonschema`
- `referencing`
- `rpds`

### Direct repo-work expectation

When Team Worker code executes inside the prepared role worktree:
- prefer `uv run` from that prepared worktree
- fail closed instead of silently switching to an unrelated interpreter state

## Home-level UI registration rules

The home-level UI registration layer must:
- exist for every active Team Worker automation in pilot or launch scope
- mirror the repo-local installed Team Worker automation definitions
- not reference deprecated `$HOME/.codex/skills/fractal-core-*` runtime skills as execution truth

The home-level UI registration layer is allowed to be machine-local.
But if it drifts from the repo-local installed automation definitions, the app pilot is no longer testing the intended Team Worker contract.

## Fail-closed rules

A Team Worker automation must stop rather than guess when:
- preflight says no work exists
- the repo-local installed wrapper path is missing
- the installed authority package is missing
- the prepared role worktree does not exist when required
- the prepared role worktree is on the wrong branch
- the role branch suffix does not match the registry-defined value
- the prompt/launcher surface depends on deprecated home-folder runtime skill paths as execution truth

## Current Fractal Core Team Worker role matrix

### Python Dev
- key: `python-team`
- family: `implementation`
- branch suffix: `dev`
- automation id: `python-team-automation`

### Frontend Dev
- key: `frontend-dev`
- family: `implementation`
- branch suffix: `frontend`
- automation id: `frontend-dev-automation`

### Backend Dev
- key: `backend-dev`
- family: `implementation`
- branch suffix: `backend`
- automation id: `backend-dev-automation`

### Infra Dev
- key: `infra-dev`
- family: `infra`
- branch suffix: `infra`
- automation id: `infra-dev-automation`

### Docs Dev
- key: `docs-dev`
- family: `docs`
- branch suffix: `docs`
- automation id: `docs-dev-automation`

## Acceptance state

The Team Worker automation contract is complete enough for the current stage when:
- Team Worker automation definitions derive role identity from project role data
- home-level UI registrations align with repo-local installed Team Worker launcher definitions
- deterministic preflight works without model invocation when no work exists
- deterministic role worktree transition remains explicit
- one non-Python Team Worker Role is already proven through the generic worker bridge
- the app/UI pilot can now resume against this contract through Stage W7
