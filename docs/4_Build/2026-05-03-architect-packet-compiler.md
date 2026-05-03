# 94. Architect Packet Compiler

## Purpose
This note captures the next bridge in PAA:
- not just resolving an execution-eligible coder brief from PAA
- but compiling the actual `architect_cycle_packet` shell from:
  - authority context
  - GitHub context
  - baseline summary
  - live PAA-backed coder-brief resolution

The result is a ready-to-validate packet file rather than a hand-composed JSON draft.

## Helper command
Use:

```bash
python3 future `paa-platform` authority/runtime command surface materialize-architect-packet \
  --manifest /absolute/path/to/fractal-core-python-authority.json \
  --project-slug fractal-core-python \
  --package-id-external <design_package_id_external> \
  --repo <owner/repo> \
  --accepted-pr-number <accepted_pr_number> \
  --accepted-pr-url <accepted_pr_url> \
  --closed-issue-number <closed_issue_number> \
  --closed-issue-url <closed_issue_url> \
  --next-issue-number <next_issue_number> \
  --next-issue-url <next_issue_url> \
  --baseline-file /absolute/path/to/baseline-summary.json \
  --remaining-gap "<remaining_gap_summary>" \
  --next-move "<next_move_1>" \
  --focus "<focus_1>" \
  --keep-stable trace \
  --keep-stable parity \
  --keep-stable benchmark \
  --governance-reminder "Dev owns implementation, validation, and keeping the PR current" \
  --governance-reminder "Architect / Spec Owner owns acceptance and merge" \
  --governance-reminder "do not merge your own slice" \
  --output .codex-work/architect-cycle-packet.json
```

## What it does
The helper:
1. loads the authority manifest
2. loads the PAA design package
3. resolves the live execution-eligible coder brief from PAA
4. fails closed if no eligible brief exists
5. fails closed if multiple eligible briefs exist without explicit parallel approval
6. compiles the packet shell with:
   - envelope
   - authority context
   - GitHub context
   - baseline summary
   - embedded coder brief
   - coder brief reference
   - coder brief resolution metadata

## Why this matters
This is the first time the next-cycle packet itself can be treated as a compiled artifact.

That means Architect is no longer expected to:
- hand-assemble queue payload JSON
- hand-copy coder brief content
- guess which execution-eligible brief should run next

PAA now answers that question first.

## Current scope
This compiler still expects a human or higher-level role to provide:
- accepted PR and issue references
- baseline summary file
- next-move / focus / governance reminder text

That is fine for now.
It means we have eliminated the structural packet-selection work before trying to automate every narrative field.

## Proof
The proving package compiled successfully to:
- `a proving compiled packet artifact in repo-local scratch output`

And validated successfully with:
- `rabbitmq_handoff.py validate`

## Next step
The next natural evolution is:
- derive more of the packet narrative from:
  - authority task authoring
  - design package
  - sequence state
- then let Architect review and finalize the compiled packet rather than composing it from scratch
