# Pilot Authority Overlay Validation

## Scope

Validate the pilot-only authority overlay/install step against the live disposable Team Worker fixture:

- issue: `108`
- PR: `109`
- task id: `py-pilot-team-worker-automation-runtime-note`

## Commands

Install:

```bash
python3 /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/runtime/install_pilot_authority_overlay.py \
  --repo-root /Users/billyweisberg/Repos/billyweisberg/fractal-core-python \
  --issue-number 108 \
  install
```

Installed authority task proof:

```bash
PYTHONPATH="/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/vendor:/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/lib" \
  /Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.venv/bin/python \
  -m paa_producer.authority_runtime task --issue-number 108
```

Installed authority authoring proof:

```bash
PYTHONPATH="/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/vendor:/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/lib" \
  /Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.venv/bin/python \
  -m paa_producer.authority_runtime authoring-check --issue-number 108
```

## Results

### Install result

- `ok = true`
- overlay root:
  - `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.project/data/paa/authority/current/overlays/pilot-fixtures/issue-108`

### Artifact install

Copied into current authority artifacts:

- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.project/data/paa/authority/current/artifacts/stage1_design_package.issue108.team_worker_automation_runtime_note.json`
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.project/data/paa/authority/current/artifacts/coder_run_brief.issue108.team-worker-automation-runtime-note.json`

The install also normalizes the copied fixture artifacts so their `authority_context` matches the pilot overlay instead of the borrowed issue `106` template values:

- `authority_version = 2026-05-03.1`
- `milestone_id = m9-team-worker-automation-pilot`
- `phase_id = p9-team-worker-automation-pilot`

### Installed authority task proof

Issue `108` now resolves from the installed authority manifest with:

- `task_id = py-pilot-team-worker-automation-runtime-note`
- `status = queued`
- `merge_policy = qa_required`
- `authoring` block present
- `design_package_id_external` present
- `coder_brief_id_external` present

### Authoring proof

Installed authority `authoring-check` passes:

- `authoring_complete = true`

### Runtime helper install

The overlay helper is present in the repo-local consumer runtime:

- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/scripts/runtime/install_pilot_authority_overlay.py`

## Verdict

- `pass`

The disposable fixture is now explicitly authorized through a pilot-only overlay instead of being silently outside the installed authority surface.
