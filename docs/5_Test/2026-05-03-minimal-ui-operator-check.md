# Minimal UI Operator Check

## Purpose

Keep the human check as small as possible.
The operator should not act as the full test harness.

## Step 1: Visibility

In the producer or consumer repo, confirm whether repo-local automations appear in the UI.

Producer expected automation on disk:
- `<producer_repo_root>/.codex/automations/fractal-core-authority-architect-automation/automation.toml`

Consumer expected automations on disk:
- `<consumer_repo_root>/.codex/automations/fractal-core-delivery-architect-automation/automation.toml`
- `<consumer_repo_root>/.codex/automations/fractal-core-qa-automation/automation.toml`
- `<consumer_repo_root>/.codex/automations/fractal-core-techlead-automation/automation.toml`
- `<consumer_repo_root>/.codex/automations/python-team-automation/automation.toml`

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
- `<producer_repo_root>/.codex/paa/bin/paa-producer smoke-test`
- `<consumer_repo_root>/.codex/paa/bin/paa-consumer smoke-test --expected-branch codex/paa-consumer-consolidation`

That is enough human validation for this stage.

## TOML Validation

Platform-owned validator:

```bash
cd <paa_platform_repo_root>
uv run --python 3.12 --no-project python scripts/runtime/validate_automation_toml.py \
  <producer_repo_root>/.codex/automations \
  <consumer_repo_root>/.codex/automations
```

Current known result on 2026-05-03:
- all installed repo-local automation TOML files parse successfully
- UI invisibility is therefore not explained by TOML syntax failure
