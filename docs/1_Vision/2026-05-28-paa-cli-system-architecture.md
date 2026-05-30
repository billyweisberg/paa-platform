Title: PAA CLI System Architecture
Doc-ID: paa-cli-system-architecture
Doc-Type: vision
Status: active
Lifecycle-Stage: vision
Created: 2026-05-28
Last-Edited: 2026-05-28
Author: Billy Weisberg
Repo: paa-platform
Component: PAAOperatorCLI
Domain: operator-cli
Keywords: paa, cli, operator, architecture, producer, consumer, authority, runtime, agent-oriented-architecture, microsoft-agent-framework
Depends-On: 2026-05-28-paa-authority-stack-and-operator-architecture.md
Supersedes: 
Superseded-By: 
Canonical: true
Review-After: 2026-06-25
Owners: 
Expires: 
Issue: 
PR: 
Authority-Source: 
Implementation-Status: 
Summary: Defines the top-level command families and ownership boundaries for the unified operator-facing PAA CLI, including agent-host worker operation and diagnostics.

# PAA CLI System Architecture

## Vision Marker

This document is a Vision-layer authority document.

It defines the unified command architecture for the full PAA operator CLI.

## Core Goal

The PAA CLI must expose the methodology as an operable system.

It must not remain a loose collection of scripts split across repos and contexts.

The CLI must provide one operator-facing surface for:
- authority
- derivation
- planning
- runtime workers
- queue operations
- verification
- acceptance
- reporting
- operations/admin

It must also provide one operator-facing surface for bounded agent-host execution where worker roles use model-driven reasoning.

## Primary Design Principle

Command families should reflect lifecycle capability, not repository accident.

The operator should think in terms of:
- what authority exists
- what is ready
- what work is next
- what worker is running
- what packet is blocked
- what slice passed or failed
- what can be accepted safely

## Top-Level Command Families

### `paa authority`
Purpose:
- inspect and validate published authority

Includes:
- current authority views
- snapshots
- sync-current
- governed lint
- authority diff
- vocabulary validation
- source-authority checks

### `paa derive`
Purpose:
- derive executable structured state from authority

Includes:
- materialize component spec
- derive design package
- evaluate derivation readiness
- derive implementation plan
- assemble coder brief
- derive next activity bundle

### `paa plan`
Purpose:
- inspect and manage implementation-plan truth

Includes:
- plan progress
- reconcile progress
- list activities
- dependency graph views
- blocked and deferred analysis
- next-slice inspection

### `paa worker`
Purpose:
- operate runtime worker services

Includes:
- start worker
- stop worker
- dry-run one packet
- run one bounded agent-host invocation
- inspect worker health
- replay worker job
- show injected services and handler map
- inspect normalized agent result
- inspect worker-host context package

### `paa queue`
Purpose:
- inspect and manage queue state and handoff flow

Includes:
- inspect queue
- preview next packet
- claim packet
- acknowledge packet
- resend packet
- dead-letter inspection
- packet validation

### `paa verify`
Purpose:
- run proof and verification flows

Includes:
- unit and integration proof
- model/code consistency
- spec/model consistency
- governed doc lint
- parity and tolerance validation when required
- QA packet assembly inputs
- worker-host result normalization checks when agent-backed roles are involved

### `paa accept`
Purpose:
- control post-verification transitions

Includes:
- accept slice
- reject slice
- safe merge checks
- issue-close checks
- next assignment derivation

### `paa report`
Purpose:
- project current truth to operators

Includes:
- realization dashboards
- authority snapshot views
- queue health
- worker health
- blocked work reports
- project progress summaries

### `paa ops`
Purpose:
- system operations and administration

Includes:
- migration commands
- environment diagnostics
- runtime state info
- lock diagnostics
- repair or reconcile operations
- bootstrap checks

## Producer And Consumer Relationship

The CLI must unify producer and consumer capabilities without erasing their different runtime responsibilities.

### Producer-aligned families
- `authority`
- `derive`
- `plan`
- `report`

### Consumer-aligned families
- `worker`
- `queue`
- `verify`
- `accept`

### Cross-cutting family
- `ops`

## Operator UX Requirements

The CLI must:
- support JSON and table output where practical
- fail closed when required authority is missing
- report blocking reasons explicitly
- avoid requiring internal repository trivia to use commands correctly
- expose dry-run modes for risky transitions
- expose bounded-run diagnostics for agent-host workers

## Command Design Rules

1. keep command nouns stable
2. prefer lifecycle verbs over implementation jargon
3. preserve structured machine-readable output
4. align command outputs to authority and runtime models already present in PAA
5. never hide authority gaps behind guessed defaults
6. never treat raw agent output as accepted system truth until it has been normalized into PAA structures

## Initial Implementation Direction

The first real implementation should unify existing working command surfaces rather than rewrite them.

Immediate candidates to absorb:
- current producer progress and next-slice commands
- current authority sync and lint flows
- current consumer service-map and diagnostic commands
- future worker-host dry-run and normalized-result inspection commands

## Non-Goals

This document does not define:
- exact parser framework
- exact command-line flags for every command
- worker runtime implementation details
- packet schema contents

Those belong in downstream Design artifacts.
