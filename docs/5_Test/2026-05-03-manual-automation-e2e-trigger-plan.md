# Manual Automation E2E Trigger Plan

## Goal

Run the Fractal Core PAA workflow one automation step at a time and validate the resulting state after each step.
This plan assumes repo-local installs, uv-first wrappers, the canonical producer repo, and the canonical consumer repo.

## Preconditions

Producer repo:
- `<producer_repo_root>`

Consumer repo:
- `<consumer_repo_root>`

Authority package install root:
- `<consumer_repo_root>/.project/data/paa/authority/current`

Expected branch policy:
- one branch per issue: `issue-<issue_number>`

## Current UI Note

Repo-local automation files currently exist on disk, but the user reported that Automations are not visible in the UI.
This plan is therefore written so each step can be triggered manually and validated independently even before UI automation visibility is restored.

## Step 0: Repo Preflight

### Validate producer runtime

```bash
cd <producer_repo_root>
./.codex/paa/bin/paa-producer authority summary
```

Validate:
- command succeeds
- authority manifest resolves from producer source
- package version is current

### Validate consumer runtime

```bash
cd <consumer_repo_root>
./.codex/paa/bin/paa-consumer validate-runtime --repo-root <consumer_repo_root>
```

Validate:
- `ok = true`
- branch is expected for the repo state under test
- authority version is installed
- no runtime errors

## Step 1: Authority Architect / Producer Sync

### Trigger

Use the Authority Architect automation intent manually from the producer repo.
For a target issue such as `106`, source-to-PAA sync should happen before packet resolution.

```bash
cd <producer_repo_root>
./.codex/paa/bin/paa-producer load-issue-into-paa \
  --repo-root <producer_repo_root> \
  --project-config <producer_repo_root>/.codex/paa/project-config.json \
  --issue-number 106 \
  --verification-key-prefix retirement-diagnostics \
  --scope-authority-label "retirement-boundary diagnostics"
```

Validate:
- work item exists in PAA
- design package exists in PAA
- coder brief exists in PAA
- sequence state is materialized
- verification obligations exist

Suggested checks:

```bash
cd <producer_repo_root>
./.codex/paa/bin/paa-producer authority task --issue-number 106
./.codex/paa/bin/paa-producer materialize-readiness --db-package-id-external fcore-stage1-2026-05-02-issue106-retirement-boundary-diagnostics --db-write
```

## Step 2: Publish Authority Package

### Trigger

```bash
cd <producer_repo_root>
./.codex/paa/bin/paa-producer publish-authority-package \
  --repo-root <producer_repo_root> \
  --project-config <producer_repo_root>/.codex/paa/project-config.json
```

Validate:
- package directory exists under `.project/data/paa/publish/`
- package contains manifest
- package contains artifact set
- package contains package metadata

## Step 3: Install Authority Package in Consumer Repo

### Trigger

```bash
cd <consumer_repo_root>
./.codex/paa/bin/paa-consumer install-authority-package \
  --repo-root <consumer_repo_root> \
  --package-root <producer_repo_root>/.project/data/paa/publish/fractal-core-python-authority-2026-05-03.1
```

Validate:
- `.project/data/paa/authority/current/` refreshed
- installed manifest exists
- installed artifact schemas exist
- installed package metadata version matches published version

## Step 4: Delivery Architect Branch Setup

### Manual operator action

In the canonical consumer repo, create or switch to the issue branch for the target issue.

Example:

```bash
cd <consumer_repo_root>
git switch -c issue-106 || git switch issue-106
```

Validate:
- current branch is `issue-106`
- no role-specific or random branch name is used

## Step 5: Delivery Architect / Inbox Review

### Trigger

Use the Delivery Architect automation intent manually.
At minimum, inspect queue/runtime state and the installed authority package.

```bash
cd <consumer_repo_root>
./.codex/paa/bin/paa-consumer queue-check --repo-root <consumer_repo_root> --queue fractal-core-python
./.codex/paa/bin/paa-consumer techlead-status --validate-schema
```

Validate:
- consumer runtime is healthy
- installed authority version is current
- queue access succeeds
- no unexpected stale-runtime errors

## Step 6: Dev Result Packet

### Trigger

Run the Dev result path using the same issue branch.

```bash
cd <consumer_repo_root>
./.codex/paa/bin/paa-producer authority materialize-slice-result-packet \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --repo <consumer_repo_root> \
  --issue-number 106 \
  --issue-url <issue_url> \
  --pr-number <pr_number> \
  --pr-url <pr_url> \
  --branch issue-106 \
  --dev-input-file <dev_input_json> \
  --persist-db
```

Validate:
- packet compilation run persisted to `paa.automation_runs`
- packet branch recorded as `issue-106`
- evidence persistence succeeds when obligations exist

## Step 7: QA Verification Packet

### Trigger

Run the QA verification path using the same issue branch.

```bash
cd <consumer_repo_root>
./.codex/paa/bin/paa-producer authority materialize-qa-verification-packet \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --repo <consumer_repo_root> \
  --issue-number 106 \
  --issue-url <issue_url> \
  --pr-number <pr_number> \
  --pr-url <pr_url> \
  --branch issue-106 \
  --qa-input-file <qa_input_json> \
  --persist-db
```

Validate:
- QA packet compilation run persisted to `paa.automation_runs`
- packet branch recorded as `issue-106`
- QA evidence persistence succeeds

## Step 8: TechLead Validation

### Trigger

```bash
cd <consumer_repo_root>
./.codex/paa/bin/paa-consumer techlead-status \
  --validate-schema \
  --output <consumer_repo_root>/.project/data/paa/reports/techlead-status-report.json
```

Validate:
- report file is written
- latest accepted chain or current active chain is correct for the scenario under test
- branch references follow `issue-<issue_number>`
- no stale-runtime or stale-branch guardrail failures appear

## Step 9: Merge and Acceptance Validation

### Manual operator action

After merge, validate that PAA and TechLead reflect the accepted state.

Validate:
- `paa.work_items.status = accepted`
- acceptance event exists
- if proof chain is complete, `full_chain_state = accepted_full_chain`
- TechLead reflects the latest accepted full-chain slice correctly

## Recommended Validation Ledger

For each manual run, record:
- issue number
- branch name used
- package id
- brief id
- published authority version
- installed authority version
- queue result
- TechLead summary result
- pass/fail notes

## Pass Criteria

The manual E2E run passes when:
- producer sync works from canonical source artifacts
- published package installs cleanly in the consumer repo
- all consumer-side manual steps run from repo-local wrappers
- one shared issue branch is used consistently end to end
- TechLead and traceability outputs remain consistent with the DB and installed authority state
