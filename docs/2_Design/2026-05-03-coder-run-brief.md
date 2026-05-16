# 75. Coder Run Brief

## Purpose
A coder agent should not be asked to derive implementation structure from semantic intent alone.

The `coder_run_brief` is the implementation-facing authority artifact for a single coding run.
It answers the practical questions a coding agent needs to perform useful work without collapsing architecture into monolithic growth.

This artifact is downstream of:
- authority task authoring
- architect design decisions
- spec fragments
- implementation targets

It is upstream of:
- a Python or other coder-agent run
- code edits
- tests
- QA handoff

## Why it exists
Our semantic authority model is useful for Architect and Project Designer roles.
It is not sufficient as the primary working context for a coder agent.

A coder agent needs:
- what component it is working on
- where that component lives architecturally
- which surfaces it may edit
- which collaborators are involved
- which tests prove the run
- which growth patterns are forbidden

Without that, coding agents reliably do the wrong thing:
- enlarge existing modules
- absorb new responsibilities into god components
- mix adjacent deltas
- satisfy behavior while damaging structure

## Layer, tier, and slice
These ideas are all useful, but they are not interchangeable.

### `slice`
The work item or implementation unit.
This already exists elsewhere in the system:
- issue
- task
- implementation target

### `component_role`
What the component does in the architecture.
Examples:
- host adapter
- top-level coordinator
- context abstraction
- hierarchy manager
- version boundary policy
- metrics surface

### `system_layer`
Where the component sits in the architecture.
Examples:
- host-adapter
- model-core
- policy
- hierarchy
- diagnostics
- contract
- test
- docs
- integration

### `tier`
Optional broader deployment or architectural tier.
Examples:
- data
- compute
- ui
- framework
- runtime

For Baby-7, `system_layer` is usually more precise than `tier`.
For broader projects like AgentHub or GIS, both may be useful.

## Minimum fields a coder agent needs

### Identity
- `component_name`
- `component_role`
- `system_layer`
- `tier` if useful
- `slice_scope_ref`

### Placement
- `target_modules`
- `allowed_edit_surfaces`
- `forbidden_edit_surfaces`
- `required_architecture_seams`
- `target_module_boundaries`

### Scope
- `component_aspects`
Examples:
- state
- interface
- functions
- configuration
- events
- hosting
- tests
- docs

### Collaboration
- `pattern_name`
- `collaborating_components`
- `callers`
- `callees`
- `event_emitters`
- `event_consumers`

### Execution prerequisites
- `prerequisite_briefs`
- `blocking_dependency_edges`
- `parallel_safe_with`
- `shared_surface_conflicts`
- `sequencing_notes`

### Dependencies
- `dependencies_to_inject`
- `runtime_inputs`
- `configuration_inputs`
- `forbidden_hidden_dependencies`

### Behavioral contract
- `behavior_to_add_or_change`
- `invariants_to_preserve`
- `edge_cases`
- `error_conditions`

### Test contract
- `tests_to_run`
- `tests_to_add_or_update`
- `protected_baseline_checks`
- `artifacts_expected`

### Execution readiness
- `readiness_class`
- `dependency_readiness`
- `blocking_causes`
- `parallel_group_id`
- `recommended_next_owner`
- `readiness_snapshot_source`

### Change budget
- `max_responsibility_expansion`
- `forbidden_module_growth_patterns`
- `expected_touch_surfaces`
- `pre_handoff_scope_checks`

### Anti-goals
- `anti_goals`
- `common_failure_modes`

## Design rule
A `coder_run_brief` should be concrete enough that a coding agent can complete a run without inventing architecture.

If a coding agent still has to infer:
- where a responsibility belongs
- which neighboring component should absorb it
- whether a giant file may grow again

then the brief is still under-specified.

## Authority Lifecycle Governance

The existence of a brief row or JSON artifact is not enough to treat it as execution authority.

PAA now distinguishes:
- `draft_brief`
- `approved_brief`
- `packet_ready_execution_authority`

Meaning:
- `draft_brief` is useful derivation output, but not launch-ready authority
- `approved_brief` has passed review, but may still be blocked on packet-preparation checks
- `packet_ready_execution_authority` is the first state a coding lane may treat as transport-ready implementation authority

DB support:
- `paa.coder_run_briefs.authority_state`
- `paa.coder_run_briefs.authority_state_updated_at`
- `paa.coder_run_briefs.approved_at`
- `paa.coder_run_briefs.packet_ready_at`
- `paa.coder_run_briefs.approval_json`
- `paa.coder_run_briefs.packet_preparation_json`
- `paa.coder_brief_authority_events`

Rule:
- do not treat a draft brief as execution authority just because the brief body exists

## Next use
The first useful concrete example should be:
- issue `#73`
- retirement lifecycle boundary

because that slice exposed the exact gap this artifact is meant to close.
