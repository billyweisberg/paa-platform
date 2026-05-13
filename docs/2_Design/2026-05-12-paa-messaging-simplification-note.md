# Why PAA Messaging Is Too Complex

Date: 2026-05-12

## Summary

The current PAA handoff model is more complicated than the underlying workflow requires.

Today, a single role transition often has to do all of the following:
- deliver work to the next role
- preserve execution context
- persist lineage and workflow state
- support retries and recovery
- preserve operator traceability
- close the previous queue packet correctly

Those are all real needs, but they are currently coupled too tightly to queue packet lifecycle.

The result is a system where queue behavior carries too much workflow meaning, and stale queue artifacts can remain operationally confusing even when the business outcome is correct.

## The Actual Problem

The core job is simple:
- determine who owns the slice next
- wake that owner up
- preserve enough context for them to act safely
- preserve a durable history of what happened

The current model makes queue packet lifecycle responsible for too much of that job.

Observed consequences:
- a role can send a correct result packet while the original assignment packet still remains on the queue
- queue cleanup can require a second explicit transaction after a successful role result send
- operators must reason about both workflow state and queue residue at the same time
- the system feels brittle even when routing logic is mostly correct

## Root Cause

PAA is currently halfway between two architectures:

1. `message-first workflow engine`
- each queue packet is treated as a meaningful unit of workflow truth
- progress depends on consuming one packet and emitting another

2. `state-first orchestration engine`
- durable workflow state exists outside the queue
- queue messages exist mainly to wake roles up and deliver context

The runtime has already grown real state, lineage, and reporting behavior, but queue lifecycle still carries too much authority.

That creates avoidable complexity.

## What Should Be Authoritative

The cleaner target model is:

- durable workflow state is authoritative
- queue messages are wakeup and transport signals
- packets are execution context and evidence, not the sole source of lifecycle truth

In plain terms:
- "Python Dev owns issue 110" should be a durable state fact
- the queue message should only help wake Python Dev up
- if a wakeup message lingers, that is an operational cleanup issue, not a workflow-truth issue

## Simpler Pattern Options

### Option A: DB-backed state machine, queue as wakeup

This is the preferred target.

Pattern:
- workflow owner/stage lives in durable DB state
- queue message says, effectively: "wake up and inspect issue 110"
- role reads authoritative state and acts
- completion updates authoritative state first
- queue cleanup is secondary transport hygiene

Benefits:
- simpler mental model
- stale queue artifacts matter less
- easier retry and recovery
- cleaner operator reporting

### Option B: Single durable handoff record with lease

Pattern:
- one durable handoff record per active slice owner
- the next role acquires a lease/claim on that handoff
- completion advances the record to the next owner
- queue is optional wakeup only

Benefits:
- avoids the dual-packet residue pattern
- claim lifecycle is easier to reason about than consume-emit-ack across two packets

### Option C: Append-only event log with derived state

Pattern:
- every transition appends an event
- current owner/stage is derived from the event stream
- queue is wakeup only

Benefits:
- strong auditability
- easy replay/debug story

Tradeoff:
- more conceptual weight than Option A for current PAA needs

## Recommended Target

Adopt Option A:
- authoritative workflow state in durable runtime/DB state
- queue semantics narrowed to wakeup/transport
- packets preserved as execution context plus evidence

This keeps the benefits of the current packet contracts while reducing the amount of workflow truth that depends on queue behavior.

## What This Means For Current PAA

This note does **not** require immediate runtime replacement.

Short-term hardening still makes sense:
- atomic send-plus-ack in role return flows
- better queue observability
- cleaner closeout behavior

But those should be treated as stabilization of the current packet model, not the long-term end state.

## Target Design Rules

### 1. Queue residue must not determine workflow truth
If workflow truth says the slice is already owned by the next role, an old queue packet should not be able to make the operator question who owns the slice.

### 2. Role wakeup and workflow transition should be separable
A queue message may fail, be retried, or linger. That should not force the workflow model itself to become ambiguous.

### 3. State transitions should be explicit and queryable without queue archaeology
Operators should be able to answer:
- who owns the slice now
- what stage it is in
- what packet or event caused that transition

without needing to infer state from queue leftovers.

### 4. Packets should remain useful, but less authoritative
Packets still matter for:
- execution context
- evidence
- replay/debug
- cross-process transport

But they should not be the only durable expression of state.

## Migration Direction

A practical migration path is:

1. keep current packet schemas
2. keep queue transport
3. make DB/runtime state authoritative for owner/stage
4. treat queue packets as wakeup/context artifacts
5. progressively reduce places where queue cleanup determines workflow interpretation

## Immediate Follow-Ups

1. keep hardening the current atomic return/ack flows
2. add explicit design work for state-authoritative orchestration
3. decide how much of `paa.queue_messages`, `paa.handoffs`, and TechLead status can become the authoritative owner/stage layer
4. eventually narrow queue reporting from "what is truth?" to "what transport cleanup remains?"

## Conclusion

PAA messaging feels too complicated because the queue layer is currently carrying too much workflow meaning.

The simpler target is not "remove packets" or "remove queues."
The simpler target is:
- state is truth
- queue is wakeup
- packets are context and evidence

That preserves the strengths of the current system while removing the most confusing part of the model.
