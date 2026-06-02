Title: PAA CLI Command Inventory And Migration Map
Doc-ID: paa-cli-command-inventory-and-migration-map
Doc-Type: design-note
Status: active
Lifecycle-Stage: design
Created: 2026-05-30
Last-Edited: 2026-06-02
Author: Billy Weisberg
Repo: paa-platform
Component: PAAOperatorCLI
Domain: operator-cli
Keywords: paa, cli, command inventory, migration map, producer, consumer, scripts
Depends-On: 2026-05-28-paa-cli-system-architecture.md, 2026-05-28-paa-operator-system-implementation-plan.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-06-20
Summary: Inventory of producer, internal consumer-package, and script command surfaces mapped to the unified `paa` CLI after the user-facing `paa_consumer` cutover was completed.

# PAA CLI Command Inventory And Migration Map

## Purpose

Create the first concrete inventory of the current operator-facing command surface.

This document exists to answer three questions:
1. what command surfaces already exist?
2. what functionality do they currently expose?
3. where should each command move in the unified `paa` CLI?

This is now a cutover-state inventory, not just a migration sketch.

## Scope

This inventory covers:
- current `paa-producer` commands
- current unified `paa` consumer/runtime commands
- internal `paa-consumer` package responsibilities that are no longer user-facing commands
- repo-local script surfaces that are still operator-relevant

It does not yet inventory:
- component/module/class ownership behind each command
- downstream project-repo wrappers
- every legacy helper outside `paa-platform`

That deeper inventory is the next pass.

## Current Command Surface Sources

Primary current sources:
- `packages/paa-producer/src/paa_producer/commands.py`
- `packages/paa-producer/src/paa_producer/__main__.py`
- `packages/paa-cli/src/paa_cli/app.py`
- `packages/paa-consumer/src/paa_consumer/`
- `scripts/docs/`
- `scripts/governance/`
- `scripts/runtime/`

## Top-Level Migration Rule

The unified operator CLI should be:
- `paa authority`
- `paa derive`
- `paa plan`
- `paa worker`
- `paa queue`
- `paa verify`
- `paa accept`
- `paa report`
- `paa ops`

Existing producer and former consumer commands should be absorbed into those families instead of preserved as parallel command roots long term.

## Producer Command Inventory

| Current command | Current package owner | Current purpose | Target unified `paa` family | Long-term canonical owner | Migration status |
|---|---|---|---|---|---|
| `install-producer-runtime` | `paa-producer` | install producer runtime assets | `paa ops install-producer-runtime` | ops/runtime install layer | migrate |
| `update-producer-runtime` | `paa-producer` | update producer runtime assets | `paa ops update-producer-runtime` | ops/runtime install layer | migrate |
| `publish-authority-package` | `paa-producer` | publish packaged authority | `paa authority publish` | producer authority publication | migrate |
| `smoke-test` | `paa-producer` | producer smoke validation | `paa verify producer-smoke` | verification layer | migrate |
| `authority` | `paa-producer` | authority-runtime subcommands | `paa authority ...` | authority subsystem | migrate |
| `derive-artifacts` | `paa-producer` | derive inventory/artifact set | `paa derive artifacts` | derivation subsystem | migrate |
| `derive-design-package` | `paa-producer` | derive Stage 1 design package | `paa derive design-package` | derivation subsystem | migrate |
| `evaluate-derivation-readiness` | `paa-producer` | evaluate package readiness | `paa derive readiness` | derivation subsystem | migrate |
| `derive-implementation-plan` | `paa-producer` | derive implementation plan from authority | `paa derive implementation-plan` | derivation subsystem | migrate |
| `materialize-component-spec` | `paa-producer` | materialize governed component spec into model truth | `paa derive materialize-component-spec` | derivation/materialization subsystem | migrate |
| `implementation-plan-progress` | `paa-producer` | inspect plan progress summary | `paa plan progress` | planning subsystem | migrate |
| `derive-next-activity-bundle` | `paa-producer` | derive next executable slice | `paa plan next` | planning subsystem | migrate |
| `reconcile-implementation-plan-progress` | `paa-producer` | recompute progress state | `paa plan reconcile` | planning subsystem | migrate |
| `assemble-coder-brief` | `paa-producer` | build draft coder brief | `paa derive coder-brief` | derivation subsystem | migrate |
| `author-brief-targets` | `paa-producer` | materialize brief targets | `paa derive brief-targets` | derivation subsystem | migrate |
| `review-coder-brief` | `paa-producer` | review brief readiness state | `paa derive review-brief` | derivation subsystem | migrate |
| `prepare-architect-packet` | `paa-producer` | prepare architect packet payload | `paa derive architect-packet` | derivation/handoff preparation | migrate |
| `materialize-readiness` | `paa-producer` | readiness CLI passthrough | `paa derive readiness-materialization` | derivation/readiness subsystem | migrate |
| `materialize-verification-obligations` | `paa-producer` | load verification obligations | `paa derive verification-obligations` | derivation subsystem | migrate |
| `load-issue-into-paa` | `paa-producer` | materialize issue into PAA structures | `paa authority load-issue` | authority ingestion subsystem | migrate |

## Runtime/Consumer Command Inventory

| Historical command | Historical package owner | Historical purpose | Unified `paa` family | Long-term canonical owner | Migration status |
|---|---|---|---|---|---|
| `install-runtime` | `paa-consumer` | install consumer runtime assets | `paa ops install-runtime` | ops/runtime install layer | completed |
| `update-runtime` | `paa-consumer` | update consumer runtime assets | `paa ops update-runtime` | ops/runtime install layer | completed |
| `install-authority-package` | `paa-consumer` | install published authority package | `paa authority install-package` | authority install layer | completed |
| `smoke-test` | `paa-consumer` | runtime smoke validation | `paa verify runtime-smoke` | verification layer | completed |
| `queue-state-info` | `paa-consumer` | inspect queue runtime state paths | `paa queue state-info` | queue subsystem | completed |
| `queue-ensure-topology` | `paa-consumer` | create/verify queue topology | `paa queue ensure-topology` | queue subsystem | completed |
| `queue-check` | `paa-consumer` | inspect queue contents | `paa queue check` | queue subsystem | completed |
| `queue-validate` | `paa-consumer` | validate one queue message | `paa queue validate` | queue subsystem | completed |
| `queue-send` | `paa-consumer` | send one queue message | `paa queue send` | queue subsystem | completed |
| `queue-claim-next` | `paa-consumer` | claim next queue message | `paa queue claim-next` | queue subsystem | completed |
| `queue-list-claims` | `paa-consumer` | list outstanding claims | `paa queue list-claims` | queue subsystem | completed |
| `queue-ack` | `paa-consumer` | acknowledge claimed message | `paa queue ack` | queue subsystem | completed |
| `queue-requeue` | `paa-consumer` | requeue claimed message | `paa queue requeue` | queue subsystem | completed |
| `automation-preflight` | `paa-consumer` | runtime preflight and environment checks | `paa ops automation-preflight` | ops/runtime guardrails | completed |
| `validate-runtime` | `paa-consumer` | consumer runtime validation | `paa ops validate-runtime` | ops/runtime guardrails | completed |
| `techlead-validate-packet` | `paa-consumer` | validate TechLead packet envelope | `paa queue validate-packet` | queue/packet subsystem | completed |
| `techlead-send-packet` | `paa-consumer` | dispatch TechLead packet | `paa queue send-packet` | queue/packet subsystem | completed |
| `techlead-service-map` | `paa-consumer` | inspect extracted TechLead service map | `paa report techlead-service-map` | reporting / worker diagnostics | completed |
| all `runtime-supervisor*` and `*-runtime` commands | `paa-consumer` | runtime supervisor and host lifecycle control | `paa runtime ...` | runtime host/supervisor layer | completed |
| legacy `techlead-*` shell commands | `paa-consumer` | direct TechLead shell orchestration and legacy worktree flows | no current unified replacement; retired with legacy shell demotion | legacy shell history only | retired |

## Script Surface Inventory

| Current script surface | Current purpose | Target unified `paa` family or canonical replacement | Long-term canonical owner | Migration status |
|---|---|---|---|---|
| `scripts/docs/paa_docs.py` | authority/doc discovery, sync, and creation | `paa authority ...` | authority subsystem | absorb |
| `scripts/docs/lint_governed_docs.sh` | governed doc lint | `paa verify governed-docs` or `paa authority lint` | verification / authority subsystem | absorb |
| `scripts/governance/paa_component_spec_model_consistency.py` | spec/model proof | `paa verify spec-model-consistency` | verification subsystem | absorb |
| `scripts/governance/paa_model_code_consistency.py` | model/code proof | `paa verify model-code-consistency` | verification subsystem | absorb |
| `scripts/governance/paa_projection_code_consistency.py` | projection/code proof | `paa verify projection-code-consistency` | verification subsystem | absorb |
| `scripts/governance/paa_runtime_evidence_model_consistency.py` | runtime-evidence/model proof | `paa verify runtime-evidence-consistency` | verification subsystem | absorb |
| `scripts/runtime/materialize_*` proof scripts | one-off materialization proofs for specific components | `paa derive materialize-component-spec` and governed component loop | derivation subsystem | retire after parity with generic path |
| `scripts/runtime/validate_phase_h*_*.py` fixture validators | phase-specific runtime validation helpers | `paa verify runtime-fixture` or folded unit/integration tests | verification subsystem | classify then migrate |
| `scripts/runtime/run_automation_preflight_with_logging.sh` | runtime preflight wrapper | `paa ops automation-preflight` | ops/runtime guardrails | migrate |
| `scripts/runtime/bootstrap_local_tooling_baseline.sh` | local runtime bootstrap helper | `paa ops bootstrap-local-tooling` | ops subsystem | migrate |
| `scripts/runtime/bootstrap_automation_logging.sh` | automation logging bootstrap | `paa ops bootstrap-automation-logging` | ops subsystem | migrate |
| `scripts/runtime/log_automation_event.py` | write automation log event | internal library or `paa ops log-event` if still operator-facing | ops/runtime diagnostics | classify |
| `scripts/runtime/install_pilot_authority_overlay.py` | pilot authority overlay helper | authority install/overlay command under `paa authority` | authority subsystem | migrate |
| `scripts/runtime/create_team_worker_pilot_fixture.py` | pilot fixture generator | `paa verify create-worker-fixture` or internal test utility | verification/test subsystem | classify |

## Current Design Reading

### What is already strong
- producer derivation surfaces are real and substantial
- consumer queue and TechLead runtime surfaces are real and substantial
- we already have a meaningful split between producer and consumer responsibilities
- the extracted TechLead service set gives the future worker controller a strong core

### What is still missing
- final retirement or rewrite of legacy TechLead shell-only behaviors that no longer have user-facing commands
- explicit migration of remaining script surfaces into stable command families
- a component/module/class inventory showing which script-backed capabilities already have proper modeled owners underneath

## Immediate Follow-On Artifact

The next inventory pass should map:
- components
- modules
- classes
- service contracts
- repositories
- worker/runtime controllers

against the command and script surfaces in this document.

That second pass will show:
1. what functionality already has real modeled ownership
2. what still depends on scripts or oversized hubs
3. what must be added before the unified CLI and worker runtime can be implemented cleanly

## Decision

The unified `paa` CLI is now the user-facing operator surface.

`paa-consumer` remains an internal package boundary for runtime hosts and support modules, not a parallel CLI.
