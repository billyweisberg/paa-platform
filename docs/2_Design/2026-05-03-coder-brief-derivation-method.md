# 80. Coder Brief Derivation Method

## Purpose
This document defines the repeatable method for deriving a `coder_run_brief` from upstream project authority.

It is the bridge between:
- Stage 1: Design / Authoring
- Stage 2: Derivation

The goal is to make coder-facing implementation packets:
- deliberate
- reviewable
- reproducible
- tool-supported
- portable across projects in this portfolio

## Core principle
A coder agent should not derive system design.

A coder agent should receive a prepared construction brief that is itself derived from reviewed upstream design authority.

That means `coder_run_brief` is not handwritten from scratch, and it is not guessed from issue text.
It is derived from a staged design model.

## Upstream inputs
A `coder_run_brief` is derived from four primary sources:
- Product / Architect / Designer authority
- spec fragments
- implementation targets
- component model

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

### Step 1: Resolve active slice package
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

### Step 2: Resolve primary component assignment
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

### Step 3: Resolve component aspects
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

### Step 4: Resolve placement and edit boundaries
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

### Step 5: Resolve collaboration context
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

### Step 6: Resolve dependency contract
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

### Step 7: Resolve behavioral contract
Input:
- spec fragment
- implementation target
- requirements
- design decisions

Output:
- behavior to add or change
- invariants to preserve
- edge cases
- error conditions

Rule:
This section should be implementation-operational, not philosophical.
It should tell the coder what code behavior must result, not why the product exists.

### Step 8: Resolve test contract
Input:
- verification obligations
- implementation target protected baseline
- authority artifact expectations

Output:
- tests to run
- tests to add or update
- protected baseline checks
- expected artifacts

Rule:
The test contract must separate:
- baseline proving checks that must remain green
- slice-specific tests that must be added or updated

### Step 9: Resolve change budget and anti-goals
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

### Step 10: Assemble and validate brief
Input:
- outputs of steps 1 through 9

Output:
- draft `coder_run_brief`

Then validate the draft against:
- schema validation
- architecture review
- scope review
- test-contract review
- packet-readiness review

Only after these pass can the brief move to:
- `approved`
- then embedded in `architect_cycle_packet`

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

1. resolve task from authority version
2. load spec fragment and implementation target
3. load linked components, surfaces, and relationships
4. load verification obligations
5. synthesize draft coder brief sections
6. require human review on authored and validated fields
7. persist approved brief in PAA
8. embed approved brief into `architect_cycle_packet`

## Suggested tool support
The system should eventually support derivation with small tools, not manual copy-paste.

### Useful simple tools
- `resolve-slice-package`
- `suggest-primary-component`
- `derive-edit-surfaces`
- `derive-collaboration-context`
- `derive-test-contract`
- `derive-change-budget-checks`
- `validate-coder-brief`
- `embed-coder-brief-into-packet`

These tools should assist derivation.
They should not replace review authority.

## Review gates before execution
A coder brief is ready for Stage 3 only when all of the following are true:
- schema-valid
- tied to current authority version
- primary component explicitly assigned
- edit boundaries explicit
- collaboration pattern explicit
- dependency contract explicit
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
- execution consumes the derived brief, not raw design intent

## Next step
The next design decision should define the exact field-level derivation rules for every section of `coder_run_brief`, including:
- which source record populates each field
- whether the field is authored, inferred, validated, or enriched
- which role must sign off on it before the brief becomes active
