# PAA Doc Header Tools

This directory contains the repo-local tools for governed PAA document headers.

## Main CLI

Path:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/paa_docs.py`

Use it to:
- index governed docs by header only
- find current canonical docs
- inspect related docs
- lint governed headers
- lint language governance in governed docs
- create new docs with headers
- retrofit headers onto existing docs

## Most Useful Commands

### 1. Show current docs for a stage
```bash
python /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/paa_docs.py current \
  --root /Users/billyweisberg/Repos/billyweisberg/paa-platform \
  --stage design
```

For build-flow recovery:
```bash
python /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/paa_docs.py current \
  --root /Users/billyweisberg/Repos/billyweisberg/paa-platform \
  --stage build
```

### 2. Show current docs for a domain
```bash
python /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/paa_docs.py current \
  --root /Users/billyweisberg/Repos/billyweisberg/paa-platform \
  --domain workflow-lifecycle
```

For language and terminology governance:
```bash
python /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/paa_docs.py current \
  --root /Users/billyweisberg/Repos/billyweisberg/paa-platform \
  --stage reference
```

### 3. Find docs for one component
```bash
python /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/paa_docs.py find \
  --root /Users/billyweisberg/Repos/billyweisberg/paa-platform \
  --component WorkflowLifecycleService
```

### 4. Inspect one doc header
```bash
python /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/paa_docs.py show \
  --root /Users/billyweisberg/Repos/billyweisberg/paa-platform \
  --path docs/2_Design/2026-05-17-workflow-lifecycle-service-component-spec.md
```

### 5. Inspect related docs
```bash
python /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/paa_docs.py related \
  --root /Users/billyweisberg/Repos/billyweisberg/paa-platform \
  --doc-id paa-workflow-lifecycle-service-component-spec
```

### 6. Create a new governed doc
```bash
python /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/paa_docs.py new-doc \
  --root /Users/billyweisberg/Repos/billyweisberg/paa-platform \
  --path /Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-18-example.md \
  --doc-type design-note \
  --status draft \
  --summary "Creates a new governed design note."
```

### 7. Add or normalize a header on an existing doc
```bash
python /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/paa_docs.py set-header \
  --root /Users/billyweisberg/Repos/billyweisberg/paa-platform \
  --path /Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/5_Test/2026-05-17-self-hosted-consumer-runtime-validation.md \
  --doc-type validation-note \
  --status active
```

## Governed Lint

Repo-local wrapper:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/lint_governed_docs.sh`

Run it with:
```bash
bash /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/lint_governed_docs.sh
```

This wrapper only checks the current governed doc set, not the entire historical docs tree.

## Language Governance Lint

Run:
```bash
python /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/paa_docs.py language-lint \
  --root /Users/billyweisberg/Repos/billyweisberg/paa-platform
```

This intentionally narrow linter checks for:
- banned vague phrases
- under-scoped strong status claims
- path claims that omit `aligned`, `hybrid`, or `legacy` classification

## Convenience Make Targets

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
```

## Workflow Rule

Preferred workflow:
1. use `current`, `find`, or `related`
2. inspect headers first
3. only then read the full bodies of the top few docs

This is the default intended recovery path for long-horizon work.
