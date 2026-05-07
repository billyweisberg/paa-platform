# Phase I2 UI Registration Alignment

## Purpose

Record the current home-level Codex automation registration state for the current proven consumer role set.

## Global UI registration surface

The Codex UI currently discovers automation registrations from:
- `/Users/billyweisberg/.codex/automations/`

This is distinct from the repo-local installed automation surfaces under:
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/automations/`

## Changes applied

The following home-level UI registration entries are now present and current:
- `/Users/billyweisberg/.codex/automations/fractal-core-techlead-automation/automation.toml`
- `/Users/billyweisberg/.codex/automations/fractal-core-delivery-architect-automation/automation.toml`
- `/Users/billyweisberg/.codex/automations/python-team-automation/automation.toml`
- `/Users/billyweisberg/.codex/automations/fractal-core-qa-automation/automation.toml`

The following legacy state was corrected:
- `/Users/billyweisberg/.codex/automations/python-team-automation/automation.toml`
  - previously a deprecated placeholder
  - now replaced with a current runnable registration surface

## Current result

The home-level UI registration layer is now real for the current proven role set:
- `TechLead`
- `Delivery Architect`
- `Python Dev`
- `QA`

This does not yet mean the automations are execution-ready.
It means the UI-visible registration dependency is now satisfied.

## Remaining readiness work

Still required before deliberate unpause:
- prompt contract alignment
- deterministic pre-run no-work gate
- explicit execution-environment contract for worktree, `uv`, cwd, and env vars
- dedicated Delivery Architect execution skill
- hardened Python Dev and QA execution-agent skills
