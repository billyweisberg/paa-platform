Title: Dev And Qa Packet Compilers
Doc-ID: paa-dev-and-qa-packet-compilers
Doc-Type: design-note
Status: active
Lifecycle-Stage: build
Created: 2026-05-18
Last-Edited: 2026-05-18
Author: Billy Weisberg
Repo: paa-platform
Component: DevAndQaPacketCompilers
Domain: packet-compilation
Keywords: dev, qa, packet, compiler, build, flow, precursor
Depends-On: 
Supersedes: 
Superseded-By: 
Canonical: false
Review-After: 2026-06-15
Owners: 
Expires: 
Issue: 
PR: 
Authority-Source: 
Implementation-Status: 
Summary: Captures the next packet-compilation design direction for dev and QA result packets after architect packet preparation.

# Dev And QA Packet Compilers

This note captures the next packet-compilation step after the PAA-backed Architect packet compiler.

## Goal

Move `slice_result_packet` and `qa_verification_packet` generation away from hand-written JSON and toward compiled packet shells that draw from:

- published authority
- Stage 1 design package state in PAA
- selected `coder_run_brief`
- explicit Dev or QA run evidence

The packet compiler should fill structural and narrative sections automatically where the system already knows the answer, while still letting the role attach the run-specific evidence that only the role can supply.

## New compiler commands

### Python / Dev

```bash
python3 future `paa-platform` authority/runtime command surface materialize-slice-result-packet \
  --project-slug fractal-core-python \
  --package-id-external <design_package_id_external> \
  --brief-id-external <brief_id_external> \
  --repo <owner/repo> \
  --issue-number <issue_number> \
  --issue-url <issue_url> \
  --pr-number <pr_number> \
  --pr-url <pr_url> \
  --branch <branch_name> \
  --dev-input-file /absolute/path/to/dev-input.json \
  --output .codex-work/slice-result-packet.json \
  --review-output .codex-work/slice-result-packet.review.md
```

### QA

```bash
python3 future `paa-platform` authority/runtime command surface materialize-qa-verification-packet \
  --project-slug fractal-core-python \
  --package-id-external <design_package_id_external> \
  --brief-id-external <brief_id_external> \
  --repo <owner/repo> \
  --issue-number <issue_number> \
  --issue-url <issue_url> \
  --pr-number <pr_number> \
  --pr-url <pr_url> \
  --branch <branch_name> \
  --qa-input-file /absolute/path/to/qa-input.json \
  --source-packet-path /absolute/path/to/slice-result-packet.json \
  --output .codex-work/qa-verification-packet.json \
  --review-output .codex-work/qa-verification-packet.review.md
```

## What is derived automatically

### Dev packet derivation

The compiler now derives or fills:

- `authority_context`
- selected `coder_run_brief_ref`
- embedded `coder_run_brief`
- `coder_brief_resolution`
- default `workflow_compliance`
- default `merge_status`
- default `architect_decision_needed`
- fallback `result_summary`
- fallback `mechanism_changed`

The Dev input file remains responsible for run-specific evidence such as:

- command results
- artifacts
- PR readiness
- any higher-fidelity result summary

### QA packet derivation

The compiler now derives or fills:

- `authority_context`
- selected `coder_run_brief_ref`
- embedded `coder_run_brief`
- `coder_brief_resolution`
- `verification_scope`
- fallback `mechanical_checks`
- fallback `technical_scope_checks`
- fallback `protected_path_checks`
- fallback `artifact_checks`
- fallback `recommended_action`

The QA input file remains responsible for:

- final `verification_status`
- findings
- any more precise mechanical or technical scope check outcomes
- explicit reviewer conclusions when the defaults are not sufficient

## Fail-closed behavior

### Dev compiler

The Dev compiler fails closed when:

- the selected design package does not exist in PAA
- the selected coder brief does not exist in the package
- the selected brief is not execution-eligible unless `--allow-nonready-brief` is passed

### QA compiler

The QA compiler fails closed when:

- the selected design package does not exist in PAA
- the selected coder brief does not exist in the package
- `verification_status` is missing or invalid

## Review outputs

Both compilers now optionally emit a review markdown artifact.

The review artifact is meant to be the role-facing pause point before send:

- Dev reviews the selected component, mechanism changed, validation, and acceptance ask
- QA reviews the verification scope, scope checks, protected path checks, findings, and recommended action

That gives the role a clean final check before validating and sending the packet.

## Proving run

The proving package now has validated compiled packet examples for:

- `slice_result_packet`
- `qa_verification_packet`

Files:

- `a proving compiled Dev packet artifact in repo-local scratch output`
- `a proving compiled Dev packet review artifact in repo-local scratch output`
- `a proving compiled QA packet artifact in repo-local scratch output`
- `a proving compiled QA packet review artifact in repo-local scratch output`

Both packet JSON files validate successfully with the live handoff validator.

## Why this matters

This extends the same compiled-authority pattern across the whole loop:

- Architect packet compiled from PAA design and sequence state
- Python result packet compiled from PAA brief plus Dev run evidence
- QA verification packet compiled from PAA brief plus QA run evidence

That reduces free-form packet writing and keeps the project record aligned with the execution record.
