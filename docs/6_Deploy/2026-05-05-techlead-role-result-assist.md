# Purpose

Add the first narrow role-result assist helper on top of the role-entry context.

This slice intentionally does only four things:
- consume the role-entry context
- validate the required result-packet context
- print the exact result compile surfaces
- stop before compiling or sending the result packet

## Command

```bash
<consumer_repo>/.codex/paa/bin/paa-consumer techlead-role-result-assist \
  --repo-root <consumer_repo> \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role <python-team|qa>
```

Optional overrides:
- `--role-branch`
- `--worktree-path`
- `--assignment-path`
- `--review-output`
- `--result-input-path`

## Behavior

The command builds on `techlead-role-entry`.

If the role-entry context is valid, it returns:
- role result family
- required result context
- missing context fields, if any
- result input contract
- exact manual result commands

## Exact manual result surfaces

The output includes:
- `enter_worktree_command`
- `assignment_json_command`
- `assignment_review_command`
- `result_input_template_path`
- `result_compile_command`

## Role-specific result families

For `Python Dev`:
- result family: `slice_result_packet`
- expected assignment type: `implement_authorized_slice`
- input flag: `--dev-input-file`

For `QA`:
- result family: `qa_verification_packet`
- expected assignment type: `verify_authorized_slice`
- input flag: `--qa-input-file`

Important:
- role work still happens in the prepared worktree
- packet compilation still uses the installed repo-root runtime wrappers
- this slice does not compile the result packet
- this slice does not send the result packet
