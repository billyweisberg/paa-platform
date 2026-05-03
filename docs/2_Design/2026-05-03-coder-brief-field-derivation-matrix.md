# 81. Coder Brief Field Derivation Matrix

## Purpose
This document defines the field-level derivation rules for `coder_run_brief`.

It is the operational companion to:
- `docs/2_Design/2026-05-03-coder-brief-derivation-method.md`
- `appdev/docs/architecture/tom-baby7-fractal-core/handoff-schemas/coder_run_brief.schema.json`

The goal is to answer, for every section of the brief:
- where the value comes from
- whether it is authored, inferred, validated, or enriched
- which role signs off on it
- what rule derives it

## Derivation status meanings
- `authored`: directly set by a design authority role
- `inferred`: mechanically derived from structured records
- `validated`: generated or proposed, then explicitly reviewed before approval
- `enriched`: operationally helpful context added without redefining authority

## Section-level matrix

| Brief section | Primary sources | Derivation status | Primary signoff | Derivation rule |
| --- | --- | --- | --- | --- |
| `brief_id` | authority version, task id, work item identity | inferred | TechLead | Generate a stable identifier from project + authority version + task id + run family. |
| `schema_type` | schema contract | inferred | none | Constant `coder_run_brief`. |
| `schema_version` | schema contract | inferred | Architect | Use the current supported brief schema version. |
| `project` | project registry | inferred | TechLead | Resolve from project slug / project record. |
| `authority_context` | authority version, authority task, work item, GitHub execution state | inferred then validated | TechLead | Populate current authority version, milestone, phase, task id, and current issue/PR if materialized. |
| `slice_scope_ref` | authority task, spec fragment, implementation target | authored plus validated | Architect | Author the slice name and authorized delta family; validate out-of-scope families against adjacent roadmap deltas. |
| `component_assignment` | component model, component surfaces, implementation target | authored plus inferred plus validated | Architect + Project Designer | Architect selects the primary component; system layer and role come from component model; aspects and target modules are derived from implementation target + component surfaces, then reviewed. |
| `architecture_constraints` | spec fragment boundary fields, implementation target boundary fields, component model | authored plus inferred plus validated | Architect | Required seams, target module boundaries, growth constraints are authored; allowed/forbidden surfaces are inferred from surfaces and constraints, then reviewed. |
| `collaboration_context` | component relationships, sequence/activity diagrams, pattern notes | inferred then validated | Project Designer | Derive pattern name and local collaborators from the component graph and design diagrams; validate that the context is local and sufficient for coding. |
| `dependency_contract` | component relationships, constructor/setup model, config contracts | inferred then validated | Project Designer + TechLead | Derive injectables, runtime inputs, and config inputs from the component graph and existing setup contracts; validate that hidden dependencies are explicitly forbidden. |
| `behavioral_contract` | spec fragment, implementation target, requirements, design decisions | validated | Architect | Convert upstream design intent into concrete implementation behavior, invariants, edge cases, and error conditions. |
| `test_contract` | verification obligations, implementation target, artifact expectations | inferred then validated | TechLead + Architect | Derive tests-to-run from obligations and baseline checks; validate added/updated tests and expected artifacts against the slice. |
| `change_budget` | implementation target, boundary fields, prior failure history | authored plus validated | Architect + TechLead | Author max responsibility expansion and expected touch surfaces; derive or validate pre-handoff scope checks so they can be executed mechanically. |
| `anti_goals` | architectural constraints, prior rejection history, known failure patterns | authored plus enriched plus validated | Architect + TechLead | Architect authors the anti-goals that preserve design intent; TechLead may enrich with recurrence and recovery warnings; review before approval. |

## Field-level breakdown

## Top-level identity

### `brief_id`
- Sources:
  - project slug
  - authority version
  - task id
  - work item identity
- Status:
  - `inferred`
- Signoff:
  - TechLead
- Rule:
  - Use a deterministic naming convention so the brief can be regenerated without semantic drift.

### `schema_type`
- Sources:
  - schema definition
- Status:
  - `inferred`
- Signoff:
  - none
- Rule:
  - Constant literal from schema.

### `schema_version`
- Sources:
  - schema definition
  - derivation tool version
- Status:
  - `inferred`
- Signoff:
  - Architect
- Rule:
  - Must match the active schema the execution lane expects.

### `project`
- Sources:
  - PAA project record
  - authority manifest project slug
- Status:
  - `inferred`
- Signoff:
  - TechLead
- Rule:
  - Resolve to canonical project identifier, not a freeform label.

## `authority_context`

### `authority_version`
- Sources:
  - published authority version
- Status:
  - `inferred`
- Signoff:
  - TechLead
- Rule:
  - Always bind the brief to the current authority version.

### `milestone_id`, `phase_id`, `task_id`
- Sources:
  - authority task definition
- Status:
  - `inferred`
- Signoff:
  - Architect
- Rule:
  - Copy from the resolved active task package.

### `issue_number`, `pr_number`
- Sources:
  - materialized work item / execution state
- Status:
  - `inferred`
- Signoff:
  - TechLead
- Rule:
  - Include if execution materialization already exists; otherwise allow null.

## `slice_scope_ref`

### `slice_name`
- Sources:
  - authority task title
  - spec fragment title
- Status:
  - `authored`
- Signoff:
  - Architect
- Rule:
  - Must be the canonical short name for the implementation slice, not a broad epic label.

### `authorized_delta_family`
- Sources:
  - spec fragment
  - implementation target
- Status:
  - `authored`
- Signoff:
  - Architect
- Rule:
  - Must name the exact authorized family being reduced by this slice.

### `out_of_scope_delta_families`
- Sources:
  - spec fragment
  - implementation target
  - roadmap adjacency analysis
- Status:
  - `authored` then `validated`
- Signoff:
  - Architect + Project Designer
- Rule:
  - Explicitly enumerate adjacent delta families a coder must not absorb.

## `component_assignment`

### `component_name`
- Sources:
  - component model
  - design decision
- Status:
  - `authored`
- Signoff:
  - Architect
- Rule:
  - Assign exactly one primary component. If multiple components change, supporting components belong elsewhere in the brief, not as co-primary owners.

### `component_role`
- Sources:
  - component model
- Status:
  - `authored`
- Signoff:
  - Project Designer
- Rule:
  - Use the stable architectural role of the component, not a temporary coding description.

### `system_layer`
- Sources:
  - component model
- Status:
  - `authored`
- Signoff:
  - Project Designer
- Rule:
  - Must come from the modeled architecture layer taxonomy.

### `tier`
- Sources:
  - component model
  - project architecture
- Status:
  - `authored` or omitted
- Signoff:
  - Project Designer
- Rule:
  - Use only when it adds real platform/deployment meaning.

### `component_aspects`
- Sources:
  - implementation target desired state
  - component surfaces
  - target modules
- Status:
  - `inferred` then `validated`
- Signoff:
  - Project Designer
- Rule:
  - Derive from the kinds of surfaces touched and the nature of the intended change.

### `target_modules`
- Sources:
  - component surfaces
  - expected touch surfaces
  - implementation target
- Status:
  - `inferred` then `validated`
- Signoff:
  - Architect + Project Designer
- Rule:
  - Resolve to concrete module paths the coder may need to change.

## `architecture_constraints`

### `required_architecture_seams`
- Sources:
  - design decisions
  - component model
  - architectural authority constraints
- Status:
  - `authored`
- Signoff:
  - Architect
- Rule:
  - State the seams that must remain distinct after the run.

### `target_module_boundaries`
- Sources:
  - architectural authority constraints
  - component model
- Status:
  - `authored`
- Signoff:
  - Architect
- Rule:
  - Describe where new responsibility is allowed to land and where it is not.

### `allowed_edit_surfaces`
- Sources:
  - component surfaces
  - target modules
  - implementation target
- Status:
  - `inferred` then `validated`
- Signoff:
  - Project Designer
- Rule:
  - Include only surfaces legitimately required by the slice.

### `forbidden_edit_surfaces`
- Sources:
  - out-of-scope delta families
  - component boundaries
  - known unrelated areas
- Status:
  - `authored` then `validated`
- Signoff:
  - Architect
- Rule:
  - Make adjacent or unrelated surfaces explicit so coders do not wander by convenience.

### `forbidden_module_growth_patterns`
- Sources:
  - architectural authority constraints
  - prior failures
- Status:
  - `authored`
- Signoff:
  - Architect
- Rule:
  - Capture the growth patterns the system is explicitly trying to prevent.

## `collaboration_context`

### `pattern_name`
- Sources:
  - sequence/activity diagrams
  - component pattern catalog
- Status:
  - `authored` or `validated`
- Signoff:
  - Project Designer
- Rule:
  - Use the local collaboration pattern that matters for the run, not the whole system topology.

### `collaborating_components`
- Sources:
  - component relationships
  - pattern definition
- Status:
  - `inferred` then `validated`
- Signoff:
  - Project Designer
- Rule:
  - Include only the local components materially involved in the run.

### `callers`, `callees`, `event_emitters`, `event_consumers`
- Sources:
  - component relationships
  - sequence diagrams
  - event contracts
- Status:
  - `inferred` then `validated`
- Signoff:
  - Project Designer
- Rule:
  - Derive from known interaction edges; omit noise.

## `dependency_contract`

### `dependencies_to_inject`
- Sources:
  - component relationships
  - constructor/setup model
- Status:
  - `inferred` then `validated`
- Signoff:
  - Project Designer
- Rule:
  - Name only real injectables or contractual collaborators.

### `runtime_inputs`
- Sources:
  - behavioral contract
  - call pattern
  - state model
- Status:
  - `validated`
- Signoff:
  - TechLead
- Rule:
  - List the runtime inputs the component actually needs to operate in this slice.

### `configuration_inputs`
- Sources:
  - config contract
  - implementation target
- Status:
  - `inferred` then `validated`
- Signoff:
  - TechLead
- Rule:
  - Include only configuration knobs relevant to the slice.

### `forbidden_hidden_dependencies`
- Sources:
  - architecture constraints
  - prior failure history
- Status:
  - `authored` then `validated`
- Signoff:
  - Architect + TechLead
- Rule:
  - Make dependency shortcuts explicit so coders do not infer convenience couplings.

## `behavioral_contract`

### `behavior_to_add_or_change`
- Sources:
  - spec fragment canonical statement
  - implementation target desired state
- Status:
  - `validated`
- Signoff:
  - Architect
- Rule:
  - Translate design intent into concrete implementation behavior statements.

### `invariants_to_preserve`
- Sources:
  - requirements
  - implementation target protected baseline
  - design decisions
- Status:
  - `authored` then `validated`
- Signoff:
  - Product Owner + Architect
- Rule:
  - Include the truths that must survive the run.

### `edge_cases`, `error_conditions`
- Sources:
  - implementation target current gap
  - prior rejection history
  - design review
- Status:
  - `validated`
- Signoff:
  - Architect + TechLead
- Rule:
  - Capture the slice-specific cases a coder should not have to discover late.

## `test_contract`

### `tests_to_run`
- Sources:
  - verification obligations
  - project baseline test rules
- Status:
  - `inferred` then `validated`
- Signoff:
  - TechLead
- Rule:
  - Derive from obligation mappings and standard proving checks.

### `tests_to_add_or_update`
- Sources:
  - implementation target
  - expected touch surfaces
  - design review
- Status:
  - `validated`
- Signoff:
  - Architect + TechLead
- Rule:
  - Name the test surfaces that should change to prove the slice.

### `protected_baseline_checks`
- Sources:
  - implementation target protected baseline
  - verification obligations
- Status:
  - `authored` then `validated`
- Signoff:
  - Product Owner + Architect
- Rule:
  - These are not optional; they carry the proving baseline.

### `artifacts_expected`
- Sources:
  - verification obligations
  - artifact contracts
- Status:
  - `inferred` then `validated`
- Signoff:
  - TechLead
- Rule:
  - Enumerate the artifacts execution or QA should produce.

## `change_budget`

### `max_responsibility_expansion`
- Sources:
  - architectural authority constraints
  - implementation target
- Status:
  - `authored`
- Signoff:
  - Architect
- Rule:
  - State in plain terms how far the coder may broaden responsibility in this run.

### `expected_touch_surfaces`
- Sources:
  - implementation target
  - component surfaces
- Status:
  - `authored` then `validated`
- Signoff:
  - Architect + Project Designer
- Rule:
  - These are expected semantic or structural surfaces, not just file paths.

### `pre_handoff_scope_checks`
- Sources:
  - implementation target
  - out-of-scope families
  - prior rejection history
- Status:
  - `validated`
- Signoff:
  - TechLead + Architect
- Rule:
  - Phrase these so tooling or the coder can execute them before QA handoff.

## `anti_goals`

### `anti_goals`
- Sources:
  - architecture constraints
  - implementation target
  - prior failure modes
- Status:
  - `authored` then `validated`
- Signoff:
  - Architect
- Rule:
  - State the tempting but wrong moves this slice must avoid.

### `common_failure_modes`
- Sources:
  - prior rejection history
  - TechLead recovery history
  - architecture review
- Status:
  - `enriched` then `validated`
- Signoff:
  - TechLead + Architect
- Rule:
  - Record the likely ways the run can go wrong so we stop rediscovering them.

## Practical derivation order
Use this order when building tooling:

1. Resolve top-level identity and authority context.
2. Resolve slice scope from task + fragment + target.
3. Resolve primary component assignment.
4. Resolve target modules and edit surfaces.
5. Resolve collaboration and dependency context.
6. Draft behavioral and test contracts.
7. Draft change budget and anti-goals.
8. Run review and signoff by role.
9. Persist approved brief in PAA.
10. Embed approved brief into `architect_cycle_packet`.

## Tooling implication
The derivation engine should preserve provenance.
For each field or section, it should eventually record:
- source records used
- derivation status
- generated timestamp
- last reviewer
- signoff status

That provenance should ultimately live in PAA, not only in a generated JSON artifact.

## Immediate next step
The next iteration should define the missing layer between method and tooling:
- the exact Stage 1 design package shape that must exist before derivation starts

That package is what lets derivation become repeatable instead of bespoke.
