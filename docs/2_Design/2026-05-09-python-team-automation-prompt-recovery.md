# Python Team Automation Prompt Recovery

## Purpose

Recover the best historically-developed prompt intent for the `Python Team Automation`.

## Recovery Sources Reviewed

### Current authoritative sources
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/project-packs/fractal-core/automations/python-team-automation/automation.toml`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/project-packs/fractal-core/skills/fractal-core-dev-result/SKILL.md`

### Installed consumer copies
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/automations/python-team-automation/automation.toml`
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/skills/fractal-core-dev-result/SKILL.md`

### Historical committed prompt surfaces
- commit `0f1ddcb`
- commit `31a93dd`
- commit `e9a5885`
- commit `6e0d090`
- commit `409173d`
- earlier skill history for `fractal-core-dev-result`

### Home-level UI registration surface
- `/Users/billyweisberg/.codex/automations/python-team-automation/automation.toml`

## Earliest Durable Wrapper Intent

Recovered early wrapper intent:

```text
Use repo-local consumer runtime only.
Use installed authority package under `.project/data/paa/authority/current`.
Use the canonical consumer repo root.
Use one shared full-cycle issue branch per issue: `issue-<issue_number>`.
Do not read project runtime from `$HOME/.codex`.
```

This reflected the older shared-branch model.
It is historically important, but it is not the final target-state execution contract.

## Current High-Value Prompt Intent

The later skill work added the real operational value:

- Python Dev preflights without model invocation first
- Python Dev receives prepared role worktree context from TechLead
- Python Dev performs work inside the prepared worktree
- Python Dev prefers `uv run` from that worktree
- Python Dev returns only `worker_result_packet` to TechLead
- Python Dev must not route directly to QA

## Recovered Canonical Python Team Prompt Intent

```text
Act as Python Dev only.
Use repo-local consumer runtime only.
Use installed authority under `.project/data/paa/authority/current`.
Launch from the canonical consumer repo root.
Poll for work first and do not invoke the model if there is no claimable assignment.

Receive assignments only from TechLead.
Return only `worker_result_packet` to TechLead.
Treat `slice_result_packet` as legacy compatibility only, not the active execution lane.
Do not route directly to QA.

Use the canonical issue branch unless TechLead explicitly authorizes an isolated deterministic role branch.
If isolated execution is authorized, use the prepared deterministic Python role worktree such as `issue-<issue_number>-dev`.
Do not invent branch names.
Do not silently switch to unrelated interpreter state.
Prefer `uv run` from the prepared worktree for repo work.

Fail closed if:
- there is no work
- the prepared worktree is missing
- the branch is wrong
- runtime truth comes from deprecated home-folder assets instead of repo-local installs
```

## Prompt Elements Worth Preserving

- repo-local runtime discipline
- authority package discipline
- no-work preflight gate
- prepared worktree intake
- `uv run` preference from the worktree
- return to TechLead only
- explicit rejection of direct Dev-to-QA routing

## Regressions To Avoid

Do not regress Python Team back to:
- shared-branch-only assumptions as the only model
- `slice_result_packet` as the active default lane
- direct routing to QA
- prompt text that ignores the prepared role worktree and execution-environment contract

## Recovery Conclusion

The strongest Python Team prompt is not the oldest one.
The best recovered version combines:
- early repo-local and authority discipline
- later TechLead-owned routing discipline
- later worktree and `uv` execution discipline
