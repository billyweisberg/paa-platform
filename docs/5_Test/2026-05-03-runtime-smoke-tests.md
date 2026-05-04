# Runtime Smoke Tests

## Goal

Replace repetitive manual runtime checks with one producer smoke test and one consumer smoke test.
These commands are intended to be run from the repo-local installed PAA wrappers.

## Producer Smoke Test

Run from the canonical producer repo:

```bash
cd /Users/billyweisberg/Repos/Individual-Centricity/appdev
./.codex/paa/bin/paa-producer smoke-test
```

What it validates:
- producer project config is present
- authority manifest resolves from the canonical producer repo
- authority version is readable
- producer source artifact paths are present in config

## Consumer Smoke Test

Run from the canonical consumer repo:

```bash
cd /Users/billyweisberg/Repos/billyweisberg/fractal-core-python
./.codex/paa/bin/paa-consumer smoke-test --expected-branch codex/paa-consumer-consolidation
```

What it validates:
- repo-local runtime guardrails
- installed authority package is readable
- queue/report path is reachable through TechLead report generation
- schema validation is optional via `--validate-schema`

## Testing an Active Issue Branch

If you are intentionally testing from an issue branch, pass that branch explicitly.

Example:

```bash
cd /Users/billyweisberg/Repos/billyweisberg/fractal-core-python
./.codex/paa/bin/paa-consumer smoke-test --expected-branch issue-106
```

## Reset After Historical Issue Testing

If you temporarily switch to a historical issue branch for regression testing, switch back when done:

```bash
cd /Users/billyweisberg/Repos/billyweisberg/fractal-core-python
git switch codex/paa-consumer-consolidation
```

If the temporary issue branch is no longer needed locally:

```bash
git branch -D issue-106
```

Only delete the branch after you are back on `codex/paa-consumer-consolidation`.


Optional schema validation:

```bash
cd /Users/billyweisberg/Repos/billyweisberg/fractal-core-python
./.codex/paa/bin/paa-consumer smoke-test --expected-branch codex/paa-consumer-consolidation --validate-schema
```
