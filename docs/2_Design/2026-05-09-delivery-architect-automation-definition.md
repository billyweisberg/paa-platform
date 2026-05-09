# Delivery Architect Automation Definition

## Purpose

Define the intended role, launch model, execution contract, and authoritative source surfaces for the `Fractal Core Delivery Architect Automation`.

## Automation identity

- automation id:
  - `fractal-core-delivery-architect-automation`
- display name:
  - `Fractal Core Delivery Architect Automation`
- role:
  - `Delivery Architect`
- current cadence:
  - `RRULE:FREQ=MINUTELY;INTERVAL=30`
- current model:
  - `gpt-5.4`
- current reasoning effort:
  - `medium`

## Primary responsibility

`Delivery Architect` is a spoke role.

The automation is responsible for:
- receiving Delivery Architect assignments from `TechLead`
- entering an authorized Delivery Architect execution surface
- performing delivery architecture review
- returning only `delivery_review_packet` to `TechLead`

It is not responsible for:
- selecting the next route directly
- sending work directly to `Python Dev`
- sending work directly to `QA`
- owning canonical lineage

## Authoritative source surfaces

### Project-pack source of truth
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/project-packs/fractal-core/automations/fractal-core-delivery-architect-automation/automation.toml`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/project-packs/fractal-core/skills/fractal-core-delivery-review/SKILL.md`

### Installed consumer copy
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/automations/fractal-core-delivery-architect-automation/automation.toml`
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/skills/fractal-core-delivery-review/SKILL.md`

### Home-level UI registration surface
- `/Users/billyweisberg/.codex/automations/fractal-core-delivery-architect-automation/automation.toml`

## Launch model

### Current launch surface
- `execution_environment = "local"`
- launch cwd:
  - `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python`

### Intended meaning of `local`
The Delivery Architect automation should:
- start from the canonical consumer repo root
- use repo-local installed consumer wrappers
- poll for work before model invocation
- transition into a deterministic Delivery Architect role worktree when work exists

It should not:
- do review on the shared repo root by default
- depend on deprecated home-folder runtime assets

## Runtime contract

### Required pre-run gate
```bash
/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-consumer automation-preflight \
  --repo-root /Users/billyweisberg/Repos/billyweisberg/fractal-core-python \
  --target-role delivery-architect
```

If `should_invoke_model = false`:
- do not invoke the model
- exit quietly

## Receive/execute/return flow

### Inspect prepared worktree
```bash
/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-consumer techlead-inspect-role-worktree \
  --repo-root /Users/billyweisberg/Repos/billyweisberg/fractal-core-python \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role delivery-architect
```

### Resolve role entry
```bash
/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-consumer techlead-role-entry \
  --repo-root /Users/billyweisberg/Repos/billyweisberg/fractal-core-python \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role delivery-architect
```

### Prepare return context
```bash
/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-consumer techlead-role-result-assist \
  --repo-root /Users/billyweisberg/Repos/billyweisberg/fractal-core-python \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role delivery-architect
```

### Return result to TechLead
```bash
/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-consumer techlead-role-return \
  --repo-root /Users/billyweisberg/Repos/billyweisberg/fractal-core-python \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role delivery-architect \
  --send
```

## Branch and worktree model

### Canonical branch
- `issue-<issue_number>`

### Authorized Delivery Architect role branch
- `issue-<issue_number>-delivery`

### Deterministic worktree model
The Delivery Architect automation should create or reuse its own authorized role worktree beneath TechLead-owned lineage.

## Packet model

### Input assignment
- `techlead_assignment_packet`
  - assignment type:
    - `delivery_architecture_review`

### Output result
- `delivery_review_packet`

## Known gaps and current risks

### Home-level UI registration drift
The home-level UI registration currently points at deprecated home-folder skill references in at least one surface.
That should be corrected so the UI entry uses only repo-local installed skill/runtime surfaces.

### Launcher contract is still under-specified
We still need a stronger encoded launcher contract for:
- env bootstrap
- worktree bootstrap
- cwd transition after launch
- exact no-work exit behavior at the app boundary

## Design status

Current assessment:
- role behavior: defined
- packet behavior: defined
- receive/return path: defined
- launcher environment contract: partially defined
- app-launched proof: not complete yet
