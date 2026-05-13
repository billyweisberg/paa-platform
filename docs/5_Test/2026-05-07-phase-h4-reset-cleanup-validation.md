# Phase H4 Physical Reset Cleanup Validation

Validated surfaces:
- source runtime command parsing
- installed consumer wrapper exposure
- fail-closed behavior on the live non-reset fixture
- positive-path physical cleanup on a disposable synthetic `dev_reset_required` fixture

Commands used:

```bash
cd <paa_platform_repo_root>
PYTHONPATH=packages/paa-consumer/src:packages/paa-core/src \
uv run --python 3.12 --no-project python -m paa_consumer.techlead reset-cleanup --help
```

```bash
cd <consumer_repo_root>
./.codex/paa/bin/paa-consumer techlead-reset-cleanup \
  --repo-root <consumer_repo_root> \
  --package-id-external fcore-stage1-2026-05-02-issue106-retirement-boundary-diagnostics \
  --brief-id-external fcore-coder-2026-05-02-issue106-retirement-boundary-diagnostics \
  --target-role python-team
```

Observed fail-closed result on the live fixture:
- `ok = false`
- `reason = reset_required_lifecycle_unavailable`
- nested lifecycle refusal:
  - `reason = reset_required_not_supported_for_current_stage`
  - `workflow_stage = dev_in_progress`

Positive-path validation used:

```bash
cd <paa_platform_repo_root>
PYTHONPATH=packages/paa-consumer/src:packages/paa-core/src \
uv run --python 3.12 --no-project python \
  scripts/runtime/validate_phase_h4_reset_cleanup_fixture.py
```

Observed positive result:
- `ok = true`
- `workflow_stage = dev_reset_required`
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
