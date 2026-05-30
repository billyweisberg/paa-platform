# PAA Methodology For Software Engineering

This README is the working guide to the PAA methodology.

It is meant to evolve into the final operator guide for using the PAA system for real software engineering.
As the unified `paa` CLI is built, this guide should absorb the actual commands and operator workflows.

For now, it records the current manual, governed process.

## 1. Start With Authority

Before writing code, identify the current authority.

Check, in order:
1. `docs/1_Vision/current/`
2. `docs/2_Design/current/`
3. `docs/3_Plan/current/`
4. `docs/4_Build/current/`

Ask:
- what is already decided?
- what lifecycle stage are we in?
- what is the next valid artifact?
- what authority is missing and must be authored before implementation continues?

## 2. Follow The Lifecycle

PAA work moves through these stages:

1. `1_Vision`
2. `2_Design`
3. `3_Plan`
4. `4_Build`
5. `5_Test`
6. `6_Deploy`
7. `7_Monitor`

Do not skip ahead without reason.

## 3. The Core Producer-Side Rule

Authority authoring is not just writing docs.
It is a structured derivation process.

The current governing process is documented in:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-authority-package-authoring-process.md`

That process says the Authority Architect should work in this order:

1. clarify desired system outcome behavior
2. brainstorm system decomposition options
3. model core domain objects and ownership
4. analyze volatility and expected change
5. analyze deployment variants and swappable boundaries
6. select a preferred layered architecture
7. define stable components and relationships
8. define data model and primary-truth boundaries
9. define repository and infrastructure port boundaries
10. derive the component dependency graph and dependency strata
11. scaffold solution and project structure from the dependency strata
12. define component elements and code artifact target taxonomy
13. define component specs
14. materialize the active slice design package and derivation readiness state
15. derive draft coder-agent brief inputs
16. review and approve execution authority
17. publish or packetize the approved execution authority

This is the process.
Do not silently compress it into "write a component spec and start coding."

## 4. Stage 1 Design Package Comes Before Derivation

The governing docs for the Stage 1 package are:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-stage1-design-package-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-stage1-schema-and-record-shape.md`

Stage 1 must produce one coherent design package for a slice.

At minimum, that package must make explicit:
1. authority context
2. product and source basis
3. requirement set
4. design decision set
5. spec fragment
6. implementation target
7. architectural authority constraints
8. component model slice
9. component surfaces
10. component relationships, collaboration pattern, and dependency graph slice
11. verification contract basis

Important rule:
- if this package is incomplete, Stage 2 derivation is not ready

## 5. The Dependency Graph Is A Gate, Not Decoration

The governing dependency-graph doc is:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-component-dependency-graph-contract.md`

The dependency graph is a first-class Stage 1 design artifact.
It is not optional documentation.

It must answer:
- what depends on what
- what kind of dependency it is
- what must be designed first
- what may parallelize
- what is blocked at design, derivation, execution, or verification time

For any significant new system area, Stage 1 should produce a local dependency-graph slice with:
- nodes
- edges
- blocking dependencies
- parallelizable dependencies
- sequencing constraints
- contract-before-implementation decisions

If this is missing, do not pretend the slice is derivation-ready.

## 6. Diagrams And Tables Are Both Required

The governing methodology docs are:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-18-paa-system-design-tables-method.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-18-paa-strict-process-record-table.md`

Use both:
- diagrams for structural shape and runtime flow
- tables for governance, ownership, sequencing, and gap detection

Typical required outputs during system design include:
- node diagrams
- object models
- collaboration and dependency tables
- business-object ownership tables
- remediation or extraction sequencing tables

## 7. Do Not Jump Straight To A Component Spec

A component spec is not the first design artifact.
The governing bridge doc is:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/current/policy/component-spec-template-materialization-bridge.md`

The placement is:
1. system design
2. component design
3. component spec
4. model materialization
5. execution authority

That means a new component spec should usually come after the relevant upstream design artifacts exist, such as:
- node diagram
- object model
- component relationships and dependency graph slice
- component surfaces
- injected-service and collaborator structure
- business-object ownership map
- code artifact target taxonomy

If those are still missing, stop and author them first.

## 8. For A New System Area

Use this order:
1. define or update the vision
2. derive the system-design package
3. derive the component-design package
4. define or revise governed component specs
5. derive the implementation plan
6. implement through governed build slices
7. test and verify
8. deploy and operate

## 9. For A New PAA Component

Treat it as a governed component.

Only do this after the upstream system-design artifacts are sufficient.

Then use this order:
1. create or update the component spec in `docs/2_Design/`
2. materialize the component spec into model truth
3. reconcile implementation-plan progress
4. derive the next activity bundle
5. implement one thin slice
6. verify the slice
7. mark the activity complete
8. rerun reconcile and next
9. repeat until the component is `fully_realized`
10. wire the component into the runtime shell, worker controller, or CLI adapter

## 10. Derivation Is Two Related Pipelines

In practice, we use the word `derivation` for two different but connected flows.

### A. Producer-side authority derivation

This is the upstream flow that turns approved design authority into executable producer-side records and artifacts.

Current governing runbooks:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/4_Build/current/flows/derive-design-package-flow.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/4_Build/current/flows/evaluate-derivation-readiness-flow.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/4_Build/current/flows/derive-implementation-plan-flow.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/4_Build/current/flows/assemble-coder-brief-flow.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/4_Build/current/flows/author-brief-targets-flow.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/4_Build/current/flows/review-coder-brief-flow.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/4_Build/current/flows/prepare-architect-packet-flow.md`

The canonical order is:
1. `derive-design-package`
2. `evaluate-derivation-readiness`
3. `derive-implementation-plan`
4. `assemble-coder-brief`
5. `author-brief-targets`
6. `review-coder-brief`
7. `prepare-architect-packet`

Important rule:
- do not skip the derivation-readiness gate
- do not assemble briefs or packets from incomplete or unapproved design-package truth

### B. Code-backed component realization derivation

This is the downstream flow we used for the TechLead service family and are now using for `PAAOperatorCLI`.

Current governing docs:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/current/policy/component-spec-doc-to-materialization-extraction-rules.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/current/policy/governed-code-backed-component-materialization-policy.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/current/policy/component-slice-successor-derivation-policy.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/4_Build/current/flows/materialize-governed-code-backed-components-flow.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/4_Build/current/flows/component-realization-loop.md`

The canonical order is:
1. `materialize-component-spec`
2. `reconcile-implementation-plan-progress`
3. `derive-next-activity-bundle`
4. implement one thin slice
5. verify
6. mark complete
7. repeat until `completed_plan` and `fully_realized`

Important rule:
- do not confuse component-spec materialization with Stage 1 design-package derivation
- the first is for governed code-backed component realization
- the second is for producer-side authority progression

### Current derivation-authority audit

The latest derivation authority we should actively rely on is:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-paa-producer-derivation-subsystem.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-paa-derivation-pipeline-validation.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-16-paa-derivation-method-validation-plan.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/4_Build/current/flows/derive-design-package-flow.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/4_Build/current/flows/evaluate-derivation-readiness-flow.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/4_Build/current/flows/derive-implementation-plan-flow.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/4_Build/current/flows/assemble-coder-brief-flow.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/4_Build/current/flows/author-brief-targets-flow.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/4_Build/current/flows/review-coder-brief-flow.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/4_Build/current/flows/prepare-architect-packet-flow.md`

Current audit conclusion:
- the producer-side derivation path is real and governed
- the code-backed component realization path is also real and governed
- they are connected, but they are not the same loop
- operator guidance should name which derivation lane is active before any command is run

### Current materialization vocabulary guardrail

For active component-spec materialization, the current extractor/materializer contract is intentionally narrow.

Before running `materialize-component-spec`, verify that the spec uses the active canonical values documented in:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/current/policy/component-spec-doc-to-materialization-extraction-rules.md`

The most common failure pattern is not bad architecture.
It is using a reasonable but non-canonical table value such as:
- a custom `element_kind`
- a generic `plan_status` like `planned`
- a scheduling-style `dependency_kind` like `finish-to-start`

If that happens, do not add ad hoc aliases casually.
First decide whether:
1. the existing canonical vocabulary is still correct and the spec should be normalized, or
2. the canonical vocabulary is genuinely missing a needed distinction and should evolve intentionally across docs, tooling, and model truth

## 11. Use Thin Slices

Do not implement a large component in one pass.

Preferred first slices are:
1. interface contract
2. DTO models
3. default implementation
4. validation surface

## 12. Keep Authority, Model, And Runtime Separate

Always distinguish:
- source/domain authority
- PAA operational authority
- runtime execution state

Runtime state must not replace published authority.

## 13. Fail Closed

If the next required artifact is missing:
1. stop
2. identify what is missing
3. create or propose that artifact
4. continue through the methodology

Do not silently work around the process.

## 14. Use The Existing PAA Tools

Common commands:

### Derive a Stage 1 design package
```bash
PYTHONPATH=packages/paa-core/src:packages/paa-producer/src:. python -m paa_producer derive-design-package --design-package docs/2_Design/<stage1-package>.json
```

### Evaluate derivation readiness
```bash
PYTHONPATH=packages/paa-core/src:packages/paa-producer/src:. python -m paa_producer evaluate-derivation-readiness --design-package docs/2_Design/<stage1-package>.json
```

### Derive an implementation plan from a Stage 1 package
```bash
PYTHONPATH=packages/paa-core/src:packages/paa-producer/src:. python -m paa_producer derive-implementation-plan --design-package docs/2_Design/<stage1-package>.json
```

### Assemble a coder brief
```bash
PYTHONPATH=packages/paa-core/src:packages/paa-producer/src:. python -m paa_producer assemble-coder-brief --design-package docs/2_Design/<stage1-package>.json
```

### Materialize a component spec
```bash
PYTHONPATH=packages/paa-core/src:packages/paa-producer/src:. python -m paa_producer materialize-component-spec --spec docs/2_Design/<component-spec>.md
```

### Show plan progress
```bash
PYTHONPATH=packages/paa-core/src:packages/paa-producer/src:. python -m paa_producer implementation-plan-progress --plan-id <implementation-plan-id>
```

### Reconcile progress
```bash
PYTHONPATH=packages/paa-core/src:packages/paa-producer/src:. python -m paa_producer reconcile-implementation-plan-progress --plan-id <implementation-plan-id>
```

### Derive the next activity bundle
```bash
PYTHONPATH=packages/paa-core/src:packages/paa-producer/src:. python -m paa_producer derive-next-activity-bundle --plan-id <implementation-plan-id>
```

### Sync current authority
```bash
python scripts/docs/paa_docs.py sync-current --root /Users/billyweisberg/Repos/billyweisberg/paa-platform
```

### Lint governed docs
```bash
bash scripts/docs/lint_governed_docs.sh
```

## 15. The Current Proven Loops

The proven producer-side derivation path is documented through:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/4_Build/current/flows/derive-design-package-flow.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/4_Build/current/flows/evaluate-derivation-readiness-flow.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/4_Build/current/flows/derive-implementation-plan-flow.md`

The proven component realization loop is documented here:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/4_Build/current/overview/component-realization-loop.md`

That loop is the current standard path for building governed components.

## 15. Current Strategic Direction

PAA is moving toward:
- one real operator CLI
- TechLead as the deterministic controller
- Dev and QA as bounded agent-host worker programs
- authority-first automated software engineering
- agent-oriented execution under deterministic PAA control

That means:
- do not invent a parallel control plane
- do not bypass authority
- do not confuse worker runtime with authority truth
- build from the documented methodology outward

## 16. Current Practical Reminder

When designing a major new system area such as `PAAOperatorCLI`, do not skip the Authority Architect system-design package.

Before treating the area as component-realization-ready, make the following explicit:
1. node diagram
2. object model
3. component relationships and dependency graph slice
4. component surfaces
5. service injection and collaboration map
6. business-object ownership map
7. architectural constraints
8. code artifact target taxonomy

Only after that should the component spec become the primary bridge into materialization.

## 17. This Guide Will Expand

As the unified `paa` CLI is implemented, this README should absorb:
- actual `paa` commands
- authority-authoring workflows
- derivation workflows
- planning workflows
- worker and queue workflows
- verification and acceptance workflows
- operator troubleshooting steps

The goal is a final guide that shows how to use the PAA system end to end for real software engineering.
