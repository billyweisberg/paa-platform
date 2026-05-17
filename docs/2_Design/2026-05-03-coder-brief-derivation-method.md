# 80. Coder Brief Derivation Method

## Purpose
This document defines the repeatable method for deriving a `coder_run_brief` from upstream project authority.

It is the bridge between:
- Stage 1: Design / Authoring
- Stage 2: Project Design / Implementation-Plan Derivation
- Stage 3: Coder Brief Derivation

The goal is to make coder-facing implementation packets:
- deliberate
- reviewable
- reproducible
- tool-supported
- portable across projects in this portfolio

## Core principle
A coder agent should not derive system design.

A coder agent should receive a prepared construction brief that is itself derived from reviewed upstream design authority.

A coder agent should also not be forced to invent the implementation plan that sits between an approved component spec and a concrete coding run.

That means `coder_run_brief` is not handwritten from scratch, and it is not guessed from issue text.
It is derived from a staged design model plus an implementation-plan derivation step.

## Upstream inputs
A `coder_run_brief` is derived from six primary sources:
- Product / Architect / Designer authority
- spec fragments
- implementation targets
- component model
- component element and code-artifact target model
- implementation plan

These are not equal peers. They play different roles in derivation.

### 1. Product / Architect / Designer authority
This is the system-intent layer.
It defines:
- why the slice exists
- what outcome is wanted
- what must remain protected
- what architectural direction is intended
- what adjacent work is explicitly out of scope

### 2. Spec fragments
This is the slice-boundary layer.
It defines:
- the exact bounded change being authorized
- the canonical statement of the slice
- the protected baseline and semantic envelope

### 3. Implementation targets
This is the implementation-shaping layer.
It defines:
- current gap
- desired state
- expected touch surfaces
- pre-handoff scope checks
- change budget and practical execution limits

### 4. Component model
This is the construction-structure layer.
It defines:
- which components exist
- where they sit architecturally
- how they collaborate
- which surfaces belong to which components
- what seams must remain intact

### 5. Component element and code-artifact target model
This is the coder-assignment layer.
It defines:
- which component elements are in scope
- which concrete code artifact forms are valid for those elements
- which target kinds are brief-targetable
- whether the target taxonomy can express the intended implementation run cleanly

### 6. Implementation plan
This is the consumer-specific construction-planning layer.
It defines:
- the concrete code-artifact set for the target stack
- the file/module touch plan
- the dependency-aware build sequence for the slice
- the proving and verification plan
- the stack-specific execution particulars that should not be improvised by the coder agent

Important rule:
The same upstream authority package may yield different implementation plans for:
- Python
- .NET
- other consumer stacks

So coder briefing must not skip this layer.

## Design decision
The `coder_run_brief` should be assembled from authored upstream records using a deterministic derivation pass.

It should not depend on a coder agent interpreting freeform architecture prose at runtime.

## Derivation model
Each `coder_run_brief` field must be classified as one of:
- `authored`
- `inferred`
- `validated`
- `enriched`

### Authored
A human design authority directly sets the value.
Typical owners:
- Product Owner
- Architect
- Project Designer

### Inferred
The value is mechanically derived from existing structured records.
Typical source:
- component graph
- surface mappings
- authority task metadata

### Validated
The value is derived or drafted, then explicitly reviewed for correctness before the brief is approved.

### Enriched
The value is not core authority, but helpful operational context added by TechLead or tooling.
It must never override authored authority.

## Derivation lifecycle states
Derivation should distinguish three authority states clearly:
- `draft_brief`
- `approved_brief`
- `packet_ready_execution_authority`

Rule:
A dry-run or draft brief can prove that the method is working.
It must not be treated as execution authority until:
- the slice package is materialized
- target taxonomy coverage is complete for the run
- review and approval are complete
- packet-readiness is confirmed

## Stage 1 output package
Before Stage 2 derivation begins, Stage 1 must produce a complete design package for the slice.

## Required Stage 1 artifacts
- source artifacts
- source statements
- requirements
- design decisions
- spec fragment
- implementation target
- authority task definition
- component model entries
- component surface mappings
- component relationships
- architectural authority constraints

## Minimum Stage 1 architectural constraints
These are required before coder derivation:
- `required_architecture_seams`
- `target_module_boundaries`
- `max_responsibility_expansion`
- `forbidden_module_growth_patterns`
- `authorized_delta_family`
- `out_of_scope_delta_families`
- `expected_touch_surfaces`
- `pre_handoff_scope_checks`

If any of these are missing, the slice is not ready for coder derivation.

## Stage 2 derivation process
The derivation process should run as a staged pipeline.

### Step 0: Confirm reviewed upstream authority
Input:
- reviewed System Design authority
- reviewed component decomposition
- reviewed component spec or equivalent

Output:
- approved upstream authority baseline for derivation

Rule:
Derivation should not begin from speculative or half-reviewed component design.

### Step 1: Resolve and materialize active slice package
Input:
- authority version
- task id
- work item

Output:
- active slice package

The active slice package is the bundle containing:
- task definition
- spec fragment
- implementation target
- linked design decisions
- linked component entries

Rule:
A note bundle may be enough for a dry run.
A normal execution-authoritative derivation should begin from a materialized slice package.

### Step 2: Derive implementation plan
Input:
- active slice package
- approved component spec
- implementation target
- consumer execution context
- language / stack specifics

Output:
- implementation plan
- stack-specific code-artifact plan
- file/module touch plan
- proving and verification plan

Rule:
This is the `Project Design` bridge.
Coder briefing should not proceed until the implementation plan exists, even if the component spec is already approved.

### Step 3: Confirm derivation readiness
Input:
- active slice package
- implementation plan
- signoff state
- dependency graph slice
- package status

Output:
- derivation-ready or blocked slice
- explicit blocking reasons if not ready

Rule:
If the slice package is not approved for derivation, the process should stop before drafting a brief.

### Step 4: Resolve top-level identity and authority context
Input:
- project identity
- authority version
- milestone / phase / task binding
- work item identity
- issue or PR context if already materialized

Output:
- top-level brief identity
- authority context
- slice scope identity

Rule:
Component identity alone is not enough.
Derivation requires slice identity.

### Step 5: Resolve primary component assignment
Input:
- spec fragment
- implementation target
- component model

Output:
- primary component
- supporting components
- component role
- system layer
- optional tier

Rule:
Every coder brief must have exactly one primary implementation component, even if multiple supporting components participate.

### Step 6: Resolve component aspects
Input:
- implementation target desired state
- expected touch surfaces
- component surfaces

Output:
- component aspects in scope

Examples:
- state
- interface
- functions
- configuration
- events
- hosting
- tests
- docs

Rule:
Component aspects must be explicit. The coder should not infer whether they are changing state, interface, tests, or documentation by reading the codebase blindly.

### Step 7: Resolve placement and edit boundaries
Input:
- component surfaces
- target module boundaries
- required architecture seams
- forbidden growth patterns

Output:
- target modules
- allowed edit surfaces
- forbidden edit surfaces
- target module boundaries
- required seams

Rule:
This is where we prevent god-file growth. If module placement is not explicit here, the brief is under-specified.

### Step 8: Resolve collaboration context
Input:
- component relationships
- sequence/activity diagrams
- pattern definitions

Output:
- collaboration pattern
- collaborating components
- callers
- callees
- emitters / consumers as applicable

Rule:
A coder brief should describe the local construction pattern, not the whole system.

### Step 9: Resolve dependency contract
Input:
- component relationships
- constructor/setup model
- configuration contracts

Output:
- dependencies to inject
- runtime inputs
- configuration inputs
- forbidden hidden dependencies

Rule:
If the implementation depends on a service or policy, the brief must say whether that dependency is injected, configured, or looked up through an existing contract.

### Step 10: Resolve code-artifact targets and validate taxonomy coverage
Input:
- component element model
- component element realization model
- component spec
- implementation target

Output:
- candidate code-artifact target set
- allowed target kinds for the slice
- explicit taxonomy coverage result
- draft brief-target dependency order

Rule:
If the current target taxonomy cannot express the intended implementation artifacts cleanly, derivation must stop and report a blocker.
Do not overload unrelated target labels just to force a slice through.

### Step 11: Resolve behavioral and proving contracts
Input:
- spec fragment
- implementation target
- requirements
- design decisions
- verification obligations

Output:
- behavior to add or change
- invariants to preserve
- edge cases
- error conditions
- tests to run
- tests to add or update
- protected baseline checks
- expected artifacts

Rule:
The proving contract must separate:
- baseline proving checks that must remain green
- slice-specific tests that must be added or updated

### Step 12: Resolve change budget and anti-goals
Input:
- implementation target
- architectural constraints
- known failure patterns
- prior rejection history if any

Output:
- change budget
- pre-handoff scope checks
- anti-goals
- common failure modes

Rule:
This is where repeated contamination patterns are prevented from recurring by design.

### Step 13: Compute brief-target sequencing and execution readiness
Input:
- approved slice package
- code-artifact target set
- target dependencies
- component dependency graph constraints
- shared-surface conflicts

Output:
- ordered brief target set
- execution prerequisites
- execution readiness classification
- blocking causes

Rule:
Sequencing is not optional planning commentary.
It is execution authority.
If target sequencing or readiness cannot be stated clearly, the brief is not ready for execution.

### Step 14: Assemble and validate draft brief
Input:
- outputs of steps 0 through 12

Output:
- draft `coder_run_brief`

Then validate the draft against:
- schema validation
- architecture review
- scope review
- target-taxonomy coverage review
- test-contract review
- packet-readiness review

### Step 15: Persist reviewed and approved brief with provenance
Input:
- reviewed draft brief
- approved target set
- signoff state

Output:
- approved `coder_run_brief`
- linked brief targets
- provenance and approval state

Rule:
Execution authority should be persisted as reviewed state, not left as an ephemeral draft artifact.

### Step 16: Embed approved brief into `architect_cycle_packet`
Input:
- approved brief
- packet preparation context

Output:
- packet-ready execution authority

Rule:
Only an approved brief that is packet-ready should be treated as execution authority for a coding lane.
## Derivation ownership
Not every part of derivation belongs to the same role.

### Product Owner
Owns or co-owns:
- product outcome intent
- acceptance meaning
- protected business or product truths

### Architect
Owns or co-owns:
- system-level intent
- architectural seams
- primary component placement
- boundary and growth constraints
- acceptance suitability of the brief

### Project Designer
Owns or co-owns:
- decomposition quality
- component model quality
- pattern mapping
- collaboration structure
- construction readability of the brief

### TechLead
Owns or co-owns:
- execution readiness
- pre-handoff scope gate practicality
- operational anti-goals
- recovery-aware enrichment

## Authored vs inferred mapping
The following mapping should guide tooling.

### Primarily authored
These should not be guessed by automation:
- slice scope
- authorized delta family
- out-of-scope delta families
- primary component assignment
- required architecture seams
- target module boundaries
- max responsibility expansion
- forbidden growth patterns
- anti-goals with architectural significance

### Primarily inferred
These can usually be derived mechanically, then reviewed:
- target modules
- allowed edit surfaces
- forbidden edit surfaces
- collaborating components
- callers / callees
- dependency candidates
- tests to run from obligation mappings
- expected artifact paths

### Derived then validated
These should be generated, then explicitly checked:
- component aspects
- behavioral contract phrasing
- test contract
- pre-handoff scope checks
- common failure modes

### TechLead enrichment
These may be added later without redefining architecture:
- operational warnings
- recovery hints
- runtime reminders
- automation-specific execution notes

## Recommended data flow
The derivation engine should work roughly like this:

1. confirm reviewed upstream authority
2. resolve and materialize slice package
3. load spec fragment, implementation target, and linked component records
4. load component elements, realization options, and candidate target kinds
5. validate code-artifact target taxonomy coverage for the slice
6. load verification obligations and dependency constraints
7. synthesize draft coder brief sections and draft brief-target set
8. require human review on authored and validated fields
9. persist approved brief and linked target set in PAA
10. embed approved brief into `architect_cycle_packet`

## Suggested tool support
The system should eventually support derivation with small tools, not manual copy-paste.

### Useful simple tools
- `resolve-slice-package`
- `evaluate-derivation-readiness`
- `suggest-primary-component`
- `derive-edit-surfaces`
- `derive-collaboration-context`
- `derive-brief-targets`
- `validate-target-taxonomy-coverage`
- `derive-test-contract`
- `derive-change-budget-checks`
- `review-coder-brief`
- `validate-coder-brief`
- `embed-coder-brief-into-packet`

These tools should assist derivation.
They should not replace review authority.

## Review gates before execution
A coder brief is ready for Stage 3 only when all of the following are true:
- schema-valid
- tied to current authority version and a materialized slice package
- primary component explicitly assigned
- edit boundaries explicit
- collaboration pattern explicit
- dependency contract explicit
- code-artifact target set explicit and taxonomy-valid
- execution prerequisites and readiness explicit
- test contract explicit
- pre-handoff scope checks explicit
- anti-goals explicit
- approved by design authority

## Failure modes this method is designed to prevent
- coder agent infers architecture from issue prose
- giant-module growth by convenience
- adjacent delta contamination
- hidden dependency introduction
- QA discovering scope problems that derivation should have prevented
- TechLead rediscovering missing construction detail during runtime

## Immediate implication for PAA
PAA should treat `coder_run_brief` as:
- a first-class derived artifact
- version-bound to an authority version
- linked to a work item and primary component
- reviewable before execution

This means the database and packet model are serving the right purpose:
- project authority stays upstream
- coder authority is derived downstream
- draft derivation output is distinct from approved execution authority
- execution consumes the approved derived brief, not raw design intent

## Next step
The next derivation refinements should make the remaining execution-authority bridge explicit:
- the exact Stage 1 slice-package shape required before derivation starts
- the code-artifact target taxonomy extensions needed for non-repository component families
- the explicit draft -> approved -> packet-ready lifecycle for derived briefs and linked target sets
