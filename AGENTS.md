# PAA Platform Agent Notes

## Doc Workflow

Use header-first document discovery before reading full document bodies.

Repo-local doc tools:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/paa_docs.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/lint_governed_docs.sh`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/.codex/skills/paa-docs-header-first/SKILL.md`

Preferred workflow:
1. run `current`, `find`, `show`, or `related` against doc headers
2. identify the smallest relevant canonical doc set
3. only then read the full body of the top relevant docs

Do not bulk-read design/planning docs when header-first lookup can narrow the target set.

If the task involves architecture descriptions, status summaries, naming a new service or component, or explaining implementation state, check the reference-stage terminology governance docs first with:
```bash
make -C /Users/billyweisberg/Repos/billyweisberg/paa-platform docs-current-reference
```

Use those docs to avoid:
- loose narrative claims
- broad status descriptions without scope
- naming hybrid runtime hubs as clean components
- overstating alignment or completeness

When changing governed docs or writing architecture/status summaries, also run:
```bash
make -C /Users/billyweisberg/Repos/billyweisberg/paa-platform docs-lint-language
```

When a governed doc is intended to bind directly to code truth, set:
- `Authority-Source: code`

Then verify the `Component:` header resolves to exported governed metadata with:
```bash
make -C /Users/billyweisberg/Repos/billyweisberg/paa-platform docs-lint-code
```

If the task is about producer implementation flow or operator execution flow, check the governed build-stage docs first with:
```bash
python /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/paa_docs.py current \
  --root /Users/billyweisberg/Repos/billyweisberg/paa-platform \
  --stage build
```

Convenience targets:
```bash
make -C /Users/billyweisberg/Repos/billyweisberg/paa-platform docs-current-design
make -C /Users/billyweisberg/Repos/billyweisberg/paa-platform docs-current-plan
make -C /Users/billyweisberg/Repos/billyweisberg/paa-platform docs-current-build
make -C /Users/billyweisberg/Repos/billyweisberg/paa-platform docs-current-test
make -C /Users/billyweisberg/Repos/billyweisberg/paa-platform docs-current-deploy
make -C /Users/billyweisberg/Repos/billyweisberg/paa-platform docs-current-operate
make -C /Users/billyweisberg/Repos/billyweisberg/paa-platform docs-current-reference
make -C /Users/billyweisberg/Repos/billyweisberg/paa-platform docs-lint-governed
make -C /Users/billyweisberg/Repos/billyweisberg/paa-platform docs-lint-language
make -C /Users/billyweisberg/Repos/billyweisberg/paa-platform docs-lint-code
```

## Governed Docs

The current governed-doc set is enforced through:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/lint_governed_docs.sh`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/.pre-commit-config.yaml`

Use:
```bash
bash /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/lint_governed_docs.sh
```

before changing governed docs.

## New Docs

When creating a new governed markdown doc, prefer:
- `new-doc`
- `set-header`

instead of hand-writing or manually editing the header.

Example:
```bash
python /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/paa_docs.py new-doc \
  --root /Users/billyweisberg/Repos/billyweisberg/paa-platform \
  --path /Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-18-example.md \
  --doc-type design-note \
  --status draft \
  --summary "Creates a new governed design note."
```
