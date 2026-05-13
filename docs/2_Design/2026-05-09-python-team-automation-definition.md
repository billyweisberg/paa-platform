# Python Team Automation Definition

## Purpose

Define the intended role, launch model, execution contract, and authoritative source surfaces for the `Python Team Automation`.

## Automation identity

- automation id:
  - `python-team-automation`
- display name:
  - `Python Team Automation`
- role:
  - `Python Dev`
- current cadence:
  - `RRULE:FREQ=MINUTELY;INTERVAL=30`
- current model:
  - `gpt-5.5`
- current reasoning effort:
  - `medium`

## Primary responsibility

`Python Dev` is a spoke role.

The automation is responsible for:
- receiving implementation assignments from `TechLead`
- entering an authorized Python execution surface
- performing implementation work from the authorized role worktree
- returning only `worker_result_packet` to `TechLead`

It is not responsible for:
- routing directly to `QA`
- bypassing `TechLead`
- owning lineage or route selection

## Authoritative source surfaces

### Project-pack source of truth
- `project-packs/fractal-core/automations/python-team-automation/automation.toml`
- `project-packs/fractal-core/skills/fractal-core-dev-result/SKILL.md`

### Installed consumer copy
- `<consumer_repo_root>/.codex/automations/python-team-automation/automation.toml`
- `<consumer_repo_root>/.codex/skills/fractal-core-dev-result/SKILL.md`

### Home-level UI registration surface
- `<codex_home>/automations/python-team-automation/automation.toml`

## Launch model

### Current launch surface
- `execution_environment = "local"`
- launch cwd:
  - `<consumer_repo_root>`

### Intended meaning of `local`
The Python automation should:
- start from the canonical consumer repo root
- use repo-local installed wrappers
- poll for work before model invocation
- create or reuse its deterministic Python role worktree when work exists
- transition into that worktree before doing implementation work

It should not:
- treat the shared repo root as the long-lived execution surface
- silently fall back to unrelated interpreter state

## Runtime contract

### Required pre-run gate
```bash
<consumer_repo_root>/.codex/paa/bin/paa-consumer automation-preflight \
  --repo-root <consumer_repo_root> \
  --target-role python-team
```

If `should_invoke_model = false`:
- do not invoke the model
- exit quietly

### `uv` expectation
The Python role should prefer `uv run` from the prepared role worktree when repo execution is required.

## Receive/execute/return flow

### Inspect prepared worktree
```bash
<consumer_repo_root>/.codex/paa/bin/paa-consumer techlead-inspect-role-worktree ... --target-role python-team
```

### Resolve role entry
```bash
<consumer_repo_root>/.codex/paa/bin/paa-consumer techlead-role-entry ... --target-role python-team
```

### Prepare return context
```bash
<consumer_repo_root>/.codex/paa/bin/paa-consumer techlead-role-result-assist ... --target-role python-team
```

### Return result to TechLead
```bash
<consumer_repo_root>/.codex/paa/bin/paa-consumer techlead-role-return ... --target-role python-team --send
```

## Branch and worktree model

### Canonical branch
- `issue-<issue_number>`

### Authorized Python role branch
- `issue-<issue_number>-dev`

### Important branch-naming note
The runtime and current project-pack definition use:
- `issue-<issue_number>-dev`

Any surviving `issue-<issue_number>-python-team` examples are drift and should be treated as defects, not design truth.

## Packet model

### Input assignment
- `techlead_assignment_packet`
  - assignment type:
    - `implement_authorized_slice`

### Output result
- active result family:
  - `worker_result_packet`
- legacy compatibility only:
  - `slice_result_packet`

## Known gaps and current risks

### Home-level UI registration drift
The home-level UI registration currently still contains at least one stale branch example using `python-team` instead of `dev`.
That is a real defect.

### Launcher contract is still under-specified
We still need stronger automation-level encoding for:
- wrapper bootstrap
- env bootstrap
- worktree transition
- `uv` verification before execution
- exact no-work exit behavior at the app boundary

## Design status

Current assessment:
- role behavior: defined
- packet behavior: defined
- branch naming truth: defined
- home-level UI registration alignment: not fully clean
- app-launched proof: not complete yet
