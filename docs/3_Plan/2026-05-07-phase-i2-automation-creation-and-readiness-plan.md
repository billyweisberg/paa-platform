# Phase I2 Automation Creation And Readiness Plan

## Why this plan exists

The current role automations do exist on disk in the consumer repo:
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/automations/fractal-core-techlead-automation/automation.toml`
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/automations/fractal-core-delivery-architect-automation/automation.toml`
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/automations/python-team-automation/automation.toml`
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/automations/fractal-core-qa-automation/automation.toml`

But that is not the same thing as being ready for unattended execution.

The gap is:
- we have prompt files and cron registrations
- but the role automations are not yet defined as complete execution agents with a clear repo/runtime/worktree contract
- and UI visibility depends on a separate global registration surface under `/Users/billyweisberg/.codex/automations/`, not just the repo-local installed copies

So this plan is about turning them from:
- present on disk

into:
- intentionally runnable

## Automation surfaces that must all exist

For the MVP, an automation is only real when all four surfaces line up:
- project-pack template source in `paa-platform`
- repo-local installed automation in the target repo `.codex/automations/`
- global UI registration entry under `/Users/billyweisberg/.codex/automations/`
- execution-environment contract for worktree, `uv`, cwd, and required environment variables

If any one of those is missing or stale, the automation is not ready for deliberate unpause.

## Current findings

### 0. UI visibility is driven by global registration, not repo-local install alone

Earlier UI probe work already established the key distinction:
- repo-local `.codex/automations/` content can exist and parse correctly
- but the Codex UI is currently discovering home-level registrations under `/Users/billyweisberg/.codex/automations/`

Current observed home-level state:
- `/Users/billyweisberg/.codex/automations/fractal-core-techlead-automation/automation.toml` exists
- `/Users/billyweisberg/.codex/automations/ui-probe-automation/automation.toml` exists
- `/Users/billyweisberg/.codex/automations/fractal-core-delivery-architect-automation/automation.toml` is missing
- `/Users/billyweisberg/.codex/automations/fractal-core-qa-automation/automation.toml` is missing
- `/Users/billyweisberg/.codex/automations/python-team-automation/automation.toml` exists, but is a deprecated home-folder placeholder rather than a current runnable registration

Conclusion:
- Delivery Architect and QA are not UI-registerable yet
- Python Dev has a name collision with an old deprecated global entry
- TechLead is visible, but its global prompt is still stale

### 1. TechLead automation exists, but its prompt is still transitional

Current installed prompt:
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/automations/fractal-core-techlead-automation/automation.toml`

Problems:
- it still says:
  - `Do not auto-send new packets in this phase; keep next-step execution human/report-driven unless explicitly instructed.`
- that is stale relative to the current proven hub loop
- the runtime now does support real assignment emission and proved it in the canonical E2E run

Conclusion:
- TechLead automation exists
- but its prompt contract is behind the real runtime capability

### 2. Delivery Architect, Python Dev, and QA prompts are still branch-model stale

Current installed prompts still teach:
- one shared full-cycle branch per issue: `issue-<issue_number>`
- do not invent role-specific branch names

That conflicts with the actual current execution bridge and ownership model:
- role automation owns create-or-reuse of its own deterministic role worktree
- role execution can legitimately happen on a role branch / prepared role worktree surface

Conclusion:
- the role automations exist
- but their prompts are still teaching an older branch/worktree model

### 3. There is no dedicated Delivery Architect role skill

Installed skills in the consumer repo include:
- `fractal-core-techlead`
- `fractal-core-authority`
- `fractal-core-dev-result`
- `fractal-core-qa-review`
- inbox/queue/common support skills

What is missing:
- a dedicated Delivery Architect execution/return skill analogous to:
  - `fractal-core-dev-result`
  - `fractal-core-qa-review`

Current Delivery Architect automation compensates by referencing:
- `fractal-core-techlead`
- `fractal-core-authority`
- `fractal-core-inbox`

That is not clean role separation.

Conclusion:
- Delivery Architect has an automation prompt
- but not a dedicated role execution skill surface

### 4.5. Automations need a pre-run no-work gate

Even with correct UI registration, prompts, and environment setup, the automations are still too expensive if every scheduled wakeup immediately invokes the model.

For the MVP, each automation needs a deterministic pre-run check that can decide whether to invoke the model at all.

That gate should be able to answer, without model tokens:
- is there a claimable packet for this role?
- is there already active in-progress work for this role that should resume?
- is the role blocked because a required prior packet or lifecycle state is not present yet?
- should this scheduled run exit quietly with no model invocation?

This matters especially for queue-polling roles:
- `TechLead`
- `Delivery Architect`
- `Python Dev`
- `QA`

Conclusion:
- polling for work must be possible without waking the model
- model invocation should happen only when the pre-run gate says work is present or resumption is required

### 4. Execution-environment contract is not yet explicit enough

Even if an automation is visible in the UI and has the right prompt, it is still not runnable unless its execution environment is fully specified.

That means each role automation needs an explicit contract for:
- the repo root it should start from
- the deterministic role worktree path it may create or reuse
- the working directory it should execute in after worktree preparation
- the repo-local `uv` binary or wrapper path it should use
- the required environment variables for PAA runtime, queue runtime, and any repo-local state roots
- any environment variables that must be forbidden or ignored because they point at deprecated home-folder runtime surfaces

Current gap:
- these expectations exist partially across runtime helpers and docs
- but they are not yet gathered into one automation-facing execution contract

Conclusion:
- execution-environment configuration is currently implicit and fragile
- Phase I2 must make it explicit before any real unpause

### 6. The worker-role skills are not yet worktree-execution skills

Current installed skills for Python Dev and QA mostly describe:
- packet compilation
- branch expectations
- routing expectations

They do not yet act like a complete unattended execution contract that says:
- claim assignment
- resolve prepared worktree
- enter worktree
- use repo-local `uv` environment correctly
- perform the assigned work in that worktree
- compile and return the result packet

Conclusion:
- the skills are present
- but they are still packet-oriented, not full automation-execution-oriented

## Core decision

We should treat the current non-Architect automations as:
- existing but not ready

not as:
- missing entirely

That means the next work is not “invent automations from zero.”
It is:
- convert the existing automation/prompt/skill surfaces into real execution agents

## Target automation model for the current proven role set

### TechLead

TechLead automation should be able to:
- inspect queue/runtime/GitHub/PAA state
- emit the next assignment packet in supported cases
- emit lifecycle/decision packets in supported cases
- inspect lineage and worktree ownership
- prepare or authorize the next role execution surface
- supervise cutover-safe routing

TechLead should not:
- perform the role’s implementation or QA work itself

### Delivery Architect

Delivery Architect automation should be able to:
- claim or receive the TechLead-issued assignment context
- create or reuse its deterministic role worktree
- run from that worktree context
- produce `delivery_review_packet`
- return to TechLead

### Python Dev

Python Dev automation should be able to:
- claim or receive the TechLead-issued assignment context
- create or reuse its deterministic role worktree
- run from that worktree context
- use the repo-local `uv` environment correctly
- perform the actual assigned work in that worktree
- produce `worker_result_packet`
- return to TechLead

### QA

QA automation should be able to:
- claim or receive the TechLead-issued assignment context
- create or reuse its deterministic role worktree
- run from that worktree context
- execute the assigned verification/test/review path
- produce `qa_verification_packet`
- return to TechLead

## What needs to be built next

### Slice 1: global UI registration alignment

Make the UI-visible registration layer real for the current proven role set:
- create current home-level UI registration entries for `Delivery Architect` and `QA`
- replace or retire the deprecated home-level `python-team-automation` placeholder with a current runnable registration
- update the existing home-level `TechLead` entry so it matches the real runtime and no longer teaches stale human-only behavior
- keep the distinction explicit between global UI registration and repo-local runtime execution

### Slice 2: prompt contract alignment

Update installed/project-pack automation prompts so they teach the real current model:
- TechLead may emit real assignment packets
- role automations use deterministic prepared role worktrees
- shared full-cycle branch wording is removed where it contradicts the role-worktree model
- prompts stop implying human-only execution if the runtime is now agent-capable

### Slice 3: dedicated role skill surfaces

Add or refactor skills so each current proven role has a role-native execution surface:
- `fractal-core-delivery-review` or equivalent dedicated Delivery Architect skill
- `fractal-core-dev-execution` or equivalent Python execution skill
- `fractal-core-qa-execution` or equivalent QA execution skill

These should be more than packet examples.
They should define:
- assignment intake
- worktree entry
- execution context
- result return

### Slice 4: pre-run no-work gate

Add a deterministic non-model preflight for each role automation:
- inspect the relevant queue or active-work runtime state without invoking the model
- exit without model invocation when there is no work to do
- invoke the model only when work is present or an active slice must resume
- make the gate role-specific but shared in shape across `TechLead`, `Delivery Architect`, `Python Dev`, and `QA`

This slice must reduce token waste before any real unpause.

### Slice 5: execution-environment contract

Document and enforce for each role automation:
- canonical consumer repo root
- deterministic role worktree path contract
- exact working directory before and after role worktree preparation
- repo-local runtime binary paths
- repo-local `uv` execution expectation
- required environment variables for runtime state, scratch paths, and queue/runtime behavior
- forbidden deprecated environment roots or fallback paths
- what counts as success/failure/blocking

This slice must make the automation environment reproducible, not inferred.

### Slice 6: repo/runtime execution contract

Use the explicit environment contract above to harden each role automation end to end:
- UI-visible registration points at the correct consumer repo cwd
- prepared worktree command surfaces enter the correct execution directory
- role commands use the intended repo-local `uv` and installed PAA wrappers
- environment variables do not silently drift to deprecated home-folder runtime surfaces

### Slice 7: supervised live automation pilot

After prompt and skill alignment:
- unpause only one role at a time in supervised mode
- prove it runs from the expected worktree/runtime contract
- only then move to multi-role unpause

## Roadmap choice after this plan

This plan remains useful for automation readiness, but it is no longer the top-level sequencing authority.

Updated rule:
- Team Worker Roles expansion is now promoted before further automation cutover work
- use `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-09-target-worker-family-expansion-implementation-plan.md` as the active sequencing authority for target-state expansion
- resume the remaining automation pilot phases only after automation surfaces are reconciled with that Team Worker Roles model

## Immediate next implementation slice

1. make the global UI registration layer real for `Delivery Architect`, `Python Dev`, and `QA`
2. align the installed/project-pack automation prompts with the real current role/worktree model
3. add the deterministic pre-run no-work gate so queue polling can happen without model invocation
4. define the explicit execution-environment contract for worktree, `uv`, cwd, and required environment variables
5. create the missing dedicated Delivery Architect execution skill
6. then harden Python Dev and QA role skills into true execution-agent skills rather than packet-only helper skills
