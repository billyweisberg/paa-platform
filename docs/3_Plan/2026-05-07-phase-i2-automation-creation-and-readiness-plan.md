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

So this plan is about turning them from:
- present on disk

into:
- intentionally runnable

## Current findings

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

### 4. The worker-role skills are not yet worktree-execution skills

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

### Slice 1: prompt contract alignment

Update installed/project-pack automation prompts so they teach the real current model:
- TechLead may emit real assignment packets
- role automations use deterministic prepared role worktrees
- shared full-cycle branch wording is removed where it contradicts the role-worktree model
- prompts stop implying human-only execution if the runtime is now agent-capable

### Slice 2: dedicated role skill surfaces

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

### Slice 3: repo/runtime execution contract

Document and enforce for each role automation:
- canonical consumer repo root
- deterministic role worktree path contract
- repo-local runtime binary paths
- repo-local `uv` execution expectation
- what counts as success/failure/blocking

### Slice 4: supervised live automation pilot

After prompt and skill alignment:
- unpause only one role at a time in supervised mode
- prove it runs from the expected worktree/runtime contract
- only then move to multi-role unpause

## Roadmap choice after this plan

The right next roadmap choice is:
- stay in `Phase I`
- finish automation execution readiness for the current proven role set
- only after that return to deferred multi-worker expansion

Reason:
- current role-set transport and lifecycle are proven
- the next real risk is execution-agent readiness, not packet design
- returning to multi-worker expansion before fixing automation execution semantics would compound the wrong layer

## Immediate next implementation slice

1. align the installed/project-pack automation prompts with the real current role/worktree model
2. create the missing dedicated Delivery Architect execution skill
3. then harden Python Dev and QA role skills into true execution-agent skills rather than packet-only helper skills
