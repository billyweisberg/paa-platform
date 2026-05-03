# 76. Coder Run Brief Packet Integration

## Purpose
This note defines how `architect_cycle_packet` should carry coder-facing implementation authority.

The design goal is:
- Architect keeps semantic and project authority
- Python receives a concrete implementation brief
- the queue packet is self-sufficient for execution
- the brief still points back to a stable authoritative artifact

## Decision
`architect_cycle_packet` should carry both:

1. an embedded full `coder_run_brief`
2. a `coder_run_brief_ref` back to the authoritative artifact path

This is not either/or.
We want both.

## Why embed the full brief
The coding agent should not need a second lookup step to begin useful work.

Embedding the full brief means:
- the queue packet is execution-ready
- the coder run can proceed even if another file path changes later
- all critical implementation constraints are present in the handoff itself

## Why also keep a reference
The embedded brief is the transport copy.
The referenced artifact is the maintainable source-of-truth copy.

The reference allows:
- auditing
- review
- reuse
- regeneration
- diffing later versions of the brief

## Required packet shape

Within `architect_cycle_packet.payload`, include:

### `coder_run_brief_ref`
- `path`
- `schema_path`
- `brief_id`

### `coder_run_brief`
Embed the full `coder_run_brief` object as defined by:
- `handoff-schemas/coder_run_brief.schema.json`

## Design rule
The coding agent should consume the embedded brief first.

The reference is used for:
- traceability
- debugging
- regeneration
- external review

The coding agent should not be forced to reconstruct the run from the reference if the packet already contains the brief.

## Python automation consumption rules
When a Python run starts from an `architect_cycle_packet`:

1. read the packet
2. require `payload.coder_run_brief`
3. treat that brief as the implementation authority for the run
4. use GitHub issue/PR only as execution state, not as the primary design brief
5. if the packet lacks `coder_run_brief`, stop and report a blocker once this migration is active

## Minimum Python behavior
The Python lane should explicitly extract from the brief:
- `component_assignment`
- `architecture_constraints`
- `collaboration_context`
- `execution_prerequisites`
- `dependency_contract`
- `behavioral_contract`
- `test_contract`
- `execution_readiness`
- `change_budget`
- `anti_goals`

And before sending QA handoff, it should evaluate:
- `change_budget.pre_handoff_scope_checks`

It should also respect:
- `execution_prerequisites.blocking_dependency_edges`
- `execution_prerequisites.parallel_safe_with`
- `execution_readiness.readiness_class`
- `execution_readiness.blocking_causes`

If the brief is not at least:
- `execution_ready`
or explicitly part of an approved:
- `parallel_ready`
set,

the coding lane should stop and report a blocker instead of beginning execution.

## Migration note
During transition, Python may still run without a `coder_run_brief`.
But once this integration is adopted as standard, missing coder brief should be treated as an under-specified Architect packet.
