---
name: fractal-core-qa-review
description: Execute a QA assignment from a prepared role worktree and return a QA verification packet to TechLead using repo-local PAA tooling.
---

Role:
- Act as `QA` only.
- Receive assignments from `TechLead`.
- Return `qa_verification_packet` only to `TechLead`.

Execution contract:
- Launch from the canonical consumer repo root: `{{REPO_ROOT}}`
- Poll for work without model invocation first:

```bash
{{REPO_ROOT}}/.codex/paa/scripts/runtime/run_automation_preflight_with_logging.sh \
  --repo-root {{REPO_ROOT}} \
  --automation-id fractal-core-qa-automation \
  --role-key qa \
  --role-display-name "QA" \
  --target-role qa \
  --phase preflight
```

- If `should_invoke_model = false`, exit without further work.
- If `should_invoke_model = true`, stay on repo-local consumer runtime only.
- Use the canonical issue branch `issue-<issue_number>` unless TechLead-authorized isolated role execution requires the deterministic role branch `issue-<issue_number>-qa`.
- Do not invent branch names.
- Do not route directly to `Architect`.
- Do not depend on deprecated `$HOME/.codex` runtime assets.

Receive-side execution flow:

1. Inspect the prepared role worktree:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-inspect-role-worktree \
  --repo-root {{REPO_ROOT}} \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role qa
```

2. Resolve the entry context and exact execution surfaces:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-role-entry \
  --repo-root {{REPO_ROOT}} \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role qa
```

3. Change into the prepared role worktree returned by the role-entry context.

4. Perform the assigned verification from that worktree.
- Prefer `uv run` from the prepared worktree when repo commands are needed.

5. Prepare the return-packet context:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-role-result-assist \
  --repo-root {{REPO_ROOT}} \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role qa
```

6. Return the QA verification packet to TechLead:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-role-return \
  --repo-root {{REPO_ROOT}} \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role qa \
  --send
```

QA result contract:
- result family: `qa_verification_packet`
- required input file keys are surfaced by `techlead-role-result-assist`

Fail-closed rules:
- do not proceed if preflight says no work
- do not proceed if the prepared worktree is missing or on the wrong branch
- do not route directly to `Architect`
