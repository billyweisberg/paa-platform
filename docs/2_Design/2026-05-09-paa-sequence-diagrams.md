# PAA Sequence Diagrams

## Purpose

Show the major call chains in the PAA system so design work can reason about runtime ownership, side effects, and hard-coded seams.

These sequences focus on the current target architecture:
- Authority Architect producer flow
- TechLead assignment flow
- generic worker return flow
- Delivery Architect return flow
- QA return flow
- lifecycle cleanup flow

## 1. Producer Packet Compilation And Send

```mermaid
sequenceDiagram
  participant AA as Authority Architect
  participant APP as appdev repo
  participant PROD as paa-producer runtime
  participant DB as PAA DB
  participant RMQ as RabbitMQ

  AA->>APP: invoke producer packet command
  APP->>PROD: compile packet from authority/design/brief context
  PROD->>PROD: validate envelope + payload + route policy
  PROD->>DB: persist packet_compilation event (optional)
  PROD->>RMQ: publish packet
  PROD->>DB: persist handoff + queue_message send state
  PROD-->>AA: compiled/sent result
```

## 2. TechLead Assignment Flow

```mermaid
sequenceDiagram
  participant TL as TechLead automation
  participant CONS as paa-consumer runtime
  participant DB as PAA DB
  participant RMQ as RabbitMQ
  participant ROLE as Target spoke role

  TL->>CONS: techlead-emit-next-assignment
  CONS->>CONS: inspect workflow state and lineage
  CONS->>CONS: derive target_role + assignment_type
  CONS->>CONS: compile techlead_assignment_packet
  CONS->>CONS: validate route policy and payload
  CONS->>RMQ: send assignment packet
  CONS->>DB: persist handoff + queue message state
  RMQ-->>ROLE: assignment available for claim
```

## 3. Generic Worker Role Return Flow

```mermaid
sequenceDiagram
  participant W as Worker automation
  participant CONS as paa-consumer runtime
  participant WT as Role worktree
  participant RMQ as RabbitMQ
  participant DB as PAA DB
  participant TL as TechLead runtime

  W->>CONS: automation-preflight
  CONS-->>W: should_invoke_model / skip
  W->>CONS: techlead-inspect-role-worktree
  CONS-->>W: assignment + lineage + worktree context
  W->>WT: execute bounded implementation work
  W->>CONS: techlead-role-result-assist
  CONS-->>W: worker_result_packet compile surface
  W->>CONS: techlead-role-return --send
  CONS->>CONS: compile worker_result_packet
  CONS->>RMQ: send worker_result_packet
  CONS->>DB: persist handoff + queue message state
  RMQ-->>TL: worker result available
```

## 4. Delivery Architect Return Flow

```mermaid
sequenceDiagram
  participant DA as Delivery Architect automation
  participant CONS as paa-consumer runtime
  participant WT as Delivery worktree
  participant RMQ as RabbitMQ
  participant TL as TechLead runtime

  DA->>CONS: automation-preflight
  CONS-->>DA: should_invoke_model / skip
  DA->>CONS: techlead-inspect-role-worktree
  CONS-->>DA: assignment + lineage + worktree context
  DA->>WT: review scope / architecture / authority impact
  DA->>CONS: techlead-role-result-assist
  CONS-->>DA: delivery_review_packet compile surface
  DA->>CONS: techlead-role-return --send
  CONS->>RMQ: send delivery_review_packet
  RMQ-->>TL: delivery review available
```

## 5. QA Return Flow

```mermaid
sequenceDiagram
  participant QA as QA automation
  participant CONS as paa-consumer runtime
  participant WT as QA worktree
  participant RMQ as RabbitMQ
  participant TL as TechLead runtime

  QA->>CONS: automation-preflight
  CONS-->>QA: should_invoke_model / skip
  QA->>CONS: techlead-inspect-role-worktree
  CONS-->>QA: assignment + lineage + worktree context
  QA->>WT: execute verification work
  QA->>CONS: techlead-role-result-assist
  CONS-->>QA: qa_verification_packet compile surface
  QA->>CONS: techlead-role-return --send
  CONS->>RMQ: send qa_verification_packet
  RMQ-->>TL: QA result available
```

## 6. TechLead Decision And Next Routing Flow

```mermaid
sequenceDiagram
  participant TL as TechLead automation
  participant CONS as paa-consumer runtime
  participant RMQ as RabbitMQ
  participant DB as PAA DB
  participant ROLE as Next target role

  TL->>CONS: inspect queue + status + lineage
  CONS->>CONS: derive workflow_stage from current packet set
  CONS->>CONS: choose next TechLead decision
  CONS->>CONS: compile techlead_decision_packet
  CONS->>DB: persist decision context
  alt decision requires new spoke assignment
    CONS->>CONS: compile techlead_assignment_packet
    CONS->>RMQ: send assignment packet
    CONS->>DB: persist handoff + queue message
    RMQ-->>ROLE: next assignment available
  else decision is terminal or pause/escalation only
    CONS-->>TL: no spoke assignment emitted
  end
```

## 7. Lifecycle Cleanup Flow

```mermaid
sequenceDiagram
  participant TL as TechLead automation
  participant CONS as paa-consumer runtime
  participant GIT as git worktree helpers
  participant DB as PAA DB

  TL->>CONS: techlead-lineage / stale / ownership
  CONS-->>TL: queryable lifecycle precursor
  TL->>CONS: reset-cleanup / superseded-cleanup / closed-cleanup
  CONS->>CONS: validate eligible workflow_stage and target_role
  CONS->>CONS: compile supporting techlead_decision_packet when needed
  CONS->>GIT: remove stale role worktree
  CONS->>DB: persist cleanup-related decision state
  CONS-->>TL: cleanup_result
```

## 8. Dynamic Worker Role Stress Point Sequence

This sequence shows where the current system stops being dynamic.

```mermaid
sequenceDiagram
  participant CFG as Project role definition
  participant CONS as paa-consumer runtime
  participant AUTO as Automation registration
  participant TL as TechLead runtime

  CFG->>CONS: define new worker role
  CONS->>CONS: normalize role name
  CONS->>CONS: map role to branch suffix
  CONS->>CONS: map role to queue binding
  CONS->>CONS: map role to CLI target choices
  CONS->>AUTO: expect matching automation definition
  TL->>CONS: assign target_role

  Note over CONS: Today these steps are still partly hard-coded.
  Note over CFG,CONS: Dynamic Worker Roles requires these mappings to become data-driven.
```

## Sequence Summary

The call chains are already structurally sound.
The main non-dynamic seams are not the DB or the packet envelope.
They are:
- role discovery
- route-policy derivation
- queue binding derivation
- branch suffix derivation
- automation-definition derivation
- CLI and helper-role enumeration
