# Phase H6 Closed Cleanup Validation

Validated surfaces:
- source runtime command parsing
- fail-closed behavior on the live non-closed fixture
- positive-path physical cleanup on a disposable synthetic `closed` fixture

Commands used:

```bash
cd <paa_platform_repo_root>
PYTHONPATH=packages/paa-consumer/src:packages/paa-core/src \
uv run --python 3.12 --no-project python -m paa_consumer.techlead closed-cleanup --help
```

```bash
cd <paa_platform_repo_root>
PYTHONPATH=packages/paa-consumer/src:packages/paa-core/src \
uv run --python 3.12 --no-project python -m paa_consumer.techlead closed-cleanup \
  --repo-root <consumer_repo_root> \
  --package-id-external fcore-stage1-2026-05-02-issue106-retirement-boundary-diagnostics \
  --brief-id-external fcore-coder-2026-05-02-issue106-retirement-boundary-diagnostics \
  --target-role python-team
```

Observed fail-closed result on the live fixture:
- `ok = false`
- `reason = closed_not_supported_for_current_stage`
- `workflow_stage = dev_in_progress`
- lineage state remained `active`

Positive-path validation used:

```bash
cd <paa_platform_repo_root>
PYTHONPATH=packages/paa-consumer/src:packages/paa-core/src \
uv run --python 3.12 --no-project python \
  scripts/runtime/validate_phase_h6_closed_cleanup_fixture.py
```

Observed positive result:
- `ok = true`
- `workflow_stage = slice_closed`
- `cleanup_performed = true`
- `cleanup_result.worktree_removed = true`
- `cleanup_result.worktree_still_registered = false`
- `cleanup_result.role_branch_preserved = true`
- `cleanup_result.canonical_branch_preserved = true`

Disposable fixture notes:
- the script provisions a disposable local `issue-106-dev` role branch if needed
- the script provisions a disposable registered role worktree at the deterministic default path
- the cleanup command removes that worktree
- the script verifies both role and canonical branches remain present after cleanup
- the script removes its disposable role branch in final cleanup if it created it
