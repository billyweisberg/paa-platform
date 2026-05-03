# Compiled Packet Transport Trace

This note captures the next transport-layer step in the PAA packet lifecycle.

## Goal

When a compiled packet is actually sent to RabbitMQ, the handoff transport layer should preserve the originating packet-compilation run identity.

That gives us a durable bridge from:

- design package
- coder brief
- compiled packet automation run

into:

- queue message
- handoff
- claim / ack lifecycle
- downstream evidence and acceptance records

## Implementation

The handoff runtime now looks up the most recent `paa.automation_runs` row that matches:

- `trigger_type = packet_compilation:<schema_type>`
- `artifacts_json->>'message_id' = <packet message id>`

When found, the runtime now:

1. attaches compiler provenance into `paa.queue_messages.metadata_json`
2. sets `paa.automation_runs.handoff_id` to the newly created handoff row

## Stored transport metadata

`paa.queue_messages.metadata_json` now carries:

- `compiled_packet_automation_run_id`
- `compiled_packet_trigger_type`
- `compiled_packet_summary`
- `compiled_packet_package_id_external`
- `compiled_packet_brief_id_external`

This is recorded alongside:

- queue name
- exchange
- publish result

## Why this matters

This creates a direct query path from a handoff send back to the exact compiled packet run that produced the message.

That means we can now join:

- `paa.design_packages`
- `paa.coder_run_briefs`
- `paa.automation_runs`
- `paa.queue_messages`
- `paa.handoffs`

without relying on ad hoc filesystem history.

## Proof run

A proving `slice_result_packet` was compiled, persisted, sent to an isolated queue, claimed, and acknowledged.

Key results from `paa_dev`:

- compiler automation run:
  - `c7dc6c4a-f2b6-4d92-8d3d-809644ecebe1`
- linked handoff:
  - `10ff8f4e-a783-44cb-af49-4f95856f2388`
- linked queue message:
  - `e09d1935-b443-45ad-af4d-99249188b98c`
- queue message metadata includes:
  - compiled packet automation run id
  - proving package id
  - proving brief id
- queue message status reached:
  - `acknowledged`
- handoff status reached:
  - `completed`

This was executed against the isolated queue:

- `fractal-core-handoff-test-compiled`

## Important integrity point

The transport trace only became complete after the proving package was attached to a real PAA work item.

That was the correct behavior.

The system should fail to create a durable handoff record when there is no valid `work_item_id` anchor rather than silently inventing one.

## Result

We now have a durable path across:

- design package
- coder brief
- compiled packet
- queue send
- claim / ack

The next natural extension is to make the downstream evidence and acceptance queries use the same compiler provenance so the full lifecycle can be reconstructed from PAA alone.
