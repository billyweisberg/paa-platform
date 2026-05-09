---
name: fractal-core-dev-result
description: Execute a Team Worker Role assignment from a prepared role worktree and return a worker result packet to TechLead using repo-local PAA tooling.
---

Role:
- Act as the current Team Worker Role only.
- Receive assignments from `TechLead`.
- Return `worker_result_packet` only to `TechLead`.
- `slice_result_packet` remains legacy-compatible only.

Role identity contract:
- The calling automation must provide:
  - `worker role cli`
  - `worker display name`
  - `worker family`
  - `role branch suffix`
- Substitute those values into the commands and expectations below.
- Example:
  - `Python Dev` / `python-team` / `implementation` / `dev`

Execution contract:
- Launch from the canonical consumer repo root: `{{REPO_ROOT}}`
- Poll for work without model invocation first:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer automation-preflight \
  --repo-root {{REPO_ROOT}} \
  --target-role <worker_role_cli>
```

- If `should_invoke_model = false`, exit without further work.
- If `should_invoke_model = true`, stay on repo-local consumer runtime only.
- Use the canonical issue branch `issue-<issue_number>` unless TechLead-authorized isolated role execution requires the deterministic role branch `issue-<issue_number>-<role_branch_suffix>`.
- Do not invent branch names.
- Do not route directly to `QA`.
- Do not depend on deprecated `$HOME/.codex` runtime assets.

Receive-side execution flow:

1. Inspect the prepared role worktree:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-inspect-role-worktree \
  --repo-root {{REPO_ROOT}} \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role <worker_role_cli>
```

2. Resolve the entry context and exact execution surfaces:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-role-entry \
  --repo-root {{REPO_ROOT}} \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role <worker_role_cli>
```

3. Change into the prepared role worktree returned by the role-entry context.

4. Perform the assigned work there.
- Prefer `uv run` from the prepared worktree for repo work.
- Do not silently switch to unrelated interpreter state.

5. Prepare the return-packet context:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-role-result-assist \
  --repo-root {{REPO_ROOT}} \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role <worker_role_cli>
```

6. Return the worker result packet to TechLead:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-role-return \
  --repo-root {{REPO_ROOT}} \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role <worker_role_cli> \
  --send
```

Team Worker Role result contract:
- active result family: `worker_result_packet`
- expected assignment type: `implement_authorized_slice`
- required input file keys are surfaced by `techlead-role-result-assist`

Fail-closed rules:
- do not proceed if preflight says no work
- do not proceed if the prepared worktree is missing or on the wrong branch
- do not teach `slice_result_packet` as the active lane
- do not route directly to `QA`
