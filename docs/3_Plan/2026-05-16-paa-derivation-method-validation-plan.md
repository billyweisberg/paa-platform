# PAA Derivation Method Validation Plan

Date: 2026-05-16

## Purpose

Define the phased plan for validating and refining the core PAA derivation process:

- `System Design -> Agent Team -> Functioning Software System`

This plan exists because we are intentionally pausing implementation to verify that the PAA system can actually translate reviewed System Design into executable coder-agent instructions that produce functioning software.

This is not a side concern.
This is the heart of PAA.

## Scope

This plan is focused on validating the derivation path using the current PAA architecture and data model, with the immediate concrete test case of:
- `Component Design Planning Service`

The goal is to verify whether the current design, data model, and tooling are strong enough to derive a correct coder-agent implementation brief for that service.

## Design Authority

Use these design notes as governing authority for this plan:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-coder-brief-derivation-method.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-coder-brief-field-derivation-matrix.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-coder-brief-sequencing.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-coder-run-brief-packet-integration.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-coder-run-brief.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-authority-package-authoring-process.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-layered-architecture-proposal.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-layered-component-dependency-graph.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-domain-object-model-and-oo-component-decomposition.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-component-design-planning-service-component-spec.md`

## Planning Rule

Do not implement the next service yet.

First verify that the derivation system can:
1. consume the current System Design outputs
2. transform them into a well-formed coder-agent brief
3. represent the required process state in the DB model
4. produce execution instructions that are concrete enough for a coder agent to build the service correctly without architectural guessing

Only after that validation passes should service implementation continue.

## Plan Objective

At the end of this plan, we should have a verified and refined derivation method that can answer these questions confidently:

1. how does System Design become a coder-agent brief?
2. what structured records are required to support that translation?
3. which derivation steps are mechanical, reviewed, or enriched?
4. what process state must be represented in the DB to manage the derivation lifecycle?
5. what architecture and tooling support is still missing?
6. can the current PAA system derive a valid implementation brief for `Component Design Planning Service`?

## Success Criteria

This plan is successful when:
- the derivation steps are explicit and internally consistent
- the existing derivation docs are refined where needed
- the current DB/data model is verified against the derivation lifecycle and gaps are recorded explicitly
- the layered architecture is validated against the derivation path
- the current producer-side tooling model is validated against the derivation path
- a concrete derived brief outline or target brief package for `Component Design Planning Service` can be produced from current design artifacts
- remaining blockers are concrete and actionable rather than conceptual

## Phased Execution

## Phase 1. Reconstruct And Normalize The Derivation Pipeline

### Goal
Make the end-to-end derivation pipeline explicit using the existing derivation notes as the baseline.

### Questions
- What exact stages exist between System Design and coder execution?
- Which steps are authored, inferred, validated, or enriched?
- Are the existing derivation docs complete and internally consistent as a pipeline?

### Work
- review and normalize the derivation flow across:
  - `coder-brief-derivation-method`
  - `coder-brief-field-derivation-matrix`
  - `coder-brief-sequencing`
  - `coder-run-brief-packet-integration`
  - `coder-run-brief`
- produce a consolidated derivation-pipeline view if needed
- identify ambiguities, overlaps, or missing transitions between stages

### Outputs
- derivation-pipeline validation note
- proposed updates to derivation docs if needed

### Exit criteria
- one coherent derivation pipeline can be stated end to end
- each existing derivation note has a clear role in that pipeline

## Phase 2. Map Current System Design Outputs To Derivation Inputs

### Goal
Verify that the current System Design artifacts actually produce the inputs required by the derivation method.

### Questions
- Do our current System Design outputs provide the information the brief derivation method expects?
- Which derivation inputs are already modeled?
- Which are still implicit or missing?

### Work
- use `Component Design Planning Service` as the concrete test case
- map from current design artifacts to required derivation inputs, including:
  - layered architecture placement
  - dependency graph placement
  - component role
  - collaborators
  - code artifact targets
  - sequencing context
  - architecture constraints
- identify any missing or under-specified source records

### Outputs
- derivation-input coverage note for `Component Design Planning Service`
- list of missing or weakly-modeled derivation inputs

### Exit criteria
- all required derivation inputs are either mapped or explicitly marked missing

## Phase 3. Validate The Data Model Against Derivation State

### Goal
Verify that the current DB/data model can represent the derivation process state needed by the method.

### Questions
- Do we have the records needed to manage derivation state explicitly?
- Can we represent authored, inferred, validated, and enriched states where needed?
- Can we manage brief sequencing, target dependencies, and signoff state correctly?

### Work
- review current DB support for:
  - `design_packages`
  - `design_package_signoffs`
  - `coder_run_briefs`
  - `coder_brief_sequence_states`
  - `component_element_types`
  - `component_elements`
  - `component_element_realization_types`
  - `component_element_realizations`
  - `coder_brief_realization_targets`
  - dependency edges and readiness state
- compare actual DB entities to the derivation process expectations
- identify missing process-state entities or missing fields/constraints

### Outputs
- derivation-state data-model validation note
- explicit DB/data-model gap list for derivation management

### Exit criteria
- we can state whether the DB model is complete enough for derivation-state management
- all known derivation-state gaps are recorded explicitly

## Phase 4. Validate Architecture And Layering Against The Derivation Process

### Goal
Verify that the layered architecture and component decomposition support the derivation path instead of obstructing it.

### Questions
- Are the right responsibilities in the right layers for derivation?
- Do producer-side services have a clear architectural home?
- Are we missing authoring-side components or service boundaries?

### Work
- check the derivation pipeline against the layered architecture
- verify that producer-side authoring services can exist cleanly in the current model
- verify that the current component decomposition supports:
  - component catalog authoring
  - element authoring
  - code artifact target authoring
  - brief-target sequencing
  - policy selection
  - deployment annotation
- identify any needed architecture refinements

### Outputs
- architecture-vs-derivation validation note
- proposed architecture refinements if needed

### Exit criteria
- derivation has a clean architectural home in the layered system
- missing producer-side service families are identified explicitly if present

## Phase 5. Validate The Tooling Model Against Real Producer-Side Use

### Goal
Verify whether the current and planned producer-side tooling model can support the derivation process in reality.

### Questions
- Which parts of derivation are currently toolable?
- Which parts are still manual?
- Which future producer-side tools/services are required to make this process operational?

### Work
- compare the derivation pipeline to current producer/runtime tooling surfaces
- assess whether current repository contracts and scaffolding support producer-side authoring tools
- identify the minimum tool/service set needed to make derivation operational, not theoretical

### Outputs
- producer-tooling validation note
- prioritized tooling/service gap list

### Exit criteria
- we can clearly distinguish what is already supported, what is partially supported, and what is missing

## Phase 6. Perform A Concrete Derivation Dry Run

### Goal
Use `Component Design Planning Service` as the first dry-run derivation target and walk from System Design to coder-agent instructions.

### Questions
- Can we derive a coherent coder-run brief or equivalent brief-target package for this component?
- Where does the process succeed cleanly?
- Where does it still require guesswork?

### Work
- perform a dry-run derivation for `Component Design Planning Service`
- derive:
  - component assignment
  - architecture constraints
  - collaboration context
  - dependency contract
  - behavioral contract
  - test contract
  - execution prerequisites
  - change budget
  - anti-goals
  - code artifact target sequencing
- identify any points where the derivation must guess or improvise

### Outputs
- dry-run derivation validation note
- candidate brief outline or draft package for `Component Design Planning Service`
- final list of refinements needed before implementation resumes

### Exit criteria
- we can either derive a credible implementation brief, or we know exactly why not

## Phase 7. Refine The Method And Process Record

### Goal
Feed the learning from all previous phases back into the reusable PAA process and derivation method.

### Questions
- What process steps need to be refined?
- What sequencing rules need to be strengthened?
- What new artifacts or checks should become standard?

### Work
- update:
  - derivation method docs as needed
  - process tracking doc as needed
  - architecture or data-model notes as needed
- explicitly record lessons learned from this validation cycle

### Outputs
- refined derivation/process docs
- final validation summary
- readiness decision for whether implementation may resume

### Exit criteria
- the derivation method is stronger than when this plan started
- the process doc reflects the refined authority-authoring method
- we have a clear go/no-go decision for implementation resumption

## Iteration Rule

Each phase should produce:
- one durable note
- one explicit gap list or validation result
- one recommendation for the next phase

This keeps the work iterative and reviewable instead of turning it into one large opaque pass.

## Important Validation Rule

This plan is not only asking:
- “can we write a brief?”

It is asking:
- “does our architecture, data model, and tooling actually support the derivation process we claim PAA is built to perform?”

That is the deeper validation target.

## Expected Outcome

If this plan succeeds, we will have much higher confidence that:
- PAA can really translate System Design into coder-agent execution authority
- the producer-side process is becoming explicit and toolable
- the architecture and data model are aligned to the core mission of PAA

And if the plan fails, it should fail usefully by revealing exactly what is still missing.
