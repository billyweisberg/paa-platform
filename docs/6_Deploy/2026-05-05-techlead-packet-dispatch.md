# TechLead Packet Dispatch

## Summary

Phase B makes TechLead packet compilation first-class.
This note makes the operator dispatch path explicit so the workflow is:

1. compile packet
2. validate packet
3. send packet

without requiring the operator to remember queue names by hand.

## Commands

Validate a TechLead packet and show the resolved queue:

```bash
<consumer_repo>/.codex/paa/bin/paa-consumer techlead-validate-packet \
  --message-file <packet.json>
```

Send a TechLead packet using repo-local runtime and queue-state configuration:

```bash
<consumer_repo>/.codex/paa/bin/paa-consumer techlead-send-packet \
  --repo-root <consumer_repo> \
  --message-file <packet.json>
```

## Queue resolution rules

`techlead_assignment_packet`
- target role `Python Dev` -> `fractal-core-python`
- target role `QA` -> `fractal-core-qa`
- target role `Delivery Architect` -> `fractal-core-architecture`

`techlead_decision_packet`
- `to_role = Authority Architect` -> `fractal-core-architecture`
- `to_role = TechLead` -> `fractal-core-architecture`

Note:
- there is not yet a dedicated TechLead queue
- Phase B keeps TechLead control traffic on the architecture queue

## Why this exists

The generic queue commands remain available:
- `queue-validate`
- `queue-send`

But they require the operator to know the correct destination queue already.
The TechLead helpers reduce that risk by:
- validating the packet envelope
- resolving the queue deterministically from packet semantics
- sending through the existing queue/control spine

## Scope

This is an operator-facing helper only.
It does not:
- auto-generate a packet
- auto-emit a next assignment from TechLead runtime
- replace manual review of compiled packet contents

The current Phase B contract is still:
- compile explicitly
- validate explicitly
- send explicitly
