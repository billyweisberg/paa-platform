# Generic Source-to-PAA Issue Loader

## Purpose

Load a canonical producer-side issue slice into PAA from source artifacts instead of maintaining issue-specific SQL.

The loader materializes:

- `paa.work_items`
- `paa.design_packages`
- `paa.coder_run_briefs`
- `paa.coder_brief_sequence_states`
- `paa.verification_obligations`

## Producer flow integration

Repo-local producer architect packet compilation now calls this loader automatically for the target next issue before resolving the package and brief from PAA:

```bash
paa-producer authority materialize-architect-packet ...
```

By default this keeps source artifacts and PAA synchronized during the normal producer flow.
Use `--skip-source-sync` only for debugging or controlled recovery work.

Producer installs for the `fractal-core` project pack also render the repo-local Authority Architect automation template:

- `fractal-core-authority-architect-automation`

That automation is expected to use the repo-local producer command surface above, so source-to-PAA synchronization happens in the normal producer workflow rather than as a one-off recovery step.

## Command

```bash
paa-producer load-issue-into-paa \
  --repo-root <producer-repo> \
  --project-config <producer-project-config> \
  --issue-number <issue>
```

Optional:

```bash
  --dry-run
  --verification-key-prefix <key-prefix>
  --scope-authority-label <qa-scope-label>
```

## Source inputs

The loader reads from the canonical producer repo:

- authority manifest:
  - `.codex/paa/project-config.json -> authority_manifest_path`
- issue-specific Stage 1 package:
  - `stage1_design_package.issue<issue>.*.json`
- issue-specific coder briefs:
  - `coder_run_brief.issue<issue>.*.json`

## Behavior

- insert-only and idempotent
- safe to rerun after partial loads
- loads sequence state from each brief's `execution_readiness`
- derives verification obligations from the Stage 1 package `verification_contract_basis`

## Retirement of issue-specific load SQL

This command replaces the operational need for issue-specific load scripts such as:

- `104-load-issue101-retirement-subsystem-into-paa.sql`
- `106-load-issue103-retirement-lifecycle-executor-into-paa.sql`
- `108-load-issue106-retirement-boundary-diagnostics-into-paa.sql`
- `109-load-issue106-retirement-boundary-diagnostics-minimal-into-paa.sql`

Those scripts remain historical artifacts only and should not be used for active producer operations.
