# Phase I1 Mini Plan: Hardening Spine And Acceptance Gate

## Summary

Start Phase I by establishing one operational hardening spine for the current proven role set:
- `TechLead`
- `Delivery Architect`
- `Python Dev`
- `QA`

Chosen scope:
- define one canonical end-to-end slice runbook
- define one prompt/runtime consistency checklist
- define one explicit automation unpause gate

Do not:
- broaden worker-role families yet
- invent new packet families
- introduce new lifecycle mutation types

The goal is to stop adding capability slices and instead measure the existing system against one shared acceptance framework.

## Why this slice is next

The core workflow and lifecycle model now exist:
- hub routing
- packet families
- role bridge
- lineage
- worktree ownership
- reset/superseded/closed cleanup

What is missing is not more architecture.
What is missing is one disciplined way to answer:
- does this system hold together end to end?
- do prompts match runtime reality?
- is it safe to unpause automations?

## Scope boundaries

### Included
- one canonical E2E runbook for the current role set
- one consistency checklist for prompts, commands, packet families, and lifecycle behavior
- one explicit unpause gate with pass/fail conditions

### Not included
- broader worker-role expansion
- new routing topology
- new lifecycle mutations
- production unpause itself

## Deliverables

### 1. Canonical E2E runbook

Create one runbook that describes the current supported path:

1. Delivery Architect assignment
2. Delivery Architect return
3. TechLead routes to Python Dev
4. Python Dev assignment, role worktree, and return
5. TechLead routes to QA
6. QA assignment, role worktree, and return
7. TechLead records the resulting decision
8. lifecycle cleanup paths remain available if the slice becomes:
   - `reset_required`
   - `superseded`
   - `closed`

This runbook should identify:
- the required commands
- the required packet families
- the expected queues
- the expected branch/worktree surfaces
- the expected pass/fail observations

### 2. Consistency checklist

Create one checklist that verifies the current system is internally coherent across:
- prompt guidance
- installed skills
- top-level wrapper commands
- TechLead runtime behavior
- packet-family defaults
- lifecycle mutation and cleanup surfaces

The checklist should explicitly call out legacy compatibility surfaces that still exist but should not be taught as active defaults.

### 3. Automation unpause gate

Create one explicit unpause gate for the current role set.

The gate should require:
- at least one canonical end-to-end slice pass
- no queue-state drift during the run
- no branch/worktree ownership ambiguity
- no prompt/runtime contract mismatch on active paths
- no hidden dependency on manual queue resolution

The gate should also define what still blocks unpause even if the E2E run mostly works.

## Acceptance criteria

This slice is complete when:
- there is one canonical current-state E2E runbook
- there is one explicit consistency checklist
- there is one explicit unpause gate
- the master map points to those artifacts as the Phase I spine
