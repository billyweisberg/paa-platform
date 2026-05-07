# Phase H5 Superseded Cleanup Validation

Validated surfaces:
- source runtime command parsing
- fail-closed behavior on the live non-superseded fixture
- positive-path physical cleanup on a disposable synthetic `superseded` fixture

Commands used:

```bash
cd /Users/billyweisberg/Repos/billyweisberg/paa-platform
PYTHONPATH=packages/paa-consumer/src:packages/paa-core/src \
uv run --python 3.12 --no-project python -m paa_consumer.techlead superseded-cleanup --help
```

```bash
cd /Users/billyweisberg/Repos/billyweisberg/paa-platform
PYTHONPATH=packages/paa-consumer/src:packages/paa-core/src \
uv run --python 3.12 --no-project python -m paa_consumer.techlead superseded-cleanup \
  --repo-root /Users/billyweisberg/Repos/billyweisberg/fractal-core-python \
  --package-id-external fcore-stage1-2026-05-02-issue106-retirement-boundary-diagnostics \
  --brief-id-external fcore-coder-2026-05-02-issue106-retirement-boundary-diagnostics \
  --target-role python-team
```

Observed fail-closed result on the live fixture:
- `ok = false`
- `reason = superseded_not_supported_for_current_stage`
- `workflow_stage = dev_in_progress`
- lineage state remained `active`

Positive-path validation used:

```bash
cd /Users/billyweisberg/Repos/billyweisberg/paa-platform
PYTHONPATH=packages/paa-consumer/src:packages/paa-core/src \
uv run --python 3.12 --no-project python \
  /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/runtime/validate_phase_h5_superseded_cleanup_fixture.py
```

Observed positive result:
- `ok = true`
- `workflow_stage = qa_superseded`
- `cleanup_performed = true`
- `cleanup_result.worktree_removed = true`
- `cleanup_result.worktree_still_registered = false`
- `cleanup_result.branch_preserved = true`

Disposable fixture notes:
- the script provisions a disposable local `issue-106-dev` role branch if needed
- the script provisions a disposable registered role worktree at the deterministic default path
- the cleanup command removes that worktree
- the script verifies the branch still exists after cleanup
- the script removes its disposable branch in final cleanup if it created it
