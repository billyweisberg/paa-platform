# Phase I3 Phase 0 Baseline Validation

## Scope

Execute `Phase 0: Baseline And Installation Sanity` from:
- `docs/5_Test/2026-05-08-phase-i3-current-role-set-test-plan.md`

Current proven role set:
- `TechLead`
- `Delivery Architect`
- `Python Dev`
- `QA`

## Inputs

- consumer repo root:
  - `<consumer_repo_root>`
- consumer wrapper:
  - `<consumer_repo_root>/.codex/paa/bin/paa-consumer`
- authority manifest:
  - `<consumer_repo_root>/.project/data/paa/authority/current/authority/fractal-core-python-authority.json`
- installed consumer automations:
  - `<consumer_repo_root>/.codex/automations/`
- installed consumer skills:
  - `<consumer_repo_root>/.codex/skills/`
- home-level UI registrations:
  - `<codex_home>/automations/`

## Checks Performed

1. verified `paa-consumer help` exposes the current consumer command surface
2. verified the installed authority manifest exists
3. verified installed consumer skills exist for:
   - `fractal-core-techlead`
   - `fractal-core-delivery-review`
   - `fractal-core-dev-result`
   - `fractal-core-qa-review`
4. verified installed consumer automations exist for:
   - `fractal-core-techlead-automation`
   - `fractal-core-delivery-architect-automation`
   - `python-team-automation`
   - `fractal-core-qa-automation`
5. verified home-level UI registration TOMLs exist for the same four automations
6. parsed installed consumer automation TOMLs
7. parsed home-level UI registration TOMLs

## Results

### Wrapper command surface

Observed `paa-consumer` commands included:
- `automation-preflight`
- `techlead-status`
- `techlead-emit-next-assignment`
- `techlead-lineage`
- `techlead-prepare-role-branch`
- `techlead-prepare-role-worktree`
- `techlead-handoff-to-role-worktree`
- `techlead-role-entry`
- `techlead-role-result-assist`
- `techlead-role-return`
- `techlead-reset-required`
- `techlead-reset-cleanup`
- `techlead-superseded-cleanup`
- `techlead-closed-cleanup`

Result:
- pass

### Authority manifest

Observed:
- present at `<consumer_repo_root>/.project/data/paa/authority/current/authority/fractal-core-python-authority.json`

Result:
- pass

### Installed consumer skills

Observed:
- all four required skill files present

Result:
- pass

### Installed consumer automations

Observed:
- all four required automation TOMLs present
- all four parsed successfully

Result:
- pass

### Home-level UI registrations

Observed:
- all four required home-level automation TOMLs present
- all four parsed successfully

Result:
- pass

## Success Criteria Evaluation

Phase 0 success criteria were:
- all required files and command surfaces are present
- no required automation or skill is missing from the current role set

Evaluation:
- satisfied

Phase 0 verdict:
- `pass`

## Notes

- This phase verified presence and parseability of the home-level UI registration files.
- This phase did **not** directly verify visual UI rendering of those automations inside the app UI.
- TOML parse validation used `python3.12` because the default `python3` on the machine does not provide `tomllib`.

## Next Step

Proceed to:
- `Phase 1: Prompt And Skill Contract Alignment`
