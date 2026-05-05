# Phase E Decision: Add A Dedicated Lineage Query Helper Before Branch Mutation Automation

## Decision

The next slice should add a dedicated lineage query/report helper before any branch mutation automation is introduced.

Chosen direction:
- keep lineage transitions recorded in `techlead_decision_packet`
- add a narrow query/report helper over that persisted lineage state
- delay automatic branch creation, reset, supersession, or closure until that helper exists and is trusted

## Why this is the right next move

We now have:
- lineage fields on `techlead_assignment_packet`
- lineage fields on `techlead_decision_packet`
- lineage surfaced in `techlead-status`
- branch-aware decision emission for:
  - `reset_required`
  - `superseded`
  - `closed`

That is enough to persist lineage intent, but not yet enough to make branch mutation automation safe.

The remaining gap is operational visibility.

Before an automation changes branches or worktrees, we need one clear runtime surface that answers:
- what is the current canonical branch for this issue?
- what is the current active role branch, if any?
- what was the last lineage action?
- is the current lineage state `active`, `reset_required`, `superseded`, or `closed`?
- what branch was superseded?
- what reset reason was recorded?
- which packet recorded the current lineage state?

`techlead-status` now contains a lineage section, but it is still part of a broader status report.
A dedicated helper will make lineage inspection:
- simpler for agents
- easier to test
- less brittle for later branch mutation automation

## Recommendation

Phase E should add a narrow lineage helper, for example:

```bash
<consumer_repo>/.codex/paa/bin/paa-consumer techlead-lineage \
  --repo-root <consumer_repo> \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external>
```

That helper should:
- read the current persisted lineage-driving packets
- return one normalized lineage object
- fail closed when lineage is ambiguous
- become the only supported precursor to future branch mutation automation

## What this avoids

This avoids jumping too early to automation that:
- resets the wrong branch
- creates a role branch off stale lineage
- closes lineage without a durable prior query step
- re-derives branch state differently across roles

## What follows after Phase E

After a dedicated lineage query helper exists and is validated, the next branch-mutation slice can safely automate:
- role branch creation
- reset branch replacement
- superseded branch retirement
- closed lineage cleanup

That is the right order.
