# QA Automation Prompt Recovery

## Purpose

Recover the best historically-developed prompt intent for the `Fractal Core QA Automation`.

## Recovery Sources Reviewed

### Current authoritative sources
- `project-packs/fractal-core/automations/fractal-core-qa-automation/automation.toml`
- `project-packs/fractal-core/skills/fractal-core-qa-review/SKILL.md`

### Installed consumer copies
- `<consumer_repo_root>/.codex/automations/fractal-core-qa-automation/automation.toml`
- `<consumer_repo_root>/.codex/skills/fractal-core-qa-review/SKILL.md`

### Historical committed prompt surfaces
- commit `0f1ddcb`
- commit `31a93dd`
- commit `e9a5885`
- commit `6e0d090`
- earlier skill history for `fractal-core-qa-review`
- pre-hub richer QA skill text from commit `e7f0426`

### Home-level UI registration surface
- `<codex_home>/automations/fractal-core-qa-automation/automation.toml`

## Earliest Durable Wrapper Intent

Recovered early wrapper intent:

```text
Use repo-local consumer runtime only.
Use installed authority package under `.project/data/paa/authority/current`.
Use the canonical consumer repo root.
Use the same shared full-cycle issue branch as Delivery Architect and Dev: `issue-<issue_number>`.
```

This reflected the older shared-branch model.
It is historically important, but it is not the final target-state execution contract.

## Earliest Rich Skill Intent

The earlier QA skill carried valuable review discipline:

- independently verify a completed Dev slice
- use issue and PR as the implementation record
- consult authority docs before recommending merge
- verify issue authorization before acceptance
- perform mechanical, technical-scope, protected-path, and artifact checks
- distinguish `pass`, `fail`, and `needs_human_review` carefully

That review discipline is still valuable even though the routing model changed.

## Current High-Value Prompt Intent

Later work added the stronger execution and routing boundaries:

- QA preflights without model invocation first
- QA receives prepared role worktree context from TechLead
- QA returns only `qa_verification_packet` to TechLead
- QA does not route directly to Architect

## Recovered Canonical QA Prompt Intent

```text
Act as QA only.
Use repo-local consumer runtime only.
Use installed authority under `.project/data/paa/authority/current`.
Launch from the canonical consumer repo root.
Poll for work first and do not invoke the model if there is no claimable assignment.

Receive assignments only from TechLead.
Return only `qa_verification_packet` to TechLead.
Do not route directly to Architect.

Use the canonical issue branch unless TechLead explicitly authorizes an isolated deterministic role branch.
If isolated execution is authorized, use the prepared deterministic QA role worktree such as `issue-<issue_number>-qa`.
Do not invent branch names.

Perform verification with explicit review domains:
- mechanical checks
- technical scope checks
- protected-path checks
- artifact checks

Use issue, PR, and authority as the implementation and acceptance record.
Fail closed if:
- there is no work
- the prepared worktree is missing
- the branch is wrong
- runtime truth comes from deprecated home-folder assets instead of repo-local installs
```

## Prompt Elements Worth Preserving

- QA as an independent verification role
- authority-aware review discipline
- protected-path and artifact review
- no-work preflight gate
- prepared worktree intake
- return to TechLead only
- explicit distinction between fail, scope failure, and human-review cases

## Regressions To Avoid

Do not regress QA back to:
- direct QA-to-Architect routing
- wrapper-only prompts with no review-domain discipline
- shared-branch-only assumptions as the only model
- prompt text that ignores prepared worktree and repo-local runtime truth

## Recovery Conclusion

The strongest QA prompt combines:
- early review-depth and authority discipline
- later TechLead-owned routing discipline
- later prepared-worktree execution discipline
