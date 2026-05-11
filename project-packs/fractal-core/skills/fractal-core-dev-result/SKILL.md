---
name: fractal-core-dev-result
description: Execute a Team Worker Role assignment from its owned deterministic role worktree and return a worker result packet to TechLead using repo-local PAA tooling.
---

Role:
- Act as the current Team Worker Role only.
- Receive assignments from `TechLead`.
- Return `worker_result_packet` only to `TechLead`.
- `slice_result_packet` remains legacy-compatible only.

Automation logging:
- bootstrap repo-local run logging before preflight through:
  - `{{REPO_ROOT}}/.codex/paa/scripts/runtime/run_automation_preflight_with_logging.sh`

Role identity contract:
- The calling automation must provide:
  - `worker role cli`
  - `worker display name`
  - `worker family`
  - `role branch suffix`
- `automation id`
- Substitute those values into the commands and expectations below.
- Example:
  - `Python Dev` / `python-team` / `implementation` / `dev` / `python-team-automation`

Execution contract:
- Launch from the canonical consumer repo root: `{{REPO_ROOT}}`
- Poll for work without model invocation first:

```bash
{{REPO_ROOT}}/.codex/paa/scripts/runtime/run_automation_preflight_with_logging.sh \
  --repo-root {{REPO_ROOT}} \
  --automation-id <automation_id> \
  --role-key <worker_role_cli> \
  --role-display-name <worker_display_name> \
  --target-role <worker_role_cli> \
  --phase preflight
```

- If `should_invoke_model = false`, exit without further work.
- If `should_invoke_model = true`, stay on repo-local consumer runtime only.
- Use the canonical issue branch `issue-<issue_number>` unless TechLead-authorized isolated role execution requires the deterministic role branch `issue-<issue_number>-<role_branch_suffix>`.
- Do not invent branch names.
- Do not route directly to `QA`.
- Do not depend on deprecated `$HOME/.codex` runtime assets.

Receive-side execution flow:

1. Create or reuse the owned deterministic role worktree first:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-prepare-role-worktree \
  --repo-root {{REPO_ROOT}} \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role <worker_role_cli>
```

- This is the required first step when real work exists.
- Team Worker roles own create-or-reuse of their own deterministic worktree beneath TechLead-authorized lineage.

2. Inspect the prepared role worktree:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-inspect-role-worktree \
  --repo-root {{REPO_ROOT}} \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role <worker_role_cli>
```

3. Resolve the entry context and exact execution surfaces:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-role-entry \
  --repo-root {{REPO_ROOT}} \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role <worker_role_cli>
```

4. Change into the prepared role worktree returned by the role-entry context.

5. Perform the assigned work there.
- Prefer `uv run` from the prepared worktree for repo work.
- Do not silently switch to unrelated interpreter state.

6. Prepare the return-packet context:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-role-result-assist \
  --repo-root {{REPO_ROOT}} \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role <worker_role_cli>
```

7. Return the worker result packet to TechLead:

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
- do not proceed if `techlead-prepare-role-worktree` fails
- do not proceed if the prepared worktree is missing or on the wrong branch after prepare-or-reuse
- do not teach `slice_result_packet` as the active lane
- do not route directly to `QA`
