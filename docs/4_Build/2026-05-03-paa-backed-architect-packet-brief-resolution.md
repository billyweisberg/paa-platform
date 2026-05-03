# 93. PAA-Backed Architect Packet Brief Resolution

## Purpose
This note captures the first live bridge from PAA sequencing state into `architect_cycle_packet` payload generation.

The design goal is simple:
- Architect should not hand-curate coder brief payloads once PAA holds live design, dependency, and readiness state.
- Architect should resolve the next execution-eligible coder brief from PAA.
- If no such brief exists, or if multiple are eligible without explicit parallel approval, packet emission must fail closed.

## Helper command
Use:

```bash
python3 future `paa-platform` authority/runtime command surface materialize-coder-brief \
  --project-slug fractal-core-python \
  --package-id-external <design_package_id_external> \
  --require-ready
```

This command returns:
- `coder_run_brief_ref`
- embedded `coder_run_brief`
- `readiness_state`
- optional `parallel_group_id`

## Fail-closed rules
The command fails closed when:
- no coder brief exists for the package
- no brief is execution-eligible
- multiple briefs are execution-eligible and explicit parallel approval has not been granted

This is the correct behavior.
It prevents Architect from guessing which component should run next.

## Why this matters
This is the first point where:
- Stage 1 package
- dependency graph
- coder brief derivation
- sequence readiness

all become direct packet-generation authority.

That is a major shift.
It means the queue packet can now be driven from the live upstream planning model instead of from manually assembled architecture context.

## Current scope
This helper currently resolves from:
- `paa.design_packages`
- `paa.coder_run_briefs`
- `paa.coder_brief_sequence_states`
- `paa.component_dependency_edges`

It does not yet build the full packet automatically.
That is fine.
The important step is that packet payload selection is now PAA-backed and fail-closed.

## Next step
The natural next evolution is:
- add a helper that materializes the full `architect_cycle_packet` shell from:
  - authority state
  - GitHub context
  - current baseline summary
  - resolved PAA-backed coder brief

At that point, Architect packet generation becomes a compiled artifact rather than a hand-composed JSON message.
