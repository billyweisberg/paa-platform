# Purpose

Add the first narrow result compile/send bridge back to `TechLead`.

This slice intentionally does only four things:
- consume the role-result-assist context
- compile the role result packet
- validate the compiled packet and resolve the queue
- optionally send it through the existing queue/control spine

## Command

```bash
<consumer_repo>/.codex/paa/bin/paa-consumer techlead-role-return \
  --repo-root <consumer_repo> \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role <delivery-architect|python-team|qa> \
  [--send]
```

Optional overrides:
- `--role-branch`
- `--worktree-path`
- `--assignment-path`
- `--assignment-review-output`
- `--result-input-path`
- `--output`
- `--review-output`

## Behavior

The command builds on `techlead-role-result-assist`.

If the assist context is valid and the role result input file exists, it returns:
- compile result
- validation result
- resolved queue
- send result when `--send` is requested

## Transitional queue mapping

This bridge intentionally preserves the current Phase A physical queue names:

- `worker_result_packet` -> `fractal-core-architecture`
- `qa_verification_packet` -> `fractal-core-architecture`
- `delivery_review_packet` -> `fractal-core-architecture`

That keeps the transport model aligned with the current TechLead-owned semantic routing model.

Legacy compatibility note:
- `slice_result_packet` still exists as a legacy Python lane artifact
- it is no longer the active default used by the Python role-return bridge

## Scope

This command does not:
- create the role worktree
- execute Dev or QA work
- claim or acknowledge the returned packet
- infer a broader next-step decision
