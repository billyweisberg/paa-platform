# Proof-Only Closeout Policy

Date: 2026-05-17

## Purpose

Define whether PAA should support a formal proof-only closeout path for validation slices that are intentionally not backed by live GitHub merge and issue-closure state.

This note exists because the self-hosted proof slice validated:
- producer derivation through `packet_ready_execution_authority`
- consumer bootstrap
- worker result
- QA pass

But it correctly failed closed at:
- `QA Pass -> Closeout`

The failure happened because the current closeout path is designed to require real GitHub merge or issue-closure evidence.

That behavior is correct for live delivery slices.
It is not sufficient to answer whether PAA should also support proof-only validation slices as a first-class governed mode.

## Decision

PAA **should support** a formal proof-only closeout policy.

But that policy must be:
- explicit
- separately governed
- visibly distinct from live delivery closeout
- unable to impersonate live acceptance, merge, or issue closure

## Why A Formal Proof-Only Policy Is Better Than Borrowing Live Closeout

A live-closeout proof would tell us whether the current runtime can close a real GitHub-backed slice.
That is useful later.

It does **not** answer the architectural question exposed by this validation cycle:
- should proof slices have a sanctioned terminal state when they are designed to validate process and architecture rather than ship a merged change?

If we keep borrowing the live-closeout path for proof slices, we create three problems:

1. governance ambiguity
- a proof run looks artificially incomplete unless we create real GitHub merge state

2. semantic drift
- proof completion starts pretending to mean the same thing as live delivery acceptance

3. operator pressure toward unsafe workarounds
- people will be tempted to fake or smuggle merge/closeout semantics just to make a proof run look finished

That is worse than stopping cleanly.

## Policy Boundary

### Live delivery closeout

Live delivery closeout remains the only path that may claim:
- merged implementation
- closed issue
- accepted delivery slice
- production-close lineage

Live delivery closeout must continue to require real external engineering state such as:
- merged PR
- closed issue
- protected-path checks
- any required QA and approval conditions

### Proof-only closeout

Proof-only closeout is a different terminal meaning.

It may claim only that:
- the proof slice completed its intended validation path
- the required proof checkpoints were exercised successfully
- the result is sufficient to advance architecture, derivation, tooling, or implementation readiness decisions

It may **not** claim that:
- a PR was merged
- an issue was closed
- production acceptance occurred
- delivery lineage is fully complete in the live-delivery sense

## Intended Use Cases

Proof-only closeout is for slices whose purpose is one or more of these:
- derivation method validation
- architecture boundary validation
- self-hosted runtime validation
- queue and transport validation
- consumer-lane bootstrap validation
- tooling validation
- controlled proof-of-concept implementation runs

It is not for:
- normal feature delivery
- production merge workflows
- release acceptance
- hidden shortcuts around required delivery governance

## Preconditions For Proof-Only Closeout

A proof slice may only use the proof-only closeout path if all of the following are true:

1. the slice is explicitly declared proof-only in its authority context
2. the derived brief or packet authority explicitly preserves that proof-only designation
3. the slice has completed the required proof checkpoints for its declared goal
4. the proof outcome has been reviewed under the appropriate producer or Architect governance rules
5. the resulting terminal record is visibly marked as proof-only in every persisted artifact and projection

## Required Semantics

A formal proof-only closeout path should do all of the following:

1. record a durable terminal proof outcome
- not just leave the slice hanging after QA pass

2. preserve queue and packet hygiene
- source packets should still be acknowledged and closed out correctly

3. persist a distinct acceptance / terminal event category
- separate from live merge acceptance

4. preserve truthful lineage
- the slice should show as proof-complete, not live-delivery-complete

5. keep future projections honest
- dashboards, lineage views, and summaries must not collapse proof-only closeout into live merged closeout

## Proposed Terminal Vocabulary

The exact DB shape can be decided later, but the semantic vocabulary should distinguish at least:
- `approved_brief`
- `packet_ready_execution_authority`
- `qa_passed`
- `proof_only_closed`
- `live_closed`

Where:
- `proof_only_closed` means validation-complete under proof governance
- `live_closed` means merge/issue-close delivery-complete under live governance

## Minimal Modeling Implications

A formal proof-only closeout path likely requires:

1. slice-mode authority designation
- example concept: `execution_mode = live_delivery | proof_only`

2. terminal acceptance-event distinction
- proof-only closeout must be queryable separately from live closeout

3. projection distinction
- traceability and workflow summaries must show proof-only terminal state explicitly

4. runtime decision distinction
- `techlead-closeout-qa-pass` or its replacement should branch intentionally on proof mode versus live mode

## Architectural Placement

This policy belongs primarily in:
- consumer/runtime governance
- verification and acceptance semantics
- workflow / acceptance / closeout interpretation

It is not primarily a producer derivation concern, though producer-side authority must carry the proof-only designation forward.

So the architectural homes are likely:
- `Verification And Acceptance Service`
- closeout / acceptance policy layer
- workflow lifecycle closeout semantics

## Recommendation For Next Execution Choice

Choose this order:

1. first, model and implement formal proof-only closeout support
2. second, rerun the proof slice through that governed proof-only terminal path
3. only after that, if still valuable, run a live GitHub-backed closeout proof to validate the live delivery path separately

That sequence is better because it answers the architectural question before creating real GitHub side effects.

## Final Rule

Until formal proof-only closeout is implemented, the current runtime behavior is correct:
- proof-only slices should fail closed at live closeout
- they should not be pushed through normal merge/issue-close semantics just to make the proof look complete

That is not a failure.
It is an honest boundary.
