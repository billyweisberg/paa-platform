# Stage W7 Phase 2 No-Work Poll Validation

## Verdict

- `Stage W7 Phase 2: pass`

## Goal

Confirm that the Team Worker-aware app-launched automations:
- execute the installed logged-preflight helper
- do not invoke the model when no work exists
- preserve repo-local durable evidence for each no-work run

## Inputs

- consumer repo root:
  - `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python`
- Team Worker-aware home-level UI registrations
- empty queue baseline
- installed logged-preflight helper:
  - `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/scripts/runtime/run_automation_preflight_with_logging.sh`
- repo-local automation log root:
  - `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.project/data/paa/logs/automations/`

## App-launched roles evaluated

- `Fractal Core TechLead Automation`
- `Fractal Core Delivery Architect Automation`
- `Python Team Automation`
- `Fractal Core QA Automation`
- `Docs Dev Automation`

## Precondition defect found and corrected before final retry

The first app-launched retry exposed real launcher defects:
- helper stack still used plain `python3`, which fell back to macOS Python 3.9
- no default repo-local `UV_CACHE_DIR` was being established
- installed repo-local wrappers did not prefer the repo `.venv` before checking `PATH`

Those defects were corrected in the installed runtime before the final Phase 2 retry.

## Evidence inspected

Latest successful run directories:
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.project/data/paa/logs/automations/fractal-core-techlead-automation/2026-05-09T19-10-07Z-34399`
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.project/data/paa/logs/automations/fractal-core-delivery-architect-automation/2026-05-09T19-10-07Z-34382`
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.project/data/paa/logs/automations/python-team-automation/2026-05-09T19-10-10Z-34674`
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.project/data/paa/logs/automations/fractal-core-qa-automation/2026-05-09T19-10-05Z-34135`
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.project/data/paa/logs/automations/docs-dev-automation/2026-05-09T19-10-05Z-34128`

## Observed outputs

For all five app-launched automations:
- `summary.json` exists
- `summary.status = preflight_complete`
- `summary.preflight.should_invoke_model = false`
- `summary.preflight.skip_model_invocation = true`
- `events.jsonl` contains:
  - `event = run_bootstrap`
  - `event = preflight_check`
  - `status = no_work`
- `stdout.log` contains the raw preflight JSON
- no queue candidates were present
- no worktree path was created or required

Observed gate reasons:
- `TechLead`
  - `gate_reason = no_techlead_work_detected`
- `Delivery Architect`
  - `gate_reason = no_role_work_detected`
- `Python Dev`
  - `gate_reason = no_role_work_detected`
- `QA`
  - `gate_reason = no_role_work_detected`
- `Docs Dev`
  - `gate_reason = no_role_work_detected`

## Queue state during evaluation

Observed from the logged preflight payloads:
- `fractal-core-python.messages_ready = 0`
- `fractal-core-qa.messages_ready = 0`
- `fractal-core-architecture.messages_ready = 0`

## Success criteria check

This phase required:
- no model invocation for the pilot roles when no work exists
- no worktree side effects
- one durable log envelope per no-work run
- preflight event evidence preserved for each tested role

Result:
- all success criteria passed

## Conclusion

The Team Worker-aware app launch surface now satisfies the narrow no-work polling requirement:
- app-launched runs can enter the installed logged-preflight path
- repo-local logs preserve the evidence we need
- the no-work gate prevents unnecessary model invocation for the pilot roles

## Next step

- proceed to `Stage W7 Phase 3: Team Worker single-role launch environment validation`
