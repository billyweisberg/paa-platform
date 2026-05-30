# PAA Platform Agent Notes

## Build Rules

PAA is a Python application.
Do not build it as a growing collection of scripts.

The implementation order is:
1. define the component or module boundary
2. define the interface and contract
3. define the classes that own the behavior
4. implement the behavior in application and domain modules
5. expose that behavior through a CLI adapter
6. retire or reduce any earlier proof-of-concept script

## PAA Methodology Rule

PAA work must follow the PAA methodology and lifecycle by default.

Do not skip directly to code implementation when the task is really in:
- `1_Vision`
- `2_Design`
- `3_Plan`
- or a governed `4_Build` realization step

Before implementing a new major capability, component, worker, CLI subsystem, or runtime controller, identify where the work currently sits in the lifecycle:
1. `1_Vision`
2. `2_Design`
3. `3_Plan`
4. `4_Build`
5. `5_Test`
6. `6_Deploy`
7. `7_Monitor`

Then follow the next valid authority step instead of inventing an ad hoc path.

### Default lifecycle expectations

For a new system area:
1. check whether the vision already exists
2. if not, create or update the `1_Vision` authority first
3. derive the required `2_Design` artifact from that vision
4. derive the required `3_Plan` implementation sequence from the design
5. only then begin `4_Build` implementation work

For a new PAA component:
1. treat it as a governed component
2. create or update its component spec under `docs/2_Design/`
3. materialize it through the producer materialization path
4. reconcile progress
5. derive the next activity bundle
6. implement one thin slice
7. verify it
8. mark the activity complete
9. repeat until `fully_realized`

### Required component-realization path

When implementing a new governed component such as a service, repository, worker controller, or CLI subsystem, use the documented component realization loop:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/4_Build/2026-05-27-component-realization-loop.md`

This is the default process for:
- component specs
- materialization
- plan progress
- successor-slice derivation
- iterative thin-slice realization

Do not bypass this loop by jumping straight from idea to code unless the user explicitly asks for a throwaway prototype.

### Required authority sources before acting

Before starting major work, inspect the smallest relevant current authority set first.

Minimum expected checks:
- `docs/1_Vision/current/`
- `docs/2_Design/current/`
- `docs/3_Plan/current/`
- `docs/4_Build/current/`

When the task is about the full PAA operator system, also inspect:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/1_Vision/current/overview/paa-authority-stack-and-operator-architecture.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/1_Vision/current/overview/paa-cli-system-architecture.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/1_Vision/current/overview/paa-worker-runtime-architecture.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/1_Vision/current/overview/paa-operator-system-implementation-plan.md`

When the task is about creating a new component such as `TechLeadWorkerService`, default to:
1. determine whether the next valid step is `2_Design`
2. author the component spec
3. only then move into materialization and implementation

### Fail-closed methodology rule

If the next authority artifact is missing, do not silently skip the methodology.

Instead:
1. state which lifecycle artifact is missing
2. create or propose that artifact
3. continue from the methodology, not around it

### Application-First Rule

Treat current repo-local scripts as:
- proof-of-concept functions
- temporary behavior references
- migration sources
- transitional wrappers only

Do **not** treat scripts as the long-term system implementation.
Do **not** build new capabilities by accumulating more one-off scripts and wrapping them later.

### CLI Rule

A real CLI in this repo means a stable operator command surface, similar in shape to:
- `git`
- `gh`
- `aws`
- `kubectl`
- `az`

That means:
- one named command surface
- coherent subcommands
- stable flags
- discoverable command grammar
- intended for repeated human and automation use

The CLI is an adapter over system components.
The CLI is **not** the primary implementation.

Preferred CLI stack for PAA:
- `Typer` for command definition and command tree structure
- `typer-di` for dependency injection into CLI commands

Build the CLI as a thin adapter over application services and domain modules.
Do not place core business logic directly inside Typer command functions.

### Object Model Rule

New behavior should be implemented as modules and classes with explicit responsibilities.
Preferred structure:
- domain objects
- application services
- repositories
- policies
- packet/result models
- infrastructure adapters
- CLI adapters

Avoid:
- large files of loose functions
- 5000-line orchestration hubs
- script-local business logic that is not represented in application modules
- hidden workflow behavior embedded only in CLI parsing or shell glue

### Packet And Workflow Rule

Roles, lanes, packets, proofs, and state transitions belong in the application model.
They should be represented as:
- typed models
- service classes
- policy classes
- deterministic transition logic

Do not leave core workflow behavior trapped in:
- shell scripts
- one-off JSON files
- undocumented ad hoc runtime glue

### TechLead Rule

`TechLead` is primarily a runtime-governor service, not the main code-writing executor.
Its core behavior should become deterministic application logic for:
- state transition
- route legality
- assignment gating
- branch/reset policy
- acceptance readiness
- packet/result interpretation

If LLM assistance exists, it should be bounded and secondary.
It should not replace deterministic routing and gating logic.

### Worker Lane Rule

Code is written in worker lanes.
Examples:
- `Python Dev`
- future implementation-worker lanes

A worker lane may be executed by:
- a human
- a coding agent
- a hybrid pair

The governance layer should not depend on one executor type.
It should govern the lane contract, required authority, and required proof.

### Delivery Architect Rule

`Delivery Architect` should prepare, narrow, conform, and prove authority.
For the component-spec materialization proof lane, build:
- application services
- packet models
- proof models
- result compilers

Do not stop at a runnable script.
The script is only acceptable as a transitional adapter over application code.

### Migration Rule

When a capability already exists as a script proof of concept:
1. preserve it as behavioral reference
2. extract the reusable logic into application modules and classes
3. make the CLI call the application layer
4. keep the script only as a thin compatibility wrapper if still needed
5. remove the script when the application path is proven

### Fail-Closed Rule

If a new capability cannot yet be implemented in application/module form, stop and record the blocker.
Do not silently accept a script-first shortcut as the final architecture.

## Doc Workflow

Use header-first document discovery before reading full document bodies.

Repo-local doc tools:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/paa_docs.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/lint_governed_docs.sh`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/.codex/skills/paa-docs-header-first/SKILL.md`

Preferred workflow:
1. run `current`, `find`, `show`, or `related` against doc headers
2. identify the smallest relevant canonical doc set
3. only then read the full body of the top relevant docs

Do not bulk-read design/planning docs when header-first lookup can narrow the target set.

If the task involves architecture descriptions, status summaries, naming a new service or component, or explaining implementation state, check the reference-stage terminology governance docs first with:
```bash
make -C /Users/billyweisberg/Repos/billyweisberg/paa-platform docs-current-reference
```

Use those docs to avoid:
- loose narrative claims
- broad status descriptions without scope
- naming hybrid runtime hubs as clean components
- overstating alignment or completeness

When changing governed docs or writing architecture/status summaries, also run:
```bash
make -C /Users/billyweisberg/Repos/billyweisberg/paa-platform docs-lint-language
```

When a governed doc is intended to bind directly to code truth, set:
- `Authority-Source: code`

Then verify the `Component:` header resolves to exported governed metadata with:
```bash
make -C /Users/billyweisberg/Repos/billyweisberg/paa-platform docs-lint-code
```

If the task is about producer implementation flow or operator execution flow, check the governed build-stage docs first with:
```bash
python /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/paa_docs.py current \
  --root /Users/billyweisberg/Repos/billyweisberg/paa-platform \
  --stage build
```

Convenience targets:
```bash
make -C /Users/billyweisberg/Repos/billyweisberg/paa-platform docs-current-design
make -C /Users/billyweisberg/Repos/billyweisberg/paa-platform docs-current-plan
make -C /Users/billyweisberg/Repos/billyweisberg/paa-platform docs-current-build
make -C /Users/billyweisberg/Repos/billyweisberg/paa-platform docs-current-test
make -C /Users/billyweisberg/Repos/billyweisberg/paa-platform docs-current-deploy
make -C /Users/billyweisberg/Repos/billyweisberg/paa-platform docs-current-operate
make -C /Users/billyweisberg/Repos/billyweisberg/paa-platform docs-current-reference
make -C /Users/billyweisberg/Repos/billyweisberg/paa-platform docs-lint-governed
make -C /Users/billyweisberg/Repos/billyweisberg/paa-platform docs-lint-language
make -C /Users/billyweisberg/Repos/billyweisberg/paa-platform docs-lint-code
```

## Governed Docs

The current governed-doc set is enforced through:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/lint_governed_docs.sh`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/.pre-commit-config.yaml`

Use:
```bash
bash /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/lint_governed_docs.sh
```

before changing governed docs.

## Component Spec Materialization Proof

When the task is to turn a governed component authority doc into a materialization-ready bridge and prove downstream model reconciliation, use:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/.codex/skills/paa-component-spec-materialization-proof/SKILL.md`

This workflow expects both proofs to pass:
```bash
cd /Users/billyweisberg/Repos/billyweisberg/paa-platform && PYTHONPATH=packages/paa-core/src python scripts/governance/paa_model_code_consistency.py --component <ComponentName>
cd /Users/billyweisberg/Repos/billyweisberg/paa-platform && PYTHONPATH=packages/paa-core/src python scripts/governance/paa_component_spec_model_consistency.py --spec <spec-path>
```

## New Docs

When creating a new governed markdown doc, prefer:
- `new-doc`
- `set-header`

instead of hand-writing or manually editing the header.

Example:
```bash
python /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/paa_docs.py new-doc \
  --root /Users/billyweisberg/Repos/billyweisberg/paa-platform \
  --path /Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-18-example.md \
  --doc-type design-note \
  --status draft \
  --summary "Creates a new governed design note."
```
