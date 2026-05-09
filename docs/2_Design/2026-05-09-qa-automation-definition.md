# QA Automation Definition

## Purpose

Define the intended role, launch model, execution contract, and authoritative source surfaces for the `Fractal Core QA Automation`.

## Automation identity

- automation id:
  - `fractal-core-qa-automation`
- display name:
  - `Fractal Core QA Automation`
- role:
  - `QA`
- current cadence:
  - `RRULE:FREQ=MINUTELY;INTERVAL=15`
- current model:
  - `gpt-5.4`
- current reasoning effort:
  - `medium`

## Primary responsibility

`QA` is a spoke role.

The automation is responsible for:
- receiving QA assignments from `TechLead`
- entering an authorized QA execution surface
- performing verification from the authorized QA worktree
- returning only `qa_verification_packet` to `TechLead`

It is not responsible for:
- routing directly to `Architect`
- routing directly around `TechLead`
- owning lineage or next-route decisions

## Authoritative source surfaces

### Project-pack source of truth
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/project-packs/fractal-core/automations/fractal-core-qa-automation/automation.toml`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/project-packs/fractal-core/skills/fractal-core-qa-review/SKILL.md`

### Installed consumer copy
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/automations/fractal-core-qa-automation/automation.toml`
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/skills/fractal-core-qa-review/SKILL.md`

### Home-level UI registration surface
- `/Users/billyweisberg/.codex/automations/fractal-core-qa-automation/automation.toml`

## Launch model

### Current launch surface
- `execution_environment = "local"`
- launch cwd:
  - `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python`

### Intended meaning of `local`
The QA automation should:
- start from the canonical consumer repo root
- use repo-local installed wrappers
- poll for work before model invocation
- create or reuse its deterministic QA role worktree when work exists
- transition into that worktree before verification work begins

## Runtime contract

### Required pre-run gate
```bash
/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-consumer automation-preflight \
  --repo-root /Users/billyweisberg/Repos/billyweisberg/fractal-core-python \
  --target-role qa
```

If `should_invoke_model = false`:
- do not invoke the model
- exit quietly

### `uv` expectation
When repo execution is needed, QA should prefer `uv run` from the prepared QA worktree.

## Receive/execute/return flow

### Inspect prepared worktree
```bash
/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-consumer techlead-inspect-role-worktree ... --target-role qa
```

### Resolve role entry
```bash
/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-consumer techlead-role-entry ... --target-role qa
```

### Prepare return context
```bash
/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-consumer techlead-role-result-assist ... --target-role qa
```

### Return result to TechLead
```bash
/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-consumer techlead-role-return ... --target-role qa --send
```

## Branch and worktree model

### Canonical branch
- `issue-<issue_number>`

### Authorized QA role branch
- `issue-<issue_number>-qa`

## Packet model

### Input assignment
- `techlead_assignment_packet`
  - assignment type:
    - `verify_authorized_slice`

### Output result
- `qa_verification_packet`

## Known gaps and current risks

### Home-level UI registration is still thin
The current UI-registration TOML is enough for visibility and launch selection, but not yet strong enough to count as a complete launcher contract.

### Launcher contract is still under-specified
We still need stronger automation-level encoding for:
- env bootstrap
- wrapper/bootstrap verification
- worktree transition
- exact no-work exit behavior at the app boundary

## Design status

Current assessment:
- role behavior: defined
- packet behavior: defined
- branch/worktree model: defined
- launcher environment contract: partially defined
- app-launched proof: not complete yet
