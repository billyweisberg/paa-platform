# PAA Docs Header-First

Use this skill when the task involves finding, choosing, or updating PAA repo documents.

## Goal

Default to header-first discovery instead of bulk-reading document bodies.

This skill exists to reduce:
- context waste
- stale-doc drift
- filename-memory dependence
- rereading of irrelevant prose

## Default workflow

1. Start with the doc CLI, not full document reads.
2. Use header-only results to identify the smallest relevant doc set.
3. Only then read the full body of the top 1 to 4 relevant docs.

## Commands

Repo root:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform`

CLI:
- `python scripts/docs/paa_docs.py`

### Discovery
- find current docs for a domain:
  - `python scripts/docs/paa_docs.py current --root /Users/billyweisberg/Repos/billyweisberg/paa-platform --domain <domain>`
- find by component:
  - `python scripts/docs/paa_docs.py find --root /Users/billyweisberg/Repos/billyweisberg/paa-platform --component <ComponentName>`
- find by lifecycle stage:
  - `python scripts/docs/paa_docs.py find --root /Users/billyweisberg/Repos/billyweisberg/paa-platform --stage <design|plan|test|deploy>`
- inspect one header:
  - `python scripts/docs/paa_docs.py show --root /Users/billyweisberg/Repos/billyweisberg/paa-platform --path <doc-path>`
- inspect relationships:
  - `python scripts/docs/paa_docs.py related --root /Users/billyweisberg/Repos/billyweisberg/paa-platform --doc-id <doc-id>`

### Governance
- lint governed docs:
  - `python scripts/docs/paa_docs.py lint --root /Users/billyweisberg/Repos/billyweisberg/paa-platform`
- show stale governed docs:
  - `python scripts/docs/paa_docs.py stale --root /Users/billyweisberg/Repos/billyweisberg/paa-platform`

### Authoring
- create a new governed doc:
  - `python scripts/docs/paa_docs.py new-doc --root /Users/billyweisberg/Repos/billyweisberg/paa-platform --path <doc-path> --doc-type <type> --status <status> --summary <summary>`
- add or normalize a header on an existing doc:
  - `python scripts/docs/paa_docs.py set-header --root /Users/billyweisberg/Repos/billyweisberg/paa-platform --path <doc-path> --doc-type <type> --status <status>`

## Rules

- Do not bulk-read docs when the CLI can narrow the target set first.
- Prefer `current`, `find`, and `related` before opening full documents.
- Treat docs without headers as legacy until upgraded.
- When writing a new governed doc, use `new-doc` or `set-header` instead of hand-authoring the header.
