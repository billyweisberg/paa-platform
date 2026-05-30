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

## 10. Use Thin Slices

Do not implement a large component in one pass.

Preferred first slices are:
1. interface contract
2. DTO models
3. default implementation
4. validation surface

## 11. Keep Authority, Model, And Runtime Separate

Always distinguish:
- source/domain authority
- PAA operational authority
- runtime execution state

Runtime state must not replace published authority.

## 12. Fail Closed

If the next required artifact is missing:
1. stop
2. identify what is missing
3. create or propose that artifact
4. continue through the methodology

Do not silently work around the process.

## 13. Use The Existing PAA Tools

Common commands:

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

## 14. The Current Proven Loop

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
