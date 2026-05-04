# Full-Cycle Branch Policy

## Purpose

The Fractal Core PAA workflow uses one shared implementation branch for the full issue cycle.
This avoids role-specific branch drift and keeps Delivery Architect, Dev, QA, and merge validation aligned on the same code line.

## Policy

For each issue under implementation, use exactly one branch in the canonical consumer repo:

- `issue-<issue_number>`

Examples:

- `issue-101`
- `issue-103`
- `issue-106`

## Rules

- Delivery Architect, Dev, and QA all use the same issue branch.
- Do not create role-specific branches such as:
  - `dev/issue-106`
  - `qa/pr-107`
  - `architect/issue-106`
  - `codex/issue-106-*`
- Do not invent descriptive branch suffixes during the active implementation cycle.
- If a branch does not exist yet for the issue, create `issue-<issue_number>` in the canonical consumer repo and reuse it for the whole cycle.
- Producer-side authority work remains in the canonical producer repo and does not create consumer role branches.

## Canonical Repos

Producer:
- `/Users/billyweisberg/Repos/Individual-Centricity/appdev`

Consumer:
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python`

## Why This Policy Exists

This policy prevents:

- random automation-created branch names
- stale PR-head clones becoming quasi-canonical
- QA and Dev validating different code lines
- TechLead and traceability reports referring to branch names that do not match the actual merged line

## Validation Expectations

Each automation step should treat the following as the expected branch for issue `<N>`:

- `issue-<N>`

TechLead and future runtime guardrails should flag branch names that do not follow this policy.
