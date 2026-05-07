# Phase G Scope Decision After Delivery Review Handling

## Decision

Do **not** expand into additional worker-role families yet.

Instead:
- close out the rest of `Phase G` with the current proven role set
- keep the active generic worker lane anchored on `Python Dev`
- keep `Delivery Architect` integrated as the non-worker spoke that routes into the worker lane through `TechLead`

## Reasoning

We now have the core packet and routing model working for the current real roles:
- `TechLead`
- `Delivery Architect`
- `Python Dev`
- `QA`

That gives us:
- generic worker packet contract proven on one real worker role
- Delivery Architect review packet proven on one real non-worker spoke
- the delivery review follow-up path proven for the supported `ready_for_dev -> Python Dev` case

Broadening immediately into:
- `Frontend Dev`
- `Backend Dev`
- `Infra Dev`
- `Docs Dev`

would increase surface area before the current hub loop is fully hardened through the remaining lifecycle and acceptance phases.

## What stays in Phase G

Keep Phase G focused on the current proven role set and packet families:
- `worker_result_packet`
- `delivery_review_packet`
- `qa_verification_packet`
- `techlead_assignment_packet`
- `techlead_decision_packet`

## What moves later

Additional worker-role family expansion moves to a later phase, but it is now a declared requirement.

Defer it until the current hub loop is fully hardened, then return to integrate:
- `Frontend Dev`
- `Backend Dev`
- `Infra Dev`
- `Docs Dev`

This is not optional cleanup. It is postponed scope that must stay visible in the plan.

## Practical implication

The next work should not be “add more worker roles.”

The next work should be:
- finish the remaining lifecycle and acceptance slices with the current role set
- keep packet model churn low
- avoid reopening the worker contract until the current loop is hardened enough to absorb the expansion cleanly
