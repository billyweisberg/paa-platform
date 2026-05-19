Title: PAA Language Governance Rules
Doc-ID: paa-language-governance-rules
Doc-Type: policy
Status: active
Lifecycle-Stage: reference
Created: 2026-05-19
Last-Edited: 2026-05-19
Author: Billy Weisberg
Repo: paa-platform
Component: PaaLanguageGovernance
Domain: terminology
Keywords: paa, language, governance, terminology, evidence, claims, narrative
Depends-On: paa-engineering-terminology-glossary.md, 2026-05-18-paa-system-design-tables-method.md
Supersedes: 
Superseded-By: 
Canonical: true
Review-After: 2026-06-15
Owners: 
Expires: 
Issue: 
PR: 
Authority-Source: 
Implementation-Status: 
Summary: Defines the mandatory language rules that govern architectural descriptions, status claims, and evidence-backed narration in PAA.

# PAA Language Governance Rules

## Purpose

These rules govern how PAA work may be described in docs, reviews, status updates, and implementation notes.

The goal is not stylistic neatness.
The goal is to prevent drift caused by:
- broad narrative claims
- ambiguous ownership language
- status claims without evidence
- architectural wording that makes procedural hubs sound like designed components

## Core Rule

PAA language must be:
- bounded
- evidence-backed
- ownership-aware
- lifecycle-aware
- precise enough to map to code, records, or governed documents

If a claim cannot be mapped to a concrete authority source, code path, DB truth, or governed document, it must not be stated as established fact.

## Required Language Behavior

### 1. Separate fact from interpretation

Every substantial architecture or implementation statement must distinguish between:
- `Fact`
- `Interpretation`
- `Next decision`

Allowed:
- `Fact: Workflow transitions are persisted in paa.workflow_transitions.`
- `Interpretation: TechLead review routing is still hybrid because it depends on runtime hub logic in techlead.py.`

Disallowed:
- `The workflow system is complete.`

### 2. State ownership explicitly

When describing a capability, name the owner.

Allowed:
- `WorkflowLifecycleService owns workflow transition evaluation and application for supported families.`
- `techlead.py still owns hybrid runtime orchestration for review and routing.`

Disallowed:
- `The system handles review routing.`

### 3. Qualify alignment claims

Do not say a path, module, or service is `aligned` unless the structure actually reflects the governing model.

Use one of:
- `aligned`
- `hybrid`
- `legacy`
- `not yet established`

If a path crosses aligned and legacy code, describe the path as `hybrid`.

### 4. Prefer table-backed governance for gap analysis

When the purpose is remediation, planning, traceability, or gap detection, do not rely on prose alone.

Use a governed table artifact for:
- process steps
- ownership boundaries
- operational remediation
- status classifications

### 5. Fail closed on vague architecture language

The following terms require qualification or replacement:
- `system`
- `handles`
- `supports`
- `works`
- `done`
- `complete`
- `integrated`
- `real`
- `clean`

Allowed only if followed by a precise scope and evidence.

Example:
- `Supported transition family: worker_result_returned.`
- not `Workflow is supported.`

## Disallowed Narrative Patterns

Disallowed unless immediately qualified by evidence:
- `the system knows`
- `the architecture does`
- `this is aligned`
- `this is complete`
- `we now have X` when X is only partial or scoped to one path
- `the component exists` when only a note or shell exists

## Required Claim Anchors

A substantial claim should be anchored to at least one of:
- governed document path
- code path
- DB truth/table/view
- validation artifact
- test result

## Preferred Reporting Form

For meaningful status updates, prefer this structure:
- `Implemented`
- `Validated`
- `Not true yet`
- `Risk / ambiguity`

This structure is preferred because it blocks narrative smoothing.

## Relationship To Other Reference Docs

Use these rules with:
- `paa-component-naming-rules`
- `paa-status-claim-rules`
- `paa-architecture-anti-patterns`
- `paa-engineering-terminology-glossary`

## Governance Intent

These rules exist to stop language from hiding:
- unclear ownership
- hybrid paths described as aligned
- procedural hubs described as architecture
- partial implementations described as complete systems
