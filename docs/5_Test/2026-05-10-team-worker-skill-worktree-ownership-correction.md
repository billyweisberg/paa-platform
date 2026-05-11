# Team Worker Skill Worktree Ownership Correction

## Purpose

Record the correction made after the live `Stage W7 Phase 4` Python Dev run exposed a mismatch between the Team Worker role-ownership model and the shared Team Worker execution skill.

## Observed failure

During the app-launched `Python Team Automation` run for issue `108`:
- the automation successfully claimed the TechLead assignment packet
- the role then failed at `techlead-inspect-role-worktree`
- the expected worktree path was:
  - `/Users/billyweisberg/.codex/worktrees/paa/fractal-core-python/issue-108-dev`
- the runtime reported that the worktree was not registered

Result:
- no implementation work could begin
- no valid `worker_result_packet` could be returned
- the live pilot stalled even though the assignment itself was valid

## Root cause

The Team Worker runtime contract already said that role automations own create-or-reuse of their deterministic worktree beneath TechLead-authorized lineage.

But the shared Team Worker execution skill still taught this order:
1. inspect role worktree
2. role entry
3. execute work

That order incorrectly assumed the worktree had already been created by TechLead.

## Fix

Updated the Team Worker execution skill so the required flow is now:
1. `techlead-prepare-role-worktree`
2. `techlead-inspect-role-worktree`
3. `techlead-role-entry`
4. execute work from the prepared worktree
5. `techlead-role-result-assist`
6. `techlead-role-return --send`

Updated source skill:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/project-packs/fractal-core/skills/fractal-core-dev-result/SKILL.md`

Updated installed consumer skill:
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/skills/fractal-core-dev-result/SKILL.md`

Updated contract:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/6_Deploy/2026-05-09-team-worker-automation-contract.md`

## Validation

The missing live worktree was then prepared successfully with:
- role branch: `issue-108-dev`
- worktree path: `/Users/billyweisberg/.codex/worktrees/paa/fractal-core-python/issue-108-dev`

The previously claimed assignment was requeued so the Python automation could retry against the corrected role contract.

## Result

This closes the specific “TechLead must pre-register Team Worker worktree” mismatch.

Remaining follow-up:
- rerun the Python Team automation on issue `108`
- confirm the corrected skill lets the role proceed from prepare-or-reuse into execution without another manual worktree intervention
