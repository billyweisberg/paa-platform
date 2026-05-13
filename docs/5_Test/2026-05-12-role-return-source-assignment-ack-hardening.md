# Role Return Source Assignment Ack Hardening

Date: 2026-05-12

## Problem

Role automations could successfully send a return packet back to `TechLead` while leaving the original source assignment packet behind on the role queue.

Observed pattern:
- `TechLead` sends assignment packet
- role automation completes work
- role automation sends result packet
- original assignment packet still remains on the queue unless a separate claim acknowledgement occurs

This created recurring queue residue on `fractal-core-architecture` during `Delivery Architect` legs and could do the same on Team Worker or `QA` legs.

## Root cause

The `techlead-role-return --send` path was not closing the full queue lifecycle.

It handled:
- compile result packet
- validate result packet
- send result packet

It did **not** own:
- acknowledgment of the claimed source assignment packet

That meant the workflow still depended on prompt/skill compliance or manual cleanup to finish the queue transaction.

## Fix

Updated:
- `packages/paa-consumer/src/paa_consumer/techlead.py`

New behavior in `role_return_bridge()` when `--send` is used:
1. send the role result packet
2. resolve the source assignment packet from the assignment artifact
3. close the source assignment packet automatically by:
   - acknowledging an existing active claim when present, or
   - claiming the next queue message, verifying it matches the expected source assignment, and then acknowledging it
4. fail closed if the runtime cannot safely close the expected source assignment

## Safety behavior

If the queue head is not the expected source assignment packet, the runtime now:
- refuses to acknowledge the wrong packet
- requeues the unexpected claim
- returns `source_assignment_ack_failed`

That keeps the closeout path safe while eliminating the common stale-assignment residue case.

## Install status

The consumer runtime in `<consumer_repo_root>` was refreshed after the source change.

Installed runtime now contains:
- `acknowledge_source_assignment()`
- `source_assignment_ack` in the `techlead-role-return` result
- `source_assignment_ack_failed` fail-closed path

## Next proof point

The live proof for this hardening is the next issue `110` worker/QA return leg.
If the fix is behaving correctly, those legs should return result packets without leaving the corresponding source assignment packet behind on their queue.
