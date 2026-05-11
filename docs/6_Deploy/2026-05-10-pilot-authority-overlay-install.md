# Pilot Authority Overlay Install

## Purpose

Disposable pilot fixtures are valid DB-backed and GitHub-backed test slices, but they are not part of the normally published authority package.

Team Worker automations correctly fail closed unless the installed current authority under:

- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.project/data/paa/authority/current/`

contains:

- an authorized manifest task for the disposable issue
- the linked stage-1 design package artifact
- the linked coder brief artifact

This note defines the pilot-only overlay/install step that makes a disposable fixture executable without pretending it is part of the normal published authority package.

## Contract

### Install source

Disposable pilot fixtures are created under:

- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex-work/pilot-fixtures/issue-<issue_number>/`

Expected inputs:

- `fixture-summary.json`
- `artifacts/stage1_design_package.issue<issue_number>.*.json`
- `artifacts/coder_run_brief.issue<issue_number>.*.json`

### Install destination

Overlay installs patch the consumer repo-local current authority under:

- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.project/data/paa/authority/current/`

Overlay-owned state is stored under:

- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.project/data/paa/authority/current/overlays/pilot-fixtures/issue-<issue_number>/`

### Installed effects

An install must:

1. copy the disposable fixture artifacts into:
   - `current/artifacts/`
2. append or replace one manifest task in:
   - `current/authority/fractal-core-python-authority.json`
3. record overlay metadata in:
   - `current/package-metadata.json`
4. preserve a pilot-only marker under:
   - `current/overlays/pilot-fixtures/issue-<issue_number>/`

### Manifest task requirements

The overlay task must be rich enough to pass installed authority checks, including:

- `task_id`
- `issue_number`
- `phase_id`
- `milestone_id`
- `title`
- `status`
- `merge_policy`
- `requires_qa`
- `allowed_successors`
- `protected_contracts`
- `source_authorities`
- `dependencies`
- `authoring`
- `design_package_id_external`
- `coder_brief_id_external`

### Reversibility

The overlay step is reversible.

Remove mode must:

1. remove the pilot task from the installed manifest
2. remove copied overlay artifacts from `current/artifacts/`
3. remove the overlay metadata entry from `package-metadata.json`
4. remove the overlay directory under `current/overlays/pilot-fixtures/issue-<issue_number>/`

## Command

Source helper:

- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/runtime/install_pilot_authority_overlay.py`

Installed helper:

- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/scripts/runtime/install_pilot_authority_overlay.py`

Example install:

```bash
python3 /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/runtime/install_pilot_authority_overlay.py \
  --repo-root /Users/billyweisberg/Repos/billyweisberg/fractal-core-python \
  --issue-number 108 \
  install
```

Example status:

```bash
python3 /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/runtime/install_pilot_authority_overlay.py \
  --repo-root /Users/billyweisberg/Repos/billyweisberg/fractal-core-python \
  --issue-number 108 \
  status
```

Example remove:

```bash
python3 /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/runtime/install_pilot_authority_overlay.py \
  --repo-root /Users/billyweisberg/Repos/billyweisberg/fractal-core-python \
  --issue-number 108 \
  remove
```

## Why This Exists

This keeps the boundary honest:

- published authority package remains the normal source of truth
- disposable pilot fixtures remain explicitly local overlays
- Team Worker automations still fail closed unless the installed authority actually authorizes the work
