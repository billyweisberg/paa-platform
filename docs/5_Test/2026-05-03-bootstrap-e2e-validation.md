# Bootstrap E2E Validation

## Purpose
Validate the producer-to-consumer flow under the new repo bootstrap model:
- repo-local `.codex/config.toml`
- `.python-version` pinning
- `uv`-first PAA wrappers
- repo-local producer and consumer installs only

## Preconditions
- canonical producer repo:
  - `/Users/billyweisberg/Repos/Individual-Centricity/appdev`
- canonical consumer repo:
  - `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python`
- platform repo:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform`
- repo-local producer and consumer installs refreshed from platform revision:
  - `b91dad4a7664b9309bec3058a5b93a4f21f13fa3`

## Validation Flow

### 1. Producer authority summary
Command:

```bash
cd /Users/billyweisberg/Repos/Individual-Centricity/appdev
./.codex/paa/bin/paa-producer authority summary
```

Result:
- authority manifest resolved from canonical producer source
- `authority_version = 2026-05-03.1`
- no active tasks reported

### 2. Producer source-to-PAA load for `#106`
Command:

```bash
cd /Users/billyweisberg/Repos/Individual-Centricity/appdev
./.codex/paa/bin/paa-producer load-issue-into-paa \
  --repo-root /Users/billyweisberg/Repos/Individual-Centricity/appdev \
  --project-config /Users/billyweisberg/Repos/Individual-Centricity/appdev/.codex/paa/project-config.json \
  --issue-number 106 \
  --verification-key-prefix retirement-diagnostics \
  --scope-authority-label 'retirement-boundary diagnostics'
```

Result:
- live idempotent load succeeded
- package resolved:
  - `fcore-stage1-2026-05-02-issue106-retirement-boundary-diagnostics`
- brief resolved:
  - `fcore-coder-2026-05-02-issue106-retirement-boundary-diagnostics`
- sequence state remained:
  - `execution_ready`
- obligation materialization count:
  - `7`

### 3. Producer authority package publish
Command:

```bash
cd /Users/billyweisberg/Repos/Individual-Centricity/appdev
./.codex/paa/bin/paa-producer publish-authority-package \
  --repo-root /Users/billyweisberg/Repos/Individual-Centricity/appdev \
  --project-config /Users/billyweisberg/Repos/Individual-Centricity/appdev/.codex/paa/project-config.json
```

Result:
- publish succeeded
- package root:
  - `/Users/billyweisberg/Repos/Individual-Centricity/appdev/.project/data/paa/publish/fractal-core-python-authority-2026-05-03.1`

### 4. Consumer authority package install
Command:

```bash
cd /Users/billyweisberg/Repos/billyweisberg/fractal-core-python
./.codex/paa/bin/paa-consumer install-authority-package \
  --repo-root /Users/billyweisberg/Repos/billyweisberg/fractal-core-python \
  --package-root /Users/billyweisberg/Repos/Individual-Centricity/appdev/.project/data/paa/publish/fractal-core-python-authority-2026-05-03.1
```

Result:
- install succeeded
- authority install root:
  - `.project/data/paa/authority/current/`
- installed package metadata remained aligned to:
  - `authority_version = 2026-05-03.1`

### 5. Consumer runtime validation
Command:

```bash
cd /Users/billyweisberg/Repos/billyweisberg/fractal-core-python
./.codex/paa/bin/paa-consumer validate-runtime --repo-root /Users/billyweisberg/Repos/billyweisberg/fractal-core-python
```

Result:
- `ok = true`
- branch:
  - `codex/paa-consumer-consolidation`
- `behind = 0`
- `authority_version = 2026-05-03.1`
- `errors = []`

### 6. Consumer queue check
Command:

```bash
cd /Users/billyweisberg/Repos/billyweisberg/fractal-core-python
./.codex/paa/bin/paa-consumer queue-check \
  --repo-root /Users/billyweisberg/Repos/billyweisberg/fractal-core-python \
  --queue fractal-core-python
```

Result:
- queue runtime resolved from repo-local state
- `messages_ready = 0`
- `messages_unacknowledged = 0`

### 7. Consumer TechLead report generation
Command:

```bash
cd /Users/billyweisberg/Repos/billyweisberg/fractal-core-python
./.codex/paa/bin/paa-consumer techlead-status \
  --validate-schema \
  --output /Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.project/data/paa/reports/techlead-status-report.json
```

Result:
- schema validation passed
- latest accepted full-chain slice:
  - `issue_number = 106`
  - `full_chain_state = accepted_full_chain`
- `authority.status = aligned`
- `unattended_safe = true`

## Conclusion
This validates the current bootstrap path end to end for the core producer-to-consumer control flow:
- producer repo-local wrapper works
- producer source-to-PAA load works
- producer publish works
- consumer install works
- consumer runtime validation works
- consumer TechLead/report path works

## Not Covered By This Flow
This validation does not yet prove:
- live queue handoff send/claim/ack with actual messages in flight
- dev packet compilation from fresh live Dev input JSON
- QA packet compilation from fresh live QA input JSON
- automation scheduler execution itself
- unpaused automation cadence safety

Those remain follow-up validation slices.
