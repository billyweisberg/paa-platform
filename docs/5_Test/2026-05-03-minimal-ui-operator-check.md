# Minimal UI Operator Check

## Purpose

Keep the human check as small as possible.
The operator should not act as the full test harness.

## Step 1: Visibility

In the producer or consumer repo, confirm whether repo-local automations appear in the UI.

Producer expected automation on disk:
- `/Users/billyweisberg/Repos/Individual-Centricity/appdev/.codex/automations/fractal-core-authority-architect-automation/automation.toml`

Consumer expected automations on disk:
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/automations/fractal-core-delivery-architect-automation/automation.toml`
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/automations/fractal-core-qa-automation/automation.toml`
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/automations/fractal-core-techlead-automation/automation.toml`
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/automations/python-team-automation/automation.toml`

Record only:
- visible or not visible
- producer or consumer repo

## Step 2: Manual Trigger

If one automation is visible, trigger exactly one manual run.
Prefer:
- producer: `Fractal Core Authority Architect Automation`
- consumer: `Fractal Core TechLead Automation`

Record only:
- did it launch
- which repo it launched against
- whether it appears to use the expected branch/repo context

## Step 3: Hand Off Back to Runtime Checks

After the UI check, use the repo-local smoke tests for the rest:
- `/Users/billyweisberg/Repos/Individual-Centricity/appdev/.codex/paa/bin/paa-producer smoke-test`
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-consumer smoke-test --expected-branch codex/paa-consumer-consolidation`

That is enough human validation for this stage.
