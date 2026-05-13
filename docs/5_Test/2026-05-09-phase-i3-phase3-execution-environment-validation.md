# Phase I3 Phase 3 Execution Environment Contract Adherence Validation

## Scope

Execute `Phase 3: Execution Environment Contract Adherence` from:
- `docs/5_Test/2026-05-08-phase-i3-current-role-set-test-plan.md`

Current proven role set:
- `TechLead`
- `Delivery Architect`
- `Python Dev`
- `QA`

## Inputs

- execution environment contract:
  - `docs/6_Deploy/2026-05-07-phase-i2-automation-execution-environment-contract.md`
- canonical consumer repo root:
  - `<consumer_repo_root>`
- wrapper paths:
  - `<consumer_repo_root>/.codex/paa/bin/paa-consumer`
  - `<consumer_repo_root>/.codex/paa/bin/paa-producer`
- queue state info:
  - `paa-consumer queue-state-info`
- worktree ownership query:
  - `paa-consumer techlead-worktree-ownership`

## Checks Performed

1. verified project-pack automation `cwds` point to the canonical consumer repo root
2. verified installed consumer automation `cwds` point to the canonical consumer repo root
3. verified home-level UI registration `cwds` point to the canonical consumer repo root
4. verified consumer wrapper paths exist
5. verified queue state root resolves to the repo-local durable state directory
6. verified no active project-pack or installed consumer runtime surface depends on deprecated home-folder runtime skills as execution roots
7. verified role skills explicitly call out:
   - launch from the canonical consumer repo root
   - transition into the prepared role worktree
   - `uv` preference where required
8. verified deterministic role-worktree paths resolve through runtime ownership queries for:
   - `delivery-architect`
   - `python-team`
   - `qa`

## Corrections Applied During Validation

### 1. Home-level UI registration execution environment

Observed mismatch:
- home-level UI registrations under `<codex_home>/automations/` used:
  - `execution_environment = "worktree"`

Contract expectation:
- automations launch from the canonical consumer repo root first
- preflight and routing happen before any role-worktree transition

Correction applied on disk:
- updated the four home-level UI registrations to:
  - `execution_environment = "local"`

Result:
- aligned

### 2. Python deterministic role-branch naming

Observed mismatch:
- runtime ownership queries resolve the Python role branch/worktree as:
  - `issue-<issue_number>-dev`
- several docs/prompts still taught:
  - `issue-<issue_number>-python-team`

Correction applied:
- aligned the project-pack docs/prompts and installed consumer copies to the runtime’s actual current Python role branch form:
  - `issue-<issue_number>-dev`

Result:
- aligned

## Results

### Canonical launch cwd

Observed:
- project-pack automations use:
  - `cwds = ["{{REPO_ROOT}}"]`
- installed consumer automations use:
  - `cwds = ["<consumer_repo_root>"]`
- corrected home-level UI registrations use:
  - `cwds = ["<consumer_repo_root>"]`

Result:
- pass

### Wrapper paths

Observed:
- consumer wrapper exists
- producer wrapper exists

Result:
- pass

### Queue state root

Observed from `queue-state-info`:
- `active_state_dir = <consumer_repo_root>/.project/data/paa/queue-state/fractal-core-handoff`
- `active_state_source = env:FRACTAL_CORE_HANDOFF_STATE_DIR`
- candidate path is writable

Interpretation:
- the repo-local durable queue state root is active
- this environment root is wrapper-managed during runtime use, which is consistent with the contract

Result:
- pass

### Deprecated home-folder runtime dependency check

Observed:
- no active project-pack or installed consumer prompt/skill surfaces reference deprecated home-folder Fractal Core runtime skills as execution truth

Result:
- pass

### Role skill execution markers

Observed installed consumer role skills explicitly teach:
- launch from canonical consumer repo root
- change into the prepared role worktree returned by role-entry
- prefer `uv run` from the prepared worktree for:
  - `Python Dev`
  - `QA`

Result:
- pass

### Deterministic role-worktree paths

Observed from runtime ownership queries:
- `delivery-architect`
  - role branch:
    - `issue-106-delivery`
  - worktree path:
    - `<codex_home>/worktrees/paa/fractal-core-python/issue-106-delivery`
- `python-team`
  - role branch:
    - `issue-106-dev`
  - worktree path:
    - `<codex_home>/worktrees/paa/fractal-core-python/issue-106-dev`
- `qa`
  - role branch:
    - `issue-106-qa`
  - worktree path:
    - `<codex_home>/worktrees/paa/fractal-core-python/issue-106-qa`

All three resolved under the deterministic worktree root:
- `<codex_home>/worktrees/paa/fractal-core-python`

Result:
- pass

## Success Criteria Evaluation

Phase 3 success criteria were:
- no environment ambiguity remains for the current role set
- cwd transition and worktree execution model are explicit and internally consistent

Evaluation:
- satisfied after the two corrections above

Phase 3 verdict:
- `pass`

## Notes

- The shell environment itself does not need `FRACTAL_CORE_HANDOFF_STATE_DIR` exported globally as long as the repo-local wrapper layer sets and uses the correct repo-local durable queue state root during runtime execution.
- The home-level UI registration corrections were applied on disk under `<codex_home>/automations/` and are not versioned in the `paa-platform` repository.

## Next Step

Proceed to:
- `Phase 4: Packet And Queue Transport Validation`
