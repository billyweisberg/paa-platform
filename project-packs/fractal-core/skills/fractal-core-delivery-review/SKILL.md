---
name: fractal-core-delivery-review
description: Execute a Delivery Architect assignment from a prepared role worktree and return a delivery review packet to TechLead using repo-local PAA tooling.
---

Role:
- Act as `Delivery Architect` only.
- Receive assignments from `TechLead`.
- Return `delivery_review_packet` only to `TechLead`.

Execution contract:
- Launch from the canonical consumer repo root: `{{REPO_ROOT}}`
- Poll for work without model invocation first:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer automation-preflight \
  --repo-root {{REPO_ROOT}} \
  --target-role delivery-architect
```

- If `should_invoke_model = false`, exit without further work.
- If `should_invoke_model = true`, stay on repo-local consumer runtime only.
- Use the canonical issue branch `issue-<issue_number>` unless TechLead-authorized isolated role execution requires the deterministic role branch `issue-<issue_number>-delivery`.
- Do not invent branch names.
- Do not depend on deprecated `$HOME/.codex` runtime assets.

Receive-side execution flow:

1. Inspect the prepared role worktree:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-inspect-role-worktree \
  --repo-root {{REPO_ROOT}} \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role delivery-architect
```

2. Resolve the entry context and exact manual execution surfaces:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-role-entry \
  --repo-root {{REPO_ROOT}} \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role delivery-architect
```

3. Change into the prepared role worktree returned by the role-entry context.

4. Perform the assigned Delivery Architect review from that worktree.

5. Prepare the return-packet context:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-role-result-assist \
  --repo-root {{REPO_ROOT}} \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role delivery-architect
```

6. Return the delivery review packet to TechLead:

```bash
{{REPO_ROOT}}/.codex/paa/bin/paa-consumer techlead-role-return \
  --repo-root {{REPO_ROOT}} \
  --package-id-external <package_id_external> \
  --brief-id-external <brief_id_external> \
  --target-role delivery-architect \
  --send
```

Delivery result contract:
- result family: `delivery_review_packet`
- required input file keys are surfaced by `techlead-role-result-assist`
- expected assignment type: `delivery_architecture_review`

Fail-closed rules:
- do not proceed if preflight says no work
- do not proceed if the prepared worktree is missing or on the wrong branch
- do not route directly to `Python Dev`, `QA`, or `Architect`
- do not send any packet other than `delivery_review_packet`
