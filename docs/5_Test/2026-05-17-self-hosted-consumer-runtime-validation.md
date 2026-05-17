# Self-Hosted Consumer Runtime Validation

Date: 2026-05-17
Repo: `/Users/billyweisberg/Repos/billyweisberg/paa-platform`
Proof slice:
- package: `paa-stage1-2026-05-16-component-design-planning-service`
- brief: `paa-coder-2026-05-16-component-design-planning-service-governed-draft`
- issue: `9002`
- proof PR linkage: `9001`

## Goal
Validate the next execution boundaries after packet-ready authority:
- self-hosted consumer runtime bootstrap in `paa-platform`
- `Packet -> Full Consumer Lane Execution`
- worker result
- QA pass
- closeout

## What was required
A self-hosted proof slice exposed four real runtime/derivation gaps that had to be corrected before validation could continue:
1. `paa_consumer.techlead` assumed a fixed installed authority filename and a fixed GitHub repo.
2. proof-only packet context was not usable when live GitHub issue/PR records were intentionally absent.
3. the Stage 1 proof `DesignPackage` had no issue binding, so the consumer lane could not resolve the work item identity from persisted authority.
4. packet-ready governance advanced `authority_state` without persisting the packet-ready brief body back into `paa.coder_run_briefs`.

## Corrections applied
Code corrections:
- `packages/paa-consumer/src/paa_consumer/techlead.py`
  - resolve installed authority manifest path dynamically
  - resolve GitHub repo from installed authority
  - fall back to packet GitHub context when live GitHub issue/PR lookup is unavailable
  - pass `--project-slug` through worker/QA result compilation commands
  - resolve proof-slice issue number from persisted `DesignPackage -> WorkItem` linkage
- `packages/paa-producer/src/paa_producer/design_package_deriver.py`
  - allow a proof slice to gain an issue binding later without forking its work-item identity
- `packages/paa-producer/src/paa_producer/architect_packet_preparer.py`
  - persist packet-ready `brief_json` and `generated_from_json.readiness_class = execution_ready`

Authority/data corrections:
- updated `docs/2_Design/2026-05-16-component-design-planning-service-stage1-design-package.json`
  - `authority_context.issue_number = 9002`
- re-ran `derive-design-package`
  - preserved `work_item_id = 9e4509a5-5738-476b-a417-28e0012278f1`
  - updated persisted work item to `issue_number = 9002`
- re-ran packet preparation
  - persisted `brief_json.execution_readiness.readiness_class = execution_ready`

Runtime setup performed:
- created repo-local `.venv` with Python 3.12
- installed editable `paa-core`, `paa-producer`, and `paa-consumer`
- installed consumer runtime into `.codex/paa/`
- installed a minimal self-hosted proof authority package into `.project/data/paa/authority/current/`

## Validation results

### 1. Self-hosted consumer runtime bootstrap
Result: `PASS`

Evidence:
- repo-local wrappers installed under `.codex/paa/bin/`
- consumer automations and skills installed under `.codex/`
- runtime validation returned:
  - `authority_version = 2026-05-16.1`
  - `ok = true`
- `automation-preflight --project-slug paa-platform --target-role python-team` returned:
  - `should_invoke_model = true`
  - `workflow_stage = architect_authorized`
  - `current_owner_role = Python Dev`

### 2. Packet -> Full Consumer Lane Execution
Result: `PASS`

Evidence:
- `techlead-handoff-to-role-worktree --target-role python-team`
  - created deterministic role branch: `issue-9002-dev`
  - created deterministic worktree: `.codex-work/worktrees/paa/issue-9002-dev`
  - compiled a TechLead assignment packet for the proof slice
- `techlead-role-entry --target-role python-team`
  - resolved assignment artifact, lineage, and compile surfaces cleanly
- `techlead-role-result-assist --target-role python-team`
  - produced the worker result input contract and return path cleanly

### 3. Worker result
Result: `PASS with cleanup caveat`

Evidence:
- compiled and validated `worker_result_packet`
- dispatched packet to `fractal-core-architecture`
- result packet message id:
  - `fcore-worker-2026-05-17-issue9002-python-team`
- routed queue:
  - `fractal-core-architecture`

Cleanup caveat:
- the first worker return was launched from a locally compiled assignment artifact that had not itself been sent through the queue runtime
- packet dispatch succeeded, but source-assignment acknowledgment correctly failed because the next claimable Python-queue message was still the older architect packet
- this did not invalidate worker-result compilation or dispatch; it exposed a sequencing truth about queue-backed cleanup

### 4. QA pass
Result: `PASS`

Evidence:
- `techlead-handoff-to-role-worktree --target-role qa --send`
  - compiled and sent QA assignment packet
  - acknowledged the worker result packet cleanly
  - created deterministic QA branch/worktree:
    - `issue-9002-qa`
- `techlead-role-return --target-role qa --send`
  - compiled and validated `qa_verification_packet`
  - dispatched packet to `fractal-core-architecture`
  - acknowledged the QA assignment packet cleanly
- QA packet message id:
  - `fcore-qa-2026-05-17-issue9002-paa-coder-2026-05-16-component-design-planning-service-governed-draft`
- verification status:
  - `pass`

### 5. Closeout
Result: `BLOCKED AS DESIGNED`

Evidence:
- `techlead-closeout-qa-pass` returned:
  - `reason = slice_not_merged_or_closed`
- effective GitHub state during proof closeout:
  - `issue_state = OPEN`
  - `pr_state = OPEN`
  - `pr_merged_at = null`

Interpretation:
- closeout still depends on live GitHub merge/issue closure semantics
- that is correct for the current architecture and governance model
- the proof slice used intentionally non-live GitHub linkage (`example.invalid` URLs and no real issue/PR), so closeout should not auto-succeed

## Final boundary decision
Validated as `GO`:
- `System Design -> Producer Derivation -> Packet-Ready Execution Authority`
- `Packet-Ready Execution Authority -> Consumer Bootstrap`
- `Packet -> Consumer Lane Execution Surfaces`
- `Packet -> Worker Result`
- `Worker Result -> QA Assignment`
- `QA Assignment -> QA Pass Packet`

Validated as `NO-GO` for proof-only closeout:
- `QA Pass -> Closeout`

Reason:
- closeout currently requires real GitHub merge/issue closure state
- this proof slice intentionally used proof-only GitHub linkage rather than live issue/PR records

## Recommended next move
Decision taken on `2026-05-17`:
1. formal proof-only closeout policy first
   - policy record:
     - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-proof-only-closeout-policy.md`
   - rationale:
     - define whether proof slices have a distinct governed terminal state before creating live GitHub side effects
2. live-closeout proof later, if still useful
   - create a real proof issue and PR in `billyweisberg/paa-platform`
   - re-run the proof slice from packet-ready authority through closeout against live GitHub state
