# Automation Reference Audit and Removal Plan

## Purpose
This note completes the next hardening slice:
- audit active automation prompts/configs for legacy path assumptions
- identify any remaining legacy-path residue in platform-owned automation/template assets
- define removal timing for deprecated home-folder and duplicate producer-repo runtime surfaces

## Audit Scope
Audited surfaces:
- `<producer_repo_root>/.codex/automations/`
- `<consumer_repo_root>/.codex/automations/`
- `project-packs/fractal-core/automations/`
- `project-packs/fractal-core/skills/`
- repo-local installed skill surfaces under producer and consumer `.codex/skills/`
- platform packet example templates that could still communicate obsolete paths

Legacy path classes checked:
- `<codex_home>`
- `appdev-authority-source`
- `appdev-authority-source-clean`
- `appdev-arch`
- `tools/codex-skills`
- `fractal-core-python-automation-dev-source`
- `fractal-core-python-automation-qa-source`

## Findings

### 1. Active repo-local automations are clean enough to continue
The active repo-local automations in the canonical producer and consumer repos do not point at:
- `appdev-arch`
- `appdev-authority-source`
- `appdev-authority-source-clean`
- role-specific legacy consumer clones
- `tools/codex-skills`

They already use:
- repo-local `.codex/skills/...`
- repo-local runtime assumptions
- canonical producer or consumer repo cwd

This is the most important result from the audit.
The live operational automation surfaces are no longer anchored to the old topology.

### 2. Project-pack automation templates are also clean
The platform-owned Fractal Core project-pack automations use:
- `{{REPO_ROOT}}/.codex/skills/...`
- `{{REPO_ROOT}}` as cwd
- repo-local runtime instructions

They do not encode old repo/worktree paths.

### 3. Packet example templates still had legacy absolute paths
This was the main actionable residue found in platform-owned template assets.
Before cleanup, these files still embedded obsolete absolute paths:
- `templates/packet-examples/architect_cycle_packet.example.json`
- `templates/packet-examples/qa_verification_packet.example.json`
- `templates/packet-examples/slice_result_packet.example.json`

Those references pointed at:
- `appdev-authority-source`
- `$HOME/.codex/authority/...`

That residue has now been cleaned up and replaced with placeholders:
- `{{CODER_RUN_BRIEF_PATH}}`
- `{{CODER_RUN_BRIEF_SCHEMA_PATH}}`
- `{{AUTHORITY_MANIFEST_PATH}}`

### 4. Some platform docs still contain historical command examples with old paths
The automation/runtime prompt audit found one clear documentation residue area:
- `docs/4_Build/2026-05-03-coder-brief-readiness-materializer.md`

That doc still includes example commands referencing:
- `appdev-authority-source`

This is not an active automation/config problem, but it is a documentation cleanup follow-up.

## Audit Result Summary

| Surface | Result | Notes |
|---|---|---|
| Producer repo-local automations | pass | no legacy topology references found |
| Consumer repo-local automations | pass | no legacy topology references found |
| Project-pack automations | pass | templated on `{{REPO_ROOT}}` |
| Project-pack skills | pass | no legacy path references found in current search |
| Repo-local installed skills | pass | no legacy path references found in current search |
| Platform packet templates | cleanup required and completed | old absolute paths replaced with placeholders |
| Platform docs | follow-up required | historical example commands still mention old source lanes |

## Removal Timing Plan

### Phase A: Immediate safe removals are still blocked by prompt/reference cleanup
Do not remove these yet:
- `<codex_home>/skills/fractal-core-*`
- `<codex_home>/automations/*fractal-core*`
- `<producer_repo_root>/tools/codex-skills/...`

Reason:
- the active automations are clean, but we have not yet completed the broader automation prompt audit and operational runbook audit
- legacy docs, habits, or manual invocations may still reference these paths
- deleting them too early would make recovery/debugging harder if we discover one missed reference

### Phase B: Remove home-folder deprecated runtime first
Removal order should start with the deprecated home-folder project-specific runtime surfaces:
- `<codex_home>/skills/fractal-core-*`
- `<codex_home>/automations/*fractal-core*`

Why first:
- they are the highest confusion risk
- they are already explicitly deprecated and paused
- they are outside the canonical producer/consumer repo boundaries
- they are the easiest surfaces for future sessions to rediscover incorrectly

Prerequisite before removal:
- finish the broader automation prompt/runbook audit
- verify one clean end-to-end run using repo-local producer and consumer installs only

### Phase C: Remove duplicate producer-repo legacy skill/tool copies next
After home-folder removal is validated, remove:
- `<producer_repo_root>/tools/codex-skills/fractal-core-authority/...`
- `<producer_repo_root>/tools/codex-skills/fractal-core-handoff/...`
- `<producer_repo_root>/tools/codex-skills/install_fractal_core_skills.py`
- `<producer_repo_root>/tools/codex-skills/fractal-core-handoff/install_to_codex_skills.py`

Why second:
- they still live inside the canonical producer repo, so they can easily be mistaken for active producer tooling
- but they are less dangerous than the home-folder copies because the repo-local installs now exist and work

Prerequisite before removal:
- finish the helper-script follow-up for installer helpers
- verify no human runbooks or session prompts still invoke those old scripts

### Phase D: Leave transitional authority-source lanes as archives until final archival step
Keep these as historical/reference lanes for now:
- `<producer_repo_root>-authority-source/...`
- `<producer_repo_root>-authority-source-clean/...`

Why last:
- they are already classified as historical/archive surfaces
- they are less likely to be mistaken for live tooling than home-folder or canonical-producer duplicates
- they still contain useful recovery and historical context during the remaining hardening work

## Required Follow-Up Work
1. finish the broader automation prompt audit beyond the installed `automation.toml` files
   - include runbooks, skill instructions, and any launch helpers
2. clean the remaining platform docs that still embed old repo-path examples
3. run one explicit end-to-end producer-to-consumer flow using only:
   - repo-local producer install
   - repo-local consumer install
   - project-pack assets
4. after that, schedule home-folder Fractal Core runtime removal
5. then schedule duplicate `appdev/tools/codex-skills/...` removal

## Bottom Line
The good news is that the active automations are already in much better shape than the old topology suggested.
The main remaining risk is not that live automations still point at old paths.
The main remaining risk is that legacy helper surfaces still exist and look runnable.

So the removal strategy should be:
1. finish reference cleanup and one end-to-end validation
2. remove deprecated home-folder Fractal Core runtime
3. remove duplicate producer-repo legacy tool copies
4. keep transitional authority-source lanes as archives until final archival
