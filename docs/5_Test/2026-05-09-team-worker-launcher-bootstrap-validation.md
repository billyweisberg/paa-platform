# Team Worker Launcher Bootstrap Validation

## Purpose

Validate the remaining `Stage W5` launcher/bootstrap and UI-surface details for `Team Worker Roles`.

This note closes the gap between:
- repo-local installed Team Worker automation definitions in the consumer repo
- machine-local home-folder UI registration entries used by the Codex app
- installed consumer runtime vendoring needed for schema-valid runtime status checks

## Inputs

- Team Worker Roles spec:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-09-team-worker-roles-design-spec.md`
- Team Worker implementation plan:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-09-target-worker-family-expansion-implementation-plan.md`
- consumer repo root:
  - `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python`
- home-level UI registration root:
  - `/Users/billyweisberg/.codex/automations`

## Scope

This validation covers:
- home-level UI registration alignment for the current Team Worker-aware automation set
- launcher prompt alignment against the repo-local installed automation definitions
- installed consumer vendor compatibility for `jsonschema` / `rpds`

It does not yet prove:
- app-visible UI presence for the new Team Worker automations
- app-launched no-work polling behavior for the new Team Worker automations
- app-launched model execution for Team Worker automations

## Automation set validated

Core current-role-set automations:
- `fractal-core-techlead-automation`
- `fractal-core-delivery-architect-automation`
- `python-team-automation`
- `fractal-core-qa-automation`

Expanded Team Worker automations:
- `frontend-dev-automation`
- `backend-dev-automation`
- `infra-dev-automation`
- `docs-dev-automation`

## Steps performed

1. validated the patched consumer install vendoring path by refreshing the consumer runtime and then reinstalling the vendor tree through the same source-backed install helper
2. verified the installed consumer runtime now carries a Python 3.12-compatible `rpds` binary under:
   - `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/vendor/rpds/rpds.cpython-312-darwin.so`
3. ran:
   - `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-consumer techlead-status --repo-root /Users/billyweisberg/Repos/billyweisberg/fractal-core-python --validate-schema`
4. synchronized the home-level UI registration layer from the installed repo-local automation definitions for all eight automations in scope
5. parsed all eight home-level `automation.toml` files successfully with `tomllib`
6. spot-checked the synchronized launcher prompts to confirm:
   - no deprecated home-folder runtime skill references remain in the active Delivery Architect registration
   - Python now uses deterministic role branch `issue-<issue_number>-dev`
   - TechLead launcher text includes the expanded Team Worker branch vocabulary
   - Team Worker launchers now exist at the home-level UI registration layer for:
     - `Frontend Dev`
     - `Backend Dev`
     - `Infra Dev`
     - `Docs Dev`

## Expected outputs

- installed consumer runtime validates `techlead-status` successfully
- home-level UI registration files exist for the full Team Worker-aware automation set
- home-level UI registration prompts match the repo-local installed automation prompt contract closely enough to be treated as the same launcher surface

## Results

### Installed runtime vendor result

- `techlead-status --validate-schema`: `pass`
- vendored `rpds` binary now matches the installed wrapper interpreter family:
  - `rpds.cpython-312-darwin.so`

### Home-level UI registration result

The following home-level UI registration files are now present and parseable:
- `/Users/billyweisberg/.codex/automations/fractal-core-techlead-automation/automation.toml`
- `/Users/billyweisberg/.codex/automations/fractal-core-delivery-architect-automation/automation.toml`
- `/Users/billyweisberg/.codex/automations/python-team-automation/automation.toml`
- `/Users/billyweisberg/.codex/automations/fractal-core-qa-automation/automation.toml`
- `/Users/billyweisberg/.codex/automations/frontend-dev-automation/automation.toml`
- `/Users/billyweisberg/.codex/automations/backend-dev-automation/automation.toml`
- `/Users/billyweisberg/.codex/automations/infra-dev-automation/automation.toml`
- `/Users/billyweisberg/.codex/automations/docs-dev-automation/automation.toml`

### Launcher contract note

All eight home-level registrations still use:
- `execution_environment = "local"`

This remains intentional for the current launcher model.
It means:
- launch from the canonical consumer repo root
- perform deterministic no-work preflight there first
- transition into the prepared role worktree only after real role work exists

So `local` is still the launch base, not the final execution work surface.

## Verdict

- `Stage W5 launcher/bootstrap and UI-surface reconciliation: pass`

## Conclusions

- the installed consumer runtime is healthy again for schema-validated TechLead reporting
- the machine-local UI registration layer is now aligned with the Team Worker-aware repo-local automation surfaces
- the automation pilot can now be re-baselined against the Team Worker Roles model without knowingly testing obsolete launcher prompts

## Remaining follow-up

Still not yet proven here:
- app-visible presence of the four newly added Team Worker UI registrations
- app-launched no-work behavior for the new Team Worker automations
- app-launched execution behavior for any Team Worker automation beyond the current proven role set

Those belong to `Stage W7`.
