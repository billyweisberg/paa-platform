# Stage W7 Phase 3 Team Worker Launch Environment Validation

## Verdict

- `Stage W7 Phase 3: pass`

## Goal

Validate one app-launched Team Worker automation against the real runtime and environment contract.

## Proving role

- `Docs Dev`

## Inputs

- consumer repo root:
  - `<consumer_repo_root>`
- Team Worker automation under test:
  - `Docs Dev Automation`
- assignment packet emitted on May 9, 2026 to:
  - `fractal-core-python`
- prepared role branch:
  - `issue-106-docs`
- prepared role worktree:
  - `<codex_home>/worktrees/paa/fractal-core-python/issue-106-docs`
- package id external:
  - `fcore-stage1-2026-05-02-issue106-retirement-boundary-diagnostics`
- brief id external:
  - `fcore-coder-2026-05-02-issue106-retirement-boundary-diagnostics`

## What was verified from disk

### 1. App-launched preflight woke only because work existed

Latest Docs Dev app-launched run:
- `<consumer_repo_root>/.project/data/paa/logs/automations/docs-dev-automation/2026-05-10T13-39-19Z-46312`

Observed in `summary.json` and `preflight.json`:
- `should_invoke_model = true`
- `skip_model_invocation = false`
- `gate_reason = claimable_assignment_packet_available`
- pending queue candidate:
  - `message_id = fcore-techlead-2026-05-09-issue106-implement_authorized_slice`
  - `schema_type = techlead_assignment_packet`
  - `to_role = docs-dev`

This proves the app-launched automation passed through the installed logged-preflight gate and correctly woke only because claimable work was present.

### 2. The Team Worker execution surface remained aligned

Observed after the run:
- `fractal-core-python` queue returned to zero
- prepared worktree remained registered and aligned
- worktree branch remained:
  - `issue-106-docs`
- worktree head remained:
  - `31a93ddcf2334875851955aff84fa9981c3de547`
- worktree was clean:
  - no tracked file modifications

Verified via:
- `techlead-worktree-ownership`
- `techlead-worktree-stale`
- direct git inspection of the prepared role worktree

Observed ownership/staleness state after the run:
- `workflow_stage = techlead_worker_review_pending`
- `runtime_owner_role = Docs Dev`
- `registered = true`
- `branch_aligned = true`
- `worktree_staleness.status = active`
- `cleanup_candidate = false`

### 3. The app-launched role returned a valid Team Worker packet

Observed pending on `fractal-core-architecture`:
- `message_id = fcore-worker-2026-05-10-issue106-docs-dev`
- `schema_type = worker_result_packet`
- `from_role = docs-dev`
- `to_role = techlead`
- `payload.worker_role = Docs Dev`
- `payload.worker_family = docs`
- `payload.result_type = blocked`

Packet file:
- `<consumer_repo_root>/.project/data/paa/reports/worker-result.issue106.docs-dev.json`

The payload documents a stale assignment condition:
- issue `#106` is already closed
- PR `#107` is already merged
- no docs edits were needed
- recommended TechLead action:
  - `clear_stale_assignment`

## Important observability limitation

The current repo-local logging contract only captured the deterministic preflight phase.

It did **not** yet capture the later role-execution milestones from the app-launched run, such as:
- packet claim
- worktree inspection
- GitHub inspection
- result packet compile/send
- queue acknowledgment

Those later actions are still evidenced indirectly by runtime state and the returned packet, not by the same run log envelope.

So this phase passes for launch/runtime coherence, but there is still an observability gap to harden.

## Success criteria check

This phase required:
- automation wakes only because work exists
- correct repo root launch context
- deterministic Team Worker role worktree path
- correct `worker_result_packet` role identity

Result:
- all required success criteria passed

## What this proves

The app-launched `Docs Dev Automation` can:
- pass through the Team Worker-aware logged preflight gate
- wake only on claimable work
- operate against the prepared deterministic Team Worker worktree surface
- return a valid `worker_result_packet` to `TechLead`

## What it does not prove yet

- end-to-end run logging beyond preflight
- final Codex-native worktree-mode automation design
- a fresh live implementation slice that produces new Team Worker changes

## Fixture note

This proof used issue `#106`, which is already closed and merged.
That made the returned packet a valid stale-assignment `blocked` result instead of a fresh implementation result.

That is acceptable for Phase 3 because this phase is about launch/runtime coherence.
It is **not** sufficient for Phase 4.

## Next step

- proceed to `Stage W7 Phase 4: supervised Team Worker live pilot slice`
- use a fresh disposable fixture instead of reusing closed issue `#106`
