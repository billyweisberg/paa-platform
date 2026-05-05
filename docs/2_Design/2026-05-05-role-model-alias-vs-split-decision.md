# TechLead Hub Role Model Decision: Alias vs Real DB Split

## Summary

Decision for the current hub-model transition:
- keep `Delivery Architect` and `Authority Architect` as packet-level/runtime vocabulary
- keep DB persistence aliased to the existing `Architect` role for now
- do **not** introduce a real DB role split in this phase

This is an intentional transitional decision, not an accident.

## Why this came up

Phase B introduced first-class TechLead packet families and explicit role vocabulary such as:
- `Delivery Architect`
- `Authority Architect`
- `Python Dev`
- `QA`
- `TechLead`

The live control spine in `paa_dev` currently contains these roles for project `fractal-core-python`:
- `Architect`
- `Product Owner`
- `Project Designer`
- `Python Dev`
- `QA`
- `TechLead`

It does **not** currently contain:
- `Delivery Architect`
- `Authority Architect`

## Current decision

### Keep packet/runtime vocabulary explicit
Use the richer role language in:
- packet schemas
- packet payloads
- route policy
- prompt/skill surfaces
- TechLead reporting logic

That means these remain valid packet-level roles:
- `Delivery Architect`
- `Authority Architect`

### Keep DB persistence aliased for now
When persisting through the existing handoff spine:
- `Delivery Architect` -> `Architect`
- `Authority Architect` -> `Architect`

This applies only to the current DB role linkage used by:
- `paa.handoffs`
- `paa.queue_messages`
- related reporting joins

## Why not split now

A real DB split is not free. It would require coordinated changes across:
- role seed data / migrations
- project bootstrap/install assumptions
- queue-routing semantics
- historical reporting interpretation
- automation agent-role joins
- possibly existing analytics/reporting docs

Right now we do **not** yet have:
- a dedicated Delivery Architect queue
- a distinct Authority Architect control surface in the consumer repo
- historical reporting that truly depends on differentiating those two roles at the DB layer

So a DB split now would add risk and migration cost before we are using the distinction operationally end to end.

## Why aliasing is acceptable for now

The important distinction in the current phase is:
- runtime and packet contracts are becoming more precise
- the persistence spine is still catching up

That means aliasing is acceptable **only** while all of the following remain true:
1. `Delivery Architect` and `Authority Architect` still share the architecture/control queue path
2. TechLead routing/reporting does not require separate historical DB analytics for those two roles
3. operator workflows can still interpret persisted `Architect` rows correctly from packet payload context

## Risks of keeping the alias too long

If we leave the alias in place indefinitely, we create these problems:
- handoff analytics blur producer-side vs consumer-side architect work
- route history becomes harder to query cleanly
- later migrations become more confusing because historical data is overloaded
- future worker-role expansion may get blocked by role-name ambiguity

So the alias is a valid transition, not a final model.

## Trigger conditions for a real DB role split

We should introduce real DB roles when one or more of these become true:
1. `Delivery Architect` gets a durable, distinct consumer-side queue or automation lane
2. `Authority Architect` gets first-class producer-side escalation persistence that needs to be queried separately from delivery review
3. TechLead reports need historical metrics split by `Delivery Architect` vs `Authority Architect`
4. branch/worktree lineage analytics need to differentiate delivery review loops from producer authority escalations
5. future worker-role growth makes role-precision in `paa.handoffs` operationally necessary rather than merely descriptive

## Recommended follow-on shape when we do split

When the split is worth doing, the cleaner path is:
1. add real role rows for:
   - `Delivery Architect`
   - `Authority Architect`
2. update role resolution / install bootstrap to seed them deterministically
3. preserve old `Architect` history as historical data
4. stop aliasing new packets to `Architect`
5. update TechLead/traceability reporting to surface the new split directly

## Immediate implementation rule

For the current hub-model phases:
- packet route rules stay explicit
- operator prompts stay explicit
- DB persistence may alias the two architect variants back to `Architect`
- any code relying on persisted role history must treat this as a known temporary collapse of semantics

## Status

Decision: `keep alias for now; revisit on first queue/runtime split that makes the distinction operationally necessary`
