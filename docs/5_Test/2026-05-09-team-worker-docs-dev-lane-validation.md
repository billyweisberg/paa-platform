# Team Worker Roles Docs Dev Lane Validation

## Scope

Validate one full additional non-Python Team Worker Role lane using `Docs Dev`.

This validation targeted the Stage W6 proving goal:
- `TechLead -> Docs Dev -> TechLead`
- plus the immediate `TechLead -> QA` derivation off the returned docs worker result

## Inputs

- consumer repo:
  - `<consumer_repo_root>`
- platform repo:
  - `<paa_platform_repo_root>`
- issue fixture:
  - `106`
- PR fixture:
  - `107`
- package id:
  - `fcore-stage1-2026-05-02-issue106-retirement-boundary-diagnostics`
- brief id:
  - `fcore-coder-2026-05-02-issue106-retirement-boundary-diagnostics`

## Validation Steps

1. confirmed all three queues started at zero
2. executed `techlead-handoff-to-role-worktree --target-role docs-dev`
3. observed successful assignment compilation and successful role branch/worktree preparation
4. executed `techlead-role-result-assist --target-role docs-dev`
5. created a minimal valid `worker_result_packet` input for `Docs Dev`
6. executed `techlead-role-return --target-role docs-dev --send`
7. executed `techlead-emit-next-assignment` with the returned docs worker packet still pending on `fractal-core-architecture`
8. confirmed QA derivation
9. removed the disposable `issue-106-docs` worktree and role branch
10. claimed and acknowledged the returned docs worker packet
11. confirmed all three queues settled back to zero

## Expected Outputs

- Docs Dev assignment compiles and validates
- Docs Dev role branch/worktree can be prepared through the generic worker bridge
- Docs Dev worker result compiles, validates, and sends as `worker_result_packet`
- TechLead derives a QA assignment from the returned docs worker packet
- disposable runtime state is cleaned up after the proof

## Observed Results

### Handoff and worktree preparation

`techlead-handoff-to-role-worktree --target-role docs-dev` returned:
- `ok = true`
- `target_role = Docs Dev`
- `resolved_queue = fractal-core-python`
- `role_branch = issue-106-docs`
- `worktree_path = <codex_home>/worktrees/paa/fractal-core-python/issue-106-docs`
- `branch_aligned = true`

### Role result return

`techlead-role-return --target-role docs-dev --send` returned:
- `ok = true`
- `result_family = worker_result_packet`
- `message_id = fcore-worker-2026-05-09-issue106-docs-dev`
- `resolved_queue = fractal-core-architecture`
- `from_role = docs-dev`
- `to_role = techlead`
- `sent = true`

### TechLead next-assignment derivation

`techlead-emit-next-assignment` with the returned docs worker packet pending returned:
- `ok = true`
- `workflow_stage = techlead_worker_review_pending`
- `derived_decision.target_role = QA`
- `derived_decision.assignment_type = verify_authorized_slice`
- `resolved_queue = fractal-core-qa`
- `source_packet_ref.message_id = fcore-worker-2026-05-09-issue106-docs-dev`

### Cleanup

- disposable role worktree removed
- disposable role branch deleted
- returned docs worker packet claimed and acknowledged
- queues settled to zero:
  - `fractal-core-python`
  - `fractal-core-qa`
  - `fractal-core-architecture`

## Real Fixes Required During This Proof

This proof exposed and forced real follow-up fixes:
- producer-side TechLead assignment compiler target-role choices were still fixed to `python-team`
- consumer-side TechLead assignment queue mapping did not yet derive Team Worker Role queue bindings from the registry
- role-worktree handoff still treated only `Python Dev` as a supported generic worker target
- TechLead next-assignment derivation still expected `techlead_dev_review_pending` instead of the generalized `techlead_worker_review_pending`
- a small dispatch bug in `paa_consumer.inbox.dispatch_packet()` referenced `schema_type` before assignment

Those fixes are now part of the implementation slice that enabled this proof.

## Residual Note

During this proof, `techlead-status --validate-schema` hit a vendored `jsonschema` / `rpds` import failure in the installed consumer runtime. That did not block the Team Worker Roles lane proof itself, but it remains an operational hardening defect to address separately.

## Verdict

- Stage W6 Docs Dev proving lane: `pass`

## What This Proves

- a non-Python Team Worker Role can now use the generic worker bridge end to end
- the Team Worker registry is now influencing:
  - assignment compilation
  - queue resolution
  - role branch naming
  - role worktree preparation
  - worker result compilation
  - TechLead follow-up derivation

## Next Step

1. finish the remaining launcher/bootstrap and UI-surface details inside Stage W5
2. then move to Stage W7 and re-baseline the paused automation pilot work against the Team Worker Roles model
