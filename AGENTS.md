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
