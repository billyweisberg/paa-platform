# PAA Methodology For Software Engineering

This is the simple working outline of the PAA methodology.

Use it when deciding what to do next.

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

## 3. For A New System Area

Use this order:
1. define or update the vision
2. derive the technical design
3. derive the implementation plan
4. implement through governed build slices
5. test and verify
6. deploy and operate

## 4. For A New PAA Component

Treat it as a governed component.

Use this order:
1. create or update the component spec in `docs/2_Design/`
2. materialize the component spec into model truth
3. reconcile implementation-plan progress
4. derive the next activity bundle
5. implement one thin slice
6. verify the slice
7. mark the activity complete
8. rerun reconcile and next
9. repeat until the component is `fully_realized`
10. wire the component into the runtime shell or CLI adapter

## 5. Use Thin Slices

Do not implement a large component in one pass.

Preferred first slices are:
1. interface contract
2. DTO models
3. default implementation
4. validation surface

## 6. Keep Authority, Model, And Runtime Separate

Always distinguish:
- source/domain authority
- PAA operational authority
- runtime execution state

Runtime state must not replace published authority.

## 7. Fail Closed

If the next required artifact is missing:
1. stop
2. identify what is missing
3. create or propose that artifact
4. continue through the methodology

Do not silently work around the process.

## 8. Use The Existing PAA Tools

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

### Lint governed docs
```bash
bash scripts/docs/lint_governed_docs.sh
```

## 9. The Current Proven Loop

The proven component realization loop is documented here:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/4_Build/current/overview/component-realization-loop.md`

That loop is the current standard path for building governed components.

## 10. Current Strategic Direction

PAA is moving toward:
- one real operator CLI
- TechLead as the deterministic controller
- Dev and QA as bounded agent-host worker programs
- authority-first automated software engineering

That means:
- do not invent a parallel control plane
- do not bypass authority
- build from the documented methodology outward
