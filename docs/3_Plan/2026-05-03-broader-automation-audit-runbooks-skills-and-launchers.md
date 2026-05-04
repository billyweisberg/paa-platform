# Broader Automation Audit: Runbooks, Skills, and Launch Helpers

## Purpose
This note extends the automation audit beyond `automation.toml` files.
It covers:
- skill prompts
- repo-local automation/readme runbooks
- repo-local launch helpers under `.codex/paa/bin/`
- remaining platform-doc examples that could still teach obsolete topology

## Scope Reviewed
Reviewed surfaces:
- `/Users/billyweisberg/Repos/Individual-Centricity/appdev/.codex/`
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/project-packs/`
- relevant platform docs under `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/`

Legacy path classes checked:
- `/Users/billyweisberg/.codex`
- `appdev-authority-source`
- `appdev-authority-source-clean`
- `appdev-arch`
- `tools/codex-skills`
- `fractal-core-python-automation-dev-source`
- `fractal-core-python-automation-qa-source`
- `.codex/authority/`

## Findings

### 1. Installed skill prompts are topology-clean
Current project-pack skills and repo-local installed skills do not reference old producer/source-clean lanes, old role clones, or `$HOME/.codex` runtime roots.

This is true for the currently active Fractal Core skill surfaces such as:
- `fractal-core-authority`
- `fractal-core-techlead`
- `fractal-core-inbox`
- `fractal-core-qa-review`
- `fractal-core-architect-handoff`

The skills are now aligned with repo-local installs and repo-local runtime expectations.

### 2. Repo-local readme/runbook surfaces are also clean
These repo-local readme surfaces do not encode old topology assumptions:
- `/Users/billyweisberg/Repos/Individual-Centricity/appdev/.codex/automations/README.md`
- `/Users/billyweisberg/Repos/Individual-Centricity/appdev/.codex/paa/README.md`
- `/Users/billyweisberg/Repos/Individual-Centricity/appdev/.codex/skills/README.md`
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/automations/README.md`
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/README.md`
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/skills/README.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/project-packs/README.md`

These are safe to keep as current runbook surfaces.

### 3. Repo-local launch helpers are topology-clean but environment-specific
Launch helpers currently do the right thing with topology:
- they resolve repo-local `vendor` and `lib` roots relative to the repo
- they do not reference `$HOME/.codex`
- they do not reference old producer/source or role-workspace paths

But they currently hardcode:
- `/opt/homebrew/bin/python3.12`

That is not a topology bug.
It is the upcoming environment/bootstrap problem and should be handled in the dedicated `uv` strategy slice.

Affected launch helpers include:
- `/Users/billyweisberg/Repos/Individual-Centricity/appdev/.codex/paa/bin/paa-producer`
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-consumer`
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-producer`

### 4. One platform build doc still had obsolete source-lane examples
This file still contained historical example commands pointing at `appdev-authority-source`:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/4_Build/2026-05-03-coder-brief-readiness-materializer.md`

That residue has now been cleaned.
The examples now use:
- `<producer_repo>/...`

### 5. Prompt quality still needs a separate refinement pass
The broader audit did not find legacy-path leakage in the installed skills, but it did confirm a different class of cleanup still ahead:
- prompt clarity
- command completeness
- role-specific instruction sharpness
- avoiding placeholder shorthand like vague `...` examples where they reduce operational reliability

That is a prompt-quality and workflow-review issue, not a topology-residue issue.

## Audit Result Summary

| Surface | Result | Notes |
|---|---|---|
| Repo-local installed skills | pass | no old topology references found |
| Project-pack skills | pass | no old topology references found |
| Repo-local readme/runbook surfaces | pass | current repo-local guidance is aligned |
| Repo-local launch helpers | pass with follow-up | topology-clean; hardcoded interpreter path remains for `uv` slice |
| Platform build docs | cleanup required and completed | one old source-lane example updated |
| Prompt quality | follow-up required | not a path/reference failure, but still needs review |

## What This Means For Removal Timing
This broader audit removes one major blocker from the removal plan:
- active skill prompts and repo-local runbook surfaces are not secretly pointing back at legacy paths

That means the remaining blockers are narrower:
1. end-to-end validation using repo-local runtime only
2. `uv` bootstrap strategy for consistent interpreter/runtime setup
3. prompt-quality review before re-enabling automations

## Updated Removal Confidence

### Home-folder deprecated Fractal Core runtime
Confidence to remove after E2E + bootstrap validation: high

Reason:
- active automations are clean
- installed skills are clean
- repo-local runbooks are clean
- the remaining risk is now operational validation, not hidden reference leakage

### Producer-repo duplicate legacy tool copies
Confidence to remove after E2E + prompt/runbook validation: medium-high

Reason:
- they are no longer referenced by active repo-local automations or installed skills
- but they still sit inside the canonical producer repo and may still be manually invoked by habit

### Transitional authority-source lanes
Confidence to leave archived for now: high

Reason:
- they are not active configuration surfaces
- they still carry historical context that can help during the remaining hardening work

## Recommended Next Slices
1. define the `uv` / session bootstrap strategy
2. define the end-to-end validation plan
3. then review automation prompts for quality and operational clarity before re-enabling any automation cadence

## Bottom Line
The broader automation audit came back better than expected.
We did not find hidden old-topology references inside the active installed skills, repo-local readmes, or launch wrappers.

The remaining work is now clearer:
- environment/bootstrap consistency
- prompt quality
- one clean end-to-end validation

That is a much narrower and more manageable hardening problem than another hidden-topology cleanup.
