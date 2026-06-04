Title: Prepare Architect Packet Flow
Doc-ID: paa-prepare-architect-packet-flow
Doc-Type: runbook
Status: active
Lifecycle-Stage: build
Created: 2026-05-18
Last-Edited: 2026-05-18
Author: Billy Weisberg
Repo: paa-platform
Component: ArchitectPacketPreparer
Domain: architect-packet-preparation
Keywords: architect-packet, packet-ready, producer, build, flow
Depends-On: 2026-05-16-assemble-coder-brief-flow.md, 2026-05-17-packet-ready-handoff-and-consumer-claim-validation.md
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
Summary: Defines the producer-side flow that promotes an approved brief to packet-ready authority and compiles an architect cycle packet.

# Prepare Architect Packet Flow

## Purpose
Define and validate the producer-side flow that promotes an approved coder brief to `packet_ready_execution_authority` and compiles a transport-ready `architect_cycle_packet` with:
- embedded packet-ready brief
- `coder_run_brief_ref`
- packet-governed authority metadata

## Command
Use:

```bash
cd /Users/billyweisberg/Repos/billyweisberg/paa-platform
PYTHONPATH=packages/paa-core/src:packages/paa-core/src:packages/paa-cli/src:. python -m paa_cli producer prepare-architect-packet \
  --manifest-path docs/2_Design/2026-05-17-paa-proof-slice-authority-manifest.json \
  --design-package docs/2_Design/2026-05-16-component-design-planning-service-stage1-design-package.json \
  --packet-output docs/2_Design/2026-05-17-component-design-planning-service-architect-cycle-packet.json \
  --brief-output docs/2_Design/2026-05-17-component-design-planning-service-packet-ready-coder-run-brief.json \
  --review-output docs/2_Design/2026-05-17-component-design-planning-service-architect-packet-review.md \
  --repo billyweisberg/paa-platform \
  --branch system-design-1 \
  --accepted-pr-number 9001 \
  --accepted-pr-url https://example.invalid/paa/proof/pull/9001 \
  --closed-issue-number 9001 \
  --closed-issue-url https://example.invalid/paa/proof/issues/9001 \
  --next-issue-number 9002 \
  --next-issue-url https://example.invalid/paa/proof/issues/9002 \
  --baseline-file docs/2_Design/2026-05-17-component-design-planning-service-packet-baseline-summary.json \
  --remaining-gap "Validate packet-ready authority and architect-packet preparation for the proof slice." \
  --next-move "promote approved brief to packet-ready authority" \
  --next-move "compile architect_cycle_packet with embedded packet-ready brief" \
  --focus "Component Design Planning Service packet-ready authority" \
  --focus "producer-side architect packet preparation" \
  --governance-reminder "Proof-only GitHub linkage is used for packet-governance validation in this run."
```

## What it does
The flow:
1. validates the active Stage 1 package
2. resolves the approved proof-slice brief from PAA
3. validates packet-readiness preconditions
4. derives a packet-ready brief artifact with:
   - `execution_readiness.readiness_class = execution_ready`
   - cleared packet-readiness blockers
   - proof execution issue / PR linkage in the brief artifact
5. compiles the `architect_cycle_packet`
6. validates the packet against `architect_cycle_packet.schema.json`
7. writes:
   - packet-ready brief artifact
   - architect packet artifact
   - architect packet review markdown
8. transitions the persisted brief to:
   - `packet_ready_execution_authority`
9. records durable packet-preparation metadata and authority-event history

## Proof-only linkage note
This validation run uses explicit proof-only GitHub linkage:
- accepted PR: `#9001`
- closed issue: `#9001`
- next issue: `#9002`

These identifiers exist only to validate packet-governance and transport packaging for the proof slice.
They are not claiming that a real downstream implementation issue has already been opened.

## Validation result
Validated successfully on `2026-05-17` for:
- `Component Design Planning Service`
- `coder_run_brief_id = fceab499-60f4-4a11-851d-b1059d8dbde9`

Outputs:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-component-design-planning-service-packet-ready-coder-run-brief.json`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-component-design-planning-service-architect-cycle-packet.json`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-component-design-planning-service-architect-packet-review.md`

Persisted state:
- `authority_state = packet_ready_execution_authority`
- `status = active`
- `packet_ready_at` populated
- `mark_packet_ready` authority event appended

## Important corrections during implementation
1. the packet must embed a packet-ready brief artifact, not a copied approved draft
2. `coder_run_brief_ref.schema_path` must point to the coder-brief schema, not the packet schema
3. rerunning packet preparation against an already packet-ready brief should refresh packet metadata without inventing a second authority transition