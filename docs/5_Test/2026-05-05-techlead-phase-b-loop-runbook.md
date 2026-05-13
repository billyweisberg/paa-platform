# TechLead Phase B Loop Runbook

## Purpose

This is the thinnest explicit runbook for exercising the current Phase B hub model without skipping steps or relying on memory.

The current contract is still:
1. compile assignment
2. validate assignment
3. send assignment
4. receive worker result
5. compile decision
6. validate decision
7. send decision

This runbook uses the existing repo-local PAA runtime and the new TechLead packet helpers.

## Repos

Producer repo:
- `<producer_repo_root>`

Consumer repo:
- `<consumer_repo_root>`

## Preconditions

- producer and consumer runtimes are installed and current
- authority package is already installed in the consumer repo
- one issue slice is selected
- canonical issue branch exists or is about to exist:
  - `issue-<issue_number>`

For examples below, substitute the real issue/package/brief values.

## Phase B loop

### 1. Compile TechLead assignment packet

Example:

```bash
<producer_repo_root>/.codex/paa/bin/paa-producer authority materialize-techlead-assignment-packet \
  --manifest <producer_repo_root>/docs/architecture/tom-baby7-fractal-core/project-authority/fractal-core-python-authority.json \
  --project-slug fractal-core-python \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --repo billyweisberg/fractal-core-python \
  --issue-number <issue_number> \
  --issue-url <issue_url> \
  --pr-number <pr_number> \
  --pr-url <pr_url> \
  --branch issue-<issue_number> \
  --target-role python-team \
  --assignment-type implement_authorized_slice \
  --assignment-summary "Implement the authorized slice and return the result to TechLead." \
  --allowed-result-type implemented_ready_for_qa \
  --allowed-result-type blocked \
  --allowed-result-type needs_clarification \
  --source-packet-path <source_packet_path> \
  --source-packet-message-id <source_packet_message_id> \
  --output <assignment_packet.json> \
  --review-output <assignment_packet.md>
```

Checks:
- packet compiles successfully
- `to_role` and `payload.target_role` are correct
- canonical branch is correct
- assignment summary is explicit

### 2. Validate TechLead assignment packet

```bash
<consumer_repo_root>/.codex/paa/bin/paa-consumer techlead-validate-packet \
  --message-file <assignment_packet.json>
```

Checks:
- `ok = true`
- resolved queue is the expected queue for the target role
- route matches the TechLead hub policy

### 3. Send TechLead assignment packet

```bash
<consumer_repo_root>/.codex/paa/bin/paa-consumer techlead-send-packet \
  --repo-root <consumer_repo_root> \
  --message-file <assignment_packet.json>
```

Checks:
- send succeeds
- queue preview shows the packet in the resolved queue
- `message_id` matches the compiled packet

### 4. Receive worker result

The worker role performs its run and returns a result packet to TechLead.

Current packet families:
- worker result:
  - `slice_result_packet`
- QA result:
  - `qa_verification_packet`

Current expected consumer-side return pattern:
- worker -> `TechLead`
- QA -> `TechLead`

Checks:
- returned packet validates
- returned packet routes to `TechLead`
- TechLead report reflects a pending TechLead decision state

### 5. Compile TechLead decision packet

Example: route to QA

```bash
<producer_repo_root>/.codex/paa/bin/paa-producer authority materialize-techlead-decision-packet \
  --manifest <producer_repo_root>/docs/architecture/tom-baby7-fractal-core/project-authority/fractal-core-python-authority.json \
  --project-slug fractal-core-python \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --repo billyweisberg/fractal-core-python \
  --issue-number <issue_number> \
  --issue-url <issue_url> \
  --pr-number <pr_number> \
  --pr-url <pr_url> \
  --branch issue-<issue_number> \
  --to-role authority-architect \
  --target-role qa \
  --decision-type assign_qa \
  --decision-rationale "The Dev result is ready for QA verification." \
  --next-assignment-type verify_authorized_slice \
  --work-item-status-update-intent qa_pending \
  --source-packet-path <source_packet_path> \
  --source-packet-message-id <source_packet_message_id> \
  --output <decision_packet.json> \
  --review-output <decision_packet.md>
```

Checks:
- decision type matches actual next move
- rationale is explicit
- target role and next assignment type agree
- work-item status update intent is sensible

### 6. Validate TechLead decision packet

```bash
<consumer_repo_root>/.codex/paa/bin/paa-consumer techlead-validate-packet \
  --message-file <decision_packet.json>
```

Checks:
- `ok = true`
- resolved queue is correct
- route matches policy

### 7. Send TechLead decision packet

```bash
<consumer_repo_root>/.codex/paa/bin/paa-consumer techlead-send-packet \
  --repo-root <consumer_repo_root> \
  --message-file <decision_packet.json>
```

Checks:
- send succeeds
- queue preview shows the decision packet
- TechLead report recognizes:
  - `techlead_decision_recorded`
  - or the next derived state after the follow-up packet is emitted

## Current limitations

Phase B still has these limits:
- TechLead does not auto-emit next assignment packets from report logic
- humans or agent-invoked commands still perform the compile/validate/send loop explicitly
- branch/worktree lineage is carried only in packet payload fields, not yet in dedicated persistence metadata
- `Delivery Architect` and `Authority Architect` still alias back to `Architect` in DB persistence

## Exit criteria for a successful Phase B loop

A full loop is successful when:
- assignment packet compiles, validates, and sends
- worker result returns to TechLead
- decision packet compiles, validates, and sends
- queue/runtime persistence succeeds
- TechLead report recognizes the new artifact states correctly
- no manual queue-name lookup was required during dispatch
