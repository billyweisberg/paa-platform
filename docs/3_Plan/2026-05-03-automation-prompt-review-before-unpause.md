# Automation Prompt Review Before Unpause

## Purpose
Record the prompt review performed before any automation is unpaused.
This pass distinguishes:
- obvious breaking changes that must be fixed now
- operational clarity issues that should be improved before re-enabling cadence

## Obvious Breaking Changes Found

### 1. Consumer Delivery Architect automation referenced producer-side architect handoff skill
This was an actual boundary mismatch.

Old state:
- consumer Delivery Architect automation referenced:
  - `fractal-core-architect-handoff`

Why this was wrong:
- that skill is for emitting the next architect cycle packet
- that is a producer-side responsibility
- keeping it in the consumer Delivery Architect prompt created role confusion and a likely wrong-command path

Fix applied:
- replaced the Delivery Architect automation skill set to use:
  - `fractal-core-authority`
  - `fractal-core-inbox`
  - `fractal-core-techlead`

### 2. Several skill files still used `...` where full command arguments were required
This was not a topology bug, but it was an operational footgun.

Affected skills:
- `fractal-core-authority`
- `fractal-core-dev-result`
- `fractal-core-qa-review`

Fix applied:
- replaced the `...` placeholders for packet compilation with full argument skeletons using explicit placeholder values

## Remaining Clarity Issues
These are not immediate breakages, but they should still be reviewed before unpausing automations.

### 1. Consumer-side use of `fractal-core-authority`
This skill now explicitly distinguishes:
- authority inspection commands that are safe on any repo with installed PAA runtime
- producer-only packet emission commands that should only be used in the canonical producer repo

That is a good first step, but the skill surface still mixes two modes.
A future refinement may split this into:
- an authority inspection skill
- a producer packet compilation skill

### 2. Role prompts are still fairly terse
The current automation prompts are now topology-safe, but still fairly thin.
Before unpause, we should make sure each prompt is explicit about:
- what role it is acting as
- what commands it may run
- what it must never do
- what conditions should cause it to stop and escalate

### 3. Queue workflow prompts still need one review pass
The queue-related skills are structurally correct, but they should still be reviewed for:
- claim lifecycle clarity
- ack vs requeue behavior
- when to escalate instead of acting

## Current Recommendation
Keep all automations paused.

Only consider unpausing after:
1. bootstrap E2E validation is complete
2. this prompt review pass is accepted
3. one more targeted prompt-quality refinement pass is performed on the live automation prompts

## Bottom Line
We found and fixed the prompt changes that were most likely to cause wrong-role or wrong-command execution.
The remaining work before unpause is now mostly about clarity, escalation behavior, and operator safety rather than hidden topology breakage.
