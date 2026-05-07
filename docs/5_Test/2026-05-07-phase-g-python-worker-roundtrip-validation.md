# Phase G Python Worker Result Round-Trip Validation

This validation proves the active Python bridge can run on:

- `worker_result_packet`

while keeping legacy `slice_result_packet` support intact.

## Scope

Validated:

1. TechLead emits Python assignment
2. Python role branch/worktree is prepared
3. Python role return compiles `worker_result_packet`
4. returned packet validates and sends to TechLead
5. TechLead derives the next QA assignment from the returned generic worker packet

Not changed:

- `materialize-slice-result-packet` still exists
- runtime acceptance for `slice_result_packet` still exists

## Commands used

### Handoff

```bash
/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-consumer techlead-handoff-to-role-worktree \
  --repo-root /Users/billyweisberg/Repos/billyweisberg/fractal-core-python \
  --package-id-external fcore-stage1-2026-05-02-issue106-retirement-boundary-diagnostics \
  --brief-id-external fcore-coder-2026-05-02-issue106-retirement-boundary-diagnostics \
  --target-role python-team \
  --send \
  --role-branch issue-106-dev-phaseg-worker
```

### Return

```bash
/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-consumer techlead-role-return \
  --repo-root /Users/billyweisberg/Repos/billyweisberg/fractal-core-python \
  --package-id-external fcore-stage1-2026-05-02-issue106-retirement-boundary-diagnostics \
  --brief-id-external fcore-coder-2026-05-02-issue106-retirement-boundary-diagnostics \
  --target-role python-team \
  --role-branch issue-106-dev-phaseg-worker \
  --result-input-path /Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.project/data/paa/reports/role-result-input.issue106.python-dev.json \
  --send
```

### TechLead follow-up derivation

```bash
/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-consumer techlead-emit-next-assignment \
  --repo-root /Users/billyweisberg/Repos/billyweisberg/fractal-core-python \
  --package-id-external fcore-stage1-2026-05-02-issue106-retirement-boundary-diagnostics \
  --brief-id-external fcore-coder-2026-05-02-issue106-retirement-boundary-diagnostics
```

## Observed results

### Python handoff

- `ok = true`
- `target_role = Python Dev`
- `resolved_queue = fractal-core-python`
- disposable role branch/worktree prepared successfully

### Python return

- `ok = true`
- `result_family = worker_result_packet`
- `resolved_queue = fractal-core-architecture`
- `sent = true`

Compiled output:

- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.project/data/paa/reports/worker-result.issue106.python-dev.json`

### TechLead next-step derivation

After the returned worker packet landed, TechLead derived:

- `workflow_stage = techlead_dev_review_pending`
- `target_role = QA`
- `assignment_type = verify_authorized_slice`
- `resolved_queue = fractal-core-qa`

That is the key migration proof:

- Python no longer needs `slice_result_packet` to drive the Dev -> TechLead -> QA flow

## Cleanup

Validation cleanup completed:

- disposable Python queue message acknowledged
- disposable architecture queue message acknowledged
- both queues returned to zero ready / zero unacknowledged
- disposable role branch deleted:
  - `issue-106-dev-phaseg-worker`
- disposable worktree removed

## Conclusion

The active Python bridge now works on `worker_result_packet`.

This means Phase G can proceed with:

- treating `worker_result_packet` as the active Python bridge result family
- demoting `slice_result_packet` to legacy compatibility rather than active default guidance
