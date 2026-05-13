# Automation Logging Bootstrap Validation

## Purpose

Validate the first reusable automation logging bootstrap surfaces.

## Helpers validated

- `scripts/runtime/bootstrap_automation_logging.sh`
- `scripts/runtime/log_automation_event.py`
- `scripts/runtime/run_automation_preflight_with_logging.sh`

## Disposable validation run

Validated against:
- consumer repo root:
  - `<consumer_repo_root>`
- automation id:
  - `docs-dev-automation`
- role key:
  - `docs-dev`
- phase:
  - `stage-w7-phase2`

## Steps performed

1. ran the bootstrap helper for a disposable `Docs Dev` logging run
2. captured the emitted shell exports
3. used the exported environment to append one structured event with:
   - `event = preflight_check`
   - `status = ok`
   - `extra.should_invoke_model = false`
4. verified:
   - run directory created
   - `events.jsonl` created
   - `summary.json` created
   - `stdout.log` created
   - `stderr.log` created
5. compiled the event helper successfully with `py_compile`
6. installed the logging helpers into the consumer runtime under:
   - `<consumer_repo_root>/.codex/paa/scripts/runtime/`
7. ran the installed consumer logged-preflight helper for:
   - `docs-dev`
8. verified the installed helper produced:
   - a no-work preflight JSON result
   - a `preflight_check` JSONL event with `status = no_work`
   - a summary file with `status = preflight_complete`
9. reproduced the app-launch failure mode under a stripped `PATH`
10. fixed the logged-preflight runtime path so it:
   - prefers the repo-local `.venv/bin/python`
   - defaults `UV_CACHE_DIR` to repo-local `.codex-work/uv-cache`
   - avoids plain `python3` calls inside the helper stack
11. reran the installed helper under:
   - `PATH=/usr/bin:/bin:/usr/sbin:/sbin`
12. verified the stripped-path run still produced:
   - `should_invoke_model = false`
   - `gate_reason = no_role_work_detected`
   - `summary.status = preflight_complete`
   - `events.jsonl` with `preflight_check` and `status = no_work`

## Observed output location

Example validated run directory:
- `<consumer_repo_root>/.project/data/paa/logs/automations/docs-dev-automation/2026-05-09T18-38-45Z-79585`

## Observed event log content

Observed bootstrap event:
- `event = run_bootstrap`
- `status = started`

Observed appended event:
- `event = preflight_check`
- `status = ok`
- `extra.should_invoke_model = false`

Observed installed consumer logged-preflight event:
- `event = preflight_check`
- `status = no_work`
- `extra.gate_reason = no_role_work_detected`

## Verdict

- `automation logging bootstrap: pass`

## Conclusions

- reusable automation logging surfaces now exist
- the installed consumer runtime now carries the logged-preflight helper the automations can call directly
- the installed logged-preflight path is now resilient to stripped app launch environments that do not expose `python3.12` or writable home `uv` cache state
- repo-local durable logging is now available before resuming `Stage W7 Phase 2`
- the paused Team Worker pilot can resume exactly where it left off, but with logging in place
