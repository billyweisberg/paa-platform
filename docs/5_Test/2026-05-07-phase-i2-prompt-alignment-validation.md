# Phase I2 Prompt Alignment Validation

## Purpose

Record that the current automation prompt surfaces no longer teach the obsolete shared full-cycle branch model or stale human-only TechLead behavior.

## Surfaces updated

Project-pack automation prompts:
- `project-packs/fractal-core/automations/fractal-core-techlead-automation/automation.toml`
- `project-packs/fractal-core/automations/fractal-core-delivery-architect-automation/automation.toml`
- `project-packs/fractal-core/automations/python-team-automation/automation.toml`
- `project-packs/fractal-core/automations/fractal-core-qa-automation/automation.toml`

Installed consumer copies:
- `<consumer_repo_root>/.codex/automations/fractal-core-techlead-automation/automation.toml`
- `<consumer_repo_root>/.codex/automations/fractal-core-delivery-architect-automation/automation.toml`
- `<consumer_repo_root>/.codex/automations/python-team-automation/automation.toml`
- `<consumer_repo_root>/.codex/automations/fractal-core-qa-automation/automation.toml`

## Validation performed

Checked that the updated prompt surfaces no longer contain:
- `shared full-cycle`
- `Do not auto-send new packets in this phase`

Observed result:
- `prompt-alignment-check=ok`

## Current prompt contract outcome

The prompts now teach:
- `TechLead` owns lineage, branch authorization, and routing decisions
- role automations may use deterministic role branches/worktrees only when authorized beneath TechLead-owned lineage
- `Python Dev` returns `worker_result_packet` to `TechLead`
- `Delivery Architect` returns `delivery_review_packet` to `TechLead`
- `QA` returns `qa_verification_packet` to `TechLead`
- obsolete shared-branch-only wording is removed from the active automation prompt layer
