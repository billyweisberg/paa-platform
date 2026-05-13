# 2026-05-12 Pilot Overlay Traceability Sync Validation

## Goal

Validate that installing the pilot-only authority overlay updates the DB-backed traceability records for issue `108`, instead of leaving stale component metadata from the original loader row.

## Problem Being Fixed

The reporting view `paa.v_work_item_full_chain_traceability` resolves component identity from `paa.coder_run_briefs.component_assignment_json`.

Before this fix, issue `108` still resolved to stale metadata:

- `component_name = RetirementBoundaryDiagnostics`

That drift remained even though the current authority artifact and live packets already carried the correct pilot brief.

## Runtime Changes

The pilot overlay installer now synchronizes DB-backed traceability fields directly by external ids:

- design package by `package_id_external`
- coder brief by `brief_id_external`
- sequence state by the resolved design package / coder brief ids

Updated helper:

- `scripts/runtime/install_pilot_authority_overlay.py`

The installed consumer helper was also refreshed so the script can run directly from:

- `<consumer_repo_root>/.codex/paa/scripts/runtime/install_pilot_authority_overlay.py`

## Validation

### 1. Direct helper invocation works

```bash
cd <consumer_repo_root>
./.codex/paa/scripts/runtime/install_pilot_authority_overlay.py \
  --repo-root <consumer_repo_root> \
  --issue-number 108 \
  status
```

Result:

- `ok: true`
- `installed: true`

### 2. DB row resolves to pilot component identity

Query result for issue `108` after sync:

- `component_name = TeamWorkerAutomationPilotNote`
- `component_role = docs note describing Team Worker automation runtime states`

### 3. Reporting view resolves the corrected component identity

Query result from `paa.v_work_item_full_chain_traceability` for issue `108`:

- `issue_number = 108`
- `work_item_status = authorized`
- `component_name = TeamWorkerAutomationPilotNote`
- `component_role = docs note describing Team Worker automation runtime states`
- `full_chain_state = qa_verified_pending_acceptance`

## Conclusion

The traceability metadata drift for issue `108` is fixed at the actual reporting source.

The reporting view now resolves the pilot component identity from synchronized DB records instead of stale pre-overlay brief metadata.
