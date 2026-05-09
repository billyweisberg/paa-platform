# TechLead Automation Definition

## Purpose

Define the intended role, launch model, execution contract, and authoritative source surfaces for the `Fractal Core TechLead Automation`.

This document exists so the automation can be reviewed as a first-class design artifact rather than only as TOML text spread across multiple install locations.

## Automation identity

- automation id:
  - `fractal-core-techlead-automation`
- display name:
  - `Fractal Core TechLead Automation`
- role:
  - `TechLead`
- current cadence:
  - `RRULE:FREQ=MINUTELY;INTERVAL=30`
- current model:
  - `gpt-5.4`
- current reasoning effort:
  - `medium`

## Primary responsibility

`TechLead` is the consumer-side routing hub.

The automation is responsible for:
- reading TechLead-visible workflow state
- interpreting returned role packets
- recording durable routing/lifecycle decisions
- emitting the next assignment in supported cases
- owning canonical lineage and role-branch authorization
- never routing around `TechLead`

It is not responsible for:
- doing Delivery Architect work
- doing Python Dev work
- doing QA work
- directly executing spoke-role implementation or verification tasks

## Authoritative source surfaces

### Project-pack source of truth
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/project-packs/fractal-core/automations/fractal-core-techlead-automation/automation.toml`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/project-packs/fractal-core/skills/fractal-core-techlead/SKILL.md`

### Installed consumer copy
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/automations/fractal-core-techlead-automation/automation.toml`
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/skills/fractal-core-techlead/SKILL.md`

### Home-level UI registration surface
- `/Users/billyweisberg/.codex/automations/fractal-core-techlead-automation/automation.toml`

## Launch model

### Current launch surface
- `execution_environment = "local"`
- launch cwd:
  - `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python`

### Intended meaning of `local`

`local` is intended to mean:
- launch from the canonical consumer repo root
- use repo-local installed wrappers
- inspect queue/runtime state from the consumer repo root
- prepare or inspect role branches/worktrees as needed
- do not assume that all actual role execution happens on the repo root

It is not intended to mean:
- execute spoke-role work on the shared repo root
- skip deterministic role worktree transitions

## Runtime contract

### Canonical consumer repo root
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python`

### Required wrapper surfaces
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-consumer`
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-producer`

### Required authority surface
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.project/data/paa/authority/current/authority/fractal-core-python-authority.json`

### Required queue/runtime state root
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.project/data/paa/queue-state/fractal-core-handoff`

### Required pre-run behavior
Before model invocation, the automation should use:

```bash
/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-consumer automation-preflight \
  --repo-root /Users/billyweisberg/Repos/billyweisberg/fractal-core-python \
  --target-role techlead
```

If no work is present:
- do not invoke the model
- exit quietly

## Core command surfaces

### Status/reporting
```bash
/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-consumer techlead-status \
  --repo-root /Users/billyweisberg/Repos/billyweisberg/fractal-core-python \
  --validate-schema
```

### Assignment emission
```bash
/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-consumer techlead-emit-next-assignment \
  --repo-root /Users/billyweisberg/Repos/billyweisberg/fractal-core-python \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  [--send]
```

### Lifecycle decisions
```bash
/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-consumer techlead-emit-decision \
  --repo-root /Users/billyweisberg/Repos/billyweisberg/fractal-core-python \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --decision-type <reset_required|superseded|closed> \
  [--send]
```

### Lineage and worktree inspection
```bash
/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-consumer techlead-lineage ...
/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-consumer techlead-worktree-ownership ...
/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-consumer techlead-worktree-stale ...
```

## Branch and worktree model

### Canonical branch
- `issue-<issue_number>`

### Authorized role branches
- `issue-<issue_number>-delivery`
- `issue-<issue_number>-dev`
- `issue-<issue_number>-qa`

`TechLead` owns:
- lineage state
- branch authorization
- lifecycle decisions

Spoke-role automations own:
- create-or-reuse of their own deterministic role worktrees beneath TechLead-authorized lineage

## Packet model

### Inputs to TechLead
- `delivery_review_packet`
- `worker_result_packet`
- `qa_verification_packet`
- legacy compatibility only:
  - `slice_result_packet`

### Outputs from TechLead
- `techlead_assignment_packet`
- `techlead_decision_packet`

## Known gaps and current risks

### Current UI registration drift
The home-level UI registration currently still has some drift from the installed/project-pack contract.
Examples include:
- stale branch examples in some home-level automation TOMLs
- under-specified execution-environment behavior

This document describes intended behavior, not every current defect.

### `execution_environment = "local"` is not enough by itself
The automation still needs a stronger launcher contract for:
- explicit env bootstrap
- explicit wrapper bootstrap
- explicit preflight-before-model path
- explicit role/worktree transition behavior

### Queue preview visibility remains incomplete
`queue-check` preview depth on `fractal-core-architecture` remains shallower than ideal.
This is not a routing blocker for the current proven role set, but it is still an observability gap.

## Design status

Current assessment:
- routing model: defined
- packet model: defined
- lifecycle model: defined
- launcher contract: partially defined
- true app-launched automation environment proof: not complete yet
