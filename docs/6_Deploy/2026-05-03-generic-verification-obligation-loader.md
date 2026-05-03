# Generic Verification Obligation Loader

## Purpose

Replace issue-specific `load-issue*.sql` obligation inserts with a repeatable producer-side command.

The loader derives verification obligations from the canonical Stage 1 design package artifact in the producer repo and inserts any missing `paa.verification_obligations` rows for a target issue.

## Command

```bash
paa-producer materialize-verification-obligations \
  --repo-root <producer-repo> \
  --project-config <producer-project-config> \
  --issue-number <issue>
```

Optional controls:

```bash
  --package-path <stage1-design-package-json>
  --verification-key-prefix <key-prefix>
  --scope-authority-label <qa-scope-label>
  --dry-run
```

## Why the parameters exist

- `--issue-number`: targets the existing `paa.work_items` row.
- `--package-path`: allows explicit source selection when there are multiple candidate artifacts.
- `--verification-key-prefix`: preserves legacy key naming when needed.
- `--scope-authority-label`: preserves legacy QA scope wording when needed.
- `--dry-run`: shows the derived contract before inserting anything.

## Current use

This is the reusable replacement for the obligation portion of one-off issue loaders such as:

- `104-load-issue101-retirement-subsystem-into-paa.sql`
- `106-load-issue103-retirement-lifecycle-executor-into-paa.sql`
- `108-load-issue106-retirement-boundary-diagnostics-into-paa.sql`

It does not replace every source-to-PAA load step yet.
Its purpose is narrower and safer:

- make the verification contract repeatable
- ensure later Dev/QA packet persistence has the obligation rows it depends on
- eliminate issue-specific SQL for proof-contract insertion
